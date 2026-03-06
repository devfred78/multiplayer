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
from multiprocessing import Process
from datetime import datetime, timedelta, timezone
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

from .game import Game, Player
from .exceptions import GameLogicError, PlayerLimitReachedError, AuthenticationError

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

def _run_server_process(host, port, password, use_tls, certfile, keyfile):
    """The main server loop that listens for and handles connections."""
    games = {}
    games_lock = threading.Lock()
    context = None
    if use_tls:
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.minimum_version = ssl.TLSVersion.TLSv1_3
        context.load_cert_chain(certfile=certfile, keyfile=keyfile)
    bindsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    bindsocket.bind((host, port))
    bindsocket.listen()
    try:
        while True:
            newsocket, fromaddr = bindsocket.accept()
            conn = context.wrap_socket(newsocket, server_side=True) if use_tls else newsocket
            thread = threading.Thread(target=_handle_client, args=(conn, fromaddr, games, games_lock, password))
            thread.start()
    finally:
        if use_tls:
            os.remove(certfile)
            os.remove(keyfile)

def _handle_client(conn, addr, games, lock, server_password):
    """Handles a single client connection."""
    print(f"Connected by {addr}")
    try:
        with conn:
            data = conn.recv(1024)
            if not data:
                return
            try:
                command = json.loads(data.decode('utf-8'))
                client_password = command.get('password')
                if server_password is not None and client_password != server_password:
                    raise AuthenticationError("Invalid server password")
                action = command.get('action')
                params = command.get('params', {})
                with lock:
                    response = _execute_command(games, action, params)
                conn.sendall(json.dumps(response).encode('utf-8'))
            except (json.JSONDecodeError, TypeError, AuthenticationError) as e:
                error_response = {'status': 'error', 'type': type(e).__name__, 'message': str(e)}
                conn.sendall(json.dumps(error_response).encode('utf-8'))
    finally:
        print(f"Disconnected from {addr}")

def _execute_command(games, action, params):
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
                game_password = params.get('game_password')
                game.add_player(player, password=game_password)
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
    except (GameLogicError, PlayerLimitReachedError, AuthenticationError) as e:
        result = {'status': 'error', 'type': type(e).__name__, 'message': str(e)}
    except Exception as e:
        result = {'status': 'error', 'type': 'ServerError', 'message': str(e)}
    return result

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
        self._server_process = Process(target=_run_server_process, args=(self.host, self.port, self.password, self.use_tls, certfile, keyfile))
        self._server_process.start()
        self._stop_discovery.clear()
        self._discovery_thread = threading.Thread(target=self._run_discovery_service)
        self._discovery_thread.start()
        print(f"Server started on {self.host}:{self.port} with PID {self._server_process.pid}")
        if self.use_tls:
            print("TLS encryption is enabled.")
        print("Network discovery service started.")

    def stop(self):
        """Stops the game server and discovery service."""
        if self._server_process and self._server_process.is_alive():
            self._server_process.terminate()
            self._server_process.join()
            print("Server stopped.")
        else:
            print("Server is not running.")
        if self._discovery_thread and self._discovery_thread.is_alive():
            self._stop_discovery.set()
            self._discovery_thread.join()
            print("Network discovery service stopped.")

    def _run_discovery_service(self):
        """Listens for multicast discovery messages and responds."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', DISCOVERY_PORT))
        mreq = struct.pack("4sl", socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        sock.settimeout(1.0)
        while not self._stop_discovery.is_set():
            try:
                data, addr = sock.recvfrom(1024)
                if data == DISCOVERY_MESSAGE:
                    print(f"Discovery request from {addr}, sending response...")
                    response_ip = self._get_lan_ip()
                    response_port = self.port
                    message = struct.pack(RESPONSE_MESSAGE_FORMAT, response_ip.encode('utf-8'), response_port)
                    sock.sendto(message, addr)
            except socket.timeout:
                continue

    def _get_lan_ip(self):
        """Finds the local IP address of the machine."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP
