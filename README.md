# Multiplayer Library V2

A Python library for managing multiplayer game sessions, users, and groups.

## Features

- **Player Management**: Create players with static and dynamic attributes.
- **User Accounts**: Authentication and role-based permissions (Player, Group Admin, Server Admin).
- **Game Sessions**: Support for turn-based and simultaneous games, private games with passwords, and observers.
- **Game Groups**: Organize multiple games into manageable groups.
- **Persistence**: Save and restore your game state using JSON or SQLite formats.
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
from multiplayer import ParameterFamily, PlayerRole

# Create a player with attributes
player = Player("Alice", score=(ParameterFamily.DYNAMIC, 0), team=(ParameterFamily.STATIC, "Red"))

# Create a user account associated with the player
user = User(username="alice_92", password="secret_password", role=PlayerRole.PLAYER)
```

### Managing Games

```python
from multiplayer.game import Game
from multiplayer.utils import suggest_name

# Create a turn-based game with a suggested name
game_name = suggest_name("egyptian_gods")
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

## Documentation

For more detailed information, please refer to:
- [REFERENCE.md](REFERENCE.md): Full API reference.

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
