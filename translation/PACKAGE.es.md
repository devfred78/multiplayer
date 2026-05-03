[English](../PACKAGE.md) | **Español** | [Français](PACKAGE.fr.md)

# Documentación del Contenedor Multiplayer

Esta guía describe cómo instalar, configurar y gestionar el contenedor Docker `multiplayer-server`.

## Instalación

### Docker Estándar
Descargue la imagen desde el GitHub Container Registry:
```bash
docker pull ghcr.io/devfred78/multiplayer-server:latest
```

### NAS Synology
1. Abra **Docker** (DSM 7.1) o **Container Manager** (DSM 7.2+).
2. Vaya a **Registro**, busque `ghcr.io/devfred78/multiplayer-server-synology`.
3. Descargue la etiqueta `latest` o una versión específica.

## Configuración

### Argumentos de Línea de Comandos
El servidor acepta los siguientes argumentos:
- `--host`: Dirección del host (por defecto: `0.0.0.0`).
- `--port`: Puerto de escucha (por defecto: `65432`).
- `--name`: Nombre de la instancia del servidor.
- `--password`: Contraseña global del servidor.
- `--admin-password`: Contraseña de administración.
- `--use-tls`: Habilita TLS v1.3.
- `--tls-cert-dir`: Directorio que contiene los certificados (mapeado a `/app/certs`).
- `--logging-host` / `--logging-port`: Detalles del servidor de registros centralizado.

### Certificados TLS
Para usar sus propios certificados:
1. Cree un directorio (ej: `./certs`) y coloque `cert.pem` y `privkey.pem` dentro.
2. Mapee este directorio a `/app/certs` en el contenedor.
3. Use `--use-tls --tls-cert-dir /app/certs --no-self-signed`.

## Ejecución y Gestión

### Iniciar el Contenedor
```bash
docker run -d \
  --name multiplayer-server \
  -p 65432:65432 \
  -v /ruta/a/certs:/app/certs \
  ghcr.io/devfred78/multiplayer-server:latest \
  --port 65432 --use-tls --tls-cert-dir /app/certs
```

### Detener e Iniciar
- **Detener**: `docker stop multiplayer-server`
- **Iniciar**: `docker start multiplayer-server`
- **Reiniciar**: `docker restart multiplayer-server`

### Interactuar con el Contenedor
- **Registros (Logs)**: `docker logs -f multiplayer-server`
- **Terminal (Shell)**: `docker exec -it multiplayer-server /bin/sh`

## Especificaciones de Synology

### DSM 7.1 (Docker)
- **Red**: Use el modo `bridge` y mapee el puerto `65432`.
- **Volumen**: Mapee su carpeta local de certificados a `/app/certs` en la pestaña **Configuración de volumen**.
- **Entorno**: Los argumentos se pasan a través del campo **Comando de ejecución** en **Configuración avanzada**.

### DSM 7.2 & 7.3 (Container Manager)
- **Proyecto**: Puede usar un archivo `docker-compose.yml` para una gestión más sencilla.
- **Capacidad**: Asegúrese de que el contenedor no tenga capacidades restringidas específicas bloqueadas si usa puertos personalizados por debajo de 1024 (no aplicable para el puerto 65432 por defecto).
- **Web Station**: Si desea usar un dominio personalizado con Reverse Proxy, configúrelo en **Web Station** para que apunte al puerto del contenedor.

---
*Para detalles de la API, consulte [REFERENCE.md](https://github.com/devfred78/multiplayer/blob/main/REFERENCE.md).*
