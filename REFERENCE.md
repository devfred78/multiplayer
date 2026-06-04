# API Reference

This document provides a comprehensive reference for the `multiplayer` library's public API.

## Core Models

### Player
`multiplayer.game.Player`

Represents a player in a game context.

**Instantiation Arguments:**
- `name (str)`: **Mandatory**. The name of the player.
- `**kwargs`: **Optional**. Custom parameters in the format `parameter_name=(ParameterFamily, initial_value)`.

**Attributes:**
- `name (str)`: The name of the player.
- `static_state (dict)`: Custom attributes that rarely change (e.g., team).
- `dynamic_state (dict)`: Custom attributes that frequently change (e.g., score).

**Properties:**
- `ID (str)`: Unique identifier (UUID) generated automatically. Read-only.

---

### User
`multiplayer.game.User`

Represents a user account with authentication.

**Instantiation Arguments:**
- `username (str)`: **Mandatory**. The account username.
- `password (str)`: **Mandatory**. The account password (will be hashed).
- `email (str)`: **Optional**. Email address (default: `""`).

**Properties:**
- `ID (str)`: Unique identifier (UUID). Read-only.
- `username (str)`: The account username. Read-only.
- `hash (str)`: The hashed password. Read-only.
- `email (str)`: The email address associated with the account.
- `role (PlayerRole)`: The role of the user (defaults to `PLAYER`).
- `groups_id (list[str])`: List of group IDs the user belongs to.
- `player (Player)`: The `Player` instance associated with this user.

**Methods:**
- `change_password(new_password: str)`: Updates the user's password.

---

### Game
`multiplayer.game.Game`

Manages a single game session.

**Instantiation Arguments:**
- `name (str)`: **Mandatory**. The name of the game.
- `password (str | None)`: **Optional**. Password for players (default: `None`).
- `observer_password (str | None)`: **Optional**. Password for observers (default: `None`).
- `max_players (int)`: **Optional**. Maximum number of players (default: `10`).
- `max_observers (int)`: **Optional**. Maximum number of observers (default: `10`).
- `turn_based (bool)`: **Optional**. Whether the game is turn-based (default: `False`).
- `**kwargs`: **Optional**. Additional configuration parameters.

**Properties:**
- `ID (str)`: Unique identifier (UUID). Read-only.
- `name (str)`: The name of the game.
- `max_players (int)`: Maximum number of players.
- `max_observers (int)`: Maximum number of observers.
- `hash (str)`: Hashed player password. Read-only.
- `observer_hash (str)`: Hashed observer password. Read-only.
- `turn_based (bool)`: Whether the game is turn-based. Read-only.
- `players (list[Player])`: List of joined players. Read-only.
- `observers (list[Player])`: List of joined observers. Read-only.
- `current_player (Player | None)`: The player whose turn it is.
- `game_state (GameState)`: Current state of the game. Read-only.
- `parameters (dict)`: Additional game parameters.

**Methods:**
- `change_password(new_password: str)`: Changes the game's player password.
- `join_game_as_player(player: Player | str, password: str | None = None)`: Adds a player to the game.
- `remove_player(player: Player | str)`: Removes a player.
- `join_game_as_observer(player: Player | str, password: str | None = None)`: Adds an observer.
- `remove_observer(player: Player | str)`: Removes an observer.
- `start()`: Transitions the game state to `IN_PROGRESS`.
- `pause()`: Transitions the game state to `PAUSING`.
- `resume()`: Resumes the game to `IN_PROGRESS`.
- `stop()`: Transitions the game state to `FINISHED`.
- `next_turn()`: Advances to the next player (turn-based games only).
- `reverse_order()`: Reverses the player turn order.
- `set_player_rank(player: Player | str, rank: int)`: Sets the final rank for a player.

---

### GameGroup
`multiplayer.game.GameGroup`

Organizes multiple games into a group.

**Instantiation Arguments:**
- `name (str)`: **Mandatory**. The name of the group.
- `**kwargs`: **Optional**. Custom group parameters.

**Properties:**
- `ID (str)`: Unique identifier (UUID). Read-only.
- `name (str)`: The name of the group.
- `games (list[Game])`: List of games in the group. Read-only.
- `parameters (dict)`: Custom group parameters.

**Methods:**
- `add_game(game: Game | str)`: Adds a game to the group.
- `remove_game(game: Game | str)`: Removes a game from the group.

---

## Enumerations

### PlayerRole
`multiplayer.PlayerRole`
- `PLAYER`: Regular player.
- `GROUP_ADMIN`: Administrator for a specific group.
- `SERVER_ADMIN`: Global server administrator.

### GameState
`multiplayer.GameState`
- `PENDING`: Waiting to start.
- `IN_PROGRESS`: Game is active.
- `PAUSING`: Game is paused.
- `FINISHED`: Game has ended.

### ParameterFamily
`multiplayer.ParameterFamily`
- `STATIC`: Parameters that rarely change.
- `DYNAMIC`: Parameters that change frequently.

---

## Utility Functions

### Name Suggestions
`multiplayer.utils`

- `suggest_game_name(category: str | None = None) -> str`: Returns a random game name.
- `suggest_player_name(category: str | None = None) -> str`: Returns a random player name.
- `get_available_categories(category_type: str = "all") -> list[str]`: Lists available name categories.
- `register_name_category(category_name: str, data: Any, category_type: str)`: Registers a new category.
- `unregister_name_category(category_name: str) -> bool`: Removes a category.

---

## Exceptions

All exceptions inherit from `multiplayer.exceptions.MultiplayerError`.

- `UserAlreadyExistsError`: Raised when a username is already taken.
- `PasswordError`: Raised when an incorrect password is provided.
- `GameIsFullError`: Raised when a game reached its player/observer limit.
- `GameAlreadyStartedError`: Raised when trying to start an already started game.
- `GameIsFinishedError`: Raised when performing actions on a finished game.
- `GameNotStartedError`: Raised when an action requires the game to be started.
- `GameAlreadyPausedError`: Raised when trying to pause a paused game.
- `GameNotPausedError`: Raised when trying to resume a non-paused game.
- `GameNotTurnBasedError`: Raised when using turn-based methods on non-turn-based games.
- `GameNotFoundError`: Raised when a game ID cannot be found.
- `PlayerNotFoundError`: Raised when a player ID cannot be found.
- `GroupNotFoundError`: Raised when a group ID cannot be found.
- `PlayerNotFoundInGameError`: Raised when a player is not in the specified game.
- `GameNotFoundInGroupError`: Raised when a game is 