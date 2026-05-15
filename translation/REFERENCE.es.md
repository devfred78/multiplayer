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
*   `add_player(player, password=None)`: Añade un objeto `Player` o `PersistentPlayer` a la partida. La contraseña es obligatoria si la partida está protegida por contraseña.
*   `remove_player(player_id)`: Elimina un jugador de la partida por su ID.
*   `add_observer(observer, password=None)`: Añade un objeto `Observer` o `PersistentPlayer` a la partida. La contraseña es obligatoria si `observer_password` (o `password`) está configurado.
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

> **Nota: `custom_state` vs `attributes`**
> - **`attributes`** (Metadatos estáticos): Definidos al momento de la creación mediante `**kwargs`. Se utilizan para configuraciones que rara vez cambian (ej: `difficulty`, `map`).
> - **`custom_state`** (Estado dinámico): Un diccionario para la lógica evolutiva del juego (ej: posiciones de las piezas, puntuaciones). En el juego en red, usa `client.set_state()` para sincronizar este estado en el servidor.

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

### `PersistentPlayer(name, password, role=PlayerRole.PLAYER, managed_groups=None, **kwargs)`
Representa una cuenta de jugador persistente (hereda de `Player`).

*   **`name`** (`str`): El nombre del jugador (único en el servidor).
*   **`password`** (`str`): La contraseña de la cuenta.
*   **`role`** (`PlayerRole`, opcional): El rol del jugador. Por defecto es `PlayerRole.PLAYER`.
*   **`managed_groups`** (`list`, opcional): Una lista de IDs de grupos gestionados por este jugador (si el rol es `GROUP_ADMIN`).
*   **`**kwargs`**: Atributos personalizados para el jugador.

#### Propiedades
*   Todas las propiedades de `Player`.
*   **`password`**: La contraseña de la cuenta.
*   **`role`**: El rol del jugador (`PlayerRole.PLAYER`, `PlayerRole.GROUP_ADMIN`, o `PlayerRole.SERVER_ADMIN`).
*   **`managed_groups`**: Lista de IDs de grupos que el jugador puede gestionar.

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

### `PlayerRole` (Enum)
Una enumeración para el rol de un jugador persistente.

*   `PlayerRole.PLAYER`: Un jugador estándar que puede unirse y participar en juegos.
*   `PlayerRole.GROUP_ADMIN`: Un jugador que puede gestionar juegos dentro de grupos específicos a los que está asignado. Este rol incluye todos los permisos de un `PLAYER`.
*   `PlayerRole.SERVER_ADMIN`: Un jugador con acceso administrativo completo al servidor. Este rol engloba el rol de `GROUP_ADMIN`, el cual a su vez puede desempeñar el rol de `PLAYER`.

---

### `GameState` (Enum)
Una enumeración que representa el estado actual de una partida.

*   `GameState.PENDING`: La partida ha sido creada pero aún no ha comenzado. Este estado está dedicado a la espera de que los jugadores se unan. Los jugadores pueden unirse o salir.
*   `GameState.PAUSING`: La partida está actualmente en pausa. Este estado se utiliza cuando una partida que estaba en curso se suspende temporalmente.
*   `GameState.IN_PROGRESS`: La partida está actualmente activa. Se pueden realizar movimientos y se aplica la lógica de turnos.
*   `GameState.FINISHED`: La partida ha terminado. No se pueden realizar más movimientos y los resultados son definitivos.

---

## Clases de Red

Estas clases gestionan la arquitectura cliente-servidor.

### `GameServer(host='0.0.0.0', port=65432, password=None, admin_password=None, use_tls=False, tls_domain="localhost", tls_cert=None, tls_key=None, tls_self_signed=True, logging_host=None, logging_port=None, name=None, unencrypted_port=None, hidden=False)`
Gestiona las sesiones de juego y maneja las peticiones de red.

*   **`host`** (`str`): La dirección del host a la que vincularse. Usa `'0.0.0.0'` para hacerlo accesible en la red local.
*   **`port`** (`int`): El puerto TCP en el que escuchar los comandos del juego.
*   **`password`** (`str`, opcional): Una contraseña global para proteger el servidor.
*   **`admin_password`** (`str`, opcional): Una contraseña para acceso administrativo.
*   **`use_tls`** (`bool`, opcional): Si es `True`, habilita el cifrado TLS v1.3 para todas las comunicaciones. Por defecto es `False`.
*   **`tls_domain`** (`str`, opcional): Nombre de dominio a incluir en el certificado generado. Por defecto es `"localhost"`.
*   **`tls_cert`** (`str`, opcional): Ruta a un archivo de certificado PEM. Este archivo debe ser una "cadena completa" (incluyendo el certificado del dominio y los certificados intermedios) o tener un archivo de "cadena" correspondiente en el mismo directorio (ej: `cert.pem` y `chain.pem`, or `ECC-cert.pem` y `ECC-chain.pem`). Si solo se proporciona uno de `tls_cert` o `tls_key` mientras `tls_self_signed` es `False`, el servidor no se iniciará.
*   **`tls_key`** (`str`, opcional): Ruta a un archivo de clave privada PEM. Si solo se proporciona uno de `tls_cert` o `tls_key` mientras `tls_self_signed` es `False`, el servidor no se iniciará.
*   **`tls_self_signed`** (`bool`, opcional): Si es `True`, genera un certificado auto-firmado si falta `tls_cert` o `tls_key`. Si es `False`, se deben proporcionar ambos. Por defecto es `True`.
*   **`logging_host`** (`str`, opcional): La dirección del host de un servidor de registros al que enviar los registros.
*   **`logging_port`** (`int`, opcional): El puerto del servidor de registros.
*   **`name`** (`str`, opcional): Un nombre para la instancia del servidor.
*   **`unencrypted_port`** (`int`, opcional): Puerto para conexiones no cifradas cuando TLS está habilitado.
*   **`hidden`** (`bool`, opcional): Si es `True`, el servidor no responderá a las peticiones de descubrimiento de red. Por defecto es `False`.

#### Métodos
*   `start()`: Inicia el servidor en un proceso de segundo plano.
*   `stop()`: Detiene el servidor.

---

### `GameClient(host='127.0.0.1', port=65432, password=None, use_tls=False, auth_user=None, auth_password=None)`
El punto de entrada principal para que un cliente se conecte a un `GameServer`.

*   **`host`** (`str`): La dirección IP del servidor.
*   **`port`** (`int`): El puerto TCP del servidor.
*   **`password`** (`str`, opcional): La contraseña global del servidor.
*   **`use_tls`** (`bool`, opcional): Si es `True`, el cliente se conectará usando TLS. Por defecto es `False`.
*   **`auth_user`** (`str`, opcional): El nombre de una cuenta de jugador persistente.
*   **`auth_password`** (`str`, opcional): La contraseña de la cuenta de jugador persistente.

#### Métodos
*   `discover_servers(timeout=2)` (método estático): Escanea la red local en busca de instancias de `GameServer` en ejecución.
    *   **Devuelve**: Una `list` de tuplas `(host, port, name)` que representan los servidores descubiertos.
*   `create_game(group_id=None, **game_options)`: Solicita al servidor crear un nuevo juego.
    *   **`group_id`** (`str`, opcional): El ID del grupo donde se debe crear el juego.
    *   **`**game_options`**: Opciones de configuración para el juego. Estas coinciden con los argumentos del constructor de la clase `Game`:
        *   `name` (`str`): El nombre de la sesión de juego.
        *   `max_players` (`int`): Número máximo de jugadores permitidos.
        *   `max_observers` (`int`): Número máximo de observadores permitidos.
        *   `turn_based` (`bool`): Indica si el juego es por turnos.
        *   `password` (`str`): Contraseña requerida para que los jugadores se unan.
        *   `observer_password` (`str`): Contraseña específica para los observadores.
        *   Cualquier otro argumento con nombre se almacenará como un atributo personalizado en la propiedad `attributes` del juego.
    *   **Devuelve**: Un objeto proxy `RemoteGame`.
*   `list_games()`: Devuelve todos los juegos activos (estado diferente de `GameState.FINISHED`).
    *   **Devuelve**: Un `dict` donde las claves son IDs de juegos (`str`) y los valores son diccionarios que contienen las propiedades del juego:
        *   `name` (`str`): El nombre de la sesión de jeu.
        *   `state` (`GameState`): El estado actual del juego (por ejemplo, `GameState.PENDING`, `GameState.IN_PROGRESS`).
        *   `attributes` (`dict`): Atributos personalizados del juego.
        *   `players_count` (`int`): Número de jugadores actualmente en el juego.
        *   `max_players` (`int`): Número máximo de jugadores permitidos.
        *   `observers_count` (`int`): Número de observadores actualmente en el juego.
        *   `max_observers` (`int`): Número máximo de observadores permitidos.
        *   `custom_state` (`dict`): El estado personalizado del juego.
        *   `include_finished` (`bool`, opcional): Si es `True`, también devuelve los juegos en el estado `GameState.FINISHED`. Solo disponible para acciones que requieren permisos superiores.
*   `create_group(name, admin_password=None, **attributes)`: Solicita al servidor crear un nuevo grupo de juegos.
    *   **Devuelve**: Un objeto proxy `RemoteGroup`.
*   `list_groups()` : Devuelve todos los grupos de juegos en el servidor.
    *   **Devuelve**: Un `dict` donde las claves son IDs de grupo (`str`) y los valores son objetos `RemoteGroup`.
*   `create_account(name, password, role=PlayerRole.PLAYER, managed_groups=None, **attributes)`: Crea una cuenta de jugador persistente en el servidor.
    *   **Error**: `UserAlreadyExistsError` si ya existe una cuenta con el mismo nombre.
    *   **Devuelve**: Un `dict` que representa los datos del jugador creado:
        *   `player_id` (`str`): El ID único de la cuenta.
        *   `name` (`str`): El nombre de la cuenta.
        *   `role` (`PlayerRole`): El rol asignado.
*   `get_server_admin()`: Devuelve una instancia de `ServerAdmin` utilizando las credenciales actuales del cliente.
    *   **Error**: `AuthenticationError` si el cliente no está autenticado con una cuenta persistente o no tiene permisos de `SERVER_ADMIN`.
*   `get_group_admin(group_id)`: Devuelve una instancia de `GroupAdmin` para el grupo especificado utilizando las credenciales actuales del cliente.
    *   **Error**: `AuthenticationError` si el cliente no está autenticado con una cuenta persistente o no tiene permisos de administración para el grupo especificado.
*   `register_remote_game(game_id)`: Crea y devuelve un objeto `RemoteGame` asociado con el ID de juego especificado.
    *   **`game_id`** (`str`): El ID del juego para asociar con el `RemoteGame`.
    *   **Devuelve**: Un objeto `RemoteGame`.
*   `unregister_remote_game(remote_game)`: Destruye un objeto `RemoteGame` y limpia sus recursos internos.
    *   **`remote_game`** (`RemoteGame`): El objeto `RemoteGame` a destruir.
*   `set_logging_for_client(host, port, name=None)`: Configura el cliente para enviar sus registros a un servidor de registros remoto.

---

### `ServerAdmin(host='127.0.0.1', port=65432, admin_password=None, use_tls=False, auth_user=None, auth_password=None)`
Una clase de cliente para que los administradores gestionen un `GameServer` (hereda de `GameClient`).

*   Todos los argumentos y parámetros de conexión de `GameClient`.
*   **`admin_password`** (`str`, opcional): La contraseña de administrador del servidor (global).

#### Métodos
*   Todos los métodos de `GameClient`.
*   `list_all_server_games()`: Recupera un diccionario de todos los juegos en el servidor (incluidos aquellos con `GameState.FINISHED`) organizado por ID.
    *   **Devuelve**: Un `dict` con el mismo formato que `GameClient.list_games()`.
*   `get_server_info()`: Devuelve información sobre el servidor.
    *   **Devuelve**: Un `dict` con las siguientes claves:
        *   `server_name` (`str`): El nombre asignado al servidor.
        *   `games_count` (`int`): Número total de juegos actualmente en el servidor.
        *   `active_games` (`list` de `str`): Una lista de IDs para juegos que no están en el estado `FINISHED`.
*   `kick_player(game_id, player_id)`: Elimina a un jugador de un juego específico por su ID.
*   `kick_observer(game_id, observer_id)`: Elimina a un observador de un juego específico por su ID.
*   `list_all_players()`: Enumera todos los jugadores conocidos actualmente por el servidor.
    *   **Devuelve**: Una `list` de `dict`, donde cada diccionario contiene:
        *   `name` (`str`): El nombre del jugador.
        *   `attributes` (`dict`): Los atributos personalizados del jugador.
        *   `game_id` (`dict`): Un diccionario donde las claves son los ID de los juegos (`str`) y los valores son los nombres de los juegos (`str`), representando los juegos en los que el jugador está actualmente.
        *   `game_name` (`dict`): Un diccionario donde las claves son los ID de los juegos (`str`) y los valores son los nombres de los juegos (`str`). Similitud a `game_id` para facilitar el acceso.
        *   `game_details` (`list` de `dict`): Una lista detallada de los juegos en los que participa el jugador, donde cada entrada contiene:
            *   `game_id` (`str`): El ID del juego.
            *   `game_name` (`str`): El nombre del juego.
            *   `attributes` (`dict`): Los atributos específicos del jugador en este juego (fusionados con los atributos persistentes si corresponde).
        *   `connected` (`bool`): `True` si el jugador está actualmente conectado a una sesión de juego.
        *   `is_persistent` (`bool`): `True` si se trata de una cuenta persistente.
*   `stop_server()`: Solicita el apagado del servidor.
*   `restart_server()` : Solicita el reinicio del servidor (borra todos los juegos actuales).
*   `set_logging_for_server(host, port)`: Configura el servidor para enviar sus registros a un servidor de registros remoto en la dirección y puerto especificados.
*   `get_cert_expiration()`: Devuelve la fecha de expiración del certificado TLS del servidor.
    *   **Devuelve**: Un `str` que representa la fecha de expiración en formato ISO, o `None` si no se utiliza TLS.
*   `set_logging_enabled(enabled)`: Activa (`True`) o desactiva (`False`) el registro en el servidor.
*   `set_server_password(new_password)`: Establece una nueva contraseña para el servidor.
*   `set_admin_password(new_password)`: Establece una nueva contraseña de administrador para el servidor.
*   `remove_group(group_id)` : Elimina un grupo de juegos del servidor por su ID.
*   `set_persistent_players_enabled(enabled)`: Activa (`True`) o desactiva (`False`) la creación de cuentas de jugadores persistentes en el servidor. Cuando se desactiva, los jugadores persistentes creados anteriormente permanecen activos y utilizables.
*   `set_server_hidden(hidden)`: Establece el servidor como oculto (`True`) o visible (`False`) para el descubrimiento de red.
*   `update_persistent_player(name, role=None, managed_groups=None, password=None, **attributes)`: Actualiza la información de un jugador persistente.
*   `remove_persistent_player(name)`: Elimina una cuenta de jugador persistente del servidor.

---

### `GroupAdmin(group_id, host='127.0.0.1', port=65432, group_admin_password=None, use_tls=False, auth_user=None, auth_password=None)`
Una clase de cliente para que los administradores de grupo gestionen juegos dentro de un `GameGroup` específico (hereda de `GameClient`).

*   Todos los argumentos y parámetros de conexión de `GameClient`.
*   **`group_id`** (`str`): El ID único del grupo a gestionar.
*   **`group_admin_password`** (`str`, opcional): La contraseña administrativa para este grupo.

#### Métodos
*   Todos los métodos de `GameClient`.
*   `list_all_group_games()`: Recupera un diccionario de todos los juegos pertenecientes a este grupo (incluidos aquellos con `GameState.FINISHED`) organizado por ID.
    *   **Devuelve**: Un `dict` con el mismo formato que `GameClient.list_games()`.
*   `kick_player(game_id, player_id)`: Elimina a un jugador de un juego específico en el grupo por su ID.
*   `kick_observer(game_id, observer_id)`: Elimina a un observador de un juego específico en el grupo por su ID.
*   `set_group_admin_password(new_password)`: Establece una nueva contraseña de administrador para este grupo.

---

### `RemoteGroup`
Un objeto proxy que representa un grupo de juegos que se ejecuta en el servidor.

*Normalmente no se crea este objeto directamente, sino que se obtiene de `client.create_group()` o `client.list_groups()`.*

#### Métodos
*   `create_game(**game_options)`: Crea un nuevo juego dentro de este grupo. Soporta las mismas `game_options` que `GameClient.create_game()`.
    *   **Devuelve**: Un objeto proxy `RemoteGame`.
*   `list_games()`: Devuelve los juegos activos pertenecientes a este grupo (estado diferente de `GameState.FINISHED`).
    *   **Devuelve**: Un `dict` donde las claves sont IDs de juegos (`str`) y los valores son diccionarios que contienen las propiedades del juego (mismo formato que `GameClient.list_games()`).

#### Propiedades
*   **`group_id`**: El ID único del grupo.
*   **`name`**: El nombre del grupo.
*   **`attributes`**: Un dictionnaire de atributos personalizados para el grupo.

---

### `RemoteGame`
Un objeto proxy que representa un juego que se ejecuta en el servidor.

*Normalmente no se crea este objeto directamente, sino que se obtiene de `client.create_game()`.*

#### Métodos
*   `add_player(player, password=None)`: Añade un `Player` o un `PersistentPlayer` al juego remoto. Se requiere la contraseña si el juego está protegido por contraseña. Si el jugador es un `PersistentPlayer`, los atributos proporcionados en el objeto `player` se fusionarán con los atributos globales de la cuenta para esta sesión de juego.
*   `add_observer(observer, password=None)`: Añade un `Observer` o un `PersistentPlayer` al juego remoto. Se requiere la contraseña si `observer_password` (o `password`) está configurado para el juego. Si el observador es un `PersistentPlayer`, los atributos proporcionados en el objeto `observer` se fusionarán con los atributos globales de la cuenta para esta sesión de juego.
*   `set_state(new_state)`: Sobrescribe el diccionario `custom_state` del juego en el servidor.
*   (Otros métodos son iguales a los de la clase `Game` local).

#### Propiedades
*   **`state`** : Devuelve el estado actual del juego remoto.
    *   **Devuelve**: Un `dict` con:
        *   `status` (`GameState`): El valor del enum del estado del juego.
        *   `custom` (`dict`): El diccionario `custom_state` del juego.
*   **`observers`** : Devuelve los observadores que están actualmente en el juego.
    *   **Devuelve**: Una `list` de `dict`, cada uno con:
        *   `id` (`str`): El ID del observador.
        *   `name` (`str`): El nombre del observador.
        *   `attributes` (`dict`): Los atributos del observador.
*   **`players`** : Devuelve los jugadores que están actualmente en el juego.
    *   **Devuelve**: Una `list` de `dict`, cada uno con:
        *   `id` (`str`): El ID del jugador.
        *   `name` (`str`): El nombre del jugador.
        *   `attributes` (`dict`): Los atributos del jugador.

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
*   **`--unencrypted-port`** (`int`): Puerto para conexiones no cifradas. Solo es relevante cuando `--use-tls` está habilitado. Esto permite que el servidor sea accesible tanto a través de TLS como de texto plano en diferentes puertos.
*   **`--name`** (`str`): Nombre legible para humanos para la instancia del servidor.
*   **`--hidden`**: Oculta el servidor del descubrimiento de red.

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
*   **MultiplayerError**: Excepción base para todos los errores específicos del módulo.
*   **GameLogicError**: Para errores en las reglas del juego.
*   **PlayerLimitReachedError**: Se lanza al añadir un jugador a un juego lleno.
*   **ObserverLimitReachedError**: Se lanza al añadir un observador a un juego que ha alcanzado su límite.
*   **GameNotFoundError**: Se lanza cuando se solicita un id de juego que no existe.
*   **NetworkError**: Excepción base para problemas de red.
*   **ConnectionError**: Se lanza cuando falla la conexión al servidor.
*   **ServerError**: Se lanza para errores genéricos del servidor.
*   **AuthenticationError**: Se lanza para fallos de autenticación.
*   **PlayerAlreadyInGameError**: Se lanza al intentar añadir un jugador u observador que ya está presente en el juego.
*   **KickedError**: Se lanza cuando un jugador u observador ha sido expulsado del juego por un administrador.
*   **UserAlreadyExistsError**: Se lanza al intentar crear un usuario que ya existe.
*   **`GroupNotFoundError`**: Se lanza cuando no se encuentra un `id` de grupo en el servidor.

## Ejemplos

### 1. Juego Local Simple
Creación de una sesión de juego básica localmente sin servidor.

```python
from multiplayer.game import Game, Player

# Crear un juego y jugadores
game = Game(name="Mi Juego de Ajedrez", turn_based=True)

# Inicializar el estado inicial del juego
game.custom_state = {"tablero": "estándar", "medios_movimientos": 0}

alice = Player("Alice")
bob = Player("Bob")

# Añadir jugadores y comenzar
game.add_player(alice)
game.add_player(bob)
game.start()

print(f"Juego '{game.name}' iniciado con estado: {game.state}")
```

### 2. Conectarse a un Servidor y Crear una Cuenta
Conexión a un servidor de juegos remoto y configuración de una cuenta persistente.

```python
from multiplayer.client import GameClient
from multiplayer.data import PlayerRole

client = GameClient(host="localhost", port=65432)
client.connect()

# Crear una cuenta persistente
account = client.create_account(
    name="Charlie", 
    password="password_seguro", 
    role=PlayerRole.PLAYER
)
print(f"Cuenta creada para {account['name']} con rol {account['role']}")

client.disconnect()
```

### 3. Gestión de Grupos y Juegos (Admin)
Creación de un grupo y una sesión de juego como Administrador de Grupo.

```python
from multiplayer.client import GameClient

client = GameClient(host="localhost", port=65432)
client.connect(password="pass_servidor")

# Iniciar sesión como administrador de grupo
admin = client.login("AdminUser", "admin_pass")

# Crear un grupo y un juego dentro de él
group = admin.create_group("Torneo A")
remote_game = group.create_game(name="Partido Final", max_players=2)

print(f"Juego '{remote_game.ID}' creado en el grupo '{group.name}'")
```

### 4. Juego por Turnos con Observadores
Gestión de un juego por turnos con espectadores en el servidor.

```python
from multiplayer.client import GameClient
from multiplayer.game import Player

client = GameClient(host="localhost", port=65432)
client.connect()

# Obtener la lista de las partidas activas en el servidor
active_games = client.list_games()
print(f"Partidas activas en el servidor: {list(active_games.keys())}")

# Unirse a la primera partida activa como jugador
game_id = list(active_games.keys())[0]
remote_game = client.register_remote_game(game_id)
me = Player("Dave")
remote_game.add_player(me)

# Avanzar turno (si es tu turno)
if remote_game.current_player.name == "Dave":
    remote_game.next_turn()

# Listar observadores
for obs in remote_game.observers:
    print(f"Espectador: {obs['name']}")
```

### 5. Avanzado: TLS, Atributos Personalizados y Registro
Uso de cifrado, metadatos y el servidor de registros autónomo.

```python
from multiplayer.client import GameClient
from multiplayer.game import Game

# Conectar usando TLS
client = GameClient(host="game.example.com", port=65432, use_tls=True)
client.connect()

# Crear un juego con metadatos personalizados
game_options = {
    "name": "Liga Pro",
    "difficulty": "experto",
    "map": "valles_marineris"
}
remote_game = client.create_game(**game_options)

# Los registros se envían automáticamente al servidor de logs
# si el GameServer se configuró con --port
print(f"Atributos del juego: {remote_game.attributes}")
```

### 6. Gestión del Servidor
Este ejemplo muestra cómo lanzar y gestionar un servidor de juegos.

```python
import time
from multiplayer.server import GameServer

# Inicializar el servidor
# host: "0.0.0.0" para escuchar en todas las interfaces
# port: 65432 (por defecto)
# password: Contraseña opcional para unirse al servidor
# admin_password: Contraseña requerida para ServerAdmin y GroupAdmin
server = GameServer(
    host="0.0.0.0",
    port=65432,
    password="player_pass",
    admin_password="admin_super_secret",
    name="Mi Servidor de Juegos Profesional",
    use_tls=True,
    tls_self_signed=True
)

# Iniciar el servidor (se ejecuta en un proceso separado)
server.start()

try:
    print("El servidor está en ejecución. Presione Ctrl+C para detenerlo.")
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Deteniendo el servidor...")
finally:
    # Detener el servidor de forma segura
    server.stop()
```
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               IT�IT~H8�H8�H8�H8�H8�G8�G8�G8�G8�G8�F8�F8�F8�F8�F8�EV
EV	CTJCT'CTCS�CS�CSvBT?BTBS�BS�BS�BSkAT0AT
AS�AS�AS�AS\@T/@T@S�@S�@S�@S[>8�>8�>8�>8�>8�=8�=8�=8�=8�=8�<8�<8�<8�<8�<8�;8�;8�;8�;8�;8�:8�:8�:8�:8�:8�98�98�98�98�98�88�88�88�88�88�7C\7CZ7CX7CV7CR6C[6CY6CW6CU6CQ5RK5F3U�       �