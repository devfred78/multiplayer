import asyncio
import json
import struct

import pytest

from multiplayer import SaveFormat
from multiplayer.game import User
from multiplayer.server import (
    AccessLevel,
    ClientSession,
    GameServer,
    PROTOCOL_VERSION,
    SERVICE_NAME,
)


class FakeWriter:
    """Minimal asyncio.StreamWriter stand-in capturing framed messages."""

    def __init__(self):
        self.buffer = bytearray()
        self.closed = False

    def write(self, data):
        self.buffer.extend(data)

    async def drain(self):
        return None

    def close(self):
        self.closed = True

    def get_extra_info(self, name):
        return ("127.0.0.1", 12345)


def _decode_messages(buffer):
    messages = []
    offset = 0
    while offset + 4 <= len(buffer):
        (length,) = struct.unpack(">I", bytes(buffer[offset : offset + 4]))
        offset += 4
        body = bytes(buffer[offset : offset + length])
        offset += length
        messages.append(json.loads(body.decode("utf-8")))
    return messages


def _make_session(server, level=AccessLevel.BASE):
    writer = FakeWriter()
    session = ClientSession("session-test", writer, ("127.0.0.1", 12345))
    session.access_level = level
    server._sessions[session.session_id] = session
    return session, writer


def _dispatch(server, session, msg_type, payload=None):
    message = {"type": msg_type, "version": PROTOCOL_VERSION, "payload": payload or {}}
    asyncio.run(server._dispatch(session, message))
    return _decode_messages(session.writer.buffer)[-1]


def test_server_instantiation_defaults():
    server = GameServer(name="Test Server")
    assert server.name == "Test Server"
    assert server.port == 65432
    assert server.use_tls is False
    assert server.password_required is False


def test_invalid_unencrypted_port():
    with pytest.raises(ValueError):
        GameServer(port=5000, unencrypted_port=5000)


def test_tls_without_certificate_raises():
    with pytest.raises(ValueError):
        GameServer(use_tls=True)


def test_discovery_response_structure():
    server = GameServer(name="Disco", port=50000)
    response = server.build_discovery_response()
    assert response["type"] == "DISCOVERY_RESPONSE"
    assert response["service_name"] == SERVICE_NAME
    assert response["version"] == PROTOCOL_VERSION
    assert response["service_port"] == 50000
    assert response["password_required"] is False


def test_framing_roundtrip():
    message = {"type": "GAME_LIST", "version": PROTOCOL_VERSION, "payload": {}}
    framed = GameServer._encode_message(message, binary=False)
    (length,) = struct.unpack(">I", framed[:4])
    assert length == len(framed) - 4
    assert GameServer._decode_body(framed[4:]) == message


def test_unsupported_version_rejected():
    server = GameServer()
    session, _ = _make_session(server)
    asyncio.run(
        server._dispatch(session, {"type": "GAME_LIST", "version": 1, "payload": {}})
    )
    response = _decode_messages(session.writer.buffer)[-1]
    assert response["payload"]["error_code"] == "UNSUPPORTED_VERSION"


def test_player_create_and_list():
    server = GameServer()
    session, _ = _make_session(server)
    created = _dispatch(server, session, "PLAYER_CREATE", {"name": "Guest", "is_default": True})
    assert created["type"] == "PLAYER_CREATE_RESPONSE"
    assert created["payload"]["success"] is True
    player_id = created["payload"]["player_id"]

    listed = _dispatch(server, session, "PLAYER_LIST")
    players = listed["payload"]["players"]
    assert len(players) == 1
    assert players[0]["player_id"] == player_id
    assert players[0]["is_default"] is True


def test_server_auth_required_then_granted():
    server = GameServer(password="secret")
    session, _ = _make_session(server, level=AccessLevel.OPEN)
    # A BASE-level request is rejected while still at OPEN level.
    rejected = _dispatch(server, session, "PLAYER_LIST")
    assert rejected["payload"]["error_code"] == "INSUFFICIENT_PERMISSIONS"

    bad = _dispatch(server, session, "SERVER_AUTH", {"password": "wrong"})
    assert bad["payload"]["success"] is False
    assert bad["payload"]["error_code"] == "INVALID_PASSWORD"

    ok = _dispatch(server, session, "SERVER_AUTH", {"password": "secret"})
    assert ok["payload"]["success"] is True
    assert ok["payload"]["access_level"] == "BASE"
    assert session.access_level == AccessLevel.BASE


def test_game_create_join_and_control():
    server = GameServer()
    session, _ = _make_session(server)
    _dispatch(server, session, "PLAYER_CREATE", {"name": "Alice", "is_default": True})

    created = _dispatch(server, session, "GAME_CREATE", {"name": "Chess", "turn_based": True})
    game_id = created["payload"]["game_id"]
    assert created["payload"]["success"] is True

    joined = _dispatch(server, session, "GAME_JOIN", {"game_id": game_id, "role": "PLAYER"})
    assert joined["payload"]["success"] is True

    started = _dispatch(
        server,
        session,
        "GAME_CONTROL",
        {"game_id": game_id, "player_id": "x", "action": "START"},
    )
    assert started["payload"]["success"] is True

    state = _dispatch(server, session, "GAME_STATE_GET", {"game_id": game_id})
    assert state["payload"]["state"]["status"] == "IN_PROGRESS"


def test_user_login_grants_player_level():
    server = GameServer()
    # Register a user directly in the server registry.
    user = User(username="login_user", password="pwd")
    server._users[user.username] = user
    server._players[user.player.ID] = user.player

    session, _ = _make_session(server)
    response = _dispatch(
        server, session, "USER_LOGIN", {"username": "login_user", "password": "pwd"}
    )
    assert response["payload"]["success"] is True
    assert response["payload"]["access_level"] == "PLAYER"
    assert session.access_level == AccessLevel.PLAYER

    bad = _dispatch(
        server, session, "USER_LOGIN", {"username": "login_user", "password": "bad"}
    )
    # Already authenticated takes precedence over invalid credentials.
    assert bad["payload"]["success"] is False


def test_persistence_path_defaults():
    server = GameServer(persistence_mode=SaveFormat.SQLITE)
    assert str(server.persistence_path).endswith("server_data.db")
    server_json = GameServer(persistence_mode=SaveFormat.JSON)
    assert str(server_json.persistence_path).endswith("server_data.json")
