"""
This module provides classes for managing a multiplayer game.
"""

import enum

class GameState(enum.Enum):
    """
    Represents the state of the game.
    """
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"

class Player:
    """
    Represents a player in the game.

    Args:
        name (str): The name of the player.
        **kwargs: Additional attributes for the player.
    """
    def __init__(self, name, **kwargs):
        self.name = name
        self.attributes = kwargs

class Game:
    """
    Represents a multiplayer game.

    Args:
        max_players (int, optional): The maximum number of players allowed in the game. Defaults to None.
        turn_based (bool, optional): Whether the game is turn-based or simultaneous. Defaults to False.
        **kwargs: Additional attributes for the game.
    """
    def __init__(self, max_players=None, turn_based=False, **kwargs):
        self.max_players = max_players
        self.turn_based = turn_based
        self.attributes = kwargs
        self.players = []
        self.state = GameState.PENDING
        self.current_player_index = 0

    def add_player(self, player):
        """
        Adds a player to the game.

        Args:
            player (Player): The player to add.

        Raises:
            ValueError: If the maximum number of players has been reached.
        """
        if self.max_players is not None and len(self.players) >= self.max_players:
            raise ValueError("Maximum number of players reached")
        self.players.append(player)

    def start(self):
        """
        Starts the game.

        Raises:
            ValueError: If there are no players in the game.
        """
        if not self.players:
            raise ValueError("Cannot start a game with no players")
        self.state = GameState.IN_PROGRESS

    def pause(self):
        """
        Pauses the game.

        Raises:
            ValueError: If the game is not in progress.
        """
        if self.state != GameState.IN_PROGRESS:
            raise ValueError("Game is not in progress")
        self.state = GameState.PENDING

    def resume(self):
        """
        Resumes the game.

        Raises:
            ValueError: If the game is not pending.
        """
        if self.state != GameState.PENDING:
            raise ValueError("Game is not pending")
        self.state = GameState.IN_PROGRESS

    def stop(self):
        """
        Stops the game.
        """
        self.state = GameState.FINISHED

    def next_turn(self):
        """
        Advances to the next turn in a turn-based game.

        Raises:
            ValueError: If the game is not turn-based or not in progress.
        """
        if not self.turn_based:
            raise ValueError("Game is not turn-based")
        if self.state != GameState.IN_PROGRESS:
            raise ValueError("Game is not in progress")
        self.current_player_index = (self.current_player_index + 1) % len(self.players)

    @property
    def current_player(self):
        """
        The current player in a turn-based game.

        Returns:
            Player: The current player.

        Raises:
            ValueError: If the game is not turn-based or not in progress.
        """
        if not self.turn_based:
            raise ValueError("Game is not turn-based")
        if self.state != GameState.IN_PROGRESS:
            raise ValueError("Game is not in progress")
        return self.players[self.current_player_index]
