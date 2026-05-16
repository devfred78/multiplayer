import os
import json
import sqlite3
import logging
from abc import ABC, abstractmethod
from ..game import Game, GameGroup, PersistentPlayer, GameState, PlayerRole

class DataStore(ABC):
    @abstractmethod
    def load(self):
        """
        Loads data from the store. 
        
        Returns:
            tuple: (games, groups, persistent_players, server_config)
        """
        pass

    @abstractmethod
    def save(self, games, groups, persistent_players, server_config=None):
        """
        Saves data to the store.
        
        Args:
            games (dict): Dictionary of games.
            groups (dict): Dictionary of game groups.
            persistent_players (dict): Dictionary of persistent players.
            server_config (dict, optional): Dictionary of server settings.
        """
        pass

class MemoryDataStore(DataStore):
    """
    An in-memory data store that does not persist anything.
    """
    def load(self):
        return {}, {}, {}, {}

    def save(self, games, groups, persistent_players, server_config=None):
        pass

class JSONDataStore(DataStore):
    """
    A data store that persists data to a JSON file.
    
    Args:
        file_path (str): The path to the JSON file.
    """
    def __init__(self, file_path):
        self.file_path = file_path
        self.logger = logging.getLogger("GameServer")

    def load(self):
        if not os.path.exists(self.file_path):
            return {}, {}, {}, {}
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Reconstruct persistent players
            persistent_players = {}
            for name, p_data in data.get('persistent_players', {}).items():
                p = PersistentPlayer(
                    name=p_data['name'],
                    password=p_data['password'],
                    role=PlayerRole(p_data['role']),
                    managed_groups=p_data.get('managed_groups', [])
                )
                if 'attributes' in p_data:
                    p.attributes.update(p_data['attributes'])
                persistent_players[name] = p

            # Reconstruct games
            games = {}
            for gid, g_data in data.get('games', {}).items():
                # Extract basic params
                params = {
                    'name': g_data.get('name'),
                    'max_players': g_data.get('max_players'),
                    'max_observers': g_data.get('max_observers'),
                    'turn_based': g_data.get('turn_based', False),
                    'password': g_data.get('password'),
                    'observer_password': g_data.get('observer_password')
                }
                # Add extra attributes
                params.update(g_data.get('attributes', {}))
                
                game = Game(**params)
                game.state = GameState(g_data['state'])
                game.custom_state = g_data.get('custom_state')
                game.end_time = g_data.get('end_time')
                # Restore player names if available
                player_names = g_data.get('players', [])
                from ..game import Player
                for pname in player_names:
                    game.players.append(Player(pname))
                
                # Note: We don't restore active player connections/objects here 
                # as they are transient. But we could restore player lists if needed.
                # For now, we restore the game metadata and state.
                games[gid] = game

            # Reconstruct groups
            groups = {}
            for gname, grp_data in data.get('groups', {}).items():
                grp = GameGroup(name=gname, **grp_data.get('attributes', {}))
                # Restore associated games
                for gid in grp_data.get('game_ids', []):
                    if gid in games:
                        grp.add_game(games[gid])
                groups[gname] = grp
            
            server_config = data.get('server_config', {})
                
            return games, groups, persistent_players, server_config
        except Exception as e:
            self.logger.error(f"Failed to load data from JSON: {e}")
            return {}, {}, {}, {}

    def save(self, games, groups, persistent_players, server_config=None):
        from ..server import EnumEncoder
        data = {
            'persistent_players': {},
            'games': {},
            'groups': {},
            'server_config': server_config or {}
        }

        for name, p in persistent_players.items():
            data['persistent_players'][name] = {
                'name': p.name,
                'password': p.password,
                'role': p.role.value,
                'managed_groups': p.managed_groups,
                'attributes': p.attributes
            }

        for gid, g in games.items():
            data['games'][gid] = {
                'name': g.name,
                'state': g.state.value,
                'attributes': g.attributes,
                'max_players': g.max_players,
                'max_observers': g.max_observers,
                'turn_based': g.turn_based,
                'password': getattr(g, 'password', None),
                'observer_password': getattr(g, 'observer_password', None),
                'custom_state': g.custom_state,
                'end_time': getattr(g, 'end_time', None),
                'players': [p.name for p in g.players]
            }

        for gname, grp in groups.items():
            data['groups'][gname] = {
                'name': grp.name,
                'attributes': grp.attributes,
                'game_ids': [g.ID for g in grp.games]
            }

        try:
            temp_file = self.file_path + ".tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, cls=EnumEncoder, indent=2)
            os.replace(temp_file, self.file_path)
        except Exception as e:
            self.logger.error(f"Failed to save data to JSON: {e}")

class SQLiteDataStore(DataStore):
    """
    A data store that persists data to a SQLite database.
    
    Args:
        db_path (str): The path to the SQLite database file.
    """
    def __init__(self, db_path):
        self.db_path = db_path
        self.logger = logging.getLogger("GameServer")
        self._init_db()

    def _init_db(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS persistent_players 
                              (name TEXT PRIMARY KEY, password TEXT, role TEXT, managed_groups TEXT, attributes TEXT)''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS games 
                              (id TEXT PRIMARY KEY, name TEXT, state TEXT, attributes TEXT, max_players INTEGER, 
                               max_observers INTEGER, turn_based INTEGER, password TEXT, observer_password TEXT, custom_state TEXT, end_time TEXT, players TEXT)''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS groups 
                              (name TEXT PRIMARY KEY, attributes TEXT, game_ids TEXT)''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS server_config
                              (key TEXT PRIMARY KEY, value TEXT)''')
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"Failed to initialize SQLite database at {self.db_path}: {e}")
            raise

    def load(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Load persistent players
            persistent_players = {}
            cursor.execute("SELECT name, password, role, managed_groups, attributes FROM persistent_players")
            for row in cursor.fetchall():
                name, password, role_val, managed_groups_json, attributes_json = row
                p = PersistentPlayer(
                    name=name,
                    password=password,
                    role=PlayerRole(role_val),
                    managed_groups=json.loads(managed_groups_json)
                )
                p.attributes.update(json.loads(attributes_json))
                persistent_players[name] = p

            # Load games
            games = {}
            cursor.execute("SELECT id, name, state, attributes, max_players, max_observers, turn_based, password, observer_password, custom_state, end_time, players FROM games")
            for row in cursor.fetchall():
                gid, name, state, attributes_json, max_players, max_observers, turn_based, password, observer_password, custom_state_json, end_time, players_json = row
                params = {
                    'name': name,
                    'max_players': max_players,
                    'max_observers': max_observers,
                    'turn_based': bool(turn_based),
                    'password': password,
                    'observer_password': observer_password
                }
                params.update(json.loads(attributes_json))
                game = Game(**params)
                game.state = GameState(state)
                game.custom_state = json.loads(custom_state_json) if custom_state_json else None
                game.end_time = end_time
                if players_json:
                    from ..game import Player
                    player_names = json.loads(players_json)
                    for pname in player_names:
                        game.players.append(Player(pname))
                games[gid] = game

            # Load groups
            groups = {}
            cursor.execute("SELECT name, attributes, game_ids FROM groups")
            for row in cursor.fetchall():
                gname, attributes_json, game_ids_json = row
                grp = GameGroup(name=gname, **json.loads(attributes_json))
                game_ids = json.loads(game_ids_json)
                for gid in game_ids:
                    if gid in games:
                        grp.add_game(games[gid])
                groups[gname] = grp

            # Load server config
            server_config = {}
            cursor.execute("SELECT key, value FROM server_config")
            for key, value in cursor.fetchall():
                server_config[key] = json.loads(value)

            conn.close()
            return games, groups, persistent_players, server_config
        except Exception as e:
            self.logger.error(f"Failed to load data from SQLite: {e}")
            return {}, {}, {}, {}

    def save(self, games, groups, persistent_players, server_config=None):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Clear old data (simple approach for now)
            cursor.execute("DELETE FROM persistent_players")
            cursor.execute("DELETE FROM games")
            cursor.execute("DELETE FROM groups")
            cursor.execute("DELETE FROM server_config")

            # Save persistent players
            for name, p in persistent_players.items():
                cursor.execute("INSERT INTO persistent_players VALUES (?, ?, ?, ?, ?)",
                               (name, p.password, p.role.value, json.dumps(p.managed_groups), json.dumps(p.attributes)))

            # Save games
            for gid, g in games.items():
                player_names = [p.name for p in g.players]
                cursor.execute("INSERT INTO games VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                               (gid, g.name, g.state.value, json.dumps(g.attributes), g.max_players, 
                                g.max_observers, 1 if g.turn_based else 0, getattr(g, 'password', None), 
                                getattr(g, 'observer_password', None), json.dumps(g.custom_state), getattr(g, 'end_time', None),
                                json.dumps(player_names)))

            # Save groups
            for gname, grp in groups.items():
                game_ids = [g.ID for g in grp.games]
                cursor.execute("INSERT INTO groups VALUES (?, ?, ?)",
                               (gname, json.dumps(grp.attributes), json.dumps(game_ids)))

            # Save server config
            if server_config:
                for key, value in server_config.items():
                    cursor.execute("INSERT INTO server_config VALUES (?, ?)",
                                   (key, json.dumps(value)))

            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"Failed to save data to SQLite: {e}")

def create_datastore(persistence_type, path=None):
    if persistence_type == 'json':
        return JSONDataStore(path or "server_data.json")
    elif persistence_type == 'sqlite':
        return SQLiteDataStore(path or "server_data.db")
    else:
        return MemoryDataStore()
