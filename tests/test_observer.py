import pytest
from multiplayer import Game, Observer, ObserverLimitReachedError

def test_observer_creation():
    """Tests that an observer can be created with attributes."""
    obs = Observer("Watcher", view_mode="full")
    assert obs.name == "Watcher"
    assert obs.attributes["view_mode"] == "full"

def test_game_with_observers():
    """Tests adding and removing observers in a local game."""
    game = Game(max_observers=2)
    obs1 = Observer("Obs1")
    obs2 = Observer("Obs2")
    obs3 = Observer("Obs3")
    
    game.add_observer(obs1)
    assert len(game.observers) == 1
    assert game.observers[0].name == "Obs1"
    
    game.add_observer(obs2)
    assert len(game.observers) == 2
    
    with pytest.raises(ObserverLimitReachedError):
        game.add_observer(obs3)
        
    game.remove_observer("Obs1")
    assert len(game.observers) == 1
    assert game.observers[0].name == "Obs2"
    
    # Observer should NOT be in the players list
    assert len(game.players) == 0

def test_game_start_without_players_but_with_observers():
    """Tests that a game cannot start without players, even if observers are present."""
    game = Game()
    game.add_observer(Observer("Watcher"))
    
    from multiplayer.exceptions import GameLogicError
    with pytest.raises(GameLogicError, match="Cannot start a game with no players"):
        game.start()

def test_observer_password_protection():
    """Tests that observers must respect the game password."""
    game = Game(password="secret")
    obs = Observer("Watcher")
    
    from multiplayer.exceptions import AuthenticationError
    with pytest.raises(AuthenticationError):
        game.add_observer(obs, password="wrong")
        
    game.add_observer(obs, password="secret")
    assert len(game.observers) == 1
