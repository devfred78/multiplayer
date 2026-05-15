import time
import os
import shutil
from multiplayer import GameServer, GameClient, ServerAdmin

def test_persistence_none():
    port = 65450
    admin_pass = "admin_secret"
    # Mode persistence 'none' (default)
    server = GameServer(port=port, admin_password=admin_pass)
    server.start()
    time.sleep(1)
    try:
        client = GameClient(port=port)
        client.create_game(name="TempGame")
        
        admin = ServerAdmin(port=port, admin_password=admin_pass)
        assert len(admin.list_all_server_games()) == 1
    finally:
        server.stop()
    
    # Redémarrage du serveur : les données doivent avoir disparu
    server = GameServer(port=port, admin_password=admin_pass)
    server.start()
    time.sleep(1)
    try:
        admin = ServerAdmin(port=port, admin_password=admin_pass)
        assert len(admin.list_all_server_games()) == 0
    finally:
        server.stop()

def test_persistence_json(tmp_path):
    port = 65451
    admin_pass = "admin_secret"
    persistence_file = tmp_path / "server_data.json"
    
    # Premier lancement avec persistance JSON
    server = GameServer(port=port, admin_password=admin_pass, persistence_type="json", persistence_path=str(persistence_file))
    server.start()
    time.sleep(1)
    try:
        client = GameClient(port=port)
        client.create_game(name="PersistentJSONGame")
        
        # Création d'un joueur persistant via create_account
        client.create_account("UserJSON", "pass")
        
        admin = ServerAdmin(port=port, admin_password=admin_pass)
        assert len(admin.list_all_server_games()) == 1
    finally:
        server.stop()
    
    assert persistence_file.exists()
    
    # Deuxième lancement : les données doivent être restaurées
    server = GameServer(port=port, admin_password=admin_pass, persistence_type="json", persistence_path=str(persistence_file))
    server.start()
    time.sleep(1)
    try:
        admin = ServerAdmin(port=port, admin_password=admin_pass)
        assert len(admin.list_all_server_games()) == 1
        
        players = admin.list_all_players()
        assert any(p['name'] == "UserJSON" for p in players.values())
    finally:
        server.stop()

def test_persistence_sqlite(tmp_path):
    port = 65452
    admin_pass = "admin_secret"
    persistence_file = tmp_path / "server_data.db"
    
    # Premier lancement avec persistance SQLite
    server = GameServer(port=port, admin_password=admin_pass, persistence_type="sqlite", persistence_path=str(persistence_file))
    server.start()
    time.sleep(1)
    try:
        client = GameClient(port=port)
        client.create_game(name="PersistentSQLiteGame")
        
        # Création d'un joueur persistant via create_account
        client.create_account("UserSQLite", "pass")
        
        admin = ServerAdmin(port=port, admin_password=admin_pass)
        assert len(admin.list_all_server_games()) == 1
    finally:
        server.stop()
    
    assert persistence_file.exists()
    
    # Deuxième lancement : les données doivent être restaurées
    server = GameServer(port=port, admin_password=admin_pass, persistence_type="sqlite", persistence_path=str(persistence_file))
    server.start()
    time.sleep(1)
    try:
        admin = ServerAdmin(port=port, admin_password=admin_pass)
        assert len(admin.list_all_server_games()) == 1
        
        players = admin.list_all_players()
        assert any(p['name'] == "UserSQLite" for p in players.values())
    finally:
        server.stop()

def test_persistence_invalid_path():
    port = 65453
    admin_pass = "admin_secret"
    # Un dossier au lieu d'un fichier
    invalid_path = "test_dir_as_file"
    os.makedirs(invalid_path, exist_ok=True)
    try:
        # On teste le comportement de run_server.py en simulant l'appel via subprocess
        import subprocess
        import sys
        
        cmd = [
            sys.executable, "-m", "multiplayer.run_server",
            "--port", str(port),
            "--admin-password", admin_pass,
            "--persistence", "json",
            "--persistence-path", invalid_path
        ]
        
        # On s'attend à ce que run_server.py s'arrête avec le code 1 à cause de la validation CLI
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        assert result.returncode == 1
        assert f"Error: Persistence path '{invalid_path}' is a directory." in result.stdout or f"Error: Persistence path '{invalid_path}' is a directory." in result.stderr
    finally:
        if os.path.exists(invalid_path):
            shutil.rmtree(invalid_path)
