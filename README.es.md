[English](README.md) | **Español** | [Français](README.fr.md)

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
*   **Estado de Juego Personalizado:** Un diccionario flexible (`custom_state`) para sincronizar cualquier dato específico del juego.
*   **Seguridad Multinivel:** Soporta contraseñas para todo el servidor y por partida, con cifrado TLS v1.3 opcional.
*   **Descubrimiento Automático de Servidores:** Los clientes pueden encontrar automáticamente servidores en funcionamiento en la red local.
*   **Sugerencias de Nombres Extensibles:** Incluye una función de utilidad para sugerir nombres creativos para juegos y jugadores.
*   **Múltiples Partidas:** El servidor puede gestionar múltiples sesiones de juego simultáneamente.
*   **Manejo de Errores Robusto:** Un conjunto claro de excepciones personalizadas para la lógica del juego y problemas de red.

## Instalación

Este módulo requiere la biblioteca `cryptography` para sus funciones de seguridad.

```sh
pip install multiplayer-0.1.0-py3-none-any.whl
```
*Reemplaza `multiplayer-0.1.0-py3-none-any.whl` con el nombre real del archivo descargado.*

## Uso

### Estado de Juego Personalizado

Una característica clave es la capacidad de gestionar tu propio estado de juego. El `custom_state` es un diccionario simple que puedes leer y escribir, perfecto para puntuaciones, posiciones o cualquier otro dato.

```python
# En un cliente
juego.set_state({
    "tablero": [["X", "O", ""], ["", "X", ""], ["O", "", ""]],
    "turno": "jugador2"
})

# En otro cliente
estado_actual = juego.state
print(estado_actual["turno"])
# > "jugador2"
```

### Uso Local

Puedes usar la clase `Game` directamente, incluso con una contraseña para validación local.

```python
from multiplayer import Game, Player, suggest_game_name

juego = Game(password="clave_juego_local")
juego.add_player(Player("Alice"), password="clave_juego_local")
juego.start()
```

### Uso en Red (Cliente-Servidor)

#### Configuración del Servidor
```python
from multiplayer import GameServer

# Iniciar un servidor seguro
servidor = GameServer(
    host='0.0.0.0',
    port=12345,
    password="mi_clave_servidor",
    use_tls=True
)
servidor.start()
```

#### Uso del Cliente
```python
from multiplayer import GameClient, Player, suggest_game_name

# 1. Descubrir y conectar al servidor
servidores = GameClient.discover_servers()
if not servidores:
    print("No se encontraron servidores.")
else:
    host, port = servidores[0]
    cliente = GameClient(
        host=host,
        port=port,
        password="mi_clave_servidor",
        use_tls=True
    )

    # 2. Crear una partida privada
    partida_privada = cliente.create_game(
        name=suggest_game_name(),
        password="mi_clave_partida"
    )

    # 3. Un jugador se une y establece el estado inicial
    partida_privada.add_player(Player("Charlie"), password="mi_clave_partida")
    partida_privada.set_state({"puntuacion": 0})
    partida_privada.start()
```

## Manejo de Errores

El módulo proporciona un conjunto de excepciones personalizadas, incluyendo `AuthenticationError` para las contraseñas del servidor y de la partida.

```python
from multiplayer import GameClient
from multiplayer.exceptions import ConnectionError, AuthenticationError

try:
    # ... conectar al cliente ...

    # Intentar unirse a una partida con la contraseña incorrecta
    juego.add_player(Player("Eve"), password="clave_incorrecta")

except AuthenticationError as e:
    print(f"La autenticación falló como se esperaba: {e}")
except ConnectionError as e:
    print(f"Ocurrió un error de conexión o descubrimiento: {e}")
```

## Contribuciones

¡Agradecemos las contribuciones! Por favor, consulta nuestras [Directrices de Contribución](CONTRIBUTING.es.md) para más detalles sobre cómo empezar.

## Ejecución de Pruebas

Para ejecutar las pruebas unitarias, necesitarás tener `pytest` instalado.

```sh
pip install pytest
```

Luego, puedes ejecutar las pruebas desde la raíz del proyecto:

```sh
pytest
```

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - consulta el archivo [LICENSE.md](LICENSE.md) para más detalles.
