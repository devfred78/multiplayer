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
    parser.add_argument("--logging-host", help="IPC logging server host")
    parser.add_argument("--logging-port", type=int, help="IPC logging server port")
    parser.add_argument("--logger-name", default="GameServer", help="Name of the logger (default: GameServer)")
    parser.add_argument("--name", help="Name of the server instance")

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
    except EOFError:
        print("\nStopping server...")
        server.stop()
