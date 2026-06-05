"""Custom exceptions for the multiplayer module."""

class MultiplayerError(Exception):
    """Base class for all multiplayer exceptions."""
    pass

class UserAlreadyExistsError(MultiplayerError):
    """Raised when a user with the same name already exists."""
    pass

class SaveError(MultiplayerError):
    """Raised when a save file is incompatible, corrupted or cannot be processed."""
    pass

class GroupNotFoundError(MultiplayerError):
    """Raised when a group ID is not found."""
    def __init__(self, group_id: str):
        self.group_id = group_id
        super().__init__(f"Group not found: {group_id}")

class PlayerNotFoundError(MultiplayerError):
    """Raised when a player ID is not found."""
    def __init__(self, player_id: str | None = None):
        self.player_id = player_id
        msg = f"Player not found: {player_id}" if player_id else "Player not found"
        super().__init__(msg)

class PlayerNotFoundInGameError(PlayerNotFoundError):
    """Raised when a player is not in the specified game."""
    def __init__(self, player_id: str | None = None):
        super().__init__(player_id)
        if player_id:
            self.args = (f"Player {player_id} not found in game",)
        else:
            self.args = ("Player not found in game",)

class PasswordError(MultiplayerError):
    """Raised when an incorrect password is provided."""
    pass

class GameIsFullError(MultiplayerError):
    """Raised when a game has reached its maximum capacity."""
    pass

class GameAlreadyStartedError(MultiplayerError):
    """Raised when trying to start a game that is already in progress."""
    pass

class GameIsFinishedError(MultiplayerError):
    """Raised when trying to modify a game that has ended."""
    pass

class GameNotStartedError(MultiplayerError):
    """Raised when an action requires the game to be started."""
    pass

class GameAlreadyPausedError(MultiplayerError):
    """Raised when trying to pause a game that is already paused."""
    pass

class GameNotPausedError(MultiplayerError):
    """Raised when trying to resume a game that is not paused."""
    pass

class GameNotTurnBasedError(MultiplayerError):
    """Raised when a turn-based action is attempted on a non-turn-based game."""
    pass

class GameNotFoundError(MultiplayerError):
    """Raised when a game ID is not found."""
    def __init__(self, game_id: str | None = None):
        self.game_id = game_id
        msg = f"Game not found: {game_id}" if game_id else "Game not found"
        super().__init__(msg)

class GameNotFoundInGroupError(GameNotFoundError):
    """Raised when a game is not found in a specific group."""
    def __init__(self, game_id: str | None = None):
        super().__init__(game_id)
        if game_id:
            self.args = (f"Game {game_id} not found in group",)
        else:
            self.args = ("Game not found in group",)
