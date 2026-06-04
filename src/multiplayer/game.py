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
    """Represents a player in the game context.

    This class stores player-specific information, including their unique identifier,
    name, and custom state parameters divided into static and dynamic categories.

    Attributes:
        name (str): The name of the player.
        static_state (dict): Custom attributes that rarely change during the game.
        dynamic_state (dict): Custom attributes that frequently change during the game.
    """

    def __init__(self, name: str, **kwargs: Any):
        """Initializes a new player instance.

        Args:
            name (str): The name of the player.
            **kwargs: Optional parameters for customizing the player.
                Each keyword argument should be a tuple of (ParameterFamily, initial_value).
                For example: score=(ParameterFamily.DYNAMIC, 0).
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
        """The unique identifier of the player.

        This ID is automatically generated using uuid.uuid4() and is read-only.

        Returns:
            str: The unique UUID of the player.
        """
        return self._id

class User:
    """Represents a user account.

    A User account allows maintaining a player profile, managing group permissions,
    and providing authentication. Each user is associated with a single Player instance.

    Attributes:
        email (str): The email address of the account.
        role (PlayerRole): The role/permission level of the account.
    """
    _existing_usernames: set[str] = set()

    def __init__(self, username: str, password: str, email: str = ""):
        """Initializes a new user account.

        Args:
            username (str): The unique name of the user.
            password (str): The password for authentication (will be hashed).
            email (str, optional): The email address. Defaults to "".

        Raises:
            UserAlreadyExistsError: If the username has already been taken.
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
        """The unique identifier of the user account.

        Returns:
            str: The unique UUID of the user.
        """
        return self._id

    @property
    def username(self) -> str:
        """The username of the account.

        Returns:
            str: The name used for identification.
        """
        return self._username

    @property
    def hash(self) -> str:
        """The bcrypt hash of the account password.

        Returns:
            str: The hashed password string.
        """
        return self._hash

    @property
    def groups_id(self) -> List[str]:
        """The list of group IDs for which the user is an administrator.

        This is only relevant if the user's role is GROUP_ADMIN.

        Returns:
            List[str]: A mutable list of group UUID strings.
        """
        return self._groups_id

    @property
    def player(self) -> Player:
        """The player profile associated with this user.

        The player name defaults to the username but can be modified independently.

        Returns:
            Player: The associated player instance.
        """
        return self._player

    def change_password(self, new_password: str) -> None:
        """Updates the account password.

        The new password is automatically hashed using bcrypt.

        Args:
            new_password (str): The new plain-text password.
        """
        self._hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()

class Game:
    """Represents a game session.

    This class handles the core logic of a game, including player management,
    observer tracking, password protection, and turn-based progression.

    Attributes:
        name (str, optional): The name of the game session.
        static_state (dict): Custom static attributes of the game.
        dynamic_state (dict): Custom dynamic attributes of the game.
    """

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
        """Initializes a new game session.

        Args:
            name (str, optional): The name of the game. Defaults to None.
            max_players (int, optional): Max number of players. Defaults to None.
            max_observers (int, optional): Max number of observers. Defaults to None.
            password (str, optional): Password required to join as a player. Defaults to None.
            observer_password (str, optional): Password for observers. Defaults to None.
            turn_based (bool, optional): Whether the game is turn-based. Defaults to False.
            **kwargs: Custom state parameters as tuples of (ParameterFamily, initial_value).
        """
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
        """The unique identifier of the game session.

        Returns:
            str: The unique UUID of the game.
        """
        return self._id

    @property
    def hash(self) -> str | None:
        """The bcrypt hash of the game password.

        Returns:
            str, optional: The hashed password string or None if public.
        """
        return self._hash

    @property
    def observer_hash(self) -> str | None:
        """The bcrypt hash of the observer password.

        Returns:
            str, optional: The hashed observer password string or None.
        """
        return self._observer_hash

    @property
    def turn_based(self) -> bool:
        """Indicates if the game uses turn-based logic.

        Returns:
            bool: True if turn-based, False otherwise.
        """
        return self._turn_based

    @property
    def players(self) -> Tuple[Player, ...]:
        """The list of players currently in the game.

        Returns:
            Tuple[Player, ...]: A read-only tuple of Player instances.
        """
        return tuple(self._players)

    @property
    def observers(self) -> Tuple[Player, ...]:
        """The list of observers currently watching the game.

        Returns:
            Tuple[Player, ...]: A read-only tuple of Player instances.
        """
        return tuple(self._observers)

    @property
    def current_player(self) -> Player | None:
        """The player whose turn it currently is.

        Only applicable for turn-based games.

        Returns:
            Player, optional: The Player instance whose turn it is, or None.
        """
        if not self._turn_based or not self._players:
            return None
        # Simple implementation: index 0 is always current player
        return self._players[0]

    @property
    def game_state(self) -> GameState:
        """The current lifecycle state of the game.

        Returns:
            GameState: One of PENDING, IN_PROGRESS, PAUSING, or FINISHED.
        """
        return self._game_state

    def change_password(self, new_password: str) -> None:
        """Updates the password required to join the game.

        Args:
            new_password (str): The new plain-text password.
        """
        self._hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()

    def join_game_as_player(self, player: Player | str, password: str | None = None) -> None:
        """Adds a player to the game session.

        Args:
            player (Player | str): The Player instance or its ID.
            password (str, optional): The password if the game is private.

        Raises:
            GameIsFullError: If the maximum number of players has been reached.
            PasswordError: If the provided password is incorrect.
            PlayerNotFoundError: If a player ID was provided but no Player object.
        """
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
        """Removes a player from the game session.

        Args:
            player (Player | str): The Player instance or its ID to remove.

        Raises:
            PlayerNotFoundInGameError: If the player is not in this game.
        """
        p_id = player if isinstance(player, str) else player.ID
        for p in self._players:
            if p.ID == p_id:
                self._players.remove(p)
                return
        raise PlayerNotFoundInGameError(p_id)

    def join_game_as_observer(self, player: Player | str, password: str | None = None) -> None:
        """Adds an observer to the game session.

        Args:
            player (Player | str): The Player instance or its ID.
            password (str, optional): The observer password if required.

        Raises:
            GameIsFullError: If the maximum number of observers has been reached.
            PasswordError: If the provided password is incorrect.
            PlayerNotFoundError: If a player ID was provided but no Player object.
        """
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
        """Removes an observer from the game session.

        Args:
            player (Player | str): The Player instance or its ID to remove.

        Raises:
            PlayerNotFoundInGameError: If the observer is not in this game.
        """
        p_id = player if isinstance(player, str) else player.ID
        for p in self._observers:
            if p.ID == p_id:
                self._observers.remove(p)
                return
        raise PlayerNotFoundInGameError(p_id)

    def start(self) -> None:
        """Starts the game session.

        Sets the state to IN_PROGRESS.

        Raises:
            GameAlreadyStartedError: If the game is already in progress or paused.
            GameIsFinishedError: If the game has already finished.
        """
        if self._game_state in (GameState.IN_PROGRESS, GameState.PAUSING):
            raise GameAlreadyStartedError()
        if self._game_state == GameState.FINISHED:
            raise GameIsFinishedError()
        self._game_state = GameState.IN_PROGRESS

    def pause(self) -> None:
        """Temporarily suspends the game session.

        Sets the state to PAUSING.

        Raises:
            GameNotStartedError: If the game is not currently in progress.
            GameAlreadyPausedError: If the game is already paused.
        """
        if self._game_state != GameState.IN_PROGRESS:
            raise GameNotStartedError()
        if self._game_state == GameState.PAUSING:
            raise GameAlreadyPausedError()
        self._game_state = GameState.PAUSING

    def resume(self) -> None:
        """Resumes a paused game session.

        Sets the state to IN_PROGRESS.

        Raises:
            GameNotPausedError: If the game is not currently paused.
        """
        if self._game_state != GameState.PAUSING:
            raise GameNotPausedError()
        self._game_state = GameState.IN_PROGRESS

    def stop(self) -> None:
        """Ends the game session permanently.

        Sets the state to FINISHED.

        Raises:
            GameNotStartedError: If the game was not in progress or paused.
        """
        if self._game_state not in (GameState.IN_PROGRESS, GameState.PAUSING):
            raise GameNotStartedError()
        self._game_state = GameState.FINISHED

    def next_turn(self) -> None:
        """Advances the game to the next player's turn.

        Only applicable for turn-based games.

        Raises:
            GameNotTurnBasedError: If the game is not turn-based.
            GameIsFinishedError: If the game has already finished.
            GameNotStartedError: If the game has not started yet.
        """
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
        """Inverses the order of players in a turn-based game.

        Raises:
            GameNotTurnBasedError: If the game is not turn-based.
            GameIsFinishedError: If the game has already finished.
        """
        if not self._turn_based:
            raise GameNotTurnBasedError()
        if self._game_state == GameState.FINISHED:
            raise GameIsFinishedError()
        self._players.reverse()

    def set_player_rank(self, player: Player | str, rank: int) -> None:
        """Changes a player's position in the turn order.

        Args:
            player (Player | str): The Player or player ID to move.
            rank (int): The new 0-based rank for the player.

        Raises:
            GameNotTurnBasedError: If the game is not turn-based.
            GameIsFinishedError: If the game has already finished.
            PlayerNotFoundInGameError: If the player is not in the game.
            IndexError: If the provided rank is out of bounds.
        """
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
    """Represents a collection of game sessions.

    A GameGroup allows managing multiple games together and can store
    shared parameters.

    Attributes:
        name (str): The name of the game group.
        parameters (dict): Custom parameters for the group.
    """

    def __init__(self, name: str, **kwargs: Any):
        """Initializes a new game group.

        Args:
            name (str): The name of the group.
            **kwargs: Optional custom parameters for the group.
        """
        self._id: str = str(uuid.uuid4())
        self.name: str = name
        self._games: List[Game] = []
        self.parameters: Dict[str, Any] = kwargs

    @property
    def ID(self) -> str:
        """The unique identifier of the game group.

        Returns:
            str: The unique UUID of the group.
        """
        return self._id

    @property
    def games(self) -> Tuple[Game, ...]:
        """The list of games currently in the group.

        Returns:
            Tuple[Game, ...]: A read-only tuple of Game instances.
        """
        return tuple(self._games)

    def add_game(self, game: Game | str) -> None:
        """Adds a game session to the group.

        Args:
            game (Game | str): The Game instance to add.

        Raises:
            GameNotFoundError: If a game ID was provided instead of an instance.
        """
        if isinstance(game, Game):
            self._games.append(game)
        else:
            raise GameNotFoundError(game)

    def remove_game(self, game: Game | str) -> None:
        """Removes a game session from the group.

        Args:
            game (Game | str): The Game instance or its ID to remove.

        Raises:
            GameNotFoundInGroupError: If the game is not in the group.
        """
        g_id = game if isinstance(game, str) else game.ID
        for g in self._games:
            if g.ID == g_id:
                self._games.remove(g)
                return
        raise GameNotFoundInGroupError(g_id)
