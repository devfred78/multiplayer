"""
This package provides classes for managing a multiplayer game, both locally and over a network.
"""
from .game import Game, Player, GameState
from .server import GameServer
from .client import GameClient, RemoteGame
from .exceptions import (
    MultiplayerError,
    GameLogicError,
    PlayerLimitReachedError,
    GameNotFoundError,
    NetworkError,
    ConnectionError,
    ServerError,
)
