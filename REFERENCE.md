**English** | [Español](translation/REFERENCE.es.md) | [Français](translation/REFERENCE.fr.md)

# API Reference for the `multiplayer` Module

This document provides a detailed reference for the public API of the `multiplayer` module.

## Main Classes

### `Game(max_players=None, turn_based=False, password=None, **kwargs)`
Represents a single game session.
*   **`max_players`** (`int`, optional): The maximum number of players that can join.
*   **`turn_based`** (`bool`, optional): `True` if the game is turn-based.
*   **`password`** (`str`, optional): A password to protect this specific game.
*   **`**kwargs`**: Custom attributes for the game.

#### Properties
*   **`state`**: The current `GameState` of the game.
*   **`custom_state`**: A dictionary for storing any game-specific data.

### `Player(name, **kwargs)`
Represents a player.
*   **`name`** (`str`): The player's name.
*   **`**kwargs`**: Custom attributes for the player.

### `GameState` (Enum)
*   `GameState.PENDING`, `GameState.IN_PROGRESS`, `GameState.FINISHED`

## Network Classes

### `GameServer(host='0.0.0.0', port=65432, password=None, use_tls=False)`
Manages game sessions and handles network requests.
*   **`password`** (`str`, optional): A global password to protect the server.
*   **`use_tls`** (`bool`, optional): If `True`, enables TLS v1.3 encryption.

### `GameClient(host='127.0.0.1', port=65432, password=None, use_tls=False)`
The main entry point for a client to connect to a `GameServer`.
*   **`password`** (`str`, optional): The global password for the server.
*   **`use_tls`** (`bool`, optional): If `True`, the client will connect using TLS.

#### Methods
*   `discover_servers(timeout=2)` (static method): Scans the local network for running `GameServer` instances.
*   `create_game(**game_options)`: Requests the server to create a new game. Returns a `RemoteGame` proxy object.
*   `list_games()`: Returns a dictionary of all active (non-finished) games on the server.

### `RemoteGame`
A proxy object representing a game running on the server.

#### Methods
*   `add_player(player, password=None)`: Adds a `Player` to the remote game.
*   `set_state(new_state)`: Overwrites the game's `custom_state` dictionary on the server.

#### Properties
*   **`state`**: Returns a dictionary containing both the `GameState` and the custom state. Example: `{'status': 'in_progress', 'custom': {'score': 100}}`.

## Utility Functions

### Name Suggestions

#### `register_name_category(category_name, data, category_type)`
Registers a new custom category for name suggestions.
*   **`category_name`** (`str`): The name for the new category.
*   **`data`** (`list` or `str`): A list of names, or a path to a text file.
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
Suggests a random name for a game.

---

#### `suggest_player_name(category=None)`
Suggests a random name for a player.

## Exceptions

*   **`MultiplayerError`**: Base exception for all module-specific errors.
*   **`GameLogicError`**: For errors in game rules.
*   **`PlayerLimitReachedError`**: Raised when adding a player to a full game.
*   **`GameNotFoundError`**: Raised when a client requests a game `id` that does not exist on the server.
*   **`NetworkError`**: Base exception for network-related issues.
*   **`ConnectionError`**: Raised when a client fails to connect to the server.
*   **`ServerError`**: Raised for generic errors reported by the server.
*   **`AuthenticationError`**: Raised for both server and game password authentication failures.
