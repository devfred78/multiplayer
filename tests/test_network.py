"""
Unit tests for the client-server architecture.
"""
import pytest
import time
import socket
import ssl
from multiplayer import GameServer, GameClient, Player, Observer, exceptions, GameState
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

def wait_for_server(port, timeout=5, use_tls=False, server_hostname='localhost'):
    """Wait for the server to be ready by trying to connect to it."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            if use_tls:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                with socket.create_connection(('127.0.0.1', port), timeout=0.5) as sock:
                    with context.wrap_socket(sock, server_hostname=server_hostname):
                        return True
            else:
                with socket.create_connection(('127.0.0.1', port), timeout=0.5):
                    return True
        except (socket.error, ConnectionRefusedError, ssl.SSLError):
            time.sleep(0.1)
    return False

@pytest.fixture(scope="module")
def game_server():
    """Fixture to start and stop a server without security."""
    server = GameServer(host='0.0.0.0', port=TEST_PORT)
    server.start()
    if not wait_for_server(TEST_PORT):
        server.stop()
        pytest.fail("Server failed to start in time")
    yield server
    server.stop()

@pytest.fixture(scope="module")
def secure_game_server():
    """Fixture to start and stop a server with a password."""
    port = TEST_PORT + 1
    server = GameServer(host='0.0.0.0', port=port, password=TEST_SERVER_PASSWORD)
    server.start()
    if not wait_for_server(port):
        server.stop()
        pytest.fail("Secure server failed to start in time")
    yield server
    server.stop()

@pytest.fixture(scope="module")
def tls_game_server():
    """Fixture to start and stop a server with TLS encryption."""
    port = TEST_PORT + 2
    server = GameServer(host='0.0.0.0', port=port, use_tls=True)
    server.start()
    if not wait_for_server(port, use_tls=True):
        server.stop()
        pytest.fail("TLS server failed to start in time")
    yield server
    server.stop()

@pytest.fixture(scope="module")
def tls_custom_game_server():
    """Fixture to start and stop a server with TLS encryption and custom domain."""
    port = TEST_PORT + 3
    server = GameServer(host='0.0.0.0', port=port, use_tls=True, tls_domain="test.local", tls_self_signed=True)
    server.start()
    if not wait_for_server(port, use_tls=True, server_hostname="test.local"):
        server.stop()
        pytest.fail("Custom TLS server failed to start in time")
    yield server
    server.stop()

def test_server_discovery(game_server):
    """Tests that the server discovery mechanism works."""
    discovered_servers = GameClient.discover_servers(timeout=1)
    if not discovered_servers:
        # Check if it was because of an OSError (no route to host)
        # On some CI systems (like MacOS), multicast discovery might not be available.
        # We try to send a test multicast packet to see if it's supported.
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as s:
                from multiplayer.client import MULTICAST_GROUP, DISCOVERY_PORT
                s.sendto(b'test', (MULTICAST_GROUP, DISCOVERY_PORT))
        except OSError:
            pytest.skip("Multicast discovery not supported on this host")
            return

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
    
    # Test getting players list
    players = game.players
    assert len(players) == 1
    assert players[0].name == "Alice"
    assert players[0].attributes['score'] == 100
    
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

def test_tls_data_exchange(tls_custom_game_server):
    """Tests complex data exchange over a TLS-encrypted connection."""
    port = TEST_PORT + 3
    client = GameClient(port=port, use_tls=True)
    
    # Create a game
    game = client.create_game(name="TLS Game", turn_based=True)
    assert game.game_id is not None
    
    # Add a player
    game.add_player(Player("TLS_Alice", score=100))
    
    # Check state
    state = game.state
    assert state['status'] == 'pending'
    
    # List games
    games = client.list_games()
    assert game.game_id in games
    
    # Verify player in state
    players = game.players
    assert len(players) == 1
    assert players[0].name == "TLS_Alice"
    
    game.stop()

def test_observer_network(game_server):
    """Tests adding and listing observers over the network."""
    client = GameClient(port=TEST_PORT)
    game = client.create_game(name="Observer Test", max_observers=1)
    
    obs = Observer("NetWatcher", status="observing")
    game.add_observer(obs)
    
    observers = game.observers
    assert len(observers) == 1
    assert observers[0].name == "NetWatcher"
    assert observers[0].attributes["status"] == "observing"
    
    # Verify limit
    with pytest.raises(exceptions.ObserverLimitReachedError):
        game.add_observer(Observer("TooMany"))

def test_game_password_success(game_server):
    """Tests joining a password-protected game with the correct password."""
    client = GameClient(port=TEST_PORT)
    game = client.create_game(password=TEST_GAME_PASSWORD)
    game.add_player(Player("Alice"), password=TEST_GAME_PASSWORD)
    # No error should be raised

def test_remote_game_lifecycle(game_server):
    """Tests the full lifecycle methods of RemoteGame (pause, resume, next_turn)."""
    client = GameClient(port=TEST_PORT)
    game = client.create_game(turn_based=True)
    game.add_player(Player("Alice"))
    game.start()
    
    game.pause()
    assert game.state['status'] == GameState.PENDING.value
    
    game.resume()
    assert game.state['status'] == GameState.IN_PROGRESS.value
    
    game.next_turn()
    # next_turn doesn't change status but we verify it doesn't crash
    assert game.state['status'] == GameState.IN_PROGRESS.value

def test_unknown_action(game_server):
    """Tests that the server handles unknown actions correctly."""
    client = GameClient(port=TEST_PORT)
    game = client.create_game()
    # We use _send_command directly to send an invalid action to a valid game
    with pytest.raises(exceptions.ServerError, match="Unknown action"):
        client._send_command('invalid_action', {'game_id': game.game_id})

def test_server_already_running(game_server):
    """Tests that starting an already running server is handled gracefully."""
    server = GameServer(host='0.0.0.0', port=TEST_PORT)
    # This should just print a message and return
    server.start()

def test_stop_non_running_server():
    """Tests stopping a server that isn't running."""
    server = GameServer(host='0.0.0.0', port=TEST_PORT + 5)
    server.stop() # Should print "Server is not running."

def test_get_current_player_no_players(game_server):
    """Tests get_current_player when a game is turn-based but has no players (and is not started)."""
    client = GameClient(port=TEST_PORT)
    game = client.create_game(turn_based=True)
    # Even if turn-based, it's not in progress, so it should raise GameLogicError
    with pytest.raises(exceptions.GameLogicError, match="Game is not in progress"):
        _ = game.current_player

def test_game_password_failure(game_server):
    """Tests that joining a password-protected game with the wrong password fails."""
    client = GameClient(port=TEST_PORT)
    game = client.create_game(password=TEST_GAME_PASSWORD)
    with pytest.raises(AuthenticationError, match="Invalid password for this game"):
        game.add_player(Player("Alice"), password="wrong_game_password")

