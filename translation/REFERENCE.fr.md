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
*   **`password`** (`str`, optionnel) : Un mot de passe pour protéger cette partie spécifique (utilisé pour les joueurs, et pour les observateurs si `observer_password` n'est pas défini).
*   **`observer_password`** (`str`, optionnel) : Un mot de passe spécifiquement pour les observateurs de cette partie.
*   **`**kwargs`** : Attributs personnalisés pour la partie (ex: `difficulty="hard"`).

#### Méthodes
*   `add_player(player, password=None)` : Ajoute un objet `Player` ou `PersistentPlayer` à la partie. Le mot de passe est requis si la partie est protégée.
*   `remove_player(player_id)` : Retire un joueur de la partie par son ID.
*   `add_observer(observer, password=None)` : Ajoute un objet `Observer` ou `PersistentPlayer` à la partie. Le mot de passe est requis si `observer_password` (ou `password`) est défini.
*   `remove_observer(observer_id)` : Retire un observateur de la partie par son ID.
*   `start()` : Démarre la partie.
*   `pause()` : Met la partie en pause.
*   `resume()` : Reprend une partie en pause.
*   `stop()` : Termine la partie.
*   `next_turn()` : Passe au joueur suivant dans un jeu au tour par tour.

#### Propriétés
*   **`ID`** : L'ID unique de la session de jeu (lecture seule).
*   **`players`** : Une liste d'objets `Player` dans la partie.
*   **`observers`** : Une liste d'objets `Observer` dans la partie.
*   **`state`** : Le `GameState` actuel de la partie (ex: `GameState.IN_PROGRESS`).
*   **`custom_state`** : Un dictionnaire pour stocker les données spécifiques au jeu.
*   **`attributes`** : Un dictionnaire d'attributs personnalisés.
*   **`current_player`** : L'objet `Player` actif dans un jeu au tour par tour.

> **Note : `custom_state` vs `attributes`**
> - **`attributes`** (Métadonnées statiques) : Définis à la création via `**kwargs`. Utilisés pour la configuration qui change rarement (ex : `difficulty`, `map`).
> - **`custom_state`** (État dynamique) : Un dictionnaire pour la logique évolutive du jeu (ex : positions des pièces, scores). En jeu réseau, utilisez `client.set_state()` pour synchroniser cet état sur le serveur.

---

### `Player(name, **kwargs)`
Représente un joueur.

*   **`name`** (`str`) : Le nom du joueur.
*   **`**kwargs`** : Attributs personnalisés pour le joueur (ex: `score=100`).

#### Propriétés
*   **`ID`** : L'ID unique du joueur (lecture seule).
*   **`name`** : Le nom du joueur.
*   **`attributes`** : Un dictionnaire des attributs personnalisés du joueur.

---

### `PersistentPlayer(name, password, role=PlayerRole.PLAYER, managed_groups=None, **kwargs)`
Représente un compte de joueur persistant (hérite de `Player`).

*   **`name`** (`str`) : Le nom du joueur (unique sur le serveur).
*   **`password`** (`str`) : Le mot de passe du compte.
*   **`role`** (`PlayerRole`, optionnel) : Le rôle du joueur. Par défaut `PlayerRole.PLAYER`.
*   **`managed_groups`** (`list`, optionnel) : Une liste d'IDs de groupes gérés par ce joueur (si le rôle est `GROUP_ADMIN`).
*   **`**kwargs`** : Attributs personnalisés pour le joueur.

#### Propriétés
*   Toutes les propriétés de `Player`.
*   **`password`** : Le mot de passe du compte.
*   **`role`** : Le rôle du joueur (`PlayerRole.PLAYER`, `PlayerRole.GROUP_ADMIN`, ou `PlayerRole.SERVER_ADMIN`).
*   **`managed_groups`** : Liste des IDs de groupes que le joueur peut gérer.

---

### `Observer(name, **kwargs)`
Représente un observateur.

*   **`name`** (`str`) : Le nom de l'observateur.
*   **`**kwargs`** : Attributs personnalisés pour l'observateur.

#### Propriétés
*   **`ID`** : L'ID unique de l'observateur (lecture seule).
*   **`name`** : Le nom de l'observateur.
*   **`attributes`** : Un dictionnaire des attributs personnalisés de l'observateur.

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
*   **`ID`** : L'ID unique du groupe (lecture seule).
*   **`name`** : Le nom du groupe.
*   **`games`** : Une liste d'objets `Game` actuellement dans le groupe.
*   **`attributes`** : Un dictionnaire d'attributs personnalisés pour le groupe.

---

### `PlayerRole` (Enum)
Une énumération pour le rôle d'un joueur persistant.

*   `PlayerRole.PLAYER` : Un joueur standard qui peut rejoindre et participer à des parties.
*   `PlayerRole.GROUP_ADMIN` : Un joueur qui peut gérer les parties au sein des groupes qui lui sont assignés. Ce rôle inclut toutes les permissions d'un `PLAYER`.
*   `PlayerRole.SERVER_ADMIN` : Un joueur avec un accès administratif complet au serveur. Ce rôle englobe le rôle de `GROUP_ADMIN`, lui-même pouvant également jouer le rôle de `PLAYER`.

---

### `GameState` (Enum)
Une énumération représentant le statut actuel d'une partie.

*   `GameState.PENDING` : La partie a été créée mais n'a pas encore commencé. Cet état est dédié à l'attente des joueurs. Les joueurs peuvent rejoindre ou quitter la partie.
*   `GameState.PAUSING` : La partie est actuellement en pause. Cet état est utilisé lorsqu'une partie qui était en cours est temporairement suspendue.
*   `GameState.IN_PROGRESS` : La partie est actuellement active. Les coups peuvent être joués et la logique du tour par tour est appliquée.
*   `GameState.FINISHED` : La partie est terminée. Plus aucun coup ne peut être joué et les résultats sont définitifs.

---

## Classes Réseau

Ces classes gèrent l'architecture client-serveur.

### `GameServer(host='0.0.0.0', port=65432, password=None, admin_password=None, use_tls=False, tls_domain="localhost", tls_cert=None, tls_key=None, tls_self_signed=True, logging_host=None, logging_port=None, name=None, unencrypted_port=None, hidden=False)`
Gère les sessions de jeu et les requêtes réseau.

*   **`host`** (`str`) : L'adresse de l'hôte sur laquelle s'écouter. Utilisez `'0.0.0.0'` pour le rendre accessible sur le réseau local.
*   **`port`** (`int`) : Le port TCP sur lequel écouter les commandes de jeu.
*   **`password`** (`str`, optionnel) : Un mot de passe global pour protéger le serveur.
*   **`admin_password`** (`str`, optionnel) : Un mot de passe pour l'accès administrateur.
*   **`use_tls`** (`bool`, optionnel) : Si `True`, active le chiffrement TLS v1.3 pour toutes les communications. Par défaut `False`.
*   **`tls_domain`** (`str`, optionnel) : Nom de domaine à inclure dans le certificat généré. Par défaut `"localhost"`.
*   **`tls_cert`** (`str`, optionnel) : Chemin vers un fichier de certificat PEM. Ce fichier doit soit être une "chaîne complète" (incluant le certificat de domaine et les certificats intermédiaires), soit être accompagné d'un fichier de "chaîne" correspondant dans le même répertoire (ex: `cert.pem` et `chain.pem`, ou `ECC-cert.pem` et `ECC-chain.pem`). Si seulement l'un de `tls_cert` ou `tls_key` est fourni alors que `tls_self_signed` est `False`, le serveur ne démarrera pas.
*   **`tls_key`** (`str`, optionnel) : Chemin vers un fichier de clé privée PEM. Si seulement l'un de `tls_cert` ou `tls_key` est fourni alors que `tls_self_signed` est `False`, le serveur ne démarrera pas.
*   **`tls_self_signed`** (`bool`, optionnel) : Si `True`, génère un certificat auto-signé si `tls_cert` ou `tls_key` est manquant. Si `False`, `tls_cert` et `tls_key` doivent être fournis tous les deux. Par défaut `True`.
*   **`logging_host`** (`str`, optionnel) : L'adresse de l'hôte d'un serveur de logging pour envoyer les logs.
*   **`logging_port`** (`int`, optionnel) : Le port du serveur de logging.
*   **`name`** (`str`, optionnel) : Un nom pour l'instance du serveur.
*   **`unencrypted_port`** (`int`, optionnel) : Port pour les connexions non chiffrées lorsque le TLS est activé.
*   **`hidden`** (`bool`, optionnel) : Si `True`, le serveur ne répondra pas aux requêtes de découverte réseau. Par défaut `False`.

#### Méthodes
*   `start()` : Démarre le serveur dans un processus d'arrière-plan.
*   `stop()` : Arrête le serveur.

---

### `GameClient(host='127.0.0.1', port=65432, password=None, use_tls=False, auth_user=None, auth_password=None)`
Le point d'entrée principal pour qu'un client se connecte à un `GameServer`.

*   **`host`** (`str`) : L'adresse IP du serveur.
*   **`port`** (`int`) : Le port TCP du serveur.
*   **`password`** (`str`, optionnel) : Le mot de passe global du serveur.
*   **`use_tls`** (`bool`, optionnel) : Si `True`, le client se connectera en utilisant TLS. Par défaut `False`.
*   **`auth_user`** (`str`, optionnel) : Le nom d'un compte joueur persistant.
*   **`auth_password`** (`str`, optionnel) : Le mot de passe du compte joueur persistant.

#### Méthodes
*   `discover_servers(timeout=2)` (méthode statique) : Scanne le réseau local à la recherche d'instances de `GameServer` en cours d'exécution.
    *   **Retourne** : Une `list` de tuples `(host, port, name)` représentant les serveurs découverts.
*   `create_game(group_id=None, **game_options)` : Demande au serveur la création d'une nouvelle partie.
    *   **`group_id`** (`str`, optionnel) : L'ID du groupe dans lequel la partie doit être créée.
    *   **`**game_options`** : Options de configuration de la partie. Celles-ci correspondent aux arguments du constructeur de la classe `Game` :
        *   `name` (`str`) : Le nom de la session de jeu.
        *   `max_players` (`int`) : Le nombre maximum de joueurs autorisés.
        *   `max_observers` (`int`) : Le nombre maximum d'observateurs autorisés.
        *   `turn_based` (`bool`) : Indique si le jeu est au tour par tour.
        *   `password` (`str`) : Mot de passe requis pour que les joueurs rejoignent.
        *   `observer_password` (`str`) : Mot de passe spécifique pour les observateurs.
        *   Tout autre argument nommé sera stocké en tant qu'attribut personnalisé dans la propriété `attributes` de la partie.
    *   **Retourne** : Un objet proxy `RemoteGame`.
*   `list_games()` : Retourne toutes les parties actives (statut différent de `GameState.FINISHED`).
    *   **Retourne** : Un `dict` où les clés sont les IDs de partie (`str`) et les valeurs sont des dictionnaires contenant les propriétés de la partie :
        *   `name` (`str`) : Le nom de la session de jeu.
        *   `state` (`GameState`) : L'état actuel de la partie (par exemple, `GameState.PENDING`, `GameState.IN_PROGRESS`).
        *   `attributes` (`dict`) : Attributs personnalisés de la partie.
        *   `players_count` (`int`) : Nombre de joueurs actuellement dans la partie.
        *   `max_players` (`int`) : Nombre maximum de joueurs autorisés.
        *   `observers_count` (`int`) : Nombre d'observateurs actuellement dans la partie.
        *   `max_observers` (`int`) : Nombre maximum d'observateurs autorisés.
        *   `custom_state` (`dict`) : L'état personnalisé de la partie.
*   `create_group(name, admin_password=None, **attributes)` : Demande au serveur la création d'un nouveau groupe de jeux.
    *   **Retourne** : Un objet proxy `RemoteGroup`.
*   `list_groups()` : Retourne tous les groupes de jeux sur le serveur.
    *   **Retourne** : Un `dict` où les clés sont les IDs de groupe (`str`) et les valeurs sont des objets `RemoteGroup`.
*   `create_account(name, password, role=PlayerRole.PLAYER, managed_groups=None, **attributes)` : Crée un compte joueur persistant sur le serveur.
    *   **Erreur** : `UserAlreadyExistsError` si un compte avec le même nom existe déjà.
    *   **Retourne** : Un `dict` représentant les données du joueur créé :
        *   `player_id` (`str`) : L'ID unique du compte.
        *   `name` (`str`) : Le nom du compte.
        *   `role` (`PlayerRole`) : Le rôle assigné.
*   `get_server_admin()` : Retourne une instance de `ServerAdmin` utilisant les identifiants actuels du client.
    *   **Erreur** : `AuthenticationError` si le client n'est pas authentifié avec un compte persistant ou n'a pas les droits `SERVER_ADMIN`.
*   `get_group_admin(group_id)` : Retourne une instance de `GroupAdmin` pour le groupe spécifié utilisant les identifiants actuels du client.
    *   **Erreur** : `AuthenticationError` si le client n'est pas authentifié avec un compte persistant ou n'a pas les droits d'administration pour le groupe spécifié.
*   `register_remote_game(game_id)` : Crée et retourne un objet `RemoteGame` associé à l'ID de jeu spécifié.
    *   **`game_id`** (`str`) : L'ID de la partie à associer au `RemoteGame`.
    *   **Retourne** : Un objet `RemoteGame`.
*   `unregister_remote_game(remote_game)` : Détruit un objet `RemoteGame` et nettoie ses ressources internes.
    *   **`remote_game`** (`RemoteGame`) : L'objet `RemoteGame` à détruire.
*   `set_logging_for_client(host, port, name=None)` : Configure le client pour envoyer ses logs à un serveur de logging distant.

---

### `ServerAdmin(host='127.0.0.1', port=65432, admin_password=None, use_tls=False, auth_user=None, auth_password=None)`
Une classe client pour les administrateurs pour gérer un `GameServer` (hérite de `GameClient`).

*   Tous les arguments et paramètres de connexion de `GameClient`.
*   **`admin_password`** (`str`, optionnel) : Le mot de passe administrateur du serveur (global).

#### Méthodes
*   Toutes les méthodes de `GameClient`.
*   `list_all_server_games()` : Récupère un dictionnaire de toutes les parties sur le serveur (y compris celles avec `GameState.FINISHED`) organisé par ID.
    *   **Retourne** : Un `dict` avec le même format que `GameClient.list_games()`.
*   `get_server_info()` : Retourne des informations sur le serveur.
    *   **Retourne** : Un `dict` avec les clés suivantes :
        *   `name` (`str`) : Le nom assigné à l'instance du serveur.
        *   `host` (`str`) : L'adresse hôte sur laquelle le serveur écoute.
        *   `port` (`int`) : Le port TCP principal du serveur.
        *   `unencrypted_port` (`int`) : Le port pour les connexions non chiffrées (si le TLS est activé).
        *   `use_tls` (`bool`) : `True` si le chiffrement TLS est activé.
        *   `tls_domain` (`str`) : Le nom de domaine utilisé pour le certificat TLS.
        *   `tls_self_signed` (`bool`) : `True` si le serveur utilise un certificat auto-signé.
        *   `logging_host` (`str`) : L'hôte du serveur de logging distant.
        *   `logging_port` (`int`) : Le port du serveur de logging distant.
        *   `hidden` (`bool`) : `True` si le serveur est caché de la découverte réseau.
        *   `uptime` (`float`) : Durée en secondes depuis le démarrage du serveur.
        *   `cert_expiration` (`str`) : Date d'expiration du certificat TLS (format ISO), ou `None`.
        *   `logging_active` (`bool`) : `True` si le logging côté serveur est actuellement activé.
        *   `persistent_players_active` (`bool`) : `True` si la création de nouveaux comptes persistants est autorisée.
        *   `connected_clients` (`int`) : Nombre actuel de connexions clients actives.
*   `kick_player(game_id, player_id)` : Retire un joueur d'une partie spécifique par son ID.
*   `kick_observer(game_id, observer_id)` : Retire un observateur d'une partie spécifique par son ID.
*   `list_all_players()` : Liste tous les joueurs actuellement connus par le serveur.
    *   **Retourne** : Un `dict` où les clés sont les ID des joueurs (`str`) et les valeurs sont des dictionnaires contenant :
        *   `name` (`str`) : Le nom du joueur.
        *   `attributes` (`dict`) : Les attributs personnalisés du joueur.
        *   `games` (`dict`) : Un dictionnaire où les clés sont les ID des parties (`str`) et les valeurs sont les noms des parties (`str`), représentant les parties dans lesquelles le joueur est actuellement présent.
        *   `connected` (`bool`) : `True` si le joueur est actuellement connecté à une session de jeu.
        *   `is_persistent` (`bool`) : `True` s'il s'agit d'un compte persistant.
*   `stop_server()` : Demande l'arrêt du serveur.
*   `restart_server()` : Demande le redémarrage du serveur (efface toutes les parties actuelles).
*   `set_logging_for_server(host, port)` : Configure le serveur pour envoyer ses logs à un serveur de logging distant à l'adresse et au port spécifiés.
*   `set_logging_enabled(enabled)` : Active (`True`) ou désactive (`False`) le logging sur le serveur.
*   `set_server_password(new_password)` : Définit un nouveau mot de passe pour le serveur.
*   `set_admin_password(new_password)` : Définit un nouveau mot de passe administrateur pour le serveur.
*   `remove_group(group_id)` : Supprime un groupe de jeux du serveur par son ID.
*   `set_persistent_players_enabled(enabled)` : Active (`True`) ou désactive (`False`) la création de comptes de joueurs persistants sur le serveur. En cas de désactivation, les joueurs persistants créés précédemment restent actifs et utilisables.
*   `set_server_hidden(hidden)` : Définit le serveur comme caché (`True`) ou visible (`False`) pour la découverte réseau.
*   `update_persistent_player(name, role=None, managed_groups=None, password=None, **attributes)` : Met à jour les informations d'un joueur persistant.
*   `remove_persistent_player(name)` : Supprime un compte de joueur persistant du serveur.

---

### `GroupAdmin(group_id, host='127.0.0.1', port=65432, group_admin_password=None, use_tls=False, auth_user=None, auth_password=None)`
Une classe cliente pour que les administrateurs de groupe gèrent les parties au sein d'un `GameGroup` spécifique (hérite de `GameClient`).

*   Tous les arguments et paramètres de connexion de `GameClient`.
*   **`group_id`** (`str`) : L'ID unique du groupe à gérer.
*   **`group_admin_password`** (`str`, optionnel) : Le mot de passe administratif pour ce groupe.

#### Méthodes
*   Toutes les méthodes de `GameClient`.
*   `list_all_group_games()` : Récupère un dictionnaire de toutes les parties appartenant à ce groupe (y compris celles avec `GameState.FINISHED`) organisé par ID.
    *   **Retourne** : Un `dict` avec le même format que `GameClient.list_games()`.
*   `kick_player(game_id, player_id)` : Retire un joueur d'une partie spécifique dans le groupe par son ID.
*   `kick_observer(game_id, observer_id)` : Retire un observateur d'une partie spécifique dans le groupe par son ID.
*   `set_group_admin_password(new_password)` : Définit un nouveau mot de passe administrateur pour ce groupe.

---

### `RemoteGroup`
Un objet proxy représentant un groupe de jeux en cours d'exécution sur le serveur.

*Vous ne créez généralement pas cet objet directement, mais vous l'obtenez via `client.create_group()` ou `client.list_groups()`.*

#### Méthodes
*   `create_game(**game_options)` : Crée une nouvelle partie au sein de ce groupe. Supporte les mêmes `game_options` que `GameClient.create_game()`.
    *   **Retourne** : Un objet proxy `RemoteGame`.
*   `list_games()` : Retourne les parties actives appartenant à ce groupe (état différent de `GameState.FINISHED`).
    *   **Retourne** : Un `dict` où les clés sont les IDs de partie (`str`) et les valeurs sont des dictionnaires contenant les propriétés de la partie (même format que `GameClient.list_games()`).

#### Propriétés
*   **`group_id`** : L'ID unique du groupe.
*   **`name`** : Le nom du groupe.
*   **`attributes`** : Un dictionnaire d'attributs personnalisés pour le groupe.

---

### `RemoteGame`
Un objet proxy représentant une partie en cours d'exécution sur le serveur.

*Vous ne créez généralement pas cet objet directement, mais vous l'obtenez via `client.create_game()`.*

#### Méthodes
*   `add_player(player, password=None)` : Ajoute un `Player` ou un `PersistentPlayer` à la partie distante. Le mot de passe est requis si la partie est protégée. Si le joueur est un `PersistentPlayer`, les attributs fournis dans l'objet `player` seront fusionnés avec les attributs globaux du compte pour cette session de jeu.
*   `add_observer(observer, password=None)` : Ajoute un `Observer` ou un `PersistentPlayer` à la partie distante. Le mot de passe est requis si `observer_password` (ou `password`) est défini pour la partie. Si l'observateur est un `PersistentPlayer`, les attributs fournis dans l'objet `observer` seront fusionnés avec les attributs globaux du compte pour cette session de jeu.
*   `set_state(new_state)` : Écrase le dictionnaire `custom_state` de la partie sur le serveur.
*   (Les autres méthodes sont identiques à la classe `Game` locale.)

#### Propriétés
*   **`state`** : Retourne l'état actuel de la partie distante.
    *   **Retourne** : Un `dict` avec :
        *   `status` (`GameState`) : La valeur enum de l'état du jeu.
        *   `custom` (`dict`) : Le dictionnaire `custom_state` du jeu.
*   **`observers`** : Retourne les observateurs actuellement dans la partie.
    *   **Retourne** : Une `list` d'objets `Observer`.
*   **`players`** : Retourne les joueurs actuellement dans la partie.
    *   **Retourne** : Une `list` d'objets `Player`.

## Serveur de Logging Autonome

Le package `multiplayer` inclut un serveur de logging autonome qui peut être utilisé pour recevoir et afficher les logs de plusieurs instances de `GameServer`.

### `multiplayer-log-server [--port PORT] [--color-mode MODE]`
Démarre le serveur de logging autonome.

*   **`--port`** (`int`, optionnel) : Le port TCP sur lequel écouter. Par défaut `5000`.
*   **`--color-mode`** (`str`, optionnel) : Le mode de coloration pour les logs. Les options sont :
    *   `level` : Colore les logs en fonction de leur criticité (ex: INFO est vert, ERROR est rouge). C'est le mode par défaut.
    *   `origin` : Colore les logs en fonction du nom du logger (ex: `GameServer`, `GameClient`, `ServerAdmin`, etc.). Cela aide à différencier les messages provenant de différentes sources.

## Serveur de Jeu Autonome

### `multiplayer-server [OPTIONS]`
Démarre un serveur de jeu autonome.

*   **`--host`** (`str`) : Adresse de l'hôte sur laquelle écouter. Par défaut `0.0.0.0`.
*   **`--port`** (`int`) : Port sur lequel écouter. Par défaut `65432`.
*   **`--password`** (`str`) : Mot de passe global du serveur.
*   **`--admin-password`** (`str`) : Mot de passe administratif.
*   **`--use-tls`** : Active le chiffrement TLS v1.3.
*   **`--tls-domain`** (`str`) : Nom de domaine pour le certificat. Par défaut `localhost`.
*   **`--tls-cert`** (`str`) : Chemin vers un fichier de certificat PEM.
*   **`--tls-key`** (`str`) : Chemin vers un fichier de clé privée PEM.
*   **`--tls-cert-dir`** (`str`) : Chemin vers un répertoire contenant des certificats PEM (`cert.pem`, `RSA-cert.pem`, ou `ECC-cert.pem`) et des clés. C'est particulièrement utile pour les volumes Docker.
*   **`--tls-self-signed`** : Génère un certificat auto-signé si les fichiers sont manquants (par défaut).
*   **`--no-self-signed`** : Désactive la génération automatique de certificats auto-signés.
*   **`--unencrypted-port`** (`int`) : Port pour les connexions non-cryptées. Uniquement pertinent lorsque `--use-tls` est activé. Cela permet au serveur d'être joignable à la fois via TLS et en clair sur des ports différents.
*   **`--name`** (`str`) : Nom lisible par l'homme pour l'instance du serveur.
*   **`--hidden`** : Cache le serveur de la découverte réseau.
*   **`--persistence`** (`str`) : Type de persistance pour les joueurs et les parties. Choix : `none` (par défaut), `json`, `sqlite`.
*   **`--persistence-path`** (`str`) : Chemin vers le fichier de persistance (ex: `server_data.json` ou `server_data.db`). Si le fichier n'existe pas, il sera créé automatiquement lors de la première utilisation. Si le répertoire n'existe pas ou n'est pas accessible en écriture, le serveur ne démarrera pas.

## Fonctions Utilitaires

### Suggestions de Noms

Le package fournit des fonctions utilitaires pour suggérer des noms de parties et de joueurs basés sur différentes catégories.

#### Catégories pour les Parties
*   **`cities`** : Grandes villes du monde.
*   **`countries`** : Nations souveraines.
*   **`rivers`** : Fleuves importants du monde.
*   **`seas_oceans`** : Principales étendues d'eau salée.
*   **`planets_moons`** : Corps célestes de notre système solaire.

#### Catégories pour les Joueurs
*   **`roman_gods`** : Divinités de la mythologie romaine.
*   **`greek_gods`** : Divinités de la mythologie grecque antique.
*   **`egyptian_gods`** : Divinités de la mythologie égyptienne antique.
*   **`european_kings`** : Monarques européens historiques (hommes).
*   **`european_queens`** : Monarques européens historiques (femmes).

#### `register_name_category(category_name, data, category_type)`
Enregistre une nouvelle catégorie personnalisée pour les suggestions de noms.

*   **`category_name`** (`str`) : Le nom de la nouvelle catégorie.
*   **`data`** (`list`, `str` ou `Path`) : Une liste de noms, ou un chemin vers un fichier texte/CSV (un nom par ligne, ou première colonne du CSV).
*   **`category_type`** (`str`) : `"game"` ou `"player"`.

#### `unregister_name_category(category_name)`
Supprime une catégorie personnalisée. Retourne `True` en cas de succès.

#### `get_available_categories(category_type="all")`
Retourne une liste des catégories de suggestions de noms disponibles.

*   **`category_type`** (`str`) : `"all"`, `"game"`, ou `"player"`.

#### `suggest_game_name(category=None)`
Suggère un nom aléatoire pour une partie. Si `category` est `None`, une catégorie liée aux parties est choisie aléatoirement.

#### `suggest_player_name(category=None)`
Suggère un nom aléatoire pour un joueur. Si `category` est `None`, une catégorie liée aux joueurs est choisie aléatoirement.

## Exceptions

*   **`MultiplayerError`** : Exception de base pour toutes les erreurs spécifiques au module.
*   **`GameLogicError`** : Pour les erreurs dans les règles du jeu.
*   **`PlayerLimitReachedError`** : Levée lors de l'ajout d'un joueur à une partie pleine.
*   **`ObserverLimitReachedError`** : Levée lors de l'ajout d'un observateur à une partie ayant atteint sa limite d'observateurs.
*   **`GameNotFoundError`** : Levée lorsqu'un client demande un `id` de partie qui n'existe pas sur le serveur.
*   **`NetworkError`** : Exception de base pour les problèmes liés au réseau.
*   **`ConnectionError`** : Levée lorsqu'un client ne parvient pas à se connecter au serveur.
*   **`ServerError`** : Levée pour les erreurs génériques signalées par le serveur.
*   **`AuthenticationError`** : Levée pour les échecs d'authentification par mot de passe du serveur et de la partie.
*   **`PlayerAlreadyInGameError`** : Levée lorsqu'on tente d'ajouter un joueur ou un observateur qui est déjà présent dans la partie.
*   **`KickedError`** : Levée lorsqu'un joueur ou un observateur a été éjecté de la partie par un administrateur.
*   **`UserAlreadyExistsError`** : Levée lors de la tentative de création d'un `PersistentPlayer` avec un nom déjà utilisé.
*   **`GroupNotFoundError`** : Levée lorsqu'un `id` de groupe n'est pas trouvé sur le serveur.

## Exemples

### 1. Partie locale simple
Création d'une session de jeu basique en local sans serveur.

```python
from multiplayer.game import Game, Player

# Créer une partie et des joueurs
game = Game(name="Ma partie d'échecs", turn_based=True)

# Initialiser l'état de départ du jeu
game.custom_state = {"plateau": "standard", "demi_coups": 0}

alice = Player("Alice")
bob = Player("Bob")

# Ajouter les joueurs et démarrer
game.add_player(alice)
game.add_player(bob)
game.start()

print(f"Partie '{game.name}' démarrée avec l'état : {game.state}")
```

### 2. Connexion à un serveur et création de compte
Connexion à un serveur de jeu distant et configuration d'un compte persistant.

```python
from multiplayer.client import GameClient
from multiplayer.data import PlayerRole

client = GameClient(host="localhost", port=65432)

# Créer un compte persistant
account = client.create_account(
    name="Charlie", 
    password="mot_de_passe_sur", 
    role=PlayerRole.PLAYER
)
print(f"Compte créé pour {account['name']} avec le rôle {account['role']}")
```

### 3. Gestion de groupe et de partie (Admin)
Création d'un groupe et d'une session de jeu en tant qu'administrateur.

```python
from multiplayer.client import GameClient

# Connexion via un compte persistant ayant des droits administratifs
client = GameClient(
    host="localhost", 
    port=65432, 
    auth_user="AdminUser", 
    auth_password="admin_pass"
)

# Obtenir un proxy d'administration pour le serveur
admin = client.get_server_admin()

# Créer un groupe et une partie à l'intérieur
group = admin.create_group("Tournoi A")
remote_game = group.create_game(name="Match Final", max_players=2)

print(f"Partie '{remote_game.game_id}' créée dans le groupe '{group.group_id}'")
```

### 4. Jeu au tour par tour avec observateurs
Gestion d'une partie au tour par tour avec des spectateurs sur le serveur.

```python
from multiplayer.client import GameClient
from multiplayer.game import Player

client = GameClient(host="localhost", port=65432)

# Récupérer la liste des parties actives sur le serveur
active_games = client.list_games()
print(f"Parties actives sur le serveur : {list(active_games.keys())}")

if active_games:
    # Rejoindre la première partie active en tant que joueur
    game_id = list(active_games.keys())[0]
    remote_game = client.register_remote_game(game_id)
    me = Player("Dave")
    remote_game.add_player(me)

    # Avancer le tour (si c'est votre tour)
    if remote_game.current_player.name == "Dave":
        remote_game.next_turn()

    # Lister les observateurs
    for obs in remote_game.observers:
        print(f"Spectateur : {obs.name}")
```

### 5. Avancé : TLS, attributs personnalisés et journalisation
Utilisation du chiffrement, des métadonnées et du serveur de journalisation autonome.

```python
from multiplayer.client import GameClient
from multiplayer.game import Game

# Se connecter via TLS
client = GameClient(host="game.example.com", port=65432, use_tls=True)

# Créer une partie avec des métadonnées personnalisées
game_options = {
    "name": "Ligue Pro",
    "difficulty": "expert",
    "map": "valles_marineris"
}
remote_game = client.create_game(**game_options)

# Si le client est configuré pour envoyer des logs à un serveur,
# le proxy de jeu distant les propagera automatiquement.
client.set_logging_for_client("logserver.example.com", 5000)
remote_game.configure_logging("logserver.example.com", 5000)
```

### 6. Gestion du serveur
Cet exemple montre comment lancer et gérer un serveur de jeu.

```python
import time
from multiplayer.server import GameServer

# Initialiser le serveur
# host : "0.0.0.0" pour écouter sur toutes les interfaces
# port : 65432 (par défaut)
# password : Mot de passe optionnel pour rejoindre le serveur
# admin_password : Mot de passe requis pour ServerAdmin et GroupAdmin
server = GameServer(
    host="0.0.0.0",
    port=65432,
    password="player_pass",
    admin_password="admin_super_secret",
    name="Mon Serveur de Jeu Professionnel",
    use_tls=True,
    tls_self_signed=True
)

# Lancer le serveur (s'exécute dans un processus séparé)
server.start()

try:
    print("Le serveur est en cours d'exécution. Appuyez sur Ctrl+C pour arrêter.")
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Arrêt du serveur...")
finally:
    # Arrêter proprement le serveur
    server.stop()
```
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        