[English](../README.md) | **Español** | [Français](README.fr.md)

# Gestor de Juegos Multijugador

> **Una Nota sobre el Origen de este Proyecto**
>
> Este proyecto es principalmente el resultado de una serie de experimentos usando Gemini Code Assist para la generación de código y el manejo de errores. En lugar de usarlo en ejemplos académicos, parecía más interesante aplicarlo a un proyecto que pudiera satisfacer una necesidad práctica real.
>
> Esta, por lo tanto, es la razón de ser de `multiplayer`: ¡puedes diseccionar el código para ver cómo Gemini (con mi guía) lo construyó, o puedes ignorar todo eso y simplemente usar esta biblioteca para tus propias necesidades!

Este módulo de Python proporciona un marco simple y flexible para gestionar juegos multijugador, tanto localmente como en una red.

Para una descripción técnica detallada de todas las clases y funciones, consulta la [Referencia de la API](REFERENCE.es.md).

## Características

*   **Local y en Red:** Úsalo en un solo proceso o en una arquitectura cliente-servidor.
*   **Estado de Juego Combinado:** Un sistema flexible para sincronizar tanto el estado principal del jeu (ej: `in_progress`) como datos de juego personalizados.
*   **Soporte de Observadores:** Capacidad de añadir observadores que pueden ver el estado del juego sin participar como jugadores.
*   **Rol de Administrador:** Nueva clase `ServerAdmin` para gestionar el servidor, expulsar jugadores/observadores y supervisar el estado del servidor.
*   **Agrupación de Juegos:** Organiza varias sesiones de juego dentro del mismo servidor utilizando la clase `GameGroup`.
*   **Seguridad Multinivel:** Soporta contraseñas de servidor, administrador y por partida, con cifrado opcional TLS v1.3. Los administradores pueden actualizar las contraseñas dinámicamente y se almacenan de forma segura mediante el hash `bcrypt`.
*   **Descubrimiento Automático de Servidores:** Los clientes pueden encontrar automáticamente servidores en funcionamiento en la red local.
*   **Sugerencias de Nombres Extensibles:** Incluye una función de utilidad para sugerir nombres creativos para juegos y jugadores.
*   **Múltiples Partidas:** El servidor puede gestionar múltiples sesiones de juego simultáneamente. Por defecto, la lista de partidas para los clientes estándar se filtra para ocultar las partidas finalizadas, pero los administradores pueden acceder a todas las sesiones a través de métodos especializados como `list_all_server_games()` o `list_all_group_games()`.
*   **Manejo de Errores Robusto:** Un conjunto claro de excepciones personalizadas para la lógica del juego y problemas de red.
*   **Cuentas de Jugador Persistentes:** Capacidad para que los jugadores creen una cuenta con contraseña para uso repetido en el servidor. Todas las contraseñas persistentes (jugadores, grupos y servidor) están protegidas con `bcrypt`.
*   **Persistencia de Datos:** Soporte opcional para la persistencia de la configuración del servidor, las cuentas de los jugadores y las sesiones de juego en disco (ej: en formato JSON). El almacenamiento de contraseñas basado en hash garantiza la seguridad incluso si el archivo de datos se ve comprometido.

## Instalación

Puedes instalarlo de dos maneras:

### 1. Desde PyPI
```sh
pip install multiplayer
```

### 2. Desde un archivo Wheel (GitHub)
Descarga el archivo `.whl` desde la página de [Lanzamientos (Releases)](https://github.com/devfred78/multiplayer/releases) y ejecuta:
```sh
pip install multiplayer-1.0.0-py3-none-any.whl
```
*Reemplaza `multiplayer-1.0.0-py3-none-any.whl` con el nombre real del archivo descargado.*

## Uso

### Gestión del Estado de Juego

Una característica clave es la capacidad de gestionar tu propio estado de juego junto con el estado principal del juego.

```python
# En un cliente, establece un estado personalizado
juego.set_state({
    "tablero": [["X", "O", ""], ["", "X", ""], ["O", "", ""]],
    "turno": "jugador2"
})

# En otro cliente, recupera el estado combinado
estado_completo = juego.state
print(f"Estado de la partida: {estado_completo['status']}")
# > Estado de la partida: in_progress

print(f"Turno actual: {estado_completo['custom']['turno']}")
# > Turno actual: jugador2
```


### Agrupación de Juegos

Puedes agrupar juegos para una mejor organización.

```python
from multiplayer import Game, GameGroup

# Crear un grupo
group = GameGroup("Torneo A", priority="high")

# Añadir juegos al grupo
game1 = Game("Match 1")
game2 = Game("Match 2")
group.add_game(game1)
group.add_game(game2)

print(f"ID del Match 1: {game1.game_id}")
# > ID del Match 1: 550e8400-e29b-41d4-a716-446655440000

print(f"El grupo '{group.name}' tiene {len(group.games)} juegos.")
# > El grupo 'Torneo A' tiene 2 juegos.
```


### Entorno de Prueba Completo

Un script está disponible para lanzar un entorno de prueba completo con:
- Un servidor de registros IPC (`IPClogging`) en una ventana separada.
- Un servidor de juegos.
- Múltiples instancias de clientes separadas (2 por defecto) simulando una partida, cada una en su propia ventana de terminal.

Para ejecutarlo:
```bash
uv run python scripts/full_test_env.py
```

Para especificar el número de jugadores:
```bash
uv run python scripts/full_test_env.py --players 3
```
Esto abrirá varias ventanas de Windows Terminal: una para el servidor de registros y otra para cada instancia de cliente, permitiéndote ver las interacciones y los registros en tiempo real.

### Uso Local

Puedes usar la clase `Game` directamente, incluyendo una contraseña para la validación local.

```python
from multiplayer import Game, Player, suggest_game_name

game = Game(name="Mi Super Partida", password="local_game_pass")
game.add_player(Player("Alice"), password="local_game_pass")
game.start()
```

### Uso en Red (Cliente-Servidor)

#### Configuración del Servidor
```python
from multiplayer import GameServer

# Iniciar un servidor seguro con un dominio personalizado y un certificado auto-firmado
server = GameServer(
    host='0.0.0.0',
    port=12345,
    name="Mi Servidor de Producción",
    password="mi_contraseña_de_servidor",
    admin_password="mi_contraseña_de_admin",
    use_tls=True,
    tls_domain="ejemplo.com",
    tls_self_signed=True
)
server.start()

# O usar archivos de certificado existentes
server = GameServer(
    use_tls=True,
    tls_cert="ruta/al/cert.pem",
    tls_key="ruta/al/key.pem",
    tls_self_signed=False
)
```

#### Uso con Docker

Puedes ejecutar el servidor de juegos usando Docker. Para usar tus propios certificados TLS, mapea un directorio local que contenga `cert.pem` y `privkey.pem` a `/app/certs` en el contenedor.

```bash
docker run -d \
  -p 65432:65432 \
  -v /ruta/a/tus/certificados:/app/certs \
  ghcr.io/tu_usuario/multiplayer-server:latest \
  --name "Mi Servidor Docker" \
  --use-tls --no-self-signed
```

El servidor buscará automáticamente los archivos `cert.pem`, `RSA-cert.pem` o `ECC-cert.pem` (y sus correspondientes claves) en el directorio `/app/certs`.

#### Uso para el Administrador

```python
from multiplayer import ServerAdmin

# Conectarse comme administrador
admin = ServerAdmin(
    host='localhost',
    port=12345,
    admin_password="mi_contraseña_de_admin",
    use_tls=True
)

# Gestionar el servidor
info = admin.get_server_info()
print(f"Uptime: {info['uptime']} segundos")

# Expulsar a un jugador si es necesario
# admin.kick_player(game_id, player_id)

# Detener el servidor de forma remota
# admin.stop_server()
```

#### Uso para el Cliente
```python
from multiplayer import GameClient, Player, suggest_game_name

# 1. Descubrir y conectarse al servidor
servers = GameClient.discover_servers()
if not servers:
    print("No se encontraron servidores.")
else:
    host, port = servers[0]
    client = GameClient(
        host=host,
        port=port,
        password="mi_contraseña_de_servidor",
        use_tls=True
    )

    # 2. Crear una partida privada
    private_game = client.create_game(
        name=suggest_game_name(),
        password="mi_contraseña_de_partida"
    )
    print(f"Partida creada con ID: {private_game.game_id}")

    # 3. Crear y usar un grupo de juegos
    group = client.create_group("Torneo A")
    game_in_group = group.create_game(name="Match Final")
    print(f"La partida en el grupo '{group.name}' tiene el ID: {game_in_group.game_id}")

    # 4. Un jugador se une y establece el estado inicial
    private_game.add_player(Player("Charlie"), password="mi_contraseña_de_partida")
    private_game.set_state({"score": 0})
    private_game.start()
```

### Sugerencias de Nombres

El paquete `multiplayer` incluye una potente utilidad de sugerencia de nombres para ayudarte a crear nombres creativos para juegos y jugadores.

```python
from multiplayer import suggest_game_name, suggest_player_name

# Obtener un nombre aleatorio
print(suggest_game_name())    # ej: "Océano Pacífico"
print(suggest_player_name())  # ej: "Zeus"

# Especificar una categoría
print(suggest_game_name(category="planets_moons")) # ej: "Europa"
print(suggest_player_name(category="european_queens")) # ej: "Isabel I"
```

#### Categorías Integradas
*   **Para Juegos**: `cities`, `countries`, `rivers`, `seas_oceans`, `planets_moons`.
*   **Para Jugadores**: `roman_gods`, `greek_gods`, `egyptian_gods`, `european_kings`, `european_queens`.

#### Categorías Personalizadas
También puedes registrar tus propias categorías utilizando una lista de nombres o un archivo:

```python
from multiplayer import register_name_category

# Registrar desde una lista
register_name_category("monstruos", ["Godzilla", "King Kong"], category_type="player")

# Registrar desde un archivo de texto/CSV
register_name_category("razas", "ruta/al/archivo/razas.txt", category_type="player")
```

## Manejo de Errores

El módulo proporciona un conjunto de excepciones personalizadas, incluyendo `AuthenticationError` tanto para contraseñas de servidor como de juego.

```python
from multiplayer import GameClient
from multiplayer.exceptions import ConnectionError, AuthenticationError

try:
    # ... conectarse al cliente ...

    # Intentar unirse a un juego con la contraseña incorrecta
    game.add_player(Player("Eve"), password="contraseña_incorrecta")

except AuthenticationError as e:
    print(f"La autenticación falló como se esperaba: {e}")
except ConnectionError as e:
    print(f"Ocurrió un error de conexión o descubrimiento: {e}")
```

## Contribución

¡Damos la bienvenida a las contribuciones! Por favor, consulta nos [Directrices de contribución](CONTRIBUTING.md) para más detalles sobre cómo empezar.

## Ejecución de Pruebas

Para ejecutar las pruebas unitarias, necesitarás tener instalado `pytest`.

```sh
pip install pytest
```

Luego, puedes ejecutar las pruebas desde la raíz del proyecto:

```sh
pytest
```

## Licencia

Este proyecto está bajo la Licencia MIT - vea el archivo [LICENSE.md](../LICENSE.md) para más detalles.
