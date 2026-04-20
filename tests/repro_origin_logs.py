import logging
import time
import threading
import sys
import os
from multiplayer.IPClogging.server import LoggingServer
from multiplayer.server import GameServer
from multiplayer.client import GameClient, Player

def run_repro():
    LOG_PORT = 5001
    SERVER_PORT = 65435
    
    log_server = LoggingServer(port=LOG_PORT, color_mode='origin')
    log_thread = threading.Thread(target=log_server.start, daemon=True)
    log_thread.start()
    time.sleep(1)

    print("--- Starting Game Server ---")
    # 2. Start Game Server configured with logging
    server = GameServer(port=SERVER_PORT, logging_host='127.0.0.1', logging_port=LOG_PORT)
    server.start()
    time.sleep(1)

    print("--- Starting Game Client Alice ---")
    # 3. Create Client and Game
    client = GameClient(port=SERVER_PORT)
    # Configure logging using the new method
    client.configure_logging('127.0.0.1', LOG_PORT, "ClientAlice")
    
    client._logger.info("Alice is starting")
    
    game = client.create_game(name="ReproGame")
    # remote_game created by create_game should automatically have logging configured
    
    alice = Player("Alice")
    
    print("--- Alice joining game ---")
    game.add_player(alice)
    
    game._logger.info("Alice has joined via RemoteGame")
    
    time.sleep(3) # Wait more for logs to arrive
    
    print("--- Cleaning up ---")
    server.stop()
    log_server.stop()

if __name__ == "__main__":
    # Add src to sys.path to ensure we can import multiplayer
    sys.path.insert(0, os.path.abspath("src"))
    run_repro()
