"""Tests for game factory templates, group game factories and their protocol messages."""
import pytest

from multiplayer import OptionType, ParameterFamily, SaveFormat
from multiplayer.exceptions import (
    GroupHasGamesError,
    MultiplayerError,
    OptionValueAlreadyGivenError,
    PlayerFactoryTemplateNotFoundError,
    UnsupportedFeatureError,
)
from multiplayer.game import (
    GameFactoryTemplate,
    GameGroup,
    Option,
    PlayerFactoryTemplate,
)
from multiplayer.server import AccessLevel, GameServer

from test_client import ServerRunner
from test_server import _dispatch, _make_session


@pytest.fixture
def server():
    runner = ServerRunner()
    runner.start()
    yield runner
    runner.stop()


def _name_option() -> Option:
    return Option(
        "Game name",
        OptionType.TEXT,
        default="Game_%%RANDOM_NUMBER%%",
    )


def _game_template() -> GameFactoryTemplate:
    template = GameFactoryTemplate("Tournament")
    template.add_option(_name_option(), "name", unicity=True)
    template.add_option(
        Option("Max players", OptionType.RANGE, min_value=2, max_value=4, default=4),
        "max_players",
    )
    return template


# --------------------------------------------------------------------------- #
# Library level
# --------------------------------------------------------------------------- #
def test_game_factory_creation_exclusions_and_atomicity():
    group = GameGroup("Group", password="secret")
    group.create_game_factory(_game_template())
    factory = group.game_factory
    assert factory is not None
    name_id, max_id = (option_id for option_id, _ in factory.options)

    game = group.create_and_add_game(
        {name_id: "Tournament_1", max_id: 4}, None, "secret"
    )
    assert game.name == "Tournament_1" and game.ID in group.games
    assert factory.get_option(name_id)["exclusions"] == ["Tournament_1"]

    with pytest.raises(OptionValueAlreadyGivenError):
        group.create_and_add_game(
            {name_id: "Tournament_1", max_id: 4}, None, "secret"
        )
    assert len(group.games) == 1

    with pytest.raises(GroupHasGamesError):
        group.create_game_factory(_game_template())

    group.remove_game(game)
    assert factory.get_option(name_id)["exclusions"] == []
    with pytest.raises(TypeError):
        group.create_game_factory("not a template")

    group.create_game_factory(None)
    assert group.game_factory is None


def test_game_factory_rejects_incompatible_options():
    template = GameFactoryTemplate("Bad")
    with pytest.raises(TypeError):
        template.add_option(Option("Decimal", OptionType.RANGE, min_value=0, max_value=1, step=0.5), "max_players")
    with pytest.raises(TypeError):
        template.add_option(Option("Check", OptionType.CHECK), "name")
    with pytest.raises(ValueError):
        template.add_option(Option("Text", OptionType.TEXT), "unknown_attribute")
    template.add_option(Option("Hidden", OptionType.TEXT, default="A"), ParameterFamily.STATIC, hide=True)
    entry = template.get_option(template.options[0][0])
    assert entry.game_attribute == ParameterFamily.STATIC and entry.hide is True
    with pytest.raises(KeyError):
        template.get_option("missing")


def test_game_factory_player_factory_template_option():
    player_template = PlayerFactoryTemplate("Player model")
    player_template.add_option(
        Option("Color", OptionType.LIST, choices=["white", "black"], default="white"),
        ParameterFamily.STATIC,
    )
    template = GameFactoryTemplate("With players")
    template.add_option(
        Option("Players", OptionType.TEXT, default=player_template.ID),
        "player_factory_template",
    )
    group = GameGroup("Group")
    group.create_game_factory(template)
    game = group.create_and_add_game()
    assert game.player_factory_template_id == player_template.ID
    assert game.player_factory is not None
    with pytest.raises(PlayerFactoryTemplateNotFoundError):
        template2 = GameFactoryTemplate("Unknown model")
        template2.add_option(
            Option("Players", OptionType.TEXT, default="missing-id"),
            "player_factory_template",
        )
        group2 = GameGroup("Group 2")
        group2.create_game_factory(template2)
        group2.create_and_add_game()


# --------------------------------------------------------------------------- #
# Protocol level
# --------------------------------------------------------------------------- #
_GAME_TEMPLATE_OPTIONS = [
    {
        "type": "TEXT",
        "name": "Game name",
        "default": "Game_%%RANDOM_NUMBER%%",
        "unicity": True,
        "target": "ATTRIBUTE",
        "attribute": "name",
    },
    {
        "type": "RANGE",
        "name": "Max players",
        "min": 2,
        "max": 4,
        "default": 4,
        "target": "ATTRIBUTE",
        "attribute": "max_players",
    },
]


def _create_game_template(server, session):
    response = _dispatch(
        server,
        session,
        "FACTORY_TEMPLATE_CREATE",
        {"name": "Tournament", "factory_type": "game_factory", "options": _GAME_TEMPLATE_OPTIONS},
    )
    assert response["payload"]["success"] is True
    return response["payload"]["template_id"]


def test_factory_type_separates_template_registries():
    server = GameServer()
    admin, _ = _make_session(server, AccessLevel.ADMIN)
    base, _ = _make_session(server)
    template_id = _create_game_template(server, admin)

    games = _dispatch(server, base, "FACTORY_TEMPLATE_LIST", {"factory_type": "game_factory"})
    assert games["payload"]["templates"][0]["factory_type"] == "game_factory"
    players = _dispatch(server, base, "FACTORY_TEMPLATE_LIST")
    assert players["payload"]["templates"] == []
    assert _dispatch(server, admin, "FACTORY_TEMPLATE_GET", {"template_id": template_id})[
        "payload"
    ]["error_code"] == "FACTORY_TEMPLATE_NOT_FOUND"
    details = _dispatch(
        server,
        admin,
        "FACTORY_TEMPLATE_GET",
        {"template_id": template_id, "factory_type": "game_factory"},
    )["payload"]
    assert details["factory_type"] == "game_factory" and len(details["options"]) == 2

    assert _dispatch(
        server,
        admin,
        "FACTORY_TEMPLATE_DELETE",
        {"template_id": template_id, "factory_type": "player_factory"},
    )["payload"]["error_code"] == "FACTORY_TEMPLATE_NOT_FOUND"
    assert _dispatch(
        server,
        base,
        "FACTORY_TEMPLATE_LIST",
        {"factory_type": "unknown"},
    )["payload"]["error_code"] == "INVALID_DATA"
    assert _dispatch(
        server,
        admin,
        "FACTORY_TEMPLATE_DELETE",
        {"template_id": template_id, "factory_type": "game_factory"},
    )["payload"]["success"] is True


def test_group_factory_get_and_game_creation():
    server = GameServer()
    admin, _ = _make_session(server, AccessLevel.ADMIN)
    template_id = _create_game_template(server, admin)
    response = _dispatch(
        server, admin, "GROUP_CREATE", {"name": "G", "game_factory_template_id": template_id}
    )
    group_id = response["payload"]["group_id"]
    listing = _dispatch(server, admin, "GROUP_LIST")["payload"]["groups"][0]
    assert listing["has_game_factory"] is True

    form = _dispatch(server, admin, "GROUP_FACTORY_GET", {"group_id": group_id})["payload"]
    assert form["success"] is True and form["factory_id"]
    assert form["options"][0]["attribute"] == "name"
    assert form["options"][0]["unicity"] is True
    assert form["options"][0]["exclusions"] == []
    assert form["options"][0]["proposed_value"].startswith("Game_")

    name_id = form["options"][0]["option_id"]
    created = _dispatch(
        server,
        admin,
        "GAME_CREATE",
        {
            "name": "ignored",
            "group_id": group_id,
            "game_factory_values": {name_id: "Unique game"},
        },
    )["payload"]
    assert created["success"] is True
    game = server._games[created["game_id"]]
    assert game.name == "Unique game"

    form = _dispatch(server, admin, "GROUP_FACTORY_GET", {"group_id": group_id})["payload"]
    assert form["options"][0]["exclusions"] == ["Unique game"]

    duplicated = _dispatch(
        server,
        admin,
        "GAME_CREATE",
        {"name": "ignored", "group_id": group_id, "game_factory_values": {name_id: "Unique game"}},
    )["payload"]
    assert duplicated["error_code"] == "OPTION_VALUE_ALREADY_GIVEN"
    assert duplicated["details"]["option_id"] == name_id

    unknown = _dispatch(
        server,
        admin,
        "GAME_CREATE",
        {"name": "ignored", "group_id": group_id, "game_factory_values": {"unknown": "x"}},
    )["payload"]
    assert unknown["error_code"] == "INVALID_OPTION_VALUE"
    assert unknown["details"]["reason"] == "UNKNOWN_OPTION"

    plain_group = _dispatch(server, admin, "GROUP_CREATE", {"name": "Plain"})["payload"]["group_id"]
    no_factory = _dispatch(
        server,
        admin,
        "GAME_CREATE",
        {"name": "x", "group_id": plain_group, "game_factory_values": {}},
    )["payload"]
    assert no_factory["error_code"] == "NO_GAME_FACTORY"
    assert _dispatch(server, admin, "GROUP_FACTORY_GET", {"group_id": plain_group})["payload"][
        "error_code"
    ] == "NO_GAME_FACTORY"


def test_group_factory_notifications_and_set():
    server = GameServer()
    admin, writer = _make_session(server, AccessLevel.ADMIN)
    template_id = _create_game_template(server, admin)
    group_id = _dispatch(
        server, admin, "GROUP_CREATE", {"name": "G", "game_factory_template_id": template_id}
    )["payload"]["group_id"]
    form = _dispatch(server, admin, "GROUP_FACTORY_GET", {"group_id": group_id})["payload"]
    name_id = form["options"][0]["option_id"]

    writer.buffer.clear()
    created = _dispatch(
        server,
        admin,
        "GAME_CREATE",
        {"name": "x", "group_id": group_id, "game_factory_values": {name_id: "Game A"}},
    )["payload"]
    from test_server import _decode_messages

    notifications = [m for m in _decode_messages(writer.buffer) if m["type"] == "GAME_CREATION_FACTORY_UPDATED"]
    assert created["success"] is True and notifications
    assert notifications[-1]["payload"]["options"] == [
        {"option_id": name_id, "exclusions": ["Game A"]}
    ]

    blocked = _dispatch(
        server,
        admin,
        "GROUP_FACTORY_SET",
        {"group_id": group_id, "template_id": template_id},
    )["payload"]
    assert blocked["error_code"] == "GROUP_HAS_GAMES"

    game_id = created["game_id"]
    _dispatch(server, admin, "GROUP_REMOVE_GAME", {"group_id": group_id, "game_id": game_id})
    replaced = _dispatch(
        server, admin, "GROUP_FACTORY_SET", {"group_id": group_id, "template_id": template_id}
    )["payload"]
    assert replaced["success"] is True and replaced["has_game_factory"] is True
    removed = _dispatch(server, admin, "GROUP_FACTORY_SET", {"group_id": group_id, "template_id": None})[
        "payload"
    ]
    assert removed["success"] is True and removed["has_game_factory"] is False
    assert admin.factory_group_id is None
    assert _dispatch(server, admin, "GROUP_FACTORY_GET", {"group_id": group_id})["payload"][
        "error_code"
    ] == "NO_GAME_FACTORY"


def test_client_game_factory_api(server):
    from multiplayer.client import GameClient

    admin = GameClient(host="127.0.0.1", port=server.port)
    admin.connect()
    try:
        admin.login("admin", "admin")
        created = admin.create_game_factory_template("Tournament", _GAME_TEMPLATE_OPTIONS)
        template_id = created["template_id"]
        assert admin.list_game_factory_templates()["templates"][0]["template_id"] == template_id
        assert admin.get_game_factory_template(template_id)["name"] == "Tournament"
        assert admin.update_game_factory_template(template_id, name="Tournament 2")["success"] is True
        with pytest.raises(ValueError):
            admin.update_game_factory_template(template_id)

        group_id = admin.send_request(
            "GROUP_CREATE", name="G", game_factory_template_id=template_id
        )["group_id"]
        form = admin.get_group_game_factory(group_id)
        option_id = form["options"][0]["option_id"]
        game_id = admin.create_game(
            "ignored", group_id=group_id, game_factory_values={option_id: "Client game"}
        )
        assert game_id in server.server._games
        assert server.server._games[game_id].name == "Client game"

        with pytest.raises(MultiplayerError):
            admin.create_game(
                "ignored", group_id=group_id, game_factory_values={"unknown": "x"}
            )

        assert admin.delete_game_factory_template(template_id)["success"] is True
        with pytest.raises(MultiplayerError):
            admin.get_game_factory_template(template_id)
    finally:
        admin.disconnect()


@pytest.mark.parametrize("save_format", list(SaveFormat))
def test_game_factory_templates_and_groups_survive_a_save(tmp_path, save_format):
    from multiplayer.save import Save

    path = tmp_path / "save.dat"
    save = Save(path, save_format)
    template = _game_template()
    save.save(template)
    group = GameGroup("G")
    group.create_game_factory(template)
    group.create_and_add_game({group.game_factory.options[0][0]: "Unique"})
    save.save(group)
    save.flush()

    restored = Save(path, save_format)
    templates = list(restored.load(GameFactoryTemplate))
    groups = list(restored.load(GameGroup))
    assert len(templates) == 1 and templates[0].name == "Tournament"
    assert len(groups) == 1 and groups[0].game_factory is not None
    assert len(groups[0].games) == 1


def test_client_requires_game_factory_feature():
    from multiplayer.client import GameClient

    client = GameClient()
    with pytest.raises(UnsupportedFeatureError):
        client.list_game_factory_templates()
    with pytest.raises(UnsupportedFeatureError):
        client.get_group_game_factory("group")
    with pytest.raises(UnsupportedFeatureError):
        client.create_game("x", game_factory_values={})
