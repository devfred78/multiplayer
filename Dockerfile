FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY scripts/run_server.py ./scripts/run_server.py

RUN pip install --no-cache-dir .

# Mount /app/data to keep server data and /app/certs to provide TLS material.
VOLUME ["/app/data", "/app/certs"]

EXPOSE 65432/tcp
EXPOSE 65433/tcp
EXPOSE 65434/udp

ENTRYPOINT ["python", "scripts/run_server.py"]
CMD ["--host", "0.0.0.0", "--port", "65432", "--unencrypted-port", "65433", "--persistence-mode", "sqlite", "--persistence-path", "/app/data/server_data.db"]
