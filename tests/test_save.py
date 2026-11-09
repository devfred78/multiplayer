import json
import uuid

import pytest

from multiplayer import UserRole, GameState, ParameterFamily, SaveFormat
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
    user.role = UserRole.GROUP_ADMIN
    user.players_id.extend(["player-1", "player-2"])
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
    assert restored.role == UserRole.GROUP_ADMIN
    assert restored.players_id == ["player-1", "player-2"]


def test_save_user_cleans_inactive_players(tmp_path, save_format):
    file_path = tmp_path / "save.dat"
    save = Save(file_path, save_format)
    waiting, active, finished, mixed, grouped = (
        Player(name) for name in ("Waiting", "Active", "Finished", "Mixed", "Grouped")
    )
    running = Game("Running")
    running.join_game_as_player(active)
    running.join_game_as_observer(mixed)
    over = Game("Over")
    over.join_game_as_player(finished)
    over.join_game_as_player(mixed)
    over.start()
    over.stop()
    group = GameGroup("Group")
    in_group = Game("In group")
    in_group.join_game_as_player(grouped)
    group.add_game(in_group)
    save.save(running)
    save.save(over)
    save.save(group)

    user = User(_unique_username(), "secret")
    user.players_id.extend(p.ID for p in (waiting, active, finished, mixed, grouped))
    save.save(user)

    expected = [waiting.ID, active.ID, mixed.ID, grouped.ID]
    assert user.players_id == expected
    save.flush()
    assert Save(file_path, save_format).load(User)[0].players_id == expected


def test_load_user_from_older_save_file(tmp_path):
    file_path = tmp_path / "save.json"
    username = _unique_username()
    content = {
        "Player": {},
        "User": {
            "user-1": {
                "id": "user-1",
                "username": username,
                "hash": "hash",
                "email": "",
                "role": "player",
                "groups_id": [],
                "player": {"id": "player-1", "name": username},
            }
        },
        "Game": {},
        "GameGroup": {},
    }
    file_path.write_text(json.dumps(content), encoding="utf-8")
    assert Save(file_path, SaveFormat.JSON).load(User)[0].players_id == ["player-1"]


def test_save_and_load_game_with_players(tmp_path, save_format):
    file_path = tmp_path / "save.dat"
    save = Save(file_path, save_format)
    game = Game(name="Chess", turn_based=True, min_players=2, style=(ParameterFamily.STATIC, "blitz"))
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
    assert restored.min_players == 2
    assert restored.game_state == GameState.IN_PROGRESS
    assert restored.players == (p1.ID, p2.ID)
    assert restored.current_player == p1.ID
    assert restored.static_state["style"] == "blitz"


def test_loaded_games_are_registered(tmp_path, save_format):
    file_path = tmp_path / "save.dat"
    save = Save(file_path, save_format)
    game = Game("Restored")
    save.save(game)
    save.flush()

    restored = Save(file_path, save_format).load(Game)[0]
    assert restored is not game
    assert Game.get_by_id(game.ID) is restored
    group = GameGroup("Group")
    group.add_game(game.ID)
    assert group.games == (game.ID,)


def test_loaded_players_are_registered(tmp_path, save_format):
    file_path = tmp_path / "save.dat"
    save = Save(file_path, save_format)
    player = Player("Restored")
    save.save(player)
    save.flush()

    restored = Save(file_path, save_format).load(Player)[0]
    assert restored is not player
    assert Player.get_by_id(player.ID) is restored
    game = Game()
    game.join_game_as_player(player.ID)
    assert game.players == (player.ID,)


def test_load_game_from_older_save_file(tmp_path):
    file_path = tmp_path / "save.json"
    content = {
        "Player": {},
        "User": {},
        "Game": {
            "game-1": {
                "id": "game-1",
                "name": "Old",
                "hash": None,
                "observer_hash": None,
                "turn_based": True,
                "players": [
                    {"id": "player-1", "name": "P1", "static_state": {}, "dynamic_state": {}},
                    {"id": "player-2", "name": "P2", "static_state": {}, "dynamic_state": {}},
                ],
                "observers": [{"id": "watcher-1", "name": "W", "static_state": {}, "dynamic_state": {}}],
                "game_state": GameState.PENDING.value,
                "static_state": {},
                "dynamic_state": {},
            }
        },
        "GameGroup": {},
    }
    file_path.write_text(json.dumps(content), encoding="utf-8")
    game = Save(file_path, SaveFormat.JSON).load(Game)[0]
    assert game.players == ("player-1", "player-2")
    assert game.observers == ("watcher-1",)


def test_save_and_load_group(tmp_path, save_format):
    file_path = tmp_path / "save.dat"
    save = Save(file_path, save_format)
    group = GameGroup("Tournament", password="group-secret", type="ranked")
    game = Game("G1")
    group.add_game(game)
    save.save(group)
    save.flush()

    reloaded = Save(file_path, save_format)
    groups = reloaded.load(GameGroup)
    assert len(groups) == 1
    assert groups[0].name == "Tournament"
    assert groups[0].hash == group.hash
    assert groups[0].check_password("group-secret") is True
    assert groups[0].check_password("wrong-secret") is False
    assert groups[0].parameters["type"] == "ranked"
    assert groups[0].games == (game.ID,)


def test_group_is_saved_with_game_ids(tmp_path):
    file_path = tmp_path / "save.json"
    save = Save(file_path, SaveFormat.JSON)
    group = GameGroup("Tournament")
    games = [Game("G1"), Game("G2")]
    for game in games:
        group.add_game(game)
    save.save(group)
    save.flush()

    content = json.loads(file_path.read_text(encoding="utf-8"))
    assert content["GameGroup"][group.ID]["games"] == [games[0].ID, games[1].ID]


def test_load_group_from_older_save_file(tmp_path):
    file_path = tmp_path / "save.json"
    embedded = {
        "id": "game-1",
        "name": "Embedded",
        "players": ["player-1"],
        "observers": [],
        "game_state": GameState.PENDING.value,
        "static_state": {},
        "dynamic_state": {},
    }
    content = {
        "Player": {},
        "User": {},
        "Game": {},
        "GameGroup": {
            "group-1": {"id": "group-1", "name": "Old group", "games": [embedded]},
        },
    }
    file_path.write_text(json.dumps(content), encoding="utf-8")
    reloaded = Save(file_path, SaveFormat.JSON)
    assert reloaded.load(GameGroup)[0].games == ("game-1",)
    games = reloaded.load(Game)
    assert [game.ID for game in games] == ["game-1"]
    assert games[0].players == ("player-1",)


def test_save_and_load_server_config(tmp_path, save_format):
    file_path = tmp_path / "save.dat"
    save = Save(file_path, save_format)
    config = {
        "name": "Configured server",
        "hidden": True,
        "server_hash": "bcrypt-hash",
        "orphan_games_allowed": False,
    }
    save.save_server_config(config)
    save.flush()

    reloaded = Save(file_path, save_format)
    assert reloaded.load_server_config() == config


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
