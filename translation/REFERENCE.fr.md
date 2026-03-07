[English](../REFERENCE.md) | [Español](REFERENCE.es.md) | **Français**

# Référence de l'API pour le Module `multiplayer`

Ce document fournit une référence détaillée de l'API publique du module `multiplayer`.

## Classes Principales

### `Game(max_players=None, turn_based=False, password=None, **kwargs)`
Représente une session de jeu unique.

*   **`max_players`** (`int`, optionnel) : Le nombre maximum de joueurs.
*   **`turn_based`** (`bool`, optionnel) : `True` si le jeu est au tour par tour.
*   **`password`** (`str`, optionnel) : Un mot de passe pour protéger cette partie.
*   **`**kwargs`** : Attributs personnalisés pour la partie.

#### Propriétés
*   **`state`**: Le `GameState` actuel de la partie (ex: `GameState.IN_PROGRESS`).
*   **`custom_state`**: Un dictionnaire pour stocker des données spécifiques au jeu.

---

### `Player(name, **kwargs)`
Représente un joueur.

*   **`name`** (`str`) : Le nom du joueur.
*   **`**kwargs`** : Attributs personnalisés pour le joueur.

---

### `GameState` (Enum)
*   `GameState.PENDING`
*   `GameState.IN_PROGRESS`
*   `GameState.FINISHED`

## Classes Réseau

### `GameServer(host='0.0.0.0', port=65432, password=None, use_tls=False)`
Gère les sessions de jeu et les requêtes réseau.

*   **`password`** (`str`, optionnel) : Un mot de passe global pour protéger le serveur.
*   **`use_tls`** (`bool`, optionnel) : Si `True`, active le chiffrement TLS v1.3.

---

### `GameClient(host='127.0.0.1', port=65432, password=None, use_tls=False)`
Le point d'entrée pour qu'un client se connecte à un `GameServer`.

*   **`password`** (`str`, optionnel) : Le mot de passe global du serveur.
*   **`use_tls`** (`bool`, optionnel) : Si `True`, le client se connectera en utilisant TLS.

#### Méthodes
*   `discover_servers(timeout=2)` (méthode statique) : Scanne le réseau local à la recherche d'instances de `GameServer`.
*   `create_game(**game_options)` : Demande au serveur de créer une nouvelle partie. Retourne un objet proxy `RemoteGame`.
*   `list_games()` : Retourne un dictionnaire de toutes les parties actives (non terminées) sur le serveur.

---

### `RemoteGame`
Un objet proxy représentant une partie exécutée sur le serveur.

#### Méthodes
*   `add_player(player, password=None)` : Ajoute un `Player` à la partie distante.
*   `set_state(new_state)` : Écrase le dictionnaire `custom_state` de la partie sur le serveur.

#### Propriétés
*   **`state`**: Retourne un dictionnaire contenant à la fois le `GameState` et l'état personnalisé. Exemple : `{'status': 'in_progress', 'custom': {'score': 100}}`.

## Fonctions Utilitaires
... (Contenu correct)

## Exceptions
... (Contenu correct)
