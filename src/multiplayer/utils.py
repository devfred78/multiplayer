"""
This module provides utility functions for the multiplayer package.
"""
import csv
import random
from importlib import resources
from pathlib import Path

# --- Built-in Categories ---
_BUILTIN_GAME_CATEGORIES = {
    "cities": "data/cities.csv",
    "countries": "data/countries.csv",
    "rivers": "data/rivers.csv",
    "seas_oceans": "data/seas_oceans.csv",
    "planets_moons": "data/planets_moons.csv",
}

_BUILTIN_PLAYER_CATEGORIES = {
    "roman_gods": "data/roman_gods.csv",
    "greek_gods": "data/greek_gods.csv",
    "egyptian_gods": "data/egyptian_gods.csv",
    "european_kings": "data/european_kings.csv",
    "european_queens": "data/european_queens.csv",
}

# --- Custom Categories (user-defined) ---
_CUSTOM_GAME_CATEGORIES = {}
_CUSTOM_PLAYER_CATEGORIES = {}

def register_name_category(category_name, data, category_type):
    """
    Registers a new custom category for name suggestions.

    Args:
        category_name (str): The name for the new category.
        data (list or str or Path): A list of strings, or a path to a CSV/text file.
                                    The file should have one name per line.
        category_type (str): "game" or "player".
    """
    if category_type == "game":
        _CUSTOM_GAME_CATEGORIES[category_name] = data
    elif category_type == "player":
        _CUSTOM_PLAYER_CATEGORIES[category_name] = data
    else:
        raise ValueError("category_type must be 'game' or 'player'")

def unregister_name_category(category_name):
    """
    Unregisters a custom category. Built-in categories cannot be removed.

    Args:
        category_name (str): The name of the custom category to remove.

    Returns:
        bool: True if the category was found and removed, False otherwise.
    """
    if category_name in _CUSTOM_GAME_CATEGORIES:
        del _CUSTOM_GAME_CATEGORIES[category_name]
        return True
    if category_name in _CUSTOM_PLAYER_CATEGORIES:
        del _CUSTOM_PLAYER_CATEGORIES[category_name]
        return True
    return False

def get_available_categories(category_type="all"):
    """
    Returns a list of available categories, including custom ones.

    Args:
        category_type (str): "all", "game", or "player".

    Returns:
        A list of strings representing the available categories.
    """
    if category_type == "game":
        return list(_BUILTIN_GAME_CATEGORIES.keys()) + list(_CUSTOM_GAME_CATEGORIES.keys())
    if category_type == "player":
        return list(_BUILTIN_PLAYER_CATEGORIES.keys()) + list(_CUSTOM_PLAYER_CATEGORIES.keys())
    return list({**_BUILTIN_GAME_CATEGORIES, **_BUILTIN_PLAYER_CATEGORIES, **_CUSTOM_GAME_CATEGORIES, **_CUSTOM_PLAYER_CATEGORIES}.keys())

def _get_names_from_source(source):
    """Internal helper to load names from a list, a file path, or a package resource."""
    if isinstance(source, list):
        return source
    
    # Ensure source uses correct separators for the OS
    source_path = Path(source)
    
    # 1. Try relative to this file first (most reliable in both dev and production layouts)
    try:
        current_file_dir = Path(__file__).parent.resolve()
        path = (current_file_dir / source_path).resolve()
        if path.is_file():
            with open(path, 'r', encoding='utf-8') as f:
                if str(source).endswith('.csv'):
                    reader = csv.reader(f)
                    try:
                        next(reader)  # Assume header
                        return [row[0] for row in reader if row]
                    except StopIteration:
                        return []
                else:
                    return [line.strip() for line in f if line.strip()]
    except Exception:
        pass

    # 2. Try as an absolute or CWD-relative file path
    try:
        if source_path.is_file():
            with open(source_path, 'r', encoding='utf-8') as f:
                if str(source).endswith('.csv'):
                    reader = csv.reader(f)
                    try:
                        next(reader)
                        return [row[0] for row in reader if row]
                    except StopIteration:
                        return []
                else:
                    return [line.strip() for line in f if line.strip()]
    except Exception:
        pass

    # 3. Fallback to package resource (standard PEP 302/modern way)
    try:
        # Try finding it in the multiplayer.data subpackage first
        try:
            package_path = resources.files('multiplayer.data')
            # If we are looking for 'data/cities.csv', and we are in 'multiplayer.data',
            # we just need 'cities.csv'
            if 'data' in source_path.parts:
                file_name = source_path.name
                resource_path = package_path.joinpath(file_name)
            else:
                resource_path = package_path.joinpath(*source_path.parts)
        except (ImportError, ModuleNotFoundError, ValueError):
            # Fallback to main package
            package_path = resources.files('multiplayer')
            resource_path = package_path.joinpath(*source_path.parts)
            
        if resource_path.is_file():
            with resource_path.open('r', encoding='utf-8') as f:
                if str(source).endswith('.csv'):
                    reader = csv.reader(f)
                    try:
                        next(reader)  # Assume header
                        return [row[0] for row in reader if row]
                    except StopIteration:
                        return []
                else:
                    return [line.strip() for line in f if line.strip()]
    except Exception:
        pass

    return None

def _suggest_from_category(category, valid_builtin_cats, valid_custom_cats):
    """Internal helper to suggest a name from a specific category."""
    if category in valid_custom_cats:
        source = valid_custom_cats[category]
    elif category in valid_builtin_cats:
        source = valid_builtin_cats[category]
    else:
        return None
        
    names = _get_names_from_source(source)
    if not names:
        return None
    return random.choice(names)

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
        return _suggest_from_category(category, _BUILTIN_GAME_CATEGORIES, _CUSTOM_GAME_CATEGORIES)
    
    all_game_cats = {**_BUILTIN_GAME_CATEGORIES, **_CUSTOM_GAME_CATEGORIES}
    if not all_game_cats:
        return None
    random_category = random.choice(list(all_game_cats.keys()))
    return _suggest_from_category(random_category, _BUILTIN_GAME_CATEGORIES, _CUSTOM_GAME_CATEGORIES)

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
        return _suggest_from_category(category, _BUILTIN_PLAYER_CATEGORIES, _CUSTOM_PLAYER_CATEGORIES)
    
    all_player_cats = {**_BUILTIN_PLAYER_CATEGORIES, **_CUSTOM_PLAYER_CATEGORIES}
    if not all_player_cats:
        return None
    random_category = random.choice(list(all_player_cats.keys()))
    return _suggest_from_category(random_category, _BUILTIN_PLAYER_CATEGORIES, _CUSTOM_PLAYER_CATEGORIES)
