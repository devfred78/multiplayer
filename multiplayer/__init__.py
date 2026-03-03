"""
This package provides classes for managing a multiplayer game, both locally and over a network.
"""
from .game import Game, Player, GameState
from .server import GameServer
from .client import GameClient, RemoteGame
