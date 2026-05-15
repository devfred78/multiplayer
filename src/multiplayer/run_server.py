import argparse
import sys
import time
import os
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
    parser.add_argument("--tls-cert-dir", help="Directory containing TLS certificate (cert.pem) and key (privkey.pem)")
    parser.add_argument("--tls-self-signed", action="store_true", default=True, help="Generate a self-signed certificate (default: True)")
    parser.add_argument("--no-self-signed", action="store_false", dest="tls_self_signed", help="Do not generate a self-signed certificate")
    parser.add_argument("--unencrypted-port", type=int, help="Port for unencrypted connections (when TLS is enabled)")
    parser.add_argument("--logging-host", help="IPC logging server host")
    parser.add_argument("--logging-port", type=int, help="IPC logging server port")
    parser.add_argument("--logger-name", default="GameServer", help="Name of the logger (default: GameServer)")
    parser.add_argument("--name", help="Human-readable name for the server instance")
    parser.add_argument("--hidden", action="store_true", help="Hide the server from network discovery")
    parser.add_argument("--persistence", choices=["json", "sqlite", "none"], default="none", help="Persistence type (default: none)")
    parser.add_argument("--persistence-path", help="Path to the persistence file (e.g. server_data.json or server_data.db)")

    args = parser.parse_args()

    tls_cert = args.tls_cert
    tls_key = args.tls_key
    tls_self_signed = args.tls_self_signed

    if args.tls_cert_dir:
        print(f"Scanning directory for certificates: {args.tls_cert_dir}")
        if not os.path.isdir(args.tls_cert_dir):
            print(f"Error: {args.tls_cert_dir} is not a directory.")
            sys.exit(1)
        
        # Look for cert.pem/privkey.pem first, then others
        potential_certs = ["cert.pem", "RSA-cert.pem", "ECC-cert.pem"]
        potential_keys = ["privkey.pem", "RSA-privkey.pem", "ECC-privkey.pem"]
        
        found_cert = None
        for c in potential_certs:
            p = os.path.join(args.tls_cert_dir, c)
            if os.path.isfile(p):
                found_cert = p
                break
        
        found_key = None
        for k in potential_keys:
            p = os.path.join(args.tls_cert_dir, k)
            if os.path.isfile(p):
                found_key = p
                break

        if found_cert and found_key:
            print(f"Found certificates in {args.tls_cert_dir}: {os.path.basename(found_cert)}, {os.path.basename(found_key)}")
            tls_cert = found_cert
            tls_key = found_key
            tls_self_signed = False
        else:
            print(f"Warning: Could not find both a certificate and a key in {args.tls_cert_dir}. Falling back to other options.")

    if args.persistence_path:
        persistence_path = os.path.abspath(args.persistence_path)
        if os.path.isdir(persistence_path):
            print(f"Error: Persistence path '{args.persistence_path}' is a directory.")
            sys.exit(1)
        
        parent_dir = os.path.dirname(persistence_path)
        if not os.path.exists(parent_dir):
            print(f"Error: Parent directory '{parent_dir}' does not exist.")
            sys.exit(1)
        
        if not os.access(parent_dir, os.W_OK):
            print(f"Error: Parent directory '{parent_dir}' is not writable.")
            sys.exit(1)
        
        if os.path.exists(persistence_path) and not os.access(persistence_path, os.W_OK):
            print(f"Error: Persistence file '{args.persistence_path}' is not writable.")
            sys.exit(1)

    server = GameServer(
        host=args.host,
        port=args.port,
        password=args.password,
        admin_password=args.admin_password,
        use_tls=args.use_tls,
        tls_domain=args.tls_domain,
        tls_cert=tls_cert,
        tls_key=tls_key,
        tls_self_signed=tls_self_signed,
        logging_host=args.logging_host,
        logging_port=args.logging_port,
        logger_name=args.logger_name,
        name=args.name,
        unencrypted_port=args.unencrypted_port,
        hidden=args.hidden,
        persistence_type=args.persistence if args.persistence != "none" else None,
        persistence_path=args.persistence_path
    )

    try:
        server.start()
        # Keep the main thread alive while the server process is running
        while True:
            time.sleep(1)
            if server._server_process and not server._server_process.is_alive():
                if server._server_process.exitcode != 0:
                    print(f"Server process exited with code {server._server_process.exitcode}")
                    sys.exit(server._server_process.exitcode)
                break
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.stop()
    except EOFError:
        print("\nStopping server...")
        server.stop()
if __name__ == "__main__":
    main()
