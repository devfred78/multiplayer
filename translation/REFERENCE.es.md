[English](../REFERENCE.md) | **Español** | [Français](REFERENCE.fr.md)

# Referencia de la API para el Módulo `multiplayer`

Este documento proporciona una referencia detallada de la API pública del módulo `multiplayer`.

## Clases Principales

### `Game(max_players=None, turn_based=False, password=None, max_observers=None, **kwargs)`
Representa una única sesión de juego.

*   **`max_players`** (`int`, opcional): El número máximo de jugadores.
*   **`max_observers`** (`int`, opcional): El número máximo de observadores.
*   **`turn_based`** (`bool`, opcional): `True` si el juego es por turnos.
*   **`password`** (`str`, opcional): Una contraseña para proteger esta partida.
*   **`**kwargs`**: Atributos personalizados para la partida.

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

### `GameServer(host='0.0.0.0', port=65432, password=None, admin_password=None, use_tls=False)`
Gestiona las sesiones de juego y las peticiones de red.

*   **`password`** (`str`, opcional): Una contraseña global para proteger el servidor.
*   **`admin_password`** (`str`, opcional): Una contraseña para acceso administrativo.
*   **`use_tls`** (`bool`, opcional): Si es `True`, habilita el cifrado TLS v1.3.

---

### `GameAdmin(host='127.0.0.1', port=65432, admin_password=None, use_tls=False)`
Una clase de cliente para que los administradores gestionen un `GameServer`.

*   **`admin_password`** (`str`, opcional): La contraseña de administrador para el servidor.
*   **`use_tls`** (`bool`, opcional): Si es `True`, el cliente se conectará usando TLS.

#### Métodos
*   `get_server_info()`: Devuelve información sobre el servidor (número de juegos, IDs activos).
*   `list_games()`: Devuelve una lista de todos los juegos activos.
*   `kick_player(game_id, player_name)`: Elimina a un jugador de un juego específico.
*   `kick_observer(game_id, observer_name)`: Elimina a un observador de un juego específico.
*   `list_all_players()`: Devuelve una lista de todos los jugadores conectados actualmente al servidor, incluyendo su ID y nombre de juego asociados.
*   `stop_server()`: Solicita que el servidor se apague.
*   `restart_server()`: Solicita que el servidor se reinicie (borra todos los juegos actuales).

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
*   **`NetworkError`**: Excepción base para problemas de red.
*   **`ConnectionError`**: Lanzada cuando un cliente no puede conectarse al servidor.
*   **`ServerError`**: Lanzada para errores genéricos reportad