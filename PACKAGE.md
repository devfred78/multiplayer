**English** | [Español](translation/PACKAGE.es.md) | [Français](translation/PACKAGE.fr.md)

# Multiplayer Container Documentation

This guide describes how to install, configure, and manage the `multiplayer-server` Docker container.

## Installation

### Standard Docker
Pull the image from GitHub Container Registry:
```bash
docker pull ghcr.io/devfred78/multiplayer-server:latest
```

### Synology NAS
1. Open **Docker** (DSM 7.1) or **Container Manager** (DSM 7.2+).
2. Go to **Registry**, search for `ghcr.io/devfred78/multiplayer-server-synology`.
3. Download the `latest` or specific version tag.

## Configuration

### Command Line Arguments
The server accepts the following arguments:
- `--host`: Host address (default: `0.0.0.0`).
- `--port`: Listening port (default: `65432`).
- `--name`: Server instance name.
- `--password`: Global server password.
- `--admin-password`: Administrative password.
- `--use-tls`: Enables TLS v1.3.
- `--tls-cert-dir`: Directory containing certificates (mapped to `/app/certs`).
- `--logging-host` / `--logging-port`: Centralized log server details.

### TLS Certificates
To use your own certificates:
1. Create a directory (e.g., `./certs`) and place `cert.pem` and `privkey.pem` inside.
2. Map this directory to `/app/certs` in the container.
3. Use `--use-tls --tls-cert-dir /app/certs --no-self-signed`.

## Execution and Management

### Run the Container
```bash
docker run -d \
  --name multiplayer-server \
  -p 65432:65432 \
  -v /path/to/certs:/app/certs \
  ghcr.io/devfred78/multiplayer-server:latest \
  --port 65432 --use-tls --tls-cert-dir /app/certs
```

### Stop and Start
- **Stop**: `docker stop multiplayer-server`
- **Start**: `docker start multiplayer-server`
- **Restart**: `docker restart multiplayer-server`

### Interact with the Container
- **Logs**: `docker logs -f multiplayer-server`
- **Shell**: `docker exec -it multiplayer-server /bin/sh`

## Synology Specifics

### DSM 7.1 (Docker)
- **Network**: Use `bridge` mode and map port `65432`.
- **Volume**: Map your local certificate folder to `/app/certs` in the **Volume Settings** tab.
- **Environment**: Arguments are passed via the **Execution Command** field in **Advanced Settings**.

### DSM 7.2 & 7.3 (Container Manager)
- **Project**: You can use a `docker-compose.yml` for easier management.
- **Capability**: Ensure the container has no specific restricted capabilities blocked if using custom ports below 1024 (not applicable for default 65432).
- **Web Station**: If you want to use a custom domain with Reverse Proxy, configure it in **Web Station** to point to the container's port.

---
*For API details, see [REFERENCE.md](https://github.com/devfred78/multiplayer/blob/main/REFERENCE.md).*
