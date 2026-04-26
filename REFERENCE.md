**English** | [Español](translation/REFERENCE.es.md) | [Français](translation/REFERENCE.fr.md)

# API Reference for the `multiplayer` Module

This document provides a detailed reference for the public API of the `multiplayer` module.

## Main Classes

These classes are used for managing game logic, whether locally or on the server.

### `Game(name=None, max_players=None, turn_based=False, password=None, max_observers=None, **kwargs)`
Represents a single game session.

*   **`name`** (`str`, optional): The name of the game session. Defaults to `None`.
*   **`max_players`** (`int`, optional): The maximum number of players that can join. Defaults to `None` (unlimited).
*   **`max_observers`** (`int`, optional): The maximum number of observers that can join. Defaults to `None` (unlimited).
*   **`turn_based`** (`bool`, optional): `True` if the game is turn-based, `False` for simultaneous play. Defaults to `False`.
*   **`password`** (`str`, optional): A password to protect this specific game.
*   **`**kwargs`**: Custom attributes for the game (e.g., `difficulty="hard"`).

#### Methods
*   `add_player(player, password=None)`: Adds a `Player` object to the game. The `password` is required if the game is password-protected.
*   `remove_player(player_name)`: Removes a player from the game by their name.
*   `add_observer(observer)`: Adds an `Observer` object to the game.
*   `remove_observer(observer_name)`: Removes an observer from the game by their name.
*   `start()`: Starts the game.
*   `pause()`: Pauses the game.
*   `resume()`: Resumes a paused game.
*   `stop()`: Ends the game.
*   `next_turn()`: Advances to the next player in a turn-based game.

#### Properties
*   **`players`**: A list of `Player` objects in the game.
*   **`observers`**: A list of `Observer` objects in the game.
*   **`state`**: The current `GameState` of the game (e.g., `GameState.IN_PROGRESS`).
*   **`custom_state`**: A dictionary for storing any game-specific data.
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

### `Observer(name, **kwargs)`
Represents an observer.

*   **`name`** (`str`): The observer's name.
*   **`**kwargs`**: Custom attributes for the observer.

#### Properties
*   **`name`**: The observer's name.
*   **`attributes`**: A dictionary of the observer's custom attributes.

---

### `GameState` (Enum)
An enumeration for the state of the game.

*   `GameState.PENDING`
*   `GameState.IN_PROGRESS`
*   `GameState.FINISHED`

## Network Classes

These classes manage the client-server architecture.

### `GameServer(host='0.0.0.0', port=65432, password=None, admin_password=None, use_tls=False, tls_domain="localhost", tls_cert=None, tls_key=None, tls_self_signed=True, logging_host=None, logging_port=None, name=None)`
Manages game sessions and handles network requests.

*   **`host`** (`str`): The host address to bind to. Use `'0.0.0.0'` to make it accessible on the local network.
*   **`port`** (`int`): The TCP port to listen on for game commands.
*   **`password`** (`str`, optional): A global password to protect the server.
*   **`admin_password`** (`str`, optional): A password for administrative access.
*   **`use_tls`** (`bool`, optional): If `True`, enables TLS v1.3 encryption for all communications. Defaults to `False`.
*   **`tls_domain`** (`str`, optional): Domain name to include in the generated certificate. Defaults to `"localhost"`.
*   **`tls_cert`** (`str`, optional): Path to a PEM certificate file. This file must either be a "Full Chain" (including the domain certificate and intermediate certificates) or have a corresponding "chain" file in the same directory (e.g., `cert.pem` and `chain.pem`, or `ECC-cert.pem` and `ECC-chain.pem`). If only one of `tls_cert` or `tls_key` is provided while `tls_self_signed` is `False`, the server will fail to start.
*   **`tls_key`** (`str`, optional): Path to a PEM private key file. If only one of `tls_cert` or `tls_key` is provided while `tls_self_signed` is `False`, the server will fail to start.
*   **`tls_self_signed`** (`bool`, optional): If `True`, generates a self-signed certificate if `tls_cert` or `tls_key` is missing. If `False`, both `tls_cert` and `tls_key` must be provided. Defaults to `True`.
*   **`logging_host`** (`str`, optional): The host address of a logging server to send logs to.
*   **`logging_port`** (`int`, optional): The port of the logging server.
*   **`name`** (`str`, optional): A name for the server instance.

#### Methods
*   `start()`: Starts the server in a background process.
*   `stop()`: Stops the server.

---

### `GameAdmin(host='127.0.0.1', port=65432, admin_password=None, use_tls=False)`
A client class for administrators to manage a `GameServer`.

*   **`host`** (`str`): The IP address of the server.
*   **`port`** (`int`): The TCP port of the server.
*   **`admin_password`** (`str`, optional): The administrator password for the server.
*   **`use_tls`** (`bool`, optional): If `True`, the client will connect using TLS. Defaults to `False`.

#### Methods
*   `get_server_info()`: Returns information about the server (name, number of games, active game IDs).
*   `list_games()`: Returns a list of all active games on the server.
*   `kick_player(game_id, player_name)`: Removes a player from a specific game.
*   `kick_observer(game_id, observer_name)`: Removes an observer from a specific game.
*   `list_all_players()`: Returns a list of all players currently connected to the server, including their associated game ID and name.
*   `stop_server()`: Requests the server to shut down.
*   `restart_server()`: Requests the server to restart (clears all current games).
*   `set_logging_config(host, port)`: Configures the server to send its logs to a remote logging server at the specified address and port.
*   `get_cert_expiration()`: Returns the expiration date of the server's TLS certificate in ISO format.
*   `set_logging_enabled(enabled)`: Enables (`True`) or disables (`False`) logging on the server.

---

### `GameClient(host='127.0.0.1', port=65432, password=None, use_tls=False)`
The main entry point for a client to connect to a `GameServer`.

*   **`host`** (`str`): The IP address of the server.
*   **`port`** (`int`): The TCP port of the server.
*   **`password`** (`str`, optional): The global password for the server.
*   **`use_tls`** (`bool`, optional): If `True`, the client will connect using TLS. Defaults to `False`.

#### Methods
*   `discover_servers(timeout=2)` (static method): Scans the local network for running `GameServer` instances. Returns a list of `(host, port)` tuples.
*   `create_game(**game_options)`: Requests the server to create a new game. Returns a `RemoteGame` proxy object. Can include a `password` for the game.
*   `list_games()`: Returns a dictionary of all active (non-finished) games on the server.

---

### `RemoteGame`
A proxy object representing a game running on the server.

*You typically do not create this object directly, but get it from `client.create_game()`.*

#### Methods
*   `add_player(player, password=None)`: Adds a `Player` to the remote game. The `password` is required if the game is password-protected.
*   `add_observer(observer)`: Adds an `Observer` to the remote game.
*   `set_state(new_state)`: Overwrites the game's `custom_state` dictionary on the server.
*   (Other methods are the same as the local `Game` class.)

#### Properties
*   **`state`**: Returns a dictionary containing both the `GameState` and the custom state. Example: `{'status': 'in_progress', 'custom': {'score': 100}}`.
*   **`observers`**: Returns a list of `Observer` names in the game.

## Standalone Logging Server

The `multiplayer` package includes a standalone logging server that can be used to receive and display logs from multiple `GameServer` instances.

### `multiplayer-log-server [--port PORT] [--color-mode MODE]`
Starts the standalone logging server.

*   **`--port`** (`int`, optional): The TCP port to listen on. Defaults to `5000`.
*   **`--color-mode`** (`str`, optional): The coloration mode for the logs. Options are:
    *   `level`: Colors logs based on their criticality (e.g., INFO is green, ERROR is red). This is the default.
    *   `origin`: Colors logs based on the name of the logger (e.g., `GameServer`, `GameClient`, `GameAdmin`, etc.). This helps differentiate messages from different sources.

## Standalone Game Server

### `multiplayer-server [OPTIONS]`
Starts a standalone game server.

*   **`--host`** (`str`): Host address to listen on. Defaults to `0.0.0.0`.
*   **`--port`** (`int`): Port to listen on. Defaults to `65432`.
*   **`--password`** (`str`): Global server password.
*   **`--admin-password`** (`str`): Administrative password.
*   **`--use-tls`**: Enables TLS v1.3 encryption.
*   **`--tls-domain`** (`str`): Domain name for the certificate. Defaults to `localhost`.
*   **`--tls-cert`** (`str`): Path to a PEM certificate file.
*   **`--tls-key`** (`str`): Path to a PEM private key file.
*   **`--tls-cert-dir`** (`str`): Path to a directory containing PEM certificates (`cert.pem`, `RSA-cert.pem`, or `ECC-cert.pem`) and keys. This is particularly useful for Docker volumes.
*   **`--tls-self-signed`**: Generates a self-signed certificate if files are missing (default).
*   **`--no-self-signed`**: Disables automatic generation of self-signed certificates.
*   **`--name`** (`str`): Human-readable name for the server instance.

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
Suggests a random name for a game.

---

#### `suggest_player_name(category=None)`
Suggests a random name for a player.

## Exceptions

*   **`MultiplayerError`**: Base exception for all module-specific errors.
*   **`GameLogicError`**: For errors in game rules.
*   **`PlayerLimitReachedError`**: Raised when adding a player to a full game.
*   **`ObserverLimitReachedError`**: Raised when adding an observer to a game that has reached its observer limit.
*   **`GameNotFoundError`**: Raised when a client requests a game `id` that does not exist on the server.
*   **`NetworkError`**: Base exception for network-related issues.
*   **`ConnectionError`**: Raised when a client fails to connect to the server.
*   **`ServerError`**: Raised for generic errors reported by the server.
*   **`AuthenticationError`**: Raised for both server and game password authentication failu