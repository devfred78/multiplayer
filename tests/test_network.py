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

# Use different ports for testing to avoid conflicts
TEST_PORT = 65433
TEST_SERVER_PASSWORD = "test_server_password"
TEST_GAME_PASSWORD = "test_game_password"

@pytest.fixture(scope="module")
def game_server():
    """Fixture to start and stop a server without security."""
    server = GameServer(host='0.0.0.0', port=TEST_PORT)
    server.start()
    time.sleep(0.2)
    yield
    server.stop()
    time.sleep(0.2)

@pytest.fixture(scope="module")
def secure_game_server():
    """Fixture to start and stop a server with a password."""
    server = GameServer(host='0.0.0.0', port=TEST_PORT + 1, password=TEST_SERVER_PASSWORD)
    server.start()
    time.sleep(0.2)
    yield
    server.stop()
    time.sleep(0.2)

@pytest.fixture(scope="module")
def tls_game_server():
    """Fixture to start and stop a server with TLS encryption."""
    server = GameServer(host='0.0.0.0', port=TEST_PORT + 2, use_tls=True)
    server.start()
    time.sleep(0.2)
    yield
    server.stop()
    time.sleep(0.2)

def test_server_discovery(game_server):
    """Tests that the server discovery mechanism works."""
    discovered_servers = GameClient.discover_servers(timeout=1)
    assert len(discovered_servers) > 0
    found = any(port == TEST_PORT for _, port in discovered_servers)
    assert found

def test_server_connection(game_server):
    """Tests that a client can connect to a server without security."""
    client = GameClient(port=TEST_PORT)
    assert client.list_games() == {}

def test_create_and_list_games(game_server):
    """Tests that a client can create, see, and then not see a game in the list."""
    client = GameClient(port=TEST_PORT)
    game = client.create_game(name="Test Game", turn_based=True)
    assert game.game_id is not None
    
    # Game should be in the list
    games_list = client.list_games()
    assert game.game_id in games_list
    
    # After stopping, it should not be in the list
    game.stop()
    games_list_after_stop = client.list_games()
    assert game.game_id not in games_list_after_stop

def test_game_proxy_interaction(game_server):
    """Tests that interactions with the RemoteGame proxy work as expected."""
    client = GameClient(port=TEST_PORT)
    game = client.create_game(turn_based=True)
    game.add_player(Player("Alice", score=100))
    game.start()
    
    current_player = game.current_player
    assert current_player.name == "Alice"
    
    # Test the new state format
    full_state = game.state
    assert full_state['status'] == 'in_progress'
    assert full_state['custom'] == {}
    
    # Test setting and getting custom state
    game.set_state({"score": 50})
    new_state = game.state
    assert new_state['custom']['score'] == 50
    
    game.stop()
    final_state = game.state
    assert final_state['status'] == 'finished'

def test_error_handling(game_server):
    """Tests that the server correctly reports errors to the client."""
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
    """Tests that a ConnectionError is raised if the server is not running."""
    client = GameClient(port=9999)
    with pytest.raises(ConnectionError):
        client.list_games()

def test_secure_server_connection_success(secure_game_server):
    """Tests connection to a password-protected server with the correct password."""
    client = GameClient(port=TEST_PORT + 1, password=TEST_SERVER_PASSWORD)
    assert client.list_games() == {}

def test_secure_server_connection_failure(secure_game_server):
    """Tests connection to a password-protected server with the wrong password."""
    client = GameClient(port=TEST_PORT + 1, password="wrong_password")
    with pytest.raises(AuthenticationError):
        client.list_games()

def test_tls_server_connection_success(tls_game_server):
    """Tests that a client can connect to a TLS-enabled server."""
    client = GameClient(port=TEST_PORT + 2, use_tls=True)
    assert client.list_games() == {}

def test_tls_server_connection_failure_mismatch(tls_game_server):
    """Tests that a non-TLS client cannot connect to a TLS-enabled server."""
    client = GameClient(port=TEST_PORT + 2, use_tls=False)
    with pytest.raises(ConnectionError):
        client.list_games()

def test_game_password_success(game_server):
    """Tests joining a password-protected game with the correct password."""
    client = GameClient(port=TEST_PORT)
    game = client.create_game(password=TEST_GAME_PASSWORD)
    game.add_player(Player("Alice"), password=TEST_GAME_PASSWORD)
    # No error should be raised

def test_game_password_failure(game_server):
    """Tests that joining a password-protected game with the wrong password fails."""
    client = GameClient(port=TEST_PORT)
    game = client.create_game(password=TEST_GAME_PASSWORD)
    with pytest.raises(AuthenticationError, match="Invalid password for this game"):
        game.add_player(Player("Alice"), password="wrong_game_password")
