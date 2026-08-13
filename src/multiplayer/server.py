"""Server-side logic for the multiplayer library.

This module implements the :class:`GameServer` class and the server side of the
client/server protocol (version 2). It is responsible for accepting client
connections, validating incoming messages, enforcing access levels, executing
the requested actions on the multiplayer domain objects (players, users, games
and groups) and broadcasting notifications to interested clients.

The transport layer relies on :mod:`asyncio`:

* TCP is used for the main communication. Each message is framed with a 4-byte
  big-endian length header followed by the serialized payload (JSON or
  MessagePack).
* UDP multicast is used for the optional network discovery feature.
"""
import asyncio
import json
import logging
import socket
import ssl
import struct
import time
import uuid
from enum import IntEnum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import bcrypt

from . import GameState, PlayerRole, SaveFormat
from .exceptions import (
    GameAlreadyStartedError,
    GameIsFinishedError,
    GameIsFullError,
    GameNotFoundInGroupError,
    GameNotPausedError,
    GameNotStartedError,
    GameNotTurnBasedError,
    MultiplayerError,
    PasswordError,
    PlayerNotFoundInGameError,
    UserAlreadyExistsError,
)
from .game import Game, GameGroup, Player, User
from .save import Save

try:
    import msgpack

    _MSGPACK_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    msgpack = None
    _MSGPACK_AVAILABLE = False

logger = logging.getLogger(__name__)

# Protocol-wide constants.
PROTOCOL_VERSION = 2
SERVICE_NAME = "multiplayer_server"
LENGTH_HEADER_SIZE = 4

# Default network configuration values.
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 65432
DEFAULT_MULTICAST_GROUP = "239.255.0.1"
DEFAULT_MULTICAST_PORT = 65434
DEFAULT_GC_PERIODICITY = 900
DEFAULT_TLS_DOMAIN = "localhost"

# Default persistence paths used when none is provided by the caller.
DEFAULT_JSON_PERSISTENCE_PATH = Path("data/server_data.json")
DEFAULT_SQLITE_PERSISTENCE_PATH = Path("data/server_data.db")


class AccessLevel(IntEnum):
    """Hierarchical access levels granted to connected clients.

    A client holding a given level is allowed to use the requests of that level
    as well as the requests of all the lower levels.
    """

    OPEN = 0
    BASE = 1
    PLAYER = 2
    GROUP_ADMIN = 3
    ADMIN = 4


# Mapping between a user role and the access level granted on authentication.
_ROLE_TO_ACCESS: Dict[PlayerRole, AccessLevel] = {
    PlayerRole.PLAYER: AccessLevel.PLAYER,
    PlayerRole.GROUP_ADMIN: AccessLevel.GROUP_ADMIN,
    PlayerRole.SERVER_ADMIN: AccessLevel.ADMIN,
}


def _check_password(plain: Optional[str], hashed: Optional[str]) -> bool:
    """Verifies a plain-text password against a bcrypt hash.

    Args:
        plain (str | None): The plain-text password supplied by the client.
        hashed (str | None): The stored bcrypt hash, or ``None`` when no
            password is configured.

    Returns:
        bool: ``True`` if the password matches (or no password is required),
        ``False`` otherwise.
    """
    if hashed is None:
        return True
    if not plain:
        return False
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except ValueError:
        return False


class ClientSession:
    """Holds the volatile state associated with a single connected client.

    A session tracks the current access level, the optionally authenticated
    user, the player objects created during the session, the active default
    player, the joined games and the subscribed groups. All of this information
    is discarded when the client disconnects.

    Attributes:
        session_id (str): The unique identifier of the session.
        peername (Any): The remote address of the client connection.
        access_level (AccessLevel): The current access level of the client.
        user (User | None): The authenticated user, if any.
        players (Dict[str, Player]): Session players indexed by their ID.
        subscribed_groups (Set[str]): IDs of the groups the client follows.
        joined_games (Set[str]): IDs of the games the client participates in.
    """

    def __init__(self, session_id: str, writer: "asyncio.StreamWriter", peername: Any):
        """Initializes a new client session.

        Args:
            session_id (str): The unique identifier of the session.
            writer (asyncio.StreamWriter): The stream writer used to send
                messages back to the client.
            peername (Any): The remote address of the client connection.
        """
        self.session_id: str = session_id
        self.peername: Any = peername
        self.access_level: AccessLevel = AccessLevel.OPEN
        self.user: Optional[User] = None
        self.players: Dict[str, Player] = {}
        self._writer: "asyncio.StreamWriter" = writer
        self._guest_default_player_id: Optional[str] = None
        self.subscribed_groups: Set[str] = set()
        self.joined_games: Set[str] = set()

    @property
    def writer(self) -> "asyncio.StreamWriter":
        """The stream writer used to push messages to the client.

        Returns:
            asyncio.StreamWriter: The associated writer.
        """
        return self._writer

    def set_default_player(self, player_id: str) -> None:
        """Designates a session (guest) player as the default one.

        Args:
            player_id (str): The ID of the player to use as default.
        """
        self._guest_default_player_id = player_id

    def resolve_default_player_id(self) -> Optional[str]:
        """Resolves the active default player for the session.

        An authenticated user takes priority over guest players. When the
        client is not authenticated, the last guest player marked as default is
        used.

        Returns:
            str | None: The ID of the active default player, or ``None`` if the
            session has no default player.
        """
        if self.user is not None:
            return self.user.player.ID
        return self._guest_default_player_id


class _DiscoveryProtocol(asyncio.DatagramProtocol):
    """UDP datagram protocol that answers network discovery requests."""

    def __init__(self, server: "GameServer"):
        """Initializes the discovery protocol.

        Args:
            server (GameServer): The owning server used to build responses.
        """
        self._server: "GameServer" = server
        self._transport: Optional[asyncio.DatagramTransport] = None

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        """Stores the datagram transport once the endpoint is ready.

        Args:
            transport (asyncio.BaseTransport): The created datagram transport.
        """
        self._transport = transport  # type: ignore[assignment]

    def datagram_received(self, data: bytes, addr: Tuple[str, int]) -> None:
        """Handles an incoming discovery datagram.

        Invalid or unsolicited datagrams are silently ignored, as mandated by
        the protocol.

        Args:
            data (bytes): The raw datagram payload.
            addr (Tuple[str, int]): The sender address.
        """
        if self._transport is None:
            return
        try:
            message = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return
        if not isinstance(message, dict):
            return
        if message.get("type") != "DISCOVERY":
            return
        if message.get("service_name") != SERVICE_NAME:
            return
        if message.get("version") != PROTOCOL_VERSION:
            return
        if self._server.hidden:
            return
        response = self._server.build_discovery_response()
        self._transport.sendto(json.dumps(response).encode("utf-8"), addr)


class GameServer:
    """Manages client connections and communications for a multiplayer service.

    The server coordinates the actions of connected clients and broadcasts the
    relevant information to them. It implements the server side of the protocol
    (version 2): network discovery, access control, user/player/game/group
    management, game events and server administration.

    Attributes:
        name (str): The human-readable name of the server.
        host (str): The IPv4 address the server listens on.
        port (int): The main TCP port the server listens on.
        use_tls (bool): Whether TLS is enabled on the main port.
    """

    # Minimal access level required for each request type.
    _MIN_ACCESS: Dict[str, AccessLevel] = {
        "SERVER_AUTH": AccessLevel.OPEN,
        "PLAYER_CREATE": AccessLevel.BASE,
        "PLAYER_LIST": AccessLevel.BASE,
        "PLAYER_UPDATE": AccessLevel.BASE,
        "USER_LOGIN": AccessLevel.BASE,
        "USER_LOGOUT": AccessLevel.BASE,
        "USER_CREATE": AccessLevel.BASE,
        "USER_UPDATE": AccessLevel.PLAYER,
        "USER_DELETE": AccessLevel.ADMIN,
        "USER_LIST": AccessLevel.PLAYER,
        "USER_LIST_ALL": AccessLevel.ADMIN,
        "PLAYER_LIST_ALL": AccessLevel.ADMIN,
        "GAME_CREATE": AccessLevel.BASE,
        "GAME_LIST": AccessLevel.BASE,
        "GAME_JOIN": AccessLevel.BASE,
        "GAME_LEAVE": AccessLevel.BASE,
        "GAME_CONTROL": AccessLevel.BASE,
        "GAME_PLAYER_ORDER": AccessLevel.BASE,
        "GAME_ACTION": AccessLevel.BASE,
        "GAME_STATE_SET": AccessLevel.BASE,
        "GAME_STATE_GET": AccessLevel.BASE,
        "GAME_NEXT_TURN": AccessLevel.BASE,
        "GAME_KICK": AccessLevel.GROUP_ADMIN,
        "GROUP_CREATE": AccessLevel.ADMIN,
        "GROUP_LIST": AccessLevel.BASE,
        "GROUP_SUBSCRIBE": AccessLevel.BASE,
        "GROUP_UNSUBSCRIBE": AccessLevel.BASE,
        "GROUP_ADD_GAME": AccessLevel.GROUP_ADMIN,
        "GROUP_REMOVE_GAME": AccessLevel.GROUP_ADMIN,
        "GROUP_DELETE": AccessLevel.ADMIN,
        "GROUP_GAME_LIST_ALL": AccessLevel.GROUP_ADMIN,
        "SERVER_INFO_GET": AccessLevel.ADMIN,
        "SERVER_CONFIG_GET": AccessLevel.ADMIN,
        "SERVER_CONFIG_SET": AccessLevel.ADMIN,
        "SERVER_AUDIT_LOG_GET": AccessLevel.ADMIN,
        "SERVER_PERSISTENCE_SAVE": AccessLevel.ADMIN,
        "SERVER_PERSISTENCE_RELOAD": AccessLevel.ADMIN,
        "SERVER_CONTROL": AccessLevel.ADMIN,
    }

    # Mapping between a request type and the type used for its response.
    _RESPONSE_TYPES: Dict[str, str] = {
        "SERVER_AUTH": "AUTH_RESPONSE",
        "USER_LOGIN": "AUTH_RESPONSE",
        "USER_LOGOUT": "USER_LOGOUT_RESPONSE",
        "PLAYER_CREATE": "PLAYER_CREATE_RESPONSE",
        "PLAYER_LIST": "PLAYER_LIST_RESPONSE",
        "PLAYER_UPDATE": "PLAYER_UPDATE_RESPONSE",
        "USER_CREATE": "USER_CREATE_RESPONSE",
        "USER_UPDATE": "USER_UPDATE_RESPONSE",
        "USER_DELETE": "USER_DELETE_RESPONSE",
        "USER_LIST": "USER_LIST_RESPONSE",
        "USER_LIST_ALL": "USER_LIST_ALL_RESPONSE",
        "PLAYER_LIST_ALL": "PLAYER_LIST_ALL_RESPONSE",
        "GAME_CREATE": "GAME_CREATE_RESPONSE",
        "GAME_LIST": "GAME_LIST_RESPONSE",
        "GAME_JOIN": "GAME_JOIN_RESPONSE",
        "GAME_LEAVE": "GAME_LEAVE_RESPONSE",
        "GAME_CONTROL": "GAME_CONTROL_RESPONSE",
        "GAME_PLAYER_ORDER": "GAME_PLAYER_ORDER_RESPONSE",
        "GAME_ACTION": "GAME_ACTION_RESPONSE",
        "GAME_STATE_SET": "GAME_STATE_SET_RESPONSE",
        "GAME_STATE_GET": "GAME_STATE_GET_RESPONSE",
        "GAME_NEXT_TURN": "GAME_NEXT_TURN_RESPONSE",
        "GAME_KICK": "GAME_KICK_RESPONSE",
        "GROUP_CREATE": "GROUP_CREATE_RESPONSE",
        "GROUP_LIST": "GROUP_LIST_RESPONSE",
        "GROUP_SUBSCRIBE": "GROUP_SUBSCRIBE_RESPONSE",
        "GROUP_UNSUBSCRIBE": "GROUP_UNSUBSCRIBE_RESPONSE",
        "GROUP_ADD_GAME": "GROUP_ADD_GAME_RESPONSE",
        "GROUP_REMOVE_GAME": "GROUP_REMOVE_GAME_RESPONSE",
        "GROUP_DELETE": "GROUP_DELETE_RESPONSE",
        "GROUP_GAME_LIST_ALL": "GROUP_GAME_LIST_ALL_RESPONSE",
        "SERVER_INFO_GET": "SERVER_INFO_GET_RESPONSE",
        "SERVER_CONFIG_GET": "SERVER_CONFIG_GET_RESPONSE",
        "SERVER_CONFIG_SET": "SERVER_CONFIG_SET_RESPONSE",
        "SERVER_AUDIT_LOG_GET": "SERVER_AUDIT_LOG_GET_RESPONSE",
        "SERVER_PERSISTENCE_SAVE": "SERVER_PERSISTENCE_SAVE_RESPONSE",
        "SERVER_PERSISTENCE_RELOAD": "SERVER_PERSISTENCE_RELOAD_RESPONSE",
        "SERVER_CONTROL": "SERVER_CONTROL_RESPONSE",
    }

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        unencrypted_port: Optional[int] = None,
        password: Optional[str] = None,
        name: str = "",
        use_tls: bool = False,
        tls_self_signed: bool = False,
        tls_domain: str = DEFAULT_TLS_DOMAIN,
        tls_cert_path: Optional[Path] = None,
        tls_key_path: Optional[Path] = None,
        discoverable: bool = False,
        multicast_group: str = DEFAULT_MULTICAST_GROUP,
        multicast_port: int = DEFAULT_MULTICAST_PORT,
        persistence_mode: Optional[SaveFormat] = None,
        persistence_path: Optional[Path] = None,
        garbage_collection_periodicity: int = DEFAULT_GC_PERIODICITY,
    ):
        """Initializes a new multiplayer game server.

        Args:
            host (str): IPv4 address to listen on. Defaults to ``"0.0.0.0"``.
            port (int): Main TCP port. Defaults to ``65432``.
            unencrypted_port (int | None): Optional unencrypted TCP port.
            password (str | None): Optional server password (level ``BASE``).
            name (str): Human-readable server name. Defaults to ``""``.
            use_tls (bool): Enable TLS 1.3 on the main port. Defaults to False.
            tls_self_signed (bool): Generate and use a self-signed certificate.
            tls_domain (str): Domain name used for the certificate.
            tls_cert_path (Path | None): Path to the TLS certificate.
            tls_key_path (Path | None): Path to the TLS private key.
            discoverable (bool): Enable multicast discovery. Defaults to False.
            multicast_group (str): Multicast address for discovery.
            multicast_port (int): UDP multicast port for discovery.
            persistence_mode (SaveFormat | None): Persistence storage format.
            persistence_path (Path | None): Path to the persistence file.
            garbage_collection_periodicity (int): Seconds between orphan player
                garbage collections.

        Raises:
            ValueError: If the network or TLS configuration is inconsistent.
        """
        if not isinstance(port, int) or not 0 <= port <= 65535:
            raise ValueError(f"Invalid TCP port: {port}")
        if unencrypted_port is not None:
            if not isinstance(unencrypted_port, int) or not 1 <= unencrypted_port <= 65535:
                raise ValueError(f"Invalid unencrypted port: {unencrypted_port}")
            if unencrypted_port == port:
                raise ValueError("The unencrypted port must differ from the main port.")
        if not isinstance(multicast_port, int) or not 1 <= multicast_port <= 65535:
            raise ValueError(f"Invalid multicast port: {multicast_port}")
        if use_tls and not tls_self_signed and (tls_cert_path is None or tls_key_path is None):
            raise ValueError(
                "TLS is enabled without self-signed certificate: both "
                "tls_cert_path and tls_key_path must be provided."
            )

        self.host: str = host
        self.port: int = port
        self.unencrypted_port: Optional[int] = unencrypted_port
        self.name: str = name
        self.use_tls: bool = use_tls
        self.tls_self_signed: bool = tls_self_signed
        self.tls_domain: str = tls_domain
        self.tls_cert_path: Optional[Path] = Path(tls_cert_path) if tls_cert_path else None
        self.tls_key_path: Optional[Path] = Path(tls_key_path) if tls_key_path else None
        self.discoverable: bool = discoverable
        self.multicast_group: str = multicast_group
        self.multicast_port: int = multicast_port
        self.garbage_collection_periodicity: int = garbage_collection_periodicity

        self._server_hash: Optional[str] = (
            bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode() if password else None
        )
        self._admin_hash: Optional[str] = None
        self.user_registration_enabled: bool = True
        self.hidden: bool = False

        # Persistence configuration.
        self.persistence_mode: Optional[SaveFormat] = persistence_mode
        if persistence_mode is None:
            self.persistence_path: Optional[Path] = (
                Path(persistence_path) if persistence_path else None
            )
        elif persistence_path is not None:
            self.persistence_path = Path(persistence_path)
        elif persistence_mode == SaveFormat.SQLITE:
            self.persistence_path = DEFAULT_SQLITE_PERSISTENCE_PATH
        else:
            self.persistence_path = DEFAULT_JSON_PERSISTENCE_PATH
        self._save: Optional[Save] = None

        # Domain registries shared by all sessions.
        self._users: Dict[str, User] = {}
        self._games: Dict[str, Game] = {}
        self._groups: Dict[str, GameGroup] = {}
        self._players: Dict[str, Player] = {}
        self._game_custom_state: Dict[str, Dict[str, Any]] = {}
        self._game_roles: Dict[str, Dict[str, str]] = {}
        self._game_creator_session: Dict[str, str] = {}
        self._audit_log: List[Dict[str, Any]] = []

        # Runtime state.
        self._sessions: Dict[str, ClientSession] = {}
        self._tcp_server: Optional[asyncio.AbstractServer] = None
        self._unencrypted_server: Optional[asyncio.AbstractServer] = None
        self._discovery_transport: Optional[asyncio.DatagramTransport] = None
        self._gc_task: Optional[asyncio.Task] = None
        self._running: bool = False
        self._start_time: float = 0.0
        self._actual_port: int = port

    @property
    def password_required(self) -> bool:
        """Indicates whether a server password is required to reach ``BASE``.

        Returns:
            bool: ``True`` if a server password is configured.
        """
        return self._server_hash is not None

    def build_discovery_response(self) -> Dict[str, Any]:
        """Builds the discovery response advertised on the local network.

        Returns:
            Dict[str, Any]: The JSON-serializable discovery response message.
        """
        return {
            "type": "DISCOVERY_RESPONSE",
            "service_name": SERVICE_NAME,
            "version": PROTOCOL_VERSION,
            "service_host": self.host,
            "service_port": self._actual_port,
            "unencrypted_port": self.unencrypted_port,
            "name": self.name,
            "use_tls": self.use_tls,
            "password_required": self.password_required,
        }

    # ------------------------------------------------------------------ #
    # Lifecycle management
    # ------------------------------------------------------------------ #
    async def start(self) -> None:
        """Starts the server asynchronously.

        Loads the persistent data when persistence is enabled, then sets up the
        TCP listener (secured with TLS when configured), the optional
        unencrypted TCP listener, the optional multicast discovery endpoint and
        the periodic garbage collection task.

        Raises:
            ValueError: If the TLS configuration cannot be applied.
        """
        if self._running:
            return

        self._load_persistence()
        self._ensure_server_admin()

        tls_context = self._build_tls_context() if self.use_tls else None
        self._tcp_server = await asyncio.start_server(
            self._handle_connection, self.host, self.port, ssl=tls_context
        )
        sockets = self._tcp_server.sockets or ()
        if sockets:
            self._actual_port = sockets[0].getsockname()[1]

        if self.unencrypted_port is not None:
            self._unencrypted_server = await asyncio.start_server(
                self._handle_connection, self.host, self.unencrypted_port
            )

        if self.discoverable:
            await self._start_discovery()

        self._running = True
        self._start_time = time.monotonic()
        self._gc_task = asyncio.ensure_future(self._garbage_collection_loop())
        logger.info("Server '%s' started on %s:%s", self.name, self.host, self._actual_port)

    async def stop(self) -> None:
        """Stops the server.

        Attempts to close the client connections cleanly, persists the data when
        persistence is enabled and releases the network resources.
        """
        if not self._running:
            return
        self._running = False

        if self._gc_task is not None:
            self._gc_task.cancel()
            try:
                await self._gc_task
            except asyncio.CancelledError:
                pass
            self._gc_task = None

        await self._broadcast_shutdown()

        for session in list(self._sessions.values()):
            self._close_session(session)
        self._sessions.clear()

        if self._discovery_transport is not None:
            self._discovery_transport.close()
            self._discovery_transport = None

        for server in (self._tcp_server, self._unencrypted_server):
            if server is not None:
                server.close()
                await server.wait_closed()
        self._tcp_server = None
        self._unencrypted_server = None

        self._save_persistence()
        logger.info("Server '%s' stopped", self.name)

    async def restart(self) -> None:
        """Restarts the server.

        Equivalent to calling :meth:`stop` followed by :meth:`start`, persisting
        and reloading the data when persistence is enabled.
        """
        await self.stop()
        await self.start()

    def _build_tls_context(self) -> ssl.SSLContext:
        """Builds the TLS 1.3 context used to secure the main TCP port.

        Returns:
            ssl.SSLContext: The configured server-side TLS context.

        Raises:
            ValueError: If the certificate material cannot be loaded or
                generated.
        """
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_3
        if self.tls_self_signed:
            cert_path, key_path = self._generate_self_signed_cert()
        else:
            cert_path, key_path = self.tls_cert_path, self.tls_key_path
        if cert_path is None or key_path is None:
            raise ValueError("Missing TLS certificate or key path.")
        try:
            context.load_cert_chain(certfile=str(cert_path), keyfile=str(key_path))
        except (ssl.SSLError, OSError) as exc:
            logger.exception("Failed to load the TLS certificate chain.")
            raise ValueError(f"Cannot load TLS material: {exc}") from exc
        return context

    def _generate_self_signed_cert(self) -> Tuple[Path, Path]:
        """Generates a self-signed certificate and its private key.

        Returns:
            Tuple[Path, Path]: The paths to the generated certificate and key.

        Raises:
            ValueError: If the ``cryptography`` package is not available.
        """
        try:
            import datetime

            from cryptography import x509
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.x509.oid import NameOID
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise ValueError(
                "Self-signed TLS certificates require the 'cryptography' package."
            ) from exc

        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = issuer = x509.Name(
            [x509.NameAttribute(NameOID.COMMON_NAME, self.tls_domain)]
        )
        now = datetime.datetime.now(datetime.timezone.utc)
        certificate = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now)
            .not_valid_after(now + datetime.timedelta(days=365))
            .add_extension(
                x509.SubjectAlternativeName([x509.DNSName(self.tls_domain)]),
                critical=False,
            )
            .sign(key, hashes.SHA256())
        )

        cert_dir = Path("data")
        cert_dir.mkdir(parents=True, exist_ok=True)
        cert_path = cert_dir / "self_signed_cert.pem"
        key_path = cert_dir / "self_signed_key.pem"
        cert_path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
        key_path.write_bytes(
            key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
        return cert_path, key_path

    async def _start_discovery(self) -> None:
        """Sets up the multicast UDP endpoint used for network discovery."""
        loop = asyncio.get_running_loop()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", self.multicast_port))
        group_bin = socket.inet_aton(self.multicast_group)
        membership = group_bin + socket.inet_aton("0.0.0.0")
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership)
        transport, _ = await loop.create_datagram_endpoint(
            lambda: _DiscoveryProtocol(self), sock=sock
        )
        self._discovery_transport = transport  # type: ignore[assignment]

    # ------------------------------------------------------------------ #
    # Persistence
    # ------------------------------------------------------------------ #
    def _ensure_server_admin(self) -> None:
        """Creates the default server administrator when none exists.

        The persistence layer must be loaded before this method is called so
        that a restored administrator prevents the bootstrap account from
        being created.
        """
        if any(user.role == PlayerRole.SERVER_ADMIN for user in self._users.values()):
            return

        admin = self._users.get("admin")
        if admin is None:
            try:
                admin = User(username="admin", password="admin")
            except UserAlreadyExistsError:
                # ``User`` keeps a process-wide username registry.  A username
                # left by another server instance must not prevent this
                # server from bootstrapping its own account.
                User._existing_usernames.discard("admin")
                admin = User(username="admin", password="admin")
        else:
            admin.change_password("admin")

        admin.role = PlayerRole.SERVER_ADMIN
        self._users[admin.username] = admin
        self._players[admin.player.ID] = admin.player

    def _load_persistence(self) -> None:
        """Loads persistent data into memory when persistence is enabled."""
        if self.persistence_mode is None or self.persistence_path is None:
            return
        self.persistence_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._save = Save(self.persistence_path, self.persistence_mode)
            for game in self._save.load(Game):
                self._games[game.ID] = game
            for group in self._save.load(GameGroup):
                self._groups[group.ID] = group
            for player in self._save.load(Player):
                self._players[player.ID] = player
            for user in self._save.load(User):
                self._users[user.username] = user
                self._players[user.player.ID] = user.player
        except MultiplayerError:
            logger.exception("Failed to load persistent data.")

    def _save_persistence(self) -> None:
        """Persists the in-memory domain objects when persistence is enabled."""
        if self.persistence_mode is None or self.persistence_path is None:
            return
        try:
            if self._save is None:
                self._save = Save(self.persistence_path, self.persistence_mode)
            for game in self._games.values():
                self._save.save(game)
            for group in self._groups.values():
                self._save.save(group)
            for player in self._players.values():
                self._save.save(player)
            for user in self._users.values():
                self._save.save(user)
            self._save.flush()
        except MultiplayerError:
            logger.exception("Failed to persist data.")

    # ------------------------------------------------------------------ #
    # Serialization and framing
    # ------------------------------------------------------------------ #
    @staticmethod
    def _encode_message(message: Dict[str, Any], binary: bool) -> bytes:
        """Serializes and frames a message for TCP transmission.

        Args:
            message (Dict[str, Any]): The message to serialize.
            binary (bool): Whether to use MessagePack instead of JSON.

        Returns:
            bytes: The framed message (4-byte big-endian length + payload).
        """
        if binary and _MSGPACK_AVAILABLE:
            body = msgpack.packb(message, use_bin_type=True)
        else:
            body = json.dumps(message).encode("utf-8")
        return struct.pack(">I", len(body)) + body

    @staticmethod
    def _decode_body(body: bytes) -> Dict[str, Any]:
        """Deserializes a received message body.

        The serialization format is detected automatically: JSON is attempted
        first, then MessagePack as a fallback.

        Args:
            body (bytes): The raw message body (without the length header).

        Returns:
            Dict[str, Any]: The deserialized message.

        Raises:
            ValueError: If the body cannot be deserialized into a mapping.
        """
        try:
            message = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            if not _MSGPACK_AVAILABLE:
                raise ValueError("Cannot decode message body.")
            try:
                message = msgpack.unpackb(body, raw=False)
            except Exception as exc:  # pragma: no cover - defensive
                raise ValueError("Cannot decode message body.") from exc
        if not isinstance(message, dict):
            raise ValueError("Message is not a JSON/MessagePack object.")
        return message

    async def _read_message(self, reader: "asyncio.StreamReader") -> Optional[Dict[str, Any]]:
        """Reads a single length-prefixed message from a TCP stream.

        Args:
            reader (asyncio.StreamReader): The stream reader to consume.

        Returns:
            Dict[str, Any] | None: The decoded message, or ``None`` if the
            connection was closed.

        Raises:
            ValueError: If the message body cannot be decoded.
        """
        header = await reader.readexactly(LENGTH_HEADER_SIZE)
        (length,) = struct.unpack(">I", header)
        body = await reader.readexactly(length)
        return self._decode_body(body)

    # ------------------------------------------------------------------ #
    # Connection handling and dispatch
    # ------------------------------------------------------------------ #
    async def _handle_connection(
        self, reader: "asyncio.StreamReader", writer: "asyncio.StreamWriter"
    ) -> None:
        """Handles the lifecycle of a single client TCP connection.

        Args:
            reader (asyncio.StreamReader): The stream reader for the client.
            writer (asyncio.StreamWriter): The stream writer for the client.
        """
        peername = writer.get_extra_info("peername")
        session = ClientSession(str(uuid.uuid4()), writer, peername)
        # A server password lifts the level to BASE; otherwise OPEN behaves as BASE.
        session.access_level = AccessLevel.OPEN if self.password_required else AccessLevel.BASE
        self._sessions[session.session_id] = session
        logger.info("Client connected: %s", peername)
        try:
            while self._running:
                try:
                    message = await self._read_message(reader)
                except (asyncio.IncompleteReadError, ConnectionError):
                    break
                except ValueError:
                    await self._send(
                        session,
                        self._make_error("ERROR", "INVALID_MESSAGE", "Malformed message."),
                    )
                    continue
                if message is None:
                    break
                await self._dispatch(session, message)
        finally:
            self._close_session(session)
            self._sessions.pop(session.session_id, None)
            logger.info("Client disconnected: %s", peername)

    async def _dispatch(self, session: ClientSession, message: Dict[str, Any]) -> None:
        """Validates and routes an incoming request to its handler.

        Args:
            session (ClientSession): The originating client session.
            message (Dict[str, Any]): The decoded request message.
        """
        request_id = message.get("request_id")
        msg_type = message.get("type")
        version = message.get("version")

        if not isinstance(msg_type, str):
            await self._send(
                session, self._make_error("ERROR", "INVALID_MESSAGE", "Missing type.", request_id)
            )
            return
        if version != PROTOCOL_VERSION:
            await self._send(
                session,
                self._make_error(
                    "ERROR", "UNSUPPORTED_VERSION", "Unsupported protocol version.", request_id
                ),
            )
            return

        handler = getattr(self, f"_handle_{msg_type.lower()}", None)
        response_type = self._RESPONSE_TYPES.get(msg_type, "ERROR")
        if handler is None or msg_type not in self._MIN_ACCESS:
            await self._send(
                session,
                self._make_error("ERROR", "UNKNOWN_TYPE", f"Unknown type: {msg_type}", request_id),
            )
            return

        if session.access_level < self._MIN_ACCESS[msg_type]:
            await self._send(
                session,
                self._make_response(
                    response_type,
                    {
                        "success": False,
                        "error_code": "INSUFFICIENT_PERMISSIONS",
                        "message": "Insufficient access level for this request.",
                    },
                    request_id,
                ),
            )
            return

        payload = message.get("payload")
        if not isinstance(payload, dict):
            payload = {}
        try:
            result = await self._call_handler(handler, session, payload)
        except Exception:  # pragma: no cover - defensive
            logger.exception("Unhandled error while processing %s", msg_type)
            await self._send(
                session,
                self._make_response(
                    response_type,
                    {
                        "success": False,
                        "error_code": "INTERNAL_ERROR",
                        "message": "Internal server error.",
                    },
                    request_id,
                ),
            )
            return

        resp_type, resp_payload = result
        await self._send(session, self._make_response(resp_type, resp_payload, request_id))

    @staticmethod
    async def _call_handler(handler: Any, session: ClientSession, payload: Dict[str, Any]) -> Any:
        """Invokes a handler, awaiting it if it is a coroutine.

        Args:
            handler (Any): The bound handler method.
            session (ClientSession): The originating client session.
            payload (Dict[str, Any]): The request payload.

        Returns:
            Any: A ``(response_type, response_payload)`` tuple.
        """
        result = handler(session, payload)
        if asyncio.iscoroutine(result):
            return await result
        return result

    @staticmethod
    def _make_response(
        response_type: str, payload: Dict[str, Any], request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Builds a protocol response message.

        Args:
            response_type (str): The response message type.
            payload (Dict[str, Any]): The response payload.
            request_id (str | None): The correlation identifier to echo back.

        Returns:
            Dict[str, Any]: The complete response message.
        """
        message: Dict[str, Any] = {
            "type": response_type,
            "version": PROTOCOL_VERSION,
            "payload": payload,
        }
        if request_id is not None:
            message["request_id"] = request_id
        return message

    @staticmethod
    def _make_error(
        response_type: str,
        error_code: str,
        message: str,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Builds a protocol error response message.

        Args:
            response_type (str): The response message type.
            error_code (str): The machine-readable error code.
            message (str): The human-readable error message.
            request_id (str | None): The correlation identifier to echo back.

        Returns:
            Dict[str, Any]: The complete error message.
        """
        return GameServer._make_response(
            response_type,
            {"success": False, "error_code": error_code, "message": message},
            request_id,
        )

    async def _send(
        self, session: ClientSession, message: Dict[str, Any], binary: bool = False
    ) -> None:
        """Sends a framed message to a single client.

        Args:
            session (ClientSession): The destination session.
            message (Dict[str, Any]): The message to send.
            binary (bool): Whether to use MessagePack encoding.
        """
        writer = session.writer
        try:
            writer.write(self._encode_message(message, binary))
            await writer.drain()
        except ConnectionError:
            logger.debug("Failed to send message to %s", session.peername)

    def _close_session(self, session: ClientSession) -> None:
        """Closes a client session and releases its resources.

        Args:
            session (ClientSession): The session to close.
        """
        for game_id in list(session.joined_games):
            self._remove_session_players_from_game(session, game_id)
        try:
            session.writer.close()
        except Exception:  # pragma: no cover - defensive
            pass

    def _remove_session_players_from_game(self, session: ClientSession, game_id: str) -> None:
        """Removes every session player from a game on disconnection.

        Args:
            session (ClientSession): The disconnecting session.
            game_id (str): The game to clean up.
        """
        game = self._games.get(game_id)
        if game is None:
            return
        roles = self._game_roles.get(game_id, {})
        for player_id in list(session.players):
            if player_id not in roles:
                continue
            try:
                if roles[player_id] == "OBSERVER":
                    game.remove_observer(player_id)
                else:
                    game.remove_player(player_id)
            except PlayerNotFoundInGameError:
                pass
            roles.pop(player_id, None)
        session.joined_games.discard(game_id)

    # ------------------------------------------------------------------ #
    # Broadcasting and notifications
    # ------------------------------------------------------------------ #
    async def _broadcast(
        self, session_ids: Set[str], message: Dict[str, Any], binary: bool = True
    ) -> None:
        """Sends a notification to a set of sessions.

        Args:
            session_ids (Set[str]): The IDs of the destination sessions.
            message (Dict[str, Any]): The notification message.
            binary (bool): Whether to use MessagePack encoding.
        """
        for session_id in list(session_ids):
            session = self._sessions.get(session_id)
            if session is not None:
                await self._send(session, message, binary=binary)

    async def _broadcast_group(self, group_id: str, message: Dict[str, Any]) -> None:
        """Sends a notification to every client subscribed to a group.

        Args:
            group_id (str): The concerned group ID.
            message (Dict[str, Any]): The notification message.
        """
        targets = {
            session.session_id
            for session in self._sessions.values()
            if group_id in session.subscribed_groups
        }
        await self._broadcast(targets, message)

    async def _broadcast_game(self, game_id: str, message: Dict[str, Any]) -> None:
        """Sends a notification to every client participating in a game.

        Args:
            game_id (str): The concerned game ID.
            message (Dict[str, Any]): The notification message.
        """
        targets = {
            session.session_id
            for session in self._sessions.values()
            if game_id in session.joined_games
        }
        await self._broadcast(targets, message)

    async def _broadcast_shutdown(self) -> None:
        """Notifies every connected client that the server is shutting down."""
        message = {
            "type": "SERVER_SHUTDOWN",
            "version": PROTOCOL_VERSION,
            "payload": {"delay": 0, "message": "The server is shutting down."},
        }
        await self._broadcast(set(self._sessions), message)

    async def _garbage_collection_loop(self) -> None:
        """Periodically removes orphan players from the server registry."""
        while self._running:
            try:
                await asyncio.sleep(self.garbage_collection_periodicity)
            except asyncio.CancelledError:
                break
            self._collect_orphan_players()

    def _collect_orphan_players(self) -> None:
        """Removes players that are neither linked to a user nor to a session."""
        linked_to_user = {user.player.ID for user in self._users.values()}
        linked_to_session: Set[str] = set()
        for session in self._sessions.values():
            linked_to_session.update(session.players)
        for player_id in list(self._players):
            if player_id in linked_to_user or player_id in linked_to_session:
                continue
            self._players.pop(player_id, None)

    # ------------------------------------------------------------------ #
    # Connection and access handlers
    # ------------------------------------------------------------------ #
    def _handle_server_auth(
        self, session: ClientSession, payload: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Handles a ``SERVER_AUTH`` request (server password presentation).

        Args:
            session (ClientSession): The originating session.
            payload (Dict[str, Any]): The request payload.

        Returns:
            Tuple[str, Dict[str, Any]]: The response type and payload.
        """
        password = payload.get("password")
        if not _check_password(password, self._server_hash):
            return "AUTH_RESPONSE", {
                "success": False,
                "access_level": session.access_level.name,
                "error_code": "INVALID_PASSWORD",
                "message": "Invalid server password.",
            }
        session.access_level = max(session.access_level, AccessLevel.BASE)
        return "AUTH_RESPONSE", {
            "success": True,
            "access_level": session.access_level.name,
            "message": "Authentication successful",
        }

    def _handle_user_login(
        self, session: ClientSession, payload: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Handles a ``USER_LOGIN`` request (user authentication).

        Args:
            session (ClientSession): The originating session.
            payload (Dict[str, Any]): The request payload.

        Returns:
            Tuple[str, Dict[str, Any]]: The response type and payload.
        """
        username = payload.get("username")
        password = payload.get("password")
        if session.user is not None:
            return "AUTH_RESPONSE", {
                "success": False,
                "access_level": session.access_level.name,
                "error_code": "ALREADY_AUTHENTICATED",
                "message": "Already authenticated.",
            }
        user = self._users.get(username) if isinstance(username, str) else None
        if user is None or not _check_password(password, user.hash):
            return "AUTH_RESPONSE", {
                "success": False,
                "access_level": session.access_level.name,
                "error_code": "INVALID_CREDENTIALS",
                "message": "Invalid username or password",
            }
        session.user = user
        session.access_level = _ROLE_TO_ACCESS.get(user.role, AccessLevel.PLAYER)
        session.players[user.player.ID] = user.player
        self._players[user.player.ID] = user.player
        return "AUTH_RESPONSE", {
            "success": True,
            "access_level": session.access_level.name,
            "username": user.username,
            "role": user.role.name,
            "player_id": user.player.ID,
            "player_name": user.player.name,
            "message": "Authentication successful",
        }

    def _handle_user_logout(
        self, session: ClientSession, payload: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Handles a ``USER_LOGOUT`` request.

        Args:
            session (ClientSession): The originating session.
            payload (Dict[str, Any]): The request payload.

        Returns:
            Tuple[str, Dict[str, Any]]: The response type and payload.
        """
        session.user = None
        session.access_level = (
            AccessLevel.OPEN if self.password_required else AccessLevel.BASE
        )
        session.access_level = max(session.access_level, AccessLevel.BASE)
        return "USER_LOGOUT_RESPONSE", {
            "success": True,
            "access_level": session.access_level.name,
            "message": "Logged out successfully",
        }

    # ------------------------------------------------------------------ #
    # Player handlers
    # ------------------------------------------------------------------ #
    def _handle_player_create(
        self, session: ClientSession, payload: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Handles a ``PLAYER_CREATE`` request (session player creation).

        Args:
            session (ClientSession): The originating session.
            payload (Dict[str, Any]): The request payload.

        Returns:
            Tuple[str, Dict[str, Any]]: The response type and payload.
        """
        name = payload.get("name")
        if not isinstance(name, str) or not name.strip():
            return "PLAYER_CREATE_RESPONSE", {
                "success": False,
                "error_code": "INVALID_NAME",
                "message": "Invalid player name.",
            }
        is_default = payload.get("is_default")
        attributes = payload.get("attributes")
        player = Player(name=name)
        if isinstance(attributes, dict):
            player.dynamic_state.update(attributes)
        session.players[player.ID] = player
        self._players[player.ID] = player
        if is_default or session.resolve_default_player_id() is None:
            session.set_default_player(player.ID)
        return "PLAYER_CREATE_RESPONSE", {
            "success": True,
            "player_id": player.ID,
            "message": "Player created successfully",
        }

    def _handle_player_list(
        self, session: ClientSession, payload: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Handles a ``PLAYER_LIST`` request (list of the session players).

        Args:
            session (ClientSession): The originating session.
            payload (Dict[str, Any]): The request payload.

        Returns:
            Tuple[str, Dict[str, Any]]: The response type and payload.
        """
        default_id = session.resolve_default_player_id()
        players = [
            {"player_id": player.ID, "name": player.name, "is_default": player.ID == default_id}
            for player in session.players.values()
        ]
        return "PLAYER_LIST_RESPONSE", {"success": True, "players": players}

    def _handle_player_update(
        self, session: ClientSession, payload: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Handles a ``PLAYER_UPDATE`` request (rename a session player).

        Args:
            session (ClientSession): The originating session.
            payload (Dict[str, Any]): The request payload.

        Returns:
            Tuple[str, Dict[str, Any]]: The response type and payload.
        """
        player_id = payload.get("player_id")
        name = payload.get("name")
        player = session.players.get(player_id) if isinstance(player_id, str) else None
        if player is None:
            return "PLAYER_UPDATE_RESPONSE", {
                "success": False,
                "error_code": "PLAYER_NOT_FOUND",
                "message": "Player not found in this session.",
            }
        if not isinstance(name, str) or not name.strip():
            return "PLAYER_UPDATE_RESPONSE", {
                "success": False,
                "error_code": "INVALID_NAME",
                "message": "Invalid player name.",
            }
        player.name = name
        return "PLAYER_UPDATE_RESPONSE", {
            "success": True,
            "player_id": player.ID,
            "message": "Player updated successfully",
        }

    def _handle_player_list_all(
        self, session: ClientSession, payload: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Handles a ``PLAYER_LIST_ALL`` request (admin: every player).

        Args:
            session (ClientSession): The originating session.
            payload (Dict[str, Any]): The request payload.

        Returns:
            Tuple[str, Dict[str, Any]]: The response type and payload.
        """
        persistent_ids = {user.player.ID for user in self._users.values()}
        connected_ids: Set[str] = set()
        for client in self._sessions.values():
            connected_ids.update(client.players)
        players = []
        for player in self._players.values():
            players.append(
                {
                    "player_id": player.ID,
                    "name": player.name,
                    "connected": player.ID in connected_ids,
                    "is_persistent": player.ID in persistent_ids,
                    "games": self._games_summary_for_player(player.ID),
                }
            )
        return "PLAYER_LIST_ALL_RESPONSE", {"success": True, "players": players}

    def _games_summary_for_player(self, player_id: str) -> List[Dict[str, Any]]:
        """Builds the per-game summary for a given player.

        Args:
            player_id (str): The player ID to inspect.

        Returns:
            List[Dict[str, Any]]: The list of game summaries with the role.
        """
        summaries = []
        for game in self._games.values():
            roles = self._game_roles.get(game.ID, {})
            if player_id not in roles:
                continue
            summary = self._game_summary(game)
            summary["role"] = roles[player_id]
            summaries.append(summary)
        return summaries

    # ------------------------------------------------------------------ #
    # User management handlers
    # ------------------------------------------------------------------ #
    def _handle_user_create(
        self, session: ClientSession, payload: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Handles a ``USER_CREATE`` request (account creation).

        Args:
            session (ClientSession): The originating session.
            payload (Dict[str, Any]): The request payload.

        Returns:
            Tuple[str, Dict[str, Any]]: The response type and payload.
        """
        username = payload.get("username")
        password = payload.get("password")
        email = payload.get("email", "")
        role_name = payload.get("role", "PLAYER")
        if not isinstance(username, str) or not username or not isinstance(password, str):
            return "USER_CREATE_RESPONSE", {
                "success": False,
                "error_code": "INVALID_DATA",
                "message": "Invalid username or password.",
            }
        try:
            role = PlayerRole[role_name] if isinstance(role_name, str) else PlayerRole.PLAYER
        except KeyError:
            return "USER_CREATE_RESPONSE", {
                "success": False,
                "error_code": "INVALID_DATA",
                "message": f"Unknown role: {role_name}",
            }
        is_admin = session.access_level >= AccessLevel.ADMIN
        if not is_admin:
            if role != PlayerRole.PLAYER:
                return "USER_CREATE_RESPONSE", {
                    "success": False,
                    "error_code": "INSUFFICIENT_PERMISSIONS",
                    "message": "Only an administrator can assign this role.",
                }
            if not self.user_registration_enabled:
                return "USER_CREATE_RESPONSE", {
                    "success": False,
                    "error_code": "REGISTRATION_DISABLED",
                    "message": "User registration is disabled.",
                }
        try:
            user = User(username=username, password=password, email=email if isinstance(email, str) else "")
        except UserAlreadyExistsError:
            return "USER_CREATE_RESPONSE", {
                "success": False,
                "error_code": "USER_ALREADY_EXISTS",
                "message": "Username already taken",
            }
        user.role = role
        attributes = payload.get("attributes")
        if isinstance(attributes, dict):
            user.player.dynamic_state.update(attributes)
        self._users[user.username] = user
        self._players[user.player.ID] = user.player
        self._audit("USER_CREATE", session, username)
        return "USER_CREATE_RESPONSE", {
            "success": True,
            "username": user.username,
            "message": "User account created successfully",
        }

    def _handle_user_update(
        self, session: ClientSession, payload: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Handles a ``USER_UPDATE`` request (account modification).

        Args:
            session (ClientSession): The originating session.
            payload (Dict[str, Any]): The request payload.

        Returns:
            Tuple[str, Dict[str, Any]]: The response type and payload.
        """
        username = payload.get("username")
        user = self._users.get(username) if isinstance(username, str) else None
        if user is None:
            return "USER_UPDATE_RESPONSE", {
                "success": False,
                "error_code": "USER_NOT_FOUND",
                "message": "User not found",
            }
        is_admin = session.access_level >= AccessLevel.ADMIN
        is_owner = session.user is not None and session.user.username == username
        if not is_admin and not is_owner:
            return "USER_UPDATE_RESPONSE", {
                "success": False,
                "error_code": "INSUFFICIENT_PERMISSIONS",
                "message": "Cannot modify this user.",
            }
        if ("role" in payload or "managed_groups" in payload) and not is_admin:
            return "USER_UPDATE_RESPONSE", {
                "success": False,
                "error_code": "INSUFFICIENT_PERMISSIONS",
                "message": "Only an administrator can change role or managed groups.",
            }
        new_password = payload.get("password")
        if isinstance(new_password, str) and new_password:
            user.change_password(new_password)
        if isinstance(payload.get("email"), str):
            user.email = payload["email"]
        if isinstance(payload.get("player_name"), str):
            user.player.name = payload["player_name"]
        if is_admin and isinstance(payload.get("role"), str):
            try:
                user.role = PlayerRole[payload["role"]]
            except KeyError:
                return "USER_UPDATE_RESPONSE", {
                    "success": False,
                    "error_code": "INVALID_DATA",
                    "message": "Unknown role.",
                }
        if is_admin and isinstance(payload.get("managed_groups"), list):
            user.groups_id.clear()
            user.groups_id.extend(
                gid for gid in payload["managed_groups"] if gid in self._groups
            )
        if isinstance(payload.get("attributes"), dict):
            user.player.dynamic_state.update(payload["attributes"])
        self._audit("USER_UPDATE", session, username)
        return "USER_UPDATE_RESPONSE", {
            "success": True,
            "username": user.username,
            "message": "User account updated successfully",
        }

    def _handle_user_delete(
        self, session: ClientSession, payload: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Handles a ``USER_DELETE`` request (account deletion).

        Args:
            session (ClientSession): The originating session.
            payload (Dict[str, Any]): The request payload.

        Returns:
            Tuple[str, Dict[str, Any]]: The response type and payload.
        """
        username = payload.get("username")
        user = self._users.get(username) if isinstance(username, str) else None
        if user is None:
            return "USER_DELETE_RESPONSE", {
                "success": False,
                "error_code": "USER_NOT_FOUND",
                "message": "User not found",
            }
        if session.user is not None and session.user.username == username:
            return "USER_DELETE_RESPONSE", {
                "success": False,
                "error_code": "CANNOT_DELETE_SELF",
                "message": "Cannot delete your own account.",
            }
        self._users.pop(username, None)
        self._players.pop(user.player.ID, None)
        User._existing_usernames.discard(username)
        self._audit("USER_DELETE", session, username)
        return "USER_DELETE_RESPONSE", {
            "success": True,
            "username": username,
            "message": "User account deleted successfully",
        }

    def _handle_user_list(
        self, session: ClientSession, payload: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Handles a ``USER_LIST`` request (connected users).

        Args:
            session (ClientSession): The originating session.
            payload (Dict[str, Any]): The request payload.

        Returns:
            Tuple[str, Dict[str, Any]]: The response type and payload.
        """
        seen: Set[str] = set()
        users = []
        for client in self._sessions.values():
            if client.user is None or client.user.username in seen:
                continue
            seen.add(client.user.username)
            users.append({"username": client.user.username, "role": client.user.role.name})
        return "USER_LIST_RESPONSE", {"success": True, "users": users}

    def _handle_user_list_all(
        self, session: ClientSession, payload: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Handles a ``USER_LIST_ALL`` request (admin: every account).

        Args:
            session (ClientSession): The originating session.
            payload (Dict[str, Any]): The request payload.

        Returns:
            Tuple[str, Dict[str, Any]]: The response type and payload.
        """
        users = [
            {
                "username": user.username,
                "role": user.role.name,
                "managed_groups": list(user.groups_id),
            }
            for user in self._users.values()
        ]
        return "USER_LIST_ALL_RESPONSE", {"success": True, "users": users}

    # ------------------------------------------------------------------ #
    # Game helpers
    # ------------------------------------------------------------------ #
    def _game_summary(self, game: Game) -> Dict[str, Any]:
        """Builds the public summary of a game.

        Args:
            game (Game): The game to summarize.

        Returns:
            Dict[str, Any]: The summary used in list and notification messages.
        """
        return {
            "game_id": game.ID,
            "name": game.name,
            "state": game.game_state.name,
            "players_count": len(game.players),
            "max_players": getattr(game, "_max_players", None),
            "observers_count": len(game.observers),
            "max_observers": getattr(game, "_max_observers", None),
            "requires_password": game.hash is not None,
        }

    def _resolve_player(
        self, session: ClientSession, player_id: Optional[str]
    ) -> Optional[Player]:
        """Resolves the player object targeted by a request.

        Args:
            session (ClientSession): The originating session.
            player_id (str | None): The explicit player ID, if any.

        Returns:
            Player | None: The resolved player, or ``None`` if it cannot be
            determined.
        """
        if player_id is None:
            player_id = session.resolve_default_player_id()
        if player_id is None:
            return None
        return self._players.get(player_id)

    def _groups_of_game(self, game_id: str) -> List[str]:
        """Returns the IDs of the groups that contain a given game.

        Args:
            game_id (str): The game ID to look up.

        Returns:
            List[str]: The matching group IDs.
        """
        return [
            group.ID
            for group in self._groups.values()
            if any(g.ID == game_id for g in group.games)
        ]

    async def _notify_game_update(self, game: Game, changed_fields: List[str]) -> None:
        """Notifies group subscribers that a game summary changed.

        Args:
            game (Game): The updated game.
            changed_fields (List[str]): The list of changed summary fields.
        """
        summary = self._game_summary(game)
        for group_id in self._groups_of_game(game.ID):
            message = {
                "type": "GROUP_GAME_UPDATED",
                "version": PROTOCOL_VERSION,
                "payload": {
                    "group_id": group_id,
                    "game_id": game.ID,
                    "changed_fields": changed_fields,
                    "game": summary,
                },
            }
            await self._broadcast_group(group_id, message)

    # ------------------------------------------------------------------ #
    # Game handlers
    # ------------------------------------------------------------------ #
    async def _handle_game_create(
        self, session: ClientSession, payload: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Handles a ``GAME_CREATE`` request.

        Args:
            session (ClientSession): The originating session.
            payload (Dict[str, Any]): The request payload.

        Returns:
            Tuple[str, Dict[str, Any]]: The response type and payload.
        """
        name = payload.get("name")
        if not isinstance(name, str) or not name:
            return "GAME_CREATE_RESPONSE", {
                "success": False,
                "error_code": "INVALID_DATA",
                "message": "A game name is required.",
            }
        game = Game(
            name=name,
            max_players=payload.get("max_players"),
            max_observers=payload.get("max_observers"),
            password=payload.get("password"),
            turn_based=bool(payload.get("turn_based", False)),
        )
        attributes = payload.get("attributes")
        if isinstance(attributes, dict):
            game.dynamic_state.update(attributes)
        self._games[game.ID] = game
        self._game_roles[game.ID] = {}
        self._game_custom_state[game.ID] = {}
        self._game_creator_session[game.ID] = session.session_id
        return "GAME_CREATE_RESPONSE", {
            "success": True,
            "game_id": game.ID,
            "message": "Game created successfully",
        }

    def _handle_game_list(
        self, session: ClientSession, payload: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Handles a ``GAME_LIST`` request.

        Args:
            session (ClientSession): The originating session.
            payload (Dict[str, Any]): The request payload.

        Returns:
            Tuple[str, Dict[str, Any]]: The response type and payload.
        """
        group_id = payload.get("group_id")
        if group_id is not None:
            group = self._groups.get(group_id)
            if group is None:
                return "GAME_LIST_RESPONSE", {
                    "success": False,
                    "error_code": "GROUP_NOT_FOUND",
                    "message": "Group not found.",
                }
            games = [self._game_summary(game) for game in group.games]
        else:
            games = [self._game_summary(game) for game in self._games.values()]
        return "GAME_LIST_RESPONSE", {"success": True, "games": games}

    async def _handle_game_join(
        self, session: ClientSession, payload: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Handles a ``GAME_JOIN`` request (join as player or observer).

        Args:
            session (ClientSession): The originating session.
            payload (Dict[str, Any]): The request payload.

        Returns:
            Tuple[str, Dict[str, Any]]: The response type and payload.
        """
        game = self._games.get(payload.get("game_id"))
        if game is None:
            return "GAME_JOIN_RESPONSE", {
                "success": False,
                "error_code": "GAME_NOT_FOUND",
                "message": "Game not found.",
            }
        role = payload.get("role")
        if role not in ("PLAYER", "OBSERVER"):
            return "GAME_JOIN_RESPONSE", {
                "success": False,
                "error_code": "INVALID_ACTION",
                "message": "Invalid role.",
            }
        player = self._resolve_player(session, payload.get("player_id"))
        if player is None:
            return "GAME_JOIN_RESPONSE", {
                "success": False,
                "error_code": "PLAYER_NOT_FOUND",
                "message": "No player available for this session.",
            }
        roles = self._game_roles.setdefault(game.ID, {})
        if player.ID in roles:
            return "GAME_JOIN_RESPONSE", {
                "success": False,
                "error_code": "ALREADY_IN_GAME",
                "message": "Already in this game.",
            }
        password = payload.get("password")
        try:
            if role == "PLAYER":
                if game.game_state != GameState.PENDING:
                    return "GAME_JOIN_RESPONSE", {
                        "success": False,
                        "error_code": "GAME_ALREADY_STARTED",
                        "message": "Game already started.",
                    }
                game.join_game_as_player(player, password=password)
            else:
                game.join_game_as_observer(player, password=password)
        except PasswordError:
            return "GAME_JOIN_RESPONSE", {
                "success": False,
                "error_code": "INVALID_PASSWORD",
                "message": "Invalid game password.",
            }
        except GameIsFullError:
            return "GAME_JOIN_RESPONSE", {
                "success": False,
                "error_code": "GAME_FULL",
                "message": "Game is full.",
            }
        roles[player.ID] = role
        session.joined_games.add(game.ID)
        await self._notify_game_update(game, ["players_count", "observers_count"])
        return "GAME_JOIN_RESPONSE", {"success": True, "message": "Joined game successfully"}

    async def _handle_game_leave(
        self, session: ClientSession, payload: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Handles a ``GAME_LEAVE`` request.

        Args:
            session (ClientSession): The originating session.
            payload (Dict[str, Any]): The request payload.

        Returns:
            Tuple[str, Dict[str, Any]]: The response type and payload.
        """
        game = self._games.get(payload.get("game_id"))
        if game is None:
            return "GAME_LEAVE_RESPONSE", {
                "success": False,
                "error_code": "GAME_NOT_FOUND",
                "message": "Game not found.",
            }
        player_id = payload.get("player_id")
        if not isinstance(player_id, str) or player_id not in session.players:
            return "GAME_LEAVE_RESPONSE", {
                "success": False,
                "error_code": "PLAYER_NOT_FOUND",
                "message": "Player not found in this session.",
            }
        roles = self._game_roles.get(game.ID, {})
        if player_id not in roles:
            return "GAME_LEAVE_RESPONSE", {
                "success": False,
                "error_code": "NOT_IN_GAME",
                "message": "Player is not in this game.",
            }
        try:
            if roles[player_id] == "OBSERVER":
                game.remove_observer(player_id)
            else:
                game.remove_player(player_id)
        except PlayerNotFoundInGameError:
            pass
        roles.pop(player_id, None)
        if not any(pid in roles for pid in session.players):
            session.joined_games.discard(game.ID)
        await self._notify_game_update(game, ["players_count", "observers_count"])
        return "GAME_LEAVE_RESPONSE", {"success": True, "message": "Left game successfully"}

    async def _handle_game_control(
        self, session: ClientSession, payload: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Handles a ``GAME_CONTROL`` request (start, pause, resume, stop).

        Args:
            session (ClientSession): The originating session.
            payload (Dict[str, Any]): The request payload.

        Returns:
            Tuple[str, Dict[str, Any]]: The response type and payload.
        """
        game = self._games.get(payload.get("game_id"))
        if game is None:
            return "GAME_CONTROL_RESPONSE", {
                "success": False,
                "error_code": "GAME_NOT_FOUND",
                "message": "Game not found.",
            }
        if not self._can_control_game(session, game.ID):
            return "GAME_CONTROL_RESPONSE", {
                "success": False,
                "error_code": "INSUFFICIENT_PERMISSIONS",
                "message": "Cannot control this game.",
            }
        action = payload.get("action")
        try:
            if action == "START":
                game.start()
            elif action == "PAUSE":
                game.pause()
            elif action == "RESUME":
                game.resume()
            elif action == "STOP":
                game.stop()
            else:
                return "GAME_CONTROL_RESPONSE", {
                    "success": False,
                    "error_code": "INVALID_ACTION",
                    "message": "Unknown action.",
                }
        except GameAlreadyStartedError:
            return "GAME_CONTROL_RESPONSE", {
                "success": False,
                "error_code": "GAME_ALREADY_STARTED",
                "message": "Game already started.",
            }
        except (GameNotStartedError, GameNotPausedError, GameIsFinishedError):
            return "GAME_CONTROL_RESPONSE", {
                "success": False,
                "error_code": "GAME_NOT_STARTED",
                "message": "Game is not in the required state.",
            }
        await self._broadcast_game(
            game.ID,
            {
                "type": "GAME_STATE_CHANGED",
                "version": PROTOCOL_VERSION,
                "payload": {"game_id": game.ID, "new_status": game.game_state.name},
            },
        )
        await self._notify_game_update(game, ["state"])
        return "GAME_CONTROL_RESPONSE", {
            "success": True,
            "message": f"Action {action} executed successfully",
        }

    def _can_control_game(self, session: ClientSession, game_id: str) -> bool:
        """Checks whether a session may control a given game.

        Args:
            session (ClientSession): The originating session.
            game_id (str): The game ID concerned.

        Returns:
            bool: ``True`` if the session created the game or has sufficient
            administrative rights.
        """
        if self._game_creator_session.get(game_id) == session.session_id:
            return True
        if session.access_level >= AccessLevel.ADMIN:
            return True
        if session.access_level >= AccessLevel.GROUP_ADMIN and session.user is not None:
            managed = set(session.user.groups_id)
            return any(gid in managed for gid in self._groups_of_game(game_id))
        return False

    async def _handle_game_player_order(
        self, session: ClientSession, payload: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Handles a ``GAME_PLAYER_ORDER`` request (reverse or set rank).

        Args:
            session (ClientSession): The originating session.
            payload (Dict[str, Any]): The request payload.

        Returns:
            Tuple[str, Dict[str, Any]]: The response type and payload.
        """
        game = self._games.get(payload.get("game_id"))
        if game is None:
            return "GAME_PLAYER_ORDER_RESPONSE", {
                "success": False,
                "error_code": "GAME_NOT_FOUND",
                "message": "Game not found.",
            }
        if not self._can_control_game(session, game.ID):
            return "GAME_PLAYER_ORDER_RESPONSE", {
                "success": False,
                "error_code": "INSUFFICIENT_PERMISSIONS",
                "message": "Cannot modify player order.",
            }
        action = payload.get("action")
        try:
            if action == "REVERSE":
                game.reverse_order()
            elif action == "SET_RANK":
                game.set_player_rank(payload.get("target_player_id"), payload.get("rank"))
            else:
                return "GAME_PLAYER_ORDER_RESPONSE", {
                    "success": False,
                    "error_code": "INVALID_ACTION",
                    "message": "Unknown action.",
                }
        except GameNotTurnBasedError:
            return "GAME_PLAYER_ORDER_RESPONSE", {
                "success": False,
                "error_code": "GAME_NOT_TURN_BASED",
                "message": "Game is not turn-based.",
            }
        except GameIsFinishedError:
            return "GAME_PLAYER_ORDER_RESPONSE", {
                "success": False,
                "error_code": "GAME_FINISHED",
                "message": "Game is finished.",
            }
        except PlayerNotFoundInGameError:
            return "GAME_PLAYER_ORDER_RESPONSE", {
                "success": False,
                "error_code": "PLAYER_NOT_FOUND",
                "message": "Target player not found in this game.",
            }
        except (IndexError, TypeError):
            return "GAME_PLAYER_ORDER_RESPONSE", {
                "success": False,
                "error_code": "INVALID_RANK",
                "message": "Invalid rank.",
            }
        return "GAME_PLAYER_ORDER_RESPONSE", {
            "success": True,
            "message": "Player order updated successfully",
        }

    async def _handle_game_action(
        self, session: ClientSession, payload: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Handles a ``GAME_ACTION`` request and broadcasts the resulting event.

        Args:
            session (ClientSession): The originating session.
            payload (Dict[str, Any]): The request payload.

        Returns:
            Tuple[str, Dict[str, Any]]: The response type and payload.
        """
        game = self._games.get(payload.get("game_id"))
        if game is None:
            return "GAME_ACTION_RESPONSE", {
                "success": False,
                "error_code": "GAME_NOT_FOUND",
                "message": "Game not found.",
            }
        player_id = payload.get("player_id")
        roles = self._game_roles.get(game.ID, {})
        if not isinstance(player_id, str) or player_id not in roles:
            return "GAME_ACTION_RESPONSE", {
                "success": False,
                "error_code": "PLAYER_NOT_FOUND",
                "message": "Player is not in this game.",
            }
        if game.game_state == GameState.PAUSING:
            return "GAME_ACTION_RESPONSE", {
                "success": False,
                "error_code": "GAME_PAUSED",
                "message": "Game is paused.",
            }
        if (
            game.turn_based
            and roles.get(player_id) == "PLAYER"
            and game.current_player is not None
            and game.current_player.ID != player_id
        ):
            return "GAME_ACTION_RESPONSE", {
                "success": False,
                "error_code": "NOT_YOUR_TURN",
                "message": "It is not your turn.",
            }
        await self._broadcast_game(
            game.ID,
            {
                "type": "GAME_EVENT",
                "version": PROTOCOL_VERSION,
                "payload": {
                    "game_id": game.ID,
                    "player_id": player_id,
                    "action_type": payload.get("action_type"),
                    "data": payload.get("data"),
                },
            },
        )
        return "GAME_ACTION_RESPONSE", {"success": True, "message": "Action accepted"}

    async def _handle_game_state_set(
        self, session: ClientSession, payload: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Handles a ``GAME_STATE_SET`` request (update custom state).

        Args:
            session (ClientSession): The originating session.
            payload (Dict[str, Any]): The request payload.

        Returns:
            Tuple[str, Dict[str, Any]]: The response type and payload.
        """
        game = self._games.get(payload.get("game_id"))
        if game is None:
            return "GAME_STATE_SET_RESPONSE", {
                "success": False,
                "error_code": "GAME_NOT_FOUND",
                "message": "Game not found.",
            }
        state = payload.get("state")
        if not isinstance(state, dict):
            return "GAME_STATE_SET_RESPONSE", {
                "success": False,
                "error_code": "INVALID_ACTION",
                "message": "Invalid state.",
            }
        self._game_custom_state.setdefault(game.ID, {}).update(state)
        await self._broadcast_game(
            game.ID,
            {
                "type": "GAME_STATE_CHANGED",
                "version": PROTOCOL_VERSION,
                "payload": {
                    "game_id": game.ID,
                    "custom_state": self._game_custom_state[game.ID],
                },
            },
        )
        return "GAME_STATE_SET_RESPONSE", {"success": True, "message": "State updated"}

    def _handle_game_state_get(
        self, session: ClientSession, payload: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Handles a ``GAME_STATE_GET`` request (retrieve full state).

        Args:
            session (ClientSession): The originating session.
            payload (Dict[str, Any]): The request payload.

        Returns:
            Tuple[str, Dict[str, Any]]: The response type and payload.
        """
        game = self._games.get(payload.get("game_id"))
        if game is None:
            return "GAME_STATE_GET_RESPONSE", {
                "success": False,
                "error_code": "GAME_NOT_FOUND",
                "message": "Game not found.",
            }
        current = game.current_player
        return "GAME_STATE_GET_RESPONSE", {
            "success": True,
            "state": {
                "status": game.game_state.name,
                "custom": self._game_custom_state.get(game.ID, {}),
                "current_player_id": current.ID if current is not None else None,
            },
        }

    async def _handle_game_next_turn(
        self, session: ClientSession, payload: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Handles a ``GAME_NEXT_TURN`` request.

        Args:
            session (ClientSession): The originating session.
            payload (Dict[str, Any]): The request payload.

        Returns:
            Tuple[str, Dict[str, Any]]: The response type and payload.
        """
        game = self._games.get(payload.get("game_id"))
        if game is None:
            return "GAME_NEXT_TURN_RESPONSE", {
                "success": False,
                "error_code": "GAME_NOT_FOUND",
                "message": "Game not found.",
            }
        if not game.turn_based:
            return "GAME_NEXT_TURN_RESPONSE", {
                "success": False,
                "error_code": "GAME_NOT_TURN_BASED",
                "message": "Game is not turn-based.",
            }
        player_id = payload.get("player_id")
        if game.current_player is not None and game.current_player.ID != player_id:
            return "GAME_NEXT_TURN_RESPONSE", {
                "success": False,
                "error_code": "NOT_YOUR_TURN",
                "message": "It is not your turn.",
            }
        try:
            game.next_turn()
        except (GameNotStartedError, GameIsFinishedError, GameNotTurnBasedError):
            return "GAME_NEXT_TURN_RESPONSE", {
                "success": False,
                "error_code": "GAME_NOT_TURN_BASED",
                "message": "Cannot advance the turn.",
            }
        current = game.current_player
        current_id = current.ID if current is not None else None
        await self._broadcast_game(
            game.ID,
            {
                "type": "GAME_TURN_CHANGED",
                "version": PROTOCOL_VERSION,
                "payload": {"game_id": game.ID, "current_player_id": current_id},
            },
        )
        return "GAME_NEXT_TURN_RESPONSE", {
            "success": True,
            "current_player_id": current_id,
            "message": "Turn advanced to next player",
        }

    async def _handle_game_kick(
        self, session: ClientSession, payload: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Handles a ``GAME_KICK`` request (force removal of a participant).

        Args:
            session (ClientSession): The originating session.
            payload (Dict[str, Any]): The request payload.

        Returns:
            Tuple[str, Dict[str, Any]]: The response type and payload.
        """
        game = self._games.get(payload.get("game_id"))
        if game is None:
            return "GAME_KICK_RESPONSE", {
                "success": False,
                "error_code": "GAME_NOT_FOUND",
                "message": "Game not found.",
            }
        if not self._can_control_game(session, game.ID):
            return "GAME_KICK_RESPONSE", {
                "success": False,
                "error_code": "INSUFFICIENT_PERMISSIONS",
                "message": "Cannot kick from this game.",
            }
        target_id = payload.get("target_id")
        roles = self._game_roles.get(game.ID, {})
        if not isinstance(target_id, str) or target_id not in self._players:
            return "GAME_KICK_RESPONSE", {
                "success": False,
                "error_code": "PLAYER_NOT_FOUND",
                "message": "Target not found.",
            }
        if target_id not in roles:
            return "GAME_KICK_RESPONSE", {
                "success": False,
                "error_code": "NOT_IN_GAME",
                "message": "Target is not in this game.",
            }
        try:
            if roles[target_id] == "OBSERVER":
                game.remove_observer(target_id)
            else:
                game.remove_player(target_id)
        except PlayerNotFoundInGameError:
            pass
        roles.pop(target_id, None)
        await self._notify_game_update(game, ["players_count", "observers_count"])
        return "GAME_KICK_RESPONSE", {
            "success": True,
            "game_id": game.ID,
            "target_id": target_id,
            "message": "Player kicked successfully",
        }

    # ------------------------------------------------------------------ #
    # Group handlers
    # ------------------------------------------------------------------ #
    def _handle_group_create(
        self, session: ClientSession, payload: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Handles a ``GROUP_CREATE`` request.

        Args:
            session (ClientSession): The originating session.
            payload (Dict[str, Any]): The request payload.

        Returns:
            Tuple[str, Dict[str, Any]]: The response type and payload.
        """
        name = payload.get("name")
        if not isinstance(name, str) or not name:
            return "GROUP_CREATE_RESPONSE", {
                "success": False,
                "error_code": "INVALID_DATA",
                "message": "A group name is required.",
            }
        attributes = payload.get("attributes")
        group = GameGroup(name=name, **(attributes if isinstance(attributes, dict) else {}))
        self._groups[group.ID] = group
        self._audit("GROUP_CREATE", session, group.ID)
        return "GROUP_CREATE_RESPONSE", {
            "success": True,
            "group_id": group.ID,
            "message": "Group created successfully",
        }

    def _handle_group_list(
        self, session: ClientSession, payload: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Handles a ``GROUP_LIST`` request.

        Args:
            session (ClientSession): The originating session.
            payload (Dict[str, Any]): The request payload.

        Returns:
            Tuple[str, Dict[str, Any]]: The response type and payload.
        """
        groups = [
            {"group_id": group.ID, "name": group.name, "games_count": len(group.games)}
            for group in self._groups.values()
        ]
        return "GROUP_LIST_RESPONSE", {"success": True, "groups": groups}

    def _handle_group_subscribe(
        self, session: ClientSession, payload: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Handles a ``GROUP_SUBSCRIBE`` request.

        Args:
            session (ClientSession): The originating session.
            payload (Dict[str, Any]): The request payload.

        Returns:
            Tuple[str, Dict[str, Any]]: The response type and payload.
        """
        group_id = payload.get("group_id")
        if group_id not in self._groups:
            return "GROUP_SUBSCRIBE_RESPONSE", {
                "success": False,
                "error_code": "GROUP_NOT_FOUND",
                "message": "Group not found.",
            }
        if group_id in session.subscribed_groups:
            return "GROUP_SUBSCRIBE_RESPONSE", {
                "success": False,
                "error_code": "ALREADY_SUBSCRIBED",
                "message": "Already subscribed to this group.",
            }
        session.subscribed_groups.add(group_id)
        return "GROUP_SUBSCRIBE_RESPONSE", {
            "success": True,
            "group_id": group_id,
            "message": "Subscribed to group successfully",
        }

    def _handle_group_unsubscribe(
        self, session: ClientSession, payload: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Handles a ``GROUP_UNSUBSCRIBE`` request.

        Args:
            session (ClientSession): The originating session.
            payload (Dict[str, Any]): The request payload.

        Returns:
            Tuple[str, Dict[str, Any]]: The response type and payload.
        """
        group_id = payload.get("group_id")
        if group_id not in self._groups:
            return "GROUP_UNSUBSCRIBE_RESPONSE", {
                "success": False,
                "error_code": "GROUP_NOT_FOUND",
                "message": "Group not found.",
            }
        if group_id not in session.subscribed_groups:
            return "GROUP_UNSUBSCRIBE_RESPONSE", {
                "success": False,
                "error_code": "NOT_SUBSCRIBED",
                "message": "Not subscribed to this group.",
            }
        session.subscribed_groups.discard(group_id)
        return "GROUP_UNSUBSCRIBE_RESPONSE", {
            "success": True,
            "group_id": group_id,
            "message": "Unsubscribed from group successfully",
        }

    def _can_admin_group(self, session: ClientSession, group_id: str) -> bool:
        """Checks whether a session can administer a given group.

        Args:
            session (ClientSession): The originating session.
            group_id (str): The group ID concerned.

        Returns:
            bool: ``True`` if the session is a server admin or a group admin of
            this group.
        """
        if session.access_level >= AccessLevel.ADMIN:
            return True
        if session.access_level >= AccessLevel.GROUP_ADMIN and session.user is not None:
            return group_id in session.user.groups_id
        return False

    async def _handle_group_add_game(
        self, session: ClientSession, payload: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Handles a ``GROUP_ADD_GAME`` request.

        Args:
            session (ClientSession): The originating session.
            payload (Dict[str, Any]): The request payload.

        Returns:
            Tuple[str, Dict[str, Any]]: The response type and payload.
        """
        group = self._groups.get(payload.get("group_id"))
        if group is None:
            return "GROUP_ADD_GAME_RESPONSE", {
                "success": False,
                "error_code": "GROUP_NOT_FOUND",
                "message": "Group not found.",
            }
        if not self._can_admin_group(session, group.ID):
            return "GROUP_ADD_GAME_RESPONSE", {
                "success": False,
                "error_code": "INSUFFICIENT_PERMISSIONS",
                "message": "Cannot modify this group.",
            }
        game = self._games.get(payload.get("game_id"))
        if game is None:
            return "GROUP_ADD_GAME_RESPONSE", {
                "success": False,
                "error_code": "GAME_NOT_FOUND",
                "message": "Game not found.",
            }
        group.add_game(game)
        await self._broadcast_group(
            group.ID,
            {
                "type": "GROUP_GAME_ADDED",
                "version": PROTOCOL_VERSION,
                "payload": {"group_id": group.ID, "game": self._game_summary(game)},
            },
        )
        return "GROUP_ADD_GAME_RESPONSE", {
            "success": True,
            "message": "Game added to group successfully",
        }

    async def _handle_group_remove_game(
        self, session: ClientSession, payload: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Handles a ``GROUP_REMOVE_GAME`` request.

        Args:
            session (ClientSession): The originating session.
            payload (Dict[str, Any]): The request payload.

        Returns:
            Tuple[str, Dict[str, Any]]: The response type and payload.
        """
        group = self._groups.get(payload.get("group_id"))
        if group is None:
            return "GROUP_REMOVE_GAME_RESPONSE", {
                "success": False,
                "error_code": "GROUP_NOT_FOUND",
                "message": "Group not found.",
            }
        if not self._can_admin_group(session, group.ID):
            return "GROUP_REMOVE_GAME_RESPONSE", {
                "success": False,
                "error_code": "INSUFFICIENT_PERMISSIONS",
                "message": "Cannot modify this group.",
            }
        game_id = payload.get("game_id")
        game = self._games.get(game_id)
        game_name = game.name if game is not None else None
        try:
            group.remove_game(game_id)
        except GameNotFoundInGroupError:
            return "GROUP_REMOVE_GAME_RESPONSE", {
                "success": False,
                "error_code": "GAME_NOT_FOUND_IN_GROUP",
                "message": "Game not found in this group.",
            }
        await self._broadcast_group(
            group.ID,
            {
                "type": "GROUP_GAME_REMOVED",
                "version": PROTOCOL_VERSION,
                "payload": {
                    "group_id": group.ID,
                    "game_id": game_id,
                    "game_name": game_name,
                },
            },
        )
        return "GROUP_REMOVE_GAME_RESPONSE", {
            "success": True,
            "message": "Game removed from group successfully",
        }

    def _handle_group_delete(
        self, session: ClientSession, payload: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Handles a ``GROUP_DELETE`` request.

        Args:
            session (ClientSession): The originating session.
            payload (Dict[str, Any]): The request payload.

        Returns:
            Tuple[str, Dict[str, Any]]: The response type and payload.
        """
        group_id = payload.get("group_id")
        if group_id not in self._groups:
            return "GROUP_DELETE_RESPONSE", {
                "success": False,
                "error_code": "GROUP_NOT_FOUND",
                "message": "Group not found.",
            }
        self._groups.pop(group_id, None)
        for client in self._sessions.values():
            client.subscribed_groups.discard(group_id)
        self._audit("GROUP_DELETE", session, group_id)
        return "GROUP_DELETE_RESPONSE", {
            "success": True,
            "message": "Group deleted successfully",
        }

    def _handle_group_game_list_all(
        self, session: ClientSession, payload: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Handles a ``GROUP_GAME_LIST_ALL`` request.

        Args:
            session (ClientSession): The originating session.
            payload (Dict[str, Any]): The request payload.

        Returns:
            Tuple[str, Dict[str, Any]]: The response type and payload.
        """
        group = self._groups.get(payload.get("group_id"))
        if group is None:
            return "GROUP_GAME_LIST_ALL_RESPONSE", {
                "success": False,
                "error_code": "GROUP_NOT_FOUND",
                "message": "Group not found.",
            }
        if not self._can_admin_group(session, group.ID):
            return "GROUP_GAME_LIST_ALL_RESPONSE", {
                "success": False,
                "error_code": "INSUFFICIENT_PERMISSIONS",
                "message": "Cannot inspect this group.",
            }
        games = [self._game_summary(game) for game in group.games]
        return "GROUP_GAME_LIST_ALL_RESPONSE", {"success": True, "games": games}

    # ------------------------------------------------------------------ #
    # Server administration handlers
    # ------------------------------------------------------------------ #
    def _audit(self, action: str, session: ClientSession, target: str) -> None:
        """Appends an entry to the in-memory audit log.

        Args:
            action (str): The audited action name.
            session (ClientSession): The session that triggered the action.
            target (str): The main target of the action.
        """
        actor = session.user.username if session.user is not None else session.session_id
        self._audit_log.append(
            {
                "timestamp": int(time.time()),
                "actor": actor,
                "action": action,
                "target": target,
                "severity": "INFO",
                "summary": f"{action} on {target}",
            }
        )

    def _handle_server_info_get(
        self, session: ClientSession, payload: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Handles a ``SERVER_INFO_GET`` request.

        Args:
            session (ClientSession): The originating session.
            payload (Dict[str, Any]): The request payload.

        Returns:
            Tuple[str, Dict[str, Any]]: The response type and payload.
        """
        uptime = time.monotonic() - self._start_time if self._running else 0.0
        return "SERVER_INFO_GET_RESPONSE", {
            "success": True,
            "info": {
                "name": self.name,
                "uptime": uptime,
                "connected_clients": len(self._sessions),
                "use_tls": self.use_tls,
                "user_registration_enabled": self.user_registration_enabled,
            },
        }

    def _handle_server_config_get(
        self, session: ClientSession, payload: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Handles a ``SERVER_CONFIG_GET`` request.

        Args:
            session (ClientSession): The originating session.
            payload (Dict[str, Any]): The request payload.

        Returns:
            Tuple[str, Dict[str, Any]]: The response type and payload.
        """
        return "SERVER_CONFIG_GET_RESPONSE", {
            "success": True,
            "config": {
                "user_registration_enabled": self.user_registration_enabled,
                "hidden": self.hidden,
                "server_password_set": self._server_hash is not None,
                "admin_password_set": self._admin_hash is not None,
            },
        }

    def _handle_server_config_set(
        self, session: ClientSession, payload: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Handles a ``SERVER_CONFIG_SET`` request.

        Args:
            session (ClientSession): The originating session.
            payload (Dict[str, Any]): The request payload.

        Returns:
            Tuple[str, Dict[str, Any]]: The response type and payload.
        """
        updated: List[str] = []
        if "user_registration_enabled" in payload:
            value = payload["user_registration_enabled"]
            if not isinstance(value, bool):
                return "SERVER_CONFIG_SET_RESPONSE", {
                    "success": False,
                    "error_code": "INVALID_DATA",
                    "message": "user_registration_enabled must be a boolean.",
                }
            self.user_registration_enabled = value
            updated.append("user_registration_enabled")
        if "hidden" in payload:
            value = payload["hidden"]
            if not isinstance(value, bool):
                return "SERVER_CONFIG_SET_RESPONSE", {
                    "success": False,
                    "error_code": "INVALID_DATA",
                    "message": "hidden must be a boolean.",
                }
            self.hidden = value
            updated.append("hidden")
        if isinstance(payload.get("server_password"), str):
            self._server_hash = bcrypt.hashpw(
                payload["server_password"].encode(), bcrypt.gensalt()
            ).decode()
            updated.append("server_password")
        if isinstance(payload.get("admin_password"), str):
            self._admin_hash = bcrypt.hashpw(
                payload["admin_password"].encode(), bcrypt.gensalt()
            ).decode()
            updated.append("admin_password")
        self._audit("SERVER_CONFIG_SET", session, "server")
        return "SERVER_CONFIG_SET_RESPONSE", {
            "success": True,
            "updated_fields": updated,
            "message": "Configuration updated successfully",
        }

    def _handle_server_audit_log_get(
        self, session: ClientSession, payload: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Handles a ``SERVER_AUDIT_LOG_GET`` request.

        Args:
            session (ClientSession): The originating session.
            payload (Dict[str, Any]): The request payload.

        Returns:
            Tuple[str, Dict[str, Any]]: The response type and payload.
        """
        limit = payload.get("limit")
        if limit is not None and (not isinstance(limit, int) or limit < 0):
            return "SERVER_AUDIT_LOG_GET_RESPONSE", {
                "success": False,
                "error_code": "INVALID_DATA",
                "message": "Invalid limit.",
            }
        entries = self._audit_log[-limit:] if isinstance(limit, int) and limit else list(self._audit_log)
        return "SERVER_AUDIT_LOG_GET_RESPONSE", {"success": True, "entries": entries}

    def _handle_server_persistence_save(
        self, session: ClientSession, payload: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Handles a ``SERVER_PERSISTENCE_SAVE`` request.

        Args:
            session (ClientSession): The originating session.
            payload (Dict[str, Any]): The request payload.

        Returns:
            Tuple[str, Dict[str, Any]]: The response type and payload.
        """
        if self.persistence_mode is None:
            return "SERVER_PERSISTENCE_SAVE_RESPONSE", {
                "success": False,
                "error_code": "PERSISTENCE_ERROR",
                "message": "Persistence is disabled.",
            }
        self._save_persistence()
        self._audit("SERVER_PERSISTENCE_SAVE", session, "server")
        return "SERVER_PERSISTENCE_SAVE_RESPONSE", {
            "success": True,
            "saved_at": int(time.time()),
            "message": "Persistent data saved successfully",
        }

    def _handle_server_persistence_reload(
        self, session: ClientSession, payload: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Handles a ``SERVER_PERSISTENCE_RELOAD`` request.

        Args:
            session (ClientSession): The originating session.
            payload (Dict[str, Any]): The request payload.

        Returns:
            Tuple[str, Dict[str, Any]]: The response type and payload.
        """
        if self.persistence_mode is None:
            return "SERVER_PERSISTENCE_RELOAD_RESPONSE", {
                "success": False,
                "error_code": "PERSISTENCE_ERROR",
                "message": "Persistence is disabled.",
            }
        self._save = None
        self._load_persistence()
        self._audit("SERVER_PERSISTENCE_RELOAD", session, "server")
        return "SERVER_PERSISTENCE_RELOAD_RESPONSE", {
            "success": True,
            "reloaded_at": int(time.time()),
            "message": "Persistent data reloaded successfully",
        }

    async def _handle_server_control(
        self, session: ClientSession, payload: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Handles a ``SERVER_CONTROL`` request (stop or restart).

        Args:
            session (ClientSession): The originating session.
            payload (Dict[str, Any]): The request payload.

        Returns:
            Tuple[str, Dict[str, Any]]: The response type and payload.
        """
        action = payload.get("action")
        if action not in ("STOP", "RESTART"):
            return "SERVER_CONTROL_RESPONSE", {
                "success": False,
                "error_code": "INVALID_ACTION",
                "message": "Unknown action.",
            }
        delay = payload.get("delay", 0)
        self._audit("SERVER_CONTROL", session, action)

        async def _deferred() -> None:
            """Performs the deferred stop or restart operation."""
            if isinstance(delay, (int, float)) and delay > 0:
                await asyncio.sleep(delay)
            if action == "STOP":
                await self.stop()
            else:
                await self.restart()

        asyncio.ensure_future(_deferred())
        verb = "shutting down" if action == "STOP" else "restarting"
        return "SERVER_CONTROL_RESPONSE", {
            "success": True,
            "message": f"Server is {verb}",
        }
