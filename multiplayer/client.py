"""
This module provides the client-side implementation for networked multiplayer games.
"""
import socket
import json
import struct
import time
from .game import Player
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
    def __init__(self, host='127.0.0.1', port=65432, password=None):
        self.host = host
        self.port = port
        self.password = password

    @staticmethod
    def discover_servers(timeout=2):
        """
        Discovers game servers on the local network using UDP multicast.

        Args:
            timeout (int): The number of seconds to listen for responses.

        Returns:
            A list of (host, port) tuples for discovered servers.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.settimeout(timeout)

        # Send the discovery message to the multicast group
        sock.sendto(DISCOVERY_MESSAGE, (MULTICAST_GROUP, DISCOVERY_PORT))

        servers = []
        end_time = time.time() + timeout

        while time.time() < end_time:
            try:
                data, _ = sock.recvfrom(1024)
                ip_bytes, port = struct.unpack(RESPONSE_MESSAGE_FORMAT, data)
                host = ip_bytes.decode('utf-8').strip('\x00')
                servers.append((host, port))
            except socket.timeout:
                break

        # Remove duplicates
        return list(set(servers))

    def _send_command(self, action, params=None):
        """Sends a command to the server and returns the response."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.host, self.port))
                command = {
                    'action': action,
                    'params': params or {},
                    'password': self.password,
                }
                s.sendall(json.dumps(command).encode('utf-8'))
                
                response_data = s.recv(1024)
                response = json.loads(response_data.decode('utf-8'))
                
                if response.get('status') == 'error':
                    self._handle_error(response)
                
                return response.get('data')
        except socket.error as e:
            raise exceptions.ConnectionError(f"Failed to connect to server: {e}")

    def _handle_error(self, response):
        """Raises the appropriate client-side exception based on the server's response."""
        error_type = response.get('type', 'ServerError')
        message = response.get('message', 'An unknown error occurred.')
        
        exception_class = getattr(exceptions, error_type, exceptions.ServerError)
        raise exception_class(message)

    def create_game(self, **game_options):
        """Requests the server to create a new game and returns a proxy to it."""
        data = self._send_command('create_game', game_options)
        return RemoteGame(data['game_id'], self.host, self.port, self.password)

    def list_games(self):
        """Retrieves a list of available games from the server."""
        return self._send_command('list_games')

class RemoteGame:
    """
    A proxy for a Game object on a remote server.
    """
    def __init__(self, game_id, host='127.0.0.1', port=65432, password=None):
        self.game_id = game_id
        self.host = host
        self.port = port
        self._client = GameClient(host, port, password)

    def _send_command(self, action, params=None):
        """Sends a command to the server for a specific game and returns the response."""
        full_params = {'game_id': self.game_id}
        if params:
            full_params.update(params)
        return self._client._send_command(action, full_params)

    def add_player(self, player):
        """Adds a player to the remote game."""
        params = {'player': {'name': player.name, 'attributes': player.attributes}}
        self._send_command('add_player', params)

    def start(self):
        """Starts the remote game."""
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
