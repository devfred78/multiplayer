[English](../REFERENCE.md) | **Español** | [Français](REFERENCE.fr.md)

# Referencia de la API para el Módulo `multiplayer`

Este documento proporciona una referencia detallada de la API pública del módulo `multiplayer`.

## Clases Principales

### `Game(max_players=None, turn_based=False, password=None, **kwargs)`
Representa una única sesión de juego.
*   **`max_players`** (`int`, opcional): El número máximo de jugadores.
*   **`turn_based`** (`bool`, opcional): `True` si el juego es por turnos.
*   **`password`** (`str`, opcional): Una contraseña para proteger esta partida.
*   **`**kwargs`**: Atributos personalizados para la partida.

#### Propiedades
*   **`state`**: El `GameState` actual de la partida (ej., `GameState.IN_PROGRESS`).
*   **`custom_state`**: Un diccionario para almacenar cualquier dato específico del juego.

---

### `Player(name, **kwargs)`
Representa a un jugador.
*   **`name`** (`str`): El nombre del jugador.
*   **`**kwargs`**: Atributos personalizados para el jugador.

---

### `GameState` (Enum)
*   `GameState.PENDING`, `GameState.IN_PROGRESS`, `GameState.FINISHED`

## Clases de Red

### `GameServer(host='0.0.0.0', port=65432, password=None, use_tls=False)`
Gestiona las sesiones de juego y las peticiones de red.
*   **`password`** (`str`, opcional): Una contraseña global para proteger el servidor.
*   **`use_tls`** (`bool`, opcional): Si es `True`, habilita el cifrado TLS v1.3.

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
*   `set_state(new_state)`: Sobrescribe el diccionario `custom_state` de la partida en el servidor.

#### Propiedades
*   **`state`**: Devuelve un diccionario que contiene tanto el `GameState` como el estado personalizado. Ejemplo: `{'status': 'in_progress', 'custom': {'score': 100}}`.

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
*   **`GameNotFoundError`**: Lanzada cuando un cliente solicita un `id` de partida que no existe.
*   **`NetworkError`**: Excepción base para problemas de red.
*   **`ConnectionError`**: Lanzada cuando un cliente no puede conectarse al servidor.
*   **`ServerError`**: Lanzada para errores genéricos reportados por el servidor.
*   **`AuthenticationError`**: Lanzada para fallos de autenticación tanto del servidor como de la partida.
