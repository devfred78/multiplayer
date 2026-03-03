"""
Unit tests for the client-server architecture.
"""
import pytest
import time
from multiplayer import GameServer, GameClient, Player
from multiplayer.exceptions import (
    ConnectionError,
    GameNotFoundError,
    PlayerLimitReachedError,
)

# Use a different port for testing to avoid conflicts
TEST_PORT = 65433

@pytest.fixture(scope="module")
def game_server():
    """Fixture to start and stop the game server for the test module."""
    server = GameServer(port=TEST_PORT)
    server.start()
    # Give the server a moment to start up
    time.sleep(0.1)
    yield
    server.stop()
    # Give the server a moment to shut down
    time.sleep(0.1)

def test_server_connection(game_server):
    """
    Tests that a client can connect to the server.
    """
    client = GameClient(port=TEST_PORT)
    # The connection itself is tested when a command is sent
    assert client.list_games() == {}

def test_create_and_list_games(game_server):
    """
    Tests that a client can create a game and see it in the list.
    """
    client = GameClient(port=TEST_PORT)
    game = client.create_game(name="Test Game", turn_based=True)
    assert game.game_id is not None
    
    games_list = client.list_games()
    assert game.game_id in games_list
    assert games_list[game.game_id]['name'] == "Test Game"

def test_game_proxy_interaction(game_server):
    """
    Tests that interactions with the RemoteGame proxy work as expected.
    """
    client = GameClient(port=TEST_PORT)
    game = client.create_game(turn_based=True)
    
    game.add_player(Player("Alice", score=100))
    game.start()
    
    current_player = game.current_player
    assert current_player is not None
    assert current_player.name == "Alice"
    assert current_player.attributes['score'] == 100
    
    assert game.state == "in_progress"
    
    game.next_turn() # Should not raise an error
    
    game.stop()
    assert game.state == "finished"

def test_error_handling(game_server):
    """
    Tests that the server correctly reports errors to the client.
    """
    client = GameClient(port=TEST_PORT)
    
    # Test GameNotFoundError
    with pytest.raises(GameNotFoundError):
        non_existent_game = client.create_game()
        # Manually create a proxy with a fake ID
        from multiplayer.client import RemoteGame
        fake_game = RemoteGame("fake-id", port=TEST_PORT)
        _ = fake_game.state

    # Test PlayerLimitReachedError
    game = client.create_game(max_players=1)
    game.add_player(Player("Alice"))
    with pytest.raises(PlayerLimitReachedError):
        game.add_player(Player("Bob"))

def test_connection_error():
    """
    Tests that a ConnectionError is raised if the server is not running.
    """
    client = GameClient(port=9999) # A port where no server is running
    with pytest.raises(ConnectionError):
        client.list_games()
