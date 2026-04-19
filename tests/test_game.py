"""
Unit tests for the local multiplayer game module.
"""
import pytest
from multiplayer import Game, Player, GameState
from multiplayer.exceptions import GameLogicError, PlayerLimitReachedError, AuthenticationError

def test_create_game():
    """
    Tests that a game can be created with default values.
    """
    game = Game()
    assert game.max_players is None
    assert not game.turn_based
    assert not game.players
    assert game.state == GameState.PENDING
    assert not game.attributes
    assert game.password is None

def test_create_game_with_password():
    """
    Tests that a game can be created with a password.
    """
    game = Game(password="secret")
    assert game.password == "secret"

def test_add_player_to_password_protected_game_success():
    """
    Tests that a player can join a password-protected game with the correct password.
    """
    game = Game(password="secret")
    player = Player("Alice")
    game.add_player(player, password="secret")
    assert len(game.players) == 1
    assert game.players[0] == player

def test_add_player_to_password_protected_game_no_password():
    """
    Tests that joining a password-protected game without a password fails.
    """
    game = Game(password="secret")
    player = Player("Alice")
    with pytest.raises(AuthenticationError, match="Invalid password for this game"):
        game.add_player(player)

def test_add_player_to_password_protected_game_wrong_password():
    """
    Tests that joining a password-protected game with the wrong password fails.
    """
    game = Game(password="secret")
    player = Player("Alice")
    with pytest.raises(AuthenticationError, match="Invalid password for this game"):
        game.add_player(player, password="wrong_secret")

def test_add_player_to_public_game_with_unnecessary_password():
    """
    Tests that providing a password to a public game still allows the player to join.
    """
    game = Game()
    player = Player("Alice")
    game.add_player(player, password="any_password")
    assert len(game.players) == 1

def test_create_game_with_options():
    """
    Tests that a game can be created with a maximum number of players and as turn-based.
    """
    game = Game(max_players=4, turn_based=True)
    assert game.max_players == 4
    assert game.turn_based
    assert not game.players
    assert game.state == GameState.PENDING

def test_create_game_with_attributes():
    """
    Tests that a game can be created with custom attributes.
    """
    game = Game(name="My Game", difficulty="Hard")
    assert game.attributes["name"] == "My Game"
    assert game.attributes["difficulty"] == "Hard"

def test_add_player():
    """
    Tests that a player can be added to a game.
    """
    game = Game()
    player = Player("Alice")
    game.add_player(player)
    assert len(game.players) == 1
    assert game.players[0] == player

def test_add_player_with_attributes():
    """
    Tests that a player can be added to a game with custom attributes.
    """
    game = Game()
    player = Player("Alice", score=100)
    game.add_player(player)
    assert len(game.players) == 1
    assert game.players[0] == player
    assert game.players[0].attributes["score"] == 100

def test_add_player_raises_error_when_max_players_reached():
    """
    Tests that adding a player to a full game raises PlayerLimitReachedError.
    """
    game = Game(max_players=1)
    game.add_player(Player("Alice"))
    with pytest.raises(PlayerLimitReachedError, match="Maximum number of players reached"):
        game.add_player(Player("Bob"))

def test_start_game():
    """
    Tests that a game can be started.
    """
    game = Game()
    game.add_player(Player("Alice"))
    game.start()
    assert game.state == GameState.IN_PROGRESS

def test_start_game_raises_error_with_no_players():
    """
    Tests that starting a game with no players raises GameLogicError.
    """
    game = Game()
    with pytest.raises(GameLogicError, match="Cannot start a game with no players"):
        game.start()

def test_pause_and_resume_game():
    """
    Tests that a game can be paused and resumed.
    """
    game = Game()
    game.add_player(Player("Alice"))
    game.start()
    assert game.state == GameState.IN_PROGRESS
    game.pause()
    assert game.state == GameState.PENDING
    game.resume()
    assert game.state == GameState.IN_PROGRESS

def test_pause_game_raises_error_if_not_in_progress():
    """
    Tests that pausing a game that is not in progress raises GameLogicError.
    """
    game = Game()
    with pytest.raises(GameLogicError, match="Game is not in progress"):
        game.pause()

def test_game_resume_not_paused():
    game = Game()
    game.add_player(Player("Alice"))
    game.start()
    with pytest.raises(GameLogicError, match="Game is not pending"):
        game.resume()

def test_game_next_turn_no_players():
    game = Game(turn_based=True)
    game.add_player(Player("Alice"))
    game.start()
    game.remove_player("Alice")
    # Now the game is back to PENDING because of remove_player logic
    assert game.state == GameState.PENDING
    with pytest.raises(GameLogicError, match="Game is not in progress"):
        game.next_turn()

def test_game_start_already_started():
    game = Game()
    game.add_player(Player("Alice"))
    game.start()
    with pytest.raises(GameLogicError, match="Game is already in progress"):
        game.start()

def test_resume_game_raises_error_if_not_pending():
    """
    Tests that resuming a game that is not pending raises GameLogicError.
    """
    game = Game()
    game.add_player(Player("Alice"))
    game.start()
    with pytest.raises(GameLogicError, match="Game is not pending"):
        game.resume()

def test_stop_game():
    """
    Tests that a game can be stopped.
    """
    game = Game()
    game.add_player(Player("Alice"))
    game.start()
    game.stop()
    assert game.state == GameState.FINISHED

def test_next_turn():
    """
    Tests that the turn can be advanced in a turn-based game.
    """
    game = Game(turn_based=True)
    alice = Player("Alice")
    bob = Player("Bob")
    game.add_player(alice)
    game.add_player(bob)
    game.start()
    assert game.current_player == alice
    game.next_turn()
    assert game.current_player == bob
    game.next_turn()
    assert game.current_player == alice

def test_next_turn_raises_error_if_not_turn_based():
    """
    Tests that advancing the turn in a non-turn-based game raises GameLogicError.
    """
    game = Game()
    with pytest.raises(GameLogicError, match="Game is not turn-based"):
        game.next_turn()

def test_current_player_raises_error_if_not_turn_based():
    """
    Tests that getting the current player in a non-turn-based game raises GameLogicError.
    """
    game = Game()
    with pytest.raises(GameLogicError, match="Game is not turn-based"):
        _ = game.current_player

def test_remove_player():
    """
    Tests that a player can be removed from a game.
    """
    game = Game(turn_based=True)
    alice = Player("Alice")
    bob = Player("Bob")
    game.add_player(alice)
    game.add_player(bob)
    game.start()
    
    assert len(game.players) == 2
    game.remove_player("Alice")
    assert len(game.players) == 1
    assert game.players[0] == bob
    assert game.current_player == bob
