# Instructions for developing multiplayer version 2

This document provides instructions for developing version 2 of the multiplayer module. It describes the coding conventions, dependencies, and technical specifications necessary to ensure compatibility and consistency between the different modules of the package.

## General rules

## Comment and docstring conventions

- All comments must be written in English.
- Modules, classes, and functions must have English docstrings and follow the PEP 257 convention and Google style.

### Naming conventions

- Names of variables, functions, and methods must be descriptive (in English) and use the snake_case convention.
- Class names must be in CamelCase.
- Constant names must be in UPPER CASE.
- Module names must be in snake_case.
- An underscore () must precede private method names_.
- Two underscores () must precede private class variables__.
- Variables must be declared first in each block of code.

### Exception Conventions
- Limit the number of custom exception classes to a minimum.
- Group related errors into a separate module for easier maintenance.
- Name exceptions in English and use the PascalCase convention with the suffix "Error".
- Inherit the Exception class (or an appropriate subclass) from the builtins module. Do not derive directly from BaseException.
- Chain exceptions with `raise ... from ...` to preserve the original cause.
- Structure the code with `try/except/else/finally` for efficient error and resource management, as far as possible according to the following scheme:
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
    # Code to execute regardless of whether exceptions occurred (file and connection cleanup, ...)
```
- Error messages must be exclusively in English.
- Error messages should be explicit and, if relevant, should also provide the input values that caused the error.
- Exceptions must be logged with the logging module: logging.exception("Message").
- In the docstring, exceptions must be mentioned (`:raises:` or `Raises:`). The conditions that trigger them must be described.
- Use of `assert` should be reserved for internal invariant checks, not for validating user input.
- Do not use exceptions for normal flow control (example: exiting a loop), because the exception mechanism is more expensive than classic control structures.

### Other conventions

- All "ID" properties must be alphanumeric strings and must be uniquely generated at instantiation, using the uuid module's `uuid.uuid4()` function. They must be read-only.
- All coded objects must go through a set of unit tests to ensure they work properly. These tests must cover all possible use cases of the objects and must be automated. They should be able to be run with `pytest`.
- The `pyproject.toml` file must conform to the TOML format specification and instructions described [here](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) and must contain the necessary information for managing the project with `uv`.
- Documentation files must be written in Markdown and must be updated regularly with changes to the code.

## Code organization

Generally speaking, code files should be structured in a way that makes the code easy to understand and maintain. Files should be divided into logical sections and each section should be well documented.

This chapter is organized into subchapters, each named after a source file to be implemented as a module of the multiplayer package.

Unless otherwise specifically indicated, the objects to be implemented (functions, classes, etc.) are described according to the expected effect from the perspective of the person using this item. The developer is free to add any objects or intermediate files that he considers necessary to achieve this final effect.

The files are organized according to the format of a Python project managed by `uv`, which uses the standard Python project structure (with the `pyproject.toml` file), adding some specificities (such as the `uv.lock` file).

So, the source files are in the `src/multiplayer` directory, the unit tests in `tests/`, the distribution files in `dist/`, and some more complex test scripts in `scripts/`. `pyproject.toml`, `uv.lock`, `README.md`, as well as all other documentation and configuration files are at the root of the project.

### Contents of the src/multiplayer/__init__.py file

This file contains the imports necessary for the multiplayer package to work. In general, it indicates all the constant elements (constants, enumerations) that the multiplayer modules use.
In particular, we find the following elements:

#### `PlayerRole` (Enum)
An enumeration for the role of a player account.

* `PlayerRole.PLAYER`: A standard player who can join and participate in games.
* `PlayerRole.GROUP_ADMIN`: A player who can manage games within the groups assigned to him. This role includes all the permissions of a `PLAYER`.
* `PlayerRole.SERVER_ADMIN`: A player with full administrative access to the server. This role includes the role of `GROUP_ADMIN`, which itself can also play the role of `PLAYER`.

#### `GameState` (Enum)
An enumeration representing the current status of a game.

* `GameState.PENDING`: The game has been created but has not yet started. This state is dedicated to waiting for players. Players can join or leave the game.
* `GameState.PAUSING`: The game is currently paused. This state is used when a game that was in progress is temporarily suspended.
* `GameState.IN_PROGRESS`: The game is currently active.
* `GameState.FINISHED`: The game is over. No more moves can be played and the results are final.
#### `ParameterFamily` (Enum)
An enumeration representing families of optional player and game customization parameters.

* `ParameterFamily.STATIC`: Static parameters that change little or nothing during the game.
* `ParameterFamily.DYNAMIC`: Dynamic parameters that can be changed often during the game.

#### `SaveFormat` (Enum)
An enumeration representing the storage formats supported by a backup file.

* `SaveFormat.JSON`: Save in a single JSON document.
* `SaveFormat.SQLITE`: Save in an SQLite database.

### Contents of the src/multiplayer/exceptions.py file

This file contains the custom exception definitions used in this module. It defines the classes and functions needed for game-specific error handling.
In particular, we find the following classes:

#### Class `MultiplayerError`
This class is the base class for all exceptions related to the `multiplayer` module. It serves as a starting point for the custom exception hierarchy.

#### Class `UserAlreadyExistsError`
This class is derived from `MultiplayerError` and is used to report an attempt to create a user account with an already existing name.

#### Class `SaveError`
This class is derived from `MultiplayerError` and is used to report that a save file is incompatible, corrupted, or cannot be read or written. It is also raised when an unknown save format is requested, or an unsupported class is saved or loaded.

#### Class `GroupNotFoundError`
This class is derived from `MultiplayerError` and is used to report an attempt to use a group (or group ID) that does not exist. This exception returns the wrong ID in its message.

#### Class `PlayerNotFoundError`
This class is derived from `MultiplayerError` and is used to report an attempt to use a player (or player ID) that does not exist. This exception returns the wrong ID in its message (if provided).

#### Class `PlayerNotFoundInGameError`
This class is derived from `PlayerNotFoundError` and is used to signal an attempt to remove a player **from a game where he is not present**. This exception returns the wrong player ID in its message (if provided).

#### Class `PasswordError`:
This class is derived from `MultiplayerError` and is used to report an attempt to use an incorrect password.

#### Class `GameIsFullError`:
This class is derived from `MultiplayerError` and is used to report an attempt to add a player or observer to a game that is already full.

#### Class `GameAlreadyStartedError`:
This class is derived from `MultiplayerError` and is used to signal an attempt to start a game that is already in progress.

#### Class `GameIsFinishedError`:
This class is derived from `MultiplayerError` and is used to report an attempt to modify a game that has ended.

#### Class `GameNotStartedError`:
This class is derived from `MultiplayerError` and is used to signal an attempt to pause, restart, stop, or progress the game (moving to the next round for example) of a game that has not yet started.

#### Class `GameAlreadyPausedError`:
This class is derived from `MultiplayerError` and is used to signal an attempt to pause a game that is already paused.

#### Class `GameNotPausedError`:
This class is derived from `MultiplayerError` and is used to signal an attempt to resume a game that is not paused.

#### Class `GameNotByTurnError`:
This class is derived from `MultiplayerError` and is used to signal an attempt at a specific turn-based action in a game that is not handled turn-based.

#### Class `GameNotFoundError`:
This class is derived from `MultiplayerError` and is used to signal an attempt to search for a game that does not exist. This exception returns in its message the ID of the erroneous part (if provided).

#### Class `GameNotFoundInGroupError`:
This class is derived from `GameNotFoundError` and is used to report an attempt to remove a part from a group that does not contain that part. This exception returns in its message the ID of the erroneous part (if provided).

### Contents of the src/multiplayer/game.py file

This file contains the main game management logic. It defines the classes and functions necessary for the creation, management, and resolution of games.
In particular, we find the following classes:

#### Class `Player`
This class represents a player in the context of the game. It is the entity that actually participates in the games. While a `User` account manages access and permissions, the `Player` object carries game-related attributes (name, score, state, etc.). A client can have several `Player` objects during its session (for example to manage several participants on the same computer). One of them is designated as the default player. Every authenticated user has a `Player` object of their own, which they find at each connection and which then becomes their default player. An unauthenticated client may also have one or more `Player` objects created for the duration of its session.

It is instantaneous with the following parameters:

| Name | Type | Description | Mandatory | Default |
|------------|----------|--------------|-------------|---------|
| `name` | str | The player's name.  | Yes | - |
| `**kwargs` | variable | Optional settings to customize the player. Each parameter must be in the form of a tuple `(family, initial_value)` of which `family` is a `ParameterFamily` object which specifies the static or dynamic nature of the parameter, and `initial_value` its initial value. The choice of family is made at the convenience of the user, to help him classify the information, but has no impact on internal processing (families are all treated in the same way). | No | - |

It has the following attributes:

| Name | Type | Description | Editable | Implementation accuracy |
|-----------------|------|-------------|------------|----------------------------|
| `ID` | str | The unique player ID.  | No | Automatically initializes with the value of `uuid.uuid4()`.  |
| `name` | str | The player's name. | Yes | Automatically initializes with the name provided during player creation.|
| `static_state` | dict | Personalized player attributes, the purpose of which is to store information that does not change or changes little during the game.  | Yes | Automatically initializes with parameters specified as belonging to the `ParameterFamily.STATIC` family, but can subsequently be supplemented with any other parameters of the user's choice. For example, if `Player` is instantiated with `Player(name="My name", color=(ParameterFamily.STATIC, "white"), score=(ParameterFamily.DYNAMIC, 0))`, then `static_state` is equal to `{"color":"white"}`. |
| `dynamic_state` | dict | Custom player attributes, whose purpose is to store information that can be modified often during the game. | Yes | Automatically initializes with parameters specified as belonging to the `ParameterFamily.DYNAMIC` family, but can subsequently be supplemented with any other parameters of the user's choice. For example, if `Player` is instantiated with `Player(name="My name", color=(ParameterFamily.STATIC, "white"), score=(ParameterFamily.DYNAMIC, 0))`, then `dynamic_state` is equal to `{"score":0}`.    |

#### Class `User`
This class represents a user account. This allows you to access various capabilities depending on your access level (authentication) and to keep a `Player` object associated with it. A user is an entity distinct from the player: the user manages identifiers and rights, while the player manages presence in the game.

It is instantaneous with the following parameters:

| Name | Type | Description | Mandatory | Default |
|------------|------|-----------------------|-------------|--------------|
| `username` | str | The account username. | Yes | - |
| `password` | str | The account password.      | Yes | - |
| `email` | str | The account email address.     | No | `""` (empty string) |


If a `User` object is instantiated with a `username` already used in an existing instance of `User`, a `UserAlreadyExistsError` exception is thrown and the instantiation fails.

The class has the following attributes:

| Name | Type | Description | Editable | Implementation accuracy |
|-------------|--------------|--------------|------------|----------------------------|
| `ID` | str | The unique identifier of the user account. | No | Automatically initializes with the value of `uuid.uuid4()`.|
| `username` | str | The account username.  | No | -|
| `hash` | str | The account password hash.| No | The hash is automatically generated from `password` with `bcrypt`.|
| `email` | str | The account email address. | Yes | -|
| `role` | `PlayerRole` | The role of the account (ie: its permission level).  | Yes | - |
| `groups_id` | List[str] | The identifiers of the groups for which the account is administrator. Only useful if `role == PlayerRole.GROUP_ADMIN`. A `GroupNotFoundError` exception is raised if one of the identifiers does not correspond to an existing group. In this case the value of `groups_id` is not updated. | No (but mutable) | Initialized with an empty list, this attribute can be completed and modified using `list` methods such as `append`, `extend`, `pop`, ... As it is a read-only attribute, re-assignment is prohibited. |
| `player` | `Player` | The player associated with the account. The `Player` object is instantiated with the `name` parameter equal to the `username` attribute. Its attributes can then be modified (including `name`, either directly via the `Player` object, or via an update request for the `User` account). Upon authentication, this player is automatically added to the client's session and becomes its default player. | No (but mutable) | The instantiated `Player` object is retained for the entire lifetime of the `User` instance that contains it, and is only deleted when the `User` instance is deleted. |

The `User` class has the following methods:

- `change_password`: allows you to change the user account password. The `hash` parameter of the current instance is updated with the new password via `bcrypt`
    - Settings:
      - `new_password` (str): the new password to use for the user account. Mandatory.
    - Return value:
      - None.


#### `Game` class
This class represents a game part. It is instantiated with the following parameters:

| Name | Type | Description | Mandatory | Default |
|---------------------|--------|-------------|-------------|---------|
| `name` | str\|`None` | The name of the game.  | No | `None` |
| `max_players` | int\|`None` | Maximum number of players. If `None`, then there is no limit. If 0 or negative, then no players are allowed.| No | `None` |
| `max_observers` | int\|`None` | Maximum number of observers. If `None`, then there is no limit. If 0 or negative, then no observers are allowed.  | No | `None` |
| `password` | str\|`None` | Game password. If `None`, then the game is public (no password is needed to access the game). | No | `None`|
| `observer_password` | str\|`None` | Observers password. If `None`, then observers use the game password, defined by the `password` parameter. If this is also `None`, then observers can access the game without a password. | No | `None` |
| `turn_based` | bool | `True` if the game is turn-based, `False` for simultaneous play. | No | `False` |
| `**kwargs` | variable | Optional settings to customize the game. Each parameter must be in the form of a tuple `(family, initial_value)` of which `family` is a `ParameterFamily` object which specifies the static or dynamic nature of the parameter, and `initial_value` its initial value. The choice of family is made at the convenience of the user, to help him classify the information, but has no impact on internal processing (families are all treated in the same way). | No | - |

The class has the following attributes:

| Name | Type | Description | Editable | Implementation accuracy |
|-----------------|-----------------|-------------|------------|----------------------------|
| `ID` | str | The unique identifier of the game. | No | Automatically initializes with the value of `uuid.uuid4()`.|
| `name` | str | The name of the game. | Yes | - |
| `hash` | str\|`None` | The hash of the game password. `None` if the game is public (without password).| No | The hash is automatically generated from `password` with `bcrypt`. |
| `observer_hash` | str\|`None` | The hash of the observer's password. `None` if no observation password is set. | No | The hash is automatically generated from `observer_password` with `bcrypt`.|
| `turn_based` | bool | `True` if the game is turn-based, `False` for simultaneous play. | No | - |
| `players` | Tuple[`Player`] | Tuple (non-mutable list) of `Player` instances representing the players of the game. The order in which players are presented corresponds to the order in which players take their turns in a turn-based game. Some games allow changing order during the game. Specific methods are therefore available to achieve these changes. Do not attempt to change the order directly in this attribute. | No | The corresponding internal variable (`_players`) is a list which is transformed into a tuple for its public display through the `players` attribute. |
| `observers` | Tuple[`Player`] | Tuple (non-mutable list) of `Player` instances representing the observers of the game. | No | The corresponding internal variable (`_observers`) is a list which is transformed into a tuple for its public display through the `observers` attribute. |
| `current_player`| `Player` | `Player` instance representing the player whose turn is in progress. Only makes sense for turn-based games. | No | - |
| `game_state` | `GameState` | Current state of the game. | No | - |
| `static_state` | dict | Custom attributes of the game, the purpose of which is to store information that does not change or changes little during the game.  | Yes | Automatically initializes with parameters specified as belonging to the `ParameterFamily.STATIC` family, but can subsequently be supplemented with any other parameters of the user's choice. For example, if `Game` is instantiated with `Game([...], style=(ParameterFamily.STATIC, "blitz"), score=(ParameterFamily.DYNAMIC, "0-0"))`, then `static_state` is equal to `{"style":"blitz"}`. |
| `dynamic_state` | dict | Custom attributes of the game, whose purpose is to store information that can be modified often during the game. | Yes | Automatically initializes with parameters specified as belonging to the `ParameterFamily.DYNAMIC` family, but can subsequently be supplemented with any other parameters of the user's choice. For example, if `Game` is instantiated with `Game([...], style=(ParameterFamily.STATIC, "blitz"), score=(ParameterFamily.DYNAMIC, "0-0"))`, then `dynamic_state` is equal to `{"score":"0-0"}`.    |

The `Game` class has the following methods:

- `change_password`: allows you to change the password of the game. The `hash` parameter of the current instance is updated with the new password via `bcrypt`
    - Settings:
      - `new_password` (str): the new password to use for the user account. Mandatory.
    - Return value:
      - None.
- `join_game_as_player`: allows you to join a game as a player.
- Description: This method allows a player to join a game by specifying their ID or `Player` object and optionally a password if the game is private. It throws an exception if the player does not exist or if the password is incorrect.
  - Implementation precision: If successful, the method adds the `Player` object to the `_players` list of the current instance.
  - Settings:
    - `player` (`Player`|str): the player who joins the game. This is either the `Player` object corresponding to the player, or a character string corresponding to his ID. Mandatory.
    - `password` (str\|`None`): password to join the game. If the game is public, then you must indicate `None`. Optional. Default: `None`.
  - Exceptions thrown:
    - `PlayerNotFoundError`: raised if the specified player does not exist.
    - `PasswordError`: raised if the password is incorrect.
    - `GameIsFullError`: raised if the maximum number of players is reached, and adding a new player is impossible.
  - Return value: None.

- `remove_player`: allows you to remove a player from the game.
  - Description: This method allows you to remove a player from the game by specifying their ID or `Player` object. It throws an exception if the player is not found in the game.
  - Implementation precision: If successful, the method removes the `Player` object from the `_players` list of the current instance.
  - Settings:
    - `player` (`Player`|str): the player to remove from the game. This is either the `Player` object corresponding to the player, or a character string corresponding to his ID. Mandatory.
  - Exceptions thrown:
    - `PlayerNotFoundInGameError`: raised if the specified player is not found in the game.
  - Return value: None.

- `join_game_as_observer`: allows you to join a game as an observer.
  - Description: This method allows a player to join a game as an observer. It throws an exception if the game is private and the password is incorrect.
  - Implementation precision: If successful, the method adds the `Player` object to the `_observers` list of the current instance.
  - Settings:
    - `player` (`Player`|str): the player who joins the game as an observer. This is either the `Player` object corresponding to the player, or a character string corresponding to his ID. Mandatory.
    - `password` (str\|`None`): password to join the game as an observer. If the game observation is public, then it must be indicated `None`. Optional. Default: `None`.
  - Exceptions thrown:
    - `PlayerNotFoundError`: raised if the specified player does not exist.
    - `PasswordError`: raised if the game is private and the password is incorrect.
    - `GameIsFullError`: raised if the maximum number of observers is reached, and adding a new observer is impossible.
  - Return value: None.

- `remove_observer`: allows you to remove an observer from a game.
  - Description: This method allows an observer to leave a game. It throws an exception if the specified player is not found in the game.
  - Implementation precision: If successful, the method removes the `Player` object from the `_observers` list of the current instance.
  - Settings:
    - `player` (`Player`|str): the player who leaves the game as an observer. This is either the `Player` object corresponding to the player, or a character string corresponding to his ID. Mandatory.
  - Exceptions thrown:
    - `PlayerNotFoundInGameError`: raised if the specified player is not found in the game.
  - Return value: None.

- `start`: allows you to start a game.
  - Description: This method allows you to start a game. It throws an exception if the game is already in progress or if it has ended. If successful, the method sets the `game_state` attribute to the value `GameState.IN_PROGRESS`.
  - Implementation clarification: The `GameState.PAUSING` status is also considered as a game in progress.
  - Settings:
    - None.
  - Exceptions thrown:
    - `GameAlreadyStartedError`: raised if the game is already in progress.
    - `GameIsFinishedError`: raised if the game is over.
  - Return value: None.

- `pause`: allows you to pause a game.
- Description: This method allows you to pause a game. It throws an exception if the game is not in progress or if it is already paused.
  - Implementation precision: If successful, the method sets the `game_state` attribute to the value `GameState.PAUSING`.
  - Settings:
    - None.
  - Exceptions thrown:
    - `GameNotStartedError`: raised if the game is not in progress.
    - `GameAlreadyPausedError`: raised if the game is already paused.
  - Return value: None.
  
- `resume`: allows you to resume a paused game.
  - Description: This method allows you to resume a paused game. It throws an exception if the game is not paused.
  - Implementation precision: If successful, the method sets the `game_state` attribute to the value `GameState.IN_PROGRESS`.
  - Settings:
    - None.
  - Exceptions thrown:
    - `GameNotPausedError`: raised if the game is not paused.
  - Return value: None.

- `stop`: allows you to end a game.
  - Description: This method allows you to end a game. It throws an exception if the game is not in progress.
  - Implementation precision: If successful, the method sets the `game_state` attribute to the value `GameState.FINISHED`.
  - Settings:
    - None.
  - Exceptions thrown:
    - `GameNotStartedError`: raised if the game is not in progress.
  - Return value: None.

- `next_turn`: allows you to move on to the next turn.
  - Description: In the case of a turn-based game, this method allows you to move on to the next turn. It throws an exception if the game is not in progress or if it has ended. If successful, the method passes the `current_player` attribute to the next player.
  - Settings:
    - None.
  - Exceptions thrown:
    - `GameNotStartedError`: raised if the game is not in progress.
    - `GameIsFinishedError`: raised if the game is over.
    - `GameNotTurnBasedError`: raised if the game is not managed turn-based.
  - Return value: None.

- `reverse_order`: allows you to reverse the order of players in a turn-based game.
  - Description: This method allows you to reverse the order of players in a game. This order inversion can be done in any state of the game other than `GameState.FINISHED`. It throws an exception if the game is over. If successful, the method reverses the order of players in the `players` attribute.
  - Implementation precision: If successful, the reverse method puts the order in the internal `_players` list.
  - Settings:
    - None.
  - Exceptions thrown:
    - `GameIsFinishedError`: raised if the game is over.
    - `GameNotTurnBasedError`: raised if the game is not managed turn-based.
  - Return value: None.

- `set_player_rank`: allows you to specify the rank of a player in a turn-based game.
  - Description: This method allows you to specify a player's rank in a turn-based game. The other players keep the same order, their rank is incremented or decremented to fill the place that the player leaves, and to leave him the place he joins. This change of rank can be carried out in any state of the game other than `GameState.FINISHED`. It throws an exception if the game is over. If successful, the rank modification appears in the `players` attribute.
  - Implementation precision: If successful, the method actually modifies the internal `_players` list.
  - Settings:
    - `player` (`Player`|str): the player whose rank is modified. This is either the `Player` object corresponding to the player, or a character string corresponding to his ID. Mandatory.
    - `rank` (int): the new rank of the player. Mandatory.
  - Exceptions thrown:
    - `IndexError`: raised if the specified rank is invalid.
    - `GameIsFinishedError`: raised if the game is over.
    - `GameNotTurnBasedError`: raised if the game is not managed turn-based.
    - `PlayerNotFoundInGameError`: raised if the specified player is not found in the game.
  - Return value: None.

#### Class `GameGroup`
This class allows you to group several parts into a single object. It allows you to manage the parts in parallel and manipulate them as a group. It is instantaneous with the following parameters:

| Name | Type | Description | Mandatory | Default |
|---------------------|--------|-------------|-------------|---------|
| `name` | str | The name of the party group.| Yes | - |
| `**kwargs` | variable | Optional settings to customize the group. | No | - |

The class has the following attributes:

| Name | Type | Description | Editable | Implementation accuracy |
|-----------------|-----------------|-------------|------------|----------------------------|
| `ID` | str | The unique identifier of the group. | No | Automatically initializes with the value of `uuid.uuid4()`.|
| `name` | str | The name of the group. | Yes | - |
| `games` | Tuple[`Game`] | Tuple (non-mutable list) of `Game` instances representing the parts of the group. | No | The corresponding internal variable (`_games`) is a list which is transformed into a tuple for its public display through the `games` attribute. |
| `parameters` | dict | Group Customization Settings | Yes | Automatically initializes with the parameters specified in `kwargs`, but can later be supplemented with any other parameters of the user's choice. |


The `GameGroup` class has the following methods:

- `add_game`: allows you to add a game to the group. The part is added to the end of the group's parts list. 
  - Description: This method allows you to add a game to the group by specifying its ID or `Game` object and possibly a group administrator password. It throws an exception if the part does not exist or if the password is incorrect. 
  - Implementation precision: If successful, the method adds the `Game` object to the `_games` list of the current instance.
  - Settings:
    - `game` (`Game`|str): the instance of the game to add, or a character string representing the ID of the game to add. Mandatory.
  - Return value:
    - None.
  - Exceptions thrown:
    - `GameNotFoundError`: raised if the specified game does not exist.
- `remove_game`: allows you to remove part of the group. The game is removed from the group's games list.
  - Settings:
    - `game` (`Game`|str): the instance of the game to be removed, or a character string representing the ID of the game to be removed. Mandatory.
  - Implementation precision: If successful, the method removes the `Game` object from the `_games` list of the current instance.
  - Return value:
    - None.
  - Exceptions thrown:
    - `GameNotFoundInGroupError`: raised if the specified game is not present in the group.

### Contents of the src/multiplayer/utils.py file

The package provides utility functions to suggest game and player names based on different categories.


#### Categories for Parties
* **`cities`**: Major cities in the world.
* **`countries`**: Sovereign nations.
* **`rivers`**: Important rivers of the world.
* **`seas_oceans`**: Main bodies of salt water.
* **`planets_moons`**: Celestial bodies in our solar system.

Implementation precision: 
* Categories are stored in simple text files, with one name per line, in the `src/multiplayer/data` directory (one file per category).
*CSV files are supported to allow for more complex structure if needed.
* Names are normalized to avoid duplicates and special characters.

#### Categories for Players
* **`roman_gods`**: Deities from Roman mythology.
* **`greek_gods`**: Deities from ancient Greek mythology.
* **`egyptian_gods`**: Deities from ancient Egyptian mythology.
* **`european_kings`**: Historical European monarchs (male).
* **`european_queens`**: Historical European monarchs (women).

Implementation precision: 
* Categories are stored in simple text files, with one name per line, in the `src/multiplayer/data` directory (one file per category).
*CSV files are supported to allow for more complex structure if necessary.
* Names are normalized to avoid duplicates and special characters.

#### Function `register_name_category(category_name, data, category_type)`
Saves a new custom category for name suggestions.

* **`category_name`** (`str`): The name of the new category.
* **`data`** (`list`, `str` or `Path`): A list of names, or a path to a text/CSV file (one name per line, or first column of the CSV).
* **`category_type`** (`str`): `"game"` or `"player"`.

#### Function `unregister_name_category(category_name)`
Deletes a custom category. Returns `True` on success.

#### Function `get_available_categories(category_type="all")`
Returns a list of available name suggestion categories.

* **`category_type`** (`str`): `"all"`, `"game"`, or `"player"`.

#### Function `suggest_game_name(category=None)`
Suggests a random name for a game. If `category` is `None`, a category linked to the games is chosen randomly.

#### Function `suggest_player_name(category=None)`
Suggest a random name for a player. If `category` is `None`, a category related to players is chosen randomly.

### Contents of the src/multiplayer/save.py file

This file contains the logic for saving and restoring objects instantiated from the `Player`, `User`, `Game` and `GameGroup` classes. It defines the `Save` class, each instance of which represents a save file and makes the link between an in-memory buffer and a persistent file (JSON document or SQLite database).

#### `Save` class
This class allows you to save, update, and restore module objects. Objects are first saved to a buffer in memory, then written to the file only when explicitly calling the `flush` method. It is instantiated with the following parameters:

| Name | Type | Description | Mandatory | Default |
|---------------|---------------------|-------------|-------------|------------------|
| `file_path` | `Path` | The path of the backup file. | Yes | - |
| `save_format` | `SaveFormat`\|str | The backup format. It is either a member of the `SaveFormat` enumeration, or a character string (`"json"` or `"sqlite"`). | Yes | - |

Behavior at instantiation:
* If the file does not exist, it is created with an empty but valid structure.
* If the file already exists, its structure is checked. If it is compatible with the requested format, its content is loaded into the buffer in memory. Otherwise, a `SaveError` exception is thrown.
* If the save format is unknown, a `SaveError` exception is thrown.

The class has the following attributes:

| Name | Type | Description | Editable | Implementation accuracy |
|---------------|---------|-------------|------------|----------------------------|
| `file_path` | `Path` | The path of the backup file. | Yes | Initializes from the `file_path` parameter. |
| `save_format` | `SaveFormat` | The storage format used. | Yes | Initializes from the `save_format` parameter. |

The `Save` class has the following methods:

- `save`: allows you to save or update an individual instance in the in-memory buffer.
  - Description: The object is serialized and stored in the buffer, indexed by its class and ID. If an object of the same class and the same ID already exists, it is replaced. The modification is only persisted in the file when `flush` is called.
  - Settings:
    - `obj` (`Player`|`User`|`Game`|`GameGroup`): the instance to save. Mandatory.
  - Exceptions thrown:
    - `SaveError`: thrown if the object is not an instance of a supported class.
  - Return value: None.

- `load`: allows you to load all instances of a given class.
  - Description: Rebuilds and returns the list of instances of the requested class from the in-memory buffer.
  - Settings:
    - `target` (str\|type): the class to load or its name (`Player`, `User`, `Game` or `GameGroup`). Mandatory.
  - Exceptions thrown:
    - `SaveError`: thrown if the target does not match a supported class.
  - Return value: The list of reconstructed instances of the requested class.

- `reset`: allows you to reset the save file.
  - Description: Flushes the buffer in memory and rewrites the save file with an empty but valid structure.
  - Settings:
    - None.
  - Return value: None.

- `flush`: allows you to actually write the buffer in memory into the save file.
- Description: Persists all the objects in the buffer in the file according to the chosen format. This method must be called to make the backups effective on disk.
  - Settings:
    - None.
  - Exceptions thrown:
    - `SaveError`: raised if the data cannot be written to the file.
  - Return value: None.

### Contents of the src/multiplayer/server.py file

This file contains the logic for managing multiplayer servers.

#### GameServer class
The `GameServer` class is responsible for managing connections and communications with clients in a multiplayer environment. It ensures the coordination of actions and the dissemination of information to connected players.

##### Settings

The `GameServer` class is instantiated with the following parameters:

| Name | Type | Description | Mandatory | Default |
|---------------|---------------------|-------------|-------------|------------------|
| `host` | str | The IPv4 address on which the server listens for connections | No | `"0.0.0.0"` |
| `port` | int | The port number on which the server listens for connections | No | 65432 |
| `unencrypted_port` | int\|`None` | The insecure port number for connections not protected by TLS | No | `None` |
| `password` | str\|`None` | The password to access the server | No | `None` |
| `name` | str | The server name | No | `""` (empty string) |
| `use_tls` | bool | Use TLS v1.3 protocol for secure communication | No | `False` |
| `tls_self_signed` | bool | Use a self-signed certificate for TLS | No | `False` |
| `tls_domain` | str | The domain name used for TLS certificate validation | No | `"localhost"` |
| `tls_cert_path` | `Path\|None` | The path to the TLS certificate | No | `None` |
| `tls_key_path` | `Path\|None` | The path to the TLS private key | No | `None` |
| `discoverable` | bool | If `True`, allow clients to search for the server on the local network through multicast discovery | No | `False` |
| `multicast_group` | str | The multicast address used for server discovery | No | `"239.255.0.1"` |
| `multicast_port` | int | The multicast port number used for server discovery | No | 65434 |
| `persistence_mode` | `SaveFormat\|None` | Server data persistence mode | No | `None` |
| `persistence_path` | `Path\|None` | The path to the server data persistence file | No | `None` |
| `garbage_collection_periodicity` | `int` | The duration in seconds between each deletion of orphaned "Player" objects (associated with a non-existent session) | No | 900 |

Additional information:
- the `host` address designates the IP address or network name on which the server will listen for incoming connections. If you do not want the server to be accessible on the network (case of a local server used only on the same machine as the clients), then you must define `127.0.0.1` or `localhost`. If, on the contrary, you want the server to be accessible from the network on **all** of the server's network interfaces, then you must define `0.0.0.0` (this is the default value). Finally, if you want the server to be accessible only from a specific network interface, then you must indicate the IP address of this interface (useful to voluntarily limit the exposure of the server).
- **Choice of ports**: a port is an integer between 0 and 65535. It is a number which identifies an **application or service** on a machine. Port `0` has a special meaning: it can instruct the system to automatically choose a free port. For a server that clients need to find easily, we generally use a fixed port. Furthermore, not all ports are equivalent:

| Beach | Name | Usage |
|---:|---|---|
| `0` to `1023` | Well-known ports | Standard services: HTTP, HTTPS, SSH… |
| `1024` to `49151` | Registered ports | Known applications or specific services |
| `49152` to `65535` | Dynamic/ephemeral ports | Often used temporarily by customers |
- `port` parameter: this is the TCP port that the server listens for connections and messages from clients. By default it is 65,432 if no port is specified when instantiating the server. The user can specify a different port if necessary, in this case it is advisable to stay in the range 49,152 to 65,535. In certain special cases (difficulty finding a free port for example), it is possible to define the port to 0. However, in this case it is essential to authorize network discovery, otherwise the clients will be unable to connect, network discovery being the only way to know the port that the machine will dynamically allocate to the server.
  - `unencrypted_port` parameter: this is the TCP port that the server listens for unsecured connections. By default it is `None`, which means that the server does not offer an insecure connection. If this parameter is defined and not equal to `None`, then it must be an integer compatible with TCP port numbering, and not equal to `port`. In this case, this port allows access to the server without having to use TLS security, even if `use_tls=True`.
  - `multicast_port` parameter: this is the UDP port that the server listens for multicast messages. By default it is 65,434 if no port is specified when instantiating the server. The user can specify a different port if necessary, in this case it is advisable to stay in the range 49,152 to 65,535. The port **must not** be 0, the client would then be unable to know the **real** port dynamically provided by the server's operating system.
- **securing communications**: the server can be configured to use TLS to secure communications between the server and clients. To do this, the server must be instantiated with `use_tls=True`. In this case, either the server generates and uses a self-signed certificate (if `tls_self_signed=True`), or you must provide the path to the TLS certificate (`tls_cert_path`) and the TLS private key (`tls_key_path`). If either is missing, an exception is thrown and the server is not instantiated. In the case of the TLS certificate, it is possible to provide either a "Full Chain" file (i.e., containing the domain certificate and intermediate certificates), or only the "cert" file, but in this case there must exist a corresponding "chain" file in the same directory (for example `cert.pem` and `chain.pem`, or `ECC-cert.pem` and `ECC-chain.pem`). Furthermore, if `unencrypted_port` is not `None` and is an integer compatible with TCP port numbering, and is not equal to `port`, then this port allows access to the server without having to use TLS security, even if `use_tls=True`. Finally, if `password` is defined and different from `None`, then this password **must** be used to access the server, in both secure and non-secure ports. See the Commands section for instructions on how to use the password. 
- **Network discovery**: a client can search for available servers on the local network. To do this, the server must be instantiated with `discoverable=True`. The principle here is the following:
  1. A server listens on the multicast address `multicast_group` and the UDP port `multicast_port`.
  2. A client sends a discovery message to this multicast address. See [Exchange protocol between the client and the server](PROTOCOLE_FR.md) for the description of the protocol used.
  3. All servers subscribed to the multicast group receive the message.
  4. Upon receipt of this message, each server verifies that the data received corresponds to expectations and responds directly to the client in UDP unicast. See [Exchange protocol between the client and the server](PROTOCOLE_FR.md) for the description of the protocol used.
- **Persistence**: Persistence allows server data to be saved on the hard drive, and restored when the server is restarted. By default, persistence is disabled (parameter `persistence_mode=None`). When persistence is enabled, server data is saved to a file defined by the `persistence_path` parameter. The file is backed up every time the server is shut down, and restored when the server restarts. It can also be saved or reloaded on demand (see the **administrator** level commands in the [Exchange protocol between the client and the server](PROTOCOLE_FR.md)). It is possible to activate 2 persistence modes:
  - `persistence_mode=SaveFormat.JSON`: allows you to save server data in a JSON file. By default (if `persistence_path=None`), the file is defined by `Path("data/server_data.json")`. The file (as well as the directories accessing it) is created automatically if it does not already exist.
  - `persistence_mode=SaveFormat.SQLITE`: allows you to save the server data in an SQLITE database. By default (if `persistence_path=None`), the file is defined by `Path("data/server_data.db")`. The database (as well as the directories accessing it) is created automatically if it does not already exist.
- **Automatic cleaning**: The server periodically cleans up orphaned `Player` objects. A player is considered an orphan if he is associated with a client session that no longer exists (disconnection) AND he is not associated with any `User`. The frequency of this cleaning is defined by the `garbage_collection_periodicity` parameter (in seconds).

The `GameServer` class has the following methods:
- `start`: Starts the server in asynchronous mode.
  - Description: Starts the server in asynchronous mode, allowing connections and client requests to be handled concurrently. This method should be called to start the server and set up the necessary network listeners. If persistence is enabled, then if the specified file exists and is compatible with the chosen save format, the data is loaded into memory and used. If the file does not exist, then it is created waiting to receive the data. If there is no administrator account (even after possibly loading the data), then the server creates the administrator account `admin` with the password `admin`. Of course, it is **very strongly** recommended to change your password, or better, to create a new administrator account and delete that one as soon as possible.
  - Settings: none
  - Return: none
- `stop`: Stops the server.
  - Description: Shuts down the server attempting to cleanly close connections and save data if persistence is enabled.
  - Settings: none
  - Return: none
- `restart`: Restarts the server.
  - Description: Restarts the server by cleanly closing connections, saving, and reloading data if persistence is enabled. Similar to `stop` then `start`.
  - Settings: none
  - Return: none

### Contents of the src/multiplayer/client.py file

This file contains the logic for managing multiplayer clients.

#### GameClient class
The `GameClient` class is responsible for connecting and communicating with a `GameServer` server. It allows you to discover servers on the network, connect to them securely or not, authenticate, and exchange messages (requests, responses, and notifications) according to the defined protocol.

##### Settings

The `GameClient` class is instantiated with the following parameters:

| Name | Type | Description | Mandatory | Default |
|---|---|---|---|---|
| `host` | str | The IPv4 address or hostname of the server | No | `"127.0.0.1"` |
| `port` | int | The server TCP port number | No | 65432 |
| `use_tls` | bool | Use TLS protocol for secure communication | No | `False` |
| `tls_ca_path` | `Path\|None` | The path to the CA certificate (or server self-signed certificate) for TLS validation. If `None`, the system's trusted certificates are used. | No | `None` |

##### Attributes

The class has the following attributes:

| Name | Type | Description | Editable | Implementation accuracy |
|---|---|---|---|---|
| `host` | str | The IPv4 address or hostname of the server | Yes | - |
| `port` | int | The server TCP port number | Yes | - |
| `tls_ca_path` | `Path\|None` | The path to the TLS validation certificate. If `None`, uses system certificates. | No | - |
| `is_connected` | bool | Indicates whether the client is currently connected to the server | No | - |
| `session_player` | `Player\|None` | The default player associated with the current session | No | Automatically updated when authenticating or creating a player. |

##### Methods

The `GameClient` class has the following methods:

- `discover` (class method): Finds available servers on the local network.
  - Description: Sends a multicast discovery message in UDP and collects responses from active servers.
  - Settings:
    - `timeout` (float): Maximum waiting time for receiving responses (in seconds). Optional. Default: 2.0.
    - `multicast_group` (str): The multicast address to use. Optional. Default: `"239.255.0.1"`.
    - `multicast_port` (int): The multicast port to use. Optional. Default: 65,434.
  - Return value: A list of dictionaries, each dictionary containing the information of a discovered server (name, host, port, etc.).
- `connect`: Establishes the TCP connection with the server.
  - Description: Attempts to open a connection with the server using the `host`, `port` and `use_tls` parameters (as well as `tls_ca_path` if provided, otherwise uses system root certificates).
  - Settings: None.
  - Return value: None.
  - Exceptions thrown:
    - `ConnectionError`: if the connection fails.
- `disconnect`: Closes the connection with the server.
  - Description: Cleanly closes the current TCP connection.
  - Settings: None.
  - Return value: None.
- `login`: Authenticates with the server.
  - Description: Sends an authentication request with the credentials provided. If successful, the client retrieves the user's information and their associated player.
  - Settings:
    - `username` (str): The username. Mandatory.
    - `password` (str): The password. Mandatory.
  - Return value: The `User` instance corresponding to the authenticated user.
  - Exceptions thrown:
    - `PasswordError`: if the password is incorrect.
    - `PlayerNotFoundError`: if the user does not exist.
- `send_request`: Sends a request to the server and waits for its response.
  - Description: Low-level method for sending any command supported by the protocol and receiving the corresponding response.
  - Settings:
    - `command` (str): The name of the command/action to execute. Mandatory.
    - `**kwargs`: The arguments associated with the command.
  - Return value: A dictionary containing the data from the server response.
  - Exceptions thrown:
    - `MultiplayerError` (or a subclass): if the server returns an error.
- `on_notification`: Registers a callback function to handle notifications.
  - Description: Allows you to associate a function with a specific type of notification or with all notifications.
  - Settings:
    - `notification_type` (str|None): The type of notification to listen for (ex: `"GAME_EVENT"`). If `None`, the callback receives all notifications.
    - `callback` (callable): The function to call, accepting the notification dictionary as an argument.
  - Return value: None.

Additional information:
- **Notification management**: The client must be able to receive and process notifications sent spontaneously by the server. The implementation relies on registering callbacks via the `on_notification` method. When a notification arrives, the client identifies the callbacks registered for that type (or global callbacks) and executes them asynchronously or sequentially depending on the chosen architecture.

  **Exhaustive list of notification types (extracts from the protocol):**
  - `SERVER_SHUTDOWN`: Warns clients that the server will shut down soon.
  - `GROUP_GAME_ADDED`: Informs clients that a game has just been added to a group.
  - `GROUP_GAME_REMOVED`: Informs clients that a game has just been removed from a group.
  - `GROUP_GAME_UPDATED`: Informs clients that part of a group has changed state or visible properties.
- `GAME_EVENT`: Notifies the participants of an action carried out by one of them or by the server.
  - `GAME_STATE_CHANGED`: Informs clients that the global or custom state of the game has been changed.
  - `GAME_TURN_CHANGED`: Notifies connected clients that a new round has started and identifies the active player.

  **Example of use:**
  ```python
  # Game event handling
  def my_game_handler(notification):
      payload = notification["payload"]
      print(f"Action {payload['action_type']} received from {payload['player_id']}")

  client.on_notification("GAME_EVENT", my_game_handler)

  # Global notification handling (log)
  client.on_notification(None, lambda n: logging.info(f"Notification received: {n['type']}"))
  ```
- **Serialization**: The client must support JSON and MessagePack formats for exchanges, in accordance with protocol requirements.

## Workflows

Github workflows are stored in `.github/workflows` and are used to automate development and deployment tasks. Files are written in YAML and follow a standardized format to ensure consistency and readability.

The workflows to be implemented are as follows:
- `lint.yml`: Automate the verification of code quality and compliance with standards. It runs automatically when a commit is pushed to the master branch (this also includes merging a branch to the master branch). He can also launch manually, on the branch of his choice.
- `test.yml`: Automate unit and functionality tests. Performs all unit tests in Windows, Linux, and macOS environments. It runs automatically when a commit is pushed to the master branch (this also includes merging a branch to the master branch). He can also launch manually, on the branch of his choice.
- `release.yml`: Automate the creation of versions and deployment on distribution platforms. Automatically launches when a tag in the form `vX.Y.Z` is created. It can also be run manually, in this case choosing the version to deploy.
- `pypi.yml`: Automate the deployment of the version on PyPI. Executes only manually, in this case with the choice of the version to deploy.

##Scripts

Scripts are stored in the `scripts` directory:

- `check_project.py`: performs the following actions:
  - Checks changes made to the code from the main branch. If there are no changes, or if the only changes made have been to the documentation files, the script stops without checking.
  - Checks for the presence of `uv` and installs it if necessary
  - In an isolated Python virtual environment:
    - Installs all the dependencies necessary for development
    - Performs verification of code quality and compliance with standards
    - Run unit and functionality tests
  - Can use `--fix` option to automatically fix style and conformance errors

- `local_game.py`: runs a visible local multiplayer game demonstration:
  - Opens a console window for the local server and one window for each player.
  - Accepts the number of players as an argument; the default is `2`.
  - Each player connects to the server, joins the same game, and simulates several exchanges and turns at a human-readable pace.
  - Finishes the game normally, then cleanly stops the server.
  - Usage:
    - `uv run python scripts/local_game.py`: starts a game with two players.
    - `uv run python scripts/local_game.py 4`: starts a game with four players.
