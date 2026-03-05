"""
This module provides utility functions for the multiplayer package.
"""
import csv
import random
from importlib import resources

def suggest_game_name():
    """
    Suggests a random game name from a list of major world cities.

    This function reads from a data file included with the package.

    Returns:
        A string containing a city name, or None if the data cannot be loaded.
    """
    try:
        # Safely access the data file packaged with the module
        with resources.files('multiplayer').joinpath('data/cities.csv').open('r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Skip the header row
            cities = [row[0] for row in reader]
            if not cities:
                return None
            return random.choice(cities)
    except (FileNotFoundError, IndexError):
        # Fallback in case the file is missing or empty
        return None

def suggest_player_name():
    """
    Suggests a random player name from a list of Roman gods.

    This function reads from a data file included with the package.

    Returns:
        A string containing a god's name, or None if the data cannot be loaded.
    """
    try:
        # Safely access the data file packaged with the module
        with resources.files('multiplayer').joinpath('data/roman_gods.csv').open('r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Skip the header row
            gods = [row[0] for row in reader]
            if not gods:
                return None
            return random.choice(gods)
    except (FileNotFoundError, IndexError):
        # Fallback in case the file is missing or empty
        return None
