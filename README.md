# Multiplayer Library V2

A Python library for managing multiplayer game sessions, users, and groups.

## Features

- **Player Management**: Create players with static and dynamic attributes.
- **User Accounts**: Authentication and role-based permissions (Player, Group Admin, Server Admin).
- **Game Sessions**: Support for turn-based and simultaneous games, private games with passwords, and observers.
- **Game Groups**: Organize multiple games into manageable groups.
- **Name Suggestions**: Built-in utility to suggest random names for players and games from various categories.

## Installation

This project is managed by `uv`.

```bash
uv sync
```

## Usage

### Creating a Player

```python
from multiplayer.game import Player
from multiplayer import ParameterFamily

player = Player("Alice", score=(ParameterFamily.DYNAMIC, 0), team=(ParameterFamily.STATIC, "Red"))
```

### Starting a Game

```python
from multiplayer.game import Game

game = Game(name="Epic Battle", turn_based=True)
game.join_game_as_player(player)
game.start()
```

## Development

Run quality checks and tests:

```bash
uv run python scripts/check_project.py
```

## License

See `LICENSE.md` for details.
