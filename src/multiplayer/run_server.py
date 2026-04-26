import argparse
import sys
import time
from multiplayer.server import GameServer

def main():
    parser = argparse.ArgumentParser(description="Run a multiplayer game server.")
    parser.add_argument("--host", default="0.0.0.0", help="Host to listen on (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=65432, help="Port to listen on (default: 65432)")
    parser.add_argument("--password", help="Server password")
    parser.add_argument("--admin-password", help="Admin password")
    parser.add_argument("--use-tls", action="store_true", help="Enable TLS")
    parser.add_argument("--tls-domain", default="localhost", help="Domain name for TLS certificate (default: localhost)")
    parser.add_argument("--tls-cert", help="Path to TLS certificate (.pem)")
    parser.add_argument("--tls-key", help="Path to TLS private key (.pem)")
    parser.add_argument("--tls-self-signed", action="store_true", default=True, help="Generate a self-signed certificate (default: True)")
    parser.add_argument("--no-self-signed", action="store_false", dest="tls_self_signed", help="Do not generate a self-signed certificate")
    parser.add_argument("--logging-host", help="IPC logging server host")
    parser.add_argument("--logging-port", type=int, help="IPC logging server port")
    parser.add_argument("--logger-name", default="GameServer", help="Name of the logger (default: GameServer)")
    parser.add_argument("--name", help="Name of the server instance")

    args = parser.parse_args()

    server = GameServer(
        host=args.host,
        port=args.port,
        password=args.password,
        admin_password=args.admin_password,
        use_tls=args.use_tls,
        tls_domain=args.tls_domain,
        tls_cert=args.tls_cert,
        tls_key=args.tls_key,
        tls_self_signed=args.tls_self_signed,
        logging_host=args.logging_host,
        logging_port=args.logging_port,
        logger_name=args.logger_name,
        name=args.name
    )

    try:
        server.start()
        # Keep the main thread alive while the server process is running
        while True:
            time.sleep(1)
            if server._server_process and not server._server_process.is_alive():
                break
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.stop()
    except