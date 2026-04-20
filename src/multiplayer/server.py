"""
This module provides the server-side implementation for networked multiplayer games.
"""
import socket
import json
import threading
import uuid
import struct
import ssl
import tempfile
import os
import logging
from multiprocessing import Process
from datetime import datetime, timedelta, timezone
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import enum

from .game import Game, Player, Observer, GameState
from .exceptions import GameLogicError, PlayerLimitReachedError, ObserverLimitReachedError, AuthenticationError

# Custom JSON Encoder to handle enums
class EnumEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, enum.Enum):
            return obj.value
        return super().default(obj)

# Constants for network discovery
MULTICAST_GROUP = '224.1.1.1'
DISCOVERY_PORT = 5007
DISCOVERY_MESSAGE = b'multiplayer_game_discovery_request'
RESPONSE_MESSAGE_FORMAT = b'!15sH' # 15-char IP, unsigned short port

def _generate_self_signed_cert():
    """Generates a temporary self-signed certificate and key."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, u"multiplayer.games"),
    ])
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.now(timezone.utc)
    ).not_valid_after(
        datetime.now(timezone.utc) + timedelta(days=1)
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName(u"localhost")]),
        critical=False,
    ).sign(key, hashes.SHA256())
    key_file = tempfile.NamedTemporaryFile(delete=False)
    cert_file = tempfile.NamedTemporaryFile(delete=False)
    key_file.write(key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ))
    cert_file.write(cert.public_bytes(serialization.Encoding.PEM))
    key_file.close()
    cert_file.close()
    return cert_file.name, key_file.name

def _run_server_process(host, port, password, admin_password, use_tls, certfile, keyfile, logging_host=None, logging_port=None, logger_name="GameServer"):
    """The main server loop that listens for and handles connections."""
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    if logging_host and logging_port:
        from logging.handlers import SocketHandler
        # Remove existing SocketHandlers if any
        for h in logger.handlers[:]:
            if isinstance(h, SocketHandler):
                logger.removeHandler(h)
        handler = SocketHandler(logging_host, logging_port)
        logger.addHandler(handler)
        logger.info(f"Logging configured to send to {logging_host}:{logging_port}")

    logger.info(f"Starting server process on {host}:{port}")
    games = {}
    games_lock = threading.Lock()
    context = None
    if use_tls:
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.minimum_version = ssl.TLSVersion.TLSv1_3
        context.load_cert_chain(certfile=certfile, keyfile=keyfile)
    bindsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    bindsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    bindsocket.bind((host, port))
    bindsocket.listen()
    try:
        bindsocket.settimeout(1.0)
        while True:
            try:
                newsocket, fromaddr = bindsocket.accept()
            except socket.timeout:
                continue
            try:
                conn = context.wrap_socket(newsocket, server_side=True) if use_tls else newsocket
                thread = threading.Thread(target=_handle_client, args=(conn, fromaddr, games, games_lock, password, admin_password, logger_name))
                thread.daemon = True
                thread.start()
            except (ssl.SSLError, OSError) as e:
                print(f"Failed to wrap socket or start thread: {e}")
                newsocket.close()
    finally:
        bindsocket.close()
        if use_tls:
            os.remove(certfile)
            os.remove(keyfile)

def _handle_client(conn, addr, games, lock, server_password, admin_password, logger_name="GameServer"):
    """Handles a single client connection."""
    logger = logging.getLogger(logger_name)
    logger.info(f"Connected by {addr}")
    try:
        with conn:
            data = conn.recv(1024)
            if not data:
                return
            try:
                command = json.loads(data.decode('utf-8'))
                client_password = command.get('password')
                action = command.get('action')
                params = command.get('params', {})

                # Check if it's an admin action
                is_admin_action = action in ['stop_server', 'restart_server', 'kick_player', 'kick_observer', 'get_server_info', 'set_logging_config', 'set_logging_enabled', 'list_all_players']
                
                if is_admin_action:
                    if admin_password is None:
                         raise AuthenticationError("Admin actions are disabled on this server")
                    if client_password != admin_password:
                        raise AuthenticationError("Invalid admin password")
                elif server_password is not None and client_password != server_password:
                    raise AuthenticationError("Invalid server password")

                with lock:
                    response = _execute_command(games, action, params)
                conn.sendall(json.dumps(response, cls=EnumEncoder).encode('utf-8'))
            except (json.JSONDecodeError, TypeError, AuthenticationError) as e:
                error_response = {'status': 'error', 'type': type(e).__name__, 'message': str(e)}
                conn.sendall(json.dumps(error_response, cls=EnumEncoder).encode('utf-8'))
    finally:
        logger.info(f"Disconnected from {addr}")

def _execute_command(games, action, params):
    """Executes a command on the game objects and returns a response."""
    try:
        # Server-level actions
        if action == 'create_game':
            game_id = str(uuid.uuid4())
            games[game_id] = Game(**params)
            return {'status': 'success', 'data': {'game_id': game_id}}
        
        elif action == 'list_games':
            game_list = {gid: g.attributes for gid, g in games.items() if g.state != GameState.FINISHED}
            return {'status': 'success', 'data': game_list}
        
        elif action == 'stop_server':
            result = {'status': 'success', 'message': 'Server stopping...'}
            def delayed_exit():
                import time
                time.sleep(0.5)
                os._exit(0)
            threading.Thread(target=delayed_exit).start()
            return result
        
        elif action == 'restart_server':
            result = {'status': 'success', 'message': 'Server restarting...'}
            def delayed_restart():
                import time
                time.sleep(0.5)
                games.clear()
            threading.Thread(target=delayed_restart).start()
            return result
        
        elif action == 'get_server_info':
            return {'status': 'success', 'data': {
                'games_count': len(games),
                'active_games': [gid for gid, g in games.items() if g.state != GameState.FINISHED]
            }}
        
        elif action == 'set_logging_config':
            logging_host = params.get('host')
            logging_port = params.get('port')
            if logging_host and logging_port:
                from logging.handlers import SocketHandler
                logger = logging.getLogger("GameServer")
                # Remove existing SocketHandlers if any to avoid duplicates
                for h in logger.handlers[:]:
                    if isinstance(h, SocketHandler):
                        logger.removeHandler(h)
                
                handler = SocketHandler(logging_host, logging_port)
                logger.addHandler(handler)
                logger.info(f"Logging reconfigured to send to {logging_host}:{logging_port}")
                return {'status': 'success'}
            else:
                return {'status': 'error', 'message': 'Missing host or port'}
        
        elif action == 'set_logging_enabled':
            enabled = params.get('enabled', True)
            logger = logging.getLogger("GameServer")
            if enabled:
                logger.setLevel(logging.INFO)
                logger.info("Logging enabled")
            else:
                logger.info("Logging disabled")
                logger.setLevel(logging.CRITICAL + 1)  # Effectively disables all logging
            return {'status': 'success'}
        
        elif action == 'list_all_players':
            all_players = []
            for gid, game in games.items():
                game_name = game.attributes.get('name', 'Unknown')
                for player in game.players:
                    all_players.append({
                        'name': player.name,
                        'attributes': player.attributes,
                        'game_id': gid,
                        'game_name': game_name
                    })
            return {'status': 'success', 'data': all_players}

        # Game-specific actions
        game_id = params.get('game_id')
        if not game_id or game_id not in games:
            return {'status': 'error', 'type': 'GameNotFoundError', 'message': 'Game not found'}
        
        game = games[game_id]
        
        if action == 'add_player':
            player_data = params['player']
            player = Player(player_data['name'], **player_data.get('attributes', {}))
            game_password = params.get('game_password')
            game.add_player(player, password=game_password)
            return {'status': 'success'}
        
        elif action == 'add_observer':
            observer_data = params['observer']
            observer = Observer(observer_data['name'], **observer_data.get('attributes', {}))
            game_password = params.get('game_password')
            game.add_observer(observer, password=game_password)
            return {'status': 'success'}
        
        elif action == 'start':
            game.start()
            return {'status': 'success'}
        
        elif action == 'pause':
            game.pause()
            return {'status': 'success'}
        
        elif action == 'resume':
            game.resume()
            return {'status': 'success'}
        
        elif action == 'stop':
            game.stop()
            return {'status': 'success'}
        
        elif action == 'next_turn':
            game.next_turn()
            return {'status': 'success'}
        
        elif action == 'get_current_player':
            player = game.current_player
            if player:
                return {'status': 'success', 'data': {'name': player.name, 'attributes': player.attributes}}
            else:
                return {'status': 'success', 'data': None}
        
        elif action == 'get_game_state':
            return {'status': 'success', 'data': {'status': game.state, 'custom': game.custom_state}}
        
        elif action == 'get_players':
            player_list = [{'name': p.name, 'attributes': p.attributes} for p in game.players]
            return {'status': 'success', 'data': player_list}
        
        elif action == 'get_observers':
            observer_list = [{'name': o.name, 'attributes': o.attributes} for o in game.observers]
            return {'status': 'success', 'data': observer_list}
        
        elif action == 'set_game_state':
            game.custom_state = params.get('state')
            return {'status': 'success'}
        
        elif action == 'kick_player':
            player_name = params.get('player_name')
            game.remove_player(player_name)
            return {'status': 'success'}
        
        elif action == 'kick_observer':
            observer_name = params.get('observer_name')
            game.remove_observer(observer_name)
            return {'status': 'success'}
        
        else:
            return {'status': 'error', 'type': 'ServerError', 'message': 'Unknown action'}
            
    except (GameLogicError, PlayerLimitReachedError, ObserverLimitReachedError, AuthenticationError) as e:
        return {'status': 'error', 'type': type(e).__name__, 'message': str(e)}
    except Exception as e:
        return {'status': 'error', 'type': 'ServerError', 'message': str(e)}

class GameServer:
    """
    Manages multiple Game instances and handles network requests from clients.
    """
    def __init__(self, host='0.0.0.0', port=65432, password=None, admin_password=None, use_tls=False, logging_host=None, logging_port=None, logger_name="GameServer"):
        self.host = host
        self.port = port
        self.password = password
        self.admin_password = admin_password
        self.use_tls = use_tls
        self.logging_host = logging_host
        self.logging_port = logging_port
        self.logger_name = logger_name
        self._server_process = None
        self._discovery_thread = None
        self._stop_discovery = threading.Event()

    def start(self):
        """Starts the game server and discovery service in separate processes/threads."""
        if self._server_process and self._server_process.is_alive():
            print("Server is already running.")
            return
        certfile, keyfile = (None, None)
        if self.use_tls:
            certfile, keyfile = _generate_self_signed_cert()
        self._server_process = Process(target=_run_server_process, args=(self.host, self.port, self.password, self.admin_password, self.use_tls, certfile, keyfile, self.logging_host, self.logging_port, self.logger_name))
        self._server_process.daemon = True
        self._server_process.start()
        self._stop_discovery.clear()
        self._discovery_thread = threading.Thread(target=self._run_discovery_service)
        self._discovery_thread.daemon = True
        self._discovery_thread.start()
        print(f"Server started on {self.host}:{self.port} with PID {self._server_process.pid}")
        if self.use_tls:
            print("TLS encryption is enabled.")
        print("Network discovery service started.")

    def stop(self, timeout=5):
        """Stops the game server and discovery service."""
        if self._server_process and self._server_process.is_alive():
            self._server_process.terminate()
            self._server_process.join(timeout=timeout)
            if self._server_process.is_alive():
                print("Server process did not terminate gracefully, killing it...")
                self._server_process.kill()
                self._server_process.join()
            print("Server stopped.")
        else:
            print("Server is not running.")
        if self._discovery_thread and self._discovery_thread.is_alive():
            self._stop_discovery.set()
            self._discovery_thread.join(timeout=timeout)
            print("Network discovery service stopped.")

    def _run_discovery_service(self):
        """Listens for multicast discovery messages and responds."""
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # SO_REUSEPORT is necessary for some OS (like MacOS) when binding to the same port
            if hasattr(socket, 'SO_REUSEPORT'):
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            
            try:
                sock.bind(('', DISCOVERY_PORT))
            except OSError as e:
                logging.getLogger(self.logger_name).error(f"Failed to bind discovery service to port {DISCOVERY_PORT}: {e}")
                return

            mreq = struct.pack("4sl", socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
            try:
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            except OSError as e:
                logging.getLogger(self.logger_name).error(f"Failed to join multicast group: {e}")
                return

            sock.settimeout(1.0)
            while not self._stop_discovery.is_set():
                try:
                    data, addr = sock.recvfrom(1024)
                    if data == DISCOVERY_MESSAGE:
                        logger = logging.getLogger(self.logger_name)
                        logger.info(f"Discovery request from {addr}, sending response...")
                        response_ip = self._get_lan_ip()
                        response_port = self.port
                        message = struct.pack(RESPONSE_MESSAGE_FORMAT, response_ip.encode('utf-8'), response_port)
                        sock.sendto(message, addr)
                except socket.timeout:
                    continue
                except Exception as e:
                    logging.getLogger(self.logger_name).error(f"Error in discovery service: {e}")

    def _get_lan_ip(self):
        """Helper to get the local LAN IP address."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect(('10.255.255.255', 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip
 