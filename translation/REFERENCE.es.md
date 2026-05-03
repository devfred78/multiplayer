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
*   **`password`** (`str`, opcional): Una contraseña para proteger esta partida específica (se usa para jugadores, y para observadores si `observer_password` no está configurado).
*   **`observer_password`** (`str`, opcional): Una contraseña específicamente para que los observadores se unan a esta partida.
*   **`**kwargs`**: Atributos personalizados para la partida (ej: `difficulty="hard"`).

#### Métodos
*   `add_player(player, password=None)`: Añade un objeto `Player` a la partida. La contraseña es obligatoria si la partida está protegida por contraseña.
*   `remove_player(player_id)`: Elimina un jugador de la partida por su ID.
*   `add_observer(observer, password=None)`: Añade un objeto `Observer` a la partida. La contraseña es obligatoria si `observer_password` (o `password`) está configurado.
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
*   **`custom_state`**: Un diccionario para almacenar cualquier dato específico del juego.
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
*   `remove_game(game_id)` : Elimina una partida del grupo por su ID.

#### Propiedades
*   **`ID`**: El ID único del grupo (solo lectura).
*   **`name`**: El nombre del grupo.
*   **`games`**: Una lista de objetos `Game` actualmente en el grupo.
*   **`attributes`**: Un diccionario de atributos personalizados para el grupo.

---

### `GameState` (Enum)
Una enumeración para el estado del juego.

*   `GameState.PENDING`
*   `GameState.IN_PROGRESS`
*   `GameState.FINISHED`

## Clases de Red

Estas clases gestionan la arquitectura cliente-servidor.

### `GameServer(host='0.0.0.0', port=65432, password=None, admin_password=None, use_tls=False, tls_domain="localhost", tls_cert=None, tls_key=None, tls_self_signed=True, logging_host=None, logging_port=None, name=None)`
Gestiona las sesiones de juego y maneja las peticiones de red.

*   **`host`** (`str`): La dirección del host a la que vincularse. Usa `'0.0.0.0'` para hacerlo accesible en la red local.
*   **`port`** (`int`): El puerto TCP en el que escuchar los comandos del juego.
*   **`password`** (`str`, opcional): Una contraseña global para proteger el servidor.
*   **`admin_password`** (`str`, opcional): Una contraseña para acceso administrativo.
*   **`use_tls`** (`bool`, opcional): Si es `True`, habilita el cifrado TLS v1.3 para todas las comunicaciones. Por defecto es `False`.
*   **`tls_domain`** (`str`, opcional): Nombre de dominio a incluir en el certificado generado. Por defecto es `"localhost"`.
*   **`tls_cert`** (`str`, opcional): Ruta a un archivo de certificado PEM. Este archivo debe ser una "cadena completa" (incluyendo el certificado del dominio y los certificados intermedios) o tener un archivo de "cadena" correspondiente en el mismo directorio (ej: `cert.pem` y `chain.pem`, o `ECC-cert.pem` y `ECC-chain.pem`). Si solo se proporciona uno de `tls_cert` o `tls_key` mientras `tls_self_signed` es `False`, el servidor no se iniciará.
*   **`tls_key`** (`str`, opcional): Ruta a un archivo de clave privada PEM. Si solo se proporciona uno de `tls_cert` o `tls_key` mientras `tls_self_signed` es `False`, el servidor no se iniciará.
*   **`tls_self_signed`** (`bool`, opcional): Si es `True`, genera un certificado auto-firmado si falta `tls_cert` o `tls_key`. Si es `False`, se deben proporcionar ambos. Por defecto es `True`.
*   **`logging_host`** (`str`, opcional): La dirección del host de un servidor de registros al que enviar los registros.
*   **`logging_port`** (`int`, opcional): El puerto del servidor de registros.
*   **`name`** (`str`, opcional): Un nombre para la instancia del servidor.

#### Métodos
*   `start()`: Inicia el servidor en un proceso de segundo plano.
*   `stop()`: Detiene el servidor.

---

### `ServerAdmin(host='127.0.0.1', port=65432, admin_password=None, use_tls=False)`
Una clase de cliente para que los administradores gestionen un `GameServer`.

*   **`host`** (`str`): La dirección IP del servidor.
*   **`port`** (`int`): El puerto TCP del servidor.
*   **`admin_password`** (`str`, opcional): La contraseña de administrador del servidor.
*   **`use_tls`** (`bool`, opcional): Si es `True`, el cliente se conectará usando TLS. Por defecto es `False`.

#### Métodos
*   `get_server_info()`: Devuelve información sobre el servidor (nombre, número de juegos, IDs de juegos activos).
*   `list_games()`: Devuelve un diccionario de juegos activos como objetos `RemoteGame`, indexados por su ID.
*   `kick_player(game_id, player_id)`: Elimina a un jugador de un juego específico por su ID.
*   `kick_observer(game_id, observer_id)`: Elimina a un observador de un juego específico por su ID.
*   `list_all_players()`: Devuelve una lista de todos los jugadores actualmente conectados al servidor, incluyendo su ID de juego asociado y su nombre.
*   `stop_server()`: Solicita el apagado del servidor.
*   `restart_server()` : Solicita el reinicio del servidor (borra todos los juegos actuales).
*   `set_logging_config(host, port)`: Configura el servidor para enviar sus registros a un servidor de registros remoto en la dirección y puerto especificados.
*   `get_cert_expiration()`: Devuelve la fecha de expiración del certificado TLS del servidor en formato ISO.
*   `set_logging_enabled(enabled)`: Activa (`True`) o desactiva (`False`) el registro en el servidor.
*   `set_server_password(new_password)`: Establece una nueva contraseña para el servidor.
*   `set_admin_password(new_password)`: Establece una nueva contraseña de administrador para el servidor.
*   `create_group(name, admin_password=None, **attributes)`: Crea un nuevo grupo de juegos en el servidor. Devuelve un objeto proxy `RemoteGroup`.
*   `remove_group(group_id)` : Elimina un grupo de juegos del servidor por su ID.
*   `list_groups()` : Devuelve un diccionario de todos los grupos de juegos en el servidor como objetos `RemoteGroup`, indexados por su `group_id`.

---

### `GroupAdmin(group_id, host='127.0.0.1', port=65432, group_admin_password=None, use_tls=False)`
Una clase de cliente para que los administradores de grupo gestionen juegos dentro de un `GameGroup` específico.

*   **`group_id`** (`str`): El ID único del grupo a gestionar.
*   **`host`** (`str`): La dirección IP del servidor.
*   **`port`** (`int`): El puerto TCP del servidor.
*   **`group_admin_password`** (`str`, opcional): La contraseña administrativa para este grupo.
*   **`use_tls`** (`bool`, opcional): Si es `True`, el cliente se conectará usando TLS. Por defecto es `False`.

#### Métodos
*   `list_games()`: Devuelve un diccionario de juegos pertenecientes a este grupo como objetos `RemoteGame`, indexados por su ID.
*   `kick_player(game_id, player_id)`: Elimina a un jugador de un juego específico en el grupo por su ID.
*   `kick_observer(game_id, observer_id)`: Elimina a un observador de un juego específico en el grupo por su ID.
*   `set_group_admin_password(new_password)`: Establece una nueva contraseña de administrador para este grupo.

---

### `GameClient(host='127.0.0.1', port=65432, password=None, use_tls=False)`
El punto de entrada principal para que un cliente se conecte a un `GameServer`.

*   **`host`** (`str`): La dirección IP del servidor.
*   **`port`** (`int`): El puerto TCP del servidor.
*   **`password`** (`str`, opcional): La contraseña global del servidor.
*   **`use_tls`** (`bool`, opcional): Si es `True`, el cliente se conectará usando TLS. Por defecto es `False`.

#### Métodos
*   `discover_servers(timeout=2)` (método estático): Escanea la red local en busca de instancias de `GameServer` en ejecución. Devuelve una lista de tuplas `(host, port)`.
*   `create_game(group_id=None, **game_options)`: Solicita al servidor crear un nuevo juego. Devuelve un objeto proxy `RemoteGame`. Puede incluir un `group_id` para asociar el juego con un grupo.
*   `list_games()`: Devuelve un diccionario de juegos activos como objetos `RemoteGame`, indexados por su ID.
*   `create_group(name, admin_password=None, **attributes)`: Solicita al servidor crear un nuevo grupo de juegos. Devuelve un objeto proxy `RemoteGroup`.
*   `list_groups()` : Devuelve un diccionario de grupos de juegos como objetos `RemoteGroup`, indexados por su ID.

---

### `RemoteGroup`
Un objeto proxy que representa un grupo de juegos que se ejecuta en el servidor.

*Normalmente no se crea este objeto directamente, sino que se obtiene de `client.create_group()` o `client.list_groups()`.*

#### Métodos
*   `create_game(**game_options)`: Crea un nuevo juego dentro de este grupo. Devuelve un objeto proxy `RemoteGame`.
*   `list_games()`: Devuelve un diccionario de juegos pertenecientes a este grupo como objetos `RemoteGame`, indexados por su ID.

#### Propiedades
*   **`group_id`**: El ID único del grupo.
*   **`name`**: El nombre del grupo.
*   **`attributes`**: Un dictionnaire de atributos personalizados para el grupo.

---

### `RemoteGame`
Un objeto proxy que representa un juego que se ejecuta en el servidor.

*Normalmente no se crea este objeto directamente, sino que se obtiene de `client.create_game()`.*

#### Métodos
*   `add_player(player, password=None)`: Añade un `Player` al juego remoto. Se requiere la contraseña si el juego está protegido por contraseña.
*   `add_observer(observer, password=None)`: Añade un `Observer` al juego remoto. Se requiere la contraseña si `observer_password` (o `password`) está configurado para el juego.
*   `set_state(new_state)`: Sobrescribe el diccionario `custom_state` del juego en el servidor.
*   (Otros métodos son iguales a los de la clase `Game` local).

#### Propiedades
*   **`state`** : Devuelve un diccionario que contiene tanto el `GameState` como el estado personalizado. Ejemplo: `{'status': 'in_progress', 'custom': {'score': 100}}`.
*   **`observers`** : Devuelve una lista de nombres de observadores en el juego.

## Servidor de Registros Autónomo

El paquete `multiplayer` incluye un servidor de registros autónomo que se puede utilizar para recibir y mostrar registros de múltiples instancias de `GameServer`.

### `multiplayer-log-server [--port PORT] [--color-mode MODE]`
Inicia el servidor de registros autónomo.

*   **`--port`** (`int`, opcional): El puerto TCP en el que escuchar. Por defecto es `5000`.
*   **`--color-mode`** (`str`, opcional): El modo de coloración para los registros. Las opciones son:
    *   `level`: Colorea los registros según su criticidad (ej: INFO es verde, ERROR es rojo). Este es el valor por defecto.
    *   `origin`: Colorea los registros según el nombre del registrador (ej: `GameServer`, `GameClient`, `ServerAdmin`, etc.). Esto ayuda a diferenciar mensajes de diferentes fuentes.

## Servidor de Juegos Autónomo

### `multiplayer-server [OPTIONS]`
Inicia un servidor de juegos autónomo.

*   **`--host`** (`str`): Dirección del host en la que escuchar. Por defecto es `0.0.0.0`.
*   **`--port`** (`int`): Puerto en el que escuchar. Por defecto es `65432`.
*   **`--password`** (`str`): Contraseña global del servidor.
*   **`--admin-password`** (`str`): Contraseña administrativa.
*   **`--use-tls`**: Habilita el cifrado TLS v1.3.
*   **`--tls-domain`** (`str`): Nombre de dominio para el certificado. Por defecto es `localhost`.
*   **`--tls-cert`** (`str`): Ruta a un archivo de certificado PEM.
*   **`--tls-key`** (`str`): Ruta a un archivo de clave privada PEM.
*   **`--tls-cert-dir`** (`str`): Ruta a un directorio que contiene certificados PEM (`cert.pem`, `RSA-cert.pem` o `ECC-cert.pem`) y claves. Esto es particularmente útil para volúmenes Docker.
*   **`--tls-self-signed`**: Genera un certificado auto-firmado si faltan los archivos (por defecto).
*   **`--no-self-signed`**: Desactiva la generación automática de certificados auto-signados.
*   **`--name`** (`str`): Nombre legible para humanos para la instancia del servidor.

## Funciones de Utilidad

### Sugerencias de Nombres

#### `register_name_category(category_name, data, category_type)`
Registra una nueva categoría personalizada para sugerencias de nombres.

*   **`category_name`** (`str`): El nombre de la nueva categoría.
*   **`data`** (`list` o `str`): Una lista de nombres, o una ruta a un archivo de texto (un nombre por línea).
*   **`category_type`** (`str`): `"game"` o `"player"`.

---

#### `unregister_name_category(category_name)`
Elimina una categoría personalizada. Devuelve `True` si tiene éxito.

---

#### `get_available_categories(category_type="all")`
Devuelve una lista de categorías de sugerencias de nombres disponibles.

*   **`category_type`** (`str`): `"all"`, `"game"` o `"player"`.

---

#### `suggest_game_name(category=None)`
Sugiere un nombre aléatorio para un juego.

---

#### `suggest_player_name(category=None)`
Sugiere un nombre aléatorio para un jugador.

## Excepciones

*   **`MultiplayerError`**: Excepción base para todos los errores específicos del módulo.
*   **`GameLogicError`**: Para errores en las reglas del juego.
*   **`PlayerLimitReachedError`**: Se lanza al añadir un jugador a un juego lleno.
*   **`ObserverLimitReachedError`**: Se lanza al añadir un observador a un juego que ha alcanzado su límite de observadores.
*   **`GameNotFoundError`**: Se lanza cuando un cliente solicita un `id` de juego que no existe en el servidor.
*   **`NetworkError`**: Excepción base para problemas relacionados con la red.
*   **`ConnectionError`**: Se lanza cuando un cliente no logra conectarse al servidor.
*   **`ServerError`**: Se lanza para errores genéricos reportados por el servidor.
*   **`AuthenticationError`**: Se lanza para fallos de autenticación de contraseña tanto del servidor como del juego.
*   **`GroupNotFoundError`**: Se lanza cuando no se encuentra un `id` de grupo en el servidor.
*   **`AccessDeniedError`**: Se lanza cuando se intenta una acción administrativa con credenciales incorrectas o ausentes.
