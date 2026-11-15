"""Client-side logic for the multiplayer library.

This module implements the :class:`GameClient` class, i.e. the client side of
the client/server protocol (version 2). It is responsible for discovering
servers on the local network, connecting to a :class:`~multiplayer.server.GameServer`
(optionally over TLS), authenticating, exchanging requests/responses and
dispatching the notifications spontaneously sent by the server.

The transport layer relies on blocking sockets:

* TCP is used for the main communication. Each message is framed with a 4-byte
  big-endian length header followed by the serialized payload (JSON or
  MessagePack).
* UDP multicast is used for the optional network discovery feature.
"""
import json
import socket
import ssl
import struct
import threading
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from . import UserRole
from .exceptions import (
    MultiplayerError,
    PasswordError,
    UnsupportedFeatureError,
    UserNotFoundError,
)
from .game import Player, User

try:
    import msgpack

    _MSGPACK_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    msgpack = None
    _MSGPACK_AVAILABLE = False

# Protocol-wide constants (kept in sync with the server implementation).
PROTOCOL_VERSION = 2
# Revision assumed for a server that does not announce its revision.
BASE_REVISION = "2.0"
# Optional protocol feature used by the player factory methods.
FEATURE_PLAYER_FACTORY = "player_factory"
SERVICE_NAME = "multiplayer_server"
LENGTH_HEADER_SIZE = 4

# Default network configuration values.
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 65432
DEFAULT_MULTICAST_GROUP = "239.255.0.1"
DEFAULT_MULTICAST_PORT = 65434

# Mapping from the role name advertised by the server to the UserRole enum.
_ROLE_BY_NAME: Dict[str, UserRole] = {role.name: role for role in UserRole}

# Message types that are sent spontaneously by the server (notifications).
NOTIFICATION_TYPES = frozenset(
    {
        "SERVER_SHUTDOWN",
        "GROUP_GAME_ADDED",
        "GROUP_GAME_REMOVED",
        "GROUP_GAME_UPDATED",
        "GAME_EVENT",
        "GAME_STATE_CHANGED",
        "GAME_TURN_CHANGED",
        "GAME_FACTORY_UPDATED",
    }
)


def _build_user_from_payload(payload: Dict[str, Any]) -> User:
    """Builds a local :class:`User` from a successful ``AUTH_RESPONSE`` payload.

    The user is created without triggering the side effects of
    :class:`User` instantiation (username registration, password hashing),
    because the client only mirrors the account already validated by the
    server.

    Args:
        payload (Dict[str, Any]): The payload of a successful ``AUTH_RESPONSE``.

    Returns:
        User: A locally reconstructed user account mirroring the server one.
    """
    user = User.__new__(User)
    user._id = str(uuid.uuid4())
    user._username = payload.get("username", "")
    user._hash = ""
    user.email = ""
    user.role = _ROLE_BY_NAME.get(payload.get("role", ""), UserRole.PLAYER)
    user._groups_id = []
    players = payload.get("players")
    user._players_id = [
        player["player_id"]
        for player in (players if isinstance(players, list) else [])
        if isinstance(player, dict) and isinstance(player.get("player_id"), str)
    ]
    return user


class GameClient:
    """Connects to and communicates with a :class:`~multiplayer.server.GameServer`.

    The client is able to discover servers on the local network, open a
    (optionally TLS-secured) TCP connection, authenticate, send arbitrary
    protocol requests and dispatch the notifications spontaneously emitted by
    the server to registered callbacks.

    Attributes:
        host (str): The IPv4 address or host name of the server.
        port (int): The TCP port of the server.
        use_tls (bool): Whether the TCP connection is secured with TLS.
        is_connected (bool): Whether the client is currently connected.
        session_user (User | None): The user associated with the current
            session, updated when the user authenticates.
        server_revision (str | None): The protocol revision announced by the
            server, ``None`` while not connected.
        server_features (tuple[str, ...]): The optional protocol features
            offered by the server.
    """

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        use_tls: bool = False,
        tls_ca_path: Optional[Path] = None,
    ):
        """Initializes a new multiplayer game client.

        Args:
            host (str): IPv4 address or host name of the server. Defaults to
                ``"127.0.0.1"``.
            port (int): TCP port of the server. Defaults to ``65432``.
            use_tls (bool): Enable TLS for the connection. Defaults to False.
            tls_ca_path (Path | None): Path to the CA certificate (or the
                server self-signed certificate) used to validate the TLS
                connection. When ``None``, the system trust store is used.
                Defaults to ``None``.

        Raises:
            ValueError: If the TCP port is not a valid port number.
        """
        if not isinstance(port, int) or not 0 <= port <= 65535:
            raise ValueError(f"Invalid TCP port: {port}")

        self.host: str = host
        self.port: int = port
        self.use_tls: bool = use_tls
        self.__tls_ca_path: Optional[Path] = Path(tls_ca_path) if tls_ca_path else None
        self.__socket: Optional[socket.socket] = None
        self.__send_lock: threading.Lock = threading.Lock()
        self.__pending_lock: threading.Lock = threading.Lock()
        self.__pending: Dict[str, Dict[str, Any]] = {}
        self.__pending_events: Dict[str, threading.Event] = {}
        self.__callbacks_lock: threading.Lock = threading.Lock()
        self.__type_callbacks: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}
        self.__global_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self.__receiver_thread: Optional[threading.Thread] = None
        self.__running: bool = False
        self.__is_connected: bool = False
        self.__session_user: Optional[User] = None
        self.__server_revision: Optional[str] = None
        self.__server_features: Tuple[str, ...] = ()

    # ------------------------------------------------------------------ #
    # Read-only properties
    # ------------------------------------------------------------------ #
    @property
    def server_revision(self) -> Optional[str]:
        """The protocol revision announced by the server.

        Returns:
            str | None: The revision (e.g. ``"2.1"``), ``"2.0"`` if the server
            does not support ``PROTOCOL_INFO``, or ``None`` while not connected.
        """
        return self.__server_revision

    @property
    def server_features(self) -> Tuple[str, ...]:
        """The optional protocol features offered by the server.

        Returns:
            tuple[str, ...]: The features (e.g. ``("player_factory",)``).
        """
        return self.__server_features

    @property
    def tls_ca_path(self) -> Optional[Path]:
        """The path to the TLS validation certificate.

        Returns:
            Path | None: The configured CA/server certificate path, or ``None``
            when the system trust store is used.
        """
        return self.__tls_ca_path

    @property
    def is_connected(self) -> bool:
        """Whether the client is currently connected to the server.

        Returns:
            bool: ``True`` if a connection is currently open.
        """
        return self.__is_connected

    @property
    def session_user(self) -> Optional[User]:
        """The user associated with the current session.

        Returns:
            User | None: The authenticated user, or ``None`` if no user has
            authenticated during the current connection.
        """
        return self.__session_user

    # ------------------------------------------------------------------ #
    # Serialization and framing
    # ------------------------------------------------------------------ #
    @staticmethod
    def _encode_message(message: Dict[str, Any], binary: bool = False) -> bytes:
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

    @staticmethod
    def _recv_exact(sock: socket.socket, size: int) -> Optional[bytes]:
        """Reads exactly ``size`` bytes from a blocking socket.

        Args:
            sock (socket.socket): The socket to read from.
            size (int): The exact number of bytes to read.

        Returns:
            bytes | None: The bytes read, or ``None`` if the connection was
            closed before ``size`` bytes could be read.
        """
        chunks = bytearray()
        while len(chunks) < size:
            try:
                chunk = sock.recv(size - len(chunks))
            except OSError:
                return None
            if not chunk:
                return None
            chunks.extend(chunk)
        return bytes(chunks)

    # ------------------------------------------------------------------ #
    # Discovery
    # ------------------------------------------------------------------ #
    @classmethod
    def discover(
        cls,
        timeout: float = 2.0,
        multicast_group: str = DEFAULT_MULTICAST_GROUP,
        multicast_port: int = DEFAULT_MULTICAST_PORT,
    ) -> List[Dict[str, Any]]:
        """Discovers the servers available on the local network.

        Sends a multicast discovery datagram over UDP and collects the unicast
        responses returned by the active servers until the timeout expires.

        Args:
            timeout (float): Maximum time to wait for responses, in seconds.
                Defaults to ``2.0``.
            multicast_group (str): The multicast address to query. Defaults to
                ``"239.255.0.1"``.
            multicast_port (int): The multicast UDP port. Defaults to ``65434``.

        Returns:
            List[Dict[str, Any]]: One dictionary per discovered server,
            containing its advertised information (name, host, port, etc.).
        """
        request = {
            "type": "DISCOVERY",
            "service_name": SERVICE_NAME,
            "version": PROTOCOL_VERSION,
        }
        data = json.dumps(request).encode("utf-8")

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        servers: List[Dict[str, Any]] = []
        seen: set = set()
        try:
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            sock.settimeout(timeout)
            sock.sendto(data, (multicast_group, multicast_port))
            while True:
                try:
                    raw, addr = sock.recvfrom(65535)
                except socket.timeout:
                    break
                except OSError:
                    break
                try:
                    message = json.loads(raw.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue
                if not isinstance(message, dict):
                    continue
                if message.get("type") != "DISCOVERY_RESPONSE":
                    continue
                if message.get("service_name") != SERVICE_NAME:
                    continue
                if message.get("version") != PROTOCOL_VERSION:
                    continue
                host = message.get("service_host")
                if not host or host in ("0.0.0.0", ""):
                    host = addr[0]
                info = {
                    "name": message.get("name", ""),
                    "host": host,
                    "port": message.get("service_port"),
                    "unencrypted_port": message.get("unencrypted_port"),
                    "use_tls": message.get("use_tls", False),
                    "password_required": message.get("password_required", False),
                    "revision": message.get("revision") or BASE_REVISION,
                }
                key = (info["host"], info["port"])
                if key in seen:
                    continue
                seen.add(key)
                servers.append(info)
        finally:
            sock.close()
        return servers

    # ------------------------------------------------------------------ #
    # Connection management
    # ------------------------------------------------------------------ #
    def connect(self) -> None:
        """Opens the TCP connection with the server.

        Uses ``host``, ``port`` and ``use_tls`` (together with ``tls_ca_path``
        when provided, otherwise the system root certificates) to establish the
        connection, then starts the background receiver used to dispatch
        notifications. Finally sends a ``PROTOCOL_INFO`` request to fill in
        :attr:`server_revision` and :attr:`server_features`; a revision 2.0
        server answering ``UNKNOWN_TYPE`` does not make the connection fail.

        Raises:
            ConnectionError: If the connection cannot be established.
        """
        if self.__is_connected:
            return
        try:
            raw_sock = socket.create_connection((self.host, self.port))
            if self.use_tls:
                context = self._build_tls_context()
                sock: socket.socket = context.wrap_socket(
                    raw_sock, server_hostname=self.host
                )
            else:
                sock = raw_sock
        except (OSError, ssl.SSLError) as exc:
            raise ConnectionError(
                f"Cannot connect to {self.host}:{self.port} ({exc})"
            ) from exc

        self.__socket = sock
        self.__is_connected = True
        self.__running = True
        self.__receiver_thread = threading.Thread(
            target=self._receive_loop, name="GameClientReceiver", daemon=True
        )
        self.__receiver_thread.start()
        self._fetch_protocol_info()

    def _fetch_protocol_info(self) -> None:
        """Retrieves the protocol revision and features of the server.

        Raises:
            ConnectionError: If the server does not answer.
        """
        try:
            payload = self._exchange("PROTOCOL_INFO", {})
        except ConnectionError:
            self.disconnect()
            raise
        revision = payload.get("revision")
        features = payload.get("features")
        if payload.get("success") is True and isinstance(revision, str):
            self.__server_revision = revision
            self.__server_features = tuple(
                feature for feature in (features if isinstance(features, list) else [])
                if isinstance(feature, str)
            )
        else:
            # A revision 2.0 server does not know PROTOCOL_INFO (UNKNOWN_TYPE).
            self.__server_revision = BASE_REVISION
            self.__server_features = ()

    def _require_feature(self, feature: str) -> None:
        """Checks that the server offers a protocol feature.

        Args:
            feature (str): The name of the feature.

        Raises:
            UnsupportedFeatureError: If the server does not offer the feature.
        """
        if feature not in self.__server_features:
            raise UnsupportedFeatureError(feature, self.__server_revision)

    def _build_tls_context(self) -> ssl.SSLContext:
        """Builds the TLS client context used to secure the connection.

        Returns:
            ssl.SSLContext: The configured client-side TLS context.
        """
        if self.__tls_ca_path is not None:
            context = ssl.create_default_context(cafile=str(self.__tls_ca_path))
        else:
            context = ssl.create_default_context()
        return context

    def disconnect(self) -> None:
        """Closes the connection with the server.

        Cleanly shuts down the current TCP connection and stops the background
        receiver. Calling this method when not connected has no effect.
        """
        self.__running = False
        self.__is_connected = False
        self.__session_user = None
        self.__server_revision = None
        self.__server_features = ()
        sock = self.__socket
        self.__socket = None
        if sock is not None:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                sock.close()
            except OSError:
                pass
        thread = self.__receiver_thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=1.0)
        self.__receiver_thread = None
        # Release any request still waiting for a response.
        with self.__pending_lock:
            events = list(self.__pending_events.values())
        for event in events:
            event.set()

    # ------------------------------------------------------------------ #
    # Receiving and notification dispatch
    # ------------------------------------------------------------------ #
    def _receive_loop(self) -> None:
        """Background loop reading and routing incoming messages.

        Responses (messages carrying a known ``request_id``) are stored and the
        corresponding waiting request is released. Every other message is
        treated as a notification and dispatched to the registered callbacks.
        """
        while self.__running:
            sock = self.__socket
            if sock is None:
                break
            header = self._recv_exact(sock, LENGTH_HEADER_SIZE)
            if header is None:
                break
            (length,) = struct.unpack(">I", header)
            body = self._recv_exact(sock, length)
            if body is None:
                break
            try:
                message = self._decode_body(body)
            except ValueError:
                continue
            self._route_message(message)
        self.__is_connected = False

    def _route_message(self, message: Dict[str, Any]) -> None:
        """Routes a decoded message to a pending request or to callbacks.

        Args:
            message (Dict[str, Any]): The decoded incoming message.
        """
        request_id = message.get("request_id")
        if isinstance(request_id, str):
            with self.__pending_lock:
                event = self.__pending_events.get(request_id)
                if event is not None:
                    self.__pending[request_id] = message
                    event.set()
                    return
        self._dispatch_notification(message)

    def _dispatch_notification(self, message: Dict[str, Any]) -> None:
        """Dispatches a notification to the registered callbacks.

        Args:
            message (Dict[str, Any]): The notification message.
        """
        msg_type = message.get("type")
        with self.__callbacks_lock:
            callbacks = list(self.__global_callbacks)
            if isinstance(msg_type, str):
                callbacks.extend(self.__type_callbacks.get(msg_type, ()))
        for callback in callbacks:
            try:
                callback(message)
            except Exception:  # pragma: no cover - user callback safety
                pass

    def on_notification(
        self,
        notification_type: Optional[str],
        callback: Callable[[Dict[str, Any]], None],
    ) -> None:
        """Registers a callback used to process notifications.

        Args:
            notification_type (str | None): The notification type to listen to
                (e.g. ``"GAME_EVENT"``). When ``None``, the callback receives
                every notification.
            callback (Callable[[Dict[str, Any]], None]): The function invoked
                with the notification message as its single argument.
        """
        with self.__callbacks_lock:
            if notification_type is None:
                self.__global_callbacks.append(callback)
            else:
                self.__type_callbacks.setdefault(notification_type, []).append(callback)

    # ------------------------------------------------------------------ #
    # Requests
    # ------------------------------------------------------------------ #
    def send_request(
        self, command: str, timeout: float = 10.0, **kwargs: Any
    ) -> Dict[str, Any]:
        """Sends a request to the server and waits for its response.

        Low-level method able to send any command supported by the protocol and
        return the corresponding response payload.

        Args:
            command (str): The name of the command/action to execute.
            timeout (float): Maximum time to wait for the response, in seconds.
                Defaults to ``10.0``.
            **kwargs: The arguments associated with the command.

        Returns:
            Dict[str, Any]: The payload of the server response.

        Raises:
            ConnectionError: If the client is not connected or the server closed
                the connection before answering.
            MultiplayerError: If the server returns an unsuccessful response.
        """
        payload = self._exchange(command, dict(kwargs), timeout)
        if payload.get("success") is False:
            raise MultiplayerError(
                payload.get("message")
                or payload.get("error_code")
                or "The server returned an error."
            )
        return payload

    def _exchange(
        self, command: str, payload: Dict[str, Any], timeout: float = 10.0
    ) -> Dict[str, Any]:
        """Sends a request and returns the raw response payload.

        Args:
            command (str): The command/action to execute.
            payload (Dict[str, Any]): The request payload.
            timeout (float): Maximum time to wait for the response, in seconds.

        Returns:
            Dict[str, Any]: The payload of the server response.

        Raises:
            ConnectionError: If the client is not connected or the server closed
                the connection before answering.
        """
        if not self.__is_connected or self.__socket is None:
            raise ConnectionError("The client is not connected to a server.")

        request_id = str(uuid.uuid4())
        message = {
            "type": command,
            "version": PROTOCOL_VERSION,
            "request_id": request_id,
            "payload": payload,
        }
        event = threading.Event()
        with self.__pending_lock:
            self.__pending_events[request_id] = event

        try:
            framed = self._encode_message(message)
            with self.__send_lock:
                sock = self.__socket
                if sock is None:
                    raise ConnectionError("The client is not connected to a server.")
                try:
                    sock.sendall(framed)
                except OSError as exc:
                    raise ConnectionError(f"Failed to send request: {exc}") from exc

            if not event.wait(timeout):
                raise ConnectionError(
                    f"Timed out waiting for the response to '{command}'."
                )
            with self.__pending_lock:
                response = self.__pending.pop(request_id, None)
        finally:
            with self.__pending_lock:
                self.__pending_events.pop(request_id, None)
                self.__pending.pop(request_id, None)

        if response is None:
            raise ConnectionError(
                "The connection was closed before the response was received."
            )

        result = response.get("payload")
        if not isinstance(result, dict):
            result = {}
        return result

    def login(self, username: str, password: str) -> User:
        """Authenticates against the server.

        Sends a ``USER_LOGIN`` request with the supplied credentials. On success
        the user becomes the user of the session, and the server attaches its
        active players (listed in ``User.players_id``) to the session.

        Args:
            username (str): The user name.
            password (str): The password.

        Returns:
            User: The authenticated user account (mirrored locally).

        Raises:
            PasswordError: If the password is incorrect.
            UserNotFoundError: If the user does not exist.
            ConnectionError: If the client is not connected.
        """
        payload = self._exchange(
            "USER_LOGIN", {"username": username, "password": password}
        )
        if payload.get("success") is not True:
            self._raise_login_error(payload)

        user = _build_user_from_payload(payload)
        self.__session_user = user
        return user

    @staticmethod
    def _raise_login_error(payload: Dict[str, Any]) -> None:
        """Raises the appropriate exception for a failed login response.

        Args:
            payload (Dict[str, Any]): The unsuccessful ``AUTH_RESPONSE`` payload.

        Raises:
            PasswordError: If the credentials are invalid.
            UserNotFoundError: If the user cannot be found.
            MultiplayerError: For any other server-reported error.
        """
        error_code = payload.get("error_code")
        message = payload.get("message") or error_code or "Authentication failed."
        if error_code in ("INVALID_CREDENTIALS", "INVALID_PASSWORD"):
            raise PasswordError(message)
        if error_code == "USER_NOT_FOUND":
            exc = UserNotFoundError()
            exc.args = (message,)
            raise exc
        raise MultiplayerError(message)

    def create_player(
        self,
        name: str,
        is_default: bool = True,
        static_attributes: Optional[Dict[str, Any]] = None,
        dynamic_attributes: Optional[Dict[str, Any]] = None,
    ) -> Player:
        """Creates a session player on the server.

        Sends a ``PLAYER_CREATE`` request and, on success, mirrors the created
        player locally. When ``is_default`` is set, the new player becomes the
        session default player on the server. When a user is authenticated, the
        server adds the new player to its ``players_id`` list, and so does the
        local mirror held by :attr:`session_user`.

        With a revision 2.0 server, the dynamic attributes are sent in the
        ``attributes`` field, and static attributes cannot be sent.

        Args:
            name (str): The name of the player to create.
            is_default (bool): Whether the created player becomes the default
                player of the session. Defaults to ``True``.
            static_attributes (dict | None): Custom attributes stored in the
                ``static_state`` dictionary of the player. Defaults to ``None``.
            dynamic_attributes (dict | None): Custom attributes stored in the
                ``dynamic_state`` dictionary of the player. Defaults to ``None``.

        Returns:
            Player: The locally mirrored created player.

        Raises:
            UnsupportedFeatureError: If static attributes are provided to a
                revision 2.0 server (the request is not sent).
            MultiplayerError: If the server rejects the creation.
            ConnectionError: If the client is not connected.
        """
        arguments: Dict[str, Any] = {"name": name, "is_default": is_default}
        if self.__server_revision == BASE_REVISION:
            if static_attributes:
                raise UnsupportedFeatureError("static_attributes", self.__server_revision)
            if dynamic_attributes:
                arguments["attributes"] = dict(dynamic_attributes)
        else:
            if static_attributes:
                arguments["static_attributes"] = dict(static_attributes)
            if dynamic_attributes:
                arguments["dynamic_attributes"] = dict(dynamic_attributes)
        payload = self.send_request("PLAYER_CREATE", **arguments)
        player = Player(name=name)
        player_id = payload.get("player_id")
        if isinstance(player_id, str):
            player._id = player_id
        player.static_state.update(static_attributes or {})
        player.dynamic_state.update(dynamic_attributes or {})
        if self.__session_user is not None:
            self.__session_user.players_id.append(player.ID)
        return player

    def update_player(
        self,
        player_id: str,
        name: Optional[str] = None,
        reset_state: bool = False,
    ) -> Dict[str, Any]:
        """Updates a player of the session on the server.

        Sends a ``PLAYER_UPDATE`` request renaming the player, emptying its
        ``static_state`` and ``dynamic_state`` attributes, or both. Resetting
        the attributes lets a player that left its game be reused for another
        game; the server refuses it while the player takes part in a game.

        Args:
            player_id (str): The ID of the player to update.
            name (str | None): The new name of the player, or ``None`` to keep
                the current one. Defaults to ``None``.
            reset_state (bool): Whether to empty the custom attributes of the
                player. Defaults to ``False``.

        Returns:
            Dict[str, Any]: The response payload from the server.

        Raises:
            ValueError: If neither a name nor a reset is requested.
            MultiplayerError: If the server rejects the update.
            ConnectionError: If the client is not connected.
        """
        if name is None and not reset_state:
            raise ValueError("A new name or a state reset is required to update a player.")
        arguments: Dict[str, Any] = {"player_id": player_id}
        if name is not None:
            arguments["name"] = name
        if reset_state:
            arguments["reset_state"] = True
        return self.send_request("PLAYER_UPDATE", **arguments)

    def create_game(
        self,
        name: str,
        min_players: int = 0,
        max_players: Optional[int] = None,
        max_observers: Optional[int] = None,
        turn_based: bool = False,
        password: Optional[str] = None,
        group_id: Optional[str] = None,
        group_password: Optional[str] = None,
        factory_template_id: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Creates a game on the server.

        Sends a ``GAME_CREATE`` request. A player factory can be given to the
        game from a template held by the server (``factory_template_id``).

        Args:
            name (str): The name of the game.
            min_players (int): The minimum number of players. Defaults to 0.
            max_players (int | None): The maximum number of players (``None``
                for unlimited). Defaults to ``None``.
            max_observers (int | None): The maximum number of observers
                (``None`` for unlimited). Defaults to ``None``.
            turn_based (bool): Whether the game is turn-based. Defaults to False.
            password (str | None): The password of the game. Defaults to ``None``.
            group_id (str | None): The group of the game. Defaults to ``None``.
            group_password (str | None): The password of the group. Defaults
                to ``None``.
            factory_template_id (str | None): The ID of the factory template
                to apply to the game. Defaults to ``None``.
            attributes (dict | None): The custom attributes of the game.
                Defaults to ``None``.

        Returns:
            str: The ID of the created game.

        Raises:
            UnsupportedFeatureError: If a factory template is requested from a
                server without the ``player_factory`` feature (the request is
                not sent).
            MultiplayerError: If the server rejects the creation.
            ConnectionError: If the client is not connected.
        """
        if factory_template_id is not None:
            self._require_feature(FEATURE_PLAYER_FACTORY)
        arguments: Dict[str, Any] = {
            "name": name,
            "min_players": min_players,
            "max_players": max_players,
            "max_observers": max_observers,
            "turn_based": turn_based,
        }
        optional = {
            "password": password,
            "group_id": group_id,
            "group_password": group_password,
            "factory_template_id": factory_template_id,
            "attributes": attributes,
        }
        arguments.update({key: value for key, value in optional.items() if value is not None})
        payload = self.send_request("GAME_CREATE", **arguments)
        return payload.get("game_id", "")

    # ------------------------------------------------------------------ #
    # Player factories
    # ------------------------------------------------------------------ #
    def _factory_request(self, command: str, **kwargs: Any) -> Dict[str, Any]:
        """Sends a request requiring the ``player_factory`` feature.

        Args:
            command (str): The command to send.
            **kwargs: The arguments of the command.

        Returns:
            Dict[str, Any]: The payload of the server response.

        Raises:
            UnsupportedFeatureError: If the server does not offer the feature.
            MultiplayerError: If the server returns an error.
            ConnectionError: If the client is not connected.
        """
        self._require_feature(FEATURE_PLAYER_FACTORY)
        return self.send_request(command, **kwargs)

    def list_factory_templates(self) -> Dict[str, Any]:
        """Retrieves the factory templates available on the server.

        Returns:
            Dict[str, Any]: The ``FACTORY_TEMPLATE_LIST_RESPONSE`` payload.
        """
        return self._factory_request("FACTORY_TEMPLATE_LIST")

    def get_factory_template(self, template_id: str) -> Dict[str, Any]:
        """Retrieves the full definition of a factory template.

        Args:
            template_id (str): The ID of the template.

        Returns:
            Dict[str, Any]: The ``FACTORY_TEMPLATE_GET_RESPONSE`` payload.
        """
        return self._factory_request("FACTORY_TEMPLATE_GET", template_id=template_id)

    def create_factory_template(self, name: str, options: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Creates a factory template on the server (administrator).

        Args:
            name (str): The name of the template.
            options (list[dict]): The definitions of the options.

        Returns:
            Dict[str, Any]: The ``FACTORY_TEMPLATE_CREATE_RESPONSE`` payload.
        """
        return self._factory_request("FACTORY_TEMPLATE_CREATE", name=name, options=options)

    def update_factory_template(
        self,
        template_id: str,
        name: Optional[str] = None,
        options: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Updates a factory template on the server (administrator).

        Args:
            template_id (str): The ID of the template.
            name (str | None): The new name. Defaults to ``None`` (unchanged).
            options (list[dict] | None): The new complete list of options.
                Defaults to ``None`` (unchanged).

        Returns:
            Dict[str, Any]: The ``FACTORY_TEMPLATE_UPDATE_RESPONSE`` payload.

        Raises:
            ValueError: If neither a name nor options are provided.
        """
        if name is None and options is None:
            raise ValueError("A new name or a new list of options is required.")
        self._require_feature(FEATURE_PLAYER_FACTORY)
        arguments: Dict[str, Any] = {"template_id": template_id}
        if name is not None:
            arguments["name"] = name
        if options is not None:
            arguments["options"] = options
        return self.send_request("FACTORY_TEMPLATE_UPDATE", **arguments)

    def delete_factory_template(self, template_id: str) -> Dict[str, Any]:
        """Deletes a factory template from the server (administrator).

        Args:
            template_id (str): The ID of the template.

        Returns:
            Dict[str, Any]: The ``FACTORY_TEMPLATE_DELETE_RESPONSE`` payload.
        """
        return self._factory_request("FACTORY_TEMPLATE_DELETE", template_id=template_id)

    def get_game_factory(
        self,
        game_id: str,
        password: Optional[str] = None,
        group_password: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Retrieves the player factory of a game.

        A successful request subscribes the session to the
        ``GAME_FACTORY_UPDATED`` notifications of the game.

        Args:
            game_id (str): The ID of the game.
            password (str | None): The password of the game. Defaults to ``None``.
            group_password (str | None): The password of a protected group
                containing the game. Defaults to ``None``.

        Returns:
            Dict[str, Any]: The ``GAME_FACTORY_GET_RESPONSE`` payload.
        """
        arguments: Dict[str, Any] = {"game_id": game_id}
        if password is not None:
            arguments["password"] = password
        if group_password is not None:
            arguments["group_password"] = group_password
        return self._factory_request("GAME_FACTORY_GET", **arguments)

    def join_game_with_factory(
        self,
        game_id: str,
        values: Optional[Dict[str, Any]] = None,
        password: Optional[str] = None,
        group_password: Optional[str] = None,
        is_default: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Creates a player from the factory of a game and makes it join the game.

        Args:
            game_id (str): The ID of the game.
            values (dict | None): The chosen values, indexed by the IDs of the
                options of the factory. Defaults to ``None``.
            password (str | None): The password of the game. Defaults to ``None``.
            group_password (str | None): The password of a protected group
                containing the game. Defaults to ``None``.
            is_default (bool | None): Whether the created player becomes the
                default player of the session. ``None`` lets the server rule
                apply. Defaults to ``None``.

        Returns:
            Dict[str, Any]: The ``GAME_FACTORY_JOIN_RESPONSE`` payload.
        """
        arguments: Dict[str, Any] = {"game_id": game_id}
        optional = {
            "values": values,
            "password": password,
            "group_password": group_password,
            "is_default": is_default,
        }
        arguments.update({key: value for key, value in optional.items() if value is not None})
        payload = self._factory_request("GAME_FACTORY_JOIN", **arguments)
        player_id = payload.get("player_id")
        if self.__session_user is not None and isinstance(player_id, str):
            self.__session_user.players_id.append(player_id)
        return payload

    def save_persistence(self) -> Dict[str, Any]:
        """Requests an immediate persistence save on the server.

        Sends a ``SERVER_PERSISTENCE_SAVE`` request to the server. The current
        session must have administrator privileges.

        Returns:
            Dict[str, Any]: The response payload from the server.

        Raises:
            MultiplayerError: If the server returns an error.
            ConnectionError: If the client is not connected.
        """
        return self.send_request("SERVER_PERSISTENCE_SAVE")

    def __enter__(self) -> "GameClient":
        """Enters the context manager, opening the connection.

        Returns:
            GameClient: The connected client instance.
        """
        self.connect()
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        """Exits the context manager, closing the connection.

        Args:
            exc_type (Any): The exception type, if any.
            exc (Any): The exception instance, if any.
            tb (Any): The traceback, if any.
        """
        self.disconnect()
