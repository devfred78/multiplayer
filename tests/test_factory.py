"""Tests for the player customization options and the player factories."""
import pytest

from multiplayer import GameState, OptionType, ParameterFamily
from multiplayer.exceptions import (
    GameAlreadyStartedError,
    GameHasPlayersError,
    GameIsFinishedError,
    InvalidOptionValueError,
    LackingOptionError,
    OptionAlreadyExistsError,
    OptionError,
    OptionValueAlreadyGivenError,
    PlayerFactoryNotDefinedError,
)
from multiplayer.game import (
    Game,
    Option,
    OptionEntry,
    Player,
    PlayerFactory,
    PlayerFactoryTemplate,
)


# ---------------------------------------------------------------------- #
# Option
# ---------------------------------------------------------------------- #
def test_option_defaults_and_attributes():
    option = Option("Color", OptionType.LIST, choices=["white", "black"])
    assert option.ID
    assert option.name == "Color"
    assert option.description == ""
    assert option.option_type == OptionType.LIST
    assert option.choices == ("white", "black")
    assert option.default is None
    assert option.step == 1


def test_option_choices_are_copied():
    choices = ["a", "b"]
    option = Option("x", OptionType.LIST, choices=choices)
    choices.append("c")
    assert option.choices == ("a", "b")


@pytest.mark.parametrize(
    "kwargs, exception",
    [
        ({"option_type": "LIST"}, TypeError),
        ({"option_type": OptionType.RANGE, "min_value": 5, "max_value": 1}, ValueError),
        ({"option_type": OptionType.RANGE, "step": 0}, ValueError),
        ({"option_type": OptionType.LIST, "choices": ["a", 1]}, TypeError),
        ({"option_type": OptionType.LIST, "choices": ["a", "a"]}, ValueError),
        ({"option_type": OptionType.LIST}, ValueError),
        ({"option_type": OptionType.CHECK, "default": 1}, TypeError),
        ({"option_type": OptionType.TEXT, "default": 3}, TypeError),
        ({"option_type": OptionType.RANGE, "default": True}, TypeError),
        ({"option_type": OptionType.RANGE, "default": 3.5}, ValueError),
        ({"option_type": OptionType.RANGE, "min_value": 0, "max_value": 3, "default": 4}, ValueError),
        ({"option_type": OptionType.LIST, "choices": ["a"], "default": "b"}, ValueError),
        ({"option_type": OptionType.TEXT, "default": "%%UNKNOWN%%"}, ValueError),
        ({"option_type": OptionType.TEXT, "default": "%%RANDOM_CHOICE%%"}, TypeError),
        ({"option_type": OptionType.CHECK, "default": "%%RANDOM_NUMBER%%"}, TypeError),
        ({"option_type": OptionType.RANGE, "default": "x%%RANDOM_NUMBER%%"}, TypeError),
        ({"option_type": OptionType.RANGE, "default": "%%RANDOM_NUMBER%%"}, ValueError),
        ({"option_type": OptionType.LIST, "choices": ["a"], "default": "%%RANDOM_NUMBER%%"}, TypeError),
    ],
)
def test_option_creation_checks(kwargs, exception):
    with pytest.raises(exception):
        Option("x", **kwargs)


def test_range_option_integer_and_decimal_conversion():
    integer = Option("n", OptionType.RANGE, min_value=0, max_value=10, default="3.0")
    assert integer.default == 3 and isinstance(integer.default, int)
    assert integer.min_value == 0 and isinstance(integer.min_value, int)
    decimal = Option("d", OptionType.RANGE, min_value=0, max_value=1, step=0.1, default=0.3)
    assert isinstance(decimal.min_value, float)
    assert decimal.default == pytest.approx(0.3)


def test_text_option_keeps_isolated_percent_signs():
    option = Option("t", OptionType.TEXT, default="100% %%done")
    assert option.evaluate_default() == "100% %%done"


def test_evaluate_default_first_available_value():
    assert Option("c", OptionType.CHECK).evaluate_default() is False
    assert Option("t", OptionType.TEXT).evaluate_default() == ""
    assert Option("l", OptionType.LIST, choices=["a", "b"]).evaluate_default() == "a"
    assert Option("r", OptionType.RANGE, min_value=2, max_value=5).evaluate_default() == 2
    assert Option("r", OptionType.RANGE).evaluate_default() == 0
    assert Option("r", OptionType.RANGE, step=2, max_value=-3).evaluate_default() == -4


def test_evaluate_default_with_constants_and_context():
    option = Option("t", OptionType.TEXT, default="%%USERNAME%%@%%GAMENAME%% %%RANDOM_NUMBER%%")
    context = {"USERNAME": "alice", "GAMENAME": "chess", "RANDOM_NUMBER": "7"}
    assert option.evaluate_default(context) == "alice@chess 7"
    assert context == {"USERNAME": "alice", "GAMENAME": "chess", "RANDOM_NUMBER": "7"}
    # Context constants absent from the context are replaced by an empty string.
    assert Option("t", OptionType.TEXT, default="[%%SERVERNAME%%]").evaluate_default() == "[]"
    # Constants are kept raw in the option.
    assert option.default == "%%USERNAME%%@%%GAMENAME%% %%RANDOM_NUMBER%%"


def test_evaluate_default_current_time_format():
    value = Option("t", OptionType.TEXT, default="%%CURRENT_TIME%%").evaluate_default()
    assert len(value) == 25 and value[10] == "T"


def test_random_draws_respect_exclusions():
    number = Option("r", OptionType.RANGE, min_value=1, max_value=3, default="%%RANDOM_NUMBER%%")
    for _ in range(20):
        assert number.evaluate_default(exclusions=[1, 3]) == 2
    assert number.evaluate_default(exclusions=[1, 2, 3]) is None
    choice = Option("l", OptionType.LIST, choices=["a", "b"], default="%%RANDOM_CHOICE%%")
    assert choice.evaluate_default(exclusions=["a"]) == "b"
    assert choice.evaluate_default(exclusions=["a", "b"]) is None


def test_option_dict_roundtrip():
    option = Option(
        "Level", OptionType.RANGE, description="d", min_value=1, max_value=9, step=2, default=3
    )
    data = option.to_dict()
    assert data == {
        "option_id": option.ID, "type": "RANGE", "name": "Level", "description": "d",
        "default": 3, "min": 1, "max": 9, "step": 2, "choices": [],
    }
    clone = Option.from_dict(data)
    assert clone.ID == option.ID and clone.to_dict() == data
    assert Option.from_dict({"name": "x", "type": "TEXT"}).ID != option.ID
    with pytest.raises(ValueError):
        Option.from_dict({"name": "x"})
    with pytest.raises(ValueError):
        Option.from_dict({"name": "x", "type": "COLOR"})


# ---------------------------------------------------------------------- #
# OptionEntry and PlayerFactoryTemplate
# ---------------------------------------------------------------------- #
def test_option_entry_is_immutable_and_copies_the_option():
    option = Option("Color", OptionType.LIST, choices=["w", "b"])
    entry = OptionEntry(option, ParameterFamily.STATIC, unicity=True, hide=True)
    with pytest.raises(AttributeError):
        entry.unicity = False
    with pytest.raises(AttributeError):
        entry.hide = False
    copy = entry.option
    copy.name = "changed"
    assert entry.option.name == "Color"
    assert entry.option.ID == option.ID
    data = entry.to_dict()
    assert data["target"] == "STATIC" and data["attribute"] is None and data["key"] == "Color"
    assert data["hide"] is True
    restored = OptionEntry.from_dict(data)
    assert restored.player_attribute == ParameterFamily.STATIC and restored.unicity is True
    assert restored.hide is True
    assert OptionEntry.from_dict({**data, "hide": None}).hide is False
    with pytest.raises(TypeError):
        OptionEntry.from_dict({**data, "hide": "yes"})
    with pytest.raises(ValueError):
        OptionEntry.from_dict({**data, "target": "OTHER"})
    with pytest.raises(ValueError):
        OptionEntry.from_dict({**data, "target": "ATTRIBUTE", "attribute": None})


def test_template_add_get_del_options():
    template = PlayerFactoryTemplate("Chess")
    option = Option("Color", OptionType.LIST, choices=["w", "b"])
    template.add_option(option, ParameterFamily.STATIC, hide=True, unicity=True)
    option.name = "Renamed"
    assert template.options == [(option.ID, "Color")]
    entry = template.get_option(option.ID)
    assert entry.key == "Color" and entry.unicity and entry.hide
    with pytest.raises(OptionAlreadyExistsError):
        template.add_option(option, ParameterFamily.DYNAMIC)
    with pytest.raises(OptionAlreadyExistsError):
        template.add_option(Option("Color", OptionType.TEXT), ParameterFamily.DYNAMIC)
    template.del_option(option.ID)
    assert template.options == []
    with pytest.raises(KeyError):
        template.get_option(option.ID)
    with pytest.raises(KeyError):
        template.del_option(option.ID)


def test_template_add_option_checks():
    template = PlayerFactoryTemplate("t")
    with pytest.raises(TypeError):
        template.add_option("not an option", ParameterFamily.STATIC)
    with pytest.raises(TypeError):
        template.add_option(Option("x", OptionType.TEXT), 3)
    with pytest.raises(TypeError):
        template.add_option(Option("x", OptionType.TEXT), ParameterFamily.STATIC, hide="yes")
    with pytest.raises(ValueError):
        template.add_option(Option("x", OptionType.TEXT), "score")
    with pytest.raises(TypeError):
        template.add_option(Option("x", OptionType.CHECK), "name")


def test_template_silently_replaces_the_name_option():
    template = PlayerFactoryTemplate("t")
    first = Option("Nick", OptionType.TEXT)
    second = Option("Nick", OptionType.LIST, choices=["a", "b"])
    template.add_option(first, "name")
    template.add_option(second, "name")
    assert template.options == [(second.ID, "Nick")]


def test_template_dict_roundtrip_is_atomic():
    template = PlayerFactoryTemplate("Chess")
    template.add_option(Option("Color", OptionType.LIST, choices=["w", "b"]), ParameterFamily.STATIC)
    template.add_option(
        Option("Nick", OptionType.TEXT, default="%%USERNAME%%"), "name", unicity=True
    )
    data = template.to_dict()
    restored = PlayerFactoryTemplate.from_dict(data)
    assert restored.ID == template.ID and restored.to_dict() == data
    duplicated = {"name": "x", "options": [data["options"][0], data["options"][0]]}
    with pytest.raises(OptionAlreadyExistsError):
        PlayerFactoryTemplate.from_dict(duplicated)


# ---------------------------------------------------------------------- #
# PlayerFactory and Game
# ---------------------------------------------------------------------- #
def _chess_game(max_players=None):
    template = PlayerFactoryTemplate("Chess")
    template.add_option(
        Option("Color", OptionType.LIST, choices=["white", "black"]),
        ParameterFamily.STATIC,
        unicity=True,
    )
    template.add_option(
        Option("Nick", OptionType.TEXT, default="%%USERNAME%%"), "name", unicity=True
    )
    template.add_option(
        Option("Level", OptionType.RANGE, min_value=1, max_value=3, default=2),
        ParameterFamily.DYNAMIC,
        unicity=True,
    )
    game = Game("chess", max_players=max_players)
    game.create_player_factory(template)
    ids = {name: option_id for option_id, name in game.player_factory.options}
    return template, game, ids


def test_factory_copies_the_template_with_new_ids():
    template, game, ids = _chess_game()
    factory = game.player_factory
    assert isinstance(factory, PlayerFactory)
    assert {i for i, _ in factory.options}.isdisjoint({i for i, _ in template.options})
    template.del_option(template.options[0][0])
    assert len(factory.options) == 3


def test_factory_keeps_the_hide_flag_and_creates_hidden_options():
    template = PlayerFactoryTemplate("Hidden")
    template.add_option(
        Option("Secret", OptionType.TEXT, default="hidden"),
        ParameterFamily.STATIC,
        hide=True,
    )
    game = Game("hidden")
    game.create_player_factory(template)
    factory = game.player_factory
    factory_id = factory.options[0][0]
    assert factory.get_option(factory_id)["entry"].hide is True
    assert factory.create_player().static_state["Secret"] == "hidden"


def test_factory_proposed_values_follow_exclusions():
    _, game, ids = _chess_game()
    factory = game.player_factory
    first = game.create_and_join_player(context={"USERNAME": "alice"})
    assert first.name == "alice"
    assert first.static_state == {"Color": "white"}
    assert first.dynamic_state == {"Level": 2}
    color = factory.get_option(ids["Color"])
    assert color["exclusions"] == ["white"] and color["proposed_value"] == "black"
    level = factory.get_option(ids["Level"])
    assert level["exclusions"] == [2] and level["proposed_value"] == 3
    nick = factory.get_option(ids["Nick"], {"USERNAME": " ALICE "})
    assert nick["proposed_value"] == ""
    second = game.create_and_join_player(context={"USERNAME": "bob"})
    assert second.static_state == {"Color": "black"} and second.dynamic_state == {"Level": 3}
    assert factory.get_option(ids["Color"])["proposed_value"] is None
    assert factory.get_option(ids["Level"])["proposed_value"] == 1
    with pytest.raises(LackingOptionError) as info:
        factory.create_player(context={"USERNAME": "carol"})
    assert info.value.reason == "NO_AVAILABLE_VALUE"
    # Removing a player makes its values available again.
    game.remove_player(first)
    assert factory.get_option(ids["Color"])["proposed_value"] == "white"


def test_factory_create_player_value_errors():
    _, game, ids = _chess_game()
    factory = game.player_factory
    with pytest.raises(InvalidOptionValueError) as info:
        factory.create_player({"unknown": 1})
    assert info.value.reason == "UNKNOWN_OPTION"
    with pytest.raises(InvalidOptionValueError) as info:
        factory.create_player({ids["Level"]: "high"})
    assert info.value.reason == "INCOMPATIBLE_TYPE"
    with pytest.raises(InvalidOptionValueError) as info:
        factory.create_player({ids["Color"]: "red"})
    assert info.value.reason == "INVALID_VALUE"
    assert isinstance(info.value, ValueError) and isinstance(info.value, OptionError)
    player = factory.create_player({ids["Level"]: "3.0", ids["Nick"]: "%%USERNAME%%"})
    assert player.dynamic_state["Level"] == 3 and player.name == "%%USERNAME%%"
    keep = game.create_and_join_player({ids["Nick"]: "Alice"})
    with pytest.raises(OptionValueAlreadyGivenError):
        factory.create_player({ids["Nick"]: " alice"})
    assert keep.name == "Alice"


def test_join_game_checks_the_factory_constraints():
    _, game, ids = _chess_game()
    with pytest.raises(LackingOptionError) as info:
        game.join_game_as_player(Player("x"))
    assert info.value.reason == "ABSENT_FROM_PLAYER"
    wrong_type = Player("x", Color=(ParameterFamily.STATIC, 1), Level=(ParameterFamily.DYNAMIC, 1))
    with pytest.raises(InvalidOptionValueError) as info:
        game.join_game_as_player(wrong_type)
    assert info.value.reason == "INCOMPATIBLE_TYPE"
    valid = Player("x", Color=(ParameterFamily.STATIC, "white"), Level=(ParameterFamily.DYNAMIC, 1))
    game.join_game_as_player(valid)
    clone = Player("X ", Color=(ParameterFamily.STATIC, "black"), Level=(ParameterFamily.DYNAMIC, 2))
    with pytest.raises(OptionValueAlreadyGivenError):
        game.join_game_as_player(clone)
    assert game.players == (valid.ID,)
    # Observers are not checked.
    game.join_game_as_observer(Player("watcher"))


def test_create_and_join_player_discards_a_rejected_player():
    _, game, ids = _chess_game(max_players=1)
    game.create_and_join_player({ids["Nick"]: "a"})
    with pytest.raises(Exception):
        game.create_and_join_player({ids["Nick"]: "b"})
    assert len(game.players) == 1
    with pytest.raises(PlayerFactoryNotDefinedError):
        Game("plain").create_and_join_player()


def test_create_player_factory_rules():
    template = PlayerFactoryTemplate("t")
    game = Game("g")
    with pytest.raises(TypeError):
        game.create_player_factory("template")
    game.join_game_as_observer(Player("watcher"))
    game.create_player_factory(template)
    assert game.player_factory is not None
    player = Player("p")
    game.join_game_as_player(player)
    with pytest.raises(GameHasPlayersError):
        game.create_player_factory(template)
    game.create_player_factory(None)
    assert game.player_factory is None
    game.start()
    with pytest.raises(GameAlreadyStartedError):
        game.create_player_factory(None)
    game.stop()
    assert game.game_state == GameState.FINISHED
    with pytest.raises(GameIsFinishedError):
        game.create_player_factory(template)


def test_factory_dict_roundtrip():
    _, game, _ = _chess_game()
    factory = game.player_factory
    data = factory.to_dict()
    restored = PlayerFactory.from_dict(data, game.ID)
    assert restored.ID == factory.ID and restored.to_dict() == data
    with pytest.raises(OptionAlreadyExistsError):
        PlayerFactory.from_dict({"options": data["options"] * 2}, game.ID)


def test_player_default_name():
    assert Player().name == "Player"
