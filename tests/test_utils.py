from multiplayer.utils import suggest_game_name, suggest_player_name, get_available_categories, register_name_category, unregister_name_category

def test_suggestions():
    name = suggest_game_name()
    assert isinstance(name, str)
    assert len(name) > 0
    
    p_name = suggest_player_name()
    assert isinstance(p_name, str)
    assert len(p_name) > 0

def test_categories():
    cats = get_available_categories("game")
    assert "cities" in cats
    assert "countries" in cats
    
    p_cats = get_available_categories("player")
    assert "roman_gods" in p_cats

def test_custom_category():
    register_name_category("fruits", ["Apple", "Banana", "Cherry"], "game")
    assert "fruits" in get_available_categories("game")
    
    suggestion = suggest_game_name("fruits")
    assert suggestion in ["Apple", "Banana", "Cherry"]
    
    unregister_name_category("fruits")
    assert "fruits" not in get_available_categories("game")
