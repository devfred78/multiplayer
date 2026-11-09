# Instructions for developing version 2 of multiplayer

This document provides instructions for developing version 2 of the multiplayer module. It describes the coding conventions, dependencies, and technical specifications needed to ensure compatibility and consistency between the different modules of the package.

## General rules

## Comment and docstring conventions

- All comments must be written in English.
- Modules, classes, and functions must have English docstrings that follow the PEP 257 convention and the Google style.

### Naming conventions

- Names of variables, functions, and methods must be descriptive (in English) and use the snake_case convention.
- Class names must be in CamelCase.
- Constant names must be in UPPER CASE.
- Module names must be in snake_case.
- Private method names must be prefixed with an underscore (`_`).
- Private class variables must be prefixed with two underscores (`__`).
- Variables must be declared first in each block of code.

### Exception conventions
- Keep the number of custom exception classes to a minimum.
- Group related errors in a separate module for easier maintenance.
- Name exceptions in English, using the PascalCase convention with the suffix "Error".
- Inherit from the `Exception` class of the builtins module (or from an appropriate subclass). Do not derive directly from `BaseException`.
- Chain exceptions with `raise ... from ...` to preserve the original cause.
- Structure the code with `try/except/else/finally` for efficient error and resource management, following this pattern whenever possible:
```
try:
    # Code that may raise exceptions
except SpecificError as e:
    # Targeted handling
except Exception as e:
    # Generic fallback (avoids hiding all errors)
else:
    # Code to execute if no exception is raised
finally:
    # Code to execute whether or not an exception occurred (file and connection cleanup, ...)
```
- Error messages must be exclusively in English.
- Error messages must be explicit and, where relevant, must also include the input values that caused the error.
- Exceptions must be logged with the logging module: `logging.exception("Message")`.
- Exceptions must be documented in the docstring (`:raises:` or `Raises:`), along with the conditions that trigger them.
- `assert` must be reserved for internal invariant checks, not for validating user input.
- Do not use exceptions for normal flow control (for example, to exit a loop), because the exception mechanism is more expensive than classic control structures.

### Other conventions

- All "ID" properties must be alphanumeric strings, generated uniquely at instantiation using the `uuid.uuid4()` function of the uuid module. They must be read-only.
- All implemented objects must be covered by a set of unit tests to ensure they work properly. These tests must cover all possible use cases of the objects and must be automated. They must be runnable with `pytest`.
- The `pyproject.toml` file must comply with the TOML format specification and with the instructions described [here](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/), and must contain the information needed to manage the project with `uv`.
- Documentation files must be written in Markdown and must be kept up to date with changes to the code.

## Code organization

Generally speaking, code files must be structured so that the code is easy to understand and maintain. Files must be divided into logical sections, and each section must be well documented.

This chapter is organized into subchapters, each named after a source file to be implemented as a module of the multiplayer package.

Unless specifically stated otherwise, the objects to be implemented (functions, classes, etc.) are described in terms of the expected effect from the point of view of the user of the object. The developer is free to add any intermediate objects or files they consider necessary to achieve this end result.

The files are organized according to the layout of a Python project managed by `uv`, which follows the standard Python project structure (with the `pyproject.toml` file) and adds a few specific elements (such as the `uv.lock` file).

The source files are therefore in the `src/multiplayer` directory, the unit tests in `tests/`, the distribution files in `dist/`, and some more complex test scripts in `scripts/`. `pyproject.toml`, `uv.lock`, `README.md`, and all other documentation and configuration files are at the root of the project.

### Contents of the src/multiplayer/__init__.py file

This file contains the imports needed for the multiplayer package to work. In general, it declares all the constant elements (constants, enumerations) used by the multiplayer modules.
In particular, it contains the following elements:

#### `UserRole` (Enum)
An enumeration for the role of a user account.

* `UserRole.PLAYER`: A standard user who can join and participate in games.
* `UserRole.GROUP_ADMIN`: A user who can manage games within the groups assigned to them. This role includes all the permissions of a `PLAYER`.
* `UserRole.SERVER_ADMIN`: A user with full administrative access to the server. This role includes the `GROUP_ADMIN` role (for all groups on the server), which itself includes the `PLAYER` role.

#### `GameState` (Enum)
An enumeration representing the current status of a game.

* `GameState.PENDING`: The game has been created but has not started yet. This state is dedicated to waiting for players. Players can join or leave the game.
* `GameState.PAUSING`: The game is currently paused. This state is used when a game in progress is temporarily suspended.
* `GameState.IN_PROGRESS`: The game is currently active.
* `GameState.FINISHED`: The game is over. No more moves can be played and the results are final.

#### `ParameterFamily` (Enum)
An enumeration representing the families of optional customization parameters for players and games.

* `ParameterFamily.STATIC`: Static parameters that rarely or never change during the game.
* `ParameterFamily.DYNAMIC`: Dynamic parameters that may change frequently during the game.

#### `SaveFormat` (Enum)
An enumeration representing the storage formats supported by a save file.

* `SaveFormat.JSON`: Save in a single JSON document.
* `SaveFormat.SQLITE`: Save in an SQLite database.

### Contents of the src/multiplayer/exceptions.py file

This file contains the definitions of the custom exceptions used in this module. It defines the classes and functions needed to handle game-specific errors.
In particular, it contains the following classes:

#### Class `MultiplayerError`
This class is the base class for all exceptions related to the `multiplayer` module. It is the root of the custom exception hierarchy.

#### Class `UserAlreadyExistsError`
This class is derived from `MultiplayerError` and is used to report an attempt to create a user account with a name that already exists.

#### Class `SaveError`
This class is derived from `MultiplayerError` and is used to report that a save file is incompatible, corrupted, or cannot be read or written. It is also raised when an unknown save format is requested, or when an unsupported class is saved or loaded.

#### Class `GroupNotFoundError`
This class is derived from `MultiplayerError` and is used to report an attempt to use a group (or group ID) that does not exist. This exception includes the invalid ID in its message.

#### Class `UserNotFoundError`
This class is derived from `MultiplayerError` and is used to report an attempt to use a user account (or its ID) that does not exist. This exception includes the invalid ID in its message (if provided).

#### Class `PlayerNotFoundError`
This class is derived from `MultiplayerError` and is used to report an attempt to use a player (or player ID) that does not exist. This exception includes the invalid ID in its message (if provided).

#### Class `PlayerNotFoundInGameError`
This class is derived from `PlayerNotFoundError` and is used to report an attempt to remove a player **from a game they are not part of**. This exception includes the invalid player ID in its message (if provided).

#### Class `PasswordError`:
This class is derived from `MultiplayerError` and is used to report an attempt to use an incorrect password.

#### Class `GameIsFullError`:
This class is derived from `MultiplayerError` and is used to report an attempt to add a player or observer to a game that is already full.

#### Class `GameAlreadyStartedError`:
This class is derived from `MultiplayerError` and is used to report an attempt to start a game that is already in progress.

#### Class `NotEnoughPlayersError`:
This class is derived from `MultiplayerError` and is used to report an attempt to start a game whose number of players is lower than the minimum required (`min_players` parameter of the `Game` class).

#### Class `GameIsFinishedError`:
This class is derived from `MultiplayerError` and is used to report an attempt to modify a game that has ended.

#### Class `GameNotStartedError`:
This class is derived from `MultiplayerError` and is used to report an attempt to pause, resume, stop, or advance (for example, move to the next turn) a game that has not started yet.

#### Class `GameAlreadyPausedError`:
This class is derived from `MultiplayerError` and is used to report an attempt to pause a game that is already paused.

#### Class `GameNotPausedError`:
This class is derived from `MultiplayerError` and is used to report an attempt to resume a game that is not paused.

#### Class `GameNotTurnBasedError`:
This class is derived from `MultiplayerError` and is used to report an attempt to perform a turn-specific action in a game that is not turn-based.

#### Class `GameNotFoundError`:
This class is derived from `MultiplayerError` and is used to report an attempt to look up a game that does not exist. This exception includes the invalid game ID in its message (if provided).

#### Class `GameNotFoundInGroupError`:
This class is derived from `GameNotFoundError` and is used to report an attempt to remove a game from a group that does not contain it. This exception includes the invalid game ID in its message (if provided).

### Contents of the src/multiplayer/game.py file

This file contains the main game management logic. It defines the classes and functions needed to create, manage, and resolve games.
In particular, it contains the following classes:

#### Class `Player`
This class represents a player in the context of the game. It is the entity that actually takes part in games. While a `User` account manages access and permissions, the `Player` object carries the game-related attributes (name, score, state, etc.). Typically, a `Player` object is created just before a game and destroyed after it ends. This behavior nevertheless remains an implementation choice, as the `multiplayer` library does not handle the creation or destruction of `Player` objects when a `Game` object is instantiated or ends (destruction may however be handled as part of the automatic cleanup feature of the `GameServer` class, see the related paragraph).

It is instantiated with the following parameters:

| Name | Type | Description | Mandatory | Default |
|------------|----------|--------------|-------------|---------|
| `name` | str | The player's name.  | Yes | - |
| `**kwargs` | variable | Optional parameters to customize the player. Each parameter must be a tuple `(family, initial_value)`, where `family` is a `ParameterFamily` member specifying whether the parameter is static or dynamic, and `initial_value` is its initial value. The family is chosen freely by the user to help organize information, but has no impact on internal processing (all families are handled the same way). | No | - |

It has the following attributes:

| Name | Type | Description | Editable | Implementation details |
|-----------------|------|-------------|------------|----------------------------|
| `ID` | str | The unique identifier of the player.  | No | Automatically initialized with the value of `uuid.uuid4()`.  |
| `name` | str | The player's name. | Yes | Automatically initialized with the name provided when the player is created.|
| `static_state` | dict | Custom player attributes, intended to store information that rarely or never changes during the game.  | Yes | Automatically initialized with the parameters declared as belonging to the `ParameterFamily.STATIC` family, but can later be extended with any other parameter of the user's choice. For example, if `Player` is instantiated with `Player(name="My name", color=(ParameterFamily.STATIC, "white"), score=(ParameterFamily.DYNAMIC, 0))`, then `static_state` is equal to `{"color":"white"}`. |
| `dynamic_state` | dict | Custom player attributes, intended to store information that may change frequently during the game. | Yes | Automatically initialized with the parameters declared as belonging to the `ParameterFamily.DYNAMIC` family, but can later be extended with any other parameter of the user's choice. For example, if `Player` is instantiated with `Player(name="My name", color=(ParameterFamily.STATIC, "white"), score=(ParameterFamily.DYNAMIC, 0))`, then `dynamic_state` is equal to `{"score":0}`.    |

Every `Player` object created (or restored from a save) is recorded in a global registry, indexed by its ID. This registry makes it possible to designate a player by its ID alone, for example in the `join_game_as_player` and `join_game_as_observer` methods of the `Game` class.

The `Player` class has the following methods:

- `get_by_id` (class method): looks up an existing player from its ID.
  - Implementation details: The registry only holds weak references (`weakref.WeakValueDictionary`): it does not prevent the destruction of a `Player` object that is no longer used elsewhere.
  - Parameters:
    - `player_id` (str): the ID of the player to look up. Mandatory.
  - Return value: The corresponding `Player` object, or `None` if no existing player has this ID.

#### Class `User`
This class represents a user account. It grants access to various capabilities depending on its access level (authentication). A user is an entity distinct from the player: the user manages credentials and rights, while the player manages presence in the game.

A user can take part in several games simultaneously, as a player as well as an observer. Each participation requires the creation of a distinct `Player` object, each one attached to the user account through the `players_id` attribute. Indeed, a given `Player` object can only take part in a single game.

It is instantiated with the following parameters:

| Name | Type | Description | Mandatory | Default |
|------------|------|-----------------------|-------------|--------------|
| `username` | str | The account username. | Yes | - |
| `password` | str | The account password.      | Yes | - |
| `email` | str | The account email address.     | No | `""` (empty string) |


If a `User` object is instantiated with a `username` already used by an existing `User` instance, a `UserAlreadyExistsError` exception is raised and the instantiation fails.

The class has the following attributes:

| Name | Type | Description | Editable | Implementation details |
|-------------|--------------|--------------|------------|----------------------------|
| `ID` | str | The unique identifier of the user account. | No | Automatically initialized with the value of `uuid.uuid4()`.|
| `username` | str | The account username.  | No | -|
| `hash` | str | The hash of the account password.| No | The hash is automatically generated from `password` with `bcrypt`.|
| `email` | str | The account email address. | Yes | -|
| `role` | `UserRole` | The role of the account (i.e. its permission level).  | Yes | - |
| `groups_id` | List[str] | The identifiers of the groups the account administers. Only relevant if `role == UserRole.GROUP_ADMIN`. A `GroupNotFoundError` exception is raised if one of the identifiers does not match an existing group. In that case, the value of `groups_id` is not updated. | No (but mutable) | Initialized with an empty list, this attribute can be extended and modified using `list` methods such as `append`, `extend`, `pop`, ... As it is a read-only attribute, reassignment is not allowed. |
| `players_id` | List[str] | The identifiers of the active `Player` objects (i.e. associated with a game that is not finished, either as a player or as an observer) created during a session in which the user was logged in. | No (but mutable) | It is the responsibility of the user of the `multiplayer` library to regularly check this list and remove from it the identifiers of `Player` objects that are only associated with finished games. However, when the persistence feature is enabled, saving `User` objects performs a check and cleanup of this list before saving. Thus, upon restoration, this list should normally be clean and consistent with the `Player` objects actually associated with unfinished games, or associated with no game (case of a `Player` object waiting to be assigned to a game). |

The `User` class has the following methods:

- `change_password`: changes the password of the user account. The `hash` attribute of the current instance is updated with the new password using `bcrypt`.
    - Parameters:
      - `new_password` (str): the new password to use for the user account. Mandatory.
    - Return value:
      - None.


#### Class `Game`
This class represents a game. It is instantiated with the following parameters:

| Name | Type | Description | Mandatory | Default |
|---------------------|--------|-------------|-------------|---------|
| `name` | str\|`None` | The name of the game.  | No | `None` |
| `max_players` | int\|`None` | Maximum number of players. If `None`, there is no limit. If 0 or negative, no players are allowed.| No | `None` |
| `max_observers` | int\|`None` | Maximum number of observers. If `None`, there is no limit. If 0 or negative, no observers are allowed.  | No | `None` |
| `password` | str\|`None` | Game password. If `None`, the game is public (no password is needed to join the game). | No | `None`|
| `observer_password` | str\|`None` | Observer password. If `None`, observers use the game password, defined by the `password` parameter. If that is also `None`, observers can join the game without a password. | No | `None` |
| `turn_based` | bool | `True` if the game is turn-based, `False` for simultaneous play. | No | `False` |
| `min_players` | int | Minimum number of players required to start the game. If 0 (or negative), the game can start without any player. If greater than `max_players`, it is equivalent to `min_players = max_players`: exactly the maximum number of players is required to start the game. | No | `0` |
| `**kwargs` | variable | Optional parameters to customize the game. Each parameter must be a tuple `(family, initial_value)`, where `family` is a `ParameterFamily` member specifying whether the parameter is static or dynamic, and `initial_value` is its initial value. The family is chosen freely by the user to help organize information, but has no impact on internal processing (all families are handled the same way). | No | - |

The class has the following attributes:

| Name | Type | Description | Editable | Implementation details |
|-----------------|-----------------|-------------|------------|----------------------------|
| `ID` | str | The unique identifier of the game. | No | Automatically initialized with the value of `uuid.uuid4()`.|
| `name` | str | The name of the game. | Yes | - |
| `hash` | str\|`None` | The hash of the game password. `None` if the game is public (no password).| No | The hash is automatically generated from `password` with `bcrypt`. |
| `observer_hash` | str\|`None` | The hash of the observer password. `None` if no observer password is set. | No | The hash is automatically generated from `observer_password` with `bcrypt`.|
| `turn_based` | bool | `True` if the game is turn-based, `False` for simultaneous play. | No | - |
| `min_players` | int | Effective minimum number of players required to start the game (0 means no minimum). | No | Initialized with the `min_players` parameter. If that value is greater than `max_players` (when not `None`), `max_players` is returned instead. |
| `players` | Tuple[str] | Tuple (immutable list) of the IDs of the `Player` objects representing the players of the game. The order of the players is the order in which they take their turns in a turn-based game. Some games allow the order to change during play, so dedicated methods are provided for this purpose. Do not attempt to change the order directly through this attribute. | No | The corresponding internal variable (`_players`) is a list, converted to a tuple when exposed publicly through the `players` attribute. |
| `observers` | Tuple[str] | Tuple (immutable list) of the IDs of the `Player` objects representing the observers of the game. | No | The corresponding internal variable (`_observers`) is a list, converted to a tuple when exposed publicly through the `observers` attribute. |
| `current_player`| str | The ID of the `Player` object whose turn it is. Only meaningful for turn-based games. | No | - |
| `game_state` | `GameState` | Current state of the game. | No | - |
| `static_state` | dict | Custom game attributes, intended to store information that rarely or never changes during the game.  | Yes | Automatically initialized with the parameters declared as belonging to the `ParameterFamily.STATIC` family, but can later be extended with any other parameter of the user's choice. For example, if `Game` is instantiated with `Game([...], style=(ParameterFamily.STATIC, "blitz"), score=(ParameterFamily.DYNAMIC, "0-0"))`, then `static_state` is equal to `{"style":"blitz"}`. |
| `dynamic_state` | dict | Custom game attributes, intended to store information that may change frequently during the game. | Yes | Automatically initialized with the parameters declared as belonging to the `ParameterFamily.DYNAMIC` family, but can later be extended with any other parameter of the user's choice. For example, if `Game` is instantiated with `Game([...], style=(ParameterFamily.STATIC, "blitz"), score=(ParameterFamily.DYNAMIC, "0-0"))`, then `dynamic_state` is equal to `{"score":"0-0"}`.    |

The `Game` class has the following methods:

- `change_password`: changes the password of the game. The `hash` attribute of the current instance is updated with the new password using `bcrypt`.
    - Parameters:
      - `new_password` (str): the new password to use for the game. Mandatory.
    - Return value:
      - None.
- `join_game_as_player`: joins a game as a player.
  - Description: This method lets a player join a game, given their ID or `Player` object, and a password if the game is private. It raises an exception if the player does not exist or if the password is incorrect.
  - Implementation details: If successful, the method adds the ID of the `Player` object to the `_players` list of the current instance.
  - Parameters:
    - `player` (`Player`|str): the player joining the game, given either as the corresponding `Player` object or as a string containing their ID. Mandatory.
    - `password` (str\|`None`): password required to join the game. If the game is public, pass `None`. Optional. Default: `None`.
  - Exceptions raised:
    - `PlayerNotFoundError`: raised if the specified player does not exist.
    - `PasswordError`: raised if the password is incorrect.
    - `GameIsFullError`: raised if the maximum number of players has been reached and no more players can be added.
  - Return value: None.

- `remove_player`: removes a player from the game.
  - Description: This method removes a player from the game, given their ID or `Player` object. It raises an exception if the player is not found in the game.
  - Implementation details: If successful, the method removes the ID of the `Player` object from the `_players` list of the current instance.
  - Parameters:
    - `player` (`Player`|str): the player to remove from the game, given either as the corresponding `Player` object or as a string containing their ID. Mandatory.
  - Exceptions raised:
    - `PlayerNotFoundInGameError`: raised if the specified player is not found in the game.
  - Return value: None.

- `join_game_as_observer`: joins a game as an observer.
  - Description: This method lets a player join a game as an observer. It raises an exception if the game is private and the password is incorrect.
  - Implementation details: If successful, the method adds the ID of the `Player` object to the `_observers` list of the current instance.
  - Parameters:
    - `player` (`Player`|str): the player joining the game as an observer, given either as the corresponding `Player` object or as a string containing their ID. Mandatory.
    - `password` (str\|`None`): password required to join the game as an observer. If observation of the game is public, pass `None`. Optional. Default: `None`.
  - Exceptions raised:
    - `PlayerNotFoundError`: raised if the specified player does not exist.
    - `PasswordError`: raised if the game is private and the password is incorrect.
    - `GameIsFullError`: raised if the maximum number of observers has been reached and no more observers can be added.
  - Return value: None.

- `remove_observer`: removes an observer from a game.
  - Description: This method lets an observer leave a game. It raises an exception if the specified player is not found in the game.
  - Implementation details: If successful, the method removes the ID of the `Player` object from the `_observers` list of the current instance.
  - Parameters:
    - `player` (`Player`|str): the player leaving the game as an observer, given either as the corresponding `Player` object or as a string containing their ID. Mandatory.
  - Exceptions raised:
    - `PlayerNotFoundInGameError`: raised if the specified player is not found in the game.
  - Return value: None.

- `start`: starts a game.
  - Description: This method starts a game. It raises an exception if the game is already in progress, has ended, or does not have enough players. If successful, the method sets the `game_state` attribute to `GameState.IN_PROGRESS`.
  - Implementation details: The `GameState.PAUSING` status is also considered a game in progress. The number of players is compared to the `min_players` attribute; with the default value (0), the game can start without any player.
  - Parameters:
    - None.
  - Exceptions raised:
    - `GameAlreadyStartedError`: raised if the game is already in progress.
    - `GameIsFinishedError`: raised if the game is over.
    - `NotEnoughPlayersError`: raised if the number of players is lower than `min_players`.
  - Return value: None.

- `pause`: pauses a game.
  - Description: This method pauses a game. It raises an exception if the game is not in progress or is already paused.
  - Implementation details: If successful, the method sets the `game_state` attribute to `GameState.PAUSING`.
  - Parameters:
    - None.
  - Exceptions raised:
    - `GameNotStartedError`: raised if the game is not in progress.
    - `GameAlreadyPausedError`: raised if the game is already paused.
  - Return value: None.

- `resume`: resumes a paused game.
  - Description: This method resumes a paused game. It raises an exception if the game is not paused.
  - Implementation details: If successful, the method sets the `game_state` attribute to `GameState.IN_PROGRESS`.
  - Parameters:
    - None.
  - Exceptions raised:
    - `GameNotPausedError`: raised if the game is not paused.
  - Return value: None.

- `stop`: ends a game.
  - Description: This method ends a game. It raises an exception if the game is not in progress.
  - Implementation details: If successful, the method sets the `game_state` attribute to `GameState.FINISHED`.
  - Parameters:
    - None.
  - Exceptions raised:
    - `GameNotStartedError`: raised if the game is not in progress.
  - Return value: None.

- `next_turn`: moves on to the next turn.
  - Description: In a turn-based game, this method moves on to the next turn. It raises an exception if the game is not in progress or has ended. If successful, the method sets the `current_player` attribute to the next player.
  - Parameters:
    - None.
  - Exceptions raised:
    - `GameNotStartedError`: raised if the game is not in progress.
    - `GameIsFinishedError`: raised if the game is over.
    - `GameNotTurnBasedError`: raised if the game is not turn-based.
  - Return value: None.

- `reverse_order`: reverses the order of the players in a turn-based game.
  - Description: This method reverses the order of the players in a game. The order can be reversed in any game state other than `GameState.FINISHED`. It raises an exception if the game is over. If successful, the reversed order is reflected in the `players` attribute.
  - Implementation details: If successful, the method actually reverses the order of the internal `_players` list.
  - Parameters:
    - None.
  - Exceptions raised:
    - `GameIsFinishedError`: raised if the game is over.
    - `GameNotTurnBasedError`: raised if the game is not turn-based.
  - Return value: None.

- `set_player_rank`: sets the rank of a player in a turn-based game.
  - Description: This method sets the rank of a player in a turn-based game. The other players keep their relative order; their ranks are incremented or decremented to fill the position the player leaves and to make room at the position the player moves to. The rank can be changed in any game state other than `GameState.FINISHED`. It raises an exception if the game is over. If successful, the new rank is reflected in the `players` attribute.
  - Implementation details: If successful, the method actually modifies the internal `_players` list.
  - Parameters:
    - `player` (`Player`|str): the player whose rank is changed, given either as the corresponding `Player` object or as a string containing their ID. Mandatory.
    - `rank` (int): the new rank of the player. Mandatory.
  - Exceptions raised:
    - `IndexError`: raised if the specified rank is invalid.
    - `GameIsFinishedError`: raised if the game is over.
    - `GameNotTurnBasedError`: raised if the game is not turn-based.
    - `PlayerNotFoundInGameError`: raised if the specified player is not found in the game.
  - Return value: None.

#### Class `GameGroup`
This class groups several games into a single object, making it possible to manage them in parallel and handle them as a group. It is instantiated with the following parameters:

| Name | Type | Description | Mandatory | Default |
|---------------------|--------|-------------|-------------|---------|
| `name` | str | The name of the game group.| Yes | - |
| `**kwargs` | variable | Optional parameters to customize the group. | No | - |

The class has the following attributes:

| Name | Type | Description | Editable | Implementation details |
|-----------------|-----------------|-------------|------------|----------------------------|
| `ID` | str | The unique identifier of the group. | No | Automatically initialized with the value of `uuid.uuid4()`.|
| `name` | str | The name of the group. | Yes | - |
| `games` | Tuple[`Game`] | Tuple (immutable list) of the `Game` instances representing the games of the group. | No | The corresponding internal variable (`_games`) is a list, converted to a tuple when exposed publicly through the `games` attribute. |
| `parameters` | dict | Customization parameters of the group. | Yes | Automatically initialized with the parameters given in `kwargs`, but can later be extended with any other parameter of the user's choice. |


The `GameGroup` class has the following methods:

- `add_game`: adds a game to the group. The game is appended to the end of the group's list of games.
  - Description: This method adds a game to the group, given its ID or `Game` object, and optionally a group administrator password. It raises an exception if the game does not exist or if the password is incorrect.
  - Implementation details: If successful, the method adds the `Game` object to the `_games` list of the current instance.
  - Parameters:
    - `game` (`Game`|str): the game to add, given either as a `Game` instance or as a string containing its ID. Mandatory.
  - Return value:
    - None.
  - Exceptions raised:
    - `GameNotFoundError`: raised if the specified game does not exist.
- `remove_game`: removes a game from the group. The game is removed from the group's list of games.
  - Parameters:
    - `game` (`Game`|str): the game to remove, given either as a `Game` instance or as a string containing its ID. Mandatory.
  - Implementation details: If successful, the method removes the `Game` object from the `_games` list of the current instance.
  - Return value:
    - None.
  - Exceptions raised:
    - `GameNotFoundInGroupError`: raised if the specified game is not in the group.

### Contents of the src/multiplayer/utils.py file

The package provides utility functions that suggest game and player names based on various categories.


#### Categories for games
* **`cities`**: Major cities of the world.
* **`countries`**: Sovereign nations.
* **`rivers`**: Major rivers of the world.
* **`seas_oceans`**: Main bodies of salt water.
* **`planets_moons`**: Celestial bodies of our solar system.

Implementation details:
* Categories are stored in plain text files, with one name per line, in the `src/multiplayer/data` directory (one file per category).
* CSV files are supported to allow a more complex structure if needed.
* Names are normalized to avoid duplicates and special characters.

#### Categories for players
* **`roman_gods`**: Deities of Roman mythology.
* **`greek_gods`**: Deities of ancient Greek mythology.
* **`egyptian_gods`**: Deities of ancient Egyptian mythology.
* **`european_kings`**: Historical European monarchs (men).
* **`european_queens`**: Historical European monarchs (women).

Implementation details:
* Categories are stored in plain text files, with one name per line, in the `src/multiplayer/data` directory (one file per category).
* CSV files are supported to allow a more complex structure if needed.
* Names are normalized to avoid duplicates and special characters.

#### Function `register_name_category(category_name, data, category_type)`
Registers a new custom category for name suggestions.

* **`category_name`** (`str`): The name of the new category.
* **`data`** (`list`, `str` or `Path`): A list of names, or a path to a text/CSV file (one name per line, or the first column of the CSV).
* **`category_type`** (`str`): `"game"` or `"player"`.

#### Function `unregister_name_category(category_name)`
Removes a custom category. Returns `True` on success.

#### Function `get_available_categories(category_type="all")`
Returns a list of the available name suggestion categories.

* **`category_type`** (`str`): `"all"`, `"game"`, or `"player"`.

#### Function `suggest_game_name(category=None)`
Suggests a random name for a game. If `category` is `None`, a game-related category is chosen at random.

#### Function `suggest_player_name(category=None)`
Suggests a random name for a player. If `category` is `None`, a player-related category is chosen at random.

### Contents of the src/multiplayer/save.py file

This file contains the logic for saving and restoring objects instantiated from the `Player`, `User`, `Game` and `GameGroup` classes. It defines the `Save` class, each instance of which represents a save file and links an in-memory buffer to a persistent file (JSON document or SQLite database).

#### Class `Save`
This class saves, updates, and restores the objects of the module. Objects are first stored in an in-memory buffer, then written to the file only when the `flush` method is explicitly called. It is instantiated with the following parameters:

| Name | Type | Description | Mandatory | Default |
|---------------|---------------------|-------------|-------------|------------------|
| `file_path` | `Path` | The path of the save file. | Yes | - |
| `save_format` | `SaveFormat`\|str | The save format, given either as a member of the `SaveFormat` enumeration or as a string (`"json"` or `"sqlite"`). | Yes | - |

Behavior at instantiation:
* If the file does not exist, it is created with an empty but valid structure.
* If the file already exists, its structure is checked. If it is compatible with the requested format, its content is loaded into the in-memory buffer. Otherwise, a `SaveError` exception is raised.
* If the save format is unknown, a `SaveError` exception is raised.

The class has the following attributes:

| Name | Type | Description | Editable | Implementation details |
|---------------|---------|-------------|------------|----------------------------|
| `file_path` | `Path` | The path of the save file. | Yes | Initialized from the `file_path` parameter. |
| `save_format` | `SaveFormat` | The storage format used. | Yes | Initialized from the `save_format` parameter. |

The `Save` class has the following methods:

- `save`: saves or updates an individual instance in the in-memory buffer.
  - Description: The object is serialized and stored in the buffer, indexed by its class and ID. If an object with the same class and ID already exists, it is replaced. The change is only persisted to the file when `flush` is called.
  - Implementation details: before saving a `User` object, a check is performed to clean up the list of identifiers of `Player` objects that are no longer associated with any unfinished game.
  - Parameters:
    - `obj` (`Player`|`User`|`Game`|`GameGroup`): the instance to save. Mandatory.
  - Exceptions raised:
    - `SaveError`: raised if the object is not an instance of a supported class.
  - Return value: None.

- `load`: loads all instances of a given class.
  - Description: Rebuilds and returns the list of instances of the requested class from the in-memory buffer.
  - Parameters:
    - `target` (str\|type): the class to load, or its name (`Player`, `User`, `Game` or `GameGroup`). Mandatory.
  - Exceptions raised:
    - `SaveError`: raised if the target does not match a supported class.
  - Return value: The list of rebuilt instances of the requested class.

- `reset`: resets the save file.
  - Description: Clears the in-memory buffer and rewrites the save file with an empty but valid structure.
  - Parameters:
    - None.
  - Return value: None.

- `flush`: writes the in-memory buffer to the save file.
  - Description: Persists all the objects in the buffer to the file, in the chosen format. This method must be called for the saves to actually be written to disk.
  - Parameters:
    - None.
  - Exceptions raised:
    - `SaveError`: raised if the data cannot be written to the file.
  - Return value: None.

### Contents of the src/multiplayer/server.py file

This file contains the logic for managing multiplayer servers.

#### Class GameServer
The `GameServer` class is responsible for managing connections and communications with clients in a multiplayer environment. It coordinates actions and broadcasts information to connected clients.

##### Parameters

The `GameServer` class is instantiated with the following parameters:

| Name | Type | Description | Mandatory | Default |
|---------------|---------------------|-------------|-------------|------------------|
| `host` | str | The IPv4 address on which the server listens for connections | No | `"0.0.0.0"` |
| `port` | int | The port number on which the server listens for connections | No | 65432 |
| `unencrypted_port` | int\|`None` | The port number for unencrypted connections, not protected by TLS | No | `None` |
| `password` | str\|`None` | The password required to access the server | No | `None` |
| `name` | str | The server name | No | `""` (empty string) |
| `use_tls` | bool | Use the TLS v1.3 protocol for secure communication | No | `False` |
| `tls_self_signed` | bool | Use a self-signed certificate for TLS | No | `False` |
| `tls_domain` | str | The domain name used for TLS certificate validation | No | `"localhost"` |
| `tls_cert_path` | `Path\|None` | The path to the TLS certificate | No | `None` |
| `tls_key_path` | `Path\|None` | The path to the TLS private key | No | `None` |
| `discoverable` | bool | If `True`, allows clients to find the server on the local network through multicast discovery | No | `False` |
| `multicast_group` | str | The multicast address used for server discovery | No | `"239.255.0.1"` |
| `multicast_port` | int | The multicast port number used for server discovery | No | 65434 |
| `persistence_mode` | `SaveFormat\|None` | The persistence mode of the server data | No | `None` |
| `persistence_path` | `Path\|None` | The path to the server data persistence file | No | `None` |
| `persistence_periodicity` | `int` | The interval in seconds between periodic persistence saves (0 to disable periodic saving) | No | 0 |
| `garbage_collection_periodicity` | `int` | The interval in seconds between each deletion of "Player" objects that are only associated with finished games, or that are associated with no game and no longer reachable (see the "Automatic cleanup" paragraph) | No | 900 |

Additional information:
- The `host` address is the IP address or network name on which the server listens for incoming connections. If the server must not be reachable from the network (for a local server used only on the same machine as the clients), set it to `127.0.0.1` or `localhost`. Conversely, if the server must be reachable from the network on **all** of its network interfaces, set it to `0.0.0.0` (the default value). Finally, if the server must only be reachable through a specific network interface, set it to the IP address of that interface (useful to deliberately limit the exposure of the server).
- **Choice of ports**: a port is an integer between 0 and 65535 that identifies an **application or service** on a machine. Port `0` has a special meaning: it can ask the system to pick a free port automatically. For a server that clients need to find easily, a fixed port is generally used. Moreover, not all ports are equivalent:

| Range | Name | Usage |
|---:|---|---|
| `0` to `1023` | Well-known ports | Standard services: HTTP, HTTPS, SSH… |
| `1024` to `49151` | Registered ports | Known applications or specific services |
| `49152` to `65535` | Dynamic/ephemeral ports | Often used temporarily by clients |

  - `port` parameter: the TCP port on which the server listens for client connections and messages. It defaults to 65432 if no port is specified when the server is instantiated. A different port can be specified if needed; in that case, it is advisable to stay within the 49152 to 65535 range. In some special cases (for example, when it is difficult to find a free port), the port can be set to 0. In that case, however, network discovery must be enabled, otherwise clients will be unable to connect, since network discovery is the only way to find out which port the machine dynamically allocates to the server.
  - `unencrypted_port` parameter: the TCP port on which the server listens for unencrypted connections. It defaults to `None`, meaning that the server does not offer unencrypted connections. If this parameter is set to a value other than `None`, it must be an integer that is a valid TCP port number and differs from `port`. In that case, this port gives access to the server without TLS, even if `use_tls=True`.
  - `multicast_port` parameter: the UDP port on which the server listens for multicast messages. It defaults to 65434 if no port is specified when the server is instantiated. A different port can be specified if needed; in that case, it is advisable to stay within the 49152 to 65535 range. The port **must not** be 0, otherwise the client would be unable to know the **actual** port dynamically allocated by the server's operating system.
- **Securing communications**: the server can be configured to use TLS to secure communications between the server and clients. To do so, the server must be instantiated with `use_tls=True`. In that case, either the server generates and uses a self-signed certificate (if `tls_self_signed=True`), or the paths to the TLS certificate (`tls_cert_path`) and the TLS private key (`tls_key_path`) must be provided. If either one is missing, an exception is raised and the server is not instantiated. The TLS certificate can be provided either as a "Full Chain" file (i.e. containing the domain certificate and the intermediate certificates), or as the "cert" file only, in which case a matching "chain" file must exist in the same directory (for example `cert.pem` and `chain.pem`, or `ECC-cert.pem` and `ECC-chain.pem`). Furthermore, if `unencrypted_port` is not `None`, is a valid TCP port number, and differs from `port`, then this port gives access to the server without TLS, even if `use_tls=True`. Finally, if `password` is set to a value other than `None`, this password **must** be used to access the server, on both the secure and the unencrypted ports. See the Commands section for details on how to use the password.
- **Network discovery**: a client can search for available servers on the local network. To allow this, the server must be instantiated with `discoverable=True`. It works as follows:
  1. A server listens on the multicast address `multicast_group` and the UDP port `multicast_port`.
  2. A client sends a discovery message to this multicast address. See the [Client-server exchange protocol](PROTOCOLE.md) for a description of the protocol used.
  3. All servers subscribed to the multicast group receive the message.
  4. On receiving this message, each server checks that the received data is as expected and replies directly to the client over UDP unicast. See the [Client-server exchange protocol](PROTOCOLE.md) for a description of the protocol used.
- **Persistence**: Persistence allows the server data to be saved to disk and restored when the server restarts. By default, persistence is disabled (parameter `persistence_mode=None`). When persistence is enabled, the server data is saved to a file defined by the `persistence_path` parameter. The file is saved periodically if `persistence_periodicity > 0`, every time the server stops, and is restored when the server restarts. It can also be saved or reloaded on demand (see the **administrator** level commands in the [Client-server exchange protocol](PROTOCOLE.md)). Two persistence modes are available:
  - `persistence_mode=SaveFormat.JSON`: saves the server data to a JSON file. By default (if `persistence_path=None`), the file is `Path("data/server_data.json")`. The file (as well as its parent directories) is created automatically if it does not already exist.
  - `persistence_mode=SaveFormat.SQLITE`: saves the server data to an SQLite database. By default (if `persistence_path=None`), the file is `Path("data/server_data.db")`. The database (as well as its parent directories) is created automatically if it does not already exist.
- **Automatic cleanup**: The server periodically cleans up `Player` objects that are only associated with finished games. `Player` objects associated with no game (case of newly created objects waiting to be assigned to a game) are not affected by this cleanup, as long as they remain attached to an open session or listed in the `players_id` attribute of a user. However, a `Player` object associated with no game that is no longer reachable (for example the player of an unauthenticated client whose session has been closed) is deleted. The frequency of this cleanup is defined by the `garbage_collection_periodicity` parameter (in seconds).

The `GameServer` class has the following methods:
- `start`: Starts the server in asynchronous mode.
  - Description: Starts the server in asynchronous mode, so that connections and client requests are handled concurrently. This method must be called to start the server and set up the required network listeners. If persistence is enabled and the specified file exists and is compatible with the chosen save format, its data is loaded into memory and used. If the file does not exist, it is created and will receive the data later. If there is no administrator account (even after any data has been loaded), the server creates an `admin` administrator account with the password `admin`. It is of course **very strongly** recommended to change this password or, better, to create a new administrator account and delete this one as soon as possible.
  - Parameters: none
  - Return value: none
- `stop`: Stops the server.
  - Description: Stops the server, attempting to close connections cleanly and to save the data if persistence is enabled.
  - Parameters: none
  - Return value: none
- `restart`: Restarts the server.
  - Description: Restarts the server by closing connections cleanly, then saving and reloading the data if persistence is enabled. Equivalent to `stop` followed by `start`.
  - Parameters: none
  - Return value: none
- `save_persistence`: Triggers an immediate persistence save.
  - Description: Immediately saves the persistent server data to the configured storage. This method has no effect if persistence is not enabled.
  - Parameters: none
  - Return value: none

### Contents of the src/multiplayer/client.py file

This file contains the logic for managing multiplayer clients.

#### Class GameClient
The `GameClient` class is responsible for connecting to and communicating with a `GameServer`. It can discover servers on the network, connect to them with or without encryption, authenticate, and exchange messages (requests, responses, and notifications) according to the defined protocol.

##### Parameters

The `GameClient` class is instantiated with the following parameters:

| Name | Type | Description | Mandatory | Default |
|---|---|---|---|---|
| `host` | str | The IPv4 address or hostname of the server | No | `"127.0.0.1"` |
| `port` | int | The TCP port number of the server | No | 65432 |
| `use_tls` | bool | Use the TLS protocol for secure communication | No | `False` |
| `tls_ca_path` | `Path\|None` | The path to the certificate authority certificate (or to the server's self-signed certificate) used for TLS validation. If `None`, the system's trusted certificates are used. | No | `None` |

##### Attributes

The class has the following attributes:

| Name | Type | Description | Editable | Implementation details |
|---|---|---|---|---|
| `host` | str | The IPv4 address or hostname of the server | Yes | - |
| `port` | int | The TCP port number of the server | Yes | - |
| `tls_ca_path` | `Path\|None` | The path to the TLS validation certificate. If `None`, the system certificates are used. | No | - |
| `is_connected` | bool | Indicates whether the client is currently connected to the server | No | - |
| `session_user` | `User\|None` | The user associated with the current session | No | Automatically updated when the user authenticates. |

##### Methods

The `GameClient` class has the following methods:

- `discover` (class method): Searches for available servers on the local network.
  - Description: Sends a multicast discovery message over UDP and collects the responses from active servers.
  - Parameters:
    - `timeout` (float): Maximum time to wait for responses (in seconds). Optional. Default: 2.0.
    - `multicast_group` (str): The multicast address to use. Optional. Default: `"239.255.0.1"`.
    - `multicast_port` (int): The multicast port to use. Optional. Default: 65434.
  - Return value: A list of dictionaries, each containing the information of a discovered server (name, host, port, etc.).
- `connect`: Opens the TCP connection to the server.
  - Description: Attempts to open a connection to the server using the `host`, `port` and `use_tls` parameters (as well as `tls_ca_path` if provided; otherwise, the system root certificates are used).
  - Parameters: None.
  - Return value: None.
  - Exceptions raised:
    - `ConnectionError`: if the connection fails.
- `disconnect`: Closes the connection to the server.
  - Description: Cleanly closes the current TCP connection.
  - Parameters: None.
  - Return value: None.
- `login`: Authenticates with the server.
  - Description: Sends an authentication request with the provided credentials. If successful, the client retrieves the user's information.
  - Parameters:
    - `username` (str): The username. Mandatory.
    - `password` (str): The password. Mandatory.
  - Return value: The `User` instance corresponding to the authenticated user.
  - Exceptions raised:
    - `PasswordError`: if the password is incorrect.
    - `UserNotFoundError`: if the user does not exist.
- `send_request`: Sends a request to the server and waits for its response.
  - Description: Low-level method for sending any command supported by the protocol and receiving the corresponding response.
  - Parameters:
    - `command` (str): The name of the command/action to execute. Mandatory.
    - `**kwargs`: The arguments of the command.
  - Return value: A dictionary containing the data of the server response.
  - Exceptions raised:
    - `MultiplayerError` (or a subclass): if the server returns an error.
- `on_notification`: Registers a callback function to handle notifications.
  - Description: Associates a function with a specific notification type or with all notifications.
  - Parameters:
    - `notification_type` (str|None): The notification type to listen for (e.g. `"GAME_EVENT"`). If `None`, the callback receives all notifications.
    - `callback` (callable): The function to call, which takes the notification dictionary as its argument.
  - Return value: None.
- `save_persistence`: Requests an immediate persistence save from the server.
  - Description: Sends a `SERVER_PERSISTENCE_SAVE` request to the server to trigger an immediate save. Requires the protocol's `ADMIN` administrator access level, i.e. a user account with the `UserRole.SERVER_ADMIN` role.
  - Parameters: None.
  - Return value: A dictionary containing the data of the server response.
  - Exceptions raised:
    - `MultiplayerError` (or a subclass): if the server returns an error.
    - `ConnectionError`: if the client is not connected.

Additional information:
- **Notification handling**: The client must be able to receive and process notifications sent spontaneously by the server. The implementation relies on registering callbacks through the `on_notification` method. When a notification arrives, the client looks up the callbacks registered for that type (as well as the global callbacks) and runs them asynchronously or sequentially, depending on the chosen architecture.

  **Exhaustive list of notification types (taken from the protocol):**
  - `SERVER_SHUTDOWN`: Warns clients that the server is about to shut down.
  - `GROUP_GAME_ADDED`: Informs clients that a game has just been added to a group.
  - `GROUP_GAME_REMOVED`: Informs clients that a game has just been removed from a group.
  - `GROUP_GAME_UPDATED`: Informs clients that a game in a group has changed state or visible properties.
  - `GAME_EVENT`: Notifies participants of an action performed by one of them or by the server.
  - `GAME_STATE_CHANGED`: Informs clients that the global or custom state of the game has changed.
  - `GAME_TURN_CHANGED`: Notifies connected clients that a new turn has started and identifies the active player.

  **Example:**
  ```python
  # Game event handling
  def my_game_handler(notification):
      payload = notification["payload"]
      print(f"Action {payload['action_type']} received from {payload['player_id']}")

  client.on_notification("GAME_EVENT", my_game_handler)

  # Global notification handling (log)
  client.on_notification(None, lambda n: logging.info(f"Notification received: {n['type']}"))
  ```
- **Serialization**: The client must support the JSON and MessagePack formats for exchanges, as required by the protocol.

## Workflows

GitHub workflows are stored in `.github/workflows` and are used to automate development and deployment tasks. The files are written in YAML and follow a standardized format to ensure consistency and readability.

The workflows to implement are the following:
- `lint.yml`: Automates code quality checks and compliance with standards. It runs automatically when a commit is pushed to the main branch (including when a branch is merged into the main branch). It can also be run manually on any branch.
- `test.yml`: Automates unit and functional tests. Runs all unit tests on Windows, Linux, and macOS. It runs automatically when a commit is pushed to the main branch (including when a branch is merged into the main branch). It can also be run manually on any branch.
- `release.yml`: Automates the creation of releases and their deployment to distribution platforms. Runs automatically when a tag of the form `vX.Y.Z` is created. It can also be run manually, in which case the version to deploy is chosen by the user.
- `pypi.yml`: Automates the deployment of a version to PyPI. Runs only manually, with the version to deploy chosen by the user.

## Scripts

Scripts are stored in the `scripts` directory:

- `check_project.py`: performs the following actions:
  - Checks the changes made to the code relative to the main branch. If there are no changes, or if the only changes concern documentation files, the script stops without running any checks.
  - Checks whether `uv` is installed and installs it if needed.
  - In an isolated Python virtual environment:
    - Installs all the dependencies needed for development.
    - Runs the code quality and standards compliance checks.
    - Runs the unit and functional tests.
  - The `--fix` option can be used to automatically fix style and compliance errors.

- `local_game.py`: runs a visible local demonstration of a multiplayer game:
  - Opens a console window for the local server and one window for each player.
  - Takes the number of players as an argument; the default is `2`.
  - Each player connects to the server, joins the same game, and simulates several exchanges and turns at a human-readable pace.
  - Ends the game normally, then stops the server cleanly.
  - Usage:
    - `uv run python scripts/local_game.py`: starts a game with two players.
    - `uv run python scripts/local_game.py 4`: starts a game with four players.
