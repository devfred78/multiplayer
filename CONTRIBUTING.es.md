[English](CONTRIBUTING.md) | **Español**

# Cómo Contribuir a Multiplayer

¡Estamos encantados de que te interese contribuir al proyecto `multiplayer`! Tu ayuda es muy apreciada. Al contribuir, puedes ayudar a que esta biblioteca sea aún mejor.

Ten en cuenta que este proyecto se publica con un [Código de Conducta del Contribuyente](CODE_OF_CONDUCT.es.md). Al participar en este proyecto, aceptas cumplir sus términos.

## Tabla de Contenidos
* [Reportar Errores](#reportar-errores)
* [Sugerir Mejoras](#sugerir-mejoras)
* [Tu Primera Contribución de Código](#tu-primera-contribución-de-código)
* [Proceso de Pull Request](#proceso-de-pull-request)

## Reportar Errores

Si encuentras un error, por favor, asegúrate de que no haya sido reportado previamente buscando en GitHub en la sección de [Issues](https://github.com/devfred78/multiplayer/issues).

Si no encuentras un issue abierto que aborde el problema, [abre uno nuevo](https://github.com/devfred78/multiplayer/issues/new). Asegúrate de incluir un **título y una descripción clara**, la mayor cantidad de información relevante posible y un **fragmento de código** o un **caso de prueba ejecutable** que demuestre el comportamiento esperado que no está ocurriendo.

## Sugerir Mejoras

Si tienes una idea para una nueva característica o una mejora para una existente, por favor, abre un issue para discutirla. Esto nos permite coordinar nuestros esfuerzos y evitar duplicar el trabajo.

1.  Busca en los [issues](https://github.com/devfred78/multiplayer/issues) para ver si la mejora ya ha sido sugerida.
2.  Si no, [abre un nuevo issue](https://github.com/devfred78/multiplayer/issues/new), proporcionando una descripción clara y detallada de la mejora propuesta y sus beneficios.

## Tu Primera Contribución de Código

¿Listo para contribuir con código? Aquí te explicamos cómo configurar `multiplayer` para el desarrollo local.

1.  **Haz un fork del repositorio** en GitHub.
2.  **Clona tu fork** localmente:
    ```sh
    git clone https://github.com/tu-usuario/multiplayer.git
    ```
3.  **Configura tu entorno.** Recomendamos usar un entorno virtual:
    ```sh
    cd multiplayer
    python -m venv .venv
    source .venv/bin/activate  # En Windows, usa `.venv\Scripts\activate`
    ```
4.  **Instala las dependencias**, incluyendo las herramientas de desarrollo y prueba:
    ```sh
    pip install -e .[dev]
    ```
5.  **Crea una nueva rama** para tus cambios:
    ```sh
    git checkout -b nombre-de-tu-mejora-o-correccion
    ```
6.  ¡Haz tus cambios!

## Proceso de Pull Request

1.  Asegúrate de que tu código se adhiera al estilo existente para mantener la coherencia.
2.  Ejecuta las pruebas para asegurarte de que tus cambios no rompan nada:
    ```sh
    pytest
    ```
3.  Añade nuevas pruebas para tu característica si es aplicable.
4.  Actualiza la documentación (`README.md`, `REFERENCE.md`, etc.) si has cambiado la API o añadido nuevas características.
5.  Confirma tus cambios con un mensaje de commit claro y descriptivo.
6.  Sube tu rama a tu fork en GitHub:
    ```sh
    git push origin nombre-de-tu-mejora-o-correccion
    ```
7.  **Envía un Pull Request** a la rama `main` del repositorio original de `multiplayer`. Proporciona un título y una descripción claros para tu PR, explicando el "qué" y el "porqué" de tus cambios.

¡Gracias por tu contribución!
