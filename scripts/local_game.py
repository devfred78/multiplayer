"""Run a small, visible local multiplayer session.

Usage::

    uv run python scripts/local_game.py       # two players
    uv run python scripts/local_game.py 4     # four players

The extra command-line modes are used internally to give the server and each
player their own console window.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

# Make direct execution (``python scripts/local_game.py``) work from a clone.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from multiplayer.client import GameClient  # noqa: E402
from multiplayer.server import GameServer  # noqa: E402


HOST = "127.0.0.1"
PORT = 65432
TURN_DELAY = 1.2


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, PermissionError):
        return {}


def _write_json(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value), encoding="utf-8")
    temporary.replace(path)


async def run_server(shutdown_file: Path) -> None:
    server = GameServer(host=HOST, port=PORT, name="Local demo server")
    await server.start()
    print(f"Server started on {HOST}:{PORT}", flush=True)
    try:
        while not shutdown_file.exists():
            await asyncio.sleep(0.25)
    finally:
        print("Stopping server cleanly...", flush=True)
        await server.stop()
        print("Server stopped.", flush=True)


def _request(client: GameClient, command: str, **payload: Any) -> dict[str, Any]:
    response = client.send_request(command, **payload)
    if not response.get("success", False):
        raise RuntimeError(response.get("message", f"{command} failed"))
    return response


def run_player(index: int, player_count: int, coordination_file: Path) -> None:
    coordination = coordination_file.with_suffix(".players")
    player_file = coordination / f"player-{index}.json"
    coordination.mkdir(exist_ok=True)
    client = GameClient(host=HOST, port=PORT)
    name = f"Player {index}"
    try:
        # The first player owns the game and publishes its ID for the others.
        for attempt in range(30):
            try:
                client.connect()
                break
            except OSError:
                if attempt == 29:
                    raise
                time.sleep(0.25)

        player = client.create_player(name, is_default=True)
        print(f"{name} connected (id={player.ID[:8]})", flush=True)
        if index == 1:
            game = _request(
                client,
                "GAME_CREATE",
                name="Local game",
                max_players=player_count,
                turn_based=True,
            )
            game_id = game["game_id"]
            _write_json(coordination_file, {"game_id": game_id})
            print(f"Game created: {game_id[:8]}", flush=True)
        else:
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline and not (game_data := _read_json(coordination_file)):
                time.sleep(0.25)
            game_id = game_data.get("game_id")
            if not game_id:
                raise RuntimeError("The game was not published in time.")

        _request(client, "GAME_JOIN", game_id=game_id, role="PLAYER")
        _write_json(player_file, {"id": player.ID, "name": name})
        print(f"{name} joined the game.", flush=True)

        # Wait until every player has joined before starting the game.
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            joined = [p for p in coordination.glob("player-*.json") if _read_json(p)]
            if len(joined) >= player_count:
                break
            time.sleep(0.25)
        else:
            raise RuntimeError("Not all players joined the game.")

        if index == 1:
            time.sleep(1)
            _request(client, "GAME_CONTROL", game_id=game_id, action="START")
            print("The game starts!", flush=True)

        # Every player polls the public state and acts only during its turn.
        actions_done = 0
        while actions_done < player_count * 2:
            state = _request(client, "GAME_STATE_GET", game_id=game_id)["state"]
            if state["status"] == "FINISHED":
                break
            if state["status"] != "IN_PROGRESS" or state["current_player_id"] != player.ID:
                time.sleep(0.35)
                continue
            actions_done += 1
            print(f"{name} is playing: action {actions_done}", flush=True)
            _request(
                client,
                "GAME_ACTION",
                game_id=game_id,
                player_id=player.ID,
                action_type="MESSAGE",
                data={"text": f"Hello from {name}!"},
            )
            time.sleep(TURN_DELAY)
            _request(client, "GAME_NEXT_TURN", game_id=game_id, player_id=player.ID)

        if index == 1:
            time.sleep(1)
            _request(client, "GAME_CONTROL", game_id=game_id, action="STOP")
            print("Game finished normally.", flush=True)
        time.sleep(2)
    except Exception as error:
        print(f"{name}: error: {error}", flush=True)
    finally:
        client.disconnect()


def _launch(command: list[str]) -> subprocess.Popen[bytes]:
    flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
    return subprocess.Popen(command, cwd=ROOT, creationflags=flags)


def run_demo(player_count: int) -> None:
    with tempfile.TemporaryDirectory(prefix="multiplayer-demo-") as temporary:
        coordination_file = Path(temporary) / "game.json"
        coordination_file.with_suffix(".players").mkdir()
        shutdown_file = Path(temporary) / "shutdown"
        script = str(Path(__file__).resolve())
        python = sys.executable
        server = _launch([python, script, "--server", str(shutdown_file)])
        time.sleep(1)
        players = [
            _launch([python, script, "--player", str(i), str(player_count), str(coordination_file)])
            for i in range(1, player_count + 1)
        ]
        try:
            for process in players:
                process.wait()
        finally:
            shutdown_file.touch()
            server.wait(timeout=10)


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch a visible local multiplayer game.")
    parser.add_argument("player_count", nargs="?", type=int, default=2, help="number of players (default: 2)")
    parser.add_argument("--server", metavar="SHUTDOWN_FILE")
    parser.add_argument("--player", nargs=3, metavar=("INDEX", "COUNT", "COORDINATION_FILE"))
    args = parser.parse_args()
    if args.server:
        asyncio.run(run_server(Path(args.server)))
    elif args.player:
        run_player(int(args.player[0]), int(args.player[1]), Path(args.player[2]))
    else:
        if args.player_count < 1:
            parser.error("the number of players must be positive")
        run_demo(args.player_count)


if __name__ == "__main__":
    main()
