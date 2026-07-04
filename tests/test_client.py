import asyncio
import struct
import threading
import time

import pytest

from multiplayer.client import (
    GameClient,
    PROTOCOL_VERSION,
    _build_user_from_payload,
)
from multiplayer import PlayerRole
from multiplayer.exceptions import MultiplayerError, PasswordError, PlayerNotFoundError
from multiplayer.game import User
from multiplayer.server import GameServer


# --------------------------------------------------------------------------- #
# Server helper running a real GameServer in a background asyncio loop.
# --------------------------------------------------------------------------- #
class ServerRunner:
    """Runs a GameServer in a dedicated thread and event loop for testing."""

    def __init__(self, **kwargs):
        self.server = GameServer(host="127.0.0.1", port=0, **kwargs)
        self.loop = asyncio.new_event_loop()
        self.port = None
        self._ready = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _run(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.server.start())
        self.port = self.server._actual_port
        self._ready.set()
        self.loop.run_forever()

    def start(self):
        self._thread.start()
        assert self._ready.wait(5), "Server did not start in time"
        return self.port

    def run_coro(self, coro):
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        return future.result(5)

    def stop(self):
        try:
            self.run_coro(self.server.stop())
        finally:
            self.loop.call_soon_threadsafe(self.loop.stop)
            self._thread.join(5)


@pytest.fixture
def server():
    runner = ServerRunner()
    runner.start()
    yield runner
    runner.stop()


# --------------------------------------------------------------------------- #
# Unit tests (no network)
# --------------------------------------------------------------------------- #
def test_client_instantiation_defaults():
    client = GameClient()
    assert client.host == "127.0.0.1"
    assert client.port == 65432
    assert client.use_tls is False
    assert client.tls_ca_path is None
    assert client.is_connected is False
    assert client.session_player is None


def test_invalid_port_raises():
    with pytest.raises(ValueError):
        GameClient(port=70000)


def test_framing_roundtrip():
    message = {"type": "GAME_LIST", "version": PROTOCOL_VERSION, "payload": {}}
    framed = GameClient._encode_message(message, binary=False)
    (length,) = struct.unpack(">I", framed[:4])
    assert length == len(framed) - 4
    assert GameClient._decode_body(framed[4:]) == message


def test_build_user_from_payload():
    payload = {
        "username": "alice",
        "role": "SERVER_ADMIN",
        "player_id": "player-123",
        "player_name": "Alice",
    }
    user = _build_user_from_payload(payload)
    assert user.username == "alice"
    assert user.role == PlayerRole.SERVER_ADMIN
    assert user.player.ID == "player-123"
    assert user.player.name == "Alice"


def test_raise_login_error_mapping():
    with pytest.raises(PasswordError):
        GameClient._raise_login_error({"error_code": "INVALID_CREDENTIALS"})
    with pytest.raises(PlayerNotFoundError):
        GameClient._raise_login_error({"error_code": "USER_NOT_FOUND"})
    with pytest.raises(MultiplayerError):
        GameClient._raise_login_error({"error_code": "SOMETHING_ELSE"})


def test_on_notification_dispatch():
    client = GameClient()
    received = []
    globals_received = []
    client.on_notification("GAME_EVENT", lambda n: received.append(n))
    client.on_notification(None, lambda n: globals_received.append(n))

    event = {"type": "GAME_EVENT", "version": PROTOCOL_VERSION, "payload": {"x": 1}}
    other = {"type": "SERVER_SHUTDOWN", "version": PROTOCOL_VERSION, "payload": {}}
    client._dispatch_notification(event)
    client._dispatch_notification(other)

    assert received == [event]
    assert globals_received == [event, other]


def test_route_message_notification_without_request_id():
    client = GameClient()
    seen = []
    client.on_notification(None, lambda n: seen.append(n))
    client._route_message({"type": "GAME_TURN_CHANGED", "payload": {}})
    assert len(seen) == 1


def test_send_request_when_not_connected_raises():
    client = GameClient()
    with pytest.raises(ConnectionError):
        client.send_request("GAME_LIST")


# --------------------------------------------------------------------------- #
# Integration tests (real server + real client over TCP)
# --------------------------------------------------------------------------- #
def test_connect_and_disconnect(server):
    client = GameClient(host="127.0.0.1", port=server.port)
    client.connect()
    assert client.is_connected is True
    client.disconnect()
    assert client.is_connected is False


def test_context_manager(server):
    with GameClient(host="127.0.0.1", port=server.port) as client:
        assert client.is_connected is True
    assert client.is_connected is False


def test_create_player_updates_session_player(server):
    client = GameClient(host="127.0.0.1", port=server.port)
    client.connect()
    try:
        player = client.create_player("Guest", is_default=True)
        assert player.ID
        assert client.session_player is not None
        assert client.session_player.ID == player.ID
    finally:
        client.disconnect()


def test_send_request_game_flow(server):
    client = GameClient(host="127.0.0.1", port=server.port)
    client.connect()
    try:
        client.create_player("Alice", is_default=True)
        created = client.send_request("GAME_CREATE", name="Chess", turn_based=True)
        assert created["success"] is True
        game_id = created["game_id"]

        joined = client.send_request("GAME_JOIN", game_id=game_id, role="PLAYER")
        assert joined["success"] is True

        listed = client.send_request("GAME_LIST")
        assert any(g["game_id"] == game_id for g in listed["games"])
    finally:
        client.disconnect()


def test_send_request_error_raises(server):
    client = GameClient(host="127.0.0.1", port=server.port)
    client.connect()
    try:
        with pytest.raises(MultiplayerError):
            # Joining a non-existent game must fail.
            client.send_request("GAME_JOIN", game_id="does-not-exist", role="PLAYER")
    finally:
        client.disconnect()


def test_login_success_and_failure(server):
    username = "client_login_user"
    user = User(username=username, password="secret")
    server.server._users[username] = user
    server.server._players[user.player.ID] = user.player

    client = GameClient(host="127.0.0.1", port=server.port)
    client.connect()
    try:
        authenticated = client.login(username, "secret")
        assert authenticated.username == username
        assert authenticated.role == PlayerRole.PLAYER
        assert client.session_player is not None
        assert client.session_player.ID == user.player.ID
    finally:
        client.disconnect()

    other = GameClient(host="127.0.0.1", port=server.port)
    other.connect()
    try:
        with pytest.raises(PasswordError):
            other.login(username, "wrong-password")
    finally:
        other.disconnect()


def test_notification_dispatch_over_socket(server):
    client = GameClient(host="127.0.0.1", port=server.port)
    received = []
    event = threading.Event()

    def handler(notification):
        received.append(notification)
        event.set()

    client.on_notification("GAME_EVENT", handler)
    client.connect()
    try:
        # Wait until the server registered the client session.
        deadline = time.time() + 5
        while not server.server._sessions and time.time() < deadline:
            time.sleep(0.02)
        assert server.server._sessions

        session = next(iter(server.server._sessions.values()))
        notification = {
            "type": "GAME_EVENT",
            "version": PROTOCOL_VERSION,
            "payload": {"action_type": "MOVE", "player_id": "p1"},
        }
        server.run_coro(server.server._send(session, notification, binary=False))

        assert event.wait(5), "Notification was not received"
        assert received[0]["payload"]["action_type"] == "MOVE"
    finally:
        client.disconnect()
