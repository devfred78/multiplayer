[English](../REFERENCE.md) | **Español** | [Français](REFERENCE.fr.md)

# Referencia de la API para el Módulo `multiplayer`

Este documento proporciona una referencia detallada de la API pública del módulo `multiplayer`.

## Clases Principales

Estas clases se utilizan para gestionar la lógica del juego, ya sea localmente o en el servidor.

### `Game(name=None, max_players=None, turn_based=False, password=None, observer_password=None, max_observers=None, **kwargs)`
Representa una única sesión de juego.

*   **`name`** (`str`, opcional): El nombre de la sesión de juego. Por defecto es `None`.
*   **`max_players`** (`int`, opcional): El número máximo de jugadores que pueden unirse. Por defecto es `None` (ilimitado).
*   **`max_observers`** (`int`, opcional): El número máximo de observadores que pueden unirse. Por defecto es `None` (ilimitado).
*   **`turn_based`** (`bool`, opcional): `True` si el juego es por turnos, `False` para juego simultáneo. Por defecto es `False`.
*   **`password`** (`str`, opcional): Una contraseña para proteger esta partida (se usa para jugadores, y para observadores si no se define `observer_password`).
*   **`observer_password`** (`str`, opcional): Una contraseña específicamente para los observadores de esta partida.
*   **`**kwargs`**: Atributos personalizados para la partida (ej: `difficulty="hard"`).

#### Métodos
*   `add_player(player, password=None)`: Añade un objeto `Player` a la partida. La contraseña es obligatoria si la partida está protegida.
*   `remove_player(player_id)`: Elimina un jugador de la partida por su ID.
*   `add_observer(observer, password=None)`: Añade un objeto `Observer` a la partida. La contraseña es obligatoria si se define `observer_password` (o `password`).
*   `remove_observer(observer_id)`: Elimina un observador de la partida por su ID.
*   `start()`: Inicia la partida.
*   `pause()`: Pausa la partida.
*   `resume()`: Reanuda una partida pausada.
*   `stop()`: Finaliza la partida.
*   `next_turn()`: Avanza al siguiente jugador en un juego por turnos.

#### Propiedades
*   **`ID`**: El ID único de la sesión de juego (solo lectura).
*   **`players`**: Una lista de objetos `Player` en la partida.
*   **`observers`**: Una lista de objetos `Observer` en la partida.
*   **`state`**: El `GameState` actual de la partida (ej: `GameState.IN_PROGRESS`).
*   **`custom_state`**: Un diccionario para almacenar datos específicos del juego.
*   **`attributes`**: Un diccionario de atributos personalizados.
*   **`current_player`**: El objeto `Player` activo en un juego por turnos.

---

### `Player(name, **kwargs)`
Representa a un jugador.

*   **`name`** (`str`): El nombre del jugador.
*   **`**kwargs`**: Atributos personalizados para el jugador (ej: `score=100`).

#### Propiedades
*   **`ID`**: El ID único del jugador (solo lectura).
*   **`name`**: El nombre del jugador.
*   **`attributes`**: Un diccionario de los atributos personalizados del jugador.

---

### `Observer(name, **kwargs)`
Representa a un observador.

*   **`name`** (`str`): El nombre del observador.
*   **`**kwargs`**: Atributos personalizados para el observador.

#### Propiedades
*   **`ID`**: El ID único del observador (solo lectura).
*   **`name`**: El nombre del observador.
*   **`attributes`**: Un diccionario de los atributos personalizados del observador.

---

### `GameGroup(name, admin_password=None, **kwargs)`
Representa un grupo de juegos en un servidor.

*   **`name`** (`str`): El nombre del grupo.
*   **`admin_password`** (`str`, opcional): Una contraseña para acciones administrativas en este grupo.
*   **`**kwargs`**: Atributos adicionales para el grupo.

#### Métodos
*   `add_game(game)`: Añade un objeto `Game` al grupo.
*   `remove_game(game_id)`: Elimina una partida del grupo por su ID.

#### Propiedades
*   **`ID`**: El ID único del grupo (solo lectura).
*   **`name`**: El nombre del grupo.
*   **`games`**: Una lista de objetos `Game` actualmente en el grupo.
*   **`attributes`**: Un diccionario de atributos personalizados para el grupo.

---

### `GameState` (Enum)
Enumeración para el estado del juego.

*   `GameState.PENDING`
*   `GameState.IN_PROGRESS`
*   `GameState.FINISHED`

## Clases de Red

Estas clases gestionan la arquitectura cliente-servidor.

### `GameServer(host='0.0.0.0', port=65432, password=None, admin_password=None, use_tls=False, tls_domain="localhost", tls_cert=None, tls_key=None, tls_self_signed=True, logging_host=None, logging_port=None, name=None)`
Gestiona las sesiones de juego y las peticiones de red.

*   **`host`** (`str`): Dirección del host. Usa `'0.0.0.0'` para acceso en red local.
*   **`port`** (`int`): Puerto TCP para comandos.
*   **`password`** (`str`, opcional): Contraseña global del servidor.
*   **`admin_password`** (`str`, opcional): Contraseña para acceso administrativo.
*   **`use_tls`** (`bool`, opcional): Si es `True`, habilita cifrado TLS v1.3. Por defecto es `False`.
*   **`tls_domain`** (`str`, opcional): Nombre de dominio para el certificado. Por defecto es `"localhost"`.
*   **`tls_cert`** (`str`, opcional): Ruta a un archivo de certificado PEM.
*   **`tls_key`** (`str`, opcional): Ruta a un archivo de clave privada PEM.
*   **`tls_self_signed`** (`bool`, opcional): Si es `True`, genera un certificado auto-firmado si faltan archivos. Por defecto es `True`.
*   **`logging_host`** (`str`, opcional): Dirección del servidor de logs.
*   **`logging_port`** (`int`, opcional): Puerto del servidor de logs.
*   **`name`** (`str`, opcional): Nombre para la instancia del servidor.

#### Métodos
*   `start()`: Inicia el servidor en un proceso de segundo plano.
*   `stop()`: Detiene el servidor.

---

### `ServerAdmin(host='127.0.0.1', port=65432, admin_password=None, use_tls=False)`
Clase de cliente para administradores de un `GameServer`.

*   **`host`** (`str`): Dirección IP del servidor.
*   **`port`** (`int`): Puerto TCP del servidor.
*   **`admin_password`** (`str`, opcional): Contraseña de administrador.
*   **`use_tls`** (`bool`, opcional): Si es `True`, usa TLS. Por defecto es `False`.

#### Métodos
*   `get_server_info()`: Devuelve información (nombre, número de juegos, IDs activos).
*   `list_games()`: Devuelve un diccionario de juegos activos como objetos `RemoteGame`, indexado por su ID.
*   `kick_player(game_id, player_id)`: Expulsa a un jugador por su ID.
*   `kick_observer(game_id, observer_id)`: Expulsa a un observador por su ID.
*   `list_all_players()`: Lista todos los jugadores conectados, incluyendo su ID y nombre de juego.
*   `stop_server()`: Solicita el apagado del servidor.
*   `restart_server()`: Solicita el reinicio del servidor (borra juegos actuales).
*   `set_logging_config(host, port)`: Configura el servidor de logs remoto.
*   `get_cert_expiration()`: Devuelve la fecha de expiración del certificado en formato ISO.
*   `set_logging_enabled(enabled)`: Activa o desactiva los registros en el servidor.
*   `set_server_password(new_password)`: Establece una nueva contraseña de servidor.
*   `set_admin_password(new_password)`: Establece una nueva contraseña de administrador.
*   `create_group(name, admin_password=None, **attributes)`: Crea un nuevo grupo. Devuelve un objeto proxy `RemoteGroup`.
*   `remove_group(group_id)`: Elimina un grupo por su ID.
*   `list_groups()`: Devuelve todos los grupos como objetos `RemoteGroup`, indexado por su `group_id`.

---

### `GroupAdmin(group_id, host='127.0.0.1', port=65432, group_admin_password=None, use_tls=False)`
Clase para que los administradores de grupo gestionen sus juegos en un `GameGroup`.

*   **`group_id`** (`str`): ID único del grupo.
*   **`group_admin_password`** (`str`, opcional): Contraseña administrativa del grupo.

#### Métodos
*   `list_games()`: Devuelve juegos del grupo como objetos `RemoteGame`, indexado por su ID.
*   `kick_player(game_id, player_id)`: Expulsa a un jugador del grupo por su ID.
*   `kick_observer(game_id, observer_id)`: Expulsa a un observador del grupo por su ID.
*   `set_group_admin_password(new_password)`: Establece nueva contraseña de administrador del grupo.

---

### `GameClient(host='127.0.0.1', port=65432, password=None, use_tls=False)`
Punto de entrada principal para conectar a un `GameServer`.

*   **`password`** (`str`, opcional): Contraseña global del servidor.
*   **`use_tls`** (`bool`, optionale): Si es `True`, usa TLS. Por defecto es `False`.

#### Métodos
*   `discover_servers(timeout=2)` (método estático): Busca instancias de `GameServer` en la red local.
*   `create_game(group_id=None, **game_options)`: Crea una nueva partida. Devuelve un objeto proxy `RemoteGame`.
*   `list_games()`: Devuelve juegos activos como objetos `RemoteGame`, indexado por su ID.
*   `create_group(name, admin_password=None, **attributes)`: Crea un nuevo grupo. Devuelve un objeto proxy `RemoteGroup`.
*   `list_groups()`: Devuelve los grupos como objetos `RemoteGroup`, indexado por su ID.

---

### `RemoteGroup`
Objeto proxy que representa un grupo de juegos en el servidor.

#### Métodos
*   `create_game(**game_options)`: Crea una nueva partida en este grupo. Devuelve un objeto proxy `RemoteGame`.
*   `list_games()`: Devuelve juegos de este grupo como objetos `RemoteGame`, indexado por su ID.

#### Propiedades
*   **`group_id`**: ID único del grupo.
*   **`name`**: Nombre del grupo.
*   **`attributes`**: Diccionario de atributos personalizados.

---

### `RemoteGame`
Objeto proxy que representa una partida en el servidor.

#### Métodos
*   `add_player(player, password=None)`: Añade un `Player` a la partida remota.
*   `add_observer(observer, password=None)`: Añade un `Observer` a la partida remota. Requiere contraseña si se definió.
*   `set_state(new_state)`: Sobrescribe `custom_state` en el servidor.
*   (Otros métodos son iguales a la clase `Game` local).

#### Propiedades
*   **`state`**: Devuelve diccionario con `status` y `custom`.
*   **`observers`**: Devuelve lista de objetos `Observer` (nombres e IDs).

## Servidor de Registros Autónomo

### `multiplayer-log-server [--port PORT] [--color-mode MODE]`
Inicia el servidor de registros autónomo.

*   **`--port`** (`int`, opcional): Puerto TCP. Por defecto es `5000`.
*   **`--color-mode`** (`str`, opcional): `level` (defecto) o `origin`.

## Servidor de Juegos Autónomo

### `multiplayer-server [OPTIONS]`
Inicia un servidor de juegos autónomo.

*   **`--host`**, **`--port`**, **`--password`**, **`--admin-password`**, **`--use-tls`**, etc.
*   **`--name`** (`str`): Nombre de la instancia.

## Funciones de Utilidad

### Sugerencias de Nombres
*   `register_name_category(...)`, `unregister_name_category(...)`, `get_available_categories(...)`, `suggest_game_name(...)`, `suggest_player_name(...)`.

## Excepciones

*   **`MultiplayerError`**: Excepción base.
*   **`GameLogicError`**: Errores de reglas.
*   **`PlayerLimitReachedError`**, **`ObserverLimitReachedError`**
*   **`GameNotFoundError`**, **`GroupNotFoundError`**
*   **`NetworkError`**, **`ConnectionError`**, **`ServerError`**
*   **`AuthenticationError`**: Error de contraseña (servidor o partida).
*   **`AccessDeniedError`**: Acción administrativa denegada.
