import pytest
import time
from multiplayer import GameServer, GameClient, GroupAdmin, Player, AuthenticationError, exceptions

def test_group_admin_access():
    server = GameServer(port=65450, admin_password="server_admin")
    server.start()
    time.sleep(1)
    try:
        client = GameClient(port=65450)
        # Create a group via a command
        client._send_command('create_group', {'name': 'WarGames', 'admin_password': 'group_secret'})
        
        # Create games in that group
        client.create_game(name="Battlefield", group_name="WarGames")
        client.create_game(name="Chess", group_name="OtherGroup")
        
        # Group Admin for WarGames
        group_admin = GroupAdmin(group_name="WarGames", port=65450, group_admin_password="group_secret")
        games = group_admin.list_games()
        assert len(games) == 1
        # In this project, _send_command returns the 'data' part of the response
        # which is a dict mapping GID to attributes.
        assert any(attr.get('name') == "Battlefield" for attr in games.values())
        
        # Group Admin cannot see other group's games via list_group_games
        # and definitely cannot use list_games (server-wide) if they don't have server password
        
        # Try wrong password
        wrong_admin = GroupAdmin(group_name="WarGames", port=65450, group_admin_password="wrong")
        with pytest.raises(AuthenticationError):
            wrong_admin.list_games()
            
    finally:
        server.stop()

def test_group_admin_kick():
    server = GameServer(port=65451, admin_password="server_admin")
    server.start()
    time.sleep(1)
    try:
        client = GameClient(port=65451)
        client._send_command('create_group', {'name': 'WarGames', 'admin_password': 'group_secret'})
        
        rem1 = client.create_game(name="Battlefield", group_name="WarGames")
        g1_id = rem1.game_id
        
        rem2 = client.create_game(name="Peace", group_name="Other")
        g2_id = rem2.game_id
        
        # Players join
        rem1.add_player(Player("Target"))
        rem2.add_player(Player("Safe"))
        
        group_admin = GroupAdmin(group_name="WarGames", port=65451, group_admin_password="group_secret")
        
        # Kick Target (allowed)
        group_admin.kick_player(g1_id, "Target")
        assert len(rem1.players) == 0
        
        # Try to kick Safe (forbidden because it's in another group)
        with pytest.raises(exceptions.ServerError) as excinfo:
            group_admin.kick_player(g2_id, "Safe")
        assert 'does not belong to group' in str(excinfo.value)
        assert len(rem2.players) == 1
        
    finally:
        server.stop()

def test_server_admin_as_group_admin():
    server = GameServer(port=65452, admin_password="server_admin")
    server.start()
    time.sleep(1)
    try:
        client = GameClient(port=65452)
        client._send_command('create_group', {'name': 'WarGames', 'admin_password': 'group_secret'})
        
        # Server admin should be able to act as group admin using their own password
        server_acting_as_group = GroupAdmin(group_name="WarGames", port=65452, group_admin_password="server_admin")
        games = server_acting_as_group.list_games()
        # list_games for GroupAdmin returns dict of games (GID -> attributes)
        assert isinstance(games, dict)
        
    finally:
        server.stop()
