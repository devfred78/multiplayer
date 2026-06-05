# API Reference

This document provides a comprehensive reference for the `multiplayer` library's public API.

## Core Models

### Player
`multiplayer.game.Player(name, **kwargs)`

Represents a player in a game context.

**Parameters:**

| Name | Type | Description | Required | Default |
|------|------|-------------|----------|---------|
| `name` | `str` | The name of the player. | Yes | - |
| `**kwargs` | variable | Optional parameters. Each parameter must be a tuple `(family, initial_value)` where `family` is a `ParameterFamily`. | No | - |

**Attributes & Properties:**

| Name | Type | Description | Settable | Implementation Detail |
|------|------|-------------|----------|-----------------------|
| `ID` | `str` | Unique identifier. | No | Automatically generated using `uuid.uuid4()`. |
| `name` | `str` | The name of the player. | Yes | Initialized with the name provided at creation. |
| `static_state` | `dict` | Custom attributes for data that rarely changes. | Yes | Initialized with parameters from `ParameterFamily.STATIC`. |
| `dynamic_state` | `dict` | Custom attributes for data that changes frequently. | Yes | Initialized with parameters from `ParameterFamily.DYNAMIC`. |

---

### User
`multiplayer.game.User(username, password, email)`

Represents a user account with authentication and role management.

**Parameters:**

| Name | Type | Description | Required | Default |
|------|------|-------------|----------|---------|
| `username` | `str` | The account username. | Yes | - |
| `password` | `str` | The account password. | Yes | - |
| `email` | `str` | Email address. | No | `""` |

*Note: Raises `UserAlreadyExistsError` if the username is already taken.*

**Attributes & Properties:**

| Name | Type | Description | Settable | Implementation Detail |
|------|------|-------------|----------|-----------------------|
| `ID` | `str` | Unique identifier. | No | Automatically generated using `uuid.uuid4()`. |
| `username` | `str` | The account username. | No | - |
| `hash` | `str` | Hashed password. | No | Automatically generated using `bcrypt`. |
| `email` | `str` | Email address. | Yes | - |
| `role` | `PlayerRole` | User's permission level. | Yes | Defaults to `PlayerRole.PLAYER`. |
| `groups_id` | `list[str]` | IDs of groups where the user is admin. | No (but mutable) | Raises `GroupNotFoundError` if an ID is invalid. |
| `player` | `Player` | Associated `Player` instance. | No (but mutable) | Created with `name=username`. Exists for the user's lifetime. |

**Methods:**

- `change_password(new_password: str)`: Updates the user's password and regenerates the hash using `bcrypt`.

---

### Game
`multiplayer.game.Game(name, max_players, max_observers, password, observer_password, turn_based, **kwargs)`

Manages a single game session, players, and state transitions.

**Parameters:**

| Name | Type | Description | Required | Default |
|------|------|-------------|----------|---------|
| `name` | `str \| None` | The name of the game. | No | `None` |
| `max_players` | `int \| None` | Max players allowed. `None` for unlimited, `<= 0` for none. | No | `None` |
| `max_observers` | `int \| None` | Max observers allowed. `None` for unlimited, `<= 0` for none. | No | `None` |
| `password` | `str \| None` | Password for players. `None` for public. | No | `None` |
| `observer_password` | `str \| None` | Password for observers. If `None`, uses `password`. | No | `None` |
| `turn_based` | `bool` | Whether the game is turn-based. | No | `False` |
| `**kwargs` | variable | Optional custom parameters (tuple of family and value). | No | - |

**Attributes & Properties:**

| Name | Type | Description | Settable | Implementation Detail |
|------|------|-------------|----------|-----------------------|
| `ID` | `str` | Unique identifier. | No | Automatically generated using `uuid.uuid4()`. |
| `name` | `str` | The name of the game. | Yes | - |
| `hash` | `str \| None` | Hashed player password. | No | Generated via `bcrypt`. |
| `observer_hash` | `str \| None` | Hashed observer password. | No | Generated via `bcrypt`. |
| `turn_based` | `bool` | Turn-based flag. | No | - |
| `players` | `tuple[Player]` | Read-only tuple of players in turn order. | No | Backed by internal list `_players`. |
| `observers` | `tuple[Player]` | Read-only tuple of observers. | No | Backed by internal list `_observers`. |
| `current_player` | `Player \| None` | The player whose turn it is. | No | Only relevant for turn-based games. |
| `game_state` | `GameState` | Current state of the game. | No | - |
| `static_state` | `dict` | Static custom attributes. | Yes | Initialized from `ParameterFamily.STATIC`. |
| `dynamic_state` | `dict` | Dynamic custom attributes. | Yes | Initialized from `ParameterFamily.DYNAMIC`. |

**Methods:**

| Method | Description | Parameters | Raises |
|--------|-------------|------------|--------|
| `change_password` | Changes the player password. | `new_password (str)` | - |
| `join_game_as_player` | Adds a player to the game. | `player (Player\|str)`, `password (str\|None)` | `PlayerNotFoundError`, `PasswordError`, `GameIsFullError` |
| `remove_player` | Removes a player. | `player (Player\|str)` | `PlayerNotFoundInGameError` |
| `join_game_as_observer` | Adds an observer. | `player (Player\|str)`, `password (str\|None)` | `PlayerNotFoundError`, `PasswordError`, `GameIsFullError` |
| `remove_observer` | Removes an observer. | `player (Player\|str)` | `PlayerNotFoundInGameError` |
| `start` | Sets state to `IN_PROGRESS`. | - | `GameAlreadyStartedError`, `GameIsFinishedError` |
| `pause` | Sets state to `PAUSING`. | - | `GameNotStartedError`, `GameAlreadyPausedError` |
| `resume` | Sets state back to `IN_PROGRESS`. | - | `GameNotPausedError` |
| `stop` | Sets state to `FINISHED`. | - | `GameNotStartedError` |
| `next_turn` | Advances to the next player. | - | `GameNotStartedError`, `GameIsFinishedError`, `GameNotTurnBasedError` |
| `reverse_order` | Inverses the player order. | - | `GameIsFinishedError`, `GameNotTurnBasedError` |
| `set_player_rank` | Sets a specific rank for a player. | `player (Player\|str)`, `rank (int)` | `IndexError`, `GameIsFinishedError`, `GameNotTurnBasedError`, `PlayerNotFoundInGameError` |

---

### GameGroup
`multiplayer.game.GameGroup`

Organizes multiple games into a group for parallel management.

**Parameters:**

| Name | Type | Description | Required | Default |
|------|------|-------------|----------|---------|
| `name` | `str` | The name of the group. | Yes | - |
| `**kwargs` | variable | Optional custom parameters. | No | - |

**Attributes & Properties:**

| Name | Type | Description | Settable | Implementation Detail |
|------|------|-------------|----------|-----------------------|
| `ID` | `str` | Unique identifier. | No | Automatically generated using `uuid.uuid4()`. |
| `name` | `str` | The name of the group. | Yes | - |
| `games` | `tuple[Game]` | Read-only tuple of games in the group. | No | Backed by internal list `_games`. |
| `parameters` | `dict` | Custom group parameters. | Yes | Initialized from `kwargs`. |

**Methods:**

- `add_game(game: Game | str)`: Adds a game to the end of the group. Raises `GameNotFoundError` if invalid.
- `remove_game(game: Game | str)`: Removes a game from the group. Raises `GameNotFoundInGroupError` if not present.

---

## Enumerations

### PlayerRole
`multiplayer.PlayerRole`
- `PLAYER`: Standard player.
- `GROUP_ADMIN`: Admin for specific groups (includes `PLAYER` permissions).
- `SERVER_ADMIN`: Global administrator (includes `GROUP_ADMIN` permissions).

### GameState
`multiplayer.GameState`
- `PENDING`: Created, waiting for players.
- `PAUSING`: Temporarily suspended.
- `IN_PROGRESS`: Currently active.
- `FINISHED`: Completed; results are final.

### ParameterFamily
`multiplayer.ParameterFamily`
- `STATIC`: Parameters that rarely change.
- `DYNAMIC`: Parameters that change frequently.

### SaveFormat
`multiplayer.SaveFormat`
- `JSON`: Persists data into a single JSON document.
- `SQLITE`: Persists data into an SQLite database.

---

## Persistence

### Save
`multiplayer.save.Save(file_path, save_format)`

Handles saving and restoring `Player`, `User`, `Game` and `GameGroup` instances to and from a save file. Objects are kept in an in-memory buffer and written to disk only when `flush()` is called.

**Parameters:**

| Name | Type | Description | Required | Default |
|------|------|-------------|----------|---------|
| `file_path` | `Path` | The path of the save file. Created if missing; validated and loaded if it exists. | Yes | - |
| `save_format` | `SaveFormat \| str` | The storage format. A `SaveFormat` member or one of the strings `"json"` / `"sqlite"`. | Yes | - |

*Note: Raises `SaveError` if the format is unknown or if an existing file has an incompatible structure.*

**Attributes & Properties:**

| Name | Type | Description | Settable | Implementation Detail |
|------|------|-------------|----------|-----------------------|
| `file_path` | `Path` | Path of the underlying save file. | Yes | Initialized from `file_path`. |
| `save_format` | `SaveFormat` | Storage format used. | Yes | Initialized from `save_format`. |

**Methods:**

| Method | Description | Parameters | Raises |
|--------|-------------|------------|--------|
| `save` | Saves or updates an instance in the in-memory buffer (replaces if same class and ID). | `obj (Player\|User\|Game\|GameGroup)` | `SaveError` |
| `load` | Returns the list of all stored instances of a given class. | `target (str\|type)` | `SaveError` |
| `reset` | Clears the buffer and rewrites the file with an empty valid structure. | - | `SaveError` |
| `flush` | Persists the in-memory buffer to the save file. | - | `SaveError` |

---

## Utility Functions
`multiplayer.utils`

The library provides utilities for suggesting names based on categories.

### Name Suggestion Categories

**For Games:**
- `cities`: Major world cities.
- `countries`: Sovereign nations.
- `rivers`: Important rivers.
- `seas_oceans`: Main bodies of salt water.
- `planets_moons`: Celestial bodies.

**For Players:**
- `roman_gods`: Roman mythology deities.
- `greek_gods`: Ancient Greek mythology deities.
- `egyptian_gods`: Ancient Egyptian mythology deities.
- `european_kings`: Historical European kings.
- `european_queens`: Historical European queens.

*Implementation Note: Data is stored in `src/multiplayer/data` as text or CSV files. Names are normalized to avoid duplicates and special characters.*

### Functions

- `register_name_category(category_name: str, data: Any, category_type: str)`
  Registers a new custom category. `data` can be a list, string, or Path to a text/CSV file. `category_type` is either `"game"` or `"player"`.
- `unregister_name_category(category_name: str) -> bool`
  Removes a custom category. Returns `True` on success.
- `get_available_categories(category_type: str = "all") -> list[str]`
  Returns available categories for `"all"`, `"game"`, or `"player"`.
- `suggest_game_name(category: str | None = None) -> str`
  Suggests a random game name. Picks a random category if `None`.
- `suggest_player_name(category: str | None = None) -> str`
  Suggests a random player name. Picks a random category if `None`.

---

## Exceptions

All exceptions inherit from `multiplayer.exceptions.MultiplayerError`.

| Exception | Description |
|-----------|-------------|
| `UserAlreadyExistsError` | Raised when a username is already taken. |
| `GroupNotFoundError` | Raised when a group ID does not exist. Returns the faulty ID in the message. |
| `PlayerNotFoundError` | Raised when a player ID does not exist. Returns the faulty ID if provided. |
| `PlayerNotFoundInGameError` | Raised when trying to remove a player who is not in the game. |
| `PasswordError` | Raised when an incorrect password is provided. |
| `GameIsFullError` | Raised when a game has reached its player or observer limit. |
| `GameAlreadyStartedError` | Raised when trying to start a game that is already active or paused. |
| `GameIsFinishedError` | Raised when attempting to modify a finished game. |
| `GameNotStartedError` | Raised when an action (pause, stop, next_turn) requires the game to be started. |
| `GameAlreadyPausedError` | Raised when trying to pause an already paused game. |
| `GameNotPausedError` | Raised when trying to resume a game that is not paused. |
| `GameNotTurnBasedError` | Raised when a turn-based action is called on a non-turn-based game. |
| `GameNotFoundError` | Raised when a game ID does not exist. Returns the faulty ID if provided. |
| `GameNotFoundInGroupError` | Raised when trying to remove a game not present in the specified group. |
| `SaveError` | Raised when a save file is incompatible or corrupted, when an unknown save format is requested, or when an unsupported class is saved or loaded. |
