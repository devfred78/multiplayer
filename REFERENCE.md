# API Reference for the `multiplayer` Module

This document provides a detailed reference for the public API of the `multiplayer` module.

## Main Classes

These classes are used for managing game logic, whether locally or on the server.

### `Game(max_players=None, turn_based=False, password=None, **kwargs)`
Represents a single game session.

*   **`max_players`** (`int`, optional): The maximum number of players that can join. Defaults to `None` (unlimited).
*   **`turn_based`** (`bool`, optional): `True` if the game is turn-based, `False` for simultaneous play. Defaults to `False`.
*   **`password`** (`str`, optional): A password to protect this specific game.
*   **`**kwargs`**: Custom attributes for the game (e.g., `name="My Game"`).

#### Methods
*   `add_player(player, password=None)`: Adds a `Player` object to the game. The `password` is required if the game is password-protected.
*   `remove_player(player_name)`: Removes a player from the game by their name.
*   `start()`: Starts the game.
*   `pause()`: Pauses the game.
*   `resume()`: Resumes a paused game.
*   `stop()`: Ends the game.
*   `next_turn()`: Advances to the next player in a turn-based game.

#### Properties
*   **`players`**: A list of `Player` objects in the game.
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

### `GameState` (Enum)
An enumeration for the state of the game.

*   `GameState.PENDING`
*   `GameState.IN_PROGRESS`
*   `GameState.FINISHED`

## Network Classes

These classes manage the client-server architecture.

### `GameServer(host='0.0.0.0', port=65432, password=None, use_tls=False)`
Manages game sessions and handles network requests.

*   **`host`** (`str`): The host address to bind to. Use `'0.0.0.0'` to make it accessible on the local network.
*   **`port`** (`int`): The TCP port to listen on for game commands.
*   **`password`** (`str`, optional): A global password to protect the server.
*   **`use_tls`** (`bool`, optional): If `True`, enables TLS v1.3 encryption for all communications. Defaults to `False`.

#### Methods
*   `start()`: Starts the server in a background process.
*   `stop()`: Stops the server.

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
*   `list_games()`: Returns a dictionary of all active games on the server.

---

### `RemoteGame`
A proxy object representing a game running on the server.

*You typically do not create this object directly, but get it from `client.create_game()`.*

#### Methods
*   `add_player(player, password=None)`: Adds a `Player` to the remote game. The `password` is required if the game is password-protected.
*   `set_state(new_state)`: Overwrites the game's `custom_state` dictionary on the server.
*   (Other methods are the same as the local `Game` class.)

#### Properties
*   **`state`**: Returns the game's `custom_state` dictionary from the server. **Note:** This is a breaking change from v0.5.2. It no longer returns the `GameState` enum.

## Utility Functions

### Name Suggestions

(This section remains the same)

## Exceptions

(This section remains the same)
