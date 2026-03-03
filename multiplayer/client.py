"""
This module provides the client-side implementation for networked multiplayer games.
"""
import socket
import json
from .game import Player

class RemoteGame:
    """
    A proxy for a Game object on a remote server.
    """
    def __init__(self, host='127.0.0.1', port=65432):
        self.host = host
        self.port = port

    def _send_command(self, action, params=None):
        """Sends a command to the server and returns the response."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.host, self.port))
            command = {'action': action, 'params': params or {}}
            s.sendall(json.dumps(command).encode('utf-8'))
            
            response_data = s.recv(1024)
            response = json.loads(response_data.decode('utf-8'))
            
            if response.get('status') == 'error':
                raise RuntimeError(f"Server error: {response.get('message')}")
            
            return response.get('data')

    def add_player(self, player):
        """Adds a player to the remote game."""
        params = {'name': player.name, 'attributes': player.attributes}
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
        return Player(data['name'], **data['attributes'])

    @property
    def state(self):
        """Gets the state of the remote game."""
        return self._send_command('get_game_state')
