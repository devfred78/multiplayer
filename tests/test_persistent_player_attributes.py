import pytest
import time
from multiplayer.server import GameServer
from multiplayer.client import GameClient
from multiplayer.game import PersistentPlayer, Player

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
    port = 65434
    admin_password = "admin_secret"
    server = GameServer(port=port, admin_password=admin_password)
    server.start()
    if not wait_for_server(port):
        server.stop()
        pytest.fail("Server failed to start")
    yield server
    server.stop()

def test_persistent_player_game_specific_attributes(server):
    client = GameClient(port=65434)
    
    # 1. Create a persistent player account with some global attributes
    client.create_account("Alice", "secret123", rank="Gold", avatar="elf")
    
    # 2. Join a game with game-specific attributes
    # The RemoteGame.add_player method uses player.attributes
    game1 = client.create_game(name="Strategy Game")
    alice1 = PersistentPlayer("Alice", "secret123", faction="Orcs", level=10)
    game1.add_player(alice1)
    
    players1 = game1.players
    assert len(players1) == 1
    attrs1 = players1[0].attributes
    
    # Verify merge: global + game-specific
    assert attrs1['rank'] == "Gold"
    assert attrs1['avatar'] == "elf"
    assert attrs1['faction'] == "Orcs"
    assert attrs1['level'] == 10
    
    # 3. Join another game with DIFFERENT game-specific attributes
    game2 = client.create_game(name="Racing Game")
    alice2 = PersistentPlayer("Alice", "secret123", car="Ferrari", speed=200)
    game2.add_player(alice2)
    
    players2 = game2.players
    attrs2 = players2[0].attributes
    
    # Verify merge: global + NEW game-specific
    assert attrs2['rank'] == "Gold"
    assert attrs2['avatar'] == "elf"
    assert attrs2['car'] == "Ferrari"
    assert attrs2['speed'] == 200
    # Should NOT have attributes from game1
    assert 'faction' not in attrs2
    assert 'level' not in attrs2

    # 4. Verify that global attributes are still there when listing all players via admin
    from multiplayer.client import ServerAdmin
    admin = ServerAdmin(port=65434, admin_password="admin_secret")
    all_players = admin.list_all_players()
    # Find all instances of Alice. One should be connected to game1, one to game2.
    # The persistent account (not connected) might NOT be in the list if the current implementation of list_all_players
    # marks them all as connected if they are in at least one game.
    
    alice_instances = [p for p in all_players if p['name'] == "Alice"]
    assert len(alice_instances) >= 2
    
    # Check that connected instances have merged attributes
    game1_alice = next(p for p in alice_instances if p['game_name'] == "Strategy Game")
    assert game1_alice['attributes']['faction'] == "Orcs"
    assert game1_alice['attributes']['rank'] == "Gold"
    
    game2_alice = next(p for p in alice_instances if p['game_name'] == "Racing Game")
    assert game2_alice['attributes']['car'] == "Ferrari"
    assert game2_alice['attributes']['rank'] == "Gold"
