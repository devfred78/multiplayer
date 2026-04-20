import logging
from logging.handlers import SocketHandler
import subprocess
import time
import sys
import os
import argparse
from pathlib import Path
from multiplayer import GameServer, GameClient

# Port configuration
LOG_PORT = 5005
GAME_PORT = 65432

def setup_logging():
    """Configures the root logger to send logs to the IPClogging server."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Handler to send logs to the IPClogging server
    socket_handler = SocketHandler('localhost', LOG_PORT)
    root_logger.addHandler(socket_handler)
    
    # Also log to local console for debugging if needed
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(levelname)s:%(name)s:%(message)s'))
    root_logger.addHandler(console_handler)

def launch_log_server(color_mode="level"):
    """Launches the log server in a new terminal window."""
    # Path to IPClogging's server.py
    # We assume the script is launched from the project root
    server_path = Path("src/multiplayer/IPClogging/server.py").resolve()
    
    print(f"Launching log server on port {LOG_PORT} (mode: {color_mode})...")
    # Using Windows Terminal (wt) to open a new window
    # Using 'uv run' to ensure dependencies (colorlog) are present
    subprocess.Popen(['wt', 'new-tab', '-p', 'Command Prompt', '-d', '.', 'cmd', '/k', 'uv', 'run', 'python', str(server_path), '--port', str(LOG_PORT), '--color-mode', color_mode], shell=True)
    
    # Give the server some time to start
    time.sleep(3)

def launch_client_instance(name, game_id, is_creator=False, num_players=2):
    """Launches a client instance in a new terminal window."""
    client_script = Path("scripts/client_instance.py").resolve()
    
    print(f"Launching client instance for {name}...")
    cmd = ['wt', 'new-tab', '-p', 'Command Prompt', '-d', '.', 'cmd', '/k', 'uv', 'run', 'python', str(client_script), '--name', name, '--game-id', game_id]
    if is_creator:
        cmd.append('--creator')
        cmd.extend(['--players', str(num_players)])
    
    subprocess.Popen(cmd, shell=True)

def run_simulation(num_players=2):
    """Coordinates the simulation between separate client instances."""
    logger = logging.getLogger("Simulation")
    
    logger.info("Starting GameServer...")
    server = GameServer(host='127.0.0.1', port=GAME_PORT)
    server.start()
    time.sleep(1) # Wait for server to start
    
    game_id = "Full-Test-Game"
    
    try:
        # Player names for the simulation
        player_names = ["Alice", "Bob", "Charlie", "Dave", "Eve", "Frank", "Grace", "Heidi"]
        if num_players > len(player_names):
            # Generate more names if needed
            for i in range(len(player_names), num_players):
                player_names.append(f"Player-{i+1}")
        
        # Launch Client 1 (Creator)
        launch_client_instance(player_names[0], game_id, is_creator=True, num_players=num_players)
        time.sleep(2) # Give it time to create the game
        
        # Launch other clients (Joiners)
        for i in range(1, num_players):
            launch_client_instance(player_names[i], game_id, is_creator=False)
            time.sleep(0.5)
        
        logger.info(f"{num_players} clients launched. The simulation is running in separate windows.")
        logger.info("Waiting for clients to finish (based on score limit in client_instance.py)...")
        
        # Monitor the game status from here
        client_monitor = GameClient(host='127.0.0.1', port=GAME_PORT)
        
        # Wait for game to appear
        max_wait = 15
        actual_game_id = None
        for _ in range(max_wait):
            games = client_monitor.list_games()
            for gid, attrs in games.items():
                if attrs.get('name') == game_id:
                    actual_game_id = gid
                    break
            if actual_game_id:
                break
            time.sleep(1)
        
        if actual_game_id:
            from multiplayer.client import RemoteGame
            game_proxy = RemoteGame(actual_game_id, host='127.0.0.1', port=GAME_PORT)
            
            while True:
                state = game_proxy.state
                status = state.get('status')
                if status in ['finished', 'stopped']:
                    logger.info(f"Game simulation ended with status: {status}")
                    break
                
                custom = state.get('custom', {})
                scores = custom.get('scores', {})
                logger.info(f"Current scores: {scores}")
                time.sleep(2)
        else:
            logger.error("Game never appeared in server list!")

    except Exception as e:
        logger.exception(f"Error during simulation: {e}")
    finally:
        logger.info("Stopping GameServer...")
        server.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Full multiplayer test environment")
    parser.add_argument("--players", type=int, default=2, help="Number of players for the simulation")
    parser.add_argument(
        "--color-mode",
        choices=["level", "origin"],
        default="level",
        help="Coloration mode for the log server: 'level' (by criticality) or 'origin' (by message source)"
    )
    args = parser.parse_args()

    # Ensure we are at project root
    project_root = Path(__file__).parent.parent.resolve()
    os.chdir(project_root)
    sys.path.append(str(project_root / "src"))

    launch_log_server(color_mode=args.color_mode)
    setup_logging()
    
    try:
        run_simulation(num_players=args.players)
    except Exception as e:
        logging.exception(f"Error during simulation: {e}")
    
    print("\nSimulation finished. You can close the log window.")
    input("Press Enter to exit...")
