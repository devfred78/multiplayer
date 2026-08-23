"""Persistence layer for the multiplayer library.

This module provides the :class:`Save` class, which is responsible for
serializing and restoring the core domain objects (``Player``, ``User``,
``Game`` and ``GameGroup``) to and from a save file. Two storage formats are
supported: a single JSON document or an SQLite database.

The objects are first stored in an in-memory buffer through the
:meth:`Save.save` method, and are only written to the underlying file when the
:meth:`Save.flush` method is explicitly called.
"""
import json
import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Union

from . import SaveFormat, PlayerRole, GameState
from .exceptions import SaveError
from .game import Player, User, Game, GameGroup

logger = logging.getLogger(__name__)

# Mapping between the public class names and the classes themselves. It defines
# the structure expected in any compatible save file.
_SUPPORTED_CLASSES: Dict[str, type] = {
    "Player": Player,
    "User": User,
    "Game": Game,
    "GameGroup": GameGroup,
}

# Name of the table used for the SQLite storage format.
_SQLITE_TABLE = "objects"
_SERVER_CONFIG_CLASS = "__server_config__"


def _player_to_dict(player: Player) -> Dict[str, Any]:
    """Serializes a Player instance into a JSON-compatible dictionary.

    Args:
        player (Player): The player instance to serialize.

    Returns:
        Dict[str, Any]: The serialized representation of the player.
    """
    return {
        "id": player.ID,
        "name": player.name,
        "static_state": player.static_state,
        "dynamic_state": player.dynamic_state,
    }


def _player_from_dict(data: Dict[str, Any]) -> Player:
    """Rebuilds a Player instance from its serialized dictionary.

    Args:
        data (Dict[str, Any]): The serialized representation of the player.

    Returns:
        Player: The reconstructed player instance.
    """
    player = Player.__new__(Player)
    player._id = data["id"]
    player.name = data["name"]
    player.static_state = data.get("static_state", {})
    player.dynamic_state = data.get("dynamic_state", {})
    return player


def _user_to_dict(user: User) -> Dict[str, Any]:
    """Serializes a User instance into a JSON-compatible dictionary.

    Args:
        user (User): The user instance to serialize.

    Returns:
        Dict[str, Any]: The serialized representation of the user.
    """
    return {
        "id": user.ID,
        "username": user.username,
        "hash": user.hash,
        "email": user.email,
        "role": user.role.value,
        "groups_id": list(user.groups_id),
        "player": _player_to_dict(user.player),
    }


def _user_from_dict(data: Dict[str, Any]) -> User:
    """Rebuilds a User instance from its serialized dictionary.

    Args:
        data (Dict[str, Any]): The serialized representation of the user.

    Returns:
        User: The reconstructed user instance.
    """
    user = User.__new__(User)
    user._id = data["id"]
    user._username = data["username"]
    user._hash = data["hash"]
    user.email = data.get("email", "")
    user.role = PlayerRole(data["role"])
    user._groups_id = list(data.get("groups_id", []))
    user._player = _player_from_dict(data["player"])
    User._existing_usernames.add(user._username)
    return user


def _game_to_dict(game: Game) -> Dict[str, Any]:
    """Serializes a Game instance into a JSON-compatible dictionary.

    Args:
        game (Game): The game instance to serialize.

    Returns:
        Dict[str, Any]: The serialized representation of the game.
    """
    return {
        "id": game.ID,
        "name": game.name,
        "max_players": game._max_players,
        "max_observers": game._max_observers,
        "hash": game.hash,
        "observer_hash": game.observer_hash,
        "turn_based": game.turn_based,
        "players": [_player_to_dict(p) for p in game.players],
        "observers": [_player_to_dict(p) for p in game.observers],
        "game_state": game.game_state.value,
        "static_state": game.static_state,
        "dynamic_state": game.dynamic_state,
    }


def _game_from_dict(data: Dict[str, Any]) -> Game:
    """Rebuilds a Game instance from its serialized dictionary.

    Args:
        data (Dict[str, Any]): The serialized representation of the game.

    Returns:
        Game: The reconstructed game instance.
    """
    game = Game.__new__(Game)
    game._id = data["id"]
    game.name = data.get("name")
    game._max_players = data.get("max_players")
    game._max_observers = data.get("max_observers")
    game._hash = data.get("hash")
    game._observer_hash = data.get("observer_hash")
    game._turn_based = data.get("turn_based", False)
    game._players = [_player_from_dict(p) for p in data.get("players", [])]
    game._observers = [_player_from_dict(p) for p in data.get("observers", [])]
    game._game_state = GameState(data["game_state"])
    game.static_state = data.get("static_state", {})
    game.dynamic_state = data.get("dynamic_state", {})
    return game


def _group_to_dict(group: GameGroup) -> Dict[str, Any]:
    """Serializes a GameGroup instance into a JSON-compatible dictionary.

    Args:
        group (GameGroup): The group instance to serialize.

    Returns:
        Dict[str, Any]: The serialized representation of the group.
    """
    return {
        "id": group.ID,
        "name": group.name,
        "hash": group.hash,
        "games": [_game_to_dict(g) for g in group.games],
        "parameters": group.parameters,
    }


def _group_from_dict(data: Dict[str, Any]) -> GameGroup:
    """Rebuilds a GameGroup instance from its serialized dictionary.

    Args:
        data (Dict[str, Any]): The serialized representation of the group.

    Returns:
        GameGroup: The reconstructed group instance.
    """
    group = GameGroup.__new__(GameGroup)
    group._id = data["id"]
    group.name = data["name"]
    # ``hash`` is optional for backward compatibility with older save files.
    group._hash = data.get("hash")
    group._games = [_game_from_dict(g) for g in data.get("games", [])]
    group.parameters = data.get("parameters", {})
    return group


# Mapping between a class name and the pair of (serializer, deserializer).
_SERIALIZERS = {
    "Player": (_player_to_dict, _player_from_dict),
    "User": (_user_to_dict, _user_from_dict),
    "Game": (_game_to_dict, _game_from_dict),
    "GameGroup": (_group_to_dict, _group_from_dict),
}


class Save:
    """Represents a save file for the multiplayer domain objects.

    An instance of this class maps an in-memory buffer of serialized objects to
    a persistent storage file (either a JSON document or an SQLite database).
    Objects are added or updated through :meth:`save`, retrieved by class
    through :meth:`load`, and only written to disk when :meth:`flush` is called.

    Attributes:
        file_path (Path): The path of the underlying save file.
        save_format (SaveFormat): The storage format used by the save file.
    """

    def __init__(self, file_path: Path, save_format: Union[SaveFormat, str]):
        """Initializes a save file handler.

        If the file does not exist, it is created with an empty structure. If it
        already exists, its structure is validated and its content is loaded
        into memory.

        Args:
            file_path (Path): The path of the save file.
            save_format (SaveFormat | str): The storage format, either a
                ``SaveFormat`` member or one of the strings ``"json"`` or
                ``"sqlite"``.

        Raises:
            SaveError: If the storage format is unknown, or if the existing file
                has an incompatible structure.
        """
        self.file_path: Path = Path(file_path)
        try:
            self.save_format: SaveFormat = (
                save_format if isinstance(save_format, SaveFormat) else SaveFormat(save_format)
            )
        except ValueError as exc:
            raise SaveError(f"Unknown save format: {save_format}") from exc

        self._data: Dict[str, Dict[str, Dict[str, Any]]] = {
            name: {} for name in _SUPPORTED_CLASSES
        }
        self._server_config: Dict[str, Any] = {}

        if self.file_path.exists():
            self._load_file()
        else:
            self.flush()

    @staticmethod
    def _resolve_class_name(target: Union[str, type]) -> str:
        """Resolves a class or class name into a supported class name.

        Args:
            target (str | type): A supported class or its name.

        Returns:
            str: The validated class name.

        Raises:
            SaveError: If the target does not match a supported class.
        """
        name = target if isinstance(target, str) else getattr(target, "__name__", None)
        if name not in _SUPPORTED_CLASSES:
            raise SaveError(f"Unsupported class: {target}")
        return name

    def _load_file(self) -> None:
        """Loads and validates the content of the existing save file.

        Raises:
            SaveError: If the file structure is incompatible or unreadable.
        """
        if self.save_format == SaveFormat.JSON:
            self._load_json()
        else:
            self._load_sqlite()

    def _load_json(self) -> None:
        """Loads the in-memory buffer from a JSON save file.

        Raises:
            SaveError: If the file is not a valid JSON document or does not match
                the expected structure.
        """
        try:
            with self.file_path.open("r", encoding="utf-8") as handle:
                content = json.load(handle)
        except (json.JSONDecodeError, OSError) as exc:
            logger.exception("Failed to read JSON save file.")
            raise SaveError(f"Cannot read save file: {self.file_path}") from exc

        expected = set(_SUPPORTED_CLASSES)
        if not isinstance(content, dict) or not expected.issubset(content) or set(content) - expected - {_SERVER_CONFIG_CLASS}:
            raise SaveError(f"Incompatible save file structure: {self.file_path}")

        for name in _SUPPORTED_CLASSES:
            section = content[name]
            if not isinstance(section, dict):
                raise SaveError(f"Incompatible save file structure: {self.file_path}")
            self._data[name] = dict(section)
        config = content.get(_SERVER_CONFIG_CLASS, {})
        if not isinstance(config, dict):
            raise SaveError(f"Incompatible save file structure: {self.file_path}")
        self._server_config = dict(config)

    def _load_sqlite(self) -> None:
        """Loads the in-memory buffer from an SQLite save file.

        Raises:
            SaveError: If the database does not contain the expected table or
                cannot be read.
        """
        connection = None
        try:
            connection = sqlite3.connect(self.file_path)
            cursor = connection.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (_SQLITE_TABLE,),
            )
            if cursor.fetchone() is None:
                raise SaveError(f"Incompatible save file structure: {self.file_path}")

            cursor.execute(f"SELECT class, id, data FROM {_SQLITE_TABLE}")
            for class_name, obj_id, raw in cursor.fetchall():
                if class_name not in _SUPPORTED_CLASSES and class_name != _SERVER_CONFIG_CLASS:
                    raise SaveError(f"Incompatible save file structure: {self.file_path}")
                data = json.loads(raw)
                if class_name == _SERVER_CONFIG_CLASS:
                    if not isinstance(data, dict):
                        raise SaveError(f"Incompatible save file structure: {self.file_path}")
                    self._server_config = data
                else:
                    self._data[class_name][obj_id] = data
        except sqlite3.DatabaseError as exc:
            logger.exception("Failed to read SQLite save file.")
            raise SaveError(f"Cannot read save file: {self.file_path}") from exc
        finally:
            if connection is not None:
                connection.close()

    def save(self, obj: Union[Player, User, Game, GameGroup]) -> None:
        """Saves or updates an object in the in-memory buffer.

        If an object with the same ID and class already exists, it is replaced.
        The change is not persisted until :meth:`flush` is called.

        Args:
            obj (Player | User | Game | GameGroup): The instance to save.

        Raises:
            SaveError: If the object is not an instance of a supported class.
        """
        name = self._resolve_class_name(type(obj))
        serializer = _SERIALIZERS[name][0]
        self._data[name][obj.ID] = serializer(obj)

    def load(self, target: Union[str, type]) -> List[Union[Player, User, Game, GameGroup]]:
        """Loads all stored instances of a given class.

        Args:
            target (str | type): The class or class name to load (one of
                ``Player``, ``User``, ``Game`` or ``GameGroup``).

        Returns:
            List: The list of reconstructed instances for the requested class.

        Raises:
            SaveError: If the target does not match a supported class.
        """
        name = self._resolve_class_name(target)
        deserializer = _SERIALIZERS[name][1]
        return [deserializer(data) for data in self._data[name].values()]

    def reset(self) -> None:
        """Clears the in-memory buffer and the underlying save file.

        The save file is rewritten with an empty but valid structure.
        """
        self._data = {name: {} for name in _SUPPORTED_CLASSES}
        self._server_config = {}
        self.flush()

    def save_server_config(self, config: Dict[str, Any]) -> None:
        """Stores the serializable server configuration in the save buffer."""
        self._server_config = dict(config)

    def load_server_config(self) -> Dict[str, Any]:
        """Returns the stored server configuration, or an empty mapping."""
        return dict(self._server_config)

    def flush(self) -> None:
        """Persists the in-memory buffer to the underlying save file.

        Raises:
            SaveError: If the data cannot be written to the file.
        """
        if self.save_format == SaveFormat.JSON:
            self._flush_json()
        else:
            self._flush_sqlite()

    def _flush_json(self) -> None:
        """Writes the in-memory buffer to a JSON save file.

        Raises:
            SaveError: If the data cannot be written.
        """
        try:
            content = dict(self._data)
            if self._server_config:
                content[_SERVER_CONFIG_CLASS] = self._server_config
            with self.file_path.open("w", encoding="utf-8") as handle:
                json.dump(content, handle, indent=2)
        except OSError as exc:
            logger.exception("Failed to write JSON save file.")
            raise SaveError(f"Cannot write save file: {self.file_path}") from exc

    def _flush_sqlite(self) -> None:
        """Writes the in-memory buffer to an SQLite save file.

        Raises:
            SaveError: If the data cannot be written.
        """
        connection = None
        try:
            connection = sqlite3.connect(self.file_path)
            cursor = connection.cursor()
            cursor.execute(
                f"CREATE TABLE IF NOT EXISTS {_SQLITE_TABLE} ("
                "class TEXT NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL, "
                "PRIMARY KEY (class, id))"
            )
            cursor.execute(f"DELETE FROM {_SQLITE_TABLE}")
            rows = [
                (name, obj_id, json.dumps(data))
                for name, section in self._data.items()
                for obj_id, data in section.items()
            ]
            if self._server_config:
                rows.append((_SERVER_CONFIG_CLASS, "server", json.dumps(self._server_config)))
            cursor.executemany(
                f"INSERT INTO {_SQLITE_TABLE} (class, id, data) VALUES (?, ?, ?)",
                rows,
            )
            connection.commit()
        except sqlite3.DatabaseError as exc:
            logger.exception("Failed to write SQLite save file.")
            raise SaveError(f"Cannot write save file: {self.file_path}") from exc
        finally:
            if connection is not None:
                connection.close()
