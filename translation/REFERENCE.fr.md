[English](../REFERENCE.md) | [Español](REFERENCE.es.md) | **Français**

# Référence de l'API pour le Module `multiplayer`

Ce document fournit une référence détaillée de l'API publique du module `multiplayer`.

## Classes Principales

### `Game(max_players=None, turn_based=False, password=None, max_observers=None, **kwargs)`
Représente une session de jeu unique.

*   **`max_players`** (`int`, optionnel) : Le nombre maximum de joueurs.
*   **`max_observers`** (`int`, optionnel) : Le nombre maximum d'observateurs.
*   **`turn_based`** (`bool`, optionnel) : `True` si le jeu est au tour par tour.
*   **`password`** (`str`, optionnel) : Un mot de passe pour protéger cette partie.
*   **`**kwargs`** : Attributs personnalisés pour la partie.

#### Méthodes
*   `add_player(player, password=None)` : Ajoute un objet `Player` à la partie.
*   `remove_player(player_name)` : Retire un joueur de la partie par son nom.
*   `add_observer(observer)` : Ajoute un objet `Observer` à la partie.
*   `remove_observer(observer_name)` : Retire un observateur de la partie par son nom.
*   `start()` : Démarre la partie.
*   `pause()` : Met la partie en pause.
*   `resume()` : Reprend une partie en pause.
*   `stop()` : Termine la partie.
*   `next_turn()` : Passe au joueur suivant.

#### Propriétés
*   **`players`**: Une liste d'objets `Player`.
*   **`observers`**: Une liste d'objets `Observer`.
*   **`state`**: Le `GameState` actuel de la partie.
*   **`custom_state`**: Un dictionnaire pour les données spécifiques au jeu.
*   **`attributes`**: Un dictionnaire d'attributs personnalisés.
*   **`current_player`**: L'objet `Player` actif.

---

### `Player(name, **kwargs)`
Représente un joueur.

*   **`name`** (`str`) : Le nom du joueur.
*   **`**kwargs`** : Attributs personnalisés pour le joueur.

---

### `Observer(name, **kwargs)`
Représente un observateur.

*   **`name`** (`str`) : Le nom de l'observateur.
*   **`**kwargs`** : Attributs personnalisés pour l'observateur.

#### Propriétés
*   **`name`**: Le nom de l'observateur.
*   **`attributes`**: Un dictionnaire d'attributs personnalisés.

---

### `GameState` (Enum)
*   `GameState.PENDING`, `GameState.IN_PROGRESS`, `GameState.FINISHED`

## Classes Réseau

### `GameServer(host='0.0.0.0', port=65432, password=None, admin_password=None, use_tls=False)`
Gère les sessions de jeu et les requêtes réseau.

*   **`password`** (`str`, optionnel) : Un mot de passe global pour protéger le serveur.
*   **`admin_password`** (`str`, optionnel) : Un mot de passe pour l'accès administrateur.
*   **`use_tls`** (`bool`, optionnel) : Si `True`, active le chiffrement TLS v1.3.

#### Méthodes
*   `start()`: Démarre le serveur.
*   `stop()`: Arrête le serveur.

---

### `GameAdmin(host='127.0.0.1', port=65432, admin_password=None, use_tls=False)`
Une classe client pour les administrateurs pour gérer un `GameServer`.

*   **`admin_password`** (`str`, optionnel) : Le mot de passe administrateur du serveur.
*   **`use_tls`** (`bool`, optionnel) : Si `True`, le client se connectera en utilisant TLS.

#### Méthodes
*   `get_server_info()` : Retourne les infos du serveur (nombre de parties, IDs actifs).
*   `list_games()` : Liste toutes les parties actives.
*   `kick_player(game_id, player_name)` : Expulse un joueur d'une partie.
*   `kick_observer(game_id, observer_name)` : Expulse un observateur d'une partie.
*   `stop_server()` : Demande l'arrêt du serveur.
*   `restart_server()` : Demande le redémarrage du serveur (efface toutes les parties en cours).

---

### `GameClient(host='127.0.0.1', port=65432, password=None, use_tls=False)`
Le point d'entrée pour qu'un client se connecte à un `GameServer`.

*   **`password`** (`str`, optionnel) : Le mot de passe global du serveur.
*   **`use_tls`** (`bool`, optionnel) : Si `True`, le client se connectera en utilisant TLS.

#### Méthodes
*   `discover_servers(timeout=2)` (méthode statique) : Scanne le réseau local à la recherche d'instances de `GameServer`.
*   `create_game(**game_options)` : Demande au serveur de créer une nouvelle partie. Retourne un objet proxy `RemoteGame`.
*   `list_games()` : Retourne un dictionnaire de toutes les parties actives (non terminées).

---

### `RemoteGame`
Un objet proxy représentant une partie exécutée sur le serveur.

#### Méthodes
*   `add_player(player, password=None)` : Ajoute un `Player` à la partie distante.
*   `add_observer(observer)` : Ajoute un `Observer` à la partie distante.
*   `set_state(new_state)` : Écrase le dictionnaire `custom_state` de la partie sur le serveur.

#### Propriétés
*   **`state`**: Retourne un dictionnaire contenant à la fois le `GameState` et l'état personnalisé. Exemple : `{'status': 'in_progress', 'custom': {'score': 100}}`.
*   **`observers`**: Retourne une liste des noms des observateurs dans la partie.

## Fonctions Utilitaires

### Suggestions de Noms

#### `register_name_category(category_name, data, category_type)`
Enregistre une nouvelle catégorie personnalisée.

*   **`category_name`** (`str`) : Le nom de la nouvelle catégorie.
*   **`data`** (`list` ou `str`) : Une liste de noms, ou le chemin vers un fichier texte.
*   **`category_type`** (`str`) : `"game"` ou `"player"`.

---

#### `unregister_name_category(category_name)`
Supprime une catégorie personnalisée. Retourne `True` en cas de succès.

---

#### `get_available_categories(category_type="all")`
Retourne une liste des catégories de suggestion de noms disponibles.

*   **`category_type`** (`str`) : `"all"`, `"game"`, ou `"player"`.

---

#### `suggest_game_name(category=None)`
Suggère un nom aléatoire pour une partie.

---

#### `suggest_player_name(category=None)`
Suggère un nom aléatoire pour un joueur.

## Exceptions

*   **`MultiplayerError`** : Exception de base pour toutes les erreurs du module.
*   **`GameLogicError`** : Pour les erreurs de logique de jeu.
*   **`PlayerLimitReachedError`** : Levée lors de l'ajout d'un joueur à une partie pleine.
*   **`ObserverLimitReachedError`** : Levée lors de l'ajout d'un observateur à une partie qui a atteint sa limite d'observateurs.
*   **`GameNotFoundError`** : Levée lorsqu'un client demande un `id` de partie qui n'existe pas.
*   **`NetworkError`** : Exception de base pour les problèmes réseau.
*   **`ConnectionError`** : Levée lorsqu'un client ne parvient pas à se connecter au serveur.
*   **`ServerError`** : Levée pour les erreurs g�