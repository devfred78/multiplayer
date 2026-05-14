import unittest
import time
from multiplayer.server import GameServer
from multiplayer.client import GameClient, ServerAdmin
from multiplayer.exceptions import AuthenticationError

class TestPersistentPlayerRoles(unittest.TestCase):
    def setUp(self):
        self.host = '127.0.0.1'
        self.port = 65435
        self.admin_password = "admin_pass"
        self.server = GameServer(host=self.host, port=self.port, admin_password=self.admin_password)
        self.server.start()
        time.sleep(1) # Wait for server to start

    def tearDown(self):
        self.server.stop()
        time.sleep(1) # Wait for server to stop

    def test_role_based_access(self):
        # 1. Connect as global admin to create accounts
        admin = ServerAdmin(self.host, self.port, admin_password=self.admin_password)
        
        # Create a server admin account
        admin._client.create_account("super_admin", "super_pass", role="server_admin")
        
        # Create a group admin account
        admin.create_group("Test Group", admin_password="group_pass")
        groups = admin.list_groups()
        gid = next(iter(groups.keys()))
        
        admin._client.create_account("group_boss", "boss_pass", role="group_admin", managed_groups=[gid])
        
        # Create a simple player account
        admin._client.create_account("simple_player", "player_pass", role="player")
        
        # 2. Test Server Admin account
        sa_client = GameClient(self.host, self.port, auth_user="super_admin", auth_password="super_pass")
        sa_admin = sa_client.get_server_admin()
        
        # Should be able to list players (server admin action)
        players = sa_admin.list_all_players()
        self.assertIsInstance(players, list)
        
        # 3. Test Group Admin account
        ga_client = GameClient(self.host, self.port, auth_user="group_boss", auth_password="boss_pass")
        ga_admin = ga_client.get_group_admin(gid)
        
        # Should be able to list games in its group
        games = ga_admin.list_games()
        self.assertIsInstance(games, dict)
        
        # Should NOT be able to list all players (server admin action)
        sa_attempt = ga_client.get_server_admin()
        with self.assertRaises(AuthenticationError):
            sa_attempt.list_all_players()
            
        # 4. Test Simple Player account
        p_client = GameClient(self.host, self.port, auth_user="simple_player", auth_password="player_pass")
        
        # Should NOT be able to do group admin actions
        p_ga_attempt = p_client.get_group_admin(gid)
        with self.assertRaises(AuthenticationError):
            p_ga_attempt.list_games()
            
        # Should NOT be able to do server admin actions
        p_sa_attempt = p_client.get_server_admin()
        with self.assertRaises(AuthenticationError):
            p_sa_attempt.list_all_players()

    def test_invalid_credentials(self):
        # Create account
        admin = ServerAdmin(self.host, self.port, admin_password=self.admin_password)
        admin._client.create_account("user1", "pass1", role="player")
        
        # Test wrong password
        client = GameClient(self.host, self.port, auth_user="user1", auth_password="wrong_password")
        with self.assertRaises(AuthenticationError):
            client.list_games()
            
        # Test non-existent user
        client2 = GameClient(self.host, self.port, auth_user="non_existent", auth_password="any")
        with self.assertRaises(AuthenticationError):
            client2.list_games()

if __name__ == '__main__':
    unittest.main()
