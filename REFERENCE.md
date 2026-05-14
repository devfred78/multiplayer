**English** | [Español](translation/REFERENCE.es.md) | [Français](translation/REFERENCE.fr.md)

# API Reference for the `multiplayer` Module

This document provides a detailed reference for the public API of the `multiplayer` module.

## Main Classes

These classes are used for managing game logic, whether locally or on the server.

### `Game(name=None, max_players=None, turn_based=False, password=None, observer_password=None, max_observers=None, **kwargs)`
Represents a single game session.

*   **`name`** (`str`, optional): The name of the game session. Defaults to `None`.
*   **`max_players`** (`int`, optional): The maximum number of players that can join. Defaults to `None` (unlimited).
*   **`max_observers`** (`int`, optional): The maximum number of observers that can join. Defaults to `None` (unlimited).
*   **`turn_based`** (`bool`, optional): `True` if the game is turn-based, `False` for simultaneous play. Defaults to `False`.
*   **`password`** (`str`, optional): A password to protect this specific game (used for players, and for observers if `observer_password` is not set).
*   **`observer_password`** (`str`, optional): A password specifically for observers to join this game.
*   **`**kwargs`**: Custom attributes for the game (e.g., `difficulty="hard"`).

#### Methods
*   `add_player(player, password=None)`: Adds a `Player` or `PersistentPlayer` object to the game. The `password` is required if the game is password-protected.
*   `remove_player(player_id)`: Removes a player from the game by their ID.
*   `add_observer(observer, password=None)`: Adds an `Observer` or `PersistentPlayer` object to the game. The `password` is required if `observer_password` (or `password`) is set.
*   `remove_observer(observer_id)`: Removes an observer from the game by their ID.
*   `start()`: Starts the game.
*   `pause()`: Pauses the game.
*   `resume()`: Resumes a paused game.
*   `stop()`: Ends the game.
*   `next_turn()`: Advances to the next player in a turn-based game.

#### Properties
*   **`ID`**: The unique ID of the game session (read-only).
*   **`players`**: A list of `Player` objects in the game.
*   **`observers`**: A list of `Observer` objects in the game.
*   **`state`**: The current `GameState` of the game (e.g., `GameState.IN_PROGRESS`).
*   **`custom_state`**: A dictionary for storing any game-specific data.
*   **`attributes`**: A dictionary of custom attributes.
*   **`current_player`**: The active `Player` object in a turn-based game.

> **Note: `custom_state` vs `attributes`**
> - **`attributes`** (Static Metadata): Defined at creation via `**kwargs`. Used for configuration that rarely changes (e.g., `difficulty`, `map`).
> - **`custom_state`** (Dynamic State): A dictionary for the game's evolving logic (e.g., piece positions, scores). In network play, use `client.set_state()` to synchronize this across the server.

---

### `Player(name, **kwargs)`
Represents a player.

*   **`name`** (`str`): The player's name.
*   **`**kwargs`**: Custom attributes for the player (e.g., `score=100`).

#### Properties
*   **`ID`**: The unique ID of the player (read-only).
*   **`name`**: The player's name.
*   **`attributes`**: A dictionary of the player's custom attributes.

---

### `PersistentPlayer(name, password, role=PlayerRole.PLAYER, managed_groups=None, **kwargs)`
Represents a persistent player account (inherits from `Player`).

*   **`name`** (`str`): The player's name (unique on the server).
*   **`password`** (`str`): The password for the account.
*   **`role`** (`PlayerRole`, optional): The role of the player. Defaults to `PlayerRole.PLAYER`.
*   **`managed_groups`** (`list`, optional): A list of group IDs managed by this player (if role is `GROUP_ADMIN`).
*   **`**kwargs`**: Custom attributes for the player.

#### Properties
*   All properties of `Player`.
*   **`password`**: The account password.
*   **`role`**: The player's role (`PlayerRole.PLAYER`, `PlayerRole.GROUP_ADMIN`, or `PlayerRole.SERVER_ADMIN`).
*   **`managed_groups`**: List of group IDs the player can manage.

---

### `Observer(name, **kwargs)`
Represents an observer.

*   **`name`** (`str`): The observer's name.
*   **`**kwargs`**: Custom attributes for the observer.

#### Properties
*   **`ID`**: The unique ID of the observer (read-only).
*   **`name`**: The observer's name.
*   **`attributes`**: A dictionary of the observer's custom attributes.

---

### `GameGroup(name, admin_password=None, **kwargs)`
Represents a group of games on a server.

*   **`name`** (`str`): The name of the group.
*   **`admin_password`** (`str`, optional): A password for administrative actions on this group.
*   **`**kwargs`**: Additional attributes for the group.

#### Methods
*   `add_game(game)`: Adds a `Game` object to the group.
*   `remove_game(game_id)`: Removes a game from the group by its ID.

#### Properties
*   **`ID`**: The unique ID of the group (read-only).
*   **`name`**: The name of the group.
*   **`games`**: A list of `Game` objects currently in the group.
*   **`attributes`**: A dictionary of custom attributes for the group.

---

### `PlayerRole` (Enum)
An enumeration for the role of a persistent player.

*   `PlayerRole.PLAYER`: A standard player who can join and play games.
*   `PlayerRole.GROUP_ADMIN`: A player who can manage games within specific groups they are assigned to. This role includes all permissions of a `PLAYER`.
*   `PlayerRole.SERVER_ADMIN`: A player with full administrative access to the server. This role includes all permissions of a `GROUP_ADMIN` and a `PLAYER`.

---

### `GameState` (Enum)
An enumeration representing the current status of a game.

*   `GameState.PENDING`: The game has been created but not yet started. This state is dedicated to waiting for players to join. Players can join or leave.
*   `GameState.PAUSING`: The game is currently paused. This state is used when a game that was in progress is temporarily suspended.
*   `GameState.IN_PROGRESS`: The game is currently active. Moves can be made, and turn-based logic is applied.
*   `GameState.FINISHED`: The game has ended. No further moves can be made, and the results are final.

---

## Network Classes

These classes manage the client-server architecture.

### `GameServer(host='0.0.0.0', port=65432, password=None, admin_password=None, use_tls=False, tls_domain="localhost", tls_cert=None, tls_key=None, tls_self_signed=True, logging_host=None, logging_port=None, name=None, unencrypted_port=None, hidden=False)`
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
*   **`unencrypted_port`** (`int`, optional): Port for unencrypted connections when TLS is enabled.
*   **`hidden`** (`bool`, optional): If `True`, the server will not respond to network discovery requests. Defaults to `False`.

#### Methods
*   `start()`: Starts the server in a background process.
*   `stop()`: Stops the server.

---

### `GameClient(host='127.0.0.1', port=65432, password=None, use_tls=False, auth_user=None, auth_password=None)`
The main entry point for a client to connect to a `GameServer`.

*   **`host`** (`str`): The IP address of the server.
*   **`port`** (`int`): The TCP port of the server.
*   **`password`** (`str`, optional): The global password for the server.
*   **`use_tls`** (`bool`, optional): If `True`, the client will connect using TLS. Defaults to `False`.
*   **`auth_user`** (`str`, optional): The name of a persistent player account.
*   **`auth_password`** (`str`, optional): The password for the persistent player account.

#### Methods
*   `discover_servers(timeout=2)` (static method): Scans the local network for running `GameServer` instances.
    *   **Returns**: A `list` of `(host, port, name)` tuples representing the discovered servers.
*   `create_game(group_id=None, **game_options)`: Requests the server to create a new game.
    *   **`group_id`** (`str`, optional): The ID of the group where the game should be created.
    *   **`**game_options`**: Configuration options for the game. These match the `Game` class constructor arguments:
        *   `name` (`str`): The name of the game session.
        *   `max_players` (`int`): Maximum number of players allowed.
        *   `max_observers` (`int`): Maximum number of observers allowed.
        *   `turn_based` (`bool`): Whether the game is turn-based.
        *   `password` (`str`): Password required for players to join.
        *   `observer_password` (`str`): Specific password for observers.
        *   Any other keyword argument will be stored as a custom attribute in the game's `attributes` property.
    *   **Returns**: A `RemoteGame` proxy object.
*   `list_games()`: Returns all active games.
    *   **Returns**: A `dict` where keys are game IDs (`str`) and values are `RemoteGame` objects.
*   `create_group(name, admin_password=None, **attributes)`: Requests the server to create a new game group.
    *   **Returns**: A `RemoteGroup` proxy object.
*   `list_groups()`: Returns all game groups on the server.
    *   **Returns**: A `dict` where keys are group IDs (`str`) and values are `RemoteGroup` objects.
*   `create_account(name, password, role=PlayerRole.PLAYER, managed_groups=None, **attributes)`: Creates a persistent player account on the server.
    *   **Raises**: `UserAlreadyExistsError` if an account with the same name already exists.
    *   **Returns**: A `dict` representing the created player's data:
        *   `player_id` (`str`): The unique ID of the account.
        *   `name` (`str`): The account name.
        *   `role` (`PlayerRole`): The assigned role.
*   `get_server_admin()`: Returns a `ServerAdmin` instance using the client's current credentials.
    *   **Raises**: `AuthenticationError` if the client is not authenticated with a persistent account or does not have `SERVER_ADMIN` permissions.
*   `get_group_admin(group_id)`: Returns a `GroupAdmin` instance for the specified group using the client's current credentials.
    *   **Raises**: `AuthenticationError` if the client is not authenticated with a persistent account or does not have administrative permissions for the specified group.
*   `set_logging_for_client(host, port, name=None)`: Configures the client to send its logs to a remote logging server.

---

### `ServerAdmin(host='127.0.0.1', port=65432, admin_password=None, use_tls=False, auth_user=None, auth_password=None)`
A client class for administrators to manage a `GameServer` (inherits from `GameClient`).

*   All arguments and connection settings from `GameClient`.
*   **`admin_password`** (`str`, optional): The administrator password for the server (global).

#### Methods
*   All methods from `GameClient`.
*   `get_server_info()`: Returns information about the server.
    *   **Returns**: A `dict` with the following keys:
        *   `server_name` (`str`): The name assigned to the server.
        *   `games_count` (`int`): Total number of games currently on the server.
        *   `active_games` (`list` of `str`): A list of IDs for games that are not in the `FINISHED` state.
*   `kick_player(game_id, player_id)`: Removes a player from a specific game by their ID.
*   `kick_observer(game_id, observer_id)`: Removes an observer from a specific game by their ID.
*   `list_all_players()`: Lists all players currently known by the server.
    *   **Returns**: A `list` of `dict`, where each dictionary contains:
        *   `name` (`str`): The player's name.
        *   `attributes` (`dict`): The player's custom attributes.
        *   `game_id` (`str` or `None`): The ID of the game the player is currently in, or `None` if not in a game.
        *   `game_name` (`str` or `None`): The name of the game, or `None`.
        *   `connected` (`bool`): `True` if the player is currently connected to a game session.
        *   `is_persistent` (`bool`): `True` if this is a persistent account.
*   `stop_server()`: Requests the server to shut down.
*   `restart_server()`: Requests the server to restart (clears all current games).
*   `set_logging_for_server(host, port)`: Configures the server to send its logs to a remote logging server at the specified address and port.
*   `get_cert_expiration()`: Returns the expiration date of the server's TLS certificate.
    *   **Returns**: A `str` representing the expiration date in ISO format, or `None` if TLS is not used.
*   `set_logging_enabled(enabled)`: Enables (`True`) or disables (`False`) logging on the server.
*   `set_server_password(new_password)`: Sets a new password for the server.
*   `set_admin_password(new_password)`: Sets a new administrator password for the server.
*   `remove_group(group_id)`: Removes a game group from the server by its ID.
*   `set_persistent_players_enabled(enabled)`: Enables (`True`) or disables (`False`) the creation of persistent player accounts on the server. When disabled, existing persistent players remain active and usable.
*   `set_server_hidden(hidden)`: Sets the server as hidden (`True`) or visible (`False`) for network discovery.
*   `update_persistent_player(name, role=None, managed_groups=None, password=None, **attributes)`: Updates a persistent player's information.
*   `remove_persistent_player(name)`: Removes a persistent player account from the server.

---

### `GroupAdmin(group_id, host='127.0.0.1', port=65432, group_admin_password=None, use_tls=False, auth_user=None, auth_password=None)`
A client class for group administrators to manage games within a specific `GameGroup` (inherits from `GameClient`).

*   All arguments and connection settings from `GameClient`.
*   **`group_id`** (`str`): The unique ID of the group to manage.
*   **`group_admin_password`** (`str`, optional): The administrative password for this group.

#### Methods
*   All methods from `GameClient`.
*   `kick_player(game_id, player_id)`: Removes a player from a specific game in the group by their ID.
*   `kick_observer(game_id, observer_id)`: Removes an observer from a specific game in the group by their ID.
*   `set_group_admin_password(new_password)`: Sets a new administrator password for this group.

---

### `RemoteGroup`
A proxy object representing a game group running on the server.

*You typically do not create this object directly, but get it from `client.create_group()` or `client.list_groups()`.*

#### Methods
*   `create_game(**game_options)`: Creates a new game within this group. Supports the same `game_options` as `GameClient.create_game()`.
    *   **Returns**: A `RemoteGame` proxy object.
*   `list_games()`: Returns all games belonging to this group.
    *   **Returns**: A `dict` where keys are game IDs (`str`) and values are `RemoteGame` objects.

#### Properties
*   **`group_id`**: The unique ID of the group.
*   **`name`**: The name of the group.
*   **`attributes`**: A dictionary of custom attributes for the group.

---

### `RemoteGame`
A proxy object representing a game running on the server.

*You typically do not create this object directly, but get it from `client.create_game()`.*

#### Methods
*   `add_player(player, password=None)`: Adds a `Player` to the remote game. The `password` is required if the game is password-protected. If the player is a `PersistentPlayer`, the attributes provided in the `player` object will be merged with the global attributes of the account for this game session.
*   `add_observer(observer, password=None)`: Adds an `Observer` to the remote game. The `password` is required if `observer_password` (or `password`) is set for the game. If the observer is a `PersistentPlayer`, the attributes provided in the `observer` object will be merged with the global attributes of the account for this game session.
*   `set_state(new_state)`: Overwrites the game's `custom_state` dictionary on the server.
*   (Other methods are the same as the local `Game` class.)

#### Properties
*   **`state`**: Returns the current state of the remote game.
    *   **Returns**: A `dict` with:
        *   `status` (`GameState`): The enum value of the game state.
        *   `custom` (`dict`): The game's `custom_state` dictionary.
*   **`observers`**: Returns the observers currently in the game.
    *   **Returns**: A `list` of `dict`, each containing:
        *   `id` (`str`): The observer's ID.
        *   `name` (`str`): The observer's name.
        *   `attributes` (`dict`): The observer's attributes.
*   **`players`**: Returns the players currently in the game.
    *   **Returns**: A `list` of `dict`, each containing:
        *   `id` (`str`): The player's ID.
        *   `name` (`str`): The player's name.
        *   `attributes` (`dict`): The player's attributes.

## Standalone Logging Server

The `multiplayer` package includes a standalone logging server that can be used to receive and display logs from multiple `GameServer` instances.

### `multiplayer-log-server [--port PORT] [--color-mode MODE]`
Starts the standalone logging server.

*   **`--port`** (`int`, optional): The TCP port to listen on. Defaults to `5000`.
*   **`--color-mode`** (`str`, optional): The coloration mode for the logs. Options are:
    *   `level`: Colors logs based on their criticality (e.g., INFO is green, ERROR is red). This is the default.
    *   `origin`: Colors logs based on the name of the logger (e.g., `GameServer`, `GameClient`, `ServerAdmin`, etc.). This helps differentiate messages from different sources.

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
*   **`--unencrypted-port`** (`int`): Port for unencrypted connections. Only relevant when `--use-tls` is enabled. This allows the server to be reachable via both TLS and plain text on different ports.
*   **`--name`** (`str`): Human-readable name for the server instance.
*   **`--hidden`**: Hides the server from network discovery.

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
*   **`AuthenticationError`**: Raised for both server and game password authentication failures.
*   **`PlayerAlreadyInGameError`**: Raised when trying to add a player or observer that is already in the game.
*   **`GroupNotFoundError`**: Raised when a group `id` is not found on the server.

## Examples

### 1. Simple Local Game
Creating a basic game session locally without a server.

```python
from multiplayer.game import Game, Player

# Create a game and players
game = Game(name="My Chess Game", turn_based=True)

# Initialize starting game state
game.custom_state = {"board": "standard", "half_moves": 0}

alice = Player("Alice")
bob = Player("Bob")

# Add players and start
game.add_player(alice)
game.add_player(bob)
game.start()

print(f"Game '{game.name}' started with state: {game.state}")
```

### 2. Connecting to a Server and Creating an Account
Connecting to a remote game server and setting up a persistent account.

```python
from multiplayer.client import GameClient
from multiplayer.data import PlayerRole

client = GameClient(host="localhost", port=65432)
client.connect()

# Create a persistent account
account = client.create_account(
    name="Charlie", 
    password="secure_password", 
    role=PlayerRole.PLAYER
)
print(f"Account created for {account['name']} with role {account['role']}")

client.disconnect()
```

### 3. Group and Game Management (Admin)
Creating a group and a game session as a Group Admin.

```python
from multiplayer.client import GameClient

client = GameClient(host="localhost", port=65432)
client.connect(password="server_pass")

# Login as group admin
admin = client.login("AdminUser", "admin_pass")

# Create a group and a game inside it
group = admin.create_group("Tournament A")
remote_game = group.create_game(name="Final Match", max_players=2)

print(f"Game '{remote_game.ID}' created in group '{group.name}'")
```

### 4. Turn-Based Game with Observers
Managing a turn-based game with spectators on the server.

```python
from multiplayer.client import GameClient
from multiplayer.game import Player

client = GameClient(host="localhost", port=65432)
client.connect()

# Get the list of active games from the server
active_games = client.list_games()
print(f"Active games on server: {list(active_games.keys())}")

# Join the first active game as a player
game_id = list(active_games.keys())[0]
remote_game = active_games[game_id]
me = Player("Dave")
remote_game.add_player(me)

# Advance turn (if it's your turn)
if remote_game.current_player.name == "Dave":
    remote_game.next_turn()

# List observers
for obs in remote_game.observers:
    print(f"Spectator: {obs['name']}")
```

### 5. Advanced: TLS, Custom Attributes, and Logging
Using encryption, metadata, and the standalone logging server.

```python
from multiplayer.client import GameClient
from multiplayer.game import Game

# Connect using TLS
client = GameClient(host="game.example.com", port=65432, use_tls=True)
client.connect()

# Create a game with custom metadata
game_options = {
    "name": "Pro League",
    "difficulty": "expert",
    "map": "valles_marineris"
}
remote_game = client.create_game(**game_options)

# Logs are automatically sent to the log server 
# if the GameServer was configured with --port
print(f"Game attributes: {remote_game.attributes}")
```

### 6. Server Management
This example shows how to launch and manage a game server.

```python
import time
from multiplayer.server import GameServer

# Initialize the server
# host: "0.0.0.0" to listen on all interfaces
# port: 65432 (default)
# password: Optional password to join the server
# admin_password: Required password for ServerAdmin and GroupAdmin
server = GameServer(
    host="0.0.0.0",
    port=65432,
    password="player_pass",
    admin_password="admin_super_secret",
    name="My Professional Game Server",
    use_tls=True,
    tls_self_signed=True
)

# Start the server (runs in a separate process)
server.start()

try:
    print("Server is running. Press Ctrl+C to stop.")
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Stopping server...")
finally:
    # Gracefully stop the server
    server.stop()
```
                                                                    Virus Database File
Version: 8.21.0.64
FUP: 0
License date: 12.5.2026
VDF date: 12.5.2026
Minimum engine: 8.3.0.0
Signatures: 7721
Required linked VDF: 