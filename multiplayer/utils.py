"""
This module provides utility functions for the multiplayer package.
"""
import csv
import random
from importlib import resources

_GAME_CATEGORIES = {
    "cities": "data/cities.csv",
    "countries": "data/countries.csv",
    "rivers": "data/rivers.csv",
    "seas_oceans": "data/seas_oceans.csv",
    "planets_moons": "data/planets_moons.csv",
}

_PLAYER_CATEGORIES = {
    "roman_gods": "data/roman_gods.csv",
    "greek_gods": "data/greek_gods.csv",
    "egyptian_gods": "data/egyptian_gods.csv",
    "european_kings": "data/european_kings.csv",
    "european_queens": "data/european_queens.csv",
}

def get_available_categories(category_type="all"):
    """
    Returns a list of available categories for name suggestions.

    Args:
        category_type (str): "all", "game", or "player".

    Returns:
        A list of strings representing the available categories.
    """
    if category_type == "game":
        return list(_GAME_CATEGORIES.keys())
    if category_type == "player":
        return list(_PLAYER_CATEGORIES.keys())
    return list({**_GAME_CATEGORIES, **_PLAYER_CATEGORIES}.keys())

def _suggest_from_category(category, valid_categories):
    """Internal helper to suggest a name from a specific category."""
    if category not in valid_categories:
        return None
    
    file_path = valid_categories[category]
    
    try:
        with resources.files('multiplayer').joinpath(file_path).open('r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Skip the header row
            items = [row[0] for row in reader]
            if not items:
                return None
            return random.choice(items)
    except (FileNotFoundError, IndexError):
        return None

def suggest_game_name(category=None):
    """
    Suggests a random game name.

    If a category is provided, a name is chosen from that category.
    If no category is provided, a random game-related category is chosen first.

    Args:
        category (str, optional): A category from get_available_categories("game").

    Returns:
        A string containing a random name, or None on failure.
    """
    if category:
        return _suggest_from_category(category, _GAME_CATEGORIES)
    
    random_category = random.choice(list(_GAME_CATEGORIES.keys()))
    return _suggest_from_category(random_category, _GAME_CATEGORIES)

def suggest_player_name(category=None):
    """
    Suggests a random player name.

    If a category is provided, a name is chosen from that category.
    If no category is provided, a random player-related category is chosen first.

    Args:
        category (str, optional): A category from get_available_categories("player").

    Returns:
        A string containing a random name, or None on failure.
    """
    if category:
        return _suggest_from_category(category, _PLAYER_CATEGORIES)
    
    random_category = random.choice(list(_PLAYER_CATEGORIES.keys()))
    return _suggest_from_category(random_category, _PLAYER_CATEGORIES)
