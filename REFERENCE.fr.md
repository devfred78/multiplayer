[English](REFERENCE.md) | [Español](REFERENCE.es.md) | **Français**

# Référence de l'API pour le Module `multiplayer`

Ce document fournit une référence détaillée de l'API publique du module `multiplayer`.

## Classes Principales

Ces classes sont utilisées pour gérer la logique du jeu, que ce soit localement ou sur le serveur.

### `Game(max_players=None, turn_based=False, password=None, **kwargs)`
Représente une session de jeu unique.

*   **`max_players`** (`int`, optionnel) : Le nombre maximum de joueurs pouvant rejoindre. Par défaut, `None` (illimité).
*   **`turn_based`** (`bool`, optionnel) : `True` si le jeu est au tour par tour, `False` pour un jeu simultané. Par défaut, `False`.
*   **`password`** (`str`, optionnel) : Un mot de passe pour protéger cette partie spécifique.
*   **`**kwargs`** : Attributs personnalisés pour la partie (ex: `name="Ma Partie"`).

#### Méthodes
*   `add_player(player, password=None)` : Ajoute un objet `Player` à la partie. Le `password` est requis si la partie est protégée.
*   `remove_player(player_name)` : Retire un joueur de la partie par son nom.
*   `start()` : Démarre la partie.
*   `pause()` : Met la partie en pause.
*   `resume()` : Reprend une partie en pause.
*   `stop()` : Termine la partie.
*   `next_turn()` : Passe au joueur suivant dans une partie au tour par tour.

#### Propriétés
*   **`players`** : Une liste d'objets `Player` dans la partie.
*   **`state`** : Le `GameState` actuel de la partie (ex: `GameState.IN_PROGRESS`).
*   **`custom_state`** : Un dictionnaire pour stocker des données spécifiques au jeu.
*   **`attributes`** : Un dictionnaire d'attributs personnalisés.
*   **`current_player`** : L'objet `Player` actif dans une partie au tour par tour.

---

### `Player(name, **kwargs)`
Représente un joueur.

*   **`name`** (`str`) : Le nom du joueur.
*   **`**kwargs`** : Attributs personnalisés pour le joueur (ex: `score=100`).

#### Propriétés
*   **`name`** : Le nom du joueur.
*   **`attributes`** : Un dictionnaire des attributs personnalisés du joueur.

---

### `GameState` (Enum)
Une énumération pour l'état de la partie.

*   `GameState.PENDING`
*   `GameState.IN_PROGRESS`
*   `GameState.FINISHED`

## Classes Réseau

Ces classes gèrent l'architecture client-serveur.

### `GameServer(host='0.0.0.0', port=65432, password=None, use_tls=False)`
Gère les sessions de jeu et les requêtes réseau.

*   **`host`** (`str`) : L'adresse hôte à laquelle se lier. Utilisez `'0.0.0.0'` pour la rendre accessible sur le réseau local.
*   **`port`** (`int`) : Le port TCP pour écouter les commandes de jeu.
*   **`password`** (`str`, optionnel) : Un mot de passe global pour protéger le serveur.
*   **`use_tls`** (`bool`, optionnel) : Si `True`, active le chiffrement TLS v1.3. Par défaut, `False`.

#### Méthodes
*   `start()` : Démarre le serveur dans un processus d'arrière-plan.
*   `stop()` : Arrête le serveur.

---

### `GameClient(host='127.0.0.1', port=65432, password=None, use_tls=False)`
Le point d'entrée principal pour qu'un client se connecte à un `GameServer`.

*   **`host`** (`str`) : L'adresse IP du serveur.
*   **`port`** (`int`) : Le port TCP du serveur.
*   **`password`** (`str`, optionnel) : Le mot de passe global du serveur.
*   **`use_tls`** (`bool`, optionnel) : Si `True`, le client se connectera en utilisant TLS. Par défaut, `False`.

#### Méthodes
*   `discover_servers(timeout=2)` (méthode statique) : Scanne le réseau local à la recherche d'instances de `GameServer`. Retourne une liste de tuples `(host, port)`.
*   `create_game(**game_options)` : Demande au serveur de créer une nouvelle partie. Retourne un objet proxy `RemoteGame`. Peut inclure un `password` pour la partie.
*   `list_games()` : Retourne un dictionnaire de toutes les parties actives sur le serveur.

---

### `RemoteGame`
Un objet proxy représentant une partie exécutée sur le serveur.

*Vous ne créez généralement pas cet objet directement, mais l'obtenez via `client.create_game()`.*

#### Méthodes
*   `add_player(player, password=None)` : Ajoute un `Player` à la partie distante. Le `password` est requis si la partie est protégée.
*   `set_state(new_state)` : Écrase le dictionnaire `custom_state` de la partie sur le serveur.
*   (Les autres méthodes sont les mêmes que celles de la classe locale `Game`.)

#### Propriétés
*   **`state`** : Retourne le dictionnaire `custom_state` de la partie depuis le serveur. **Note :** Il s'agit d'un changement qui rompt la compatibilité avec la v0.5.2. Cette propriété ne retourne plus l'énumération `GameState`.

## Fonctions Utilitaires

### Suggestions de Noms

#### `register_name_category(category_name, data, category_type)`
Enregistre une nouvelle catégorie personnalisée.

*   **`category_name`** (`str`) : Le nom de la nouvelle catégorie.
*   **`data`** (`list` ou `str`) : Une liste de noms, ou le chemin vers un fichier texte (un nom par ligne).
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
*   **`GameNotFoundError`** : Levée lorsqu'un client demande un `id` de partie qui n'existe pas.
*   **`NetworkError`** : Exception de base pour les problèmes réseau.
*   **`ConnectionError`** : Levée lorsqu'un client ne parvient pas à se connecter au serveur.
*   **`ServerError`** : Levée pour les erreurs génériques signalées par le serveur.
*   **`AuthenticationError`** : Levée pour les échecs d'authentification par mot de passe (serveur et partie).
