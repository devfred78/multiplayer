"""Multiplayer package initialization."""
from enum import Enum

class PlayerRole(Enum):
    """Enumeration for player account roles."""
    PLAYER = "player"
    GROUP_ADMIN = "group_admin"
    SERVER_ADMIN = "server_admin"

class GameState(Enum):
    """Enumeration for the current status of a game."""
    PENDING = "pending"
    PAUSING = "pausing"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"

class ParameterFamily(Enum):
    """Enumeration for optional parameter families."""
    STATIC = "static"
    DYNAMIC = "dynamic"

class SaveFormat(Enum):
    """Enumeration for the supported persistence formats of a save file."""
    JSON = "json"
    SQLITE = "sqlite"
