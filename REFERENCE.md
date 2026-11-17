# API Reference

This document provides a comprehensive reference for the `multiplayer` library's public API.

## Core Models

### Option
`multiplayer.game.Option(name, option_type, description, default, min_value, max_value, step, choices)`

A player customization option, whose value is chosen when a player is created by a player factory.

**Parameters:**

| Name | Type | Description | Required | Default |
|------|------|-------------|----------|---------|
| `name` | `str` | The name of the option. | Yes | - |
| `option_type` | `OptionType` | The type of the option. | Yes | - |
| `description` | `str` | The description of the option. | No | `""` |
| `default` | `bool\|int\|float\|str\|None` | The default value, which can contain runtime constants (`%%USERNAME%%`, `%%RANDOM_NUMBER%%`, ...). `None` means "first available value". | No | `None` |
| `min_value` | `float\|int\|None` | Minimum value (`RANGE` options). | No | `None` |
| `max_value` | `float\|int\|None` | Maximum value (`RANGE` options). | No | `None` |
| `step` | `float\|int` | Increment between two possible values (`RANGE` options). | No | `1` |
| `choices` | `list[str]\|tuple[str, ...]` | Possible choices (`LIST` options). | No | `[]` |

*Note: Raises `TypeError` or `ValueError` if the parameters are inconsistent (see [INSTRUCTION.md](INSTRUCTION.md)).*

**Attributes & Properties:** `ID`, `option_type`, `choices`, `min_value`, `max_value`, `step` and `default` (raw, constants unevaluated) are read-only; `name` and `description` are settable.

**Methods:**

| Method | Description | Parameters | Raises |
|--------|-------------|------------|--------|
| `evaluate_default` | Returns the default value after evaluation of the runtime constants. | `context (dict[str, str]\|None)`, `exclusions (list\|None)` | - |
| `to_dict` | Returns the dictionary representation (keys `option_id`, `type`, `name`, `description`, `default`, `min`, `max`, `step`, `choices`). | - | - |
| `from_dict` (class method) | Creates an option from its dictionary representation, keeping its ID. | `data (dict)` | `TypeError`, `ValueError` |

---

### OptionEntry
`multiplayer.game.OptionEntry`

Immutable description of an option registered in a template or a factory: `option` (copy keeping the ID), `unicity`, `hide`, `player_attribute` (`"name"` or a `ParameterFamily`) and `key` (frozen key). Provides `to_dict` (option representation plus `unicity`, `target`, `attribute`, `key`, `hide`) and `from_dict`.

---

### PlayerFactoryTemplate
`multiplayer.game.PlayerFactoryTemplate(name)`

Set of options defining how the players of a game are customized. Independent of any game.

**Attributes & Properties:** `ID` (read-only), `name` (settable), `options` (new list of `(ID, name)` tuples).

**Methods:**

| Method | Description | Parameters | Raises |
|--------|-------------|------------|--------|
| `add_option` | Adds a copy of an option. An option associated with `"name"` replaces the previous one. | `option (Option)`, `player_attribute (str\|ParameterFamily)`, `hide (bool = False)`, `unicity (bool = False)` | `TypeError`, `ValueError`, `OptionAlreadyExistsError` |
| `get_option` | Returns the `OptionEntry` of an option. | `option_id (str)` | `KeyError` |
| `del_option` | Removes an option. | `option_id (str)` | `KeyError` |
| `to_dict` / `from_dict` | Dictionary representation (`template_id`, `name`, `options`). | - / `data (dict)` | `TypeError`, `ValueError`, `OptionAlreadyExistsError` |

---

### PlayerFactory
`multiplayer.game.PlayerFactory(template, game_id)`

Creates the players of a game from a copy of the options of a template (the options receive new IDs). Created by `Game.create_player_factory`. The excluded values of unique options are computed from the players of the game.

**Attributes & Properties:** `ID`, `game_id`, `options` (new list of `(ID, name)` tuples).

**Methods:**

| Method | Description | Parameters | Raises |
|--------|-------------|------------|--------|
| `get_option` | Returns `{"entry", "exclusions", "proposed_value"}` for an option. | `option_id (str)`, `context (dict[str, str]\|None)` | `KeyError` |
| `create_player` | Creates a `Player` from the chosen values (absent options take their proposed value). The player is not added to the game. | `values (dict\|None)`, `context (dict[str, str]\|None)` | `InvalidOptionValueError`, `OptionValueAlreadyGivenError`, `LackingOptionError` |
| `to_dict` / `from_dict` | Dictionary representation (`factory_id`, `options`); `from_dict` is reserved for restoration. | - / `data (dict)`, `game_id (str)` | `TypeError`, `ValueError`, `OptionAlreadyExistsError` |

---

### Player
`multiplayer.game.Player(name, **kwargs)`

Represents a player in a game context.

**Parameters:**

| Name | Type | Description | Required | Default |
|------|------|-------------|----------|---------|
| `name` | `str` | The name of the player. | No | `"Player"` |
| `**kwargs` | variable | Optional parameters. Each parameter must be a tuple `(family, initial_value)` where `family` is a `ParameterFamily`. | No | - |

**Attributes & Properties:**

| Name | Type | Description | Settable | Implementation Detail |
|------|------|-------------|----------|-----------------------|
| `ID` | `str` | Unique identifier. | No | Automatically generated using `uuid.uuid4()`. |
| `name` | `str` | The name of the player. | Yes | Initialized with the name provided at creation. |
| `static_state` | `dict` | Custom attributes for data that rarely changes. | Yes | Initialized with parameters from `ParameterFamily.STATIC`. |
| `dynamic_state` | `dict` | Custom attributes for data that changes frequently. | Yes | Initialized with parameters from `ParameterFamily.DYNAMIC`. |

**Methods:**

| Method | Description | Parameters | Raises |
|--------|-------------|------------|--------|
| `get_by_id` (class method) | Returns the existing player with the given ID, or `None`. Every created (or restored) player is recorded in a global registry of weak references, which does not keep players alive. | `player_id (str)` | - |

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
| `role` | `UserRole` | User's permission level. | Yes | Defaults to `UserRole.PLAYER`. |
| `groups_id` | `list[str]` | IDs of groups where the user is admin. | No (but mutable) | Initialized as an empty list; the list itself does not validate group IDs. |
| `players_id` | `list[str]` | IDs of the active `Player` objects (associated with an unfinished game, as player or observer) created during a session in which the user was logged in. | No (but mutable) | Initialized as an empty list. Library users are responsible for removing IDs of players only associated with finished games; when persistence is enabled, the list is cleaned up before each `User` save. |

**Methods:**

- `change_password(new_password: str)`: Updates the user's password and regenerates the hash using `bcrypt`.

---

### Game
`multiplayer.game.Game(name, max_players, max_observers, password, observer_password, turn_based, min_players, **kwargs)`

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
| `min_players` | `int` | Min players required to start the game. `0` (or `<= 0`) allows starting without players. Capped at `max_players` when greater. | No | `0` |
| `**kwargs` | variable | Optional custom parameters (tuple of family and value). | No | - |

**Attributes & Properties:**

| Name | Type | Description | Settable | Implementation Detail |
|------|------|-------------|----------|-----------------------|
| `ID` | `str` | Unique identifier. | No | Automatically generated using `uuid.uuid4()`. |
| `name` | `str` | The name of the game. | Yes | - |
| `hash` | `str \| None` | Hashed player password. | No | Generated via `bcrypt`. |
| `observer_hash` | `str \| None` | Hashed observer password. | No | Generated via `bcrypt`. |
| `turn_based` | `bool` | Turn-based flag. | No | - |
| `min_players` | `int` | Effective min players required to start the game. | No | Initialized from the `min_players` parameter, capped at `max_players` when greater. |
| `player_factory` | `PlayerFactory \| None` | The player factory of the game, or `None`. | No | Set by `create_player_factory`. |
| `players` | `tuple[str]` | Read-only tuple of the IDs of the players, in turn order. | No | Backed by internal list `_players` (of player IDs). |
| `observers` | `tuple[str]` | Read-only tuple of the IDs of the observers. | No | Backed by internal list `_observers` (of player IDs). |
| `current_player` | `str \| None` | The ID of the player whose turn it is. | No | Only relevant for turn-based games. |
| `game_state` | `GameState` | Current state of the game. | No | - |
| `static_state` | `dict` | Static custom attributes. | Yes | Initialized from `ParameterFamily.STATIC`. |
| `dynamic_state` | `dict` | Dynamic custom attributes. | Yes | Initialized from `ParameterFamily.DYNAMIC`. |

**Methods:**

| Method | Description | Parameters | Raises |
|--------|-------------|------------|--------|
| `get_by_id` (class method) | Returns the existing game with the given ID, or `None`. Every created (or restored) game is recorded in a global registry of weak references, which does not keep games alive. | `game_id (str)` | - |
| `change_password` | Changes the game password. | `new_password (str)` | - |
| `create_player_factory` | Creates, replaces (no player yet) or removes (`None`) the player factory, while the game is pending. | `template (PlayerFactoryTemplate\|None)` | `TypeError`, `GameAlreadyStartedError`, `GameIsFinishedError`, `GameHasPlayersError` |
| `join_game_as_player` | Adds a player to the game, checking the constraints of the player factory if any. | `player (Player\|str)`, `password (str\|None)` | `PlayerNotFoundError`, `PasswordError`, `GameIsFullError`, `LackingOptionError`, `InvalidOptionValueError`, `OptionValueAlreadyGivenError` |
| `create_and_join_player` | Creates a player from the factory and adds it to the game atomically; returns the player. | `values (dict\|None)`, `password (str\|None)`, `context (dict[str, str]\|None)` | `PlayerFactoryNotDefinedError` and the exceptions of `create_player` / `join_game_as_player` |
| `remove_player` | Removes a player. | `player (Player\|str)` | `PlayerNotFoundInGameError` |
| `join_game_as_observer` | Adds an observer. | `player (Player\|str)`, `password (str\|None)` | `PlayerNotFoundError`, `PasswordError`, `GameIsFullError` |
| `remove_observer` | Removes an observer. | `player (Player\|str)` | `PlayerNotFoundInGameError` |
| `start` | Sets state to `IN_PROGRESS`. | - | `GameAlreadyStartedError`, `GameIsFinishedError`, `NotEnoughPlayersError` |
| `pause` | Sets state to `PAUSING`. | - | `GameNotStartedError` |
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
| `games` | `tuple[str]` | Read-only tuple of the IDs of the games in the group. | No | Backed by internal list `_games` (of game IDs). |
| `parameters` | `dict` | Custom group parameters. | Yes | Initialized from `kwargs`. |

**Methods:**

- `add_game(game: Game | str)`: Adds the ID of a game to the end of the group. The game can be given by its ID, as long as the `Game` object still exists. Raises `GameNotFoundError` if no existing game matches.
- `remove_game(game: Game | str)`: Removes the ID of a game from the group. Raises `GameNotFoundInGroupError` if not present.

---

## Enumerations

### UserRole
`multiplayer.UserRole`
- `PLAYER`: Standard user.
- `GROUP_ADMIN`: Admin for specific groups (includes `PLAYER` permissions).
- `SERVER_ADMIN`: Global administrator (includes `GROUP_ADMIN` permissions for all groups on the server).

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

### OptionType
`multiplayer.OptionType`
- `CHECK`: Boolean option (checkbox).
- `RANGE`: Numeric option within an interval (slider, numeric field).
- `LIST`: Option chosen among `choices` (drop-down list).
- `TEXT`: Text option (text field).

---

## Persistence

### Save
`multiplayer.save.Save(file_path, save_format)`

Handles saving and restoring `Player`, `User`, `Game`, `GameGroup` and `PlayerFactoryTemplate` instances to and from a save file. `Option` and `PlayerFactory` objects are saved within the template or the game that contains them. Objects are kept in an in-memory buffer and written to disk only when `flush()` is called. Save files produced before templates were introduced remain readable.

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
| `save` | Saves or updates an instance in the in-memory buffer (replaces if same class and ID). Before saving a `User`, cleans its `players_id` list of players no longer associated with any unfinished game. | `obj (Player\|User\|Game\|GameGroup\|PlayerFactoryTemplate)` | `SaveError` |
| `load` | Returns the list of all stored instances of a given class. | `target (str\|type)` | `SaveError` |
| `reset` | Clears the buffer and rewrites the file with an empty valid structure. | - | `SaveError` |
| `flush` | Persists the in-memory buffer to the save file. | - | `SaveError` |

---

## Networking

### GameServer
`multiplayer.server.GameServer(host, port, unencrypted_port, password, name, use_tls, tls_self_signed, tls_domain, tls_cert_path, tls_key_path, discoverable, multicast_group, multicast_port, persistence_mode, persistence_path, persistence_periodicity, garbage_collection_periodicity)`

Manages the server side of the multiplayer protocol (version 2, revision 2.1, features `player_factory`). It handles client connections, authentication, game state distribution, and holds a registry of player factory templates (`FACTORY_TEMPLATE_*` requests, persisted with the other server data).

**Parameters:**

| Name | Type | Description | Required | Default |
|------|------|-------------|----------|---------|
| `host` | `str` | IPv4 address to listen on. | No | `"0.0.0.0"` |
| `port` | `int` | Main TCP port (TLS-secured if `use_tls` is `True`). | No | `65432` |
| `unencrypted_port` | `int \| None` | Optional secondary TCP port without encryption. | No | `None` |
| `password` | `str \| None` | Optional password required for initial connection. | No | `None` |
| `name` | `str` | Human-readable server name. | No | `""` |
| `use_tls` | `bool` | Enable TLS 1.3 on the main port. | No | `False` |
| `tls_self_signed` | `bool` | Generate and use a self-signed certificate. | No | `False` |
| `tls_domain` | `str` | Domain name used for the certificate. | No | `"localhost"` |
| `tls_cert_path` | `Path \| None` | Path to the TLS certificate. | No | `None` |
| `tls_key_path` | `Path \| None` | Path to the TLS private key. | No | `None` |
| `discoverable` | `bool` | Enable multicast discovery. | No | `False` |
| `multicast_group` | `str` | Multicast address for discovery. | No | `"239.255.0.1"` |
| `multicast_port` | `int` | UDP multicast port for discovery. | No | `65434` |
| `persistence_mode` | `SaveFormat \| None` | Persistence storage format. | No | `None` |
| `persistence_path` | `Path \| None` | Path to the persistence file. | No | `None` |
| `persistence_periodicity` | `int` | Seconds between cyclic persistence saves (0 to disable). | No | `0` |
| `garbage_collection_periodicity` | `int` | Seconds between cleanups of players only associated with finished games or with no game and no longer reachable (players with no game are kept while attached to an open session or listed in a user's `players_id`). | No | `900` |

**Attributes & Properties:**

| Name | Type | Description | Settable |
|------|------|-------------|----------|
| `password_required` | `bool` | Indicates whether a server password is required. | No |

**Methods:**

| Method | Description | Parameters |
|--------|-------------|------------|
| `build_discovery_response` | Builds the information returned to a multicast discovery request. | - |
| `start` | Starts the server asynchronously. | - |
| `stop` | Stops the server asynchronously and persists data. | - |
| `restart` | Restarts the server asynchronously. | - |
| `save_persistence` | Immediately saves persistent server data (no-op if disabled). | - |

---

### GameClient
`multiplayer.client.GameClient(host, port, use_tls, tls_ca_path)`

Client side for connecting to and communicating with a `GameServer`.

**Parameters:**

| Name | Type | Description | Required | Default |
|------|------|-------------|----------|---------|
| `host` | `str` | Server IPv4 address or host name. | No | `"127.0.0.1"` |
| `port` | `int` | Server TCP port. | No | `65432` |
| `use_tls` | `bool` | Enable TLS for the connection. | No | `False` |
| `tls_ca_path` | `Path \| None` | Path to CA/server certificate for TLS validation. | No | `None` |

**Attributes & Properties:**

| Name | Type | Description | Settable |
|------|------|-------------|----------|
| `host` | `str` | Server IPv4 address or host name. | Yes |
| `port` | `int` | Server TCP port. | Yes |
| `use_tls` | `bool` | Whether TLS is enabled. | Yes |
| `tls_ca_path` | `Path \| None` | TLS validation certificate path, or `None` to use the system trust store. | No |
| `is_connected` | `bool` | Whether the client is currently connected. | No |
| `session_user` | `User \| None` | The user associated with the current session. | No |
| `server_revision` | `str \| None` | The protocol revision announced by the server (`"2.0"` if it does not support `PROTOCOL_INFO`, `None` while not connected). | No |
| `server_features` | `tuple[str, ...]` | The optional protocol features offered by the server. | No |

**Methods:**

| Method | Description | Parameters |
|--------|-------------|------------|
| `discover` | (Class method) Discovers servers on the local network (each result includes its `revision`). | `timeout (float = 2.0)`, `multicast_group (str = "239.255.0.1")`, `multicast_port (int = 65434)` |
| `connect` | Opens the TCP connection and retrieves the protocol revision and features (`PROTOCOL_INFO`). | - |
| `disconnect` | Closes the connection. | - |
| `login` | Authenticates a user and retrieves the account info. | `username (str)`, `password (str)` |
| `create_player` | Creates a new player for the session. Raises `UnsupportedFeatureError` if static attributes are sent to a revision 2.0 server. | `name (str)`, `is_default (bool = True)`, `static_attributes (dict\|None = None)`, `dynamic_attributes (dict\|None = None)` |
| `update_player` | Renames a player of the session and/or empties its `static_state` and `dynamic_state` (refused while the player takes part in a game). | `player_id (str)`, `name (str\|None = None)`, `reset_state (bool = False)` |
| `create_game` | Creates a game, optionally with a player factory built from a server template; returns its ID. | `name (str)`, `min_players`, `max_players`, `max_observers`, `turn_based`, `password`, `group_id`, `group_password`, `factory_template_id`, `attributes` |
| `list_factory_templates` / `get_factory_template` | Lists / details the factory templates of the server. | - / `template_id (str)` |
| `create_factory_template` / `update_factory_template` / `delete_factory_template` | Manages the factory templates (admin only). | `name`, `options` / `template_id`, `name`, `options` / `template_id` |
| `get_game_factory` | Retrieves the player factory of a game (exclusions, proposed values) and subscribes to `GAME_FACTORY_UPDATED`. | `game_id (str)`, `password (str\|None)`, `group_password (str\|None)` |
| `join_game_with_factory` | Creates a player from the factory of a game and joins it. | `game_id (str)`, `values (dict\|None)`, `password`, `group_password`, `is_default (bool\|None)` |
| `send_request` | Sends a protocol request and returns its response payload. | `command (str)`, `timeout (float = 10.0)`, `**kwargs` |
| `on_notification` | Registers a callback to handle server notifications. | `notification_type (str\|None)`, `callback (Callable[[dict], None])` |
| `save_persistence` | Requests an immediate persistence save from the server (admin only). | - |

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

*Implementation Note: Data is stored in `src/multiplayer/data` as CSV files. Registered names are stripped, empty names are removed, and duplicates are removed; special characters are preserved.*

### Functions

- `register_name_category(category_name: str, data: Any, category_type: str)`
  Registers a new custom category. `data` can be a list or a string/`Path` pointing to a CSV file. `category_type` is stored as supplied; use `"game"` or `"player"` for it to be returned by the corresponding suggestion functions.
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
| `MultiplayerError` | Base class for all multiplayer exceptions. |
| `UserAlreadyExistsError` | Raised when a username is already taken. |
| `GroupNotFoundError` | Raised when a group ID does not exist. Returns the faulty ID in the message. |
| `UserNotFoundError` | Raised when a user account (or its ID) does not exist. Returns the faulty ID if provided. |
| `PlayerNotFoundError` | Raised when a player ID does not exist. Returns the faulty ID if provided. |
| `PlayerNotFoundInGameError` | Raised when trying to remove a player who is not in the game. |
| `PasswordError` | Raised when an incorrect password is provided. |
| `GameIsFullError` | Raised when a game has reached its player or observer limit. |
| `GameAlreadyStartedError` | Raised when trying to start a game that is already active or paused. |
| `NotEnoughPlayersError` | Raised when trying to start a game with fewer players than `min_players`. |
| `GameIsFinishedError` | Raised when attempting to modify a finished game. |
| `GameNotStartedError` | Raised when an action (pause, stop, next_turn) requires the game to be started. |
| `GameAlreadyPausedError` | Raised when trying to pause an already paused game. |
| `GameNotPausedError` | Raised when trying to resume a game that is not paused. |
| `GameNotTurnBasedError` | Raised when a turn-based action is called on a non-turn-based game. |
| `GameNotFoundError` | Raised when a game ID does not exist. Returns the faulty ID if provided. |
| `GameNotFoundInGroupError` | Raised when trying to remove a game not present in the specified group. |
| `SaveError` | Raised when a save file is incompatible or corrupted, when an unknown save format is requested, or when an unsupported class is saved or loaded. |
| `GameHasPlayersError` | Raised when a player factory is created or replaced in a game that already has players. |
| `PlayerFactoryNotDefinedError` | Raised when the player factory of a game without factory is used. |
| `UnsupportedFeatureError` | Raised by `GameClient` when a protocol feature not offered by the server is used. |
| `OptionError` | Base class of the option-related errors below. |
| `OptionValueAlreadyGivenError` | A unique option value is already carried by another player (`option_id`, `value`). |
| `LackingOptionError` | No value is available for an option (`option_id`, `reason`: `ABSENT_FROM_PLAYER` or `NO_AVAILABLE_VALUE`). |
| `InvalidOptionValueError` | Also a `ValueError`: unknown option, incompatible type or invalid value (`option_id`, `value`, `reason`). |
| `OptionAlreadyExistsError` | An identical or similar option is already present in a template or factory. |
