import pytest
import time
from multiplayer import GameServer, GameAdmin

def test_server_name_initialization():
    server_name = "Test Server Instance"
    server = GameServer(port=65447, admin_password="admin_secret", name=server_name)
    server.start()
    time.sleep(1)
    try:
        admin = GameAdmin(port=65447, admin_password="admin_secret")
        info = admin.get_server_info()
        assert info.get('server_name') == server_name
    finally:
        server.stop()

def test_server_name_none_by_default():
    server = GameServer(port=65448, admin_password="admin_secret")
    server.start()
    time.sleep(1)
    try:
        admin = GameAdmin(port=65448, admin_password="admin_secret")
        info = admin.get_server_info()
        assert info.get('server_name') is None
    finally:
        server.stop()
