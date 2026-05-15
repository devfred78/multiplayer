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
from multiprocessing import get_context
from datetime import datetime, timedelta, timezone
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import enum

from .game import Game, Player, Observer, GameState, PersistentPlayer
from .exceptions import GameLogicError, PlayerLimitReachedError, ObserverLimitReachedError, AuthenticationError

# Custom JSON Encoder to handle enums
class EnumEncoder(json.JSONEncoder):
    """
    Custom JSON Encoder to handle enums.
    """
    def default(self, obj):
        if isinstance(obj, enum.Enum):
            return obj.value
        return super().default(obj)

# Constants for network discovery
MULTICAST_GROUP = '224.1.1.1'
DISCOVERY_PORT = 5007
DISCOVERY_MESSAGE = b'multiplayer_game_discovery_request'
RESPONSE_MESSAGE_FORMAT = b'!15sH64s' # 15-char IP, unsigned short port, 64-char name

def _generate_self_signed_cert(domain="localhost"):
    """
    Generates a temporary self-signed TLS certificate and key.
    
    Args:
        domain (str): The domain name for the certificate.
        
    Returns:
        tuple: (cert_path, key_path) of the temporary files.
    """
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, domain),
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
        datetime.now(timezone.utc) + timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName(domain)]),
        critical=False,
    ).sign(key, hashes.SHA256())
    key_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pem")
    cert_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pem")
    key_file.write(key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ))
    cert_file.write(cert.public_bytes(serialization.Encoding.PEM))
    key_file.close()
    cert_file.close()
    return cert_file.name, key_file.name

def get_cert_expiration(cert_path):
    """
    Gets the expiration date of a PEM certificate.
    
    Args:
        cert_path (str): Path to the certificate file.
        
    Returns:
        str: ISO format date string or error message if failed.
    """
    try:
        with open(cert_path, "rb") as f:
            cert_data = f.read()
        cert = x509.load_pem_x509_certificate(cert_data)
        return cert.not_valid_after_utc.isoformat()
    except Exception as e:
        return f"Error reading certificate: {e}"

def _run_server_process(host, port, password, admin_password, use_tls, certfile, keyfile, 
                        logging_host=None, logging_port=None, logger_name="GameServer", name=None, 
                        persistent_players_enabled=True, unencrypted_port=None, hidden=False, 
                        discovery_event=None, tls_domain=None, tls_self_signed=None, 
                        persistence_type=None, persistence_path=None):
    """
    The main server loop that listens for and handles connections.
    """
    from .data.persistence import create_datastore
    datastore = create_datastore(persistence_type, persistence_path)
    
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

    server_start_msg = f"Starting server process on {host}:{port}"
    if unencrypted_port:
        server_start_msg += f" (Unencrypted on {host}:{unencrypted_port})"
    if name:
        server_start_msg += f" (Name: {name})"
    logger.info(server_start_msg)
    
    games, groups, persistent_players = datastore.load()
    if games or groups or persistent_players:
        logger.info(f"Loaded {len(games)} games, {len(groups)} groups, and {len(persistent_players)} persistent players from storage.")
    
    games_lock = threading.Lock()
    context = None
    if use_tls:
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.minimum_version = ssl.TLSVersion.TLSv1_3
        context.load_cert_chain(certfile=certfile, keyfile=keyfile)
    
    # Primary listener
    bindsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    bindsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    bindsocket.bind((host, port))
    bindsocket.listen()
    
    # Secondary listener (unencrypted)
    unencrypted_bindsocket = None
    if use_tls and unencrypted_port:
        unencrypted_bindsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        unencrypted_bindsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        unencrypted_bindsocket.bind((host, unencrypted_port))
        unencrypted_bindsocket.listen()

    import time
    server_passwords = {
        'server': password, 
        'admin': admin_password, 
        'persistent_players_enabled': persistent_players_enabled, 
        'hidden': hidden, 
        'start_time': time.time(),
        'host': host,
        'port': port,
        'unencrypted_port': unencrypted_port,
        'tls_domain': tls_domain,
        'tls_self_signed': tls_self_signed,
        'logging_host': logging_host,
        'logging_port': logging_port
    }
    
    import select
    
    try:
        inputs = [bindsocket]
        if unencrypted_bindsocket:
            inputs.append(unencrypted_bindsocket)
            
        while True:
            readable, _, _ = select.select(inputs, [], [], 1.0)
            
            # Sync discovery state if event is provided
            if discovery_event:
                if server_passwords.get('hidden', False):
                    discovery_event.set()
                else:
                    discovery_event.clear()
            
            for s in readable:
                try:
                    newsocket, fromaddr = s.accept()
                    is_tls_conn = (s == bindsocket and use_tls)
                    conn = context.wrap_socket(newsocket, server_side=True) if is_tls_conn else newsocket
                    thread = threading.Thread(target=_handle_client, args=(conn, fromaddr, games, groups, games_lock, server_passwords, logger_name, name, is_tls_conn, certfile, persistent_players, datastore))
                    thread.daemon = True
                    thread.start()
                except (ssl.SSLError, OSError) as e:
                    logger.error(f"Failed to wrap socket or start thread: {e}")
                    # Attempt to close newsocket if it was accepted but wrapping/threading failed
                    try:
                        newsocket.close()
                    except Exception:
                        pass
    finally:
        bindsocket.close()
        if unencrypted_bindsocket:
            unencrypted_bindsocket.close()
        # Clean up temporary files if they were created (indicated by "tmp" in filename or being specifically tracked)
        # Note: self._temp_certs from GameServer is not available here, so we rely on path indicators or naming.
        if use_tls and certfile and ("tmp" in certfile.lower() or "multiplayer_fullchain" in certfile.lower()): 
             try:
                if os.path.exists(certfile):
                    os.remove(certfile)
                # Only remove keyfile if it's also a temp file (like in self-signed case)
                if keyfile and "tmp" in keyfile.lower() and os.path.exists(keyfile): 
                    os.remove(keyfile)
             except Exception:
                 pass

def _handle_client(conn, addr, games, groups, lock, server_passwords, logger_name="GameServer", 
                   server_name=None, use_tls=False, certfile=None, persistent_players=None, datastore=None):
    """
    Handles a single client connection.
    """
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
                auth_user = command.get('auth_user')
                auth_password = command.get('auth_password')
                
                server_password = server_passwords.get('server')
                admin_password = server_passwords.get('admin')

                # Check persistent player credentials if provided
                user_role = None
                user_managed_groups = []
                if auth_user and auth_password:
                    if persistent_players and auth_user in persistent_players:
                        p = persistent_players[auth_user]
                        if p.password == auth_password:
                            user_role = p.role
                            user_managed_groups = p.managed_groups
                            logger.info(f"Authenticated as persistent player: {auth_user} (role: {user_role})")
                        else:
                            logger.warning(f"Failed authentication for persistent player: {auth_user} (wrong password)")
                            raise AuthenticationError("Invalid persistent player password")
                    else:
                        logger.warning(f"Failed authentication for persistent player: {auth_user} (not found)")
                        raise AuthenticationError("Persistent player account not found")

                # Check if it's an admin action
                is_server_admin_action = action in ['stop_server', 'restart_server', 'get_server_info', 'set_logging_for_server', 'set_logging_enabled', 'list_all_players', 'get_cert_expiration', 'set_server_password', 'set_admin_password', 'create_group', 'remove_group', 'list_groups', 'set_persistent_players_enabled']
                is_group_admin_action = action in ['list_group_games', 'kick_player', 'kick_observer', 'set_group_admin_password', 'get_group_info']
                is_persistent_player_action = action in ['create_persistent_player']
                
                # If it's a kick action, it could be server admin OR group admin
                # If group_id is provided, we check group admin rights.
                # If not, we check server admin rights.
                group_id = params.get('group_id')
                
                # Authorization check
                from .game import PlayerRole
                if is_server_admin_action:
                    # Authorized if:
                    # 1. Global admin password matches
                    # 2. Persistent player is SERVER_ADMIN
                    authorized = False
                    if admin_password is not None and client_password == admin_password:
                        authorized = True
                    elif user_role == PlayerRole.SERVER_ADMIN:
                        authorized = True
                    
                    if not authorized:
                        if admin_password is None and user_role != PlayerRole.SERVER_ADMIN:
                            raise AuthenticationError("Admin actions are disabled on this server")
                        raise AuthenticationError("Invalid admin credentials")
                    
                    # For get_server_info, we need more info than just server_passwords
                    if action == 'get_server_info':
                        params['__server_info__'] = {
                            'host': server_passwords.get('host') or command.get('client_host'),
                            'port': server_passwords.get('port') or command.get('client_port'),
                            'unencrypted_port': server_passwords.get('unencrypted_port'),
                            'use_tls': use_tls,
                            'tls_domain': server_passwords.get('tls_domain'),
                            'tls_self_signed': server_passwords.get('tls_self_signed'),
                            'logging_host': server_passwords.get('logging_host'),
                            'logging_port': server_passwords.get('logging_port'),
                            'hidden': server_passwords.get('hidden', False),
                            'name': server_name,
                            'certfile': certfile
                        }
                
                elif is_group_admin_action and group_id:
                    with lock:
                        group = None
                        for g in groups.values():
                            if g.ID == group_id:
                                group = g
                                break
                        if not group:
                            raise GameLogicError(f"Group with ID '{group_id}' not found")
                        
                        authorized = False
                        # 1. Global admin password matches
                        if admin_password is not None and client_password == admin_password:
                            authorized = True
                        # 2. Persistent player is SERVER_ADMIN
                        elif user_role == PlayerRole.SERVER_ADMIN:
                            authorized = True
                        # 3. Persistent player is GROUP_ADMIN for THIS group
                        elif user_role == PlayerRole.GROUP_ADMIN:
                            # Search by name or ID in managed_groups
                            found = False
                            for mg in user_managed_groups:
                                if mg == group_id:
                                    found = True
                                    break
                                # Also check if mg is the name of the group
                                for gname, g in groups.items():
                                    if gname == mg and g.ID == group_id:
                                        found = True
                                        break
                                if found:
                                    break
                            if found:
                                authorized = True
                        # 4. Group admin password matches
                        elif group.admin_password is not None and client_password == group.admin_password:
                            authorized = True
                        
                        if not authorized:
                            logger.warning(f"Unauthorized group admin action: {action} on group {group_id} for user {auth_user} (role {user_role}). Managed groups: {user_managed_groups}")
                            if group.admin_password is None and admin_password is None and user_role not in [PlayerRole.SERVER_ADMIN, PlayerRole.GROUP_ADMIN]:
                                raise AuthenticationError(f"Group admin actions are disabled for group ID '{group_id}'")
                            raise AuthenticationError("Invalid group admin credentials")
                
                elif is_group_admin_action: # Action without group_id (like kick without group)
                    authorized = False
                    if admin_password is not None and client_password == admin_password:
                        authorized = True
                    elif user_role == PlayerRole.SERVER_ADMIN:
                        authorized = True
                    
                    if not authorized:
                        if admin_password is None and user_role != PlayerRole.SERVER_ADMIN:
                            raise AuthenticationError("Admin actions are disabled on this server")
                        raise AuthenticationError("Invalid admin credentials")
                
                elif is_persistent_player_action:
                    if server_password is not None and client_password != server_password:
                        # Allow server admin to create accounts even if server password is set but not provided?
                        # For simplicity, if server password is set, it must be provided as 'password' field 
                        # OR the user must be already authenticated as SERVER_ADMIN.
                        if user_role != PlayerRole.SERVER_ADMIN:
                             raise AuthenticationError("Invalid server password")
                
                elif server_password is not None and client_password != server_password:
                    if user_role is None: # Not even a simple persistent player logged in
                         raise AuthenticationError("Invalid server password")

                with lock:
                    try:
                        response = _execute_command(games, groups, action, params, server_name=server_name, use_tls=use_tls, certfile=certfile, server_passwords=server_passwords, persistent_players=persistent_players, logger=logger)
                        # Sync to datastore after successful command if it might have changed state
                        if datastore and action in [
                            'create_persistent_player', 'update_persistent_player', 'remove_persistent_player',
                            'create_game', 'stop_game', 'pause_game', 'resume_game', 'set_custom_state',
                            'create_group', 'remove_group', 'set_server_password', 'set_admin_password',
                            'set_persistent_players_enabled', 'set_server_hidden'
                        ]:
                            datastore.save(games, groups, persistent_players)
                    except Exception as e:
                        response = {'status': 'error', 'type': e.__class__.__name__, 'message': str(e)}
                conn.sendall(json.dumps(response, cls=EnumEncoder).encode('utf-8'))
            except Exception as e:
                error_response = {'status': 'error', 'type': e.__class__.__name__, 'message': str(e)}
                conn.sendall(json.dumps(error_response, cls=EnumEncoder).encode('utf-8'))
    finally:
        logger.info(f"Disconnected from {addr}")

def _execute_command(games, groups, action, params, server_name=None, use_tls=False, 
                     certfile=None, server_passwords=None, persistent_players=None, logger=None):
    """
    Executes a command on the game objects and returns a response.
    """
    from .game import GameGroup, PlayerRole
    import logging as logging_module
    if logger is None:
        logger = logging_module.getLogger("GameServer")
    try:
        # Server-level actions
        if action == 'set_persistent_players_enabled':
            enabled = params.get('enabled')
            
            if server_passwords is not None:
                server_passwords['persistent_players_enabled'] = enabled
                status = "enabled" if enabled else "disabled"
                return {'status': 'success', 'message': f'Persistent player creation {status} globally'}
            return {'status': 'error', 'message': 'Server passwords dictionary not available'}

        elif action == 'set_server_hidden':
            hidden = params.get('hidden', False)
            if server_passwords is not None:
                server_passwords['hidden'] = hidden
                status = "hidden" if hidden else "visible"
                return {'status': 'success', 'message': f'Server is now {status}'}
            return {'status': 'error', 'message': 'Server passwords dictionary not available'}

        elif action == 'create_persistent_player':
            name = params.get('name')
            password = params.get('password')
            role_val = params.get('role', 'player')
            managed_groups = params.get('managed_groups', [])
            
            try:
                role = PlayerRole(role_val)
            except ValueError:
                return {'status': 'error', 'message': f"Invalid role: {role_val}"}
            
            if not name or not password:
                return {'status': 'error', 'message': 'Missing name or password'}
            
            # Check if persistent players are enabled
            enabled = True
            if server_passwords is not None:
                enabled = server_passwords.get('persistent_players_enabled', True)
            
            if not enabled:
                return {'status': 'error', 'message': 'Persistent player creation is disabled on this server'}

            if name in persistent_players:
                return {'status': 'error', 'type': 'UserAlreadyExistsError', 'message': f"Player '{name}' already exists"}
            
            player = PersistentPlayer(name, password, role=role, managed_groups=managed_groups, **params.get('attributes', {}))
            persistent_players[name] = player
            return {'status': 'success', 'data': {'player_id': player.ID, 'name': player.name, 'role': player.role.value}}

        elif action == 'update_persistent_player':
            name = params.get('name')
            if not name or name not in persistent_players:
                return {'status': 'error', 'message': f"Player '{name}' not found"}
            
            player = persistent_players[name]
            
            # Update role if provided
            role_val = params.get('role')
            if role_val:
                try:
                    player.role = PlayerRole(role_val)
                except ValueError:
                    return {'status': 'error', 'message': f"Invalid role: {role_val}"}
            
            # Update managed_groups if provided
            managed_groups = params.get('managed_groups')
            if managed_groups is not None:
                player.managed_groups = managed_groups
            
            # Update password if provided
            password = params.get('password')
            if password:
                player.password = password
            
            # Update attributes
            attributes = params.get('attributes', {})
            player.attributes.update(attributes)
            
            return {'status': 'success', 'message': f"Player '{name}' updated"}

        elif action == 'remove_persistent_player':
            name = params.get('name')
            if not name or name not in persistent_players:
                return {'status': 'error', 'message': f"Player '{name}' not found"}
            
            del persistent_players[name]
            return {'status': 'success', 'message': f"Player '{name}' removed"}

        elif action == 'create_game':
            game_id = str(uuid.uuid4())
            # Ensure name is in params so it's part of attributes
            game = Game(**params)
            games[game_id] = game
            
            # If group_id is provided, add game to group
            group_id = params.get('group_id')
            if group_id:
                group = None
                for g in groups.values():
                    if g.ID == group_id:
                        group = g
                        break
                if group:
                    group.add_game(game)
                
            return {'status': 'success', 'data': {'game_id': game_id, 'name': game.name}}

        elif action == 'create_group':
            group_name = params.get('name')
            if not group_name:
                return {'status': 'error', 'message': 'Missing group name'}
            if group_name in groups:
                return {'status': 'error', 'message': f'Group {group_name} already exists'}
            admin_password = params.get('admin_password')
            group = GameGroup(group_name, admin_password=admin_password, **params.get('attributes', {}))
            groups[group_name] = group
            return {'status': 'success', 'data': {'group_id': group.ID, 'name': group.name}}

        elif action == 'remove_group':
            group_id = params.get('group_id')
            if not group_id:
                return {'status': 'error', 'message': 'Missing group ID'}
            
            target_name = None
            for name, group in groups.items():
                if group.ID == group_id:
                    target_name = name
                    break
            
            if not target_name:
                return {'status': 'error', 'message': f'Group with ID {group_id} not found'}
            
            del groups[target_name]
            return {'status': 'success', 'message': f'Group {target_name} removed'}

        elif action == 'list_groups':
            group_list = {}
            for name, group in groups.items():
                group_list[group.ID] = {
                    'name': group.name,
                    'attributes': group.attributes,
                    'games_count': len(group.games)
                }
            return {'status': 'success', 'data': group_list}

        elif action == 'set_server_password':
            new_password = params.get('new_password')
            if server_passwords is not None:
                server_passwords['server'] = new_password
                return {'status': 'success', 'message': 'Server password updated'}
            return {'status': 'error', 'message': 'Server passwords dictionary not available'}

        elif action == 'set_admin_password':
            new_password = params.get('new_password')
            if server_passwords is not None:
                server_passwords['admin'] = new_password
                return {'status': 'success', 'message': 'Admin password updated'}
            return {'status': 'error', 'message': 'Server passwords dictionary not available'}

        elif action == 'set_group_admin_password':
            group_id = params.get('group_id')
            new_password = params.get('new_password')
            group = None
            for g in groups.values():
                if g.ID == group_id:
                    group = g
                    break
            if not group:
                return {'status': 'error', 'message': f'Group with ID {group_id} not found'}
            group.admin_password = new_password
            return {'status': 'success', 'message': f'Admin password for group {group.name} updated'}

        elif action == 'list_group_games':
            group_id = params.get('group_id')
            include_finished = params.get('include_finished', False)
            group = None
            for g in groups.values():
                if g.ID == group_id:
                    group = g
                    break
            if not group:
                return {'status': 'error', 'message': f'Group with ID {group_id} not found'}
            # We need to find the GIDs for the games in the group
            group_games = {}
            for gid, g in games.items():
                if g in group.games and (include_finished or g.state != GameState.FINISHED):
                    group_games[gid] = {
                        'name': g.name,
                        'state': g.state,
                        'attributes': g.attributes,
                        'players_count': len(g.players),
                        'max_players': g.max_players,
                        'observers_count': len(g.observers),
                        'max_observers': g.max_observers,
                        'custom_state': g.custom_state
                    }
            return {'status': 'success', 'data': group_games}
        
        elif action == 'get_group_info':
            group_id = params.get('group_id')
            group = None
            for g in groups.values():
                if g.ID == group_id:
                    group = g
                    break
            if not group:
                return {'status': 'error', 'message': f'Group with ID {group_id} not found'}
            return {
                'status': 'success', 
                'data': {
                    'name': group.name,
                    'attributes': group.attributes,
                    'games_count': len(group.games)
                }
            }

        elif action == 'list_games':
            include_finished = params.get('include_finished', False)
            game_list = {}
            for gid, g in games.items():
                if include_finished or g.state != GameState.FINISHED:
                    game_list[gid] = {
                        'name': g.name,
                        'state': g.state,
                        'attributes': g.attributes,
                        'players_count': len(g.players),
                        'max_players': g.max_players,
                        'observers_count': len(g.observers),
                        'max_observers': g.max_observers,
                        'custom_state': g.custom_state
                    }
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
                groups.clear()
            threading.Thread(target=delayed_restart).start()
            return result
        
        elif action == 'get_server_info':
            import time
            server_info = params.get('__server_info__', {})
            
            uptime = 0
            if server_passwords is not None:
                start_time = server_passwords.get('start_time')
                if start_time:
                    uptime = time.time() - start_time
            
            cert_expiration = None
            if use_tls and certfile:
                cert_expiration = get_cert_expiration(certfile)
            
            # Check if logging is active
            logger_instance = logging.getLogger("GameServer")
            logging_active = logger_instance.getEffectiveLevel() <= logging.INFO
            
            # Persistent players creation active
            persistent_players_active = True
            if server_passwords is not None:
                persistent_players_active = server_passwords.get('persistent_players_enabled', True)
            
            # Number of clients connected - we can estimate this by active threads
            # but more accurately, we could track it. For now, let's use threading.active_count() - 2 
            # (main thread + discovery thread). This is not perfect if other threads exist.
            # However, GameServer runs in a separate process, so it should be relatively accurate.
            connected_clients = threading.active_count() - 2
            if connected_clients < 0:
                connected_clients = 0

            return {'status': 'success', 'data': {
                'name': server_info.get('name'),
                'host': server_info.get('host'),
                'port': server_info.get('port'),
                'unencrypted_port': server_info.get('unencrypted_port'),
                'use_tls': server_info.get('use_tls'),
                'tls_domain': server_info.get('tls_domain'),
                'tls_self_signed': server_info.get('tls_self_signed'),
                'logging_host': server_info.get('logging_host'),
                'logging_port': server_info.get('logging_port'),
                'hidden': server_info.get('hidden'),
                'uptime': uptime,
                'cert_expiration': cert_expiration,
                'logging_active': logging_active,
                'persistent_players_active': persistent_players_active,
                'connected_clients': connected_clients
            }}
        
        elif action == 'set_logging_for_server':
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
            player_map = {}
            
            # First, list all currently connected players in games
            for gid, game in games.items():
                game_name = game.name or 'Unknown'
                for player in game.players:
                    is_persistent = persistent_players is not None and player.name in persistent_players
                    
                    if player.ID not in player_map:
                        player_map[player.ID] = {
                            'name': player.name,
                            'attributes': player.attributes, # Note: This takes attributes from the first game found
                            'games': {},
                            'connected': True,
                            'is_persistent': is_persistent
                        }
                    
                    player_map[player.ID]['games'][gid] = game_name
                    player_map[player.ID]['connected'] = True

            # Then, add persistent players who are NOT connected
            if persistent_players:
                for name, p_player in persistent_players.items():
                    if p_player.ID not in player_map:
                        player_map[p_player.ID] = {
                            'name': p_player.name,
                            'attributes': p_player.attributes,
                            'games': {},
                            'connected': False,
                            'is_persistent': True
                        }
                        
            return {'status': 'success', 'data': player_map}


        # Game-specific actions
        game_id = params.get('game_id')
        if not game_id or game_id not in games:
            return {'status': 'error', 'type': 'GameNotFoundError', 'message': 'Game not found'}
        
        game = games[game_id]
        
        if action == 'add_player':
            player_data = params['player']
            player_name = player_data['name']
            persistent_player_password = params.get('persistent_player_password')
            
            # If the player is in persistent_players, we must authenticate
            if persistent_players is not None and player_name in persistent_players:
                p_player = persistent_players[player_name]
                if persistent_player_password != p_player.password:
                    raise AuthenticationError(f"Invalid password for persistent player '{player_name}'")
                # Use the persistent player object's properties
                # Combine persistent attributes with game-specific attributes provided in player_data
                combined_attributes = p_player.attributes.copy()
                combined_attributes.update(player_data.get('attributes', {}))
                player = Player(p_player.name, **combined_attributes)
                player._force_id(p_player.ID)
            else:
                player = Player(player_name, **player_data.get('attributes', {}))
                
            game_password = params.get('game_password')
            game.add_player(player, password=game_password)
            return {'status': 'success'}
        
        elif action == 'add_observer':
            observer_data = params['observer']
            observer_name = observer_data['name']
            persistent_player_password = params.get('persistent_player_password')
            
            # If the player is in persistent_players, we must authenticate
            if persistent_players is not None and observer_name in persistent_players:
                p_player = persistent_players[observer_name]
                if persistent_player_password != p_player.password:
                    raise AuthenticationError(f"Invalid password for persistent player '{observer_name}'")
                # Combine persistent attributes with observer-specific attributes
                combined_attributes = p_player.attributes.copy()
                combined_attributes.update(observer_data.get('attributes', {}))
                observer = Observer(p_player.name, **combined_attributes)
                observer._force_id(p_player.ID)
            else:
                observer = Observer(observer_name, **observer_data.get('attributes', {}))
                
            observer_password = params.get('observer_password')
            game.add_observer(observer, password=observer_password)
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
            return {'status': 'success', 'data': {'status': game.state, 'custom': game.custom_state, 'kicked_ids': list(game.kicked_ids)}}
        
        elif action == 'get_players':
            player_list = [{'id': p.ID, 'name': p.name, 'attributes': p.attributes} for p in game.players]
            return {'status': 'success', 'data': player_list}
        
        elif action == 'get_observers':
            observer_list = [{'id': o.ID, 'name': o.name, 'attributes': o.attributes} for o in game.observers]
            return {'status': 'success', 'data': observer_list}
        
        elif action == 'set_game_state':
            game.custom_state = params.get('state')
            return {'status': 'success'}
        
        elif action == 'kick_player':
            player_id = params.get('player_id')
            # Use the logger passed to the function or global one
            logger.info(f"Kicking player {player_id} from game {game_id}")
            group_id = params.get('group_id')
            if group_id:
                group = None
                for g in groups.values():
                    if g.ID == group_id:
                        group = g
                        break
                if not group or game not in group.games:
                     return {'status': 'error', 'message': f'Game {game_id} does not belong to group ID {group_id}'}
            
            logger.info(f"DEBUG: Before kick, players={[p.ID for p in game.players]}, kicked={game.kicked_ids}")
            game.remove_player(player_id)
            logger.info(f"DEBUG: After kick, players={[p.ID for p in game.players]}, kicked={game.kicked_ids}")
            return {'status': 'success'}
        
        elif action == 'kick_observer':
            observer_id = params.get('observer_id')
            group_id = params.get('group_id')
            if group_id:
                group = None
                for g in groups.values():
                    if g.ID == group_id:
                        group = g
                        break
                if not group or game not in group.games:
                     return {'status': 'error', 'message': f'Game {game_id} does not belong to group ID {group_id}'}
            game.remove_observer(observer_id)
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
    
    Args:
        host (str): Host to listen on.
        port (int): Port to listen on.
        password (str, optional): Server password.
        admin_password (str, optional): Admin password.
        use_tls (bool): Enable TLS encryption.
        tls_domain (str): Domain for self-signed cert.
        tls_cert (str, optional): Path to cert file.
        tls_key (str, optional): Path to key file.
        tls_self_signed (bool): Generate self-signed cert if missing.
        logging_host (str, optional): IPC logging host.
        logging_port (int, optional): IPC logging port.
        logger_name (str): Name for the logger.
        name (str, optional): Human-readable server name.
        unencrypted_port (int, optional): Port for unencrypted traffic if TLS is on.
        hidden (bool): Hide from discovery.
        persistence_type (str, optional): 'json' or 'sqlite'.
        persistence_path (str, optional): Path to persistence file.
    """
    def __init__(self, host='0.0.0.0', port=65432, password=None, admin_password=None, 
                 use_tls=False, tls_domain="localhost", tls_cert=None, tls_key=None, 
                 tls_self_signed=True, logging_host=None, logging_port=None, 
                 logger_name="GameServer", name=None, unencrypted_port=None, 
                 hidden=False, persistence_type=None, persistence_path=None):
        self.host = host
        self.port = port
        self.unencrypted_port = unencrypted_port
        self.password = password
        self.admin_password = admin_password
        self.use_tls = use_tls
        self.tls_domain = tls_domain
        self.tls_cert = tls_cert
        self.tls_key = tls_key
        self.tls_self_signed = tls_self_signed
        self.logging_host = logging_host
        self.logging_port = logging_port
        self.logger_name = logger_name
        self.name = name
        self.hidden = hidden
        self.persistence_type = persistence_type
        self.persistence_path = persistence_path
        self._server_process = None
        self._discovery_thread = None
        self._stop_discovery = threading.Event()
        self._hidden_event = None
        self._temp_certs = False

    def start(self):
        """Starts the game server and discovery service in separate processes/threads."""
        if self._server_process and self._server_process.is_alive():
            print("Server is already running.")
            return
        
        certfile, keyfile = (self.tls_cert, self.tls_key)
        self._temp_certs = False
        
        if self.use_tls:
            if self.tls_self_signed:
                print(f"Generating self-signed certificate for {self.tls_domain}...")
                certfile, keyfile = _generate_self_signed_cert(self.tls_domain)
                self._temp_certs = True
            elif not certfile or not keyfile:
                # If one is provided but not the other, and self_signed is False, it's an error
                if certfile or keyfile:
                    print("Error: Both tls_cert and tls_key must be provided if tls_self_signed is False.")
                    return
                # If neither is provided, fallback to self-signed but warn
                print(f"Warning: No certificate provided and tls_self_signed is False. Generating self-signed certificate anyway for {self.tls_domain}...")
                certfile, keyfile = _generate_self_signed_cert(self.tls_domain)
                self._temp_certs = True
            else:
                if not os.path.exists(certfile) or not os.path.exists(keyfile):
                    print(f"Error: Certificate file {certfile} or key file {keyfile} not found.")
                    return
                
                # Auto-detect chain file
                # If cert is 'cert.pem', looks for 'chain.pem'
                # If cert is 'ECC-cert.pem', looks for 'ECC-chain.pem'
                # If cert is 'RSA-cert.pem', looks for 'RSA-chain.pem'
                cert_dir = os.path.dirname(os.path.abspath(certfile))
                cert_name = os.path.basename(certfile)
                if "-cert.pem" in cert_name:
                    chain_name = cert_name.replace("-cert.pem", "-chain.pem")
                elif cert_name == "cert.pem":
                    chain_name = "chain.pem"
                else:
                    chain_name = None
                
                if chain_name:
                    chain_path = os.path.join(cert_dir, chain_name)
                    if os.path.exists(chain_path):
                        print(f"Found matching chain file: {chain_name}. Creating full chain...")
                        try:
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".pem", prefix="multiplayer_fullchain_") as tmp_fullchain:
                                with open(certfile, 'rb') as f_cert:
                                    tmp_fullchain.write(f_cert.read())
                                if not tmp_fullchain.tell() == 0: # Ensure newline between certs if needed
                                    tmp_fullchain.write(b"\n")
                                with open(chain_path, 'rb') as f_chain:
                                    tmp_fullchain.write(f_chain.read())
                                certfile = tmp_fullchain.name
                        except Exception as e:
                            print(f"Warning: Failed to create temporary full chain file: {e}. Using original certificate.")

        # Use 'spawn' start method to avoid DeprecationWarning and potential deadlocks when forking from a multi-threaded process.
        ctx = get_context('spawn')
        self._hidden_event = ctx.Event()
        if self.hidden:
            self._hidden_event.set()
            
        self._server_process = ctx.Process(target=_run_server_process, args=(self.host, self.port, self.password, self.admin_password, self.use_tls, certfile, keyfile, self.logging_host, self.logging_port, self.logger_name, self.name, True, self.unencrypted_port, self.hidden, self._hidden_event, self.tls_domain, self.tls_self_signed, self.persistence_type, self.persistence_path))
        self._server_process.daemon = True
        self._server_process.start()
        self._stop_discovery.clear()
        self._discovery_thread = threading.Thread(target=self._run_discovery_service)
        self._discovery_thread.daemon = True
        self._discovery_thread.start()
        start_msg = f"Server started on {self.host}:{self.port} with PID {self._server_process.pid}"
        if self.name:
            start_msg += f" (Name: {self.name})"
        print(start_msg)
        if self.use_tls:
            print("TLS encryption is enabled.")
            if self.unencrypted_port:
                print(f"Unencrypted connections allowed on port {self.unencrypted_port}")
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
            
            # Allow broadcasting and multicast
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
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
                        # Check if hidden via shared event
                        if self._hidden_event and self._hidden_event.is_set():
                            continue
                        
                        logger = logging.getLogger(self.logger_name)
                        logger.info(f"Discovery request from {addr}, sending response...")
                        response_ip = self._get_lan_ip()
                        response_port = self.port
                        server_name = (self.name or "").encode('utf-8')
                        message = struct.pack(RESPONSE_MESSAGE_FORMAT, response_ip.encode('utf-8'), response_port, server_name)
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
  
