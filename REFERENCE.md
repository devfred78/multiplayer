# API Reference for the `multiplayer` Module

This document provides a detailed reference for the public API of the `multiplayer` module.

## Main Classes

These classes are used for managing game logic, whether locally or on the server.

### `Game(max_players=None, turn_based=False, **kwargs)`
Represents a single game session.

*   **`max_players`** (`int`, optional): The maximum number of players that can join. Defaults to `None` (unlimited).
*   **`turn_based`** (`bool`, optional): `True` if the game is turn-based, `False` for simultaneous play. Defaults to `False`.
*   **`**kwargs`**: Custom attributes for the game (e.g., `name="My Game"`).

#### Methods
*   `add_player(player)`: Adds a `Player` object to the game.
*   `remove_player(player_name)`: Removes a player from the game by their name.
*   `start()`: Starts the game.
*   `pause()`: Pauses the game.
*   `resume()`: Resumes a paused game.
*   `stop()`: Ends the game.
*   `next_turn()`: Advances to the next player in a turn-based game.

#### Properties
*   **`players`**: A list of `Player` objects in the game.
*   **`state`**: The current `GameState` of the game.
*   **`attributes`**: A dictionary of custom attributes.
*   **`current_player`**: The active `Player` object in a turn-based game.

---

### `Player(name, **kwargs)`
Represents a player.

*   **`name`** (`str`): The player's name.
*   **`**kwargs`**: Custom attributes for the player (e.g., `score=100`).

#### Properties
*   **`name`**: The player's name.
*   **`attributes`**: A dictionary of the player's custom attributes.

---

### `GameState` (Enum)
An enumeration for the state of the game.

*   `GameState.PENDING`
*   `GameState.IN_PROGRESS`
*   `GameState.FINISHED`

## Network Classes

These classes manage the client-server architecture.

### `GameServer(host='0.0.0.0', port=65432, password=None)`
Manages game sessions and handles network requests.

*   **`host`** (`str`): The host address to bind to. Use `'0.0.0.0'` to make it accessible on the local network.
*   **`port`** (`int`): The TCP port to listen on for game commands.
*   **`password`** (`str`, optional): A password to protect the server. If set, clients must provide it to connect.

#### Methods
*   `start()`: Starts the server in a background process.
*   `stop()`: Stops the server.

---

### `GameClient(host='127.0.0.1', port=65432, password=None)`
The main entry point for a client to connect to a `GameServer`.

*   **`host`** (`str`): The IP address of the server.
*   **`port`** (`int`): The TCP port of the server.
*   **`password`** (`str`, optional): The password for the server.

#### Methods
*   `discover_servers(timeout=2)` (static method): Scans the local network for running `GameServer` instances. Returns a list of `(host, port)` tuples.
*   `create_game(**game_options)`: Requests the server to create a new game. Returns a `RemoteGame` proxy object.
*   `list_games()`: Returns a dictionary of all active games on the server.

---

### `RemoteGame`
A proxy object representing a game running on the server. It has the same methods and properties as the local `Game` class, but all calls are transparently sent over the network.

*You typically do not create this object directly, but get it from `client.create_game()`.*

## Utility Functions

### Name Suggestions

#### `register_name_category(category_name, data, category_type)`
Registers a new custom category for name suggestions.

*   **`category_name`** (`str`): The name for the new category.
*   **`data`** (`list` or `str`): A list of names, or a path to a text file (one name per line).
*   **`category_type`** (`str`): `"game"` or `"player"`.

---

#### `unregister_name_category(category_name)`
Removes a custom category. Returns `True` on success.

---

#### `get_available_categories(category_type="all")`
Returns a list of available name suggestion categories.

*   **`category_type`** (`str`): `"all"`, `"game"`, or `"player"`.

---

#### `suggest_game_name(category=None)`
Suggests a random name for a game. If `category` is omitted, a random game-related category is chosen.

---

#### `suggest_player_name(category=None)`
Suggests a random name for a player. If `category` is omitted, a random player-related category is chosen.

## Exceptions

*   **`MultiplayerError`**: Base exception for all module-specific errors.
*   **`GameLogicError`**: For errors in game rules (e.g., pausing a game that is not in progress).
*   **`PlayerLimitReachedError`**: Raised when adding a player to a full game.
*   **`GameNotFoundError`**: Raised when a client requests a game `id` that does not exist on the server.
*   **`NetworkError`**: Base exception for network-related issues.
*   **`ConnectionError`**: Raised when a client fails to connect to the server.
*   **`ServerError`**: Raised for generic errors reported by the server.
*   **`AuthenticationError`**: Raised for password authentication failures.
