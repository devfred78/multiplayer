import pytest
import time
from multiplayer import GameServer, GameClient, ServerAdmin, GroupAdmin, Player, AuthenticationError, exceptions

def test_group_admin_access():
    server = GameServer(port=65450, admin_password="server_admin")
    server.start()
    time.sleep(1)
    try:
        admin = ServerAdmin(port=65450, admin_password="server_admin")
        # Create a group via a command
        res = admin.create_group('WarGames', admin_password='group_secret')
        group_id = res.group_id
        
        # Create games in that group
        client = GameClient(port=65450)
        client.create_game(name="Battlefield", group_id=group_id)
        # Note: Chess will be in a group named "OtherGroup" (created automatically by server for backward compat?)
        # Actually server now uses group_id.
        res2 = admin.create_group("OtherGroup")
        other_group_id = res2.group_id
        client.create_game(name="Chess", group_id=other_group_id)
        
        # Group Admin for WarGames
        group_admin = GroupAdmin(group_id=group_id, port=65450, group_admin_password="group_secret")
        games = group_admin.list_games()
        assert len(games) == 1
        # list_games now returns a dict mapping GID to game data.
        assert any(game['name'] == "Battlefield" for game in games.values())
        # Actually, let's just check if we can access the games.
        # We can't easily check the name without a command, but RemoteGame doesn't have .name property.
        # But we know there is 1 game.
        
        # Group Admin cannot see other group's games via list_group_games
        # and definitely cannot use list_games (server-wide) if they don't have server password
        
        # Try wrong password
        wrong_admin = GroupAdmin(group_id=group_id, port=65450, group_admin_password="wrong")
        with pytest.raises(AuthenticationError):
            wrong_admin.list_games()
            
    finally:
        server.stop()

def test_group_admin_kick():
    server = GameServer(port=65451, admin_password="server_admin")
    server.start()
    time.sleep(1)
    try:
        admin = ServerAdmin(port=65451, admin_password="server_admin")
        res = admin.create_group('WarGames', admin_password='group_secret')
        group_id = res.group_id
        
        client = GameClient(port=65451)
        rem1 = client.create_game(name="Battlefield", group_id=group_id)
        g1_id = rem1.game_id
        
        res2 = admin.create_group('Other')
        other_group_id = res2.group_id
        rem2 = client.create_game(name="Peace", group_id=other_group_id)
        g2_id = rem2.game_id
        
        # Players join
        rem1.add_player(Player("Target"))
        rem2.add_player(Player("Safe"))
        
        group_admin = GroupAdmin(group_id=group_id, port=65451, group_admin_password="group_secret")
        
        # Kick Target (allowed)
        # We need the ID of the player "Target"
        target_id = None
        for p in rem1.players:
            if p.name == "Target":
                target_id = p.ID
                break
        
        group_admin.kick_player(g1_id, target_id)
        assert len(rem1.players) == 0
        
        # Try to kick Safe (forbidden because it's in another group)
        safe_id = None
        for p in rem2.players:
            if p.name == "Safe":
                safe_id = p.ID
                break
        with pytest.raises(exceptions.ServerError) as excinfo:
            group_admin.kick_player(g2_id, safe_id)
        assert 'does not belong to group' in str(excinfo.value)
        assert len(rem2.players) == 1
        
    finally:
        server.stop()

def test_server_admin_as_group_admin():
    server = GameServer(port=65452, admin_password="server_admin")
    server.start()
    time.sleep(1)
    try:
        admin = ServerAdmin(port=65452, admin_password="server_admin")
        res = admin.create_group('WarGames', admin_password='group_secret')
        group_id = res.group_id
        
        # Server admin should be able to act as group admin using their own password
        server_acting_as_group = GroupAdmin(group_id=group_id, port=65452, group_admin_password="server_admin")
        games = server_acting_as_group.list_games()
        # list_games for GroupAdmin returns dict of games (GID -> attributes)
        assert isinstance(games, dict)
        
    finally:
        server.stop()
