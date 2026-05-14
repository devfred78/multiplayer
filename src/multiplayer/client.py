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
from .game import Player, Observer, PersistentPlayer, PlayerRole
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
    def __init__(self, host='127.0.0.1', port=65432, password=None, use_tls=False, auth_user=None, auth_password=None):
        self.host = host
        self.port = port
        self.password = password
        self.use_tls = use_tls
        self.auth_user = auth_user
        self.auth_password = auth_password
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
                    'auth_user': self.auth_user,
                    'auth_password': self.auth_password,
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
        
        # Check if error_type is a string and handle it
        if isinstance(error_type, dict):
            # This shouldn't happen based on server code but being safe
            error_name = error_type.get('name', 'ServerError')
        else:
            error_name = error_type

        exception_class = getattr(exceptions, error_name, exceptions.ServerError)
        raise exception_class(message)

    def create_game(self, group_id=None, **game_options):
        """Requests the server to create a new game and returns a proxy to it."""
        params = game_options.copy()
        if group_id:
            params['group_id'] = group_id
        data = self._send_command('create_game', params)
        remote_game = RemoteGame(data['game_id'], self.host, self.port, self.password, self.use_tls, self.auth_user, self.auth_password)
        
        # Propagate logging configuration if any
        for h in self._logger.handlers:
            if isinstance(h, SocketHandler):
                remote_game.configure_logging(h.host, h.port)
                break
                
        return remote_game

    def list_games(self):
        """Retrieves a dictionary of active games as RemoteGame objects, indexed by ID."""
        games_data = self._send_command('list_games')
        
        remote_games = {}
        for gid in games_data:
            remote_games[gid] = RemoteGame(gid, self.host, self.port, self.password, self.use_tls, self.auth_user, self.auth_password)
            
            # Propagate logging configuration if any
            for h in self._logger.handlers:
                if isinstance(h, SocketHandler):
                    remote_games[gid].configure_logging(h.host, h.port)
                    break
                    
        return remote_games

    def create_group(self, name, admin_password=None, **attributes):
        """Requests the server to create a new game group and returns a proxy to it."""
        data = self._send_command('create_group', {'name': name, 'admin_password': admin_password, 'attributes': attributes})
        remote_group = RemoteGroup(data['group_id'], self.host, self.port, self.password, self.use_tls, self.auth_user, self.auth_password)
        
        # Propagate logging configuration if any
        for h in self._logger.handlers:
            if isinstance(h, SocketHandler):
                remote_group.configure_logging(h.host, h.port)
                break
                
        return remote_group

    def list_groups(self):
        """Retrieves a dictionary of game groups as RemoteGroup objects, indexed by ID."""
        groups_data = self._send_command('list_groups')
        
        remote_groups = {}
        for gid in groups_data:
            remote_groups[gid] = RemoteGroup(gid, self.host, self.port, self.password, self.use_tls, self.auth_user, self.auth_password)
            
            # Propagate logging configuration if any
            for h in self._logger.handlers:
                if isinstance(h, SocketHandler):
                    remote_groups[gid].configure_logging(h.host, h.port)
                    break
                    
        return remote_groups

    def create_account(self, name, password, role=PlayerRole.PLAYER, managed_groups=None, **attributes):
        """
        Creates a persistent player account on the server.

        Args:
            name (str): The name of the player.
            password (str): The password for the account.
            role (PlayerRole, optional): The player's role (PlayerRole.PLAYER, PlayerRole.GROUP_ADMIN, or PlayerRole.SERVER_ADMIN). Defaults to PlayerRole.PLAYER.
            managed_groups (list, optional): A list of group IDs managed by this player (if role is PlayerRole.GROUP_ADMIN).
            **attributes: Additional attributes for the player.

        Returns:
            dict: The created player's data.
        """
        params = {
            'name': name,
            'password': password,
            'role': role.value if isinstance(role, PlayerRole) else role,
            'managed_groups': managed_groups or [],
            'attributes': attributes
        }
        data = self._send_command('create_persistent_player', params=params)
        if 'role' in data:
            try:
                data['role'] = PlayerRole(data['role'])
            except ValueError:
                pass
        return data

    def get_server_admin(self):
        """
        Returns a ServerAdmin instance using this client's credentials.
        Only useful if the current user has SERVER_ADMIN role.
        """
        return ServerAdmin(self.host, self.port, self.password, self.use_tls, self.auth_user, self.auth_password)

    def get_group_admin(self, group_id):
        """
        Returns a GroupAdmin instance for the specified group using this client's credentials.
        Only useful if the current user has SERVER_ADMIN role or is GROUP_ADMIN for this group.
        """
        return GroupAdmin(group_id, self.host, self.port, self.password, self.use_tls, self.auth_user, self.auth_password)

class ServerAdmin:
    """
    A client class for administrators to connect to and manage a GameServer.
    """
    def __init__(self, host='127.0.0.1', port=65432, admin_password=None, use_tls=False, auth_user=None, auth_password=None):
        self.host = host
        self.port = port
        self.admin_password = admin_password
        self.use_tls = use_tls
        self.auth_user = auth_user
        self.auth_password = auth_password
        self._client = GameClient(host, port, admin_password, use_tls, auth_user, auth_password)
        self._logger = logging.getLogger("ServerAdmin")
        self._logger.setLevel(logging.INFO)

    def configure_logging(self, host, port):
        """Configures the admin client to send logs to a logging server."""
        self._client.configure_logging(host, port, "ServerAdmin")
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

    def kick_player(self, game_id, player_id):
        """Kicks a player from a specific game."""
        return self._client._send_command('kick_player', {'game_id': game_id, 'player_id': player_id})

    def kick_observer(self, game_id, observer_id):
        """Kicks an observer from a specific game."""
        return self._client._send_command('kick_observer', {'game_id': game_id, 'observer_id': observer_id})

    def list_all_players(self):
        """Lists all players currently connected to the server across all games."""
        return self._client._send_command('list_all_players')

    def set_logging_config(self, host, port):
        """Sets the logging server address and port."""
        return self._client._send_command('set_logging_config', {'host': host, 'port': port})

    def set_logging_enabled(self, enabled):
        """Enables or disables logging on the server."""
        return self._client._send_command('set_logging_enabled', {'enabled': enabled})

    def get_cert_expiration(self):
        """Returns the expiration date of the server's TLS certificate."""
        response = self._client._send_command('get_cert_expiration')
        return response.get('expiration')

    def set_server_password(self, new_password):
        """Sets a new password for the server."""
        return self._client._send_command('set_server_password', {'new_password': new_password})

    def set_admin_password(self, new_password):
        """Sets a new administrator password for the server."""
        result = self._client._send_command('set_admin_password', {'new_password': new_password})
        if result.get('status') == 'success':
            self.admin_password = new_password
            self._client.password = new_password
        return result

    def create_group(self, name, admin_password=None, **attributes):
        """Creates a new game group on the server."""
        return self._client.create_group(name, admin_password, **attributes)

    def remove_group(self, group_id):
        """Removes a game group from the server by its ID."""
        return self._client._send_command('remove_group', {'group_id': group_id})

    def list_groups(self):
        """Retrieves a list of all game groups on the server as RemoteGroup objects."""
        return self._client.list_groups()

    def set_persistent_players_enabled(self, enabled):
        """Enables or disables the creation of persistent players on the server."""
        return self._client._send_command('set_persistent_players_enabled', {
            'enabled': enabled
        })

class GroupAdmin:
    """
    A client class for group administrators to manage games within a specific GameGroup.
    """
    def __init__(self, group_id, host='127.0.0.1', port=65432, group_admin_password=None, use_tls=False, auth_user=None, auth_password=None):
        self.group_id = group_id
        self.host = host
        self.port = port
        self.group_admin_password = group_admin_password
        self.use_tls = use_tls
        self.auth_user = auth_user
        self.auth_password = auth_password
        self._client = GameClient(host, port, group_admin_password, use_tls, auth_user, auth_password)
        self._logger = logging.getLogger(f"GroupAdmin.{group_id}")
        self._logger.setLevel(logging.INFO)

    def configure_logging(self, host, port):
        """Configures the group admin client to send logs to a logging server."""
        self._client.configure_logging(host, port, f"GroupAdmin.{self.group_id}")
        self._logger = self._client._logger

    def list_games(self):
        """Retrieves a dictionary of games belonging to this group as RemoteGame objects, indexed by ID."""
        remote_group = RemoteGroup(self.group_id, self.host, self.port, self.group_admin_password, self.use_tls, self.auth_user, self.auth_password)
        
        # Propagate logging configuration if any
        for h in self._logger.handlers:
            if isinstance(h, SocketHandler):
                remote_group.configure_logging(h.host, h.port)
                break
                
        return remote_group.list_games()

    def kick_player(self, game_id, player_id):
        """Kicks a player from a specific game in the group."""
        return self._client._send_command('kick_player', {
            'game_id': game_id, 
            'player_id': player_id,
            'group_id': self.group_id
        })

    def kick_observer(self, game_id, observer_id):
        """Kicks an observer from a specific game in the group."""
        return self._client._send_command('kick_observer', {
            'game_id': game_id, 
            'observer_id': observer_id,
            'group_id': self.group_id
        })

    def set_group_admin_password(self, new_password):
        """Sets a new administrator password for this group."""
        result = self._client._send_command('set_group_admin_password', {
            'group_id': self.group_id,
            'new_password': new_password
        })
        if result.get('status') == 'success':
            self.group_admin_password = new_password
            self._client.password = new_password
        return result

class RemoteGame:
    """
    A proxy for a Game object on a remote server.
    """
    def __init__(self, game_id, host='127.0.0.1', port=65432, password=None, use_tls=False, auth_user=None, auth_password=None):
        self.game_id = game_id
        self.host = host
        self.port = port
        self._client = GameClient(host, port, password, use_tls, auth_user, auth_password)
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
        if isinstance(player, PersistentPlayer):
            params['persistent_player_password'] = player.password
            
        self._send_command('add_player', params)

    def add_observer(self, observer, password=None):
        """
        Adds an observer to the remote game.

        Args:
            observer (Observer): The observer to add.
            password (str, optional): The password for observers of this game.
        """
        self._logger.info(f"Adding observer {observer.name} to game {self.game_id}")
        params = {
            'observer': {'name': observer.name, 'attributes': observer.attributes},
            'observer_password': password,
        }
        if isinstance(observer, PersistentPlayer):
            params['persistent_player_password'] = observer.password
            
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
        return [Player(p['name'], id=p['id'], **p['attributes']) for p in data]

    @property
    def observers(self):
        """Gets the list of observers in the remote game."""
        data = self._send_command('get_observers')
        return [Observer(o['name'], id=o['id'], **o['attributes']) for o in data]

    def set_state(self, state):
        """Sets the state of the remote game."""
        return self._send_command('set_game_state', {'state': state})

class RemoteGroup:
    """
    A proxy for a GameGroup object on a remote server.
    """
    def __init__(self, group_id, host='127.0.0.1', port=65432, password=None, use_tls=False, auth_user=None, auth_password=None):
        self.group_id = group_id
        self.host = host
        self.port = port
        self._client = GameClient(host, port, password, use_tls, auth_user, auth_password)
        self._logger = logging.getLogger(f"RemoteGroup.{group_id}")
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = True

    def configure_logging(self, host, port, name=None):
        """Configures the remote group proxy to send logs to a logging server."""
        if name is None:
            name = f"RemoteGroup.{self.group_id[:8]}"
        self._client.configure_logging(host, port, name)
        self._logger = self._client._logger

    def _send_command(self, action, params=None):
        """Sends a command to the server for a specific group and returns the response."""
        full_params = {'group_id': self.group_id}
        if params:
            full_params.update(params)
        return self._client._send_command(action, full_params)

    def create_game(self, **game_options):
        """Creates a new game within this group."""
        return self._client.create_game(group_id=self.group_id, **game_options)

    def list_games(self):
        """Lists all games in this group."""
        games_data = self._client._send_command('list_group_games', {'group_id': self.group_id})
        
        remote_games = {}
        for gid in games_data:
            remote_games[gid] = RemoteGame(gid, self.host, self.port, self._client.password, self._client.use_tls, self._client.auth_user, self._client.auth_password)
            
            # Propagate logging configuration if any
            for h in self._logger.handlers:
                if isinstance(h, SocketHandler):
                    remote_games[gid].configure_logging(h.host, h.port)
                    break
                    
        return remote_games

    @property
    def name(self):
        """Gets the name of the group."""
        return self._send_command('get_group_info').get('name')

    @property
    def attributes(self):
        """Gets the attributes of the group."""
        return self._send_command('get_group_info').get('attributes', {})
