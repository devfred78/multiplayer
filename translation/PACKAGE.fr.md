[English](../PACKAGE.md) | [Español](PACKAGE.es.md) | **Français**

# Package Multiplayer

Ce package permet de gérer des parties de jeux multijoueurs, localement ou en réseau.

## Installation

Pour installer le package depuis PyPI :

```bash
pip install multiplayer
```

## Configuration

Le serveur peut être configuré via des arguments de ligne de commande ou lors de son instanciation en Python.

### Utilisation de TLS (Sécurité)
Pour activer le chiffrement TLS v1.3 :
- Soit en laissant le serveur générer un certificat auto-signé (`--use-tls`).
- Soit en fournissant vos propres fichiers PEM (`--tls-cert` et `--tls-key`).

## Exécution

### Lancer un serveur de jeu
Vous pouvez lancer un serveur autonome via la commande :

```bash
multiplayer-server --port 65432 --name "Mon Serveur"
```

### Lancer un serveur de logs
Pour centraliser les logs de plusieurs serveurs :

```bash
multiplayer-log-server --port 5000
```

### Exemple de code Client
```python
from multiplayer import GameClient, Player

client = GameClient(host='localhost', port=65432)
game = client.create_game(name="Ma Partie")
game.add_player(Player("Alice"))
game.start()
```

---
*Pour plus de détails techniques, consultez la documentation complète sur le [dépôt GitHub](https://github.com/devfred78/multiplayer).*
