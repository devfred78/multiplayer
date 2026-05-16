"""
This module provides classes for managing a multiplayer game.
"""

import enum
import uuid
from datetime import datetime
from .exceptions import (
    GameLogicError, 
    PlayerLimitReachedError, 
    ObserverLimitReachedError, 
    AuthenticationError,
    PlayerAlreadyInGameError
)

class GameState(enum.Enum):
    """
    Represents the state of the game.
    """
    PENDING = "pending"
    PAUSING = "pausing"
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
        self._id = str(uuid.uuid4())

    def _force_id(self, id):
        """
        Internal use only to restore an object with a specific ID.
        """
        self._id = id

    @property
    def ID(self):
        """
        The unique ID of the player.
        """
        return self._id

class PlayerRole(enum.Enum):
    """
    Represents the role of a persistent player.
    """
    PLAYER = "player"
    GROUP_ADMIN = "group_admin"
    SERVER_ADMIN = "server_admin"

class PersistentPlayer(Player):
    """
    Represents a persistent player with a password.

    Args:
        name (str): The name of the player.
        password (str): The password for the account.
        role (PlayerRole, optional): The role of the player. Defaults to PlayerRole.PLAYER.
        managed_groups (list, optional): A list of group IDs managed by this player if role is GROUP_ADMIN.
        **kwargs: Additional attributes for the player.
    """
    def __init__(self, name, password, role=PlayerRole.PLAYER, managed_groups=None, **kwargs):
        super().__init__(name, **kwargs)
        self.password = password
        self.role = role
        self.managed_groups = managed_groups or []

    @property
    def role(self):
        """
        The role of the player.
        """
        return self._role

    @role.setter
    def role(self, value):
        if not isinstance(value, PlayerRole):
            raise TypeError("role must be an instance of PlayerRole")
        self._role = value

class GameGroup:
    """
    Represents a group of games on a server.

    Args:
        name (str): The name of the group.
        admin_password (str, optional): A password for administrative actions on this group.
        **kwargs: Additional attributes for the group.
    """
    def __init__(self, name, admin_password=None, **kwargs):
        self.name = name
        self.admin_password = admin_password
        self.attributes = kwargs
        self.games = []
        self._id = str(uuid.uuid4())

    @property
    def ID(self):
        """
        The unique ID of the group.
        """
        return self._id

    def add_game(self, game):
        """
        Adds a game to the group.

        Args:
            game (Game): The game to add.
        """
        if game not in self.games:
            self.games.append(game)

    def remove_game(self, game_id):
        """
        Removes a game from the group by ID.

        Args:
            game_id (str): The ID of the game to remove.
        """
        game_to_remove = next((g for g in self.games if g.ID == game_id), None)
        if game_to_remove:
            self.games.remove(game_to_remove)

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
        self._id = str(uuid.uuid4())

    def _force_id(self, id):
        """
        Internal use only to restore an object with a specific ID.
        """
        self._id = id

    @property
    def ID(self):
        """
        The unique ID of the observer.
        """
        return self._id

class Game:
    """
    Represents a game instance.
    
    Args:
        name (str, optional): Name of the game.
        max_players (int, optional): Maximum number of players.
        max_observers (int, optional): Maximum number of observers.
        turn_based (bool): Whether the game is turn-based.
        password (str, optional): Password to join as a player.
        observer_password (str, optional): Password to join as an observer.
        **kwargs: Additional attributes for the game.
    """
    def __init__(self, name=None, max_players=None, max_observers=None, turn_based=False, password=None, observer_password=None, **kwargs):
        self.name = name
        self.max_players = max_players
        self.max_observers = max_observers
        self.turn_based = turn_based
        self.password = password
        self.observer_password = observer_password
        self.attributes = kwargs
        self.players = []
        self.observers = []
        self.state = GameState.PENDING
        self.current_player_index = 0
        self.custom_state = {}
        self.kicked_ids = set() # Track players/observers who have been kicked
        self.start_time = None
        self.end_time = None
        self._id = str(uuid.uuid4())

    @property
    def ID(self):
        """
        The unique ID of the game.
        """
        return self._id

    def _force_id(self, id):
        """
        Forces the ID of the game. Use with caution, mainly for persistence.
        """
        self._id = id

    def add_player(self, player, password=None):
        """
        Adds a player to the game.

        Args:
            player (Player): The player to add.
            password (str, optional): The password required to join the game.

        Raises:
            AuthenticationError: If the provided password does not match the game's password.
            PlayerLimitReachedError: If the maximum number of players has been reached.
            PlayerAlreadyInGameError: If the player is already in the game.
        """
        if any(p.ID == player.ID for p in self.players):
            raise PlayerAlreadyInGameError(f"Player with ID {player.ID} is already in the game")
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
            password (str, optional): The password required to join the game as an observer.

        Raises:
            AuthenticationError: If the provided password does not match the observer password (or game password if no observer password is set).
            ObserverLimitReachedError: If the maximum number of observers has been reached.
            PlayerAlreadyInGameError: If the observer is already in the game.
        """
        if any(o.ID == observer.ID for o in self.observers):
            raise PlayerAlreadyInGameError(f"Observer with ID {observer.ID} is already in the game")
        required_password = self.observer_password if self.observer_password is not None else self.password
        if required_password is not None and required_password != password:
            raise AuthenticationError("Invalid password for this game")
        if self.max_observers is not None and len(self.observers) >= self.max_observers:
            raise ObserverLimitReachedError("Maximum number of observers reached")
        self.observers.append(observer)

    def remove_player(self, player_id):
        """
        Removes a player from the game by ID.

        Args:
            player_id (str): The ID of the player to remove.
        """
        player_to_remove = next((p for p in self.players if p.ID == player_id), None)
        if player_to_remove:
            removed_player_index = self.players.index(player_to_remove)
            self.players.remove(player_to_remove)
            self.kicked_ids.add(player_id)
            
            if self.turn_based and self.state == GameState.IN_PROGRESS:
                if not self.players:
                    self.state = GameState.PAUSING
                elif self.current_player_index >= removed_player_index:
                    self.current_player_index = self.current_player_index % len(self.players)

    def remove_observer(self, observer_id):
        """
        Removes an observer from the game by ID.

        Args:
            observer_id (str): The ID of the observer to remove.
        """
        observer_to_remove = next((o for o in self.observers if o.ID == observer_id), None)
        if observer_to_remove:
            self.observers.remove(observer_to_remove)
            self.kicked_ids.add(observer_id)

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
        self.start_time = datetime.now().isoformat()

    def pause(self):
        """
        Pauses the game.

        Raises:
            GameLogicError: If the game is not in progress.
        """
        if self.state != GameState.IN_PROGRESS:
            raise GameLogicError("Game is not in progress")
        self.state = GameState.PAUSING

    def resume(self):
        """
        Resumes the game.

        Raises:
            GameLogicError: If the game is not pausing.
        """
        if self.state != GameState.PAUSING:
            raise GameLogicError("Game is not pausing")
        self.state = GameState.IN_PROGRESS

    def stop(self):
        """
        Stops the game.
        """
        self.state = GameState.FINISHED
        self.end_time = datetime.now().isoformat()

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