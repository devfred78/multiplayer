# Instructions for developing version 3 of multiplayer

This document provides instructions for developing version 3 of the multiplayer module. It describes the coding conventions, dependencies, and technical specifications needed to ensure compatibility and consistency between the different modules of the package.

The version of the module is independent of the version of the client-server exchange protocol. The protocol is at version 2, revision 2.1: the major version (`2`) is transmitted in the `version` field of every message and guarantees compatibility between programs, while the revision (`2.1`) indicates the available features and is announced by the server (see the "Versioning and extensibility" paragraph of the [Client-server exchange protocol](PROTOCOLE.md)).

## General rules

### Comment and docstring conventions

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

- All "ID" properties must be alphanumeric strings, generated uniquely at instantiation using the `uuid.uuid4()` function of the uuid module. They must be read-only. Exceptions to this generation rule are objects rebuilt from the representation of an existing object (restoration of a save, `from_dict` methods), which keep the original ID, as well as copies that represent the same object (for example the `option` attribute of the `OptionEntry` class): two objects carrying the same ID then designate the same object.
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

#### `OptionType` (Enum)
An enumeration representing the types of options used to configure player customization parameters. These options are typically used by a client process to build a customization form.

* `OptionType.CHECK`: A boolean option, which can typically be represented by a checkbox.
* `OptionType.RANGE`: A numeric option, whose value lies within a specified interval, which can be represented by a slider or a numeric input field.
* `OptionType.LIST`: A list option, which can typically be represented by a drop-down list.
* `OptionType.TEXT`: A text option, which can be represented by a text input field.

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

#### Class `PasswordError`
This class is derived from `MultiplayerError` and is used to report an attempt to use an incorrect password.

#### Class `GameIsFullError`
This class is derived from `MultiplayerError` and is used to report an attempt to add a player or observer to a game that is already full.

#### Class `GameAlreadyStartedError`
This class is derived from `MultiplayerError` and is used to report an attempt to start a game that is already in progress.

#### Class `NotEnoughPlayersError`
This class is derived from `MultiplayerError` and is used to report an attempt to start a game whose number of players is lower than the minimum required (`min_players` parameter of the `Game` class).

#### Class `GameIsFinishedError`
This class is derived from `MultiplayerError` and is used to report an attempt to modify a game that has ended.

#### Class `GameNotStartedError`
This class is derived from `MultiplayerError` and is used to report an attempt to pause, resume, stop, or advance (for example, move to the next turn) a game that has not started yet.

#### Class `GameAlreadyPausedError`
This class is derived from `MultiplayerError` and is used to report an attempt to pause a game that is already paused.

#### Class `GameNotPausedError`
This class is derived from `MultiplayerError` and is used to report an attempt to resume a game that is not paused.

#### Class `GameNotTurnBasedError`
This class is derived from `MultiplayerError` and is used to report an attempt to perform a turn-specific action in a game that is not turn-based.

#### Class `GameNotFoundError`
This class is derived from `MultiplayerError` and is used to report an attempt to look up a game that does not exist. This exception includes the invalid game ID in its message (if provided).

#### Class `GameNotFoundInGroupError`
This class is derived from `GameNotFoundError` and is used to report an attempt to remove a game from a group that does not contain it. This exception includes the invalid game ID in its message (if provided).

#### Class `GameHasPlayersError`
This class is derived from `MultiplayerError` and is used to report an attempt to perform an operation on a game that is only possible as long as no player has joined it (for example creating or replacing the player factory). The presence of observers is not taken into account. This exception includes the ID of the game concerned in its message.

#### Class `PlayerFactoryNotDefinedError`
This class is derived from `MultiplayerError` and is used to report an attempt to use the player factory of a game that does not have one (`player_factory` attribute set to `None`), for example with the `create_and_join_player` method of the `Game` class. This exception includes the ID of the game concerned in its message.

#### Class `UnsupportedFeatureError`
This class is derived from `MultiplayerError` and is used by the `GameClient` class to report an attempt to use a protocol feature that the server does not offer (for example the `player_factory` feature with a revision 2.0 server). It is raised before the corresponding request is sent. This exception includes the name of the feature concerned and the revision announced by the server in its message.

#### Class `OptionError`
This class is derived from `MultiplayerError` and serves as the common base class for exceptions related to player customization options (`OptionValueAlreadyGivenError`, `LackingOptionError`, `InvalidOptionValueError` and `OptionAlreadyExistsError`). It is not intended to be raised directly, but makes it possible to catch all option-related errors at once (`except OptionError`), without confusing them with the other errors of the module.

#### Class `OptionValueAlreadyGivenError`
This class is derived from `OptionError` and is used to report an attempt to introduce an object containing an option whose value has already been used, although it is supposed to be unique in the context. This exception includes the ID of the option concerned and the offending value in its message.

It has the following attributes, set when it is created:

| Name | Type | Description |
|-----|------|-------------|
| `option_id` | str | The ID of the option concerned. |
| `value` | any | The value already used. |

#### Class `LackingOptionError`
This class is derived from `OptionError` and is used to report that no value is available for an option that is mandatory in the context: either the introduced object does not carry a value for this option, or no value was provided for this option and there is no possible value left. This exception includes the ID of the missing option and the reason for the error in its message.

It has the following attributes, set when it is created:

| Name | Type | Description |
|-----|------|-------------|
| `option_id` | str | The ID of the option concerned. |
| `reason` | str | The reason for the error: `"ABSENT_FROM_PLAYER"` if the `Player` object introduced into a game does not carry a value for this option (or carries the value `None`, which is considered as an absence of value), or `"NO_AVAILABLE_VALUE"` if no value was provided for this option when creating a player and there is no possible value left (proposed value set to `None`). |

#### Class `InvalidOptionValueError`
This class is derived from both `OptionError` and `ValueError`, and is used to report an incorrect option value, either when a player is created by a factory or when a player is introduced into a game that has a factory. Deriving from `ValueError` allows code that catches this standard exception to keep working. This exception includes the ID of the option concerned, the offending value and the reason for the error in its message.

It has the following attributes, set when it is created:

| Name | Type | Description |
|-----|------|-------------|
| `option_id` | str | The ID of the option concerned (or the key provided, if it does not match any option). |
| `value` | any | The offending value. |
| `reason` | str | The reason for the error: `"UNKNOWN_OPTION"` (the key provided does not match any option), `"INCOMPATIBLE_TYPE"` (the value is not accepted for the type of the option, according to the conversion rules of the `Option` class) or `"INVALID_VALUE"` (the value is outside the `min_value` / `max_value` bounds, does not match a `step` increment, or is not in `choices`). |

#### Class `OptionAlreadyExistsError`
This class is derived from `OptionError` and is used to report an attempt to introduce an option that is already present. This exception includes the ID of the option already present in its message. This exception is also raised when a similar option is already present. Similarity is defined either by the equality of the option IDs, or by the equality between the name of the introduced option and the frozen key of an option already present (see the `add_option` method of the `PlayerFactoryTemplate` class).

### Contents of the src/multiplayer/game.py file

This file contains the main game management logic. It defines the classes and functions needed to create, manage, and resolve games.
In particular, it contains the following classes:

#### Class `Option`
This class represents an option in the context of the game. An option is a customization parameter whose value is chosen when a player is created, by means of a player factory. It can be of different types, such as boolean, numeric, text, etc. Each option is defined by a type and specific parameters.

It is instantiated with the following parameters:

| Name | Type | Description | Mandatory | Default |
|---------|----------|----------------------|-------------|-------------------|
| `name` | str | The name of the option. It is a string that identifies the option. | Yes | - |
| `option_type` | OptionType | The type of the option. | Yes | - |
| `description` | str | A description of the option. It is a string that describes the option. | No | "" (empty string)|
| `default` | bool\|int\|float\|str\|`None` | The default value of the option. `None` means "first available value" (see the "`None` default value" paragraph below). | No | `None` |
| `min_value` | float\|int\|`None` | The minimum value of the option. Only relevant for `OptionType.RANGE` options. Ignored otherwise. `None` means that there is no minimum.| No | `None` |
| `max_value` | float\|int\|`None` | The maximum value of the option. Only relevant for `OptionType.RANGE` options. Ignored otherwise. `None` means that there is no maximum. | No | `None` |
| `step` | float\|int | The step of the option. Defines the increment between the possible values of an `OptionType.RANGE` option (see the "Possible values of an `OptionType.RANGE` option" paragraph below). | No | 1 |
| `choices` | list[str]\|tuple[str, ...] | The possible values of the option. Only relevant for `OptionType.LIST` options. Ignored otherwise. | No | [] (empty list) |

The parameter names `option_type`, `min_value` and `max_value` avoid shadowing the Python built-in functions `type`, `min` and `max`. The dictionary representations (`to_dict` method), used by the save feature and by the network protocol, however keep the keys `type`, `min` and `max`.

When the option is created, the following checks are performed. If a check fails, the indicated exception is raised and the option is not created:

| Case | Exception |
|-----|-----------|
| `option_type` is not a member of the `OptionType` enumeration | `TypeError` |
| `min_value` and `max_value` are both defined, and `min_value` is greater than `max_value` | `ValueError` |
| `step` is less than or equal to 0 | `ValueError` |
| `choices` contains an element that is not a string | `TypeError` |
| `choices` contains a duplicate | `ValueError` |
| The option is of type `OptionType.LIST` and `choices` is empty | `ValueError` |
| `default` (if it does not contain a runtime constant and is not `None`) is not accepted for the type of the option, according to the conversion rules below | `TypeError` |
| `default` (if it does not contain a runtime constant and is not `None`) is not a possible value of the option: outside the `min_value` / `max_value` bounds, not matching a `step` increment, or not in `choices` | `ValueError` |

If `default` contains runtime constants (see the "Runtime constants" paragraph below), the following checks apply instead of the check of the default value, which is only possible after evaluation:
- if a constant is not recognized, a `ValueError` exception is raised;
- if a constant is used in an option type that does not allow it, or in a way that is not allowed for this option type, a `TypeError` exception is raised;
- if `%%RANDOM_NUMBER%%` is used in an `OptionType.RANGE` option whose `min_value` or `max_value` is `None`, a `ValueError` exception is raised.

It has the following attributes:

| Name | Type | Description | Editable | Implementation details |
|---------|----------|----------------------|----------------|--------------------------------|
| `ID` | str | The unique identifier of the option | No | Automatically initialized with the value of `uuid.uuid4()`. |
| `name` | str | Name of the option | Yes | Automatically initialized with the name provided when the option is created |
| `description` | str | Description of the option | Yes | Automatically initialized with the description provided when the option is created |
| `option_type` | OptionType | The type of the option. | No | Takes the value of the type provided when the option is created |
| `choices` | tuple[str, ...] | The possible choices for the option | No | Takes the value of the choices provided when the option is created, copied into a tuple: the attribute therefore cannot be modified, and a later modification of the list provided at creation has no effect on the option. |
| `min_value` | float\|int\|`None` | The minimum value for the option | No | Takes the minimum value provided when the option is created, converted according to whether the option is integer or decimal. |
| `max_value` | float\|int\|`None` | The maximum value for the option | No | Takes the maximum value provided when the option is created, converted according to whether the option is integer or decimal. |
| `step` | float\|int | The increment value for the option | No | Takes the increment value provided when the option is created |
| `default` | bool\|int\|float\|str\|`None` | The default value for the option | No | Takes the default value provided when the option is created, converted according to the conversion rules, without evaluating any runtime constants it contains. |

The `Option` class has the following methods:

- `evaluate_default`: provides the default value of the option, after evaluating any runtime constants it contains.
  - Parameters:
    - `context` (dict[str, str]\|`None`): the context providing the value of the constants (see the "Runtime constants" paragraph). Optional. Default: `None` (equivalent to an empty dictionary).
    - `exclusions` (list\|`None`): list of values not to select during a random draw (`%%RANDOM_NUMBER%%` for an `OptionType.RANGE` option, `%%RANDOM_CHOICE%%` for an `OptionType.LIST` option): the draw is performed only among the possible values that are not in this list. No effect on the other constants. Optional. Default: `None` (no exclusion).
  - Implementation details: if `default` is `None`, the method returns the first available value, according to the "`None` default value" paragraph (without taking the `exclusions` parameter into account, the next value rule being applied by the factory). If `default` does not contain any runtime constant, the method returns `default` as is. The context provided is not modified by the method.
  - Return value: the evaluated default value. For a random draw, `None` if all possible values are in `exclusions`.

- `to_dict`: provides a dictionary representation of the option, made up only of simple types (strings, numbers, booleans, `None`, lists). This representation is shared by the save feature (see the `save.py` file) and by network exchanges (see the [Client-server exchange protocol](PROTOCOLE.md), "Option representation" paragraph).
  - Parameters: None.
  - Return value: a `dict` object with the following elements:

    | Key | Value |
    |-----|--------|
    | `option_id` | The ID of the option. |
    | `type` | The name of the `OptionType` enumeration member of the `option_type` attribute (e.g. `"RANGE"`). |
    | `name` | The current name of the option. |
    | `description` | The description of the option. |
    | `default` | The raw value of the `default` attribute, without evaluation of any runtime constants. |
    | `min` | The value of the `min_value` attribute. |
    | `max` | The value of the `max_value` attribute. |
    | `step` | The value of the `step` attribute. |
    | `choices` | The possible choices (`choices` attribute), as a list. |

- `from_dict` (class method): creates an option from a dictionary representation, in the format returned by the `to_dict` method. This method is used to restore a save and to create options from data received by the server.
  - Parameters:
    - `data` (dict): the representation of the option. The `name` and `type` keys are mandatory. The other keys are optional and, if absent, take the default values of the corresponding constructor parameters (`description`, `default`, `min` for `min_value`, `max` for `max_value`, `step`, `choices`). Mandatory.
  - Implementation details: if the `option_id` key is present, the created option keeps this ID; otherwise, a new ID is generated with `uuid.uuid4()`. All the checks performed when an option is created apply. Unknown keys are ignored. The dictionary provided is not modified.
  - Exceptions raised:
    - `TypeError` or `ValueError`: in the same cases as when an option is created, as well as if a mandatory key is missing (`ValueError`) or if the value of `type` is not the name of a member of the `OptionType` enumeration (`ValueError`).
  - Return value: the created `Option` object.

##### Value conversion rules

The following rules apply identically to the default value (when the option is created), to the values provided when a player is created (`create_player` method of the `PlayerFactory` class) and to the values checked when a player is introduced into a game (`join_game_as_player` method of the `Game` class):

| Option type | Accepted values | Conversion |
|---------------|-------------------|------------|
| `OptionType.CHECK` | `bool` only. | None. |
| `OptionType.RANGE` | `int`, `float`, or a string representing a number (e.g. `"3.0"`). `bool` values are rejected, even though `bool` is a subclass of `int` in Python. | To `int` if the option is integer (`"3.0"` gives `3`, but `"3.5"` or `3.5` are rejected), to `float` if the option is decimal (see the next paragraph). |
| `OptionType.LIST` | String only. | None. |
| `OptionType.TEXT` | String only. | None. |

A value that is not accepted is of an incompatible type: depending on the context, it causes a `TypeError` exception (when the option is created) or an `InvalidOptionValueError` exception with `reason` set to `"INCOMPATIBLE_TYPE"` (when a player is created or introduced). It is always the converted value that is retained: it is stored in the `Player` object, and it is the one compared for the uniqueness check.

##### Possible values of an `OptionType.RANGE` option

The possible values of an `OptionType.RANGE` option are the values of the form `reference + k × step` (where `k` is a signed integer) lying between `min_value` and `max_value` (when they are defined). The reference is `min_value` if it is defined, and `0` otherwise.

An `OptionType.RANGE` option is **integer** if `step`, as well as `min_value`, `max_value` and `default` when they are defined (and `default` does not contain a runtime constant), are all of type `int`: its values are then of type `int`. Otherwise, the option is **decimal**: its values are of type `float`, and whether a value belongs to the grid defined by `step`, as well as the equality of two values, is evaluated with a tolerance (`math.isclose` function), in order to avoid floating-point rounding errors.

##### `None` default value

A default value of `None` means "first available value". When the proposed value is computed (see the `get_option` method of the `PlayerFactory` class), it is replaced by:

| Option type | Retained value |
|---------------|----------------|
| `OptionType.CHECK` | `False` |
| `OptionType.RANGE` | `min_value` if it is defined, otherwise the possible value closest to `0` (favoring the positive value in case of a tie) |
| `OptionType.LIST` | The first element of `choices` |
| `OptionType.TEXT` | `""` (empty string) |

If this value is excluded, the next value rule applies (see the `get_option` method of the `PlayerFactory` class).

##### Runtime constants

Runtime constants, whose value is computed when the program runs, can be used to define the default value of an option (`default` parameter).

These constants are recognized because their name, made up of uppercase letters and the `_` character, is surrounded by two double "percent" characters (`%%CONSTANT%%`, i.e. the pattern `%%[A-Z_]+%%`). The rest of the string is not interpreted: an isolated `%` character, or a sequence that does not match this pattern, is kept as is.

The recognized runtime constants are the following:

| Name | Produced type | Source | Description |
|------------|--------------|--------|--------------|
| `%%CURRENT_TIME%%` | str | Library | The local date and time at the moment of evaluation, in ISO 8601 format, to the second, with the UTC offset (e.g. `"2026-11-15T12:34:56+01:00"`). |
| `%%RANDOM_NUMBER%%` | int | Library | For an `OptionType.TEXT` option: an integer drawn at random between 0 and 100 inclusive. For an `OptionType.RANGE` option: a value drawn at random among the possible values of the option (see below). |
| `%%RANDOM_CHOICE%%` | str | Library | For an `OptionType.LIST` option only: a value drawn at random among the possible choices of the option (see below). |
| `%%GAMENAME%%` | str | Factory | The name of the game the factory is associated with (`name` attribute of the `Game` object). If the game has no name (`name` attribute set to `None`), the constant is replaced by an empty string (`""`). |
| `%%USERNAME%%` | str | Context | The name of the user for whom the player is created (`username` attribute of the `User` object). |
| `%%SERVERNAME%%` | str | Context | The name of the server (`name` attribute of the `GameServer` object). |
| `%%CLIENTADDRESS%%` | str | Context | The IP address (IPv4 or IPv6) of the client. |
| `%%SERVERADDRESS%%` | str | Context | The IP address (IPv4 or IPv6) of the server. |

The "Source" column indicates who provides the value of the constant:
- Library: the value is computed by the `multiplayer` library itself, at the moment of evaluation.
- Factory: the value is provided by the `PlayerFactory` object performing the evaluation, based on the game it is associated with.
- Context: the value is provided by the caller, through a context dictionary (see below). On the server side, it is the `GameServer` object that builds this context from the session and the connection of the user concerned.

The **context** is a dictionary of type `dict[str, str]`, whose keys are the names of the constants without the `%%` characters (for example `{"USERNAME": "alice", "CLIENTADDRESS": "192.168.1.12"}`), and whose values are the values to substitute for them. A constant present in the context always takes the value from the context, even if it is a constant normally provided by the library or by the factory: this makes it possible, in particular, to obtain reproducible results in unit tests (for example by setting `CURRENT_TIME` or `RANDOM_NUMBER`). A constant whose source is "Context" and which is absent from the context is replaced by an empty string (`""`).

The rules for using the constants depend on the type of the option:

| Option type | Allowed use in `default` |
|---------------|--------------------------------------|
| `OptionType.TEXT` | Free substitution within the string: one or more constants can be combined with text (e.g. `"Player_%%RANDOM_NUMBER%%"`). The result of the evaluation is a string. `%%RANDOM_CHOICE%%` is not allowed. |
| `OptionType.RANGE` | Only the exact string `"%%RANDOM_NUMBER%%"`, without any other text. The `min_value` and `max_value` parameters must then both be defined (other than `None`). The value is drawn at random among the possible values of the option, i.e. lying between `min_value` and `max_value` and matching a `step` increment. |
| `OptionType.LIST` | Only the exact string `"%%RANDOM_CHOICE%%"`, without any other text. The value is drawn at random among the elements of `choices`. |
| `OptionType.CHECK` | No constant allowed. |

Constants are not allowed in the other parameters of the option (`min_value`, `max_value`, `step`, `choices`, `name`, `description`).

Constants are kept unevaluated in the `Option` object (the `default` attribute always returns the raw value, for example `"Player_%%RANDOM_NUMBER%%"`), as well as when options are copied into a template or into a factory. They are only evaluated when the proposed value of an option is computed, by the `evaluate_default` method, called by the `get_option` and `create_player` methods of the `PlayerFactory` class. Each evaluation is independent: two successive evaluations may give different results (date and time, random draws). It is therefore recommended that the client process explicitly pass to the `create_player` method the proposed value it presented to the user, rather than letting the factory perform a new evaluation.

#### Class `OptionEntry`
This class describes an option as it is registered in a template (`PlayerFactoryTemplate`) or in a factory (`PlayerFactory`): the option itself, together with the parameters that were associated with it when it was added to the template. These parameters do not belong to the `Option` object, since the same option can be added to several templates with different parameters.

`OptionEntry` objects are created by the `PlayerFactoryTemplate` and `PlayerFactory` classes, and returned by their `get_option` methods. They are not intended to be instantiated directly by the user of the `multiplayer` library.

An `OptionEntry` object is immutable: none of its attributes can be modified, and it does not give access to the internal objects of the template or of the factory.

It has the following attributes:

| Name | Type | Description | Editable | Implementation details |
|-----|------|-------------|------------|----------------------------|
| `option` | `Option` | The option concerned. | No | This is a copy of the `Option` object held by the template or the factory: modifying it has no effect on the template or the factory. This copy represents the same option, not a new option: it therefore keeps the ID of the original option (see the ID convention). In this respect it differs from the copies made when a factory is created, which constitute new options and receive a new ID. |
| `unicity` | bool | The value of the `unicity` parameter associated with the option. | No | - |
| `hide` | bool | The value of the `hide` parameter associated with the option. | No | - |
| `player_attribute` | str\|`ParameterFamily` | The value of the `player_attribute` parameter associated with the option. | No | - |
| `key` | str | The frozen key of the option. | No | - |

The `OptionEntry` class has the following methods:

- `to_dict`: provides a dictionary representation of the registered option, shared by the save feature and by network exchanges.
  - Parameters: None.
  - Return value: a `dict` object made up of the elements returned by the `to_dict` method of the `option` attribute, supplemented by the following elements:

    | Key | Value |
    |-----|--------|
    | `unicity` | The value of the `unicity` attribute. |
    | `hide` | The value of the `hide` attribute. |
    | `target` | `"ATTRIBUTE"` if `player_attribute` is a string, `"STATIC"` if it is `ParameterFamily.STATIC`, `"DYNAMIC"` if it is `ParameterFamily.DYNAMIC`. |
    | `attribute` | The value of `player_attribute` when `target` is `"ATTRIBUTE"` (e.g. `"name"`), `None` otherwise. |
    | `key` | The frozen key of the option. |

- `from_dict` (class method): creates an `OptionEntry` object from a dictionary representation, in the format returned by the `to_dict` method. This method is mainly used by the `from_dict` methods of the `PlayerFactoryTemplate` and `PlayerFactory` classes.
  - Parameters:
    - `data` (dict): the representation of the registered option. The elements of the option itself are processed by the `from_dict` method of the `Option` class. The `target` key is mandatory, as is the `attribute` key when `target` is `"ATTRIBUTE"`. The `unicity` key is optional (`False` if absent). The `hide` key is optional (`False` if absent). The `key` key is optional: if it is absent, the frozen key is the name of the option. Mandatory.
  - Implementation details: the `player_attribute` parameter is rebuilt from `target` and `attribute` (`"STATIC"` gives `ParameterFamily.STATIC`, `"DYNAMIC"` gives `ParameterFamily.DYNAMIC`, `"ATTRIBUTE"` gives the value of `attribute`). The checks applied to `player_attribute` by the `add_option` method of the `PlayerFactoryTemplate` class apply. The dictionary provided is not modified.
  - Exceptions raised:
    - `TypeError` or `ValueError`: in the same cases as the `from_dict` method of the `Option` class and as the `player_attribute` checks of the `add_option` method, as well as if `target` is missing or is not `"ATTRIBUTE"`, `"STATIC"` or `"DYNAMIC"` (`ValueError`).
  - Return value: the created `OptionEntry` object.

#### Class `Player`
This class represents a player in the context of the game. It is the entity that actually takes part in games. While a `User` account manages access and permissions, the `Player` object carries the game-related attributes (name, score, state, etc.). Typically, a `Player` object is created just before a game and destroyed after it ends. This behavior nevertheless remains an implementation choice, as the `multiplayer` library does not handle the creation or destruction of `Player` objects when a `Game` object is instantiated or ends (destruction may however be handled as part of the automatic cleanup feature of the `GameServer` class, see the related paragraph).

It is instantiated with the following parameters:

| Name | Type | Description | Mandatory | Default |
|------------|----------|--------------|-------------|---------|
| `name` | str | The player's name.  | No | "Player" |
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

#### Class `PlayerFactoryTemplate`
When a game is created, it is possible to define how the players will be created, the parameters they will have to handle, and the values that it will be possible to assign to them before the game starts. For example, for a chess game, the player who wants to join the game must be able to decide whether they will play white or black.
It is also possible to make the possible values evolve and narrow down as players join the game. For example, still in the context of a chess game, if a player has chosen to play white, then the second player can only play black.
To do so, a `PlayerFactoryTemplate` object must be created, and `Option` objects must be assigned to it to define the parameters, the possible values, and the default values. This `PlayerFactoryTemplate` object can then be used by a `Game` object to create within it (i.e. in the namespace of the `Game` object) a `PlayerFactory` object, which is in turn used to support the creation of the `Player` objects to be assigned to the game as players. A factory is specific to a game: it determines the values that are still available from the list of players of that game (in particular to handle "unique" choices, such as the color - white or black - assigned in a chess game). This is why it is created within the `Game` object. The template, on the other hand, is independent of any game and lives in the global namespace: it can be used to create the factories of several games.

The `PlayerFactoryTemplate` class is instantiated with the following parameters:

| Name | Type | Description | Mandatory | Default |
|------------|------|------------------|-------------|-------------------|
| `name` | str | Name of the template | Yes | - |

This `name` parameter allows a user to identify the template, for example in the list of templates held by a server (see the factory template registry of the `GameServer` class, and the `FACTORY_TEMPLATE_LIST` request of the [Client-server exchange protocol](PROTOCOLE.md)). In local use, the `multiplayer` library does not keep any registry of templates: it is up to the user to keep the templates they create. Although it is not mandatory, it is **strongly** recommended to provide a unique name for each template.

It has the following attributes:

| Name | Type | Description | Editable | Implementation details |
|------------|------|---------------------------------|------------|----------------------------|
| `ID` | str | Unique identifier of the template| No | Automatically initialized with the value of `uuid.uuid4()`. |
| `name` | str | Name of the template | Yes | Automatically initialized with the name provided when the template is created.|
| `options` | list[tuple[str,str]] | List of the IDs and names of the options of the template, as (ID, name) tuples | No | A new list is created each time this attribute is read; modifying it has no impact on the options contained in the template. |


The `PlayerFactoryTemplate` class has the following methods:

- `add_option`: adds an option to the template.
  - Description: adds an option to the template. The template records a copy of the `Option` object provided, not the object itself: a later modification of the object provided (for example of its `name` or `description` attribute) has no effect on the template. This copy represents the same option and therefore keeps its ID (see the ID convention). Checks that a similar option is not already present in the template. Similarity is defined either by the equality of the option IDs, or by the equality between the current name of the option to add (which will become its frozen key) and the frozen key of an option already present in the template. For options already present, it is their frozen key that is taken into account, not their name (the two can only differ for an option rebuilt by a `from_dict` method). In case of similarity, an `OptionAlreadyExistsError` exception is raised.
  - Parameters (in this order):
    - `option` (`Option`): the `Option` object to add to the template. Mandatory.
    - `player_attribute` (str|`ParameterFamily`): the attribute of the `Player` object associated with this option. Mandatory. Depending on this parameter, the option is integrated into the generated `Player` object either in the `static_state` attributes (`ParameterFamily.STATIC`), or in the `dynamic_state` attributes (`ParameterFamily.DYNAMIC`), or associated with the attribute whose name matches the specified string (only one possible case for now: `"name"`). Since the `name` attribute of the `Player` object is a string, only options of type `OptionType.TEXT` and `OptionType.LIST` can be associated with it.
    - `hide` (bool): indicates whether the option must be hidden in the player creation form in the user interface. If `True`, this makes it possible to create an attribute used by the game logic but that does not need to be initialized by the user. Only meaningful if `player_attribute` is `ParameterFamily.STATIC` or `ParameterFamily.DYNAMIC`, ignored otherwise. Optional. `False` by default.
    - `unicity` (bool): If `True`, a value of this option carried by a player of the game cannot be carried by another player of the same game. The value becomes available again as soon as the player carrying it is removed from the game. For an option associated with `ParameterFamily.DYNAMIC`, it is the current value carried by the player that is taken into account: if it changes during the game, the excluded values change accordingly. Uniqueness is only guaranteed at the moment the player joins the game (`join_game_as_player` method of the `Game` class): a later modification of the value carried by a player (`name`, `static_state` or `dynamic_state` attribute) is not checked, and may therefore result in two players carrying the same value. It is the responsibility of the user of the `multiplayer` library to preserve uniqueness after the players have been introduced, if the game requires it. For a unique option associated with the `name` attribute, the default name of a `Player` object (`"Player"`) is a value like any other: a player carrying this name forbids it to the following players. It is therefore recommended to give such an option a variable default value, for example `"%%USERNAME%%"` or `"Player_%%RANDOM_NUMBER%%"`. Optional. `False` by default.
  - Exceptions raised:
    - `TypeError` if the object provided is not an instance of `Option`.
    - `TypeError` if `player_attribute` is neither a string nor a member of the `ParameterFamily` enumeration.
    - `ValueError` if `player_attribute` is a string other than `"name"`.
    - `TypeError` if `player_attribute` is `"name"` and the option is not of type `OptionType.TEXT` or `OptionType.LIST`.
    - `OptionAlreadyExistsError` if a similar option is already present in the template.
  - Return value: None.

> Implementation details:
> - Silent replacement only concerns the `name` attribute of the `Player` object: if `player_attribute` is `"name"` and another option of the template is already associated with `name`, then the old option is silently replaced by the new option. The old option is then removed from the template (in the same way as with the `del_option` method). For this similarity check, the replaced option is not compared on its frozen key (the new option can therefore have the same name as the option it replaces), but it is still compared on its ID.
> - For `ParameterFamily.STATIC` and `ParameterFamily.DYNAMIC`, no replacement takes place: a single template can contain as many options associated with the same family as needed, each one identified by its frozen key. An option whose name matches the frozen key of an option already present causes an `OptionAlreadyExistsError` exception (see the similarity check above).
> - If `player_attribute` is a string, the chosen value of the option is assigned as is to this attribute (only one possible case for now: `name`).
> - If `player_attribute` is `ParameterFamily.STATIC` or `ParameterFamily.DYNAMIC`, the option is added as a field in the corresponding dictionaries of the generated `Player` object (`static_state` or `dynamic_state`), in the form:
>
> | Key | Value |
> |---------|------------|
> | Value of the `name` attribute of the option | chosen value of the option |
>
> - Each option receives a frozen key when `add_option` is called: it is the value of the option's `name` attribute at that moment. A later modification of the option's `name` attribute has no effect on this key. For options associated with `ParameterFamily.STATIC` or `ParameterFamily.DYNAMIC`, it is this key that is used in `static_state` or `dynamic_state`, both when creating players and for the checks performed by the game. For all options, it is also this key that is used for the similarity check: two options of the same template can therefore never share the same frozen key. Since the template records a copy of the option provided, and offers no way to rename an option it contains, the frozen key of an option added by `add_option` remains equal to its name. It can only differ from it for an option rebuilt from a representation that explicitly provides its key (`from_dict` methods, for example when restoring a save).

- `get_option`: provides a specific option of the template.
  - Parameters:
    - `option_id` (str): the ID of the option to get. Mandatory.
  - Exceptions raised:
    - `KeyError` if the option does not exist in the template.
  - Return value: an `OptionEntry` object describing the requested option, with its `unicity`, `hide` and `player_attribute` parameters and its frozen key.

- `del_option`: removes an option from the template.
  - Parameters:
    - `option_id` (str): the ID of the option to remove. Mandatory.
  - Exceptions raised:
    - `KeyError` if the option does not exist in the template.
  - Return value: None.

- `to_dict`: provides a dictionary representation of the template, shared by the save feature and by network exchanges.
  - Parameters: None.
  - Return value: a `dict` object with the following elements:

    | Key | Value |
    |-----|--------|
    | `template_id` | The ID of the template. |
    | `name` | The name of the template. |
    | `options` | The list of the options of the template, in the order in which they were added, each in the form returned by the `to_dict` method of the `OptionEntry` class. |

- `from_dict` (class method): creates a template from a dictionary representation, in the format returned by the `to_dict` method. This method is used to restore a save, and by the server to create and modify templates from data received from clients.
  - Parameters:
    - `data` (dict): the representation of the template. The `name` key is mandatory. The `options` key is optional (no option if absent). The `template_id` key is optional. Mandatory.
  - Implementation details: if the `template_id` key is present, the created template keeps this ID; otherwise, a new ID is generated. Each option is rebuilt by the `from_dict` method of the `OptionEntry` class, then added to the template in the order of the list, according to the rules of the `add_option` method (similarity check, replacement of an option associated with the `name` attribute), but keeping its ID and frozen key when they are provided. Creation is atomic: if one of the options is rejected, no template is created. The dictionary provided is not modified.
  - Exceptions raised:
    - `TypeError` or `ValueError`: if the data is malformed, or in the same cases as the `from_dict` method of the `OptionEntry` class.
    - `OptionAlreadyExistsError`: if two options of the list share the same ID or the same frozen key.
  - Return value: the created `PlayerFactoryTemplate` object.

#### Class `PlayerFactory`

This class creates `Player` objects from predefined options. It is particularly useful for defining the characteristics of players according to the type of game they will take part in. For example, for a chess game, players are characterized by the color white or black, which are mutually exclusive (there cannot be 2 players of the same color). These constraints can be implemented in a `PlayerFactory` instance, and used to generate `Player` objects compatible with the chess game carried by a `Game` object with which the `PlayerFactory` object has been associated.

A `PlayerFactory` object is typically used to create `Player` objects only in the context of a particular game. Thus, a `PlayerFactory` object should only be instantiated in the namespace of a `Game` object, and never in the global namespace. In practice, the `PlayerFactory` object should only be created with the `create_player_factory` method of the `Game` object in which it is to be integrated.

The user accesses the options through the `options` attribute (to get the IDs and names of the options) and through the `get_option` method (to get the full option, with its `unicity`, `hide` and `player_attribute` parameters, its frozen key, its exclusion list and the proposed value). This allows the user to choose a value for each option. The chosen values are then passed all at once, as a parameter of the `create_player` method, which creates the corresponding `Player` object.

The factory does not keep any value being entered: each call to `create_player` is independent of the others. Several users can thus prepare their player simultaneously from the same factory, without their choices interfering.

The list of players of the game (`players` attribute of the associated `Game` object) is the only reference for determining the excluded values: the factory does not reserve any value. A `Player` object created by the factory is only taken into account in the exclusions once it has actually joined the game through the `join_game_as_player` method, and ceases to be as soon as it is removed from it. It is the `join_game_as_player` method that performs the final check of the factory's constraints. For a user's choices to be immediately taken into account in the values proposed to the following users, it is recommended to create players by means of the `create_and_join_player` method of the `Game` class, which chains the creation of the player and its introduction into the game in a single operation.

> Implementation details: the excluded values are not stored, but computed each time they are needed (`get_option` and `create_player` methods). For each option created with `unicity` set to `True`, the excluded values are the values of this option carried by the `Player` objects present in the `players` attribute of the associated game (observers are ignored). The value carried by a player is read according to the `player_attribute` parameter of the option: in the player's `name` attribute, or in `static_state` / `dynamic_state` under the key frozen when the option was added to the template (see the `add_option` method of the `PlayerFactoryTemplate` class). A player who does not carry a value for this option, or who carries the value `None`, is ignored for this option.

The `PlayerFactory` class is instantiated with the following parameters:

| Name | Type | Description | Mandatory | Default |
|------------|------|------------------|-------------|-------------------|
| `template` | `PlayerFactoryTemplate` | The template from which the factory copies the options, as well as their `unicity`, `hide` and `player_attribute` parameters, and their frozen keys. | Yes | - |
| `game_id` | str | The ID of the `Game` object the factory is associated with. The game is retrieved through the `Game.get_by_id` class method. | Yes | - |

These parameters are provided by the `create_player_factory` method of the `Game` class, which is the only intended way to create a `PlayerFactory` object.

> Implementation details: at instantiation, the `Option` objects of the template are copied into the factory (they are not shared), as are their `unicity`, `hide` and `player_attribute` parameters and their frozen keys. A later modification of the template (addition, removal or replacement of an option) or of the `Option` objects it contains is not reflected in the factory, and vice versa. Each copied option receives a new ID, generated with `uuid.uuid4()`: the IDs of the factory's options are therefore distinct from those of the template's options, and must be obtained through the `options` attribute of the factory.

It has the following attributes:

| Name | Type | Description | Editable | Implementation details |
|------------|------|---------------------------------|------------|----------------------------|
| `ID` | str | Unique identifier of the factory| No | Automatically initialized with the value of `uuid.uuid4()`. |
| `options` | list[tuple[str,str]] | List of the IDs and names of the options of the factory, as (ID, name) tuples | No | A new list is created each time this attribute is read; modifying it has no impact on the options contained in the factory. |

The `PlayerFactory` class has the following methods:

- `get_option`: provides a specific option of the factory.
  - Parameters:
    - `option_id` (str): the ID of the option to get. Mandatory.
    - `context` (dict[str, str]\|`None`): the context providing the value of the runtime constants for computing the proposed value (see the "Runtime constants" paragraph of the `Option` class). Optional. Default: `None`.
  - Exceptions raised:
    - `KeyError` if the option does not exist in the factory.
  - Return value: a `dict` object with the following elements:

    | Key | Value |
    |--------|---------|
    | `entry`| an `OptionEntry` object describing the requested option, with its `unicity`, `hide` and `player_attribute` parameters and its frozen key. |
    | `exclusions`| the list of excluded values for this option, computed at the time of the call from the players present in the game. Empty list for an option created with `unicity` set to `False`. |
    | `proposed_value`| the proposed value for this option, computed at the time of the call (see below). It can be used to pre-fill an input form, and it is the value used by `create_player` if no value is provided for this option. |

> Implementation details: the proposed value is the default value of the option, as returned by the `evaluate_default` method of the `Option` object. This method is called with the context provided, supplemented by the factory with the `GAMENAME` constant (name of the associated game) if it is not already present, and with the excluded values of the option (`exclusions` parameter), so that a random draw never selects an excluded value. If the default value thus evaluated turns out to be an excluded value (according to the exclusions computed at the time of the call), then the proposed value is the next value, determined according to the type of the option:
>
> | Option type | Next value |
> |---------------|-----------------|
> | `OptionType.LIST` | The first non-excluded element of `choices`, going through the choices starting from the one following the default value, then wrapping around to the beginning of the list. |
> | `OptionType.RANGE` | The first non-excluded possible value, going through the possible values in ascending order from the default value, up to `max_value`, then if necessary in descending order below the default value, down to `min_value`. When one of the bounds is not defined, the search always succeeds, since the excluded values are finite in number. |
> | `OptionType.CHECK` | The other boolean value. |
> | `OptionType.TEXT` | `""` (empty string). |
>
> If there is no possible value left (all values are excluded, or the empty string is itself excluded for an `OptionType.TEXT` option), then the proposed value is `None`.
>
> Values are compared to the excluded values after applying the conversion rules of the `Option` class, according to the following rules, which also apply to the uniqueness check performed by the `join_game_as_player` method of the `Game` class:
>
> | Option type | Comparison rule |
> |---------------|----------------------|
> | `OptionType.RANGE` | Numeric equality: `3` and `3.0` are equal. For a decimal option, equality is evaluated with a tolerance (`math.isclose` function). |
> | `OptionType.CHECK` | Strict equality. |
> | `OptionType.LIST` | Strict equality. |
> | `OptionType.TEXT` | Equality insensitive to case and to leading and trailing whitespace: `"Alice"`, `"alice"` and `" ALICE "` are considered identical. The value carried by the player nevertheless remains the one that was chosen, without transformation. |

- `create_player`: generates a `Player` object from the values chosen for the options of the factory.
  - Parameters:
    - `values` (dict[str, any]): the chosen values, as a dictionary whose keys are the IDs of the factory's options (as provided by the `options` attribute) and whose values are the values chosen for these options. It is not necessary to provide a value for each option: an option absent from the dictionary takes its proposed value (see the `get_option` method). A `None` value means "no choice": the corresponding option is treated as if it were absent from the dictionary, and therefore takes its proposed value. Optional. Default: empty dictionary (all options take their proposed value).
    - `context` (dict[str, str]\|`None`): the context providing the value of the runtime constants, used to compute the proposed value of the options absent from the `values` dictionary (see the `get_option` method). The values provided in `values` are never evaluated as runtime constants: a string such as `"%%USERNAME%%"` is an ordinary value there. They are, however, converted according to the conversion rules of the `Option` class. Optional. Default: `None`.
  - Exceptions raised:
    - `InvalidOptionValueError` if a key of the `values` dictionary does not match any option of the factory (`reason` set to `"UNKNOWN_OPTION"`), if a value provided is not compatible with the type expected for the corresponding option (`reason` set to `"INCOMPATIBLE_TYPE"`), or if a value provided is not valid for the corresponding option (`reason` set to `"INVALID_VALUE"`).
    - `OptionValueAlreadyGivenError` if a value provided for an option created with `unicity` set to `True` is among the excluded values at the time of the call.
    - `LackingOptionError` if an option absent from the `values` dictionary has no proposed value (proposed value set to `None`), with `reason` set to `"NO_AVAILABLE_VALUE"`.
  - Return value: a `Player` object.

> Implementation details: the method does not modify the state of the factory. Creating a `Player` object does not reserve any value: the created object is only taken into account in the exclusions once it has been added to the game by the `join_game_as_player` method. Two successive or simultaneous calls to `create_player` with the same value for a unique option can therefore both succeed: it is when the players are introduced into the game that the second one will be rejected (`OptionValueAlreadyGivenError` exception). The `values` dictionary provided is not modified by the method.

- `to_dict`: provides a dictionary representation of the factory, used to save the game it is associated with.
  - Parameters: None.
  - Return value: a `dict` object with the following elements:

    | Key | Value |
    |-----|--------|
    | `factory_id` | The ID of the factory. |
    | `options` | The list of the options of the factory, in their order of definition, each in the form returned by the `to_dict` method of the `OptionEntry` class. |

- `from_dict` (class method): recreates a factory from a dictionary representation, in the format returned by the `to_dict` method, without going through a template. This method is reserved for restoring a saved game: apart from this case, a factory must be created by the `create_player_factory` method of the `Game` class.
  - Parameters:
    - `data` (dict): the representation of the factory. Mandatory.
    - `game_id` (str): the ID of the game the factory is associated with. Mandatory.
  - Implementation details: the factory and its options keep the IDs and frozen keys provided. Each option is rebuilt by the `from_dict` method of the `OptionEntry` class. The dictionary provided is not modified.
  - Exceptions raised:
    - `TypeError` or `ValueError`: if the data is malformed, or in the same cases as the `from_dict` method of the `OptionEntry` class.
    - `OptionAlreadyExistsError`: if two options of the list share the same ID or the same frozen key.
  - Return value: the created `PlayerFactory` object.

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
| `name` | str\|`None` | The name of the game. `None` if the game has no name. | Yes | Initialized with the `name` parameter. |
| `hash` | str\|`None` | The hash of the game password. `None` if the game is public (no password).| No | The hash is automatically generated from `password` with `bcrypt`. |
| `observer_hash` | str\|`None` | The hash of the observer password. `None` if no observer password is set. | No | The hash is automatically generated from `observer_password` with `bcrypt`.|
| `turn_based` | bool | `True` if the game is turn-based, `False` for simultaneous play. | No | - |
| `min_players` | int | Effective minimum number of players required to start the game (0 means no minimum). | No | Initialized with the `min_players` parameter. If that value is greater than `max_players` (when not `None`), `max_players` is returned instead. |
| `player_factory` | `PlayerFactory`\|`None` | Player factory that helps create the players of the game, and checks their parameters when they are introduced into the game. If `None`, there is neither help with creating players nor any check of their parameters when they are introduced into the game. | No | Created by the `create_player_factory` method. |
| `players` | Tuple[str] | Tuple (immutable list) of the IDs of the `Player` objects representing the players of the game. The order of the players is the order in which they take their turns in a turn-based game. Some games allow the order to change during play, so dedicated methods are provided for this purpose. Do not attempt to change the order directly through this attribute. | No | The corresponding internal variable (`_players`) is a list, converted to a tuple when exposed publicly through the `players` attribute. |
| `observers` | Tuple[str] | Tuple (immutable list) of the IDs of the `Player` objects representing the observers of the game. | No | The corresponding internal variable (`_observers`) is a list, converted to a tuple when exposed publicly through the `observers` attribute. |
| `current_player`| str | The ID of the `Player` object whose turn it is. Only meaningful for turn-based games. | No | - |
| `game_state` | `GameState` | Current state of the game. | No | - |
| `static_state` | dict | Custom game attributes, intended to store information that rarely or never changes during the game.  | Yes | Automatically initialized with the parameters declared as belonging to the `ParameterFamily.STATIC` family, but can later be extended with any other parameter of the user's choice. For example, if `Game` is instantiated with `Game([...], style=(ParameterFamily.STATIC, "blitz"), score=(ParameterFamily.DYNAMIC, "0-0"))`, then `static_state` is equal to `{"style":"blitz"}`. |
| `dynamic_state` | dict | Custom game attributes, intended to store information that may change frequently during the game. | Yes | Automatically initialized with the parameters declared as belonging to the `ParameterFamily.DYNAMIC` family, but can later be extended with any other parameter of the user's choice. For example, if `Game` is instantiated with `Game([...], style=(ParameterFamily.STATIC, "blitz"), score=(ParameterFamily.DYNAMIC, "0-0"))`, then `dynamic_state` is equal to `{"score":"0-0"}`.    |

Every `Game` object created (or restored from a save) is recorded in a global registry, indexed by its ID. This registry makes it possible to designate a game by its ID alone, for example in the `add_game` method of the `GameGroup` class.

> Implementation details: the `player_factory` attribute, when it is defined, makes it easier to create the players of the game, by making it possible to create customized players from the `PlayerFactory` class rather than creating default players from the `Player` class. Its use is not mandatory, and the `Player` objects created from this factory must be treated like any other `Player` object: they must be integrated into the game using the `join_game_as_player` method. The factory's `create_player` method does not automatically integrate them into the game. To create a player and integrate it into the game in a single operation, the `create_and_join_player` method should be used.
> However, if `player_factory` is defined, adding players with the `join_game_as_player` method checks that the `Player` object passed does meet the constraints of the factory, for the options specified in it: presence of the option, compatibility of the value's type, validity of the value, and uniqueness of the value among the players of the game for options created with the `unicity` parameter set to `True`. The details of these checks, and of the exceptions raised, are described in the `join_game_as_player` method. The list of players of the game is the only reference for the uniqueness of values: removing a player from the game automatically makes their values available again. These checks are only performed when a player is introduced: uniqueness is therefore only guaranteed at the time of the `join`, and a later modification of the values carried by the players is not checked.

The `Game` class has the following methods:

- `get_by_id` (class method): looks up an existing game from its ID.
  - Implementation details: The registry only holds weak references (`weakref.WeakValueDictionary`): it does not prevent the destruction of a `Game` object that is no longer used elsewhere.
  - Parameters:
    - `game_id` (str): the ID of the game to look up. Mandatory.
  - Return value: The corresponding `Game` object, or `None` if no existing game has this ID.
- `change_password`: changes the password of the game. The `hash` attribute of the current instance is updated with the new password using `bcrypt`.
    - Parameters:
      - `new_password` (str): the new password to use for the game. Mandatory.
    - Return value:
      - None.

- `create_player_factory`: creates a player factory from a template.
  - Description: This method creates a player factory from a template, or replaces an existing player factory. If the template is `None`, the factory is removed. Once created, the factory is stored in the `player_factory` attribute of the current instance. This method can only be used as long as the game has not started (`game_state` set to `GameState.PENDING`): creating, replacing and removing the factory are forbidden once the game has started, is paused or is finished. In addition, creating or replacing the factory (`template` parameter other than `None`) is only allowed if the game does not yet have any player: the presence of observers does not prevent the operation. Thus, all the players of the game are necessarily checked against the constraints of the factory when they are introduced. Removing the factory (`template` parameter set to `None`) remains possible when the game already has players, as long as it is in the `GameState.PENDING` state. In all forbidden cases, the `player_factory` attribute is not modified.
  - Implementation details: the factory is instantiated with the template provided and the ID of the current instance (`template` and `game_id` parameters of the `PlayerFactory` class). Since observers are ignored when computing the excluded values, their possible presence at the time the factory is created has no effect on it.
  - Parameters:
    - `template` (`PlayerFactoryTemplate`|`None`): the template to use to create the factory. Mandatory.
  - Exceptions raised:
    - `TypeError`: if the `template` parameter is not of type `PlayerFactoryTemplate` or `None`.
    - `GameAlreadyStartedError`: raised if the game is in progress (`GameState.IN_PROGRESS` or `GameState.PAUSING`).
    - `GameIsFinishedError`: raised if the game is over (`GameState.FINISHED`).
    - `GameHasPlayersError`: raised if the `template` parameter is not `None` and the game already has at least one player.
  - Return value:
      - None.

- `join_game_as_player`: joins a game as a player.
  - Description: This method lets a player join a game, given their ID or `Player` object, and a password if the game is private. It raises an exception if the player does not exist or if the password is incorrect. If the `player_factory` attribute is defined, the `Player` object is checked, and is only added if it does meet the constraints of the factory, for the options specified in it (options not handled by the factory are ignored). For each of these options, the value carried by the player (read in its `name` attribute, or in `static_state` / `dynamic_state` under the frozen key of the option) undergoes the following checks, in this order:
    1. Presence: if the value is absent from the `Player` object, or if it is `None` (which is considered as an absence of value), a `LackingOptionError` exception is raised, with `reason` set to `"ABSENT_FROM_PLAYER"`.
    2. Type: if the value is not accepted for the type of the option, according to the conversion rules of the `Option` class, an `InvalidOptionValueError` exception is raised, with `reason` set to `"INCOMPATIBLE_TYPE"`.
    3. Validity: if the value is not valid for the option (outside the `min_value` / `max_value` bounds, not matching a `step` increment, or not in `choices`), an `InvalidOptionValueError` exception is raised, with `reason` set to `"INVALID_VALUE"`.
    4. Uniqueness: for options created with the `unicity` parameter set to `True`, if the value is found in another `Player` object already introduced as a player (observers are ignored in this check), an `OptionValueAlreadyGivenError` exception is raised.

    In all these cases, the player is not added.
  - Implementation details: If successful, the method adds the ID of the `Player` object to the `_players` list of the current instance. The factory-related checks and the addition of the player to the `_players` list must be performed atomically (for example under the protection of a lock), so that two players carrying the same value of a unique option cannot be added simultaneously.
  - Parameters:
    - `player` (`Player`|str): the player joining the game, given either as the corresponding `Player` object or as a string containing their ID. Mandatory.
    - `password` (str\|`None`): password required to join the game. If the game is public, pass `None`. Optional. Default: `None`.
  - Exceptions raised:
    - `PlayerNotFoundError`: raised if the specified player does not exist.
    - `PasswordError`: raised if the password is incorrect.
    - `GameIsFullError`: raised if the maximum number of players has been reached and no more players can be added.
    - `OptionValueAlreadyGivenError`: raised if the `Player` object being introduced has an option value that is already present with the same value in another `Player` object already introduced as a player.
    - `LackingOptionError`: raised if the `Player` object being introduced does not carry a value for an option specified in the factory (`reason` set to `"ABSENT_FROM_PLAYER"`).
    - `InvalidOptionValueError`: raised if the `Player` object being introduced carries, for an option specified in the factory, a value whose type is not compatible with that of the option (`reason` set to `"INCOMPATIBLE_TYPE"`), or a value that is not valid for this option (`reason` set to `"INVALID_VALUE"`).
  - Return value: None.

- `create_and_join_player`: creates a player from the game's factory, and immediately adds it to the game as a player.
  - Description: This method chains, in a single operation, the call to the `create_player` method of the `player_factory` attribute and the call to the `join_game_as_player` method with the `Player` object thus created. Since the two steps are performed together, a player created by this method is either added to the game or discarded: there can be no player that has been created but not yet introduced, whose values would not be taken into account in the factory's exclusions. This method is the recommended way to create players when the game has a factory. The factory's `create_player` method and the `join_game_as_player` method nevertheless remain usable separately.
  - Implementation details: the creation of the player and its introduction into the game are performed under the protection of the same lock as the one used by the `join_game_as_player` method, so that no other player can be added between the computation of the exclusions and the addition of the player. If the introduction fails (for whatever reason), the created `Player` object is not returned and is not referenced anywhere: it is then destroyed, and disappears from the global player registry (which only holds weak references). If successful, the ID of the `Player` object is added to the `_players` list of the current instance, as with the `join_game_as_player` method.
  - Parameters:
    - `values` (dict[str, any]): the values chosen for the options of the factory, in the same form as the `values` parameter of the `create_player` method of the `PlayerFactory` class. Optional. Default: empty dictionary (all options take their proposed value).
    - `password` (str\|`None`): password required to join the game. If the game is public, pass `None`. Optional. Default: `None`.
    - `context` (dict[str, str]\|`None`): the context providing the value of the runtime constants, passed as is to the factory's `create_player` method. Optional. Default: `None`.
  - Exceptions raised:
    - `PlayerFactoryNotDefinedError`: raised if the `player_factory` attribute is `None`.
    - All the exceptions of the `create_player` method of the `PlayerFactory` class (`InvalidOptionValueError`, `OptionValueAlreadyGivenError`, `LackingOptionError`).
    - All the exceptions of the `join_game_as_player` method (`PasswordError`, `GameIsFullError`, `OptionValueAlreadyGivenError`, `LackingOptionError`, `InvalidOptionValueError`), except `PlayerNotFoundError`, which does not apply here since the player has just been created.
  - Return value: the `Player` object created and added to the game. It is up to the caller to attach it, where appropriate, to the user account concerned (`players_id` attribute of the `User` class).

- `remove_player`: removes a player from the game.
  - Description: This method removes a player from the game, given their ID or `Player` object. It raises an exception if the player is not found in the game.
  - Implementation details: If successful, the method removes the ID of the `Player` object from the `_players` list of the current instance. If the `player_factory` attribute is defined, no additional processing is needed: since the excluded values are computed from the players present in the game, the option values carried by the removed player automatically become available again in the factory.
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
| `games` | Tuple[str] | Tuple (immutable list) of the IDs of the `Game` objects representing the games of the group. | No | The corresponding internal variable (`_games`) is a list, converted to a tuple when exposed publicly through the `games` attribute. |
| `parameters` | dict | Customization parameters of the group. | Yes | Automatically initialized with the parameters given in `kwargs`, but can later be extended with any other parameter of the user's choice. |


The `GameGroup` class has the following methods:

- `add_game`: adds a game to the group. The game is appended to the end of the group's list of games.
  - Description: This method adds a game to the group, given its ID or `Game` object, and optionally a group administrator password. It raises an exception if the game does not exist or if the password is incorrect.
  - Implementation details: If successful, the method adds the ID of the `Game` object to the `_games` list of the current instance.
  - Parameters:
    - `game` (`Game`|str): the game to add, given either as a `Game` instance or as a string containing its ID. Mandatory.
  - Return value:
    - None.
  - Exceptions raised:
    - `GameNotFoundError`: raised if the specified game does not exist.
- `remove_game`: removes a game from the group. The game is removed from the group's list of games.
  - Parameters:
    - `game` (`Game`|str): the game to remove, given either as a `Game` instance or as a string containing its ID. Mandatory.
  - Implementation details: If successful, the method removes the ID of the `Game` object from the `_games` list of the current instance.
  - Return value:
    - None.
  - Exceptions raised:
    - `GameNotFoundInGroupError`: raised if the specified game is not in the group.

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

This file contains the logic for saving and restoring objects instantiated from the `Player`, `User`, `Game`, `GameGroup` and `PlayerFactoryTemplate` classes. `Option` and `PlayerFactory` objects are not saved on their own: they are saved within the object that contains them (see the "Saving options, templates and factories" paragraph below). It defines the `Save` class, each instance of which represents a save file and links an in-memory buffer to a persistent file (JSON document or SQLite database).

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
    - `obj` (`Player`|`User`|`Game`|`GameGroup`|`PlayerFactoryTemplate`): the instance to save. Mandatory. An `Option` or `PlayerFactory` object provided directly is not supported, and causes a `SaveError` exception.
  - Exceptions raised:
    - `SaveError`: raised if the object is not an instance of a supported class.
  - Return value: None.

- `load`: loads all instances of a given class.
  - Description: Rebuilds and returns the list of instances of the requested class from the in-memory buffer.
  - Parameters:
    - `target` (str\|type): the class to load, or its name (`Player`, `User`, `Game`, `GameGroup` or `PlayerFactoryTemplate`). Mandatory.
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

#### Saving options, templates and factories

`Option`, `PlayerFactoryTemplate` and `PlayerFactory` objects are saved according to the following rules.

**`Option` objects**: they are never saved on their own, but only within the template or factory that contains them. Within a template or a factory, each option is serialized with the parameters that were associated with it when it was added to the template, in the form returned by the `to_dict` method of the `OptionEntry` class:
- the elements of the option itself (`option_id`, `type`, `name`, `description`, `default`, `min`, `max`, `step`, `choices`), as returned by the `to_dict` method of the `Option` class. The default value is saved raw, without evaluation of any runtime constants (e.g. `"Player_%%RANDOM_NUMBER%%"`). The value `None` is represented by `null` in JSON and `NULL` in SQLite;
- the associated parameters: `unicity`, `hide`, `target` and `attribute` (representation of the `player_attribute` parameter, which makes it possible to distinguish unambiguously between an attribute of the `Player` object and a `ParameterFamily` family), and `key` (frozen key).

This representation is identical to the one used in network exchanges (see the [Client-server exchange protocol](PROTOCOLE.md), "Option representation" paragraph).

**`PlayerFactoryTemplate` objects**: they are saved on their own, like `Player`, `User`, `Game` and `GameGroup` objects, indexed by their class and ID. Each template is serialized with its ID, its name (`name`), and the ordered list of its options (with, for each one, the elements described above), in the form returned by the `to_dict` method of the `PlayerFactoryTemplate` class, and restored by its `from_dict` method.

**`PlayerFactory` objects**: they are never saved on their own, but only within the `Game` object they are associated with, in the `player_factory` element of the game. This element is `null` (JSON) or `NULL` (SQLite) when the game does not have a factory. Otherwise, the factory is serialized with its ID and the ordered list of its options (with, for each one, the elements described above), in the form returned by the `to_dict` method of the `PlayerFactory` class, and restored by its `from_dict` method. The following elements are not saved:
- the ID of the associated game, which is that of the game in which the factory is saved;
- the template from which the factory was created: since the options of the factory are independent copies of those of the template, the factory is self-sufficient, and its restoration does not depend on the presence of the template in the save;
- the excluded values of the options, which are never stored but computed from the players of the game: they are therefore automatically consistent after restoration, as long as the players of the game are restored.

> Implementation details:
> - On restoration, all IDs (of templates, factories and options) are restored identically, without being regenerated by `uuid.uuid4()`. The same goes for frozen keys, which are restored as is, even if they differ from the current name of the option.
> - Restoring an option applies the same checks as creating it (see the `Option` class), through the `from_dict` methods. If the restored data is inconsistent (unknown option type, unrecognized value of `target` or `attribute`, default value incompatible with the option, duplicate frozen keys, etc.), the exceptions raised by the `from_dict` methods (`TypeError`, `ValueError`, `OptionAlreadyExistsError`) are chained into a `SaveError` exception.
> - Restoring a `Game` object that has a factory directly recreates the `PlayerFactory` object from the saved data, by means of the `from_dict` method of the `PlayerFactory` class, without going through the `create_player_factory` method: the checks related to the state of the game and to the presence of players (`GameAlreadyStartedError`, `GameIsFinishedError` and `GameHasPlayersError` exceptions) therefore do not apply to restoration.
> - Backward compatibility: a save file produced before these objects were introduced must remain readable. A game saved without a `player_factory` element is restored with `player_factory` set to `None`, and a file that does not contain any template gives an empty list when the `PlayerFactoryTemplate` class is loaded.

### Contents of the src/multiplayer/server.py file

This file contains the logic for managing multiplayer servers.

#### Class `GameServer`
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
- **Protocol version and revision**: the server transmits the major version of the protocol (`2`) in the `version` field of every message, and rejects any message carrying another major version. It announces its protocol revision (`"2.1"`) and the list of features it offers (`["player_factory"]`) in the response to the `PROTOCOL_INFO` request, usable at the `OPEN` level before any authentication, as well as its revision in the `revision` field of the discovery response (`DISCOVERY_RESPONSE`). The revision and the list of features are defined by constants of the `server.py` module, updated with each new revision of the protocol.
- **Player factory templates**: the server holds a registry of factory templates (`PlayerFactoryTemplate` objects), indexed by their ID and shared by the whole server. These templates are exposed to clients through the `FACTORY_TEMPLATE_LIST` and `FACTORY_TEMPLATE_GET` requests (`BASE` level), and managed through the `FACTORY_TEMPLATE_CREATE`, `FACTORY_TEMPLATE_UPDATE` and `FACTORY_TEMPLATE_DELETE` requests (`ADMIN` level), described in the [Client-server exchange protocol](PROTOCOLE.md). When persistence is enabled, the registry is saved and restored along with the other server data (`PlayerFactoryTemplate` class of the `Save` object), including during on-demand saves and reloads. The creation, modification and deletion of a template are recorded in the server's audit log. A template is applied to a game only when the game is created (`factory_template_id` field of the `GAME_CREATE` request), by the `create_player_factory` method of the `Game` class: later modification or deletion of the template has no effect on games already created.
- **Creating players from a game's factory**: the `GAME_FACTORY_GET` and `GAME_FACTORY_JOIN` requests rely respectively on the `get_option` method of the `PlayerFactory` class and on the `create_and_join_player` method of the `Game` class. For each of these requests, the server itself builds the context for evaluating the runtime constants (see the "Runtime constants" paragraph of the `Option` class) from the client's session and connection: `USERNAME` (name of the authenticated user of the session, absent otherwise), `CLIENTADDRESS` (IP address of the client), `SERVERNAME` (`name` attribute of the server) and `SERVERADDRESS` (local IP address of the connection). The context is never accepted from the client. The representations of the options sent to clients are obtained through the `to_dict` method of the `OptionEntry` objects (and, for the `FACTORY_TEMPLATE_GET` request, through the `to_dict` method of the `PlayerFactoryTemplate` object). For the `FACTORY_TEMPLATE_CREATE` request, the server creates the template by means of the `from_dict` method of the `PlayerFactoryTemplate` class, without providing any ID: the template and its options receive new IDs, and the frozen key of each option is its name. For the `FACTORY_TEMPLATE_UPDATE` request, the server builds a new template in the same way, providing it with the ID of the existing template (`template_id`) and, if the options are not provided, the representation of the existing options; if successful, this new template replaces the old one in the registry. Both operations are thus atomic: in case of error, the registry is not modified. The exceptions raised by the `from_dict` methods are translated into the error codes `INVALID_OPTION` (`TypeError`, `ValueError`) and `OPTION_ALREADY_EXISTS` (`OptionAlreadyExistsError`). The exceptions raised by the library are translated into protocol error codes as follows, the attributes of the exceptions feeding the `details` field of the response: `InvalidOptionValueError` gives `INVALID_OPTION_VALUE` (with `option_id`, `value` and `reason`), `OptionValueAlreadyGivenError` gives `OPTION_VALUE_ALREADY_GIVEN` (with `option_id` and `value`), `LackingOptionError` gives `LACKING_OPTION` (with `option_id` and `reason`), and `PlayerFactoryNotDefinedError` gives `NO_PLAYER_FACTORY`. For each game that has a factory, the server also keeps up to date the list of sessions subscribed to the `GAME_FACTORY_UPDATED` notification, and sends them this notification each time a player joins or leaves the game.

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

#### Class `GameClient`
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
| `server_revision` | str\|`None` | The protocol revision announced by the server (e.g. `"2.1"`). `"2.0"` if the server does not support the `PROTOCOL_INFO` request. `None` as long as the client is not connected. | No | Automatically updated by the `connect` method. |
| `server_features` | tuple[str, ...] | The optional protocol features offered by the server (e.g. `("player_factory",)`). Empty tuple if the server does not support the `PROTOCOL_INFO` request, or as long as the client is not connected. | No | Automatically updated by the `connect` method. |

##### Methods

The `GameClient` class has the following methods:

- `discover` (class method): Searches for available servers on the local network.
  - Description: Sends a multicast discovery message over UDP and collects the responses from active servers.
  - Parameters:
    - `timeout` (float): Maximum time to wait for responses (in seconds). Optional. Default: 2.0.
    - `multicast_group` (str): The multicast address to use. Optional. Default: `"239.255.0.1"`.
    - `multicast_port` (int): The multicast port to use. Optional. Default: 65434.
  - Return value: A list of dictionaries, each containing the information of a discovered server (name, host, port, etc.), including its protocol revision (`revision` key, which is `"2.0"` if the server does not announce it).
- `connect`: Opens the TCP connection to the server.
  - Description: Attempts to open a connection to the server using the `host`, `port` and `use_tls` parameters (as well as `tls_ca_path` if provided; otherwise, the system root certificates are used). Once the connection is established, sends a `PROTOCOL_INFO` request to fill in the `server_revision` and `server_features` attributes. If the server responds with the `UNKNOWN_TYPE` error code (revision 2.0 server), `server_revision` takes the value `"2.0"` and `server_features` an empty tuple, without the connection failing.
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
- `create_player`: Creates a session player on the server.
  - Description: Sends a `PLAYER_CREATE` request and, if successful, locally creates a `Player` object reflecting the created player, with the ID assigned by the server. If a user is authenticated, the server adds the created player to the `players_id` list of their account, and the local `User` object of the session (`session_user` attribute) is updated in the same way. The custom attributes are sent to the server, which stores them in the dictionary chosen by the client (`static_state` or `dynamic_state`), and are also copied into the local `Player` object.
  - Parameters:
    - `name` (str): The name of the player to create. Mandatory.
    - `is_default` (bool): If `True`, the created player becomes the default player of the session. Optional. Default: `True`.
    - `static_attributes` (dict\|`None`): The custom attributes to store in the player's `static_state` dictionary (`static_attributes` field of the request). Optional. Default: `None` (no attribute).
    - `dynamic_attributes` (dict\|`None`): The custom attributes to store in the player's `dynamic_state` dictionary (`dynamic_attributes` field of the request). Optional. Default: `None` (no attribute).
  - Implementation details: the `static_attributes` and `dynamic_attributes` fields were introduced by revision 2.1 of the protocol. With a revision 2.0 server (`server_revision` attribute set to `"2.0"`), which would ignore these fields, the dynamic attributes are sent in the `attributes` field, which is equivalent to them; since the static attributes cannot be sent, the method then raises the `UnsupportedFeatureError` exception if `static_attributes` is provided, without sending the request.
  - Return value: The local `Player` object corresponding to the created player.
  - Exceptions raised:
    - `UnsupportedFeatureError`: if `static_attributes` is provided and the server is a revision 2.0 server (the request is then not sent).
    - `MultiplayerError` (or a subclass): if the server refuses the creation.
    - `ConnectionError`: if the client is not connected.
- `update_player`: Modifies a session player on the server.
  - Description: Sends a `PLAYER_UPDATE` request to rename the player, clear its `static_state` and `dynamic_state` dictionaries, or both. Resetting the attributes makes it possible to reuse, for another game, a player who has left their game; the server refuses it as long as the player is taking part in a game.
  - Parameters:
    - `player_id` (str): The ID of the player to modify. Mandatory.
    - `name` (str\|`None`): The new name of the player. Optional. Default: `None` (name unchanged).
    - `reset_state` (bool): If `True`, the custom attributes of the player are cleared. Optional. Default: `False`.
  - Return value: A dictionary containing the data of the server response.
  - Exceptions raised:
    - `ValueError`: if neither a new name nor a reset is requested (the request is then not sent).
    - `MultiplayerError` (or a subclass): if the server refuses the modification.
    - `ConnectionError`: if the client is not connected.
- `create_game`: Creates a game on the server.
  - Description: Sends a `GAME_CREATE` request. In particular, it makes it possible to give the game a player factory, built from a template held by the server (`factory_template_id` parameter, see the `list_factory_templates` method). The template can only be chosen when the game is created.
  - Parameters:
    - `name` (str): The name of the game. Mandatory.
    - `min_players` (int): The minimum number of players required to start the game. Optional. Default: `0`.
    - `max_players` (int\|`None`): The maximum number of players (`None` for unlimited). Optional. Default: `None`.
    - `max_observers` (int\|`None`): The maximum number of observers (`None` for unlimited). Optional. Default: `None`.
    - `turn_based` (bool): `True` if the game is turn-based. Optional. Default: `False`.
    - `password` (str\|`None`): The password required to join the game (`None` for a public game). Optional. Default: `None`.
    - `group_id` (str\|`None`): The ID of the group in which to create the game. Optional. Default: `None`.
    - `group_password` (str\|`None`): The password of the group, if needed. Optional. Default: `None`.
    - `factory_template_id` (str\|`None`): The ID of the player factory template to apply to the game (`None` for a game without a factory). Requires the `player_factory` feature of the protocol: if this parameter is provided and the feature is not in the `server_features` attribute, the `UnsupportedFeatureError` exception is raised and the request is not sent. Optional. Default: `None`.
    - `attributes` (dict\|`None`): The custom attributes of the game. Optional. Default: `None`.
  - Implementation details: parameters set to `None` are not sent in the request, except `max_players` and `max_observers`, which are explicitly sent as `null` to indicate the absence of a limit.
  - Return value: The ID of the created game.
  - Exceptions raised:
    - `UnsupportedFeatureError`: if `factory_template_id` is provided and the server does not offer the `player_factory` feature (the request is then not sent).
    - `MultiplayerError` (or a subclass): if the server refuses the creation, for example if the specified template does not exist (`FACTORY_TEMPLATE_NOT_FOUND` code).
    - `ConnectionError`: if the client is not connected.
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

The following methods make it easier to use factory templates and the player factories of games. Each one sends the corresponding protocol request and returns a dictionary containing the data of the server response (`payload` field). They all require the `player_factory` feature of the protocol (revision 2.1): before sending the request, each one checks that this feature is in the `server_features` attribute. All of them can raise the following exceptions:
- `UnsupportedFeatureError`: if the server does not offer the `player_factory` feature (the request is then not sent);
- `MultiplayerError` (or a subclass): if the server returns an error;
- `ConnectionError`: if the client is not connected.

- `list_factory_templates`: Retrieves the list of factory templates available on the server.
  - Description: Sends a `FACTORY_TEMPLATE_LIST` request. In particular, it makes it possible to offer the user a choice of template when creating a game.
  - Parameters: None.
- `get_factory_template`: Retrieves the full definition of a factory template.
  - Description: Sends a `FACTORY_TEMPLATE_GET` request.
  - Parameters:
    - `template_id` (str): The ID of the template. Mandatory.
- `create_factory_template`: Creates a factory template on the server.
  - Description: Sends a `FACTORY_TEMPLATE_CREATE` request. Requires the protocol's `ADMIN` access level.
  - Parameters:
    - `name` (str): The name of the template. Mandatory.
    - `options` (list[dict]): The list of the options of the template, each described by a dictionary in the format defined by the `FACTORY_TEMPLATE_CREATE` request (`type`, `name`, `description`, `default`, `min`, `max`, `step`, `choices`, `unicity`, `target`, `attribute`). Mandatory.
- `update_factory_template`: Modifies an existing factory template.
  - Description: Sends a `FACTORY_TEMPLATE_UPDATE` request. Requires the protocol's `ADMIN` access level.
  - Parameters:
    - `template_id` (str): The ID of the template to modify. Mandatory.
    - `name` (str\|`None`): The new name of the template. Optional. Default: `None` (name unchanged).
    - `options` (list[dict]\|`None`): The new complete list of options. Optional. Default: `None` (options unchanged).
  - Exceptions raised (in addition to those listed above):
    - `ValueError`: if `name` and `options` are both `None` (the request is then not sent).
- `delete_factory_template`: Deletes a factory template from the server.
  - Description: Sends a `FACTORY_TEMPLATE_DELETE` request. Requires the protocol's `ADMIN` access level.
  - Parameters:
    - `template_id` (str): The ID of the template to delete. Mandatory.
- `get_game_factory`: Retrieves the player factory of a game, in order to build the player creation form.
  - Description: Sends a `GAME_FACTORY_GET` request. For each option, the response provides the values already taken (`exclusions`) and the proposed value (`proposed_value`). A successful lookup subscribes the session to the game's `GAME_FACTORY_UPDATED` notification, which can be handled with the `on_notification` method.
  - Parameters:
    - `game_id` (str): The ID of the game. Mandatory.
    - `password` (str\|`None`): The password of the game, if it is private. Optional. Default: `None`.
    - `group_password` (str\|`None`): The password of a protected group containing the game, if needed. Optional. Default: `None`.
- `join_game_with_factory`: Creates a player from a game's factory and makes it join the game in a single operation.
  - Description: Sends a `GAME_FACTORY_JOIN` request. It is recommended to explicitly pass in `values` the values presented to the user, including the proposed values they did not modify.
  - Parameters:
    - `game_id` (str): The ID of the game. Mandatory.
    - `values` (dict[str, any]\|`None`): The chosen values, indexed by the ID of the factory's options. Optional. Default: `None` (all options take their proposed value).
    - `password` (str\|`None`): The password of the game, if it is private. Optional. Default: `None`.
    - `group_password` (str\|`None`): The password of a protected group containing the game, if needed. Optional. Default: `None`.
    - `is_default` (bool\|`None`): If `True`, the created player becomes the default player of the session. If `None`, the field is not sent and the server rule applies (the player becomes the default player if it is the first player of the session). Optional. Default: `None`.

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
