# Multiplayer Game Manager

This Python module provides a simple and flexible framework for managing multiplayer games, both locally and over a network.

## Features

*   **Local & Networked:** Use in a single process or in a client-server architecture.
*   **Automatic Server Discovery:** Clients can automatically find running servers on the local network.
*   **Extensible Name Suggestions:** Includes a utility function to suggest creative names for games and players from various built-in or custom categories.
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

### Name Suggestions

The module can suggest names for games and players, either randomly or from a specific category. You can also register your own custom categories.

#### Basic Usage
```python
from multiplayer import suggest_game_name, suggest_player_name, get_available_categories

# Suggest a random game name from any built-in game-related category
random_game_name = suggest_game_name()
print(f"Random game name: {random_game_name}")

# Suggest a name from a specific category
print(f"Game categories: {get_available_categories('game')}")
specific_game_name = suggest_game_name("cities")
print(f"Specific game name: {specific_game_name}")
```

#### Advanced Usage: Custom Categories
You can register your own categories from a list or a file path.

```python
from multiplayer import register_name_category, suggest_player_name

# Register a custom category from a list
my_heroes = ["Aragorn", "Gandalf", "Legolas"]
register_name_category("my_heroes", my_heroes, "player")

# Register a custom category from a file (one name per line)
# with open("my_locations.txt", "w") as f:
#     f.write("The Shire\nRivendell\n")
# register_name_category("my_locations", "my_locations.txt", "game")

# Use the new custom category
new_player_name = suggest_player_name("my_heroes")
print(f"Custom player name: {new_player_name}")
```

### Local Usage

For simple, single-process applications, you can use the `Game` class directly.

```python
from multiplayer import Game, Player, suggest_game_name, suggest_player_name

# Create a new turn-based game with a random name
game = Game(max_players=4, turn_based=True, name=suggest_game_name())

# Add players with random names
game.add_player(Player(suggest_player_name(), score=100))
game.add_player(Player(suggest_player_name("egyptian_gods"), score=50)) # From a specific category

# Start the game
game.start()
```

### Networked Usage (Client-Server)

For games running on different machines, you can use the client-server architecture.

#### Server Setup
```python
from multiplayer import GameServer

server = GameServer(host='0.0.0.0', port=12345)
server.start()
```

#### Client Usage
```python
from multiplayer import GameClient, Player, suggest_game_name, suggest_player_name

# 1. Discover servers on the network
servers = GameClient.discover_servers()
if not servers:
    print("No servers found.")
else:
    host, port = servers[0]
    client = GameClient(host=host, port=port)

    # 2. Create a new game with a suggested name
    game = client.create_game(turn_based=True, name=suggest_game_name())

    # 3. Add a player with a suggested name
    player_name = suggest_player_name()
    game.add_player(Player(player_name, level=5))

    print(f"Player '{player_name}' joined game '{game.attributes['name']}'")
    game.start()
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
    servers = GameClient.discover_servers(timeout=1)
    if not servers:
        raise ConnectionError("No servers found on the network.")

    client = GameClient(*servers[0])
    game = client.create_game(max_players=1)
    game.add_player(Player("Alice"))
    game.add_player(Player("Bob")) # This line is expected to fail

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
