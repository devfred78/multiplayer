# Multiplayer Game Manager

This Python module provides a simple and flexible framework for managing multiplayer games, both locally and over a network.

For a detailed technical description of all classes and functions, see the [API Reference](REFERENCE.md).

## Features

*   **Local & Networked:** Use in a single process or in a client-server architecture.
*   **Password-Protected Servers:** Secure your game server with a simple password.
*   **Automatic Server Discovery:** Clients can automatically find running servers on the local network.
*   **Extensible Name Suggestions:** Includes a utility function to suggest creative names for games and players from various built-in or custom categories.
*   **Multiple Games:** The server can manage multiple game sessions simultaneously.
*   **Flexible Configuration:** Create games with an optional maximum number of players, turn-based or simultaneous play, and custom attributes.
*   **Robust Error Handling:** A clear set of custom exceptions for both game logic and network issues.

## Installation

To install the module, download the `.whl` file from the release page and run the following command:

```sh
pip install multiplayer-0.1.0-py3-none-any.whl
```
*Replace `multiplayer-0.1.0-py3-none-any.whl` with the actual name of the downloaded file.*

## Usage

### Name Suggestions

The module can suggest names for games and players. See the [API Reference](REFERENCE.md) for advanced usage.

```python
from multiplayer import suggest_game_name, suggest_player_name

# Suggest a random game name and player name
game_name = suggest_game_name()
player_name = suggest_player_name()
```

### Local Usage

For simple, single-process applications, you can use the `Game` class directly.

```python
from multiplayer import Game, Player, suggest_game_name

game = Game(max_players=4, turn_based=True, name=suggest_game_name())
game.add_player(Player("Alice", score=100))
game.start()
```

### Networked Usage (Client-Server)

For games running on different machines, you can use the client-server architecture.

#### Server Setup
You can start a server with or without a password.

```python
from multiplayer import GameServer

# Start a password-protected server
server = GameServer(host='0.0.0.0', port=12345, password="my_secret_password")
server.start()
```

#### Client Usage
Clients must provide the correct password to connect.

```python
from multiplayer import GameClient, Player, suggest_game_name

# 1. Discover servers on the network
servers = GameClient.discover_servers()
if not servers:
    print("No servers found.")
else:
    host, port = servers[0]

    # 2. Connect to the server with the password
    client = GameClient(host=host, port=port, password="my_secret_password")

    # 3. Create a new game
    game = client.create_game(turn_based=True, name=suggest_game_name())

    # 4. Add a player and start
    game.add_player(Player("Charlie", level=5))
    game.start()
```

## Error Handling

The module provides a set of custom exceptions, including `AuthenticationError`.

```python
from multiplayer import GameClient
from multiplayer.exceptions import ConnectionError, AuthenticationError

try:
    servers = GameClient.discover_servers(timeout=1)
    if not servers:
        raise ConnectionError("No servers found.")

    # Try to connect with the wrong password
    client = GameClient(*servers[0], password="wrong_password")
    client.list_games()

except AuthenticationError as e:
    print(f"Authentication failed as expected: {e}")
except ConnectionError as e:
    print(f"A connection or discovery error occurred: {e}")
```

## Running Tests

To run the unit tests, you will need to have `pytest` installed.

```sh
pip install pytest
```

Then, you can run the tests from the root of the project:

```sh
pytest
```

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.
