[English](../REFERENCE.md) | [Español](REFERENCE.es.md) | **Français**

# Référence de l'API pour le Module `multiplayer`

Ce document fournit une référence détaillée de l'API publique du module `multiplayer`.

## Classes Principales

### `Game(name=None, max_players=None, turn_based=False, password=None, observer_password=None, max_observers=None, **kwargs)`
Représente une session de jeu unique.

*   **`name`** (`str`, optionnel) : Le nom de la session de jeu. Par défaut `None`.
*   **`max_players`** (`int`, optionnel) : Le nombre maximum de joueurs.
*   **`max_observers`** (`int`, optionnel) : Le nombre maximum d'observateurs.
*   **`turn_based`** (`bool`, optionnel) : `True` si le jeu est au tour par tour.
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
*   `next_turn()` : Passe au joueur suivant.

#### Propriétés
*   **`ID`**: L'ID unique de la session de jeu (lecture seule).
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

#### Propriétés
*   **`ID`**: L'ID unique du joueur (lecture seule).
*   **`name`**: Le nom du joueur.
*   **`attributes`**: Un dictionnaire d'attributs personnalisés.

---

### `Observer(name, **kwargs)`
Représente un observateur.

*   **`name`** (`str`) : Le nom de l'observateur.
*   **`**kwargs`** : Attributs personnalisés pour l'observateur.

#### Propriétés
*   **`ID`**: L'ID unique de l'observateur (lecture seule).
*   **`name`**: Le nom de l'observateur.
*   **`attributes`**: Un dictionnaire d'attributs personnalisés.

---

### `GameGroup(name, admin_password=None, **kwargs)`
Représente un groupe de parties sur un serveur.

*   **`name`** (`str`) : Le nom du groupe.
*   **`admin_password`** (`str`, optionnel) : Un mot de passe pour les actions administratives sur ce groupe.
*   **`**kwargs`** : Attributs supplémentaires pour le groupe.

#### Méthodes
*   `add_game(game)` : Ajoute un objet `Game` au groupe.
*   `remove_game(game_id)` : Retire un objet `Game` du groupe par son ID.

#### Propriétés
*   **`ID`**: L'ID unique du groupe (lecture seule).
*   **`name`**: Le nom du groupe.
*   **`games`**: Une liste d'objets `Game` actuellement dans le groupe.
*   **`attributes`**: Un dictionnaire d'attributs personnalisés pour le groupe.

---

### `GameState` (Enum)
*   `GameState.PENDING`, `GameState.IN_PROGRESS`, `GameState.FINISHED`

## Classes Réseau

### `GameServer(host='0.0.0.0', port=65432, password=None, admin_password=None, use_tls=False, tls_domain="localhost", tls_cert=None, tls_key=None, tls_self_signed=True, logging_host=None, logging_port=None, name=None)`
Gère les sessions de jeu et les requêtes réseau.

*   **`host`** (`str`) : L'adresse de l'hôte sur laquelle s'écouter. Utilisez `'0.0.0.0'` pour le rendre accessible sur le réseau local.
*   **`port`** (`int`) : Le port TCP sur lequel écouter les commandes de jeu.
*   **`password`** (`str`, optionnel) : Un mot de passe global pour protéger le serveur.
*   **`admin_password`** (`str`, optionnel) : Un mot de passe pour l'accès administrateur.
*   **`use_tls`** (`bool`, optionnel) : Si `True`, active le chiffrement TLS v1.3 pour toutes les communications. Par défaut `False`.
*   **`tls_domain`** (`str`, optionnel) : Nom de domaine à inclure dans le certificat généré. Par défaut `"localhost"`.
*   **`tls_cert`** (`str`, optionnel) : Chemin vers un fichier de certificat PEM. Ce fichier doit soit être une "chaîne complète" (incluant le certificat de domaine et les certificats intermédiaires), soit être accompagné d'un fichier de "chaîne" correspondant dans le même répertoire (ex: `cert.pem` et `chain.pem`, ou `ECC-cert.pem` et `ECC-chain.pem`). Si seulement l'un des paramètres `tls_cert` ou `tls_key` est fourni alors que `tls_self_signed` est `False`, le démarrage du serveur échouera.
*   **`tls_key`** (`str`, optionnel) : Chemin vers un fichier de clé privée PEM. Si seulement l'un des paramètres `tls_cert` ou `tls_key` est fourni alors que `tls_self_signed` est `False`, le démarrage du serveur échouera.
*   **`tls_self_signed`** (`bool`, optionnel) : Si `True`, génère un certificat auto-signé si `tls_cert` ou `tls_key` est manquant. Si `False`, `tls_cert` et `tls_key` doivent tous deux être fournis. Par défaut `True`.
*   **`logging_host`** (`str`, optionnel) : L'adresse de l'hôte d'un serveur de logging.
*   **`logging_port`** (`int`, optionnel) : Le port du serveur de logging.
*   **`name`** (`str`, optionnel) : Un nom pour l'instance du serveur.

#### Méthodes
*   `start()`: Démarre le serveur.
*   `stop()`: Arrête le serveur.

---

### `ServerAdmin(host='127.0.0.1', port=65432, admin_password=None, use_tls=False)`
Une classe client pour les administrateurs pour gérer un `GameServer`.

*   **`admin_password`** (`str`, optionnel) : Le mot de passe administrateur du serveur.
*   **`use_tls`** (`bool`, optionnel) : Si `True`, le client se connectera en utilisant TLS.

#### Méthodes
*   `get_server_info()` : Retourne les infos du serveur (nom, nombre de parties, IDs actifs).
*   `list_games()` : Retourne un dictionnaire des parties actives sous forme d'objets `RemoteGame`, indexé par leur ID.
*   `kick_player(game_id, player_id)` : Expulse un joueur d'une partie par son ID.
*   `kick_observer(game_id, observer_id)` : Expulse un observateur d'une partie par son ID.
*   `list_all_players()` : Liste tous les joueurs actuellement connectés au serveur, incluant l'ID et le nom de leur partie respective.
*   `stop_server()` : Demande l'arrêt du serveur.
*   `restart_server()` : Demande le redémarrage du serveur (efface toutes les parties en cours).
*   `set_logging_config(host, port)` : Configure le serveur pour envoyer ses logs à un serveur de logging distant à l'adresse et au port spécifiés.
*   `get_cert_expiration()` : Retourne la date d'expiration du certificat TLS du serveur au format ISO.
*   `set_logging_enabled(enabled)` : Active (`True`) ou désactive (`False`) les logs sur le serveur.
*   `set_server_password(new_password)` : Définit un nouveau mot de passe pour le serveur.
*   `set_admin_password(new_password)` : Définit un nouveau mot de passe administrateur pour le serveur.
*   `create_group(name, admin_password=None, **attributes)` : Crée un nouveau groupe de jeux sur le serveur. Retourne un objet proxy `RemoteGroup`.
*   `remove_group(group_id)` : Supprime un groupe de jeux du serveur par son ID.
*   `list_groups()` : Renvoie un dictionnaire de tous les groupes de jeux sur le serveur sous forme d'objets `RemoteGroup`, indexé par leur `group_id`.

---

### `GroupAdmin(group_id, host='127.0.0.1', port=65432, group_admin_password=None, use_tls=False)`
Une classe cliente pour que les administrateurs de groupe puissent gérer les parties au sein d'un `GameGroup` spécifique.

*   **`group_id`** (`str`) : L'ID unique du groupe à gérer.
*   **`host`** (`str`) : L'adresse IP du serveur.
*   **`port`** (`int`) : Le port TCP du serveur.
*   **`group_admin_password`** (`str`, optionnel) : Le mot de passe administrateur pour ce groupe.
*   **`use_tls`** (`bool`, optionnel) : Si `True`, le client se connectera en utilisant TLS. Par défaut à `False`.

#### Méthodes
*   `list_games()` : Retourne un dictionnaire des parties appartenant à ce groupe sous forme d'objets `RemoteGame`, indexé par leur ID.
*   `kick_player(game_id, player_id)` : Supprime un joueur d'une partie spécifique du groupe par son ID.
*   `kick_observer(game_id, observer_id)` : Supprime un observateur d'une partie spécifique du groupe par son ID.
*   `set_group_admin_password(new_password)` : Définit un nouveau mot de passe administrateur pour ce groupe.

---

### `GameClient(host='127.0.0.1', port=65432, password=None, use_tls=False)`
Le point d'entrée pour qu'un client se connecte à un `GameServer`.

*   **`password`** (`str`, optionnel) : Le mot de passe global du serveur.
*   **`use_tls`** (`bool`, optionnel) : Si `True`, le client se connectera en utilisant TLS.

#### Méthodes
*   `discover_servers(timeout=2)` (méthode statique) : Scanne le réseau local à la recherche d'instances de `GameServer`.
*   `create_game(group_id=None, **game_options)` : Demande au serveur de créer une nouvelle partie. Retourne un objet proxy `RemoteGame`. Peut inclure un `group_id` para associer la partie à un groupe.
*   `list_games()` : Retourne un dictionnaire des parties actives sous forme d'objets `RemoteGame`, indexé par leur ID.
*   `create_group(name, admin_password=None, **attributes)` : Demande au serveur de créer un nouveau groupe de jeux. Retourne un objet proxy `RemoteGroup`.
*   `list_groups()` : Retourne un dictionnaire des groupes de jeux sous forme d'objets `RemoteGroup`, indexé par leur ID.

---

### `RemoteGroup`
Un objet proxy représentant un groupe de jeux s'exécutant sur le serveur.

*Généralement, vous ne créez pas cet objet directement, mais vous l'obtenez via `client.create_group()` ou `client.list_groups()`.*

#### Méthodes
*   `create_game(**game_options)` : Crée une nouvelle partie au sein de ce groupe. Retourne un objet proxy `RemoteGame`.
*   `list_games()` : Retourne un dictionnaire des parties appartenant à ce groupe sous forme d'objets `RemoteGame`, indexé par leur ID.

#### Propriétés
*   **`group_id`** : L'ID unique du groupe.
*   **`name`** : Le nom du groupe.
*   **`attributes`** : Un dictionnaire d'attributs personnalisés pour le groupe.

---

### `RemoteGame`
Un objet proxy représentant une partie exécutée sur le serveur.

#### Méthodes
*   `add_player(player, password=None)` : Ajoute un `Player` à la partie distante. Le mot de passe est requis si la partie est protégée.
*   `add_observer(observer, password=None)` : Ajoute un `Observer` à la partie distante. Le mot de passe est requis si `observer_password` (ou `password`) est défini pour la partie.
*   `set_state(new_state)` : Écrase le dictionnaire `custom_state` de la partie sur le serveur.

#### Propriétés
*   **`state`**: Retourne un dictionnaire contenant à la fois le `GameState` et l'état personnalisé. Exemple : `{'status': 'in_progress', 'custom': {'score': 100}}`.
*   **`observers`**: Retourne une liste des noms des observateurs dans la partie.

## Serveur de Logging Autonome

Le package `multiplayer` inclut un serveur de logging autonome qui peut être utilisé pour recevoir et afficher les logs de plusieurs instances de `GameServer`.

### `multiplayer-log-server [--port PORT] [--color-mode MODE]`
Démarre le serveur de logging autonome.

*   **`--port`** (`int`, optionnel) : Le port TCP sur lequel écouter. Par défaut `5000`.
*   **`--color-mode`** (`str`, optionnel) : Le mode de coloration des logs. Les options sont :
    *   `level` : Colore les logs en fonction de leur criticité (ex: INFO est vert, ERROR est rouge). C'est le mode par défaut.
    *   `origin` : Colore les logs en fonction du nom du logger (ex: `GameServer`, `GameClient`, `ServerAdmin`, etc.). Cela aide à différencier les messages provenant de différentes sources.

## Serveur de Jeu Autonome

### `multiplayer-server [OPTIONS]`
Démarre un serveur de jeu autonome.

*   **`--host`** (`str`) : Adresse de l'hôte sur laquelle écouter. Par défaut `0.0.0.0`.
*   **`--port`** (`int`) : Port sur lequel écouter. Par défaut `65432`.
*   **`--password`** (`str`) : Mot de passe global du serveur.
*   **`--admin-password`** (`str`) : Mot de passe d'administration.
*   **`--use-tls`** : Active le chiffrement TLS v1.3.
*   **`--tls-domain`** (`str`) : Nom de domaine pour le certificat. Par défaut `localhost`.
*   **`--tls-cert`** (`str`) : Chemin vers un fichier de certificat PEM.
*   **`--tls-key`** (`str`) : Chemin vers un fichier de clé privée PEM.
*   **`--tls-cert-dir`** (`str`) : Chemin vers un répertoire contenant des certificats PEM (`cert.pem`, `RSA-cert.pem`, ou `ECC-cert.pem`) et des clés. Particulièrement utile pour les volumes Docker.
*   **`--tls-self-signed`** : Génère un certificat auto-signé si les fichiers sont manquants (comportement par défaut).
*   **`--no-self-signed`** : Désactive la génération automatique de certificats auto-signés.
*   **`--name`** (`str`) : Nom lisible par l'homme pour l'instance du serveur.

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