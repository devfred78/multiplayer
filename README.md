# Multiplayer Library V2

A Python library for managing multiplayer game sessions, users, and groups.

## Features

- **Player Management**: Create players with static and dynamic attributes.
- **User Accounts**: Authentication and role-based permissions (Player, Group Admin, Server Admin).
- **Game Sessions**: Support for turn-based and simultaneous games, private games with passwords, and observers.
- **Game Groups**: Organize multiple games into manageable groups, optionally with a game factory that creates games and enforces unique option values.
- **Factories**: Define reusable player and game factory templates, with options, exclusions and proposed values exposed to clients.
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

# Create a user account (credentials and permissions, distinct from players)
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
group.add_game(game)   # or group.add_game(game.ID)
print(group.games)     # tuple of game IDs
```

### Using Game Factories

A `GameFactoryTemplate` defines how the games of a group are created. The group factory copies its options and computes the values already taken by the games of the group.

```python
from multiplayer import OptionType
from multiplayer.game import GameFactoryTemplate, GameGroup, Option

template = GameFactoryTemplate("Tournament")
template.add_option(
    Option("Game name", OptionType.TEXT, default="Game_%%RANDOM_NUMBER%%"),
    "name",
    unicity=True,
)
template.add_option(
    Option("Max players", OptionType.RANGE, min_value=2, max_value=4, default=4),
    "max_players",
)

group = GameGroup("Summer Tournament", password="secret")
group.create_game_factory(template)

factory = group.game_factory
name_option_id = factory.options[0][0]
info = factory.get_option(name_option_id)  # entry, exclusions, proposed_value
print(info["exclusions"], info["proposed_value"])

game = group.create_and_add_game({name_option_id: "Final_1"}, password="secret")
print(game.name, group.games)  # unique names are enforced when games join the group
```

Over a network, the server can announce the `game_factory` feature. An administrator creates a game factory template, applies it to a group (`GROUP_FACTORY_SET` is also available), then clients build their creation form from `get_group_game_factory` and call `create_game(..., game_factory_values=...)`. They can subscribe to `GAME_CREATION_FACTORY_UPDATED` to refresh their form when other games take a value.

```python
# Administrator (client is a connected GameClient logged in as admin)
options = [
    {"type": "TEXT", "name": "Game name", "default": "Game_%%RANDOM_NUMBER%%",
     "unicity": True, "target": "ATTRIBUTE", "attribute": "name"},
    {"type": "RANGE", "name": "Max players", "min": 2, "max": 4, "default": 4,
     "target": "ATTRIBUTE", "attribute": "max_players"},
]
template_id = client.create_game_factory_template("Tournament", options)["template_id"]
group_id = client.send_request(
    "GROUP_CREATE", name="Summer Tournament", game_factory_template_id=template_id
)["group_id"]

# Player preparing a game
client.on_notification("GAME_CREATION_FACTORY_UPDATED", lambda n: print(n["payload"]))
form = client.get_group_game_factory(group_id)
option_id = form["options"][0]["option_id"]
game_id = client.create_game(
    "Tournament", group_id=group_id, game_factory_values={option_id: "Final_1"}
)
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
- [INSTRUCTION.md](INSTRUCTION.md): Detailed design of the library classes.
- [PROTOCOLE.md](PROTOCOLE.md): Client-server protocol, including the `game_factory` feature.
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
