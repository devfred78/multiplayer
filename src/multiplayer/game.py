"""
This module provides classes for managing a multiplayer game.
"""

import enum
from .exceptions import GameLogicError, PlayerLimitReachedError, ObserverLimitReachedError, AuthenticationError

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

class Observer:
    """
    Represents an observer in the game.

    Args:
        name (str): The name of the observer.
        **kwargs: Additional attributes for the observer.
    """
    def __init__(self, name, **kwargs):
        self.name = name
        self.attributes = kwargs

class Game:
    """
    Represents a multiplayer game.

    Args:
        name (str, optional): The name of the game session. Defaults to None.
        max_players (int, optional): The maximum number of players allowed in the game. Defaults to None.
        max_observers (int, optional): The maximum number of observers allowed in the game. Defaults to None.
        turn_based (bool, optional): Whether the game is turn-based or simultaneous. Defaults to False.
        password (str, optional): A password to protect this specific game.
        **kwargs: Additional attributes for the game.
    """
    def __init__(self, name=None, max_players=None, max_observers=None, turn_based=False, password=None, **kwargs):
        self.name = name
        self.max_players = max_players
        self.max_observers = max_observers
        self.turn_based = turn_based
        self.password = password
        self.attributes = kwargs
        self.players = []
        self.observers = []
        self.state = GameState.PENDING
        self.current_player_index = 0
        self.custom_state = {}

    def add_player(self, player, password=None):
        """
        Adds a player to the game.

        Args:
            player (Player): The player to add.
            password (str, optional): The password required to join the game.

        Raises:
            AuthenticationError: If the provided password does not match the game's password.
            PlayerLimitReachedError: If the maximum number of players has been reached.
        """
        if self.password is not None and self.password != password:
            raise AuthenticationError("Invalid password for this game")
        if self.max_players is not None and len(self.players) >= self.max_players:
            raise PlayerLimitReachedError("Maximum number of players reached")
        self.players.append(player)

    def add_observer(self, observer, password=None):
        """
        Adds an observer to the game.

        Args:
            observer (Observer): The observer to add.
            password (str, optional): The password required to join the game.

        Raises:
            AuthenticationError: If the provided password does not match the game's password.
            ObserverLimitReachedError: If the maximum number of observers has been reached.
        """
        if self.password is not None and self.password != password:
            raise AuthenticationError("Invalid password for this game")
        if self.max_observers is not None and len(self.observers) >= self.max_observers:
            raise ObserverLimitReachedError("Maximum number of observers reached")
        self.observers.append(observer)

    def remove_player(self, player_name):
        """
        Removes a player from the game by name.

        Args:
            player_name (str): The name of the player to remove.
        """
        player_to_remove = next((p for p in self.players if p.name == player_name), None)
        if player_to_remove:
            removed_player_index = self.players.index(player_to_remove)
            self.players.remove(player_to_remove)
            
            if self.turn_based and self.state == GameState.IN_PROGRESS:
                if not self.players:
                    self.state = GameState.PENDING
                elif self.current_player_index >= removed_player_index:
                    self.current_player_index = self.current_player_index % len(self.players)

    def remove_observer(self, observer_name):
        """
        Removes an observer from the game by name.

        Args:
            observer_name (str): The name of the observer to remove.
        """
        observer_to_remove = next((o for o in self.observers if o.name == observer_name), None)
        if observer_to_remove:
            self.observers.remove(observer_to_remove)

    def start(self):
        """
        Starts the game.

        Raises:
            GameLogicError: If there are no players in the game or if the game is already in progress.
        """
        if self.state == GameState.IN_PROGRESS:
            raise GameLogicError("Game is already in progress")
        if not self.players:
            raise GameLogicError("Cannot start a game with no players")
        self.state = GameState.IN_PROGRESS

    def pause(self):
        """
        Pauses the game.

        Raises:
            GameLogicError: If the game is not in progress.
        """
        if self.state != GameState.IN_PROGRESS:
            raise GameLogicError("Game is not in progress")
        self.state = GameState.PENDING

    def resume(self):
        """
        Resumes the game.

        Raises:
            GameLogicError: If the game is not pending.
        """
        if self.state != GameState.PENDING:
            raise GameLogicError("Game is not pending")
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
            GameLogicError: If the game is not turn-based or not in progress.
        """
        if not self.turn_based:
            raise GameLogicError("Game is not turn-based")
        if self.state != GameState.IN_PROGRESS:
            raise GameLogicError("Game is not in progress")
        if self.players:
            self.current_player_index = (self.current_player_index + 1) % len(self.players)

    @property
    def current_player(self):
        """
        The current player in a turn-based game.

        Returns:
            Player: The current player.

        Raises:
            GameLogicError: If the game is not turn-based or not in progress.
        """
        if not self.turn_based:
            raise GameLogicError("Game is not turn-based")
        if self.state != GameState.IN_PROGRESS:
            raise GameLogicError("Game is not in progress")
        if not self.players:
            return None
        return self.players[self.current_player_index]
