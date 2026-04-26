[English](../REFERENCE.md) | **Español** | [Français](REFERENCE.fr.md)

# Referencia de la API para el Módulo `multiplayer`

Este documento proporciona una referencia detallada de la API pública del módulo `multiplayer`.

## Clases Principales

### `Game(name=None, max_players=None, turn_based=False, password=None, max_observers=None, **kwargs)`
Representa una única sesión de juego.

*   **`name`** (`str`, opcional): El nombre de la sesión de juego. Por defecto es `None`.
*   **`max_players`** (`int`, opcional): El número máximo de jugadores.
*   **`max_observers`** (`int`, opcional): El número máximo de observadores.
*   **`turn_based`** (`bool`, opcional): `True` si el juego es por turnos.
*   **`password`** (`str`, opcional): Una contraseña para proteger esta partida.
*   **`**kwargs`**: Atributos personalizados para la partida (ej: `difficulty="hard"`).

#### Métodos
*   `add_player(player, password=None)`: Añade un objeto `Player` a la partida.
*   `remove_player(player_name)`: Elimina un jugador de la partida por su nombre.
*   `add_observer(observer)`: Añade un objeto `Observer` a la partida.
*   `remove_observer(observer_name)`: Elimina un observador de la partida por su nombre.
*   `start()`: Inicia la partida.

#### Propiedades
*   **`players`**: Una lista de objetos `Player`.
*   **`observers`**: Una lista de objetos `Observer`.
*   **`state`**: El `GameState` actual de la partida (ej., `GameState.IN_PROGRESS`).
*   **`custom_state`**: Un diccionario para almacenar cualquier dato específico del juego.

---

### `Player(name, **kwargs)`
Representa a un jugador.

*   **`name`** (`str`): El nombre del jugador.
*   **`**kwargs`**: Atributos personalizados para el jugador.

---

### `Observer(name, **kwargs)`
Representa a un observador.

*   **`name`** (`str`): El nombre del observador.
*   **`**kwargs`**: Atributos personalizados para el observador.

#### Propiedades
*   **`name`**: El nombre del observador.
*   **`attributes`**: Un diccionario de los atributos personalizados del observador.

---

### `GameState` (Enum)
*   `GameState.PENDING`, `GameState.IN_PROGRESS`, `GameState.FINISHED`

## Clases de Red

### `GameServer(host='0.0.0.0', port=65432, password=None, admin_password=None, use_tls=False, tls_domain="localhost", tls_cert=None, tls_key=None, tls_self_signed=True, logging_host=None, logging_port=None, name=None)`
Gestiona las sesiones de juego y las peticiones de red.

*   **`host`** (`str`): La dirección del host a la que vincularse. Usa `'0.0.0.0'` para que sea accesible en la red local.
*   **`port`** (`int`): El puerto TCP en el que escuchar los comandos del juego.
*   **`password`** (`str`, opcional): Una contraseña global para proteger el servidor.
*   **`admin_password`** (`str`, opcional): Una contraseña para acceso administrativo.
*   **`use_tls`** (`bool`, opcional): Si es `True`, habilita el cifrado TLS v1.3 para todas las comunicaciones. Por defecto es `False`.
*   **`tls_domain`** (`str`, opcional): Nombre de dominio a incluir en el certificado generado. Por defecto es `"localhost"`.
*   **`tls_cert`** (`str`, opcional): Ruta a un archivo de certificado PEM. Este archivo debe ser una "cadena completa" (que incluya el certificado de dominio y los certificados intermedios) o tener un archivo de "cadena" correspondiente en el mismo directorio (ej: `cert.pem` y `chain.pem`, o `ECC-cert.pem` y `ECC-chain.pem`). Si solo se proporciona uno de `tls_cert` o `tls_key` mientras `tls_self_signed` es `False`, el servidor no se iniciará.
*   **`tls_key`** (`str`, opcional): Ruta a un archivo de clave privada PEM. Si solo se proporciona uno de `tls_cert` o `tls_key` mientras `tls_self_signed` es `False`, el servidor no se iniciará.
*   **`tls_self_signed`** (`bool`, opcional): Si es `True`, genera un certificado auto-firmado si falta `tls_cert` o `tls_key`. Si es `False`, se deben proporcionar tanto `tls_cert` como `tls_key`. Por defecto es `True`.
*   **`logging_host`** (`str`, opcional): La dirección del host de un serveur de logging.
*   **`logging_port`** (`int`, opcional): El puerto del servidor de logging.
*   **`name`** (`str`, opcional): Un nombre para la instancia del servidor.

---

### `GameAdmin(host='127.0.0.1', port=65432, admin_password=None, use_tls=False)`
Una clase de cliente para que los administradores gestionen un `GameServer`.

*   **`admin_password`** (`str`, opcional): La contraseña de administrador para el servidor.
*   **`use_tls`** (`bool`, opcional): Si es `True`, el cliente se conectará usando TLS.

#### Métodos
*   `get_server_info()`: Devuelve información sobre el servidor (nombre, número de juegos, IDs activos).
*   `list_games()`: Devuelve una lista de todos los juegos activos.
*   `kick_player(game_id, player_name)`: Elimina a un jugador de un juego específico.
*   `kick_observer(game_id, observer_name)`: Elimina a un observador de un juego específico.
*   `list_all_players()`: Devuelve una lista de todos los jugadores conectados actualmente al servidor, incluyendo su ID y nombre de juego asociados.
*   `stop_server()`: Solicita que el servidor se apague.
*   `restart_server()`: Solicita que el servidor se reinicie (borra todos los juegos actuales).
*   `set_logging_config(host, port)`: Configura el servidor para enviar sus registros a un servidor de registros remoto en la dirección y el puerto especificados.
*   `get_cert_expiration()`: Devuelve la fecha de expiración del certificado TLS del servidor en formato ISO.
*   `set_logging_enabled(enabled)`: Activa (`True`) ou desactiva (`False`) los registros en el servidor.

---

### `GameClient(host='127.0.0.1', port=65432, password=None, use_tls=False)`
El punto de entrada principal para que un cliente se conecte a un `GameServer`.

*   **`password`** (`str`, opcional): La contraseña global del servidor.
*   **`use_tls`** (`bool`, opcional): Si es `True`, el cliente se conectará usando TLS.

#### Métodos
*   `discover_servers(timeout=2)` (método estático): Escanea la red local en busca de instancias de `GameServer`.
*   `create_game(**game_options)`: Solicita al servidor que cree una nueva partida. Devuelve un objeto proxy `RemoteGame`.
*   `list_games()`: Devuelve un diccionario de todas las partidas activas (no finalizadas) en el servidor.

---

### `RemoteGame`
Un objeto proxy que representa una partida en el servidor.

#### Métodos
*   `add_player(player, password=None)`: Añade un `Player` a la partida remota.
*   `add_observer(observer)`: Añade un `Observer` a la partida remota.
*   `set_state(new_state)`: Sobrescribe el diccionario `custom_state` de la partida en el servidor.

#### Propiedades
*   **`state`**: Devuelve un diccionario que contiene tanto el `GameState` como el estado personalizado. Ejemplo: `{'status': 'in_progress', 'custom': {'score': 100}}`.
*   **`observers`**: Devuelve una lista de nombres de los observadores en la partida.

## Servidor de Registros Autónomo

El paquete `multiplayer` incluye un servidor de registros autónomo que se puede usar para recibir y mostrar registros de múltiples instancias de `GameServer`.

### `multiplayer-log-server [--port PORT] [--color-mode MODE]`
Inicia el servidor de registros autónomo.

*   **`--port`** (`int`, opcional): El puerto TCP en el que escuchar. Por defecto es `5000`.
*   **`--color-mode`** (`str`, opcional): El modo de coloración para los registros. Las opciones son:
    *   `level`: Colorea los registros según su criticidad (ej. INFO es verde, ERROR es rojo). Este es el modo predeterminado.
    *   `origin`: Colorea los registros según el nombre del registrador (ej. `GameServer`, `GameClient`, `GameAdmin`, etc.). Esto ayuda a diferenciar los mensajes de diferentes fuentes.

## Servidor de Juegos Autónomo

### `multiplayer-server [OPTIONS]`
Inicia un servidor de juegos autónomo.

*   **`--host`** (`str`): Dirección del host en la que escuchar. Por defecto es `0.0.0.0`.
*   **`--port`** (`int`): Puerto en el que escuchar. Por defecto es `65432`.
*   **`--password`** (`str`): Contraseña global del servidor.
*   **`--admin-password`** (`str`): Contraseña de administración.
*   **`--use-tls`**: Habilita el cifrado TLS v1.3.
*   **`--tls-domain`** (`str`): Nombre de dominio para el certificado. Por defecto es `localhost`.
*   **`--tls-cert`** (`str`): Ruta a un archivo de certificado PEM.
*   **`--tls-key`** (`str`): Ruta a un archivo de clave privada PEM.
*   **`--tls-cert-dir`** (`str`): Ruta a un directorio que contenga certificados PEM (`cert.pem`, `RSA-cert.pem` o `ECC-cert.pem`) y claves. Esto es particularmente útil para volúmenes Docker.
*   **`--tls-self-signed`**: Genera un certificado auto-firmado si faltan los archivos (comportamiento predeterminado).
*   **`--no-self-signed`**: Desactiva la generación automática de certificados auto-firmados.
*   **`--name`** (`str`): Nombre legible por humanos para la instancia del servidor.

## Funciones de Utilidad

### Sugerencias de Nombres

#### `register_name_category(category_name, data, category_type)`
Registra una nueva categoría personalizada.

*   **`category_name`** (`str`): El nombre de la nueva categoría.
*   **`data`** (`list` o `str`): Una lista de nombres, o la ruta a un archivo de texto.
*   **`category_type`** (`str`): `"game"` o `"player"`.

---

#### `unregister_name_category(category_name)`
Elimina una categoría personalizada. Devuelve `True` si tiene éxito.

---

#### `get_available_categories(category_type="all")`
Devuelve una lista de categorías de nombres disponibles.

*   **`category_type`** (`str`): `"all"`, `"game"`, o `"player"`.

---

#### `suggest_game_name(category=None)`
Sugiere un nombre aleatorio para una partida.

---

#### `suggest_player_name(category=None)`
Sugiere un nombre aleatorio para un jugador.

## Excepciones

*   **`MultiplayerError`**: Excepción base para todos los errores del módulo.
*   **`GameLogicError`**: Para errores en las reglas del juego.
*   **`PlayerLimitReachedError`**: Lanzada al añadir un jugador a una partida llena.
*   **`ObserverLimitReachedError`**: Lanzada al añadir un observador a una partida qui ha alcanzado su límite de observadores.
*   **`GameNotFoundError`**: Lanzada cuando un cliente solicita un `id` de partida que no existe.
*   **`NetworkError`**: Excepción base para prob