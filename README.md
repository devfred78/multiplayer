# Multiplayer Game Manager

This Python module provides a simple and flexible framework for managing multiplayer games, both locally and over a network.

## Features

*   **Local & Networked:** Use in a single process or in a client-server architecture.
*   **Automatic Server Discovery:** Clients can automatically find running servers on the local network.
*   **Multiple Games:** The server can manage multiple game sessions simultaneously.
*   **Flexible Configuration:** Create games with an optional maximum number of players, turn-based or simultaneous play, and custom attributes.
*   **Dynamic Attributes:** Add any custom key-value attributes to both `Game` and `Player` objects.
*   **Complete Game Lifecycle:** Manage the game's flow with `start()`, `pause()`, `resume()`, and `stop()` methods.
*   **Robust Error Handling:** A clear set of custom exceptions for both game logic and network issues.

## Installation

To install the module, download the `.whl` file from the release page and run the following command:

```sh
pip install multiplayer-0.1.0-py3-none-any.whl
```
*Replace `multiplayer-0.1.0-py3-none-any.whl` with the actual name of the downloaded file.*

## Usage

You can use this module in two ways: locally for a single-process application, or in a client-server architecture for networked games.

### 1. Local Usage

For simple, single-process applications, you can use the `Game` class directly.

```python
from multiplayer import Game, Player

# Create a new turn-based game
game = Game(max_players=4, turn_based=True, name="My Local Game")

# Add players
game.add_player(Player("Alice", score=100))
game.add_player(Player("Bob", score=50))

# Start the game
game.start()

# Access game state and players directly
print(f"Current player: {game.current_player.name}")
game.next_turn()
print(f"Next player: {game.current_player.name}")
```

### 2. Networked Usage (Client-Server)

For games running on different machines, you can use the client-server architecture.

#### Server Setup

First, start the `GameServer` on your server machine. It will run in the background, manage all game sessions, and be discoverable on the local network.

```python
from multiplayer import GameServer

# Start the server (it will run in a separate process)
# Using host='0.0.0.0' makes it accessible from other machines on the network.
server = GameServer(host='0.0.0.0', port=12345)
server.start()

# The server is now listening for client connections.
# You can stop it later with server.stop()
```

#### Client Usage

Clients can now automatically discover and connect to the server.

```python
from multiplayer import GameClient, Player

# 1. Discover servers on the network
print("Searching for servers...")
servers = GameClient.discover_servers()

if not servers:
    print("No servers found.")
else:
    host, port = servers[0]
    print(f"Found server at {host}:{port}")

    # 2. Connect to the first discovered server
    client = GameClient(host=host, port=port)

    # 3. Create a new game on the server
    game = client.create_game(turn_based=True, name="My Networked Game")
    print(f"Created game with ID: {game.game_id}")

    # 4. Interact with the game through the proxy
    game.add_player(Player("Charlie", level=5))
    game.start()

    current_player = game.current_player
    print(f"Current player is: {current_player.name}")
```

## Error Handling

The module provides a set of custom exceptions to handle specific errors gracefully.

```python
from multiplayer import GameClient, Player
from multiplayer.exceptions import (
    ConnectionError,
    GameLogicError,
    PlayerLimitReachedError,
    GameNotFoundError
)

try:
    # Discover and connect to a server
    servers = GameClient.discover_servers(timeout=1)
    if not servers:
        raise ConnectionError("No servers found on the network.")

    client = GameClient(*servers[0])

    # Try to create a game with a limit of 1 player
    game = client.create_game(max_players=1)

    game.add_player(Player("Alice"))
    print("Alice joined the game.")

    # This next line is expected to fail
    game.add_player(Player("Bob"))

except PlayerLimitReachedError as e:
    print(f"As expected, the game is full: {e}")
except GameLogicError as e:
    print(f"A game logic error occurred: {e}")
except GameNotFoundError as e:
    print(f"The requested game was not found on the server: {e}")
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
