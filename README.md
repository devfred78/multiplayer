# Multiplayer Game Manager

This Python module provides a simple and flexible framework for managing multiplayer games, both locally and over a network.

For a detailed technical description of all classes and functions, see the [API Reference](REFERENCE.md).

## Features

*   **Local & Networked:** Use in a single process or in a client-server architecture.
*   **Secure Communications:** Supports password protection and TLS v1.3 encryption for all network traffic.
*   **Automatic Server Discovery:** Clients can automatically find running servers on the local network.
*   **Extensible Name Suggestions:** Includes a utility function to suggest creative names for games and players.
*   **Multiple Games:** The server can manage multiple game sessions simultaneously.
*   **Robust Error Handling:** A clear set of custom exceptions for both game logic and network issues.

## Installation

This module requires the `cryptography` library for its security features.

```sh
pip install multiplayer-0.1.0-py3-none-any.whl
```
*Replace `multiplayer-0.1.0-py3-none-any.whl` with the actual name of the downloaded file.*

## Usage

### Local Usage

For simple, single-process applications, you can use the `Game` class directly.

```python
from multiplayer import Game, Player, suggest_game_name

game = Game(max_players=4, turn_based=True, name=suggest_game_name())
game.add_player(Player("Alice", score=100))
game.start()
```

### Networked Usage (Client-Server)

For games running on different machines, you can use the client-server architecture with optional security.

#### Server Setup
You can start a server with a password and/or TLS encryption.

```python
from multiplayer import GameServer

# Start a secure server with a password and TLS encryption
server = GameServer(
    host='0.0.0.0',
    port=12345,
    password="my_secret_password",
    use_tls=True
)
server.start()
```

#### Client Usage
Clients must use the same security settings as the server.

```python
from multiplayer import GameClient, Player, suggest_game_name

# 1. Discover servers on the network
servers = GameClient.discover_servers()
if not servers:
    print("No servers found.")
else:
    host, port = servers[0]

    # 2. Connect to the server with the correct password and TLS enabled
    client = GameClient(
        host=host,
        port=port,
        password="my_secret_password",
        use_tls=True
    )

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
    client = GameClient(*servers[0], password="wrong_password", use_tls=True)
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
