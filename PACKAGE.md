**English** | [Español](translation/PACKAGE.es.md) | [Français](translation/PACKAGE.fr.md)

# Multiplayer Package

This package allows managing multiplayer game sessions, either locally or over a network.

## Installation

To install the package from PyPI:

```bash
pip install multiplayer
```

## Configuration

The server can be configured via command-line arguments or when instantiated in Python.

### TLS Usage (Security)
To enable TLS v1.3 encryption:
- Either let the server generate a self-signed certificate (`--use-tls`).
- Or provide your own PEM files (`--tls-cert` and `--tls-key`).

## Execution

### Launch a game server
You can launch a standalone server using the command:

```bash
multiplayer-server --port 65432 --name "My Server"
```

### Launch a log server
To centralize logs from multiple servers:

```bash
multiplayer-log-server --port 5000
```

### Client Code Example
```python
from multiplayer import GameClient, Player

client = GameClient(host='localhost', port=65432)
game = client.create_game(name="My Game")
game.add_player(Player("Alice"))
game.start()
```

---
*For more technical details, consult the full documentation on the [GitHub repository](https://github.com/devfred78/multiplayer).*
