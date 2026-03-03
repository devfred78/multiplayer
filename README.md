# Multiplayer Game Manager

This Python module provides a simple and flexible framework for managing multiplayer games, both locally and over a network.

## Features

*   **Local & Networked:** Use in a single process or in a client-server architecture.
*   **Multiple Games:** The server can manage multiple game sessions simultaneously.
*   **Flexible Configuration:** Create games with an optional maximum number of players, turn-based or simultaneous play, and custom attributes.
*   **Dynamic Attributes:** Add any custom key-value attributes to both `Game` and `Player` objects.
*   **Complete Game Lifecycle:** Manage the game's flow with `start()`, `pause()`, `resume()`, and `stop()` methods.
*   **Automatic Cleanup:** Players are automatically removed from a game when they disconnect from the server.

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

First, start the `GameServer` on your server machine. It will run in the background and manage all game sessions.

```python
from multiplayer import GameServer

# Start the server (it will run in a separate process)
server = GameServer(host='0.0.0.0', port=12345)
server.start()

# The server is now listening for client connections.
# You can stop it later with server.stop()
```

#### Client Usage

Clients can then connect to the server, create new games, or join existing ones.

```python
from multiplayer import GameClient, Player

# 1. Connect to the server
client = GameClient(host='<server-ip-address>', port=12345)

# 2. Create a new game on the server
# This returns a RemoteGame proxy object.
game = client.create_game(turn_based=True, name="My Networked Game")
print(f"Created game with ID: {game.game_id}")

# 3. (Optional) List available games on the server
available_games = client.list_games()
print("Available games on server:", available_games)

# 4. Interact with the game through the proxy
game.add_player(Player("Charlie", level=5))
game.start()

# The game logic runs on the server
current_player = game.current_player
print(f"Current player is: {current_player.name}")
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
