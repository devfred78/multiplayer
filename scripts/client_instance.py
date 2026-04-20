import logging
import argparse
import time
import sys
from pathlib import Path
from logging.handlers import SocketHandler
from multiplayer import GameClient, Player, exceptions
from multiplayer.client import RemoteGame

def setup_logging(log_port, player_name):
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Handler to send logs to the IPClogging server
    socket_handler = SocketHandler('localhost', log_port)
    root_logger.addHandler(socket_handler)
    
    # Local console logging
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(f'%(levelname)s:{player_name}:%(message)s'))
    root_logger.addHandler(console_handler)

    # Configure specific loggers to use the same handlers
    for name in ["GameClient", "RemoteGame", f"Client-{player_name}"]:
        l = logging.getLogger(name)
        l.setLevel(logging.INFO)
        l.propagate = True

def run_client(player_name, game_id, host, port, is_creator, min_players, log_host, log_port):
    logger = logging.getLogger(f"Client-{player_name}")
    logger.info(f"Connecting to server at {host}:{port}...")
    
    client = GameClient(host=host, port=port)
    # If log_host and log_port are provided, configure the client to use them
    # This will also set the internal logger name to Client-NAME
    if log_host and log_port:
        client.configure_logging(log_host, log_port, f"Client-{player_name}")
        # Local reference should point to the same logger
        logger = client._logger
    
    if is_creator:
        logger.info(f"Creating game: {game_id}")
        game_proxy = client.create_game(name=game_id, turn_based=True)
        # Ensure the proxy also knows about the custom logger name
        if log_host and log_port:
            game_proxy.configure_logging(log_host, log_port, f"Client-{player_name}")
            logger = game_proxy._logger
        
        actual_game_id = game_proxy.game_id
        logger.info(f"Actual game ID: {actual_game_id}")
    else:
        logger.info(f"Searching for game named: {game_id}")
        # Wait a bit for game to be created
        max_retries = 10
        actual_game_id = None
        for i in range(max_retries):
            games = client.list_games()
            # Search by name in games attributes
            for gid, attrs in games.items():
                if attrs.get('name') == game_id:
                    actual_game_id = gid
                    break
            if actual_game_id:
                break
            logger.info(f"Game '{game_id}' not found yet, retrying ({i+1}/{max_retries})...")
            time.sleep(1)
        
        if not actual_game_id:
            logger.error(f"Game '{game_id}' not found after retries.")
            return

        game_proxy = RemoteGame(actual_game_id, host=host, port=port)
        if log_host and log_port:
            game_proxy.configure_logging(log_host, log_port, f"Client-{player_name}")
            logger = game_proxy._logger

    logger.info(f"Adding player {player_name}...")
    game_proxy.add_player(Player(player_name, score=0))

    if is_creator:
        # Wait for all players
        logger.info(f"Waiting for {min_players} players to join...")
        while len(game_proxy.players) < min_players:
            time.sleep(0.5)
        
        logger.info("Starting the game...")
        game_proxy.start()

    # Play turns
    try:
        while True:
            try:
                state = game_proxy.state
            except exceptions.ConnectionError:
                logger.info("Connection lost (server likely stopped).")
                break

            if state.get('status') == 'finished' or state.get('status') == 'stopped':
                logger.info("Game over or stopped.")
                break
            
            if state.get('status') == 'pending':
                # logger.info("Waiting for the game to start...")
                time.sleep(0.5)
                continue

            try:
                current = game_proxy.current_player
            except exceptions.ConnectionError:
                logger.info("Connection lost while waiting for turn.")
                break
            except Exception as e:
                # If game status changed between check and current_player call
                try:
                    state = game_proxy.state
                    if state.get('status') in ['finished', 'stopped']:
                        logger.info("Game finished while waiting for turn.")
                        break
                except exceptions.ConnectionError:
                    logger.info("Connection lost while checking game status.")
                    break
                raise e

            if current and current.name == player_name:
                logger.info(f"It's my turn ({player_name})!")
                time.sleep(1)
                
                # Update score
                custom = state.get('custom', {})
                scores = custom.get('scores', {})
                scores[player_name] = scores.get(player_name, 0) + 10
                
                try:
                    game_proxy.set_state({'scores': scores})
                except exceptions.ConnectionError:
                    logger.info("Connection lost while updating score.")
                    break
                
                logger.info(f"I now have {scores[player_name]} points")
                logger.info("Ending my turn.")
                try:
                    game_proxy.next_turn()
                except exceptions.ConnectionError:
                    logger.info("Connection lost while ending turn.")
                    break
                except Exception as e:
                    try:
                        state = game_proxy.state
                        if state.get('status') in ['finished', 'stopped']:
                            logger.info("Game finished while ending turn.")
                            break
                    except exceptions.ConnectionError:
                        logger.info("Connection lost while checking game status.")
                        break
                    raise e
            else:
                if current:
                    # logger.info(f"Waiting for {current.name}'s turn...")
                    pass
                time.sleep(0.5)
            
            # Limit turns for simulation if it's the creator
            if is_creator:
                try:
                    custom = game_proxy.state.get('custom', {})
                    scores = custom.get('scores', {})
                    total_score = sum(scores.values())
                    if total_score >= 80: # 4 turns each approximately
                        logger.info("Score limit reached, stopping simulation.")
                        game_proxy.stop()
                        break
                except exceptions.ConnectionError:
                    logger.info("Connection lost while monitoring limit.")
                    break

    except Exception as e:
        logger.exception(f"Error during game: {e}")
    
    logger.info(f"Client {player_name} exiting.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multiplayer Game Client Instance")
    parser.add_argument("--name", required=True, help="Player name")
    parser.add_argument("--game-id", required=True, help="Game ID to create or join")
    parser.add_argument("--host", default="127.0.0.1", help="Server host")
    parser.add_argument("--port", type=int, default=65432, help="Server port")
    parser.add_argument("--log-port", type=int, default=5005, help="IPClogging port")
    parser.add_argument("--creator", action="store_true", help="Flag if this client creates the game")
    parser.add_argument("--players", type=int, default=2, help="Minimum number of players to wait for (creator only)")
    
    args = parser.parse_args()

    # Setup paths
    project_root = Path(__file__).parent.parent.resolve()
    sys.path.append(str(project_root / "src"))

    setup_logging(args.log_port, args.name)
    run_client(args.name, args.game_id, args.host, args.port, args.creator, args.players, "localhost", args.log_port)