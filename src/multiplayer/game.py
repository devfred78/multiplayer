"""Game logic for the multiplayer library."""
import uuid
from typing import List, Tuple, Dict, Any
import bcrypt
from . import PlayerRole, GameState, ParameterFamily
from .exceptions import (
    UserAlreadyExistsError,
    PlayerNotFoundError,
    PlayerNotFoundInGameError,
    PasswordError,
    GameIsFullError,
    GameAlreadyStartedError,
    GameIsFinishedError,
    GameNotStartedError,
    GameAlreadyPausedError,
    GameNotPausedError,
    GameNotTurnBasedError,
    GameNotFoundError,
    GameNotFoundInGroupError,
)

class Player:
    """Represents a player in the game context."""

    def __init__(self, name: str, **kwargs: Any):
        """Initializes a new player.

        Args:
            name: The name of the player.
            **kwargs: Optional parameters in the form (ParameterFamily, value).
        """
        self._id: str = str(uuid.uuid4())
        self.name: str = name
        self.static_state: Dict[str, Any] = {}
        self.dynamic_state: Dict[str, Any] = {}

        for key, value in kwargs.items():
            if isinstance(value, tuple) and len(value) == 2 and isinstance(value[0], ParameterFamily):
                family, val = value
                if family == ParameterFamily.STATIC:
                    self.static_state[key] = val
                else:
                    self.dynamic_state[key] = val

    @property
    def ID(self) -> str:
        """The unique identifier of the player."""
        return self._id

class User:
    """Represents a user account."""
    _existing_usernames: set[str] = set()

    def __init__(self, username: str, password: str, email: str = ""):
        """Initializes a new user.

        Args:
            username: The username of the account.
            password: The password of the account.
            email: The email address of the account.

        Raises:
            UserAlreadyExistsError: If the username is already taken.
        """
        if username in User._existing_usernames:
            raise UserAlreadyExistsError(f"User '{username}' already exists.")
        
        self._id: str = str(uuid.uuid4())
        self._username: str = username
        self._hash: str = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        self.email: str = email
        self.role: PlayerRole = PlayerRole.PLAYER
        self._groups_id: List[str] = []
        self._player: Player = Player(name=username)
        
        User._existing_usernames.add(username)

    @property
    def ID(self) -> str:
        """The unique identifier of the user."""
        return self._id

    @property
    def username(self) -> str:
        """The username of the account."""
        return self._username

    @property
    def hash(self) -> str:
        """The hash of the account password."""
        return self._hash

    @property
    def groups_id(self) -> List[str]:
        """The IDs of the groups the user admins."""
        return self._groups_id

    @property
    def player(self) -> Player:
        """The player associated with the user."""
        return self._player

    def change_password(self, new_password: str) -> None:
        """Changes the account password.

        Args:
            new_password: The new password to set.
        """
        self._hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()

class Game:
    """Represents a game session."""

    def __init__(
        self,
        name: str | None = None,
        max_players: int | None = None,
        max_observers: int | None = None,
        password: str | None = None,
        observer_password: str | None = None,
        turn_based: bool = False,
        **kwargs: Any
    ):
        """Initializes a new game session."""
        self._id: str = str(uuid.uuid4())
        self.name: str | None = name
        self._max_players: int | None = max_players
        self._max_observers: int | None = max_observers
        self._hash: str | None = (
            bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode() if password else None
        )
        self._observer_hash: str | None = (
            bcrypt.hashpw(observer_password.encode(), bcrypt.gensalt()).decode()
            if observer_password
            else (self._hash if password else None)
        )
        self._turn_based: bool = turn_based
        self._players: List[Player] = []
        self._observers: List[Player] = []
        self._game_state: GameState = GameState.PENDING
        self.static_state: Dict[str, Any] = {}
        self.dynamic_state: Dict[str, Any] = {}

        for key, value in kwargs.items():
            if isinstance(value, tuple) and len(value) == 2 and isinstance(value[0], ParameterFamily):
                family, val = value
                if family == ParameterFamily.STATIC:
                    self.static_state[key] = val
                else:
                    self.dynamic_state[key] = val

    @property
    def ID(self) -> str:
        """Unique ID of the game."""
        return self._id

    @property
    def hash(self) -> str | None:
        """Hash of the game password."""
        return self._hash

    @property
    def observer_hash(self) -> str | None:
        """Hash of the observer password."""
        return self._observer_hash

    @property
    def turn_based(self) -> bool:
        """Whether the game is turn-based."""
        return self._turn_based

    @property
    def players(self) -> Tuple[Player, ...]:
        """Tuple of players in the game."""
        return tuple(self._players)

    @property
    def observers(self) -> Tuple[Player, ...]:
        """Tuple of observers in the game."""
        return tuple(self._observers)

    @property
    def current_player(self) -> Player | None:
        """The player whose turn it is."""
        if not self._turn_based or not self._players:
            return None
        # Simple implementation: index 0 is always current player
        return self._players[0]

    @property
    def game_state(self) -> GameState:
        """Current state of the game."""
        return self._game_state

    def change_password(self, new_password: str) -> None:
        """Changes the game password."""
        self._hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()

    def join_game_as_player(self, player: Player | str, password: str | None = None) -> None:
        """Allows a player to join the game."""
        if self._max_players is not None and len(self._players) >= self._max_players:
            raise GameIsFullError("Game is full.")

        if self._hash and (not password or not bcrypt.checkpw(password.encode(), self._hash.encode())):
            raise PasswordError("Incorrect password.")

        if isinstance(player, Player):
            p_obj = player
        else:
            # For testing purpose or when ID is used, but we don't have a global registry
            # We assume it should be a Player object in most cases for this implementation
            raise PlayerNotFoundError(player)
        
        self._players.append(p_obj)

    def remove_player(self, player: Player | str) -> None:
        """Removes a player from the game."""
        p_id = player if isinstance(player, str) else player.ID
        for p in self._players:
            if p.ID == p_id:
                self._players.remove(p)
                return
        raise PlayerNotFoundInGameError(p_id)

    def join_game_as_observer(self, player: Player | str, password: str | None = None) -> None:
        """Allows a player to join as an observer."""
        if self._max_observers is not None and len(self._observers) >= self._max_observers:
            raise GameIsFullError("Observers list is full.")

        target_hash = self._observer_hash
        if target_hash and (not password or not bcrypt.checkpw(password.encode(), target_hash.encode())):
            raise PasswordError("Incorrect observer password.")

        if isinstance(player, Player):
            p_obj = player
        else:
            raise PlayerNotFoundError(player)

        self._observers.append(p_obj)

    def remove_observer(self, player: Player | str) -> None:
        """Removes an observer from the game."""
        p_id = player if isinstance(player, str) else player.ID
        for p in self._observers:
            if p.ID == p_id:
                self._observers.remove(p)
                return
        raise PlayerNotFoundInGameError(p_id)

    def start(self) -> None:
        """Starts the game."""
        if self._game_state in (GameState.IN_PROGRESS, GameState.PAUSING):
            raise GameAlreadyStartedError()
        if self._game_state == GameState.FINISHED:
            raise GameIsFinishedError()
        self._game_state = GameState.IN_PROGRESS

    def pause(self) -> None:
        """Pauses the game."""
        if self._game_state != GameState.IN_PROGRESS:
            raise GameNotStartedError()
        if self._game_state == GameState.PAUSING:
            raise GameAlreadyPausedError()
        self._game_state = GameState.PAUSING

    def resume(self) -> None:
        """Resumes a paused game."""
        if self._game_state != GameState.PAUSING:
            raise GameNotPausedError()
        self._game_state = GameState.IN_PROGRESS

    def stop(self) -> None:
        """Ends the game."""
        if self._game_state not in (GameState.IN_PROGRESS, GameState.PAUSING):
            raise GameNotStartedError()
        self._game_state = GameState.FINISHED

    def next_turn(self) -> None:
        """Moves to the next turn."""
        if not self._turn_based:
            raise GameNotTurnBasedError()
        if self._game_state == GameState.FINISHED:
            raise GameIsFinishedError()
        if self._game_state != GameState.IN_PROGRESS and self._game_state != GameState.PAUSING:
            raise GameNotStartedError()
        
        if self._players:
            first = self._players.pop(0)
            self._players.append(first)

    def reverse_order(self) -> None:
        """Reverses player order."""
        if not self._turn_based:
            raise GameNotTurnBasedError()
        if self._game_state == GameState.FINISHED:
            raise GameIsFinishedError()
        self._players.reverse()

    def set_player_rank(self, player: Player | str, rank: int) -> None:
        """Sets a player's rank."""
        if not self._turn_based:
            raise GameNotTurnBasedError()
        if self._game_state == GameState.FINISHED:
            raise GameIsFinishedError()
        
        p_id = player if isinstance(player, str) else player.ID
        target_p = None
        for p in self._players:
            if p.ID == p_id:
                target_p = p
                break
        
        if not target_p:
            raise PlayerNotFoundInGameError(p_id)

        self._players.remove(target_p)
        if rank < 0 or rank > len(self._players):
            # Rollback
            self._players.append(target_p)
            raise IndexError("Invalid rank.")
        
        self._players.insert(rank, target_p)

class GameGroup:
    """Represents a group of games."""

    def __init__(self, name: str, **kwargs: Any):
        """Initializes a new game group."""
        self._id: str = str(uuid.uuid4())
        self.name: str = name
        self._games: List[Game] = []
        self.parameters: Dict[str, Any] = kwargs

    @property
    def ID(self) -> str:
        """Unique ID of the group."""
        return self._id

    @property
    def games(self) -> Tuple[Game, ...]:
        """Tuple of games in the group."""
        return tuple(self._games)

    def add_game(self, game: Game | str) -> None:
        """Adds a game to the group."""
        if isinstance(game, Game):
            self._games.append(game)
        else:
            raise GameNotFoundError(game)

    def remove_game(self, game: Game | str) -> None:
        """Removes a game from the group."""
        g_id = game if isinstance(game, str) else game.ID
        for g in self._games:
            if g.ID == g_id:
                self._games.remove(g)
                return
        raise GameNotFoundInGroupError(g_id)
