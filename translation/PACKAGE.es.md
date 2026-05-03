[English](../PACKAGE.md) | **Español** | [Français](PACKAGE.fr.md)

# Paquete Multiplayer

Este paquete permite gestionar sesiones de juegos multijugador, ya sea localmente o a través de una red.

## Instalación

Para instalar el paquete desde PyPI:

```bash
pip install multiplayer
```

## Configuración

El servidor puede configurarse mediante argumentos de línea de comandos o al instanciarlo en Python.

### Uso de TLS (Seguridad)
Para habilitar el cifrado TLS v1.3:
- O bien dejar que el servidor genere un certificado autofirmado (`--use-tls`).
- O bien proporcionar sus propios archivos PEM (`--tls-cert` y `--tls-key`).

## Ejecución

### Iniciar un servidor de juego
Puede iniciar un servidor independiente mediante el comando:

```bash
multiplayer-server --port 65432 --name "Mi Servidor"
```

### Iniciar un servidor de registros (logs)
Para centralizar los registros de varios servidores:

```bash
multiplayer-log-server --port 5000
```

### Ejemplo de código del Cliente
```python
from multiplayer import GameClient, Player

client = GameClient(host='localhost', port=65432)
game = client.create_game(name="Mi Partida")
game.add_player(Player("Alice"))
game.start()
```

---
*Para más detalles técnicos, consulte la documentación completa en el [repositorio GitHub](https://github.com/devfred78/multiplayer).*
