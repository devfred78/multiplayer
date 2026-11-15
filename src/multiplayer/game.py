"""Game logic for the multiplayer library."""
import datetime
import math
import random
import re
import threading
import uuid
import weakref
from typing import List, Tuple, Dict, Any, Iterable
import bcrypt
from . import UserRole, GameState, ParameterFamily, OptionType
from .exceptions import (
    GameHasPlayersError,
    InvalidOptionValueError,
    LackingOptionError,
    OptionAlreadyExistsError,
    OptionValueAlreadyGivenError,
    PlayerFactoryNotDefinedError,
    UserAlreadyExistsError,
    PlayerNotFoundError,
    PlayerNotFoundInGameError,
    PasswordError,
    GameIsFullError,
    GameAlreadyStartedError,
    NotEnoughPlayersError,
    GameIsFinishedError,
    GameNotStartedError,
    GameAlreadyPausedError,
    GameNotPausedError,
    GameNotTurnBasedError,
    GameNotFoundError,
    GameNotFoundInGroupError,
)

# Pattern of the runtime constants usable in the default value of an option.
_CONSTANT_PATTERN = re.compile(r"%%([A-Z_]+)%%")
# Runtime constants computed by the library itself.
_LIBRARY_CONSTANTS = frozenset({"CURRENT_TIME", "RANDOM_NUMBER", "RANDOM_CHOICE"})
# Runtime constants provided by the player factory.
_FACTORY_CONSTANTS = frozenset({"GAMENAME"})
# Runtime constants provided by the caller through a context dictionary.
_CONTEXT_CONSTANTS = frozenset({"USERNAME", "SERVERNAME", "CLIENTADDRESS", "SERVERADDRESS"})
_KNOWN_CONSTANTS = _LIBRARY_CONSTANTS | _FACTORY_CONSTANTS | _CONTEXT_CONSTANTS
# Tolerance used to compare the values of decimal RANGE options.
_REL_TOL = 1e-9
_ABS_TOL = 1e-9
# Maximum number of possible values enumerated for a random draw.
_MAX_ENUMERATED_VALUES = 10000
# Attributes of a Player object that an option can be associated with.
_PLAYER_ATTRIBUTES = ("name",)
# Representations of the ``player_attribute`` parameter of an option.
_TARGET_ATTRIBUTE = "ATTRIBUTE"
_TARGET_BY_FAMILY = {ParameterFamily.STATIC: "STATIC", ParameterFamily.DYNAMIC: "DYNAMIC"}
_FAMILY_BY_TARGET = {target: family for family, target in _TARGET_BY_FAMILY.items()}


def _is_number(value: Any) -> bool:
    """Tells whether a value is an ``int`` or a ``float`` (booleans excluded).

    Args:
        value (Any): The value to inspect.

    Returns:
        bool: True if the value is a number.
    """
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _parse_number(value: Any) -> int | float:
    """Converts a number, or a string representing a number, into a number.

    Args:
        value (Any): The value to convert.

    Returns:
        int | float: The number, as an ``int`` when it is written as an
        integer, as a ``float`` otherwise.

    Raises:
        TypeError: If the value is neither a finite number nor a string
            representing one.
    """
    if _is_number(value):
        number = value
    elif isinstance(value, str):
        text = value.strip()
        try:
            number = int(text)
        except ValueError:
            try:
                number = float(text)
            except ValueError as exc:
                raise TypeError(f"Value {value!r} is not a number.") from exc
    else:
        raise TypeError(f"Value {value!r} is not a number.")
    if isinstance(number, float) and not math.isfinite(number):
        raise TypeError(f"Value {value!r} is not a finite number.")
    return number


def _check_player_attribute(option: "Option", player_attribute: Any) -> None:
    """Checks the ``player_attribute`` parameter associated with an option.

    Args:
        option (Option): The option concerned.
        player_attribute (Any): The value to check.

    Raises:
        TypeError: If the value is neither a string nor a ``ParameterFamily``
            member, or if it is ``"name"`` and the option is neither a TEXT
            nor a LIST option.
        ValueError: If the value is a string other than ``"name"``.
    """
    if isinstance(player_attribute, ParameterFamily):
        return
    if not isinstance(player_attribute, str):
        raise TypeError(
            f"player_attribute must be a string or a ParameterFamily member, "
            f"got {player_attribute!r}."
        )
    if player_attribute not in _PLAYER_ATTRIBUTES:
        raise ValueError(f"Unsupported player attribute: {player_attribute!r}.")
    if option.option_type not in (OptionType.TEXT, OptionType.LIST):
        raise TypeError(
            f"Only TEXT and LIST options can be associated with the player attribute "
            f"{player_attribute!r} (option type: {option.option_type.name})."
        )


class Option:
    """Represents a player customization option.

    An option is a parameter whose value is chosen when a player is created by
    means of a player factory. Its type (see :class:`OptionType`) determines
    the accepted values and the parameters that are relevant to it.

    The default value can contain runtime constants (``%%CONSTANT%%``), which
    are kept unevaluated in the option and evaluated by :meth:`evaluate_default`.

    Attributes:
        name (str): The name of the option.
        description (str): The description of the option.
    """

    def __init__(
        self,
        name: str,
        option_type: OptionType,
        description: str = "",
        default: bool | int | float | str | None = None,
        min_value: float | int | None = None,
        max_value: float | int | None = None,
        step: float | int = 1,
        choices: List[str] | Tuple[str, ...] = (),
    ):
        """Initializes a new option.

        Args:
            name (str): The name of the option.
            option_type (OptionType): The type of the option.
            description (str, optional): The description of the option.
                Defaults to "".
            default (bool | int | float | str, optional): The default value,
                possibly containing runtime constants. ``None`` means "first
                available value". Defaults to None.
            min_value (float | int, optional): The minimum value (RANGE
                options). ``None`` means no minimum. Defaults to None.
            max_value (float | int, optional): The maximum value (RANGE
                options). ``None`` means no maximum. Defaults to None.
            step (float | int, optional): The increment between two possible
                values (RANGE options). Defaults to 1.
            choices (list[str] | tuple[str, ...], optional): The possible
                choices (LIST options). Defaults to an empty tuple.

        Raises:
            TypeError: If a parameter has an unexpected type, if the default
                value is not accepted for the type of the option, or if a
                runtime constant is misused.
            ValueError: If the parameters are inconsistent, if the default
                value is not a possible value of the option, or if a runtime
                constant is unknown.
        """
        if not isinstance(option_type, OptionType):
            raise TypeError(f"option_type must be an OptionType member, got {option_type!r}.")
        if not isinstance(name, str):
            raise TypeError(f"The name of an option must be a string, got {name!r}.")
        if not isinstance(description, str):
            raise TypeError(f"The description of an option must be a string, got {description!r}.")
        for label, bound in (("min_value", min_value), ("max_value", max_value)):
            if bound is not None and not _is_number(bound):
                raise TypeError(f"{label} must be a number or None, got {bound!r}.")
        if not _is_number(step):
            raise TypeError(f"step must be a number, got {step!r}.")
        if min_value is not None and max_value is not None and min_value > max_value:
            raise ValueError(
                f"min_value ({min_value!r}) is greater than max_value ({max_value!r})."
            )
        if step <= 0:
            raise ValueError(f"step must be strictly positive, got {step!r}.")
        if not isinstance(choices, (list, tuple)):
            raise TypeError(f"choices must be a list or a tuple, got {choices!r}.")
        for choice in choices:
            if not isinstance(choice, str):
                raise TypeError(f"Every choice must be a string, got {choice!r}.")
        if len(set(choices)) != len(choices):
            raise ValueError(f"choices contains duplicates: {list(choices)!r}.")
        if option_type == OptionType.LIST and not choices:
            raise ValueError("A LIST option requires at least one choice.")

        self._id: str = str(uuid.uuid4())
        self.name: str = name
        self.description: str = description
        self._type: OptionType = option_type
        self._choices: Tuple[str, ...] = tuple(choices)
        self._step: float | int = step
        self._has_constants: bool = (
            isinstance(default, str) and _CONSTANT_PATTERN.search(default) is not None
        )

        if option_type == OptionType.RANGE:
            # A string default is converted according to the nature of the
            # option, so only a numeric default takes part in determining it.
            if default is not None and not self._has_constants and not isinstance(default, str):
                numeric_default = _parse_number(default)
            else:
                numeric_default = None
            self._integer: bool = all(
                isinstance(value, int)
                for value in (step, min_value, max_value, numeric_default)
                if value is not None
            )
            convert = int if self._integer else float
            self._min: float | int | None = None if min_value is None else convert(min_value)
            self._max: float | int | None = None if max_value is None else convert(max_value)
        else:
            self._integer = False
            self._min = min_value
            self._max = max_value

        if self._has_constants:
            self._check_constants(default)  # type: ignore[arg-type]
            self._default: bool | int | float | str | None = default
        elif default is None:
            self._default = None
        else:
            value = self._convert(default)
            self._validate(value)
            self._default = value

    # ------------------------------------------------------------------ #
    # Read-only attributes
    # ------------------------------------------------------------------ #
    @property
    def ID(self) -> str:
        """The unique identifier of the option.

        Returns:
            str: The UUID of the option.
        """
        return self._id

    @property
    def option_type(self) -> OptionType:
        """The type of the option.

        Returns:
            OptionType: The type of the option.
        """
        return self._type

    @property
    def choices(self) -> Tuple[str, ...]:
        """The possible choices of the option (LIST options).

        Returns:
            tuple[str, ...]: The possible choices.
        """
        return self._choices

    @property
    def min_value(self) -> float | int | None:
        """The minimum value of the option (RANGE options).

        Returns:
            float | int | None: The minimum value, or None if there is none.
        """
        return self._min

    @property
    def max_value(self) -> float | int | None:
        """The maximum value of the option (RANGE options).

        Returns:
            float | int | None: The maximum value, or None if there is none.
        """
        return self._max

    @property
    def step(self) -> float | int:
        """The increment between two possible values (RANGE options).

        Returns:
            float | int: The increment.
        """
        return self._step

    @property
    def default(self) -> bool | int | float | str | None:
        """The raw default value, runtime constants left unevaluated.

        Returns:
            bool | int | float | str | None: The default value.
        """
        return self._default

    # ------------------------------------------------------------------ #
    # Value conversion and validation
    # ------------------------------------------------------------------ #
    def _check_constants(self, default: str) -> None:
        """Checks the runtime constants contained in the default value.

        Args:
            default (str): The default value containing runtime constants.

        Raises:
            ValueError: If a constant is unknown, or if ``%%RANDOM_NUMBER%%``
                is used in a RANGE option without both bounds.
            TypeError: If a constant is not allowed for the type of the
                option, or is used in a way that is not allowed.
        """
        names = _CONSTANT_PATTERN.findall(default)
        unknown = [name for name in names if name not in _KNOWN_CONSTANTS]
        if unknown:
            raise ValueError(f"Unknown runtime constant(s) in {default!r}: {unknown!r}.")
        if self._type == OptionType.CHECK:
            raise TypeError(f"CHECK options do not accept runtime constants: {default!r}.")
        if self._type == OptionType.TEXT:
            if "RANDOM_CHOICE" in names:
                raise TypeError(f"%%RANDOM_CHOICE%% is not allowed in TEXT options: {default!r}.")
        elif self._type == OptionType.RANGE:
            if default != "%%RANDOM_NUMBER%%":
                raise TypeError(
                    f"RANGE options only accept the exact default '%%RANDOM_NUMBER%%', "
                    f"got {default!r}."
                )
            if self._min is None or self._max is None:
                raise ValueError(
                    "%%RANDOM_NUMBER%% requires both min_value and max_value in RANGE options."
                )
        elif self._type == OptionType.LIST and default != "%%RANDOM_CHOICE%%":
            raise TypeError(
                f"LIST options only accept the exact default '%%RANDOM_CHOICE%%', got {default!r}."
            )

    def _convert(self, value: Any) -> Any:
        """Converts a value according to the conversion rules of the option.

        Args:
            value (Any): The value to convert.

        Returns:
            Any: The converted value.

        Raises:
            TypeError: If the value is not accepted for the type of the option.
        """
        if self._type == OptionType.CHECK:
            if not isinstance(value, bool):
                raise TypeError(f"CHECK options only accept booleans, got {value!r}.")
            return value
        if self._type in (OptionType.LIST, OptionType.TEXT):
            if not isinstance(value, str):
                raise TypeError(f"{self._type.name} options only accept strings, got {value!r}.")
            return value
        number = _parse_number(value)
        if not self._integer:
            return float(number)
        if isinstance(number, float):
            if not number.is_integer():
                raise TypeError(f"Integer RANGE options only accept integers, got {value!r}.")
            return int(number)
        return number

    def _reference(self) -> float | int:
        """Returns the reference of the grid of the possible values (RANGE).

        Returns:
            float | int: ``min_value`` if it is defined, 0 otherwise.
        """
        return self._min if self._min is not None else 0

    def _grid_value(self, index: int) -> float | int:
        """Returns the possible value of a RANGE option at a grid index.

        Args:
            index (int): The signed index on the grid.

        Returns:
            float | int: The value ``reference + index * step``.
        """
        value = self._reference() + index * self._step
        return int(value) if self._integer else float(value)

    def _grid_position(self, value: float | int) -> float:
        """Returns the (possibly fractional) grid index of a value (RANGE).

        Args:
            value (float | int): The value to locate.

        Returns:
            float: The position of the value on the grid.
        """
        return (value - self._reference()) / self._step

    def _below_max(self, value: float | int) -> bool:
        """Tells whether a value does not exceed ``max_value`` (RANGE).

        Args:
            value (float | int): The value to check.

        Returns:
            bool: True if the value is lower than or equal to the maximum.
        """
        if self._max is None or value <= self._max:
            return True
        return not self._integer and math.isclose(value, self._max, rel_tol=_REL_TOL, abs_tol=_ABS_TOL)

    def _above_min(self, value: float | int) -> bool:
        """Tells whether a value is not lower than ``min_value`` (RANGE).

        Args:
            value (float | int): The value to check.

        Returns:
            bool: True if the value is greater than or equal to the minimum.
        """
        if self._min is None or value >= self._min:
            return True
        return not self._integer and math.isclose(value, self._min, rel_tol=_REL_TOL, abs_tol=_ABS_TOL)

    def _on_grid(self, value: float | int) -> bool:
        """Tells whether a value matches a ``step`` increment (RANGE).

        Args:
            value (float | int): The value to check.

        Returns:
            bool: True if the value lies on the grid of the possible values.
        """
        if self._integer:
            return (value - self._reference()) % self._step == 0
        index = round(self._grid_position(value))
        return math.isclose(self._grid_value(index), value, rel_tol=_REL_TOL, abs_tol=_ABS_TOL)

    def _validate(self, value: Any) -> None:
        """Checks that a converted value is a possible value of the option.

        Args:
            value (Any): The converted value.

        Raises:
            ValueError: If the value is outside the bounds, does not match a
                ``step`` increment, or is not in ``choices``.
        """
        if self._type == OptionType.RANGE:
            if not self._above_min(value) or not self._below_max(value):
                raise ValueError(
                    f"Value {value!r} is outside the bounds [{self._min!r}, {self._max!r}]."
                )
            if not self._on_grid(value):
                raise ValueError(f"Value {value!r} does not match a step of {self._step!r}.")
        elif self._type == OptionType.LIST and value not in self._choices:
            raise ValueError(f"Value {value!r} is not in the choices {list(self._choices)!r}.")

    def _same_value(self, first: Any, second: Any) -> bool:
        """Compares two converted values according to the type of the option.

        Args:
            first (Any): The first value.
            second (Any): The second value.

        Returns:
            bool: True if both values are considered identical.
        """
        if self._type == OptionType.RANGE:
            if not (_is_number(first) and _is_number(second)):
                return False
            if self._integer:
                return first == second
            return math.isclose(first, second, rel_tol=_REL_TOL, abs_tol=_ABS_TOL)
        if self._type == OptionType.TEXT:
            if not (isinstance(first, str) and isinstance(second, str)):
                return False
            return first.strip().casefold() == second.strip().casefold()
        return type(first) is type(second) and first == second

    def _is_excluded(self, value: Any, exclusions: Iterable[Any]) -> bool:
        """Tells whether a value is among excluded values.

        Args:
            value (Any): The value to look for.
            exclusions (Iterable[Any]): The excluded values.

        Returns:
            bool: True if the value is excluded.
        """
        return any(self._same_value(value, excluded) for excluded in exclusions)

    # ------------------------------------------------------------------ #
    # Default value evaluation
    # ------------------------------------------------------------------ #
    def _first_value(self) -> Any:
        """Returns the first available value of the option.

        Returns:
            Any: The value used when the default value is ``None``.
        """
        if self._type == OptionType.CHECK:
            return False
        if self._type == OptionType.LIST:
            return self._choices[0]
        if self._type == OptionType.TEXT:
            return ""
        if self._min is not None:
            return self._min
        if self._max is None or self._max >= 0:
            return self._grid_value(0)
        return self._grid_value(math.floor(self._grid_position(self._max) + _ABS_TOL))

    def _values_count(self) -> int:
        """Returns the number of possible values of a bounded RANGE option.

        Returns:
            int: The number of possible values between both bounds.
        """
        return math.floor(self._grid_position(self._max) + _ABS_TOL) + 1  # type: ignore[arg-type]

    def _random_range_value(self, exclusions: List[Any]) -> float | int | None:
        """Draws a possible value of a bounded RANGE option at random.

        Args:
            exclusions (list): The values not to select.

        Returns:
            float | int | None: The drawn value, or None if every possible
            value is excluded.
        """
        count = self._values_count()
        if count <= _MAX_ENUMERATED_VALUES:
            candidates = [
                value
                for value in (self._grid_value(index) for index in range(count))
                if not self._is_excluded(value, exclusions)
            ]
            return random.choice(candidates) if candidates else None
        # Too many values to be enumerated: the exclusions being few, a
        # rejection sampling quickly finds an available value.
        for _ in range(_MAX_ENUMERATED_VALUES):
            value = self._grid_value(random.randrange(count))
            if not self._is_excluded(value, exclusions):
                return value
        return None

    def _constant_value(self, name: str, context: Dict[str, str]) -> str:
        """Returns the textual value of a runtime constant.

        Args:
            name (str): The name of the constant, without the ``%%`` characters.
            context (dict[str, str]): The evaluation context.

        Returns:
            str: The value substituted for the constant.
        """
        if name in context:
            return str(context[name])
        if name == "CURRENT_TIME":
            return datetime.datetime.now().astimezone().isoformat(timespec="seconds")
        if name == "RANDOM_NUMBER":
            return str(random.randint(0, 100))
        return ""

    def evaluate_default(
        self,
        context: Dict[str, str] | None = None,
        exclusions: List[Any] | None = None,
    ) -> Any:
        """Provides the default value, after evaluation of the runtime constants.

        Args:
            context (dict[str, str], optional): The values of the runtime
                constants, indexed by their name without the ``%%`` characters.
                A constant present in the context always takes its value.
                Defaults to None (empty context).
            exclusions (list, optional): The values not to select during a
                random draw. Defaults to None (no exclusion).

        Returns:
            Any: The evaluated default value. For a random draw, None if all
            the possible values are excluded.
        """
        if self._default is None:
            return self._first_value()
        if not self._has_constants:
            return self._default
        ctx = context or {}
        excluded = list(exclusions or [])
        if self._type == OptionType.RANGE:
            if "RANDOM_NUMBER" in ctx:
                try:
                    return self._convert(ctx["RANDOM_NUMBER"])
                except TypeError:
                    return ctx["RANDOM_NUMBER"]
            return self._random_range_value(excluded)
        if self._type == OptionType.LIST:
            if "RANDOM_CHOICE" in ctx:
                return ctx["RANDOM_CHOICE"]
            candidates = [
                choice for choice in self._choices if not self._is_excluded(choice, excluded)
            ]
            return random.choice(candidates) if candidates else None
        return _CONSTANT_PATTERN.sub(
            lambda match: self._constant_value(match.group(1), ctx),
            self._default,  # type: ignore[arg-type]
        )

    # ------------------------------------------------------------------ #
    # Dictionary representation
    # ------------------------------------------------------------------ #
    def to_dict(self) -> Dict[str, Any]:
        """Provides a dictionary representation of the option.

        Returns:
            dict: The representation, made up of simple types only.
        """
        return {
            "option_id": self._id,
            "type": self._type.name,
            "name": self.name,
            "description": self.description,
            "default": self._default,
            "min": self._min,
            "max": self._max,
            "step": self._step,
            "choices": list(self._choices),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Option":
        """Creates an option from its dictionary representation.

        Args:
            data (dict): The representation, as returned by :meth:`to_dict`.
                The ``name`` and ``type`` keys are mandatory.

        Returns:
            Option: The created option, which keeps the ``option_id`` provided.

        Raises:
            TypeError: If the data has an unexpected type.
            ValueError: If a mandatory key is missing, if the type is unknown,
                or in the same cases as when an option is created.
        """
        if not isinstance(data, dict):
            raise TypeError(f"An option representation must be a dictionary, got {data!r}.")
        for key in ("name", "type"):
            if key not in data:
                raise ValueError(f"Missing key {key!r} in option representation.")
        type_name = data["type"]
        if not isinstance(type_name, str) or type_name not in OptionType.__members__:
            raise ValueError(f"Unknown option type: {type_name!r}.")

        def _get(key: str, default: Any) -> Any:
            value = data.get(key)
            return default if value is None else value

        option = cls(
            name=data["name"],
            option_type=OptionType[type_name],
            description=_get("description", ""),
            default=data.get("default"),
            min_value=data.get("min"),
            max_value=data.get("max"),
            step=_get("step", 1),
            choices=_get("choices", []),
        )
        option_id = data.get("option_id")
        if option_id is not None:
            if not isinstance(option_id, str):
                raise TypeError(f"option_id must be a string, got {option_id!r}.")
            option._id = option_id
        return option

    def _copy(self, keep_id: bool = True) -> "Option":
        """Returns an independent copy of the option.

        Args:
            keep_id (bool): Whether the copy represents the same option (same
                ID) or a new option (new ID). Defaults to True.

        Returns:
            Option: The copy.
        """
        data = self.to_dict()
        if not keep_id:
            data.pop("option_id")
        return Option.from_dict(data)


class OptionEntry:
    """Describes an option registered in a template or in a factory.

    An entry gathers the option and the parameters associated with it when it
    was added to a template: uniqueness, associated player attribute and
    frozen key. Entries are immutable.
    """

    __slots__ = ("_option", "_unicity", "_player_attribute", "_key")
    _option: Option
    _unicity: bool
    _player_attribute: str | ParameterFamily
    _key: str

    def __init__(
        self,
        option: Option,
        player_attribute: str | ParameterFamily,
        unicity: bool = False,
        key: str | None = None,
    ):
        """Initializes a new entry.

        Entries are created by :class:`PlayerFactoryTemplate` and
        :class:`PlayerFactory`; they are not intended to be created directly.

        Args:
            option (Option): The option, of which a copy keeping its ID is
                recorded.
            player_attribute (str | ParameterFamily): The associated attribute
                of the Player object.
            unicity (bool, optional): Whether a value can only be carried by a
                single player of a game. Defaults to False.
            key (str, optional): The frozen key. Defaults to the name of the
                option.

        Raises:
            TypeError: If a parameter has an unexpected type.
            ValueError: If ``player_attribute`` is an unsupported attribute.
        """
        if not isinstance(option, Option):
            raise TypeError(f"An Option instance is required, got {option!r}.")
        _check_player_attribute(option, player_attribute)
        if not isinstance(unicity, bool):
            raise TypeError(f"unicity must be a boolean, got {unicity!r}.")
        if key is None:
            key = option.name
        if not isinstance(key, str):
            raise TypeError(f"The key of an option must be a string, got {key!r}.")
        object.__setattr__(self, "_option", option._copy(keep_id=True))
        object.__setattr__(self, "_unicity", unicity)
        object.__setattr__(self, "_player_attribute", player_attribute)
        object.__setattr__(self, "_key", key)

    def __setattr__(self, name: str, value: Any) -> None:
        """Forbids any modification of the entry.

        Raises:
            AttributeError: Always.
        """
        raise AttributeError("OptionEntry objects are immutable.")

    def __delattr__(self, name: str) -> None:
        """Forbids any deletion of an attribute of the entry.

        Raises:
            AttributeError: Always.
        """
        raise AttributeError("OptionEntry objects are immutable.")

    @property
    def option(self) -> Option:
        """A copy of the registered option, keeping its ID.

        Returns:
            Option: The copy of the option.
        """
        return self._option._copy(keep_id=True)

    @property
    def unicity(self) -> bool:
        """Whether a value can only be carried by a single player of a game.

        Returns:
            bool: The uniqueness parameter.
        """
        return self._unicity

    @property
    def player_attribute(self) -> str | ParameterFamily:
        """The attribute of the Player object associated with the option.

        Returns:
            str | ParameterFamily: The attribute name or the family.
        """
        return self._player_attribute

    @property
    def key(self) -> str:
        """The frozen key of the option.

        Returns:
            str: The key.
        """
        return self._key

    @property
    def _option_id(self) -> str:
        """The ID of the registered option.

        Returns:
            str: The ID of the option.
        """
        return self._option.ID

    def to_dict(self) -> Dict[str, Any]:
        """Provides a dictionary representation of the registered option.

        Returns:
            dict: The representation of the option, supplemented by the
            ``unicity``, ``target``, ``attribute`` and ``key`` elements.
        """
        data = self._option.to_dict()
        if isinstance(self._player_attribute, ParameterFamily):
            target, attribute = _TARGET_BY_FAMILY[self._player_attribute], None
        else:
            target, attribute = _TARGET_ATTRIBUTE, self._player_attribute
        data.update(
            {"unicity": self._unicity, "target": target, "attribute": attribute, "key": self._key}
        )
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OptionEntry":
        """Creates an entry from its dictionary representation.

        Args:
            data (dict): The representation, as returned by :meth:`to_dict`.

        Returns:
            OptionEntry: The created entry.

        Raises:
            TypeError: If the data has an unexpected type.
            ValueError: If the data is inconsistent.
        """
        option = Option.from_dict(data)
        target = data.get("target")
        if target is None:
            raise ValueError("Missing key 'target' in option representation.")
        if target == _TARGET_ATTRIBUTE:
            player_attribute = data.get("attribute")
            if player_attribute is None:
                raise ValueError("Missing key 'attribute' for target 'ATTRIBUTE'.")
        elif isinstance(target, str) and target in _FAMILY_BY_TARGET:
            player_attribute = _FAMILY_BY_TARGET[target]
        else:
            raise ValueError(f"Unknown option target: {target!r}.")
        unicity = data.get("unicity")
        return cls(
            option,
            player_attribute,
            unicity=False if unicity is None else unicity,
            key=data.get("key"),
        )


class Player:
    """Represents a player in the game context.

    This class stores player-specific information, including their unique identifier,
    name, and custom state parameters divided into static and dynamic categories.

    Every instance is recorded in a global registry indexed by its ID, so that a
    player can be designated by its ID alone (see :meth:`get_by_id`). The
    registry only holds weak references: it does not keep a player alive.

    Attributes:
        name (str): The name of the player.
        static_state (dict): Custom attributes that rarely change during the game.
        dynamic_state (dict): Custom attributes that frequently change during the game.
    """

    _registry: "weakref.WeakValueDictionary[str, Player]" = weakref.WeakValueDictionary()

    def __init__(self, name: str = "Player", **kwargs: Any):
        """Initializes a new player instance.

        Args:
            name (str, optional): The name of the player. Defaults to "Player".
            **kwargs: Optional parameters for customizing the player.
                Each keyword argument should be a tuple of (ParameterFamily, initial_value).
                For example: score=(ParameterFamily.DYNAMIC, 0).
        """
        self._id: str = str(uuid.uuid4())
        self.name: str = name
        self.static_state: Dict[str, Any] = {}
        self.dynamic_state: Dict[str, Any] = {}

        for key, value in kwargs.items():
            if isinstance(value, tuple) and len(value) == 2 and isinstance(value[0], ParameterFamily):
                family, val = value
                if family == ParameterFamily.STATIC:
                    self.static_state[key] = val
                else:
                    self.dynamic_state[key] = val

        Player._registry[self._id] = self

    @classmethod
    def get_by_id(cls, player_id: str) -> "Player | None":
        """Looks up an existing player from its ID.

        Args:
            player_id (str): The ID of the player to look up.

        Returns:
            Player, optional: The player with this ID, or None if no such
            player exists (anymore).
        """
        return cls._registry.get(player_id)

    @classmethod
    def _resolve(cls, player: "Player | str") -> "Player":
        """Returns the player designated by an instance or by its ID.

        Args:
            player (Player | str): The Player instance or its ID.

        Returns:
            Player: The designated player.

        Raises:
            PlayerNotFoundError: If no existing player has the given ID.
        """
        if isinstance(player, Player):
            return player
        found = cls.get_by_id(player) if isinstance(player, str) else None
        if found is None:
            raise PlayerNotFoundError(player)
        return found

    @property
    def ID(self) -> str:
        """The unique identifier of the player.

        This ID is automatically generated using uuid.uuid4() and is read-only.

        Returns:
            str: The unique UUID of the player.
        """
        return self._id


class PlayerFactoryTemplate:
    """Defines the customization options of the players of a game.

    A template holds options, together with their uniqueness parameter, their
    associated player attribute and their frozen key. It is independent of any
    game, and is used by :meth:`Game.create_player_factory` to create the
    player factory of a game.

    Attributes:
        name (str): The name of the template.
    """

    def __init__(self, name: str):
        """Initializes a new, empty template.

        Args:
            name (str): The name of the template.

        Raises:
            TypeError: If the name is not a string.
        """
        if not isinstance(name, str):
            raise TypeError(f"The name of a template must be a string, got {name!r}.")
        self._id: str = str(uuid.uuid4())
        self.name: str = name
        self._entries: List[OptionEntry] = []

    @property
    def ID(self) -> str:
        """The unique identifier of the template.

        Returns:
            str: The UUID of the template.
        """
        return self._id

    @property
    def options(self) -> List[Tuple[str, str]]:
        """The IDs and names of the options of the template.

        Returns:
            list[tuple[str, str]]: A new list of (ID, name) tuples.
        """
        return [(entry._option.ID, entry._option.name) for entry in self._entries]

    def add_option(
        self,
        option: Option,
        player_attribute: str | ParameterFamily,
        unicity: bool = False,
    ) -> None:
        """Adds a copy of an option to the template.

        An option associated with the ``name`` attribute silently replaces the
        option previously associated with this attribute.

        Args:
            option (Option): The option to add.
            player_attribute (str | ParameterFamily): The attribute of the
                Player object associated with the option.
            unicity (bool, optional): Whether a value can only be carried by a
                single player of a game. Defaults to False.

        Raises:
            TypeError: If a parameter has an unexpected type.
            ValueError: If ``player_attribute`` is an unsupported attribute.
            OptionAlreadyExistsError: If a similar option is already present.
        """
        if not isinstance(option, Option):
            raise TypeError(f"An Option instance is required, got {option!r}.")
        self._add_entry(OptionEntry(option, player_attribute, unicity))

    def _add_entry(self, entry: OptionEntry) -> None:
        """Adds an entry according to the rules of :meth:`add_option`.

        Args:
            entry (OptionEntry): The entry to add.

        Raises:
            OptionAlreadyExistsError: If a similar option is already present.
        """
        replaced = None
        if isinstance(entry.player_attribute, str):
            replaced = next(
                (
                    existing
                    for existing in self._entries
                    if existing.player_attribute == entry.player_attribute
                ),
                None,
            )
        for existing in self._entries:
            if existing._option_id == entry._option_id:
                raise OptionAlreadyExistsError(existing._option_id)
            if existing is not replaced and existing.key == entry.key:
                raise OptionAlreadyExistsError(existing._option_id)
        if replaced is not None:
            self._entries.remove(replaced)
        self._entries.append(entry)

    def _find(self, option_id: str) -> OptionEntry:
        """Returns the entry of an option.

        Args:
            option_id (str): The ID of the option.

        Returns:
            OptionEntry: The entry.

        Raises:
            KeyError: If the option does not exist in the template.
        """
        for entry in self._entries:
            if entry._option_id == option_id:
                return entry
        raise KeyError(option_id)

    def get_option(self, option_id: str) -> OptionEntry:
        """Provides an option of the template.

        Args:
            option_id (str): The ID of the option.

        Returns:
            OptionEntry: The description of the option.

        Raises:
            KeyError: If the option does not exist in the template.
        """
        return self._find(option_id)

    def del_option(self, option_id: str) -> None:
        """Removes an option from the template.

        Args:
            option_id (str): The ID of the option.

        Raises:
            KeyError: If the option does not exist in the template.
        """
        self._entries.remove(self._find(option_id))

    def to_dict(self) -> Dict[str, Any]:
        """Provides a dictionary representation of the template.

        Returns:
            dict: The ``template_id``, ``name`` and ``options`` elements.
        """
        return {
            "template_id": self._id,
            "name": self.name,
            "options": [entry.to_dict() for entry in self._entries],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlayerFactoryTemplate":
        """Creates a template from its dictionary representation.

        The creation is atomic: if one of the options is rejected, no template
        is created.

        Args:
            data (dict): The representation, as returned by :meth:`to_dict`.

        Returns:
            PlayerFactoryTemplate: The created template.

        Raises:
            TypeError: If the data has an unexpected type.
            ValueError: If the data is inconsistent.
            OptionAlreadyExistsError: If two options share an ID or a key.
        """
        if not isinstance(data, dict):
            raise TypeError(f"A template representation must be a dictionary, got {data!r}.")
        if "name" not in data:
            raise ValueError("Missing key 'name' in template representation.")
        options = data.get("options")
        if options is None:
            options = []
        if not isinstance(options, list):
            raise TypeError(f"The options of a template must be a list, got {options!r}.")
        template = cls(data["name"])
        template_id = data.get("template_id")
        if template_id is not None:
            if not isinstance(template_id, str):
                raise TypeError(f"template_id must be a string, got {template_id!r}.")
            template._id = template_id
        for item in options:
            template._add_entry(OptionEntry.from_dict(item))
        return template


class PlayerFactory:
    """Creates the players of a game from predefined options.

    A factory belongs to a game, whose players are the only reference used to
    compute the values excluded by unique options. It is created by
    :meth:`Game.create_player_factory`.
    """

    def __init__(self, template: PlayerFactoryTemplate, game_id: str):
        """Initializes a new factory from a template.

        The options of the template are copied, and receive new IDs.

        Args:
            template (PlayerFactoryTemplate): The template to copy.
            game_id (str): The ID of the associated game.

        Raises:
            TypeError: If the template is not a PlayerFactoryTemplate.
        """
        if not isinstance(template, PlayerFactoryTemplate):
            raise TypeError(f"A PlayerFactoryTemplate instance is required, got {template!r}.")
        self._id: str = str(uuid.uuid4())
        self._game_id: str = game_id
        self._entries: List[OptionEntry] = [
            OptionEntry(
                entry._option._copy(keep_id=False),
                entry.player_attribute,
                entry.unicity,
                entry.key,
            )
            for entry in template._entries
        ]

    @property
    def ID(self) -> str:
        """The unique identifier of the factory.

        Returns:
            str: The UUID of the factory.
        """
        return self._id

    @property
    def game_id(self) -> str:
        """The ID of the game the factory is associated with.

        Returns:
            str: The ID of the game.
        """
        return self._game_id

    @property
    def options(self) -> List[Tuple[str, str]]:
        """The IDs and names of the options of the factory.

        Returns:
            list[tuple[str, str]]: A new list of (ID, name) tuples.
        """
        return [(entry._option.ID, entry._option.name) for entry in self._entries]

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _find(self, option_id: str) -> OptionEntry:
        """Returns the entry of an option.

        Args:
            option_id (str): The ID of the option.

        Returns:
            OptionEntry: The entry.

        Raises:
            KeyError: If the option does not exist in the factory.
        """
        for entry in self._entries:
            if entry._option_id == option_id:
                return entry
        raise KeyError(option_id)

    def _game_players(self) -> List[Player]:
        """Returns the players of the associated game.

        Returns:
            list[Player]: The existing players of the game, observers excluded.
        """
        game = Game.get_by_id(self._game_id)
        if game is None:
            return []
        players = (Player.get_by_id(player_id) for player_id in game.players)
        return [player for player in players if player is not None]

    @staticmethod
    def _read_value(player: Player, entry: OptionEntry) -> Tuple[bool, Any]:
        """Reads the value of an option carried by a player.

        Args:
            player (Player): The player to inspect.
            entry (OptionEntry): The option concerned.

        Returns:
            tuple[bool, Any]: Whether a value is present, and the value.
        """
        attribute = entry.player_attribute
        if isinstance(attribute, str):
            return True, getattr(player, attribute, None)
        state = player.static_state if attribute == ParameterFamily.STATIC else player.dynamic_state
        if entry.key in state:
            return True, state[entry.key]
        return False, None

    @staticmethod
    def _normalize(entry: OptionEntry, value: Any) -> Any:
        """Converts a value when possible, according to the rules of the option.

        Args:
            entry (OptionEntry): The option concerned.
            value (Any): The value to convert.

        Returns:
            Any: The converted value, or the value as is if it cannot be
            converted.
        """
        try:
            return entry._option._convert(value)
        except TypeError:
            return value

    def _exclusions(self, entry: OptionEntry, ignored_player_id: str | None = None) -> List[Any]:
        """Computes the values excluded for an option.

        Args:
            entry (OptionEntry): The option concerned.
            ignored_player_id (str, optional): The ID of a player not to take
                into account. Defaults to None.

        Returns:
            list: The distinct values carried by the players of the game for a
            unique option, an empty list for a non-unique option.
        """
        if not entry.unicity:
            return []
        exclusions: List[Any] = []
        for player in self._game_players():
            if player.ID == ignored_player_id:
                continue
            present, value = self._read_value(player, entry)
            if not present or value is None:
                continue
            value = self._normalize(entry, value)
            if not entry._option._is_excluded(value, exclusions):
                exclusions.append(value)
        return exclusions

    def _next_value(self, option: Option, value: Any, exclusions: List[Any]) -> Any:
        """Returns the next available value after an excluded value.

        Args:
            option (Option): The option concerned.
            value (Any): The excluded value.
            exclusions (list): The excluded values.

        Returns:
            Any: The next available value, or None if there is none.
        """
        option_type = option.option_type
        if option_type == OptionType.LIST:
            choices = list(option.choices)
            if value in choices:
                index = choices.index(value)
                choices = choices[index + 1:] + choices[:index]
            return next((c for c in choices if not option._is_excluded(c, exclusions)), None)
        if option_type == OptionType.CHECK:
            other = not value if isinstance(value, bool) else True
            return None if option._is_excluded(other, exclusions) else other
        if option_type == OptionType.TEXT:
            return None if option._is_excluded("", exclusions) else ""
        if not _is_number(value):
            value = option._first_value()
        position = option._grid_position(value)
        index = math.ceil(position - _ABS_TOL)
        if option.min_value is not None:
            index = max(index, 0)
        # Ascending search up to max_value; it always succeeds without maximum,
        # since the excluded values are finite in number.
        while True:
            candidate = option._grid_value(index)
            if not option._below_max(candidate):
                break
            if not option._is_excluded(candidate, exclusions):
                return candidate
            index += 1
        index = math.floor(position + _ABS_TOL)
        if option.max_value is not None:
            index = min(index, math.floor(option._grid_position(option.max_value) + _ABS_TOL))
        # Descending search down to min_value.
        while option.min_value is None or index >= 0:
            candidate = option._grid_value(index)
            if not option._is_excluded(candidate, exclusions):
                return candidate
            index -= 1
        return None

    def _proposed_value(
        self,
        entry: OptionEntry,
        context: Dict[str, str] | None,
        exclusions: List[Any],
    ) -> Any:
        """Computes the proposed value of an option.

        Args:
            entry (OptionEntry): The option concerned.
            context (dict[str, str], optional): The evaluation context.
            exclusions (list): The excluded values.

        Returns:
            Any: The proposed value, or None if no value is available.
        """
        ctx = dict(context or {})
        if "GAMENAME" not in ctx:
            game = Game.get_by_id(self._game_id)
            ctx["GAMENAME"] = "" if game is None or game.name is None else str(game.name)
        option = entry._option
        value = option.evaluate_default(ctx, exclusions)
        if value is None:
            return None
        value = self._normalize(entry, value)
        if not option._is_excluded(value, exclusions):
            return value
        return self._next_value(option, value, exclusions)

    @staticmethod
    def _checked_value(entry: OptionEntry, value: Any) -> Any:
        """Converts and validates a value for an option.

        Args:
            entry (OptionEntry): The option concerned.
            value (Any): The value to check.

        Returns:
            Any: The converted value.

        Raises:
            InvalidOptionValueError: If the value is of an incompatible type
                or is not a possible value of the option.
        """
        option = entry._option
        try:
            converted = option._convert(value)
        except TypeError as exc:
            raise InvalidOptionValueError(option.ID, value, "INCOMPATIBLE_TYPE") from exc
        try:
            option._validate(converted)
        except ValueError as exc:
            raise InvalidOptionValueError(option.ID, value, "INVALID_VALUE") from exc
        return converted

    def _check_player(self, player: Player) -> None:
        """Checks that a player meets the constraints of the factory.

        Args:
            player (Player): The player about to join the game.

        Raises:
            LackingOptionError: If the player does not carry a value for an
                option.
            InvalidOptionValueError: If a value is of an incompatible type or
                invalid.
            OptionValueAlreadyGivenError: If a unique value is already carried
                by another player of the game.
        """
        for entry in self._entries:
            option_id = entry._option_id
            present, raw = self._read_value(player, entry)
            if not present or raw is None:
                raise LackingOptionError(option_id, "ABSENT_FROM_PLAYER")
            value = self._checked_value(entry, raw)
            if entry.unicity and entry._option._is_excluded(
                value, self._exclusions(entry, ignored_player_id=player.ID)
            ):
                raise OptionValueAlreadyGivenError(option_id, raw)

    # ------------------------------------------------------------------ #
    # Public methods
    # ------------------------------------------------------------------ #
    def get_option(self, option_id: str, context: Dict[str, str] | None = None) -> Dict[str, Any]:
        """Provides an option of the factory with its exclusions and proposed value.

        Args:
            option_id (str): The ID of the option.
            context (dict[str, str], optional): The values of the runtime
                constants. Defaults to None.

        Returns:
            dict: The ``entry`` (OptionEntry), ``exclusions`` (list) and
            ``proposed_value`` elements.

        Raises:
            KeyError: If the option does not exist in the factory.
        """
        entry = self._find(option_id)
        exclusions = self._exclusions(entry)
        return {
            "entry": entry,
            "exclusions": list(exclusions),
            "proposed_value": self._proposed_value(entry, context, exclusions),
        }

    def create_player(
        self,
        values: Dict[str, Any] | None = None,
        context: Dict[str, str] | None = None,
    ) -> Player:
        """Creates a player from the values chosen for the options.

        The player is not added to the game, and no value is reserved.

        Args:
            values (dict[str, Any], optional): The chosen values, indexed by
                the IDs of the options. An absent option, or an option whose
                value is None, takes its proposed value. Defaults to None.
            context (dict[str, str], optional): The values of the runtime
                constants, used for the proposed values. Defaults to None.

        Returns:
            Player: The created player.

        Raises:
            TypeError: If ``values`` is not a dictionary.
            InvalidOptionValueError: If a key is unknown, or if a value is of
                an incompatible type or invalid.
            OptionValueAlreadyGivenError: If a value of a unique option is
                already carried by a player of the game.
            LackingOptionError: If an absent option has no proposed value.
        """
        if values is None:
            values = {}
        if not isinstance(values, dict):
            raise TypeError(f"values must be a dictionary, got {values!r}.")
        known = {entry._option_id for entry in self._entries}
        for key, value in values.items():
            if key not in known:
                raise InvalidOptionValueError(key, value, "UNKNOWN_OPTION")

        assignments: List[Tuple[OptionEntry, Any]] = []
        for entry in self._entries:
            option_id = entry._option_id
            exclusions = self._exclusions(entry)
            chosen = values.get(option_id)
            if chosen is None:
                proposed = self._proposed_value(entry, context, exclusions)
                if proposed is None:
                    raise LackingOptionError(option_id, "NO_AVAILABLE_VALUE")
                value = self._checked_value(entry, proposed)
            else:
                value = self._checked_value(entry, chosen)
                if entry.unicity and entry._option._is_excluded(value, exclusions):
                    raise OptionValueAlreadyGivenError(option_id, value)
            assignments.append((entry, value))

        player = Player()
        for entry, value in assignments:
            attribute = entry.player_attribute
            if isinstance(attribute, str):
                setattr(player, attribute, value)
            elif attribute == ParameterFamily.STATIC:
                player.static_state[entry.key] = value
            else:
                player.dynamic_state[entry.key] = value
        return player

    def to_dict(self) -> Dict[str, Any]:
        """Provides a dictionary representation of the factory.

        Returns:
            dict: The ``factory_id`` and ``options`` elements.
        """
        return {
            "factory_id": self._id,
            "options": [entry.to_dict() for entry in self._entries],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], game_id: str) -> "PlayerFactory":
        """Recreates a factory from its dictionary representation.

        Reserved for the restoration of a saved game.

        Args:
            data (dict): The representation, as returned by :meth:`to_dict`.
            game_id (str): The ID of the associated game.

        Returns:
            PlayerFactory: The recreated factory, keeping its IDs and keys.

        Raises:
            TypeError: If the data has an unexpected type.
            ValueError: If the data is inconsistent.
            OptionAlreadyExistsError: If two options share an ID or a key.
        """
        if not isinstance(data, dict):
            raise TypeError(f"A factory representation must be a dictionary, got {data!r}.")
        options = data.get("options")
        if options is None:
            options = []
        if not isinstance(options, list):
            raise TypeError(f"The options of a factory must be a list, got {options!r}.")
        factory = cls.__new__(cls)
        factory_id = data.get("factory_id")
        if factory_id is not None and not isinstance(factory_id, str):
            raise TypeError(f"factory_id must be a string, got {factory_id!r}.")
        factory._id = factory_id if factory_id is not None else str(uuid.uuid4())
        factory._game_id = game_id
        factory._entries = []
        for item in options:
            entry = OptionEntry.from_dict(item)
            for existing in factory._entries:
                if (
                    existing._option_id == entry._option_id
                    or existing.key == entry.key
                    or (
                        isinstance(entry.player_attribute, str)
                        and existing.player_attribute == entry.player_attribute
                    )
                ):
                    raise OptionAlreadyExistsError(existing._option_id)
            factory._entries.append(entry)
        return factory


class User:
    """Represents a user account.

    A User account provides authentication and manages permissions (role and
    administered groups). It is distinct from the players: it only keeps the
    IDs of the active players created during the sessions in which the user
    was logged in.

    Attributes:
        email (str): The email address of the account.
        role (UserRole): The role/permission level of the account.
    """
    _existing_usernames: set[str] = set()

    def __init__(self, username: str, password: str, email: str = ""):
        """Initializes a new user account.

        Args:
            username (str): The unique name of the user.
            password (str): The password for authentication (will be hashed).
            email (str, optional): The email address. Defaults to "".

        Raises:
            UserAlreadyExistsError: If the username has already been taken.
        """
        if username in User._existing_usernames:
            raise UserAlreadyExistsError(f"User '{username}' already exists.")
        
        self._id: str = str(uuid.uuid4())
        self._username: str = username
        self._hash: str = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        self.email: str = email
        self.role: UserRole = UserRole.PLAYER
        self._groups_id: List[str] = []
        self._players_id: List[str] = []
        
        User._existing_usernames.add(username)

    @property
    def ID(self) -> str:
        """The unique identifier of the user account.

        Returns:
            str: The unique UUID of the user.
        """
        return self._id

    @property
    def username(self) -> str:
        """The username of the account.

        Returns:
            str: The name used for identification.
        """
        return self._username

    @property
    def hash(self) -> str:
        """The bcrypt hash of the account password.

        Returns:
            str: The hashed password string.
        """
        return self._hash

    @property
    def groups_id(self) -> List[str]:
        """The list of group IDs for which the user is an administrator.

        This is only relevant if the user's role is GROUP_ADMIN.

        Returns:
            List[str]: A mutable list of group UUID strings.
        """
        return self._groups_id

    @property
    def players_id(self) -> List[str]:
        """The IDs of the active players created while the user was logged in.

        A player is active when it is associated with an unfinished game (as a
        player or as an observer), or with no game yet. The list is mutable but
        cannot be reassigned. Keeping it clean is the responsibility of the
        library user; the save layer cleans it before saving the account.

        Returns:
            List[str]: A mutable list of player UUID strings.
        """
        return self._players_id

    def change_password(self, new_password: str) -> None:
        """Updates the account password.

        The new password is automatically hashed using bcrypt.

        Args:
            new_password (str): The new plain-text password.
        """
        self._hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()

class Game:
    """Represents a game session.

    This class handles the core logic of a game, including player management,
    observer tracking, password protection, and turn-based progression.

    Every instance is recorded in a global registry indexed by its ID, so that a
    game can be designated by its ID alone (see :meth:`get_by_id`), for example
    by :meth:`GameGroup.add_game`. The registry only holds weak references: it
    does not keep a game alive.

    Attributes:
        name (str, optional): The name of the game session.
        static_state (dict): Custom static attributes of the game.
        dynamic_state (dict): Custom dynamic attributes of the game.
    """

    _registry: "weakref.WeakValueDictionary[str, Game]" = weakref.WeakValueDictionary()

    def __init__(
        self,
        name: str | None = None,
        max_players: int | None = None,
        max_observers: int | None = None,
        password: str | None = None,
        observer_password: str | None = None,
        turn_based: bool = False,
        min_players: int = 0,
        **kwargs: Any
    ):
        """Initializes a new game session.

        Args:
            name (str, optional): The name of the game. Defaults to None.
            max_players (int, optional): Max number of players. Defaults to None.
            max_observers (int, optional): Max number of observers. Defaults to None.
            password (str, optional): Password required to join as a player. Defaults to None.
            observer_password (str, optional): Password for observers. Defaults to None.
            turn_based (bool, optional): Whether the game is turn-based. Defaults to False.
            min_players (int, optional): Min number of players required to start the
                game. 0 (or negative) means the game can start without any player.
                If greater than ``max_players``, ``max_players`` is used instead.
                Defaults to 0.
            **kwargs: Custom state parameters as tuples of (ParameterFamily, initial_value).
        """
        self._id: str = str(uuid.uuid4())
        self.name: str | None = name
        self._min_players: int = min_players
        self._max_players: int | None = max_players
        self._max_observers: int | None = max_observers
        self._hash: str | None = (
            bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode() if password else None
        )
        self._observer_hash: str | None = (
            bcrypt.hashpw(observer_password.encode(), bcrypt.gensalt()).decode()
            if observer_password
            else (self._hash if password else None)
        )
        self._turn_based: bool = turn_based
        self._players: List[str] = []
        self._observers: List[str] = []
        self._game_state: GameState = GameState.PENDING
        self._player_factory: PlayerFactory | None = None
        self._lock: threading.RLock = threading.RLock()
        self.static_state: Dict[str, Any] = {}
        self.dynamic_state: Dict[str, Any] = {}

        for key, value in kwargs.items():
            if isinstance(value, tuple) and len(value) == 2 and isinstance(value[0], ParameterFamily):
                family, val = value
                if family == ParameterFamily.STATIC:
                    self.static_state[key] = val
                else:
                    self.dynamic_state[key] = val

        Game._registry[self._id] = self

    @classmethod
    def get_by_id(cls, game_id: str) -> "Game | None":
        """Looks up an existing game from its ID.

        Args:
            game_id (str): The ID of the game to look up.

        Returns:
            Game, optional: The game with this ID, or None if no such game
            exists (anymore).
        """
        return cls._registry.get(game_id)

    @classmethod
    def _resolve(cls, game: "Game | str") -> "Game":
        """Returns the game designated by an instance or by its ID.

        Args:
            game (Game | str): The Game instance or its ID.

        Returns:
            Game: The designated game.

        Raises:
            GameNotFoundError: If no existing game has the given ID.
        """
        if isinstance(game, Game):
            return game
        found = cls.get_by_id(game) if isinstance(game, str) else None
        if found is None:
            raise GameNotFoundError(game)
        return found

    @property
    def ID(self) -> str:
        """The unique identifier of the game session.

        Returns:
            str: The unique UUID of the game.
        """
        return self._id

    @property
    def hash(self) -> str | None:
        """The bcrypt hash of the game password.

        Returns:
            str, optional: The hashed password string or None if public.
        """
        return self._hash

    @property
    def observer_hash(self) -> str | None:
        """The bcrypt hash of the observer password.

        Returns:
            str, optional: The hashed observer password string or None.
        """
        return self._observer_hash

    @property
    def turn_based(self) -> bool:
        """Indicates if the game uses turn-based logic.

        Returns:
            bool: True if turn-based, False otherwise.
        """
        return self._turn_based

    @property
    def min_players(self) -> int:
        """The minimum number of players required to start the game.

        If the requested minimum exceeds ``max_players``, the maximum number of
        players is used instead: the game then needs exactly ``max_players``
        players to start.

        Returns:
            int: The effective minimum number of players (0 means no minimum).
        """
        if self._max_players is not None and self._min_players > self._max_players:
            return self._max_players
        return self._min_players

    @property
    def players(self) -> Tuple[str, ...]:
        """The IDs of the players currently in the game, in turn order.

        Returns:
            Tuple[str, ...]: A read-only tuple of Player IDs.
        """
        return tuple(self._players)

    @property
    def observers(self) -> Tuple[str, ...]:
        """The IDs of the observers currently watching the game.

        Returns:
            Tuple[str, ...]: A read-only tuple of Player IDs.
        """
        return tuple(self._observers)

    @property
    def current_player(self) -> str | None:
        """The ID of the player whose turn it currently is.

        Only applicable for turn-based games.

        Returns:
            str, optional: The ID of the Player whose turn it is, or None.
        """
        if not self._turn_based or not self._players:
            return None
        # Simple implementation: index 0 is always current player
        return self._players[0]

    @property
    def game_state(self) -> GameState:
        """The current lifecycle state of the game.

        Returns:
            GameState: One of PENDING, IN_PROGRESS, PAUSING, or FINISHED.
        """
        return self._game_state

    @property
    def player_factory(self) -> "PlayerFactory | None":
        """The player factory of the game.

        Returns:
            PlayerFactory, optional: The factory, or None if the game has none.
        """
        return self._player_factory

    def change_password(self, new_password: str) -> None:
        """Updates the password required to join the game.

        Args:
            new_password (str): The new plain-text password.
        """
        self._hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()

    def create_player_factory(self, template: PlayerFactoryTemplate | None) -> None:
        """Creates, replaces or removes the player factory of the game.

        Only possible while the game is pending. Creating or replacing the
        factory also requires the game to have no player (observers are not
        taken into account); removing it does not.

        Args:
            template (PlayerFactoryTemplate | None): The template to create the
                factory from, or None to remove the factory.

        Raises:
            TypeError: If the template is neither a PlayerFactoryTemplate nor None.
            GameAlreadyStartedError: If the game is in progress or paused.
            GameIsFinishedError: If the game is finished.
            GameHasPlayersError: If a factory is created while the game
                already has players.
        """
        if template is not None and not isinstance(template, PlayerFactoryTemplate):
            raise TypeError(
                f"template must be a PlayerFactoryTemplate or None, got {template!r}."
            )
        with self._lock:
            if self._game_state in (GameState.IN_PROGRESS, GameState.PAUSING):
                raise GameAlreadyStartedError()
            if self._game_state == GameState.FINISHED:
                raise GameIsFinishedError()
            if template is None:
                self._player_factory = None
                return
            if self._players:
                raise GameHasPlayersError(self._id)
            self._player_factory = PlayerFactory(template, self._id)

    def join_game_as_player(self, player: Player | str, password: str | None = None) -> None:
        """Adds a player to the game session.

        When the game has a player factory, the player must meet its
        constraints. The checks and the addition are performed atomically.

        Args:
            player (Player | str): The Player instance or its ID.
            password (str, optional): The password if the game is private.

        Raises:
            GameIsFullError: If the maximum number of players has been reached.
            PasswordError: If the provided password is incorrect.
            PlayerNotFoundError: If no existing player has the provided ID.
            LackingOptionError: If the player does not carry a value for an
                option of the factory.
            InvalidOptionValueError: If the player carries a value of an
                incompatible type or an invalid value for an option.
            OptionValueAlreadyGivenError: If the player carries a value of a
                unique option already carried by another player of the game.
        """
        with self._lock:
            if self._max_players is not None and len(self._players) >= self._max_players:
                raise GameIsFullError("Game is full.")

            if self._hash and (
                not password or not bcrypt.checkpw(password.encode(), self._hash.encode())
            ):
                raise PasswordError("Incorrect password.")

            resolved = Player._resolve(player)
            if self._player_factory is not None:
                self._player_factory._check_player(resolved)
            self._players.append(resolved.ID)

    def create_and_join_player(
        self,
        values: Dict[str, Any] | None = None,
        password: str | None = None,
        context: Dict[str, str] | None = None,
    ) -> Player:
        """Creates a player from the factory of the game and adds it as a player.

        Both steps are performed atomically: a player that cannot join the
        game is discarded.

        Args:
            values (dict[str, Any], optional): The values chosen for the
                options, indexed by their IDs. Defaults to None.
            password (str, optional): The password if the game is private.
            context (dict[str, str], optional): The values of the runtime
                constants. Defaults to None.

        Returns:
            Player: The created player, added to the game.

        Raises:
            PlayerFactoryNotDefinedError: If the game has no player factory.
            InvalidOptionValueError: See :meth:`PlayerFactory.create_player`
                and :meth:`join_game_as_player`.
            OptionValueAlreadyGivenError: See :meth:`PlayerFactory.create_player`
                and :meth:`join_game_as_player`.
            LackingOptionError: See :meth:`PlayerFactory.create_player` and
                :meth:`join_game_as_player`.
            PasswordError: If the provided password is incorrect.
            GameIsFullError: If the maximum number of players has been reached.
        """
        with self._lock:
            if self._player_factory is None:
                raise PlayerFactoryNotDefinedError(self._id)
            player = self._player_factory.create_player(values, context)
            self.join_game_as_player(player, password)
            return player

    def remove_player(self, player: Player | str) -> None:
        """Removes a player from the game session.

        Args:
            player (Player | str): The Player instance or its ID to remove.

        Raises:
            PlayerNotFoundInGameError: If the player is not in this game.
        """
        p_id = player if isinstance(player, str) else player.ID
        if p_id not in self._players:
            raise PlayerNotFoundInGameError(p_id)
        self._players.remove(p_id)

    def join_game_as_observer(self, player: Player | str, password: str | None = None) -> None:
        """Adds an observer to the game session.

        Args:
            player (Player | str): The Player instance or its ID.
            password (str, optional): The observer password if required.

        Raises:
            GameIsFullError: If the maximum number of observers has been reached.
            PasswordError: If the provided password is incorrect.
            PlayerNotFoundError: If no existing player has the provided ID.
        """
        if self._max_observers is not None and len(self._observers) >= self._max_observers:
            raise GameIsFullError("Observers list is full.")

        target_hash = self._observer_hash
        if target_hash and (not password or not bcrypt.checkpw(password.encode(), target_hash.encode())):
            raise PasswordError("Incorrect observer password.")

        self._observers.append(Player._resolve(player).ID)

    def remove_observer(self, player: Player | str) -> None:
        """Removes an observer from the game session.

        Args:
            player (Player | str): The Player instance or its ID to remove.

        Raises:
            PlayerNotFoundInGameError: If the observer is not in this game.
        """
        p_id = player if isinstance(player, str) else player.ID
        if p_id not in self._observers:
            raise PlayerNotFoundInGameError(p_id)
        self._observers.remove(p_id)

    def start(self) -> None:
        """Starts the game session.

        Sets the state to IN_PROGRESS.

        Raises:
            GameAlreadyStartedError: If the game is already in progress or paused.
            GameIsFinishedError: If the game has already finished.
            NotEnoughPlayersError: If the game has fewer players than ``min_players``.
        """
        if self._game_state in (GameState.IN_PROGRESS, GameState.PAUSING):
            raise GameAlreadyStartedError()
        if self._game_state == GameState.FINISHED:
            raise GameIsFinishedError()
        min_players = self.min_players
        if len(self._players) < min_players:
            raise NotEnoughPlayersError(
                f"At least {min_players} player(s) required to start the game "
                f"({len(self._players)} currently)."
            )
        self._game_state = GameState.IN_PROGRESS

    def pause(self) -> None:
        """Temporarily suspends the game session.

        Sets the state to PAUSING.

        Raises:
            GameNotStartedError: If the game is not currently in progress.
            GameAlreadyPausedError: If the game is already paused.
        """
        if self._game_state != GameState.IN_PROGRESS:
            raise GameNotStartedError()
        if self._game_state == GameState.PAUSING:
            raise GameAlreadyPausedError()
        self._game_state = GameState.PAUSING

    def resume(self) -> None:
        """Resumes a paused game session.

        Sets the state to IN_PROGRESS.

        Raises:
            GameNotPausedError: If the game is not currently paused.
        """
        if self._game_state != GameState.PAUSING:
            raise GameNotPausedError()
        self._game_state = GameState.IN_PROGRESS

    def stop(self) -> None:
        """Ends the game session permanently.

        Sets the state to FINISHED.

        Raises:
            GameNotStartedError: If the game was not in progress or paused.
        """
        if self._game_state not in (GameState.IN_PROGRESS, GameState.PAUSING):
            raise GameNotStartedError()
        self._game_state = GameState.FINISHED

    def next_turn(self) -> None:
        """Advances the game to the next player's turn.

        Only applicable for turn-based games.

        Raises:
            GameNotTurnBasedError: If the game is not turn-based.
            GameIsFinishedError: If the game has already finished.
            GameNotStartedError: If the game has not started yet.
        """
        if not self._turn_based:
            raise GameNotTurnBasedError()
        if self._game_state == GameState.FINISHED:
            raise GameIsFinishedError()
        if self._game_state != GameState.IN_PROGRESS and self._game_state != GameState.PAUSING:
            raise GameNotStartedError()
        
        if self._players:
            first = self._players.pop(0)
            self._players.append(first)

    def reverse_order(self) -> None:
        """Inverses the order of players in a turn-based game.

        Raises:
            GameNotTurnBasedError: If the game is not turn-based.
            GameIsFinishedError: If the game has already finished.
        """
        if not self._turn_based:
            raise GameNotTurnBasedError()
        if self._game_state == GameState.FINISHED:
            raise GameIsFinishedError()
        self._players.reverse()

    def set_player_rank(self, player: Player | str, rank: int) -> None:
        """Changes a player's position in the turn order.

        Args:
            player (Player | str): The Player or player ID to move.
            rank (int): The new 0-based rank for the player.

        Raises:
            GameNotTurnBasedError: If the game is not turn-based.
            GameIsFinishedError: If the game has already finished.
            PlayerNotFoundInGameError: If the player is not in the game.
            IndexError: If the provided rank is out of bounds.
        """
        if not self._turn_based:
            raise GameNotTurnBasedError()
        if self._game_state == GameState.FINISHED:
            raise GameIsFinishedError()
        
        p_id = player if isinstance(player, str) else player.ID
        if p_id not in self._players:
            raise PlayerNotFoundInGameError(p_id)
        if not isinstance(rank, int) or rank < 0 or rank >= len(self._players):
            raise IndexError(f"Invalid rank: {rank!r}.")

        self._players.remove(p_id)
        self._players.insert(rank, p_id)

class GameGroup:
    """Represents a collection of game sessions.

    A GameGroup allows managing multiple games together and can store
    shared parameters. The group only keeps the IDs of its games.

    Attributes:
        name (str): The name of the game group.
        parameters (dict): Custom parameters for the group.
    """

    def __init__(self, name: str, password: str | None = None, **kwargs: Any):
        """Initializes a new game group.

        Args:
            name (str): The name of the group.
            password: Optional password required to access the group.
            **kwargs: Optional custom parameters for the group.
        """
        self._id: str = str(uuid.uuid4())
        self.name: str = name
        self._games: List[str] = []
        self.parameters: Dict[str, Any] = kwargs
        self._hash: str | None = (
            bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            if password else None
        )

    @property
    def ID(self) -> str:
        """The unique identifier of the game group.

        Returns:
            str: The unique UUID of the group.
        """
        return self._id

    @property
    def games(self) -> Tuple[str, ...]:
        """The IDs of the games currently in the group.

        Returns:
            Tuple[str, ...]: A read-only tuple of game UUID strings.
        """
        return tuple(self._games)

    @property
    def hash(self) -> str | None:
        """The bcrypt hash of the group access password, if configured."""
        return self._hash

    @property
    def password_required(self) -> bool:
        """Whether access to the group requires a password."""
        return self._hash is not None

    def check_password(self, password: str | None) -> bool:
        """Checks a plain-text group password."""
        return bool(
            self._hash
            and isinstance(password, str)
            and bcrypt.checkpw(password.encode(), self._hash.encode())
        )

    def change_password(self, new_password: str | None) -> None:
        """Sets a password or removes protection when ``None`` is supplied."""
        self._hash = (
            bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
            if new_password else None
        )

    def add_game(self, game: Game | str) -> None:
        """Adds a game session to the end of the group.

        Args:
            game (Game | str): The Game instance to add, or its ID.

        Raises:
            GameNotFoundError: If no existing game has the given ID.
        """
        self._games.append(Game._resolve(game).ID)

    def remove_game(self, game: Game | str) -> None:
        """Removes a game session from the group.

        Args:
            game (Game | str): The Game instance or its ID to remove.

        Raises:
            GameNotFoundInGroupError: If the game is not in the group.
        """
        g_id = game.ID if isinstance(game, Game) else game
        if g_id not in self._games:
            raise GameNotFoundInGroupError(g_id)
        self._games.remove(g_id)
