# Installing the multiplayer server with Docker on Synology DSM 7.1

This guide explains how to run the `multiplayer` server in Synology DSM 7.1's
**Docker** application. The images are built and published by the GitHub
Actions `docker.yml` workflow to GitHub Container Registry (GHCR).

## 1. Prerequisites

- A Synology NAS running DSM 7.1 with the **Docker** package installed from
  the Package Center.
- DSM administrator access and, for the commands below, SSH access enabled in
  **Control Panel > Terminal & SNMP**.
- The Docker image published by the GitHub Actions workflow. If the GHCR
  package is private, a GitHub access token with the `read:packages`
  permission is also required before downloading the image.

The server uses TCP port `65432` by default. It stores its data in a persistent
SQLite database at `/app/data/server_data.db` inside the container.

## 2. Identify the NAS architecture

Connect to the NAS through SSH and run:

```bash
uname -m
```

Choose the image that matches the result:

| Common result | Docker architecture | Image tag to use |
|---|---|---|
| `x86_64` | 64-bit Intel/AMD (`linux/amd64`) | `latest-amd64` |
| `aarch64` or `arm64` | 64-bit ARM (`linux/arm64`) | `latest-arm64` |

The workflow can be run manually with a different tag prefix. For example, the
`v2.0.0` prefix produces the `v2.0.0-amd64` and `v2.0.0-arm64` tags.

## 3. Prepare NAS directories

Create a persistent directory for server data:

```bash
sudo mkdir -p /volume1/docker/multiplayer/data
```

If TLS is required, also create a directory for the certificate and private
key:

```bash
sudo mkdir -p /volume1/docker/multiplayer/certs
```

Copy the certificate and key into that directory. The certificate may be a
full chain. If it contains only the domain certificate, the matching chain file
must be present in the same directory, as required by `GameServer`.

Never put the private key in the `data` directory. Restrict access to the
`certs` directory to NAS administrators.

## 4. Download the image

DSM 7.1's Docker interface generally cannot list GHCR images directly, so
download the image through SSH. Replace `latest-amd64` with `latest-arm64` on
an ARM NAS:

```bash
sudo docker pull ghcr.io/devfred78/multiplayer-server:latest-amd64
```

If the GHCR package is private, authenticate first:

```bash
echo "YOUR_GITHUB_TOKEN" | sudo docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
```

## 5. Create the container in the DSM interface

1. Open the **Docker** application, then the **Image** tab.
2. Select the downloaded image, for example
   `ghcr.io/devfred78/multiplayer-server:latest-amd64`, then click **Launch**.
3. Name the container `multiplayer-server`.
4. In **Advanced Settings > Port Settings**, add the TCP mapping:

   | NAS local port | Container port | Protocol |
   |---:|---:|---|
   | `65432` | `65432` | TCP |

5. In **Advanced Settings > Volume**, add the read-write data mapping:

   | NAS local directory | Container mount path | Access |
   |---|---|---|
   | `/volume1/docker/multiplayer/data` | `/app/data` | Read/write |

6. Enable an automatic restart policy if available, then finish the wizard and
   start the container.

The image's default command starts the server on `0.0.0.0:65432` and enables
SQLite persistence. No environment variable is required for this basic
configuration.

### Optional network discovery

Multicast discovery is disabled by default. If it is enabled through a custom
command, also map UDP port `65434` to `65434` in the port settings. Multicast
may not work in a `bridge` network; start with a direct connection to the NAS
IP address instead.

## 6. Enable TLS with a mounted certificate

Add the following second volume mapping in **Advanced Settings > Volume**:

| NAS local directory | Container mount path | Access |
|---|---|---|
| `/volume1/docker/multiplayer/certs` | `/app/certs` | Read-only |

In DSM's custom command field, provide all the arguments below. A custom
command replaces the image's default arguments, which is why the persistence
options are included:

```text
--host 0.0.0.0 --port 65432 --persistence-mode sqlite --persistence-path /app/data/server_data.db --use-tls --tls-cert-path /app/certs/cert.pem --tls-key-path /app/certs/key.pem
```

Replace `cert.pem` and `key.pem` with the actual filenames. TCP port `65432`
then carries the TLS connection, so the port mapping from the previous section
is unchanged. An additional unencrypted port can be configured using
`--unencrypted-port PORT_NUMBER` and a second TCP port mapping.

## 7. Command-line equivalent

The standard configuration without TLS can also be created directly through
SSH:

```bash
sudo docker run -d \
  --name multiplayer-server \
  --restart unless-stopped \
  -p 65432:65432/tcp \
  -v /volume1/docker/multiplayer/data:/app/data \
  ghcr.io/devfred78/multiplayer-server:latest-amd64
```

Example with TLS:

```bash
sudo docker run -d \
  --name multiplayer-server \
  --restart unless-stopped \
  -p 65432:65432/tcp \
  -v /volume1/docker/multiplayer/data:/app/data \
  -v /volume1/docker/multiplayer/certs:/app/certs:ro \
  ghcr.io/devfred78/multiplayer-server:latest-amd64 \
  --host 0.0.0.0 \
  --port 65432 \
  --persistence-mode sqlite \
  --persistence-path /app/data/server_data.db \
  --use-tls \
  --tls-cert-path /app/certs/cert.pem \
  --tls-key-path /app/certs/key.pem
```

## 8. Verify operation

View the container logs:

```bash
sudo docker logs -f multiplayer-server
```

The log should show the listening address and port, followed by the number of
connected clients. From a client on the local network, connect to the NAS IP
address on port `65432`. Enable TLS on the client only if the server was
started with `--use-tls`.

## 9. Update the image

1. Download the new tag that matches the NAS architecture using `docker pull`.
2. Stop and remove the current container:

   ```bash
   sudo docker stop multiplayer-server
   sudo docker rm multiplayer-server
   ```

3. Recreate it with the same mappings and the new image.

The save file remains intact because it is stored outside the container in
`/volume1/docker/multiplayer/data`.

## 10. Quick troubleshooting

- **The NAS cannot download the image:** Check the architecture tag, Internet
  access, and GHCR authentication if the package is private.
- **The port is already in use:** Choose another NAS local port, for example
  `-p 50000:65432/tcp`, or stop the service currently using `65432`.
- **TLS does not start:** Check the mounted paths, read permissions for the
  certificate and key, and the presence of the certificate chain if needed.
- **Data disappears after recreating the container:** Verify that the mapping
  from `/volume1/docker/multiplayer/data` to `/app/data` exists and is
  read-write.
