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
from multiprocessing import Process, Event, Queue
from queue import Empty
from datetime import datetime, timedelta, timezone
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import enum

from .game import Game, Player, GameState
from .exceptions import GameLogicError, PlayerLimitReachedError, AuthenticationError

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

def _generate_self_signed_cert_data():
    """Generates a self-signed certificate and key, returning their content."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, u"multiplayer.games")])
    cert = x509.CertificateBuilder().subject_name(subject).issuer_name(issuer).public_key(key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(datetime.now(timezone.utc)).not_valid_after(datetime.now(timezone.utc) + timedelta(days=1)).add_extension(x509.SubjectAlternativeName([x509.DNSName(u"localhost")]), critical=False).sign(key, hashes.SHA256())
    key_data = key.private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.TraditionalOpenSSL, encryption_algorithm=serialization.NoEncryption())
    cert_data = cert.public_bytes(serialization.Encoding.PEM)
    return cert_data, key_data

def _run_discovery_service(tcp_port, stop_event):
    """Listens for multicast discovery messages and responds."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', DISCOVERY_PORT))
        mreq = struct.pack("4sl", socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        sock.settimeout(1.0)
        
        def get_lan_ip():
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try: s.connect(('10.255.255.255', 1)); IP = s.getsockname()[0]
            except Exception: IP = '127.0.0.1'
            finally: s.close()
            return IP

        while not stop_event.is_set():
            try:
                data, addr = sock.recvfrom(1024)
                if data == DISCOVERY_MESSAGE:
                    response_ip = get_lan_ip()
                    message = struct.pack(RESPONSE_MESSAGE_FORMAT, response_ip.encode('utf-8'), tcp_port)
                    sock.sendto(message, addr)
            except socket.timeout:
                continue
    except Exception as e:
        print(f"Discovery service error: {e}")
    print("Network discovery service stopped.")

def _run_tcp_server(host, port, password, use_tls, cert_data, key_data, stop_event, status_queue):
    """The main server loop that listens for and handles connections."""
    games = {}
    games_lock = threading.Lock()
    context = None
    certfile, keyfile = None, None
    server_socket = None

    try:
        if use_tls:
            with tempfile.NamedTemporaryFile(delete=False) as cert_file_obj:
                certfile = cert_file_obj.name; cert_file_obj.write(cert_data)
            with tempfile.NamedTemporaryFile(delete=False) as key_file_obj:
                keyfile = key_file_obj.name; key_file_obj.write(key_data)
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.minimum_version = ssl.TLSVersion.TLSv1_3
            context.load_cert_chain(certfile=certfile, keyfile=keyfile)

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Allow immediate reuse of the port to avoid WinError 10013/10048 after quick restarts
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((host, port))
        server_socket.listen()
        server_socket.settimeout(1.0)
        
        # Signal successful bind
        status_queue.put("READY")

        while not stop_event.is_set():
            try:
                newsocket, fromaddr = server_socket.accept()
                conn = context.wrap_socket(newsocket, server_side=True) if use_tls else newsocket
                thread = threading.Thread(target=_handle_client, args=(conn, fromaddr, games, games_lock, password))
                thread.start()
            except socket.timeout:
                continue
    except Exception as e:
        status_queue.put(str(e))
    finally:
        if server_socket:
            server_socket.close()
        if use_tls:
            if certfile and os.path.exists(certfile): os.remove(certfile)
            if keyfile and os.path.exists(keyfile): os.remove(keyfile)
        print("TCP server stopped.")

def _handle_client(conn, addr, games, lock, server_password):
    """Handles a single client connection."""
    try:
        with conn:
            data = conn.recv(1024)
            if not data: return
            try:
                command = json.loads(data.decode('utf-8'))
                if server_password is not None and command.get('password') != server_password:
                    raise AuthenticationError("Invalid server password")
                response = _execute_command(games, command.get('action'), command.get('params', {}))
                conn.sendall(json.dumps(response, cls=EnumEncoder).encode('utf-8'))
            except (json.JSONDecodeError, TypeError, AuthenticationError) as e:
                error_response = {'status': 'error', 'type': type(e).__name__, 'message': str(e)}
                conn.sendall(json.dumps(error_response, cls=EnumEncoder).encode('utf-8'))
    except Exception as e:
        print(f"Error handling client {addr}: {e}")

def _execute_command(games, action, params):
    """Executes a command on the game objects and returns a response."""
    try:
        if action == 'create_game':
            game_id = str(uuid.uuid4()); games[game_id] = Game(**params)
            return {'status': 'success', 'data': {'game_id': game_id}}
        elif action == 'list_games':
            return {'status': 'success', 'data': {gid: g.attributes for gid, g in games.items() if g.state != GameState.FINISHED}}
        
        game_id = params.get('game_id')
        if not game_id or game_id not in games:
            return {'status': 'error', 'type': 'GameNotFoundError', 'message': 'Game not found'}
        game = games[game_id]

        if action == 'add_player':
            player = Player(params['player']['name'], **params['player'].get('attributes', {}))
            game.add_player(player, password=params.get('game_password'))
        elif action == 'start': game.start()
        elif action == 'pause': game.pause()
        elif action == 'resume': game.resume()
        elif action == 'stop': game.stop()
        elif action == 'next_turn': game.next_turn()
        elif action == 'get_current_player':
            player = game.current_player
            return {'status': 'success', 'data': {'name': player.name, 'attributes': player.attributes} if player else None}
        elif action == 'get_game_state':
            return {'status': 'success', 'data': {'status': game.state, 'custom': game.custom_state}}
        elif action == 'set_game_state':
            game.custom_state = params.get('state')
        else:
            return {'status': 'error', 'type': 'ServerError', 'message': 'Unknown action'}
        return {'status': 'success'}
    except (GameLogicError, PlayerLimitReachedError, AuthenticationError) as e:
        return {'status': 'error', 'type': type(e).__name__, 'message': str(e)}
    except Exception as e:
        return {'status': 'error', 'type': 'ServerError', 'message': str(e)}

def _server_main_loop(host, port, password, use_tls, cert_data, key_data, stop_event, status_queue):
    """The main function for the server process, running both services."""
    # We pass status_queue to tcp_server to report bind errors
    tcp_thread = threading.Thread(target=_run_tcp_server, args=(host, port, password, use_tls, cert_data, key_data, stop_event, status_queue))
    tcp_thread.start()
    
    # Wait for TCP server to initialize (bind port)
    # It will put "READY" or an error message in the queue
    status = status_queue.get()
    
    if status != "READY":
        # If TCP server failed, we don't start discovery and we exit
        print(f"Server process failed to bind: {status}")
        # We put the status back so the parent process can read it too if needed, 
        # but actually the parent reads from the same queue.
        # Since queue is consumed, we should put it back or let parent read it directly?
        # Better: Parent reads it. We just peek or wait? 
        # Actually, if we are here, we are in the child process. The parent is waiting on the queue too.
        # If multiple consumers wait on a queue, only one gets it.
        # So we should NOT consume it here if the parent waits for it.
        # BUT, we need to know if we should start discovery.
        
        # Alternative: Parent waits for queue. Child puts in queue.
        # Child threads run.
        # Let's change logic: _run_tcp_server puts in queue.
        # Parent reads queue.
        # If READY, parent is happy.
        # Child needs to know too? No, child just runs threads.
        # If _run_tcp_server fails, it returns/exits.
        # So we should start discovery only if TCP server is running?
        # Let's just start both. If TCP fails, it will exit, and we can stop discovery.
        pass
    else:
        # If READY, we start discovery
        print(f"Server process started with PID {os.getpid()}")
        if use_tls: print("TLS encryption is enabled.")
        
        discovery_thread = threading.Thread(target=_run_discovery_service, args=(port, stop_event))
        discovery_thread.start()
        print("Network discovery service started.")
        
        discovery_thread.join()

    tcp_thread.join()
    print("Server process shutting down.")

class GameServer:
    """
    Manages multiple Game instances and handles network requests from clients.
    """
    def __init__(self, host='0.0.0.0', port=65432, password=None, use_tls=False):
        self.host = host
        self.port = port
        self.password = password
        self.use_tls = use_tls
        self._server_process = None
        self._stop_event = None

    def start(self):
        """Starts the game server and discovery service in a separate process."""
        if self._server_process and self._server_process.is_alive():
            print("Server is already running.")
            return
        
        self._stop_event = Event()
        status_queue = Queue() # Queue for communicating startup status
        
        cert_data, key_data = (None, None)
        if self.use_tls:
            cert_data, key_data = _generate_self_signed_cert_data()

        self._server_process = Process(target=_server_main_loop, args=(self.host, self.port, self.password, self.use_tls, cert_data, key_data, self._stop_event, status_queue))
        self._server_process.start()
        
        # Wait for the server process to signal that it's ready or failed
        try:
            status = status_queue.get(timeout=5)
            if status != "READY":
                self._server_process.terminate()
                self._server_process.join()
                raise RuntimeError(f"Server failed to start: {status}")
        except Empty:
             self._server_process.terminate()
             self._server_process.join()
             raise RuntimeError("Server timed out during startup (check firewall).")

        print(f"Main process: Server process launched with PID {self._server_process.pid}")

    def stop(self):
        """Stops the game server and discovery service."""
        if self._server_process and self._server_process.is_alive():
            print("Stopping server process...")
            self._stop_event.set()
            self._server_process.join(timeout=5)
            if self._server_process.is_alive():
                print("Server process did not stop gracefully, terminating.")
                self._server_process.terminate()
            print("Server stopped.")
        else:
            print("Server is not running.")
