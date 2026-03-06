"""
Unit tests for the client-server architecture.
"""
import pytest
import time
from multiplayer import GameServer, GameClient, Player
from multiplayer.exceptions import (
    ConnectionError,
    GameNotFoundError,
    PlayerLimitReachedError,
    AuthenticationError,
)

# Use a different port for testing to avoid conflicts
TEST_PORT = 65433
TEST_PASSWORD = "test_password"

@pytest.fixture(scope="module")
def game_server():
    """Fixture to start and stop a server without a password."""
    server = GameServer(host='0.0.0.0', port=TEST_PORT)
    server.start()
    time.sleep(0.2)
    yield
    server.stop()
    time.sleep(0.2)

@pytest.fixture(scope="module")
def secure_game_server():
    """Fixture to start and stop a server with a password."""
    server = GameServer(host='0.0.0.0', port=TEST_PORT + 1, password=TEST_PASSWORD)
    server.start()
    time.sleep(0.2)
    yield
    server.stop()
    time.sleep(0.2)

def test_server_discovery(game_server):
    """
    Tests that the server discovery mechanism works.
    """
    discovered_servers = GameClient.discover_servers(timeout=1)
    assert len(discovered_servers) > 0
    found = any(port == TEST_PORT for _, port in discovered_servers)
    assert found, f"Test server on port {TEST_PORT} not found in discovered list: {discovered_servers}"

def test_server_connection(game_server):
    """
    Tests that a client can connect to a server without a password.
    """
    client = GameClient(port=TEST_PORT)
    assert client.list_games() == {}

def test_create_and_list_games(game_server):
    """
    Tests that a client can create a game and see it in the list.
    """
    client = GameClient(port=TEST_PORT)
    game = client.create_game(name="Test Game", turn_based=True)
    assert game.game_id is not None
    games_list = client.list_games()
    assert game.game_id in games_list
    assert games_list[game.game_id]['name'] == "Test Game"

def test_game_proxy_interaction(game_server):
    """
    Tests that interactions with the RemoteGame proxy work as expected.
    """
    client = GameClient(port=TEST_PORT)
    game = client.create_game(turn_based=True)
    game.add_player(Player("Alice", score=100))
    game.start()
    current_player = game.current_player
    assert current_player is not None
    assert current_player.name == "Alice"
    assert game.state == "in_progress"
    game.stop()
    assert game.state == "finished"

def test_error_handling(game_server):
    """
    Tests that the server correctly reports errors to the client.
    """
    client = GameClient(port=TEST_PORT)
    with pytest.raises(GameNotFoundError):
        from multiplayer.client import RemoteGame
        fake_game = RemoteGame("fake-id", port=TEST_PORT)
        _ = fake_game.state
    game = client.create_game(max_players=1)
    game.add_player(Player("Alice"))
    with pytest.raises(PlayerLimitReachedError):
        game.add_player(Player("Bob"))

def test_connection_error():
    """
    Tests that a ConnectionError is raised if the server is not running.
    """
    client = GameClient(port=9999)
    with pytest.raises(ConnectionError):
        client.list_games()

def test_secure_server_connection_success(secure_game_server):
    """
    Tests that a client can connect to a password-protected server with the correct password.
    """
    client = GameClient(port=TEST_PORT + 1, password=TEST_PASSWORD)
    assert client.list_games() == {}

def test_secure_server_connection_failure_no_password(secure_game_server):
    """
    Tests that a client cannot connect to a password-protected server without a password.
    """
    client = GameClient(port=TEST_PORT + 1)
    with pytest.raises(AuthenticationError, match="Invalid password"):
        client.list_games()

def test_secure_server_connection_failure_wrong_password(secure_game_server):
    """
    Tests that a client cannot connect to a password-protected server with the wrong password.
    """
    client = GameClient(port=TEST_PORT + 1, password="wrong_password")
    with pytest.raises(AuthenticationError, match="Invalid password"):
        client.list_games()
