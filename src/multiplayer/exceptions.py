"""
Custom exceptions for the multiplayer module.
"""

class MultiplayerError(Exception):
    """Base class for exceptions in this module."""
    pass

class GameLogicError(MultiplayerError):
    """Raised for errors in game logic (e.g., starting a game with no players)."""
    pass

class PlayerLimitReachedError(GameLogicError):
    """Raised when trying to add a player to a full game."""
    pass

class GameNotFoundError(MultiplayerError):
    """Raised when a game_id is not found on the server."""
    pass

class NetworkError(MultiplayerError):
    """Base class for network-related errors."""
    pass

class ConnectionError(NetworkError):
    """Raised for errors connecting to the server."""
    pass

class ServerError(NetworkError):
    """Raised when the server reports a generic internal error."""
    pass

class AuthenticationError(NetworkError):
    """Raised for password authentication failures."""
    pass
