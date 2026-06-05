import json
import uuid

import pytest

from multiplayer import PlayerRole, GameState, ParameterFamily, SaveFormat
from multiplayer.game import Player, User, Game, GameGroup
from multiplayer.save import Save
from multiplayer.exceptions import SaveError


def _unique_username() -> str:
    return f"user_{uuid.uuid4().hex[:8]}"


@pytest.fixture(params=[SaveFormat.JSON, SaveFormat.SQLITE])
def save_format(request):
    return request.param


def test_creates_file_if_missing(tmp_path, save_format):
    file_path = tmp_path / "save.dat"
    assert not file_path.exists()
    Save(file_path, save_format)
    assert file_path.exists()


def test_unknown_format(tmp_path):
    with pytest.raises(SaveError):
        Save(tmp_path / "save.dat", "yaml")


def test_save_and_load_player(tmp_path, save_format):
    file_path = tmp_path / "save.dat"
    save = Save(file_path, save_format)
    player = Player("Alice", team=(ParameterFamily.STATIC, "Blue"), score=(ParameterFamily.DYNAMIC, 5))
    save.save(player)
    save.flush()

    reloaded = Save(file_path, save_format)
    players = reloaded.load(Player)
    assert len(players) == 1
    assert players[0].ID == player.ID
    assert players[0].name == "Alice"
    assert players[0].static_state["team"] == "Blue"
    assert players[0].dynamic_state["score"] == 5


def test_save_and_load_user(tmp_path, save_format):
    file_path = tmp_path / "save.dat"
    save = Save(file_path, save_format)
    user = User(_unique_username(), "secret", "a@b.com")
    user.role = PlayerRole.GROUP_ADMIN
    save.save(user)
    save.flush()

    reloaded = Save(file_path, save_format)
    users = reloaded.load("User")
    assert len(users) == 1
    restored = users[0]
    assert restored.ID == user.ID
    assert restored.username == user.username
    assert restored.hash == user.hash
    assert restored.email == "a@b.com"
    assert restored.role == PlayerRole.GROUP_ADMIN
    assert restored.player.name == user.player.name


def test_save_and_load_game_with_players(tmp_path, save_format):
    file_path = tmp_path / "save.dat"
    save = Save(file_path, save_format)
    game = Game(name="Chess", turn_based=True, style=(ParameterFamily.STATIC, "blitz"))
    p1, p2 = Player("P1"), Player("P2")
    game.join_game_as_player(p1)
    game.join_game_as_player(p2)
    game.start()
    save.save(game)
    save.flush()

    reloaded = Save(file_path, save_format)
    games = reloaded.load(Game)
    assert len(games) == 1
    restored = games[0]
    assert restored.ID == game.ID
    assert restored.name == "Chess"
    assert restored.turn_based is True
    assert restored.game_state == GameState.IN_PROGRESS
    assert [p.ID for p in restored.players] == [p1.ID, p2.ID]
    assert restored.static_state["style"] == "blitz"


def test_save_and_load_group(tmp_path, save_format):
    file_path = tmp_path / "save.dat"
    save = Save(file_path, save_format)
    group = GameGroup("Tournament", type="ranked")
    group.add_game(Game("G1"))
    save.save(group)
    save.flush()

    reloaded = Save(file_path, save_format)
    groups = reloaded.load(GameGroup)
    assert len(groups) == 1
    assert groups[0].name == "Tournament"
    assert groups[0].parameters["type"] == "ranked"
    assert len(groups[0].games) == 1


def test_update_existing_object(tmp_path, save_format):
    file_path = tmp_path / "save.dat"
    save = Save(file_path, save_format)
    player = Player("Alice")
    save.save(player)
    player.name = "Bob"
    save.save(player)
    save.flush()

    reloaded = Save(file_path, save_format)
    players = reloaded.load(Player)
    assert len(players) == 1
    assert players[0].name == "Bob"


def test_no_flush_does_not_persist(tmp_path, save_format):
    file_path = tmp_path / "save.dat"
    save = Save(file_path, save_format)
    save.save(Player("Alice"))
    # No flush

    reloaded = Save(file_path, save_format)
    assert reloaded.load(Player) == []


def test_reset(tmp_path, save_format):
    file_path = tmp_path / "save.dat"
    save = Save(file_path, save_format)
    save.save(Player("Alice"))
    save.flush()
    save.reset()

    reloaded = Save(file_path, save_format)
    assert reloaded.load(Player) == []


def test_load_unsupported_class(tmp_path, save_format):
    save = Save(tmp_path / "save.dat", save_format)
    with pytest.raises(SaveError):
        save.load("Unknown")


def test_incompatible_json_file(tmp_path):
    file_path = tmp_path / "save.json"
    file_path.write_text(json.dumps({"foo": "bar"}), encoding="utf-8")
    with pytest.raises(SaveError):
        Save(file_path, SaveFormat.JSON)


def test_incompatible_sqlite_file(tmp_path):
    import sqlite3

    file_path = tmp_path / "save.db"
    connection = sqlite3.connect(file_path)
    connection.execute("CREATE TABLE wrong (id TEXT)")
    connection.commit()
    connection.close()
    with pytest.raises(SaveError):
        Save(file_path, SaveFormat.SQLITE)
