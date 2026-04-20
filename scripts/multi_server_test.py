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
GAME_PORT_1 = 65432
GAME_PORT_2 = 65433

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

def launch_log_server(color_mode="origin"):
    """Launches the log server in a new terminal window."""
    server_path = Path("src/multiplayer/IPClogging/server.py").resolve()
    
    print(f"Launching central log server on port {LOG_PORT} (mode: {color_mode})...")
    subprocess.Popen(['wt', 'new-tab', '-p', 'Command Prompt', '-d', '.', 'cmd', '/k', 'uv', 'run', 'python', str(server_path), '--port', str(LOG_PORT), '--color-mode', color_mode], shell=True)
    
    # Give the server some time to start
    time.sleep(3)

def launch_client_instance(name, game_id, port, is_creator=False, num_players=2):
    """Launches a client instance in a new terminal window."""
    client_script = Path("scripts/client_instance.py").resolve()
    
    print(f"Launching client {name} connecting to port {port}...")
    cmd = ['wt', 'new-tab', '-p', 'Command Prompt', '-d', '.', 'cmd', '/k', 'uv', 'run', 'python', str(client_script), '--name', name, '--game-id', game_id, '--port', str(port), '--log-port', str(LOG_PORT)]
    if is_creator:
        cmd.append('--creator')
        cmd.extend(['--players', str(num_players)])
    
    subprocess.Popen(cmd, shell=True)

def run_multi_server_simulation():
    """Coordinates simulation with 2 servers and 1 log server."""
    logger = logging.getLogger("MultiServerSim")
    
    logger.info("Starting GameServer 1 on port %d...", GAME_PORT_1)
    server1 = GameServer(
        host='127.0.0.1', 
        port=GAME_PORT_1,
        logging_host='localhost',
        logging_port=LOG_PORT,
        logger_name="GameServer-1"
    )
    server1.start()
    
    logger.info("Starting GameServer 2 on port %d...", GAME_PORT_2)
    server2 = GameServer(
        host='127.0.0.1', 
        port=GAME_PORT_2,
        logging_host='localhost',
        logging_port=LOG_PORT,
        logger_name="GameServer-2"
    )
    server2.start()
    
    time.sleep(1) # Wait for servers to start
    
    game_id_1 = "Game-On-Server-1"
    game_id_2 = "Game-On-Server-2"
    
    try:
        # Launch clients for Server 1
        logger.info("Launching clients for Server 1...")
        launch_client_instance("Alice-S1", game_id_1, GAME_PORT_1, is_creator=True, num_players=2)
        time.sleep(1)
        launch_client_instance("Bob-S1", game_id_1, GAME_PORT_1, is_creator=False)
        
        # Launch clients for Server 2
        logger.info("Launching clients for Server 2...")
        launch_client_instance("Charlie-S2", game_id_2, GAME_PORT_2, is_creator=True, num_players=2)
        time.sleep(1)
        launch_client_instance("Dave-S2", game_id_2, GAME_PORT_2, is_creator=False)
        
        logger.info("All clients launched. Monitor the log server window.")
        logger.info("The simulation will run until score limits are reached in both games.")
        
        # Simple monitoring for both servers
        monitor1 = GameClient(host='127.0.0.1', port=GAME_PORT_1)
        monitor2 = GameClient(host='127.0.0.1', port=GAME_PORT_2)
        
        done1 = False
        done2 = False
        
        while not (done1 and done2):
            if not done1:
                games = monitor1.list_games()
                if not any(g.get('name') == game_id_1 for g in games.values()):
                    # Wait a bit more if it hasn't appeared yet
                    pass
                else:
                    # Actually we should use RemoteGame to check status but let's just wait
                    pass
            
            # For simplicity in this script, we'll just wait for a while or check periodically
            # Since client_instance.py stops the game when score is reached, 
            # we can check if games are gone from the list (if they were finished/stopped)
            
            active_games_1 = monitor1.list_games()
            active_games_2 = monitor2.list_games()
            
            if not any(g.get('name') == game_id_1 for g in active_games_1.values()):
                if not done1:
                    logger.info("Game 1 finished.")
                    done1 = True
            
            if not any(g.get('name') == game_id_2 for g in active_games_2.values()):
                if not done2:
                    logger.info("Game 2 finished.")
                    done2 = True
                    
            time.sleep(5)
            logger.info("Status: Server1 done=%s, Server2 done=%s", done1, done2)

    except Exception as e:
        logger.exception(f"Error during simulation: {e}")
    finally:
        logger.info("Stopping GameServers...")
        server1.stop()
        server2.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-server multiplayer test environment")
    parser.add_argument(
        "--color-mode",
        choices=["level", "origin"],
        default="origin",
        help="Coloration mode for the log server"
    )
    args = parser.parse_args()

    # Ensure we are at project root
    project_root = Path(__file__).parent.parent.resolve()
    os.chdir(project_root)
    sys.path.append(str(project_root / "src"))

    launch_log_server(color_mode=args.color_mode)
    setup_logging()
    
    try:
        run_multi_server_simulation()
    except KeyboardInterrupt:
        print("\nSimulation interrupted.")
    except Exception as e:
        logging.exception(f"Error during simulation: {e}")
    
    print("\nSimulation finished. You can close the log window.")
    input("Press Enter to exit...")
