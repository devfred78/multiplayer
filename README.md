# Multiplayer Library V2

A Python library for managing multiplayer game sessions, users, and groups.

## Features

- **Player Management**: Create players with static and dynamic attributes.
- **User Accounts**: Authentication and role-based permissions (Player, Group Admin, Server Admin).
- **Game Sessions**: Support for turn-based and simultaneous games, private games with passwords, and observers.
- **Game Groups**: Organize multiple games into manageable groups.
- **Persistence**: Save and restore your game state using JSON or SQLite formats.
- **Networking**: Client-Server architecture using TCP with optional TLS 1.3 encryption, automatic server discovery, and real-time notifications.
- **Name Suggestions**: Built-in utility to suggest random names for players and games from various categories.

## Installation

Install the library using `pip`:

```bash
pip install multiplayer
```

Alternatively, you can install it by downloading the `.whl` file from the [Releases](https://github.com/devfred78/multiplayer/releases) section of the GitHub repository:

```bash
pip install multiplayer-2.0.0-py3-none-any.whl
```

## Quick Start

### Creating a Player and User

```python
from multiplayer.game import Player, User
from multiplayer import ParameterFamily

# Create a player with attributes
player = Player("Alice", score=(ParameterFamily.DYNAMIC, 0), team=(ParameterFamily.STATIC, "Red"))

# Create a user account associated with its own player profile
user = User(username="alice_92", password="secret_password", email="alice@example.com")
```

### Managing Games

```python
from multiplayer.game import Game
from multiplayer.utils import suggest_game_name

# Create a turn-based game with a suggested name
game_name = suggest_game_name("cities")
game = Game(name=game_name, turn_based=True)

# Join and start the game
game.join_game_as_player(player)
game.start()
```

### Using Game Groups

```python
from multiplayer.game import GameGroup

# Organize multiple games
group = GameGroup(name="Summer Tournament")
group.add_game(game)
```

### Persistence

```python
from pathlib import Path
from multiplayer.save import Save
from multiplayer import SaveFormat

# Initialize a save file (JSON or SQLite)
save_handler = Save(file_path=Path("savegame.json"), save_format=SaveFormat.JSON)

# Save an object
save_handler.save(game)
save_handler.flush()  # Effective write to disk

# Load objects
loaded_games = save_handler.load("Game")
```

### Networking

#### Starting a Server

```python
import asyncio
from multiplayer.server import GameServer

async def main():
    # Create and start a discoverable server
    server = GameServer(name="Battle Server", discoverable=True)
    await server.start()
    try:
        await asyncio.Event().wait()
    finally:
        await server.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
```

#### Connecting a Client

```python
from multiplayer.client import GameClient

# Connect to a server
client = GameClient(host="127.0.0.1")
try:
    client.connect()

    # Register a notification handler
    client.on_notification("GAME_EVENT", lambda p: print(f"Received event: {p}"))

    # Create a player for this client session
    player = client.create_player("Alice")
    print(f"Connected as {player.name}")
finally:
    client.disconnect()
```

For a command-line server, run `uv run python scripts/run_server.py --help`.
Press `CTRL+C` to stop it cleanly.

## Documentation

For more detailed information, please refer to:
- [REFERENCE.md](REFERENCE.md): Full API reference.
- [INSTALL_DOCKER_CONTAINER_SYNOLOGY_DSM71.md](INSTALL_DOCKER_CONTAINER_SYNOLOGY_DSM71.md): Install the Docker image on Synology DSM 7.1, including data and TLS certificate volume mappings.

## Development

The project uses [uv](https://github.com/astral-sh/uv) for dependency management.

```bash
# Install development dependencies
uv sync

# Run quality checks and tests
uv run python scripts/check_project.py
uv run pytest
```

## License

See `LICENSE.md` for details.
