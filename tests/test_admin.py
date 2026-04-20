import pytest
import time
from multiplayer import GameServer, GameClient, GameAdmin, Player, AuthenticationError

def test_admin_authentication_success():
    server = GameServer(port=65440, admin_password="admin_secret")
    server.start()
    time.sleep(1)
    try:
        admin = GameAdmin(port=65440, admin_password="admin_secret")
        info = admin.get_server_info()
        assert 'games_count' in info
    finally:
        server.stop()

def test_admin_authentication_failure():
    server = GameServer(port=65441, admin_password="admin_secret")
    server.start()
    time.sleep(1)
    try:
        admin = GameAdmin(port=65441, admin_password="wrong_password")
        with pytest.raises(AuthenticationError):
            admin.get_server_info()
    finally:
        server.stop()

def test_admin_kick_player():
    server = GameServer(port=65442, admin_password="admin_secret")
    server.start()
    time.sleep(1)
    try:
        client = GameClient(port=65442)
        remote_game = client.create_game(name="KickTest")
        remote_game.add_player(Player("Victim"))
        
        assert len(remote_game.players) == 1
        
        admin = GameAdmin(port=65442, admin_password="admin_secret")
        admin.kick_player(remote_game.game_id, "Victim")
        
        assert len(remote_game.players) == 0
    finally:
        server.stop()

def test_admin_stop_server():
    server = GameServer(port=65443, admin_password="admin_secret")
    server.start()
    time.sleep(1)
    
    admin = GameAdmin(port=65443, admin_password="admin_secret")
    admin.stop_server()
    
    time.sleep(1)
    # The process should be dead. GameServer.stop() might still be called in finally but it should handle it.
    assert not server._server_process.is_alive()
    server.stop() # Cleanup discovery service

def test_admin_restart_server():
    server = GameServer(port=65444, admin_password="admin_secret")
    server.start()
    time.sleep(1)
    try:
        client = GameClient(port=65444)
        client.create_game(name="GameToClear")
        
        admin = GameAdmin(port=65444, admin_password="admin_secret")
        info = admin.get_server_info()
        assert info['games_count'] == 1
        
        admin.restart_server()
        time.sleep(1) # Laisse le temps au thread de vider les jeux
        
        info = admin.get_server_info()
        assert info['games_count'] == 0
    finally:
        server.stop()

def test_admin_list_all_players():
    server = GameServer(port=65446, admin_password="admin_secret")
    server.start()
    time.sleep(1)
    try:
        client = GameClient(port=65446)
        
        # Game 1
        g1 = client.create_game(name="Game1")
        g1.add_player(Player("Alice"))
        g1.add_player(Player("Bob"))
        
        # Game 2
        g2 = client.create_game(name="Game2")
        g2.add_player(Player("Charlie"))
        
        admin = GameAdmin(port=65446, admin_password="admin_secret")
        players_info = admin.list_all_players()
        
        assert len(players_info) == 3
        
        alice = next(p for p in players_info if p['name'] == 'Alice')
        assert alice['game_id'] == g1.game_id
        assert alice['game_name'] == 'Game1'
        
        charlie = next(p for p in players_info if p['name'] == 'Charlie')
        assert charlie['game_id'] == g2.game_id
        assert charlie['game_name'] == 'Game2'
    finally:
        server.stop()
