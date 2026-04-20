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
*   **Seguridad Multinivel:** Soporta contraseñas para todo el servidor y por partida, con cifrado TLS v1.3 opcional.
*   **Descubrimiento Automático de Servidores:** Los clientes pueden encontrar automáticamente servidores en funcionamiento en la red local.
*   **Sugerencias de Nombres Extensibles:** Incluye una función de utilidad para sugerir nombres creativos para juegos y jugadores.
*   **Múltiples Partidas:** El servidor puede gestionar múltiples sesiones de juego simultáneamente, y la lista de partidas ahora se filtra para ocultar las partidas finalizadas.
*   **Manejo de Errores Robusto:** Un conjunto claro de excepciones personalizadas para la lógica del juego y problemas de red.

## Instalación

Este módulo requiere la biblioteca `cryptography` para sus funciones de seguridad.

```sh
pip install multiplayer-0.1.0-py3-none-any.whl
```
*Reemplaza `multiplayer-0.1.0-py3-none-any.whl` con el nombre real del archivo descargado.*

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

### Uso Local
... (El resto del contenido es correcto)
