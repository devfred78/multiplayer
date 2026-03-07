[English](../REFERENCE.md) | **Español** | [Français](REFERENCE.fr.md)

# Referencia de la API para el Módulo `multiplayer`

Este documento proporciona una referencia detallada de la API pública del módulo `multiplayer`.

## Clases Principales

Estas clases se utilizan para gestionar la lógica del juego, ya sea localmente o en el servidor.

### `Game(max_players=None, turn_based=False, password=None, **kwargs)`
Representa una única sesión de juego.

*   **`max_players`** (`int`, opcional): El número máximo de jugadores que pueden unirse. Por defecto es `None` (ilimitado).
*   **`turn_based`** (`bool`, opcional): `True` si el juego es por turnos, `False` para juego simultáneo. Por defecto es `False`.
*   **`password`** (`str`, opcional): Una contraseña para proteger esta partida específica.
*   **`**kwargs`**: Atributos personalizados para la partida (ej., `name="Mi Juego"`).

#### Métodos
*   `add_player(player, password=None)`: Añade un objeto `Player` a la partida. Se requiere la `password` si la partida está protegida.
*   `remove_player(player_name)`: Elimina a un jugador de la partida por su nombre.
*   `start()`: Inicia la partida.
*   `pause()`: Pausa la partida.
*   `resume()`: Reanuda una partida pausada.
*   `stop()`: Finaliza la partida.
*   `next_turn()`: Avanza al siguiente jugador en una partida por turnos.

#### Propiedades
*   **`players`**: Una lista de objetos `Player` en la partida.
*   **`state`**: El `GameState` actual de la partida (ej., `GameState.IN_PROGRESS`).
*   **`custom_state`**: Un diccionario para almacenar cualquier dato específico del juego.
*   **`attributes`**: Un diccionario de atributos personalizados.
*   **`current_player`**: El objeto `Player` activo en una partida por turnos.

---

### `Player(name, **kwargs)`
Representa a un jugador.

*   **`name`** (`str`): El nombre del jugador.
*   **`**kwargs`**: Atributos personalizados para el jugador (ej., `score=100`).

#### Propiedades
*   **`name`**: El nombre del jugador.
*   **`attributes`**: Un diccionario de los atributos personalizados del jugador.

---

### `GameState` (Enum)
Una enumeración para el estado de la partida.

*   `GameState.PENDING`
*   `GameState.IN_PROGRESS`
*   `GameState.FINISHED`

## Clases de Red

Estas clases gestionan la arquitectura cliente-servidor.

### `GameServer(host='0.0.0.0', port=65432, password=None, use_tls=False)`
Gestiona las sesiones de juego y las peticiones de red.

*   **`host`** (`str`): La dirección del host a la que vincularse. Usa `'0.0.0.0'` para que sea accesible en la red local.
*   **`port`** (`int`): El puerto TCP en el que escuchar los comandos del juego.
*   **`password`** (`str`, opcional): Una contraseña global para proteger el servidor.
*   **`use_tls`** (`bool`, opcional): Si es `True`, habilita el cifrado TLS v1.3. Por defecto es `False`.

#### Métodos
*   `start()`: Inicia el servidor en un proceso en segundo plano.
*   `stop()`: Detiene el servidor.

---

### `GameClient(host='127.0.0.1', port=65432, password=None, use_tls=False)`
El punto de entrada principal para que un cliente se conecte a un `GameServer`.

*   **`host`** (`str`): La dirección IP del servidor.
*   **`port`** (`int`): El puerto TCP del servidor.
*   **`password`** (`str`, opcional): La contraseña global del servidor.
*   **`use_tls`** (`bool`, opcional): Si es `True`, el cliente se conectará usando TLS. Por defecto es `False`.

#### Métodos
*   `discover_servers(timeout=2)` (método estático): Escanea la red local en busca de instancias de `GameServer`. Devuelve una lista de tuplas `(host, port)`.
*   `create_game(**game_options)`: Solicita al servidor que cree una nueva partida. Devuelve un objeto proxy `RemoteGame`. Puede incluir una `password` para la partida.
*   `list_games()`: Devuelve un diccionario de todas las partidas activas en el servidor.

---

### `RemoteGame`
Un objeto proxy que representa una partida en el servidor.

*Normalmente no se crea este objeto directamente, sino que se obtiene de `client.create_game()`.*

#### Métodos
*   `add_player(player, password=None)`: Añade un `Player` a la partida remota. Se requiere la `password` si la partida está protegida.
*   `set_state(new_state)`: Sobrescribe el diccionario `custom_state` de la partida en el servidor.
*   (Los otros métodos son iguales a los de la clase local `Game`.)

#### Propiedades
*   **`state`**: Devuelve el diccionario `custom_state` de la partida desde el servidor. **Nota:** Este es un cambio que rompe la compatibilidad con la v0.5.2. Ya no devuelve el enum `GameState`.

## Funciones de Utilidad

### Sugerencias de Nombres

#### `register_name_category(category_name, data, category_type)`
Registra una nueva categoría personalizada.

*   **`category_name`** (`str`): El nombre de la nueva categoría.
*   **`data`** (`list` o `str`): Una lista de nombres, o la ruta a un archivo de texto (un nombre por línea).
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
