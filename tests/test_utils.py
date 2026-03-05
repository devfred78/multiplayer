"""
Unit tests for the utility functions.
"""
import pytest
from multiplayer.utils import (
    get_available_categories,
    suggest_game_name,
    suggest_player_name,
    register_name_category,
    unregister_name_category,
)

# Fixture to ensure custom categories are cleaned up after each test
@pytest.fixture(autouse=True)
def cleanup_custom_categories():
    """Cleans up any registered custom categories after a test."""
    yield
    # This code runs after each test
    all_custom = get_available_categories("all")
    for cat in all_custom:
        unregister_name_category(cat)


def test_get_available_categories():
    """
    Tests that get_available_categories returns the correct lists of categories.
    """
    all_cats = get_available_categories()
    game_cats = get_available_categories("game")
    player_cats = get_available_categories("player")

    assert "cities" in game_cats
    assert "roman_gods" in player_cats
    assert "cities" in all_cats
    assert "roman_gods" in all_cats
    assert "roman_gods" not in game_cats
    assert "cities" not in player_cats

def test_suggest_game_name_random():
    """
    Tests that suggest_game_name with no category returns a valid name.
    """
    name = suggest_game_name()
    assert isinstance(name, str)
    assert len(name) > 0

def test_suggest_game_name_specific_category():
    """
    Tests that suggest_game_name with a specific category returns a valid name.
    """
    name = suggest_game_name("cities")
    assert isinstance(name, str)
    assert len(name) > 0

def test_suggest_game_name_invalid_category():
    """
    Tests that suggest_game_name with an invalid category returns None.
    """
    name = suggest_game_name("invalid_category")
    assert name is None

def test_suggest_game_name_player_category_is_invalid():
    """
    Tests that suggest_game_name with a player-specific category returns None.
    """
    name = suggest_game_name("roman_gods")
    assert name is None

def test_suggest_player_name_random():
    """
    Tests that suggest_player_name with no category returns a valid name.
    """
    name = suggest_player_name()
    assert isinstance(name, str)
    assert len(name) > 0

def test_suggest_player_name_specific_category():
    """
    Tests that suggest_player_name with a specific category returns a valid name.
    """
    name = suggest_player_name("greek_gods")
    assert isinstance(name, str)
    assert len(name) > 0

def test_suggest_player_name_invalid_category():
    """
    Tests that suggest_player_name with an invalid category returns None.
    """
    name = suggest_player_name("invalid_category")
    assert name is None

def test_suggest_player_name_game_category_is_invalid():
    """
    Tests that suggest_player_name with a game-specific category returns None.
    """
    name = suggest_player_name("cities")
    assert name is None

def test_register_and_use_custom_game_category_from_list():
    """
    Tests registering and using a custom game category from a list.
    """
    custom_list = ["MyCoolGame", "AnotherAwesomeGame"]
    register_name_category("custom_games", custom_list, "game")
    
    assert "custom_games" in get_available_categories("game")
    assert "custom_games" in get_available_categories("all")
    
    suggested_name = suggest_game_name("custom_games")
    assert suggested_name in custom_list

def test_register_and_use_custom_player_category_from_file(tmp_path):
    """
    Tests registering and using a custom player category from a file.
    """
    custom_file = tmp_path / "custom_players.txt"
    custom_file.write_text("Hero1\nHero2\n")
    
    register_name_category("heroes", str(custom_file), "player")
    
    assert "heroes" in get_available_categories("player")
    
    suggested_name = suggest_player_name("heroes")
    assert suggested_name in ["Hero1", "Hero2"]

def test_register_invalid_category_type():
    """
    Tests that registering with an invalid type raises a ValueError.
    """
    with pytest.raises(ValueError):
        register_name_category("test", [], "invalid_type")

def test_unregister_custom_category():
    """
    Tests that a custom category can be unregistered.
    """
    register_name_category("temp_cat", ["a", "b"], "game")
    assert "temp_cat" in get_available_categories("game")
    
    result = unregister_name_category("temp_cat")
    assert result is True
    assert "temp_cat" not in get_available_categories("game")

def test_unregister_non_existent_category():
    """
    Tests that unregistering a non-existent category returns False.
    """
    result = unregister_name_category("non_existent")
    assert result is False

def test_unregister_builtin_category_is_not_allowed():
    """
    Tests that built-in categories cannot be unregistered.
    """
    assert "cities" in get_available_categories("game")
    result = unregister_name_category("cities")
    assert result is False
    assert "cities" in get_available_categories("game")
