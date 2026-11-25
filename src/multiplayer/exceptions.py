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

class UserNotFoundError(MultiplayerError):
    """Raised when a user account (or its ID) is not found."""
    def __init__(self, user_id: str | None = None):
        self.user_id = user_id
        msg = f"User not found: {user_id}" if user_id else "User not found"
        super().__init__(msg)

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

class NotEnoughPlayersError(MultiplayerError):
    """Raised when trying to start a game that has fewer players than required."""
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

class GameHasPlayersError(MultiplayerError):
    """Raised when an operation requires a game without any player.

    Observers are not taken into account.
    """
    def __init__(self, game_id: str | None = None):
        self.game_id = game_id
        super().__init__(f"Game {game_id} already has players")

class PlayerFactoryNotDefinedError(MultiplayerError):
    """Raised when the player factory of a game without factory is used."""
    def __init__(self, game_id: str | None = None):
        self.game_id = game_id
        super().__init__(f"Game {game_id} has no player factory")

class GameFactoryNotDefinedError(MultiplayerError):
    """Raised when the game factory of a group without factory is used."""
    def __init__(self, group_id: str | None = None):
        self.group_id = group_id
        super().__init__(f"Group {group_id} has no game factory")

class GroupHasGamesError(MultiplayerError):
    """Raised when an operation requires a group without any game."""
    def __init__(self, group_id: str | None = None):
        self.group_id = group_id
        super().__init__(f"Group {group_id} already has games")

class PlayerFactoryTemplateNotFoundError(MultiplayerError):
    """Raised when a player factory template ID is not found."""
    def __init__(self, template_id: str | None = None):
        self.template_id = template_id
        msg = (
            f"Player factory template not found: {template_id}"
            if template_id
            else "Player factory template not found"
        )
        super().__init__(msg)

class UnsupportedFeatureError(MultiplayerError):
    """Raised when a protocol feature not offered by the server is used."""
    def __init__(self, feature: str, revision: str | None = None):
        self.feature = feature
        self.revision = revision
        super().__init__(
            f"Feature '{feature}' is not supported by the server (revision {revision})"
        )

class OptionError(MultiplayerError):
    """Common base class of the errors related to player customization options."""
    pass

class OptionValueAlreadyGivenError(OptionError):
    """Raised when a unique option value is already carried by another player.

    Attributes:
        option_id (str): The ID of the option concerned.
        value (Any): The value already used.
    """
    def __init__(self, option_id: str, value: object):
        self.option_id = option_id
        self.value = value
        super().__init__(f"Value {value!r} of option {option_id} is already given")

class LackingOptionError(OptionError):
    """Raised when no value is available for a mandatory option.

    Attributes:
        option_id (str): The ID of the option concerned.
        reason (str): ``"ABSENT_FROM_PLAYER"``, ``"ABSENT_FROM_GAME"`` or
            ``"NO_AVAILABLE_VALUE"``.
    """
    def __init__(self, option_id: str, reason: str):
        self.option_id = option_id
        self.reason = reason
        super().__init__(f"No value for option {option_id} ({reason})")

class InvalidOptionValueError(OptionError, ValueError):
    """Raised when an option value is unknown, of an incompatible type or invalid.

    Attributes:
        option_id (str): The ID of the option concerned (or the key provided).
        value (Any): The offending value.
        reason (str): ``"UNKNOWN_OPTION"``, ``"INCOMPATIBLE_TYPE"`` or
            ``"INVALID_VALUE"``.
    """
    def __init__(self, option_id: str, value: object, reason: str):
        self.option_id = option_id
        self.value = value
        self.reason = reason
        super().__init__(f"Invalid value {value!r} for option {option_id} ({reason})")

class OptionAlreadyExistsError(OptionError):
    """Raised when an identical or similar option is already present."""
    def __init__(self, option_id: str | None = None):
        self.option_id = option_id
        super().__init__(f"Option already exists: {option_id}")
