"""
This package provides classes for managing a multiplayer game, both locally and over a network.
"""
from .game import Game, Player, Observer, GameState, GameGroup
from .server import GameServer
from .client import GameClient, RemoteGame, ServerAdmin, GroupAdmin

from .utils import (
    suggest_game_name,
    suggest_player_name,
    get_available_categories,
    register_name_category,
    unregister_name_category,
)
from .exceptions import (
    MultiplayerError,
    GameLogicError,
    PlayerLimitReachedError,
    ObserverLimitReachedError,
    GameNotFoundError,
    NetworkError,
    ConnectionError,
    ServerError,
    AuthenticationError,
)

__all__ = [
    'Game',
    'Player',
    'Observer',
    'GameState',
    'GameGroup',
    'GameServer',
    'GameClient',
    'RemoteGame',
    'ServerAdmin',
    'GroupAdmin',
    'suggest_game_name',
    'suggest_player_name',
    'get_available_categories',
    'register_name_category',
    'unregister_name_category',
    'MultiplayerError',
    'GameLogicError',
    'PlayerLimitReachedError',
    'ObserverLimitReachedError',
    'GameNotFoundError',
    'NetworkError',
    'ConnectionError',
    'ServerError',
    'AuthenticationError',
]
