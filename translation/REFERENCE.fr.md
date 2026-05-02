[English](../REFERENCE.md) | [Español](REFERENCE.es.md) | **Français**

# Référence de l'API pour le Module `multiplayer`

Ce document fournit une référence détaillée de l'API publique du module `multiplayer`.

## Classes Principales

Ces classes sont utilisées pour gérer la logique de jeu, que ce soit localement ou sur le serveur.

### `Game(name=None, max_players=None, turn_based=False, password=None, observer_password=None, max_observers=None, **kwargs)`
Représente une session de jeu unique.

*   **`name`** (`str`, optionnel) : Le nom de la session de jeu. Par défaut `None`.
*   **`max_players`** (`int`, optionnel) : Le nombre maximum de joueurs pouvant rejoindre. Par défaut `None` (illimité).
*   **`max_observers`** (`int`, optionnel) : Le nombre maximum d'observateurs pouvant rejoindre. Par défaut `None` (illimité).
*   **`turn_based`** (`bool`, optionnel) : `True` si le jeu est au tour par tour, `False` pour un jeu simultané. Par défaut `False`.
*   **`password`** (`str`, optionnel) : Un mot de passe pour protéger cette partie (utilisé pour les joueurs, et pour les observateurs si `observer_password` n'est pas défini).
*   **`observer_password`** (`str`, optionnel) : Un mot de passe spécifiquement pour les observateurs de cette partie.
*   **`**kwargs`** : Attributs personnalisés pour la partie (ex: `difficulty="hard"`).

#### Méthodes
*   `add_player(player, password=None)` : Ajoute un objet `Player` à la partie. Le mot de passe est requis si la partie est protégée.
*   `remove_player(player_id)` : Retire un joueur de la partie par son ID.
*   `add_observer(observer, password=None)` : Ajoute un objet `Observer` à la partie. Le mot de passe est requis si `observer_password` (ou `password`) est défini.
*   `remove_observer(observer_id)` : Retire un observateur de la partie par son ID.
*   `start()` : Démarre la partie.
*   `pause()` : Met la partie en pause.
*   `resume()` : Reprend une partie en pause.
*   `stop()` : Termine la partie.
*   `next_turn()` : Passe au joueur suivant dans un jeu au tour par tour.

#### Propriétés
*   **`ID`**: L'ID unique de la session de jeu (lecture seule).
*   **`players`**: Une liste d'objets `Player` dans la partie.
*   **`observers`**: Une liste d'objets `Observer` dans la partie.
*   **`state`**: Le `GameState` actuel de la partie (ex: `GameState.IN_PROGRESS`).
*   **`custom_state`**: Un dictionnaire pour stocker les données spécifiques au jeu.
*   **`attributes`**: Un dictionnaire d'attributs personnalisés.
*   **`current_player`**: L'objet `Player` actif dans un jeu au tour par tour.

---

### `Player(name, **kwargs)`
Représente un joueur.

*   **`name`** (`str`) : Le nom du joueur.
*   **`**kwargs`** : Attributs personnalisés pour le joueur (ex: `score=100`).

#### Propriétés
*   **`ID`**: L'ID unique du joueur (lecture seule).
*   **`name`**: Le nom du joueur.
*   **`attributes`**: Un dictionnaire des attributs personnalisés du joueur.

---

### `Observer(name, **kwargs)`
Représente un observateur.

*   **`name`** (`str`) : Le nom de l'observateur.
*   **`**kwargs`** : Attributs personnalisés pour l'observateur.

#### Propriétés
*   **`ID`**: L'ID unique de l'observateur (lecture seule).
*   **`name`**: Le nom de l'observateur.
*   **`attributes`**: Un dictionnaire des attributs personnalisés de l'observateur.

---

### `GameGroup(name, admin_password=None, **kwargs)`
Représente un groupe de parties sur un serveur.

*   **`name`** (`str`) : Le nom du groupe.
*   **`admin_password`** (`str`, optionnel) : Un mot de passe pour les actions administratives sur ce groupe.
*   **`**kwargs`** : Attributs supplémentaires pour le groupe.

#### Méthodes
*   `add_game(game)` : Ajoute un objet `Game` au groupe.
*   `remove_game(game_id)` : Retire une partie du groupe par son ID.

#### Propriétés
*   **`ID`**: L'ID unique du groupe (lecture seule).
*   **`name`**: Le nom du groupe.
*   **`games`**: Une liste d'objets `Game` actuellement dans le groupe.
*   **`attributes`**: Un dictionnaire d'attributs personnalisés pour le groupe.

---

### `GameState` (Enum)
Une énumération pour l'état de la partie.

*   `GameState.PENDING`
*   `GameState.IN_PROGRESS`
*   `GameState.FINISHED`

## Classes Réseau

Ces classes gèrent l'architecture client-serveur.

### `GameServer(host='0.0.0.0', port=65432, password=None, admin_password=None, use_tls=False, tls_domain="localhost", tls_cert=None, tls_key=None, tls_self_signed=True, logging_host=None, logging_port=None, name=None)`
Gère les sessions de jeu et les requêtes réseau.

*   **`host`** (`str`) : L'adresse de l'hôte sur laquelle s'écouter. Utilisez `'0.0.0.0'` pour le rendre accessible sur le réseau local.
*   **`port`** (`int`) : Le port TCP sur lequel écouter les commandes de jeu.
*   **`password`** (`str`, optionnel) : Un mot de passe global pour protéger le serveur.
*   **`admin_password`** (`str`, optionnel) : Un mot de passe pour l'accès administrateur.
*   **`use_tls`** (`bool`, optionnel) : Si `True`, active le chiffrement TLS v1.3 pour toutes les communications. Par défaut `False`.
*   **`tls_domain`** (`str`, optionnel) : Nom de domaine à inclure dans le certificat généré. Par défaut `"localhost"`.
*   **`tls_cert`** (`str`, optionnel) : Chemin vers un fichier de certificat PEM. Ce fichier doit soit être une "chaîne complète" (incluant le certificat de domaine et les certificats intermédiaires), soit être accompagné d'un fichier de "chaîne" correspondant dans le même répertoire.
*   **`tls_key`** (`str`, optionnel) : Chemin vers un fichier de clé privée PEM.
*   **`tls_self_signed`** (`bool`, optionnel) : Si `True`, génère un certificat auto-signé si `tls_cert` ou `tls_key` est manquant. Par défaut `True`.
*   **`logging_host`** (`str`, optionnel) : L'adresse de l'hôte d'un serveur de logging.
*   **`logging_port`** (`int`, optionnel) : Le port du serveur de logging.
*   **`name`** (`str`, optionnel) : Un nom pour l'instance du serveur.

#### Méthodes
*   `start()` : Démarre le serveur dans un processus d'arrière-plan.
*   `stop()` : Arrête le serveur.

---

### `ServerAdmin(host='127.0.0.1', port=65432, admin_password=None, use_tls=False)`
Une classe client pour les administrateurs pour gérer un `GameServer`.

*   **`host`** (`str`) : L'adresse IP du serveur.
*   **`port`** (`int`) : Le port TCP du serveur.
*   **`admin_password`** (`str`, optionnel) : Le mot de passe administrateur du serveur.
*   **`use_tls`** (`bool`, optionnel) : Si `True`, le client se connectera en utilisant TLS. Par défaut `False`.

#### Méthodes
*   `get_server_info()` : Retourne des informations sur le serveur (nom, nombre de parties, IDs actifs).
*   `list_games()` : Retourne un dictionnaire des parties actives sous forme d'objets `RemoteGame`, indexé par leur ID.
*   `kick_player(game_id, player_id)` : Expulse un joueur d'une partie spécifique par son ID.
*   `kick_observer(game_id, observer_id)` : Expulse un observateur d'une partie spécifique par son ID.
*   `list_all_players()` : Retourne une liste de tous les joueurs connectés, incluant l'ID et le nom de leur partie.
*   `stop_server()` : Demande l'arrêt du serveur.
*   `restart_server()` : Demande le redémarrage du serveur (efface toutes les parties).
*   `set_logging_config(host, port)` : Configure le serveur pour envoyer ses logs à un serveur distant.
*   `get_cert_expiration()` : Retourne la date d'expiration du certificat TLS du serveur au format ISO.
*   `set_logging_enabled(enabled)` : Active ou désactive le logging sur le serveur.
*   `set_server_password(new_password)` : Définit un nouveau mot de passe pour le serveur.
*   `set_admin_password(new_password)` : Définit un nouveau mot de passe administrateur pour le serveur.
*   `create_group(name, admin_password=None, **attributes)` : Crée un nouveau groupe de jeux sur le serveur. Retourne un objet proxy `RemoteGroup`.
*   `remove_group(group_id)` : Supprime un groupe de jeux du serveur par son ID.
*   `list_groups()` : Renvoie un dictionnaire de tous les groupes sous forme d'objets `RemoteGroup`, indexé par leur `group_id`.

---

### `GroupAdmin(group_id, host='127.0.0.1', port=65432, group_admin_password=None, use_tls=False)`
Une classe cliente pour que les administrateurs de groupe gèrent les parties au sein d'un `GameGroup` spécifique.

*   **`group_id`** (`str`) : L'ID unique du groupe à gérer.
*   **`host`** (`str`) : L'adresse IP du serveur.
*   **`port`** (`int`) : Le port TCP du serveur.
*   **`group_admin_password`** (`str`, optionnel) : Le mot de passe administrateur pour ce groupe.
*   **`use_tls`** (`bool`, optionnel) : Si `True`, le client se connectera en utilisant TLS. Par défaut `False`.

#### Méthodes
*   `list_games()` : Retourne un dictionnaire des parties de ce groupe sous forme d'objets `RemoteGame`, indexé par leur ID.
*   `kick_player(game_id, player_id)` : Expulse un joueur d'une partie du groupe par son ID.
*   `kick_observer(game_id, observer_id)` : Expulse un observateur d'une partie du groupe par son ID.
*   `set_group_admin_password(new_password)` : Définit un nouveau mot de passe administrateur pour ce groupe.

---

### `GameClient(host='127.0.0.1', port=65432, password=None, use_tls=False)`
Le point d'entrée principal pour qu'un client se connecte à un `GameServer`.

*   **`host`** (`str`) : L'adresse IP du serveur.
*   **`port`** (`int`) : Le port TCP du serveur.
*   **`password`** (`str`, optionnel) : Le mot de passe global du serveur.
*   **`use_tls`** (`bool`, optionnel) : Si `True`, le client se connectera en utilisant TLS. Par défaut `False`.

#### Méthodes
*   `discover_servers(timeout=2)` (méthode statique) : Scanne le réseau local à la recherche d'instances de `GameServer`.
*   `create_game(group_id=None, **game_options)` : Demande la création d'une nouvelle partie. Retourne un objet proxy `RemoteGame`.
*   `list_games()` : Retourne un dictionnaire des parties actives sous forme d'objets `RemoteGame`, indexé par leur ID.
*   `create_group(name, admin_password=None, **attributes)` : Demande la création d'un nouveau groupe. Retourne un objet proxy `RemoteGroup`.
*   `list_groups()` : Retourne un dictionnaire des groupes sous forme d'objets `RemoteGroup`, indexé par leur ID.

---

### `RemoteGroup`
Un objet proxy représentant un groupe de jeux sur le serveur.

#### Méthodes
*   `create_game(**game_options)` : Crée une nouvelle partie au sein de ce groupe. Retourne un objet proxy `RemoteGame`.
*   `list_games()` : Retourne un dictionnaire des parties de ce groupe sous forme d'objets `RemoteGame`, indexé par leur ID.

#### Propriétés
*   **`group_id`** : L'ID unique du groupe.
*   **`name`** : Le nom du groupe.
*   **`attributes`** : Un dictionnaire d'attributs personnalisés pour le groupe.

---

### `RemoteGame`
Un objet proxy représentant une partie sur le serveur.

#### Méthodes
*   `add_player(player, password=None)` : Ajoute un `Player` à la partie distante.
*   `add_observer(observer, password=None)` : Ajoute un `Observer` à la partie distante. Le mot de passe est requis si `observer_password` (ou `password`) est défini.
*   `set_state(new_state)` : Écrase le dictionnaire `custom_state` de la partie sur le serveur.
*   (Les autres méthodes sont identiques à la classe `Game` locale.)

#### Propriétés
*   **`state`**: Retourne un dictionnaire contenant `status` et `custom`.
*   **`observers`**: Retourne une liste des objets `Observer` (avec leurs noms et IDs).

## Serveur de Logging Autonome

### `multiplayer-log-server [--port PORT] [--color-mode MODE]`
Démarre le serveur de logging autonome.

*   **`--port`** (`int`, optionnel) : Le port TCP. Par défaut `5000`.
*   **`--color-mode`** (`str`, optionnel) : `level` (défaut) ou `origin`.

## Serveur de Jeu Autonome

### `multiplayer-server [OPTIONS]`
Démarre un serveur de jeu autonome.

*   **`--host`**, **`--port`**, **`--password`**, **`--admin-password`**, **`--use-tls`**, etc.
*   **`--name`** (`str`) : Nom de l'instance du serveur.

## Fonctions Utilitaires

### Suggestions de Noms
*   `register_name_category(category_name, data, category_type)`
*   `unregister_name_category(category_name)`
*   `get_available_categories(category_type="all")`
*   `suggest_game_name(category=None)`
*   `suggest_player_name(category=None)`

## Exceptions

*   **`MultiplayerError`** : Exception de base.
*   **`GameLogicError`** : Erreurs de règles.
*   **`PlayerLimitReachedError`**, **`ObserverLimitReachedError`**
*   **`GameNotFoundError`**, **`GroupNotFoundError`**
*   **`NetworkError`**, **`ConnectionError`**, **`ServerError`**
*   **`AuthenticationError`** : Échec de mot de passe (serveur ou partie).
*   **`AccessDeniedError`** : Action administrative refusée.
