"""
This module provides the server-side implementation for networked multiplayer games.
"""
import socket
import json
import threading
import uuid
from multiprocessing import Process
from .game import Game, Player
from .exceptions import GameLogicError, PlayerLimitReachedError

class GameServer:
    """
    Manages multiple Game instances and handles network requests from clients.
    """
    def __init__(self, host='127.0.0.1', port=65432):
        self.host = host
        self.port = port
        self._server_process = None

    def start(self):
        """Starts the game server in a separate process."""
        if self._server_process and self._server_process.is_alive():
            print("Server is already running.")
            return

        self._server_process = Process(target=self._run_server)
        self._server_process.start()
        print(f"Server started on {self.host}:{self.port} with PID {self._server_process.pid}")

    def stop(self):
        """Stops the game server process."""
        if self._server_process and self._server_process.is_alive():
            self._server_process.terminate()
            self._server_process.join()
            print("Server stopped.")
        else:
            print("Server is not running.")

    def _run_server(self):
        """The main server loop that listens for and handles connections."""
        games = {}
        games_lock = threading.Lock()
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen()
            
            while True:
                conn, addr = s.accept()
                thread = threading.Thread(target=self._handle_client, args=(conn, addr, games, games_lock))
                thread.start()

    def _handle_client(self, conn, addr, games, lock):
        """Handles a single client connection."""
        print(f"Connected by {addr}")
        client_player_name = None
        game_id = None
        
        try:
            with conn:
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    
                    try:
                        command = json.loads(data.decode('utf-8'))
                        action = command.get('action')
                        params = command.get('params', {})
                        
                        if action == 'add_player':
                            client_player_name = params.get('player', {}).get('name')
                            game_id = params.get('game_id')
                        
                        with lock:
                            response = self._execute_command(games, action, params)
                        
                        conn.sendall(json.dumps(response).encode('utf-8'))
                    except (json.JSONDecodeError, TypeError) as e:
                        error_response = {'status': 'error', 'type': 'ServerError', 'message': str(e)}
                        conn.sendall(json.dumps(error_response).encode('utf-8'))
        finally:
            if client_player_name and game_id and game_id in games:
                with lock:
                    games[game_id].remove_player(client_player_name)
                print(f"Player '{client_player_name}' from {addr} has disconnected and been removed from game {game_id}.")
            else:
                print(f"Disconnected from {addr}")

    def _execute_command(self, games, action, params):
        """Executes a command on the game objects and returns a response."""
        try:
            if action == 'create_game':
                game_id = str(uuid.uuid4())
                games[game_id] = Game(**params)
                result = {'status': 'success', 'data': {'game_id': game_id}}
            elif action == 'list_games':
                game_list = {gid: g.attributes for gid, g in games.items()}
                result = {'status': 'success', 'data': game_list}
            else:
                game_id = params.get('game_id')
                if not game_id or game_id not in games:
                    return {'status': 'error', 'type': 'GameNotFoundError', 'message': 'Game not found'}
                
                game = games[game_id]
                
                if action == 'add_player':
                    player_data = params['player']
                    player = Player(player_data['name'], **player_data.get('attributes', {}))
                    game.add_player(player)
                    result = {'status': 'success'}
                elif action == 'start':
                    game.start()
                    result = {'status': 'success'}
                elif action == 'pause':
                    game.pause()
                    result = {'status': 'success'}
                elif action == 'resume':
                    game.resume()
                    result = {'status': 'success'}
                elif action == 'stop':
                    game.stop()
                    result = {'status': 'success'}
                elif action == 'next_turn':
                    game.next_turn()
                    result = {'status': 'success'}
                elif action == 'get_current_player':
                    player = game.current_player
                    if player:
                        result = {'status': 'success', 'data': {'name': player.name, 'attributes': player.attributes}}
                    else:
                        result = {'status': 'success', 'data': None}
                elif action == 'get_game_state':
                    result = {'status': 'success', 'data': game.state.value}
                else:
                    result = {'status': 'error', 'type': 'ServerError', 'message': 'Unknown action'}
        except (GameLogicError, PlayerLimitReachedError) as e:
            result = {'status': 'error', 'type': type(e).__name__, 'message': str(e)}
        except Exception as e:
            result = {'status': 'error', 'type': 'ServerError', 'message': str(e)}
            
        return result
