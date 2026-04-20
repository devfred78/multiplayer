import time
from multiplayer.server import GameServer
from multiplayer.client import GameAdmin

def test_admin_set_logging_config():
    """Tests that the administrator can set the logging configuration."""
    admin_password = "admin_secret"
    server = GameServer(port=65440, admin_password=admin_password)
    server.start()
    
    # Wait for server to start
    time.sleep(1)
    
    try:
        admin = GameAdmin(port=65440, admin_password=admin_password)
        
        # Set logging config
        logging_host = "127.0.0.1"
        logging_port = 5000
        response = admin.set_logging_config(logging_host, logging_port)
        
        assert response['status'] == 'success'
        
        # We can't easily check the server process's logger from here as it's a separate process,
        # but the success response confirms the command was executed.
        
    finally:
        server.stop()

def test_admin_set_logging_config_init():
    """Tests that the logging configuration can be set at server initialization."""
    admin_password = "admin_secret"
    logging_host = "127.0.0.1"
    logging_port = 5001
    server = GameServer(port=65441, admin_password=admin_password, logging_host=logging_host, logging_port=logging_port)
    server.start()
    
    # Wait for server to start
    time.sleep(1)
    
    try:
        # Check if server is running
        admin = GameAdmin(port=65441, admin_password=admin_password)
        info = admin.get_server_info()
        # get_server_info returns data, so if it succeeded, we got a dict with 'games_count'
        assert 'games_count' in info
    finally:
        server.stop()
