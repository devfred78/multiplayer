import pytest
import time
from multiplayer.game import PersistentPlayer
from multiplayer.server import GameServer
from multiplayer.client import GameClient

def test_persistent_player_as_observer():
    server = GameServer(port=65435)
    server.start()
    time.sleep(1)
    
    try:
        client = GameClient(port=65435)
        
        # 1. Créer un compte persistant
        client.create_account("Alice", "password123", team="Alpha")
        
        # 2. Créer une partie
        remote_game = client.create_game(name="Test Game")
        
        # 3. Tenter de rejoindre en tant qu'observateur
        alice = PersistentPlayer("Alice", "password123")
        remote_game.add_observer(alice)
        
        # Vérifier si Alice est bien dans la liste des observateurs
        observers = remote_game.observers
        assert len(observers) == 1
        assert observers[0].name == "Alice"
        # Vérifier la fusion des attributs (team="Alpha" vient du compte)
        assert observers[0].attributes.get("team") == "Alpha"
        
        # 4. Vérifier qu'une erreur d'authentification est levée avec un mauvais mot de passe
        wrong_alice = PersistentPlayer("Alice", "wrong_password")
        with pytest.raises(Exception) as excinfo:
            remote_game.add_observer(wrong_alice)
        assert "AuthenticationError" in str(excinfo.value) or "Invalid password" in str(excinfo.value)
        
        # 5. Vérifier la fusion des attributs spécifiques à la session
        bob_client = GameClient(port=65435)
        bob_client.create_account("Bob", "pass", role="player", user_type="User")
        bob = PersistentPlayer("Bob", "pass", temp_status="watching")
        remote_game.add_observer(bob)
        
        bob_observer = [o for o in remote_game.observers if o.name == "Bob"][0]
        assert bob_observer.attributes["user_type"] == "User"
        assert bob_observer.attributes["temp_status"] == "watching"
        
    finally:
        server.stop()

if __name__ == "__main__":
    test_persistent_player_as_observer()
