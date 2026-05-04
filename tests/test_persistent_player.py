import pytest
import time
from multiplayer.server import GameServer
from multiplayer.client import GameClient
from multiplayer.game import PersistentPlayer, Player
from multiplayer.exceptions import AuthenticationError, UserAlreadyExistsError

def wait_for_server(port, timeout=5):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            import socket
            with socket.create_connection(('127.0.0.1', port), timeout=1):
                return True
        except (ConnectionRefusedError, socket.timeout):
            time.sleep(0.1)
    return False

@pytest.fixture
def server():
    port = 65433
    server = GameServer(port=port)
    server.start()
    if not wait_for_server(port):
        server.stop()
        pytest.fail("Server failed to start")
    yield server
    server.stop()

def test_persistent_player_creation_and_auth(server):
    client = GameClient(port=65433)
    
    # 1. Create a persistent player account
    account_data = client.create_account("Alice", "secret123", avatar="elf")
    assert account_data['name'] == "Alice"
    
    # 2. Try to create the same account again (should fail)
    with pytest.raises(UserAlreadyExistsError):
        client.create_account("Alice", "other")
    
    # 3. Create a game and join as Alice with correct password
    remote_game = client.create_game(name="Test Game")
    
    alice = PersistentPlayer("Alice", "secret123")
    remote_game.add_player(alice)
    
    players = remote_game.players
    assert len(players) == 1
    assert players[0].name == "Alice"
    
    # 4. Try to join as Alice with wrong password (should fail)
    bob_client = GameClient(port=65433)
    remote_game2 = bob_client.create_game(name="Test Game 2")
    
    alice_imposter = PersistentPlayer("Alice", "wrong_password")
    with pytest.raises(AuthenticationError):
        remote_game2.add_player(alice_imposter)

def test_regular_player_still_works(server):
    client = GameClient(port=65433)
    remote_game = client.create_game(name="Test Game")
    
    charlie = Player("Charlie")
    remote_game.add_player(charlie)
    
    players = remote_game.players
    assert len(players) == 1
    assert players[0].name == "Charlie"
