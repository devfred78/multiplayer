"""Launch a multiplayer game server from the command line.

Example:
    uv run python scripts/run_server.py --host 127.0.0.1 --port 65432
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Make direct execution (``python scripts/run_server.py``) work from a clone.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from multiplayer import SaveFormat  # noqa: E402
from multiplayer.server import (  # noqa: E402
    DEFAULT_GC_PERIODICITY,
    DEFAULT_HOST,
    DEFAULT_MULTICAST_GROUP,
    DEFAULT_MULTICAST_PORT,
    DEFAULT_PORT,
    DEFAULT_TLS_DOMAIN,
    GameServer,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser for a :class:`GameServer`.

    Returns:
        argparse.ArgumentParser: The configured argument parser.
    """
    parser = argparse.ArgumentParser(description="Launch a multiplayer game server.")
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"listening host (default: {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"main TCP port (default: {DEFAULT_PORT})")
    parser.add_argument("--unencrypted-port", type=int, help="optional unencrypted TCP port")
    parser.add_argument("--password", help="optional server password")
    parser.add_argument("--name", default="", help="human-readable server name")
    parser.add_argument("--use-tls", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--tls-self-signed", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument(
        "--tls-domain", default=DEFAULT_TLS_DOMAIN, help=f"TLS domain (default: {DEFAULT_TLS_DOMAIN})"
    )
    parser.add_argument("--tls-cert-path", type=Path, help="path to the TLS certificate")
    parser.add_argument("--tls-key-path", type=Path, help="path to the TLS private key")
    parser.add_argument("--discoverable", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument(
        "--multicast-group",
        default=DEFAULT_MULTICAST_GROUP,
        help=f"discovery multicast group (default: {DEFAULT_MULTICAST_GROUP})",
    )
    parser.add_argument(
        "--multicast-port",
        type=int,
        default=DEFAULT_MULTICAST_PORT,
        help=f"discovery multicast port (default: {DEFAULT_MULTICAST_PORT})",
    )
    parser.add_argument(
        "--persistence-mode",
        choices=[save_format.value for save_format in SaveFormat],
        help="persistence format: json or sqlite",
    )
    parser.add_argument("--persistence-path", type=Path, help="path to the persistence file")
    parser.add_argument(
        "--garbage-collection-periodicity",
        type=int,
        default=DEFAULT_GC_PERIODICITY,
        help=f"orphan player cleanup period in seconds (default: {DEFAULT_GC_PERIODICITY})",
    )
    return parser


def create_server(args: argparse.Namespace) -> GameServer:
    """Create a server from parsed command-line arguments.

    Args:
        args: Parsed command-line arguments.

    Returns:
        GameServer: The configured server instance.
    """
    persistence_mode = (
        SaveFormat(args.persistence_mode) if args.persistence_mode is not None else None
    )
    return GameServer(
        host=args.host,
        port=args.port,
        unencrypted_port=args.unencrypted_port,
        password=args.password,
        name=args.name,
        use_tls=args.use_tls,
        tls_self_signed=args.tls_self_signed,
        tls_domain=args.tls_domain,
        tls_cert_path=args.tls_cert_path,
        tls_key_path=args.tls_key_path,
        discoverable=args.discoverable,
        multicast_group=args.multicast_group,
        multicast_port=args.multicast_port,
        persistence_mode=persistence_mode,
        persistence_path=args.persistence_path,
        garbage_collection_periodicity=args.garbage_collection_periodicity,
    )


async def run_server(server: GameServer) -> None:
    """Run a server until an interruption is received.

    Args:
        server: The server to start and stop.
    """
    await server.start()
    server_name = f" '{server.name}'" if server.name else ""
    print(
        f"Server{server_name} started on {server.host}:{server._actual_port}",
        flush=True,
    )
    status_task = asyncio.create_task(_display_client_count(server))
    try:
        await asyncio.Event().wait()
    finally:
        status_task.cancel()
        try:
            await status_task
        except asyncio.CancelledError:
            pass
        print("Stopping server cleanly...", flush=True)
        await server.stop()
        print("Server stopped.", flush=True)


async def _display_client_count(server: GameServer) -> None:
    """Display the current number of connected client sessions.

    Args:
        server: The running server whose sessions are monitored.
    """
    try:
        while True:
            print(f"\rConnected clients: {len(server._sessions)}", end="", flush=True)
            await asyncio.sleep(0.25)
    finally:
        print("\r" + " " * 80 + "\r", end="", flush=True)


def main() -> None:
    """Parse arguments and run the server until ``CTRL+C`` is pressed."""
    args = build_parser().parse_args()
    server = create_server(args)
    try:
        asyncio.run(run_server(server))
    except KeyboardInterrupt:
        # ``run_server`` stops the server from its ``finally`` block first.
        pass


if __name__ == "__main__":
    main()
