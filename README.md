**English** | [Español](translation/README.es.md) | [Français](translation/README.fr.md)

# Multiplayer Game Manager

> **A Note on this Project's Origin**
>
> This project is primarily the result of a series of experiments using Gemini Code Assist for code generation and error handling. Rather than using it on academic examples, it seemed more interesting to apply it to a project that could meet a real practical need.
>
> This, therefore, is the reason for `multiplayer`'s existence: you can dissect the code to see how Gemini (with my guidance) went about building it, or you can ignore all that and just use this library for your own needs!

This Python module provides a simple and flexible framework for managing multiplayer games, both locally and over a network.

For a detailed technical description of all classes and functions, see the [API Reference](REFERENCE.md).

## Features

*   **Local & Networked:** Use in a single process or in a client-server architecture.
*   **Combined Game State:** A flexible system for synchronizing both the core game status (e.g., `in_progress`) and any custom game data.
*   **Multi-Layered Security:** Supports both server-wide passwords and per-game passwords, with optional TLS v1.3 encryption.
*   **Automatic Server Discovery:** Clients can automatically find running servers on the local network.
*   **Extensible Name Suggestions:** Includes a utility function to suggest creative names for games and players.
*   **Multiple Games:** The server can manage multiple game sessions simultaneously, and the game list is now filtered to hide finished games.
*   **Robust Error Handling:** A clear set of custom exceptions for both game logic and network issues.

## Installation

This module requires the `cryptography` library for its security features.

```sh
pip install multiplayer-0.1.0-py3-none-any.whl
```
*Replace `multiplayer-0.1.0-py3-none-any.whl` with the actual name of the downloaded file.*

## Usage

### Game State Management

A key feature is the ability to manage your own game state alongside the core game status.

```python
# On one client, set a custom state
game.set_state({
    "board": [["X", "O", ""], ["", "X", ""], ["O", "", ""]],
    "turn": "player2"
})

# On another client, retrieve the combined state
full_state = game.state
print(f"Game status: {full_state['status']}")
# > Game status: in_progress

print(f"Current turn: {full_state['custom']['turn']}")
# > Current turn: player2
```


### Full Test Environment

A script is available to launch a complete test environment with:
- An IPC log server (`IPClogging`) in a separate window.
- A game server.
- Multiple separate client instances (default is 2) simulating a game, each in its own terminal window.

To run it:
```bash
uv run python scripts/full_test_env.py
```

To specify the number of players:
```bash
uv run python scripts/full_test_env.py --players 3
```
This will open several Windows Terminal windows: one for the log server and one for each client instance, allowing you to see the real-time interactions and logs.

### Local Usage

You can use the `Game` class directly, including with a password for local validation.

```python
from multiplayer import Game, Player, suggest_game_name

game = Game(password="local_game_pass")
game.add_player(Player("Alice"), password="local_game_pass")
game.start()
```

### Networked Usage (Client-Server)

#### Server Setup
```python
from multiplayer import GameServer

# Start a secure server
server = GameServer(
    host='0.0.0.0',
    port=12345,
    password="my_server_password",
    use_tls=True
)
server.start()
```

#### Client Usage
```python
from multiplayer import GameClient, Player, suggest_game_name

# 1. Discover and connect to the server
servers = GameClient.discover_servers()
if not servers:
    print("No servers found.")
else:
    host, port = servers[0]
    client = GameClient(
        host=host,
        port=port,
        password="my_server_password",
        use_tls=True
    )

    # 2. Create a private game
    private_game = client.create_game(
        name=suggest_game_name(),
        password="my_game_password"
    )

    # 3. A player joins and sets the initial state
    private_game.add_player(Player("Charlie"), password="my_game_password")
    private_game.set_state({"score": 0})
    private_game.start()
```

## Error Handling

The module provides a set of custom exceptions, including `AuthenticationError` for both server and game passwords.

```python
from multiplayer import GameClient
from multiplayer.exceptions import ConnectionError, AuthenticationError

try:
    # ... connect to client ...

    # Try to join a game with the wrong password
    game.add_player(Player("Eve"), password="wrong_game_password")

except AuthenticationError as e:
    print(f"Authentication failed as expected: {e}")
except ConnectionError as e:
    print(f"A connection or discovery error occurred: {e}")
```

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for more details on how to get started.

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
