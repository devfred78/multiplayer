import pytest
import bcrypt
from multiplayer.game import Player, User, Game, GameGroup
from multiplayer import UserRole, GameState, ParameterFamily
from multiplayer.exceptions import (
    UserAlreadyExistsError, PasswordError, GameIsFullError, 
    GameAlreadyStartedError, GameIsFinishedError, NotEnoughPlayersError,
    PlayerNotFoundError, PlayerNotFoundInGameError
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
    assert u.role == UserRole.PLAYER
    assert bcrypt.checkpw("password123".encode(), u.hash.encode())
    assert u.players_id == []

def test_user_players_id_is_mutable_but_read_only():
    u = User("carol", "password123")
    u.players_id.append("player-1")
    u.players_id.extend(["player-2", "player-3"])
    u.players_id.pop()
    assert u.players_id == ["player-1", "player-2"]
    with pytest.raises(AttributeError):
        u.players_id = []

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
    
    assert g.players == (p1.ID, p2.ID)
    
    g.start()
    assert g.game_state == GameState.IN_PROGRESS
    assert g.current_player == p1.ID
    
    g.next_turn()
    assert g.current_player == p2.ID
    
    g.pause()
    assert g.game_state == GameState.PAUSING
    
    g.resume()
    assert g.game_state == GameState.IN_PROGRESS
    
    g.stop()
    assert g.game_state == GameState.FINISHED

def test_game_stores_participant_ids():
    g = Game(turn_based=True)
    p1, p2, p3 = Player("P1"), Player("P2"), Player("P3")
    watcher = Player("Watcher")
    for player in (p1, p2, p3):
        g.join_game_as_player(player)
    g.join_game_as_observer(watcher)

    assert g.players == (p1.ID, p2.ID, p3.ID)
    assert g.observers == (watcher.ID,)
    assert all(isinstance(player_id, str) for player_id in g.players + g.observers)

    g.set_player_rank(p3, 0)
    assert g.players == (p3.ID, p1.ID, p2.ID)
    g.set_player_rank(p1.ID, 2)
    assert g.players == (p3.ID, p2.ID, p1.ID)
    with pytest.raises(IndexError):
        g.set_player_rank(p2, 3)
    assert g.players == (p3.ID, p2.ID, p1.ID)
    g.reverse_order()
    assert g.players == (p1.ID, p2.ID, p3.ID)

    g.remove_player(p2)
    g.remove_player(p3.ID)
    g.remove_observer(watcher.ID)
    assert g.players == (p1.ID,)
    assert g.observers == ()
    with pytest.raises(PlayerNotFoundInGameError):
        g.remove_player(p2.ID)
    with pytest.raises(PlayerNotFoundInGameError):
        g.remove_observer(watcher)

def test_game_rejects_unknown_player_id():
    g = Game()
    with pytest.raises(PlayerNotFoundError):
        g.join_game_as_player("unknown-id")
    with pytest.raises(PlayerNotFoundError):
        g.join_game_as_observer("unknown-id")
    assert g.players == ()
    assert g.observers == ()

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

def test_game_min_players_default_allows_empty_start():
    g = Game()
    assert g.min_players == 0
    g.start()
    assert g.game_state == GameState.IN_PROGRESS

def test_game_min_players_blocks_start():
    g = Game(min_players=2)
    g.join_game_as_player(Player("P1"))
    with pytest.raises(NotEnoughPlayersError):
        g.start()
    assert g.game_state == GameState.PENDING

    g.join_game_as_player(Player("P2"))
    g.start()
    assert g.game_state == GameState.IN_PROGRESS

def test_game_min_players_capped_by_max_players():
    g = Game(min_players=5, max_players=2)
    assert g.min_players == 2
    g.join_game_as_player(Player("P1"))
    with pytest.raises(NotEnoughPlayersError):
        g.start()
    g.join_game_as_player(Player("P2"))
    g.start()
    assert g.game_state == GameState.IN_PROGRESS

def test_game_min_players_not_capped_without_max_players():
    assert Game(min_players=5).min_players == 5

def test_game_group():
    group = GameGroup("My Group", type="ranked")
    g1 = Game("Game 1")
    group.add_game(g1)
    assert len(group.games) == 1
    assert group.parameters["type"] == "ranked"
    
    group.remove_game(g1)
    assert len(group.games) == 0
