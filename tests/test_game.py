import pytest
import bcrypt
from multiplayer.game import Player, User, Game, GameGroup
from multiplayer import PlayerRole, GameState, ParameterFamily
from multiplayer.exceptions import (
    UserAlreadyExistsError, PasswordError, GameIsFullError, 
    GameAlreadyStartedError, GameIsFinishedError
)

def test_player_creation():
    p = Player("Alice", score=(ParameterFamily.DYNAMIC, 10), team=(ParameterFamily.STATIC, "Blue"))
    assert p.name == "Alice"
    assert p.dynamic_state["score"] == 10
    assert p.static_state["team"] == "Blue"
    assert p.ID is not None

def test_user_creation():
    u = User("bob", "password123", "bob@example.com")
    assert u.username == "bob"
    assert u.email == "bob@example.com"
    assert u.role == PlayerRole.PLAYER
    assert bcrypt.checkpw("password123".encode(), u.hash.encode())
    assert u.player.name == "bob"

def test_user_duplicate():
    User("duplicate", "pass")
    with pytest.raises(UserAlreadyExistsError):
        User("duplicate", "pass")

def test_game_lifecycle():
    g = Game(name="Test Game", turn_based=True)
    assert g.game_state == GameState.PENDING
    
    p1 = Player("P1")
    p2 = Player("P2")
    
    g.join_game_as_player(p1)
    g.join_game_as_player(p2)
    
    assert len(g.players) == 2
    
    g.start()
    assert g.game_state == GameState.IN_PROGRESS
    assert g.current_player.ID == p1.ID
    
    g.next_turn()
    assert g.current_player.ID == p2.ID
    
    g.pause()
    assert g.game_state == GameState.PAUSING
    
    g.resume()
    assert g.game_state == GameState.IN_PROGRESS
    
    g.stop()
    assert g.game_state == GameState.FINISHED

def test_game_passwords():
    g = Game(password="secret", observer_password="watch")
    p = Player("Observer")
    
    with pytest.raises(PasswordError):
        g.join_game_as_player(p, password="wrong")
        
    g.join_game_as_player(p, password="secret")
    
    o = Player("Watcher")
    with pytest.raises(PasswordError):
        g.join_game_as_observer(o, password="wrong")
        
    g.join_game_as_observer(o, password="watch")

def test_game_errors():
    g = Game(max_players=1, turn_based=True)
    p1 = Player("P1")
    p2 = Player("P2")
    
    g.join_game_as_player(p1)
    with pytest.raises(GameIsFullError):
        g.join_game_as_player(p2)
        
    g.start()
    with pytest.raises(GameAlreadyStartedError):
        g.start()
        
    g.stop()
    with pytest.raises(GameIsFinishedError):
        g.next_turn()

def test_game_group():
    group = GameGroup("My Group", type="ranked")
    g1 = Game("Game 1")
    group.add_game(g1)
    assert len(group.games) == 1
    assert group.parameters["type"] == "ranked"
    
    group.remove_game(g1)
    assert len(group.games) == 0
