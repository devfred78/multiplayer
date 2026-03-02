# Multiplayer Game Manager

This Python module provides a simple framework for managing multiplayer games. It allows you to create games, add players with custom attributes, and manage the game state.

## Features

*   Create games with an optional maximum number of players.
*   Support for both turn-based and simultaneous-play games.
*   Add custom attributes to players and games.
*   Manage game state (pending, in-progress, finished).
*   Pause, resume, and stop games.
*   Simple and intuitive API.

## Installation

To use this module in your project, you can clone this repository and install the dependencies.

```sh
git clone <repository-url>
cd multiplayer
pip install -e .
```

## Usage

Here is a quick example of how to use the `multiplayer` module:

```python
from multiplayer import Game, Player

# Create a new turn-based game with a maximum of 4 players and custom attributes
game = Game(max_players=4, turn_based=True, name="My Awesome Game", difficulty="Hard")

# Add players with custom attributes
game.add_player(Player("Alice", score=100))
game.add_player(Player("Bob", score=50))

# Start the game
game.start()

# Print game and player info
print(f"Welcome to '{game.attributes['name']}' (Difficulty: {game.attributes['difficulty']})")
print(f"Current player: {game.current_player.name}")
print(f"{game.current_player.name}'s score: {game.current_player.attributes['score']}")

# Advance to the next turn
game.next_turn()

print(f"Current player: {game.current_player.name}")

# Stop the game
game.stop()

print(f"Game state: {game.state.value}")
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
