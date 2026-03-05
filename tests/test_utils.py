"""
Unit tests for the utility functions.
"""
import pytest
from multiplayer.utils import (
    get_available_categories,
    suggest_game_name,
    suggest_player_name,
)

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
    assert len(all_cats) == len(game_cats) + len(player_cats)
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
    # This is a design choice: suggest_game_name only works with game categories
    # if a category is specified.
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
