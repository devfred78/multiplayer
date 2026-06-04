"""Utility functions for name suggestions."""
import random
import csv
from pathlib import Path
from typing import List, Dict, Any

_CATEGORIES: Dict[str, Dict[str, Any]] = {}

def _load_default_categories() -> None:
    data_dir = Path(__file__).parent / "data"
    game_cats = ["cities", "countries", "rivers", "seas_oceans", "planets_moons"]
    player_cats = ["roman_gods", "greek_gods", "egyptian_gods", "european_kings", "european_queens"]
    
    for cat in game_cats:
        path = data_dir / f"{cat}.csv"
        if path.exists():
            register_name_category(cat, path, "game")
            
    for cat in player_cats:
        path = data_dir / f"{cat}.csv"
        if path.exists():
            register_name_category(cat, path, "player")

def register_name_category(category_name: str, data: List[str] | str | Path, category_type: str) -> None:
    """Registers a new name category for suggestions.

    Args:
        category_name (str): The name of the new category.
        data (list, str or Path): A list of names, or a path to a text/CSV file
            (one name per line, or the first column of the CSV).
        category_type (str): Either "game" or "player".
    """
    names: List[str] = []
    if isinstance(data, (str, Path)):
        path = Path(data)
        if path.exists():
            with open(path, mode="r", encoding="utf-8") as f:
                # Handle simple text or CSV (first column)
                reader = csv.reader(f)
                for row in reader:
                    if row:
                        names.append(row[0].strip())
    elif isinstance(data, list):
        names = [str(n).strip() for n in data]
    
    # Normalize: unique and non-empty
    names = sorted(list(set(n for n in names if n)))
    
    _CATEGORIES[category_name] = {
        "type": category_type,
        "names": names
    }

def unregister_name_category(category_name: str) -> bool:
    """Removes a previously registered category.

    Args:
        category_name (str): The name of the category to remove.

    Returns:
        bool: True if the category was found and removed, False otherwise.
    """
    if category_name in _CATEGORIES:
        del _CATEGORIES[category_name]
        return True
    return False

def get_available_categories(category_type: str = "all") -> List[str]:
    """Returns available categories for a given type."""
    if category_type == "all":
        return list(_CATEGORIES.keys())
    return [k for k, v in _CATEGORIES.items() if v["type"] == category_type]

def suggest_game_name(category: str | None = None) -> str:
    """Suggests a random game name."""
    if category is None:
        cats = get_available_categories("game")
        if not cats:
            return "New Game"
        category = random.choice(cats)
    
    if category in _CATEGORIES and _CATEGORIES[category]["type"] == "game":
        names = _CATEGORIES[category]["names"]
        return random.choice(names) if names else "New Game"
    return "New Game"

def suggest_player_name(category: str | None = None) -> str:
    """Suggests a random player name."""
    if category is None:
        cats = get_available_categories("player")
        if not cats:
            return "New Player"
        category = random.choice(cats)
    
    if category in _CATEGORIES and _CATEGORIES[category]["type"] == "player":
        names = _CATEGORIES[category]["names"]
        return random.choice(names) if names else "New Player"
    return "New Player"

# Initialize
_load_default_categories()
