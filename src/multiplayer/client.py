"""
This module provides the client-side implementation for networked multiplayer games.
"""
import socket
import json
import struct
import time
import ssl
import logging
from logging.handlers import SocketHandler
from .game import Player, Observer
from . import exceptions

# Constants for network discovery
MULTICAST_GROUP = '224.1.1.1'
DISCOVERY_PORT = 5007
DISCOVERY_MESSAGE = b'multiplayer_game_discovery_request'
RESPONSE_MESSAGE_FORMAT = b'!15sH' # 15-char IP, unsigned short port

class GameClient:
    """
    A client for connecting to a GameServer.
    """
    def __init__(self, host='127.0.0.1', port=65432, password=None, use_tls=False):
        self.host = host
        self.port = port
        self.password = password
        self.use_tls = use_tls
        self._logger = logging.getLogger("GameClient")
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = True # Ensure it bubbles up to root by default
        # Check if root logger has a SocketHandler (configured by setup_logging in scripts)
        # but better yet, let's look for any SocketHandler in the hierarchy
        self._check_external_logging()

    def _check_external_logging(self):
        """Checks if a SocketHandler is already configured in the logging hierarchy."""
        curr = self._logger
        while curr:
            for h in curr.handlers:
                if isinstance(h, SocketHandler):
                    return True
            if not curr.propagate:
                break
            curr = curr.parent
        return False

    def configure_logging(self, host, port, name=None):
        """
        Configures the client to send logs to a logging server.
        
        Args:
            host (str): The host of the logging server.
            port (int): The port of the logging server.
            name (str, optional): A custom name for the logger.
        """
        if name:
            self._logger = logging.getLogger(name)
            self._logger.setLevel(logging.INFO)
            # Ensure propagation is True so it reaches root logger if configured there
            self._logger.propagate = True
            
        # Check if already connected to this host/port via hierarchy
        if self._check_external_logging():
            self._logger.info(f"Using existing IPC logging configuration for {self._logger.name}")
            return

        # Remove existing SocketHandlers ONLY on this specific logger to avoid duplicates
        # but keep others if they were there (though unlikely on this specific logger)
        for h in self._logger.handlers[:]:
            if isinstance(h, SocketHandler):
                self._logger.removeHandler(h)
                
        handler = SocketHandler(host, port)
        self._logger.addHandler(handler)
        self._logger.info(f"Logging configured for {self._logger.name} to {host}:{port}")

    @staticmethod
    def discover_servers(timeout=2):
        """
        Discovers game servers on the local network using UDP multicast.

        Args:
            timeout (int): The number of seconds to listen for responses.

        Returns:
            A list of (host, port) tuples for discovered servers.
        """
        servers = []
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.settimeout(timeout)
            
            try:
                sock.sendto(DISCOVERY_MESSAGE, (MULTICAST_GROUP, DISCOVERY_PORT))
            except OSError:
                # On some systems (like MacOS in CI), multicast might not be available
                return []
            
            end_time = time.time() + timeout
            while time.time() < end_time:
                try:
                    data, _ = sock.recvfrom(1024)
                    ip_bytes, port = struct.unpack(RESPONSE_MESSAGE_FORMAT, data)
                    host = ip_bytes.decode('utf-8').strip('\x00')
                    servers.append((host, port))
                except socket.timeout:
                    break
                except Exception:
                    continue
        
        return list(set(servers))

    def _send_command(self, action, params=None, timeout=5):
        """Sends a command to the server and returns the response."""
        self._logger.debug(f"Sending command {action} with params {params}")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            
            conn = None
            if self.use_tls:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE # Accept self-signed cert
                conn = context.wrap_socket(sock, server_hostname=self.host)
            else:
                conn = sock

            with conn:
                conn.connect((self.host, self.port))
                command = {
                    'action': action,
                    'params': params or {},
                    'password': self.password,
                }
                conn.sendall(json.dumps(command).encode('utf-8'))
                
                response_data = conn.recv(1024)
                if not response_data:
                    raise exceptions.ConnectionError("Server closed the connection without a response (possible TLS mismatch).")
                
                response = json.loads(response_data.decode('utf-8'))
                
                if response.get('status') == 'error':
                    self._handle_error(response)
                
                # If there's data, return it; otherwise return the response itself
                # to allow checking 'status' or other fields for commands without 'data'.
                if 'data' in response:
                    return response.get('data')
                return response
        except (socket.error, ssl.SSLError) as e:
            raise exceptions.ConnectionError(f"Failed to connect to server: {e}")
        except json.JSONDecodeError:
            raise exceptions.ConnectionError("Failed to decode server response (possible TLS mismatch).")

    def _handle_error(self, response):
        """Raises the appropriate client-side exception based on the server's response."""
        error_type = response.get('type', 'ServerError')
        message = response.get('message', 'An unknown error occurred.')
        
        exception_class = getattr(exceptions, error_type, exceptions.ServerError)
        raise exception_class(message)

    def create_game(self, **game_options):
        """Requests the server to create a new game and returns a proxy to it."""
        data = self._send_command('create_game', game_options)
        remote_game = RemoteGame(data['game_id'], self.host, self.port, self.password, self.use_tls)
        
        # Propagate logging configuration if any
        for h in self._logger.handlers:
            if isinstance(h, SocketHandler):
                remote_game.configure_logging(h.host, h.port)
                break
                
        return remote_game

    def list_games(self):
        """Retrieves a list of available games from the server."""
        return self._send_command('list_games')

class GameAdmin:
    """
    A client class for administrators to connect to and manage a GameServer.
    """
    def __init__(self, host='127.0.0.1', port=65432, admin_password=None, use_tls=False):
        self.host = host
        self.port = port
        self.admin_password = admin_password
        self.use_tls = use_tls
        self._client = GameClient(host, port, admin_password, use_tls)
        self._logger = logging.getLogger("GameAdmin")
        self._logger.setLevel(logging.INFO)

    def configure_logging(self, host, port):
        """Configures the admin client to send logs to a logging server."""
        self._client.configure_logging(host, port, "GameAdmin")
        self._logger = self._client._logger

    def stop_server(self):
        """Requests the server to shut down."""
        return self._client._send_command('stop_server')

    def restart_server(self):
        """Requests the server to restart (clears all current games)."""
        return self._client._send_command('restart_server')

    def get_server_info(self):
        """Retrieves information about the server's status and active games."""
        return self._client._send_command('get_server_info')

    def list_games(self):
        """Retrieves a list of available games from the server."""
        return self._client.list_games()

    def kick_player(self, game_id, player_name):
        """Kicks a player from a specific game."""
        return self._client._send_command('kick_player', {'game_id': game_id, 'player_name': player_name})

    def kick_observer(self, game_id, observer_name):
        """Kicks an observer from a specific game."""
        return self._client._send_command('kick_observer', {'game_id': game_id, 'observer_name': observer_name})

    def list_all_players(self):
        """Lists all players currently connected to the server across all games."""
        return self._client._send_command('list_all_players')

    def set_logging_config(self, host, port):
        """Sets the logging server address and port."""
        return self._client._send_command('set_logging_config', {'host': host, 'port': port})

    def set_logging_enabled(self, enabled):
        """Enables or disables logging on the server."""
        return self._client._send_command('set_logging_enabled', {'enabled': enabled})

class RemoteGame:
    """
    A proxy for a Game object on a remote server.
    """
    def __init__(self, game_id, host='127.0.0.1', port=65432, password=None, use_tls=False):
        self.game_id = game_id
        self.host = host
        self.port = port
        self._client = GameClient(host, port, password, use_tls)
        self._logger = logging.getLogger("RemoteGame")
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = True
        # RemoteGame should ideally use the same logger name if possible
        # but for now we just ensure it propagates to the same destination.

    def configure_logging(self, host, port, name=None):
        """Configures the remote game proxy to send logs to a logging server."""
        if name is None:
            name = f"RemoteGame.{self.game_id[:8]}"
        self._client.configure_logging(host, port, name)
        self._logger = self._client._logger

    def _send_command(self, action, params=None):
        """Sends a command to the server for a specific game and returns the response."""
        full_params = {'game_id': self.game_id}
        if params:
            full_params.update(params)
        return self._client._send_command(action, full_params)

    def add_player(self, player, password=None):
        """
        Adds a player to the remote game.

        Args:
            player (Player): The player to add.
            password (str, optional): The password for this specific game.
        """
        self._logger.info(f"Adding player {player.name} to game {self.game_id}")
        params = {
            'player': {'name': player.name, 'attributes': player.attributes},
            'game_password': password,
        }
        self._send_command('add_player', params)

    def add_observer(self, observer, password=None):
        """
        Adds an observer to the remote game.

        Args:
            observer (Observer): The observer to add.
            password (str, optional): The password for this specific game.
        """
        params = {
            'observer': {'name': observer.name, 'attributes': observer.attributes},
            'game_password': password,
        }
        self._send_command('add_observer', params)

    def start(self):
        """Starts the remote game."""
        self._logger.info(f"Starting game {self.game_id}")
        self._send_command('start')

    def pause(self):
        """Pauses the remote game."""
        self._send_command('pause')

    def resume(self):
        """Resumes the remote game."""
        self._send_command('resume')

    def stop(self):
        """Stops the remote game."""
        self._send_command('stop')

    def next_turn(self):
        """Advances to the next turn in the remote game."""
        self._logger.debug(f"Advancing turn in game {self.game_id}")
        self._send_command('next_turn')

    @property
    def current_player(self):
        """Gets the current player from the remote game."""
        data = self._send_command('get_current_player')
        if data:
            return Player(data['name'], **data['attributes'])
        return None

    @property
    def state(self):
        """Gets the state of the remote game."""
        return self._send_command('get_game_state')

    @property
    def players(self):
        """Gets the list of players in the remote game."""
        data = self._send_command('get_players')
        return [Player(p['name'], **p['attributes']) for p in data]

    @property
    def observers(self):
        """Gets the list of observers in the remote game."""
        data = self._send_command('get_observers')
        return [Observer(o['name'], **o['attributes']) for o in data]

    def set_state(self, state):
        """Sets the state of the remote game."""
        return self._send_command('set_game_state', {'state': state})
