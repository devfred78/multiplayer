import tomllib
import requests
import pytest
from pathlib import Path

def test_pyproject_classifiers_valid():
    """
    Vérifie que tous les classifieurs présents dans pyproject.toml sont valides
    selon la liste officielle de PyPI.
    """
    # 1. Charger pyproject.toml
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        pyproject_data = tomllib.load(f)
    
    project_metadata = pyproject_data.get("project", {})
    classifiers = project_metadata.get("classifiers", [])
    
    if not classifiers:
        pytest.skip("Aucun classifieur trouvé dans pyproject.toml")
    
    # 2. Récupérer la liste officielle des classifieurs de PyPI
    # Utilisation de l'API textuelle de PyPI pour l'action list_classifiers
    pypi_url = "https://pypi.org/pypi?%3Aaction=list_classifiers"
    try:
        response = requests.get(pypi_url, timeout=10)
        response.raise_for_status()
        official_classifiers = set(line.strip() for line in response.text.splitlines() if line.strip())
    except requests.RequestException as e:
        pytest.fail(f"Impossible de récupérer la liste officielle des classifieurs PyPI : {e}")

    # 3. Vérifier chaque classifieur
    invalid_classifiers = [c for c in classifiers if c not in official_classifiers]
    
    assert not invalid_classifiers, f"Classifieurs invalides trouvés : {invalid_classifiers}"
