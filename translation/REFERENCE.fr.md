﻿[English](../REFERENCE.md) | [EspaÃ±ol](REFERENCE.es.md) | **FranÃ§ais**

# RÃ©fÃ©rence de l'API pour le Module `multiplayer`

Ce document fournit une rÃ©fÃ©rence dÃ©taillÃ©e de l'API publique du module `multiplayer`.

## Classes Principales

Ces classes sont utilisÃ©es pour gÃ©rer la logique de jeu, que ce soit localement ou sur le serveur.

### `Game(name=None, max_players=None, turn_based=False, password=None, observer_password=None, max_observers=None, **kwargs)`
ReprÃ©sente une session de jeu unique.

*   **`name`** (`str`, optionnel) : Le nom de la session de jeu. Par dÃ©faut `None`.
*   **`max_players`** (`int`, optionnel) : Le nombre maximum de joueurs pouvant rejoindre. Par dÃ©faut `None` (illimitÃ©).
*   **`max_observers`** (`int`, optionnel) : Le nombre maximum d'observateurs pouvant rejoindre. Par dÃ©faut `None` (illimitÃ©).
*   **`turn_based`** (`bool`, optionnel) : `True` si le jeu est au tour par tour, `False` pour un jeu simultanÃ©. Par dÃ©faut `False`.
*   **`password`** (`str`, optionnel) : Un mot de passe pour protÃ©ger cette partie spÃ©cifique (utilisÃ© pour les joueurs, et pour les observateurs si `observer_password` n'est pas dÃ©fini).
*   **`observer_password`** (`str`, optionnel) : Un mot de passe spÃ©cifiquement pour les observateurs de cette partie.
*   **`**kwargs`** : Attributs personnalisÃ©s pour la partie (ex: `difficulty="hard"`).

#### MÃ©thodes
*   `add_player(player, password=None)` : Ajoute un objet `Player` ou `PersistentPlayer` Ã  la partie. Le mot de passe est requis si la partie est protÃ©gÃ©e.
*   `remove_player(player_id)` : Retire un joueur de la partie par son ID.
*   `add_observer(observer, password=None)` : Ajoute un objet `Observer` ou `PersistentPlayer` Ã  la partie. Le mot de passe est requis si `observer_password` (ou `password`) est dÃ©fini.
*   `remove_observer(observer_id)` : Retire un observateur de la partie par son ID.
*   `start()` : DÃ©marre la partie.
*   `pause()` : Met la partie en pause.
*   `resume()` : Reprend une partie en pause.
*   `stop()` : Termine la partie.
*   `next_turn()` : Passe au joueur suivant dans un jeu au tour par tour.

#### PropriÃ©tÃ©s
*   **`ID`** : L'ID unique de la session de jeu (lecture seule).
*   **`players`** : Une liste d'objets `Player` dans la partie.
*   **`observers`** : Une liste d'objets `Observer` dans la partie.
*   **`state`** : Le `GameState` actuel de la partie (ex: `GameState.IN_PROGRESS`).
*   **`custom_state`** : Un dictionnaire pour stocker les donnÃ©es spÃ©cifiques au jeu.
*   **`attributes`** : Un dictionnaire d'attributs personnalisÃ©s.
*   **`current_player`** : L'objet `Player` actif dans un jeu au tour par tour.
*   **`start_time`** : L'heure Ã  laquelle la partie a commencÃ© (format ISO), ou `None`.
*   **`end_time`** : L'heure Ã  laquelle la partie s'est terminÃ©e (format ISO), ou `None`.

> **Note : `custom_state` vs `attributes`**
> - **`attributes`** (MÃ©tadonnÃ©es statiques) : DÃ©finis Ã  la crÃ©ation via `**kwargs`. UtilisÃ©s pour la configuration qui change rarement (ex : `difficulty`, `map`).
> - **`custom_state`** (Ã‰tat dynamique) : Un dictionnaire pour la logique Ã©volutive du jeu (ex : positions des piÃ¨ces, scores). En jeu rÃ©seau, utilisez `client.set_state()` pour synchroniser cet Ã©tat sur le serveur.

---

### `Player(name, **kwargs)`
ReprÃ©sente un joueur.

*   **`name`** (`str`) : Le nom du joueur.
*   **`**kwargs`** : Attributs personnalisÃ©s pour le joueur (ex: `score=100`).

#### PropriÃ©tÃ©s
*   **`ID`** : L'ID unique du joueur (lecture seule).
*   **`name`** : Le nom du joueur.
*   **`attributes`** : Un dictionnaire des attributs personnalisÃ©s du joueur.

---

### `PersistentPlayer(name, password, role=PlayerRole.PLAYER, managed_groups=None, **kwargs)`
ReprÃ©sente un compte de joueur persistant (hÃ©rite de `Player`). Les mots de passe des joueurs persistants sont automatiquement hachÃ©s avec `bcrypt` avant d'Ãªtre stockÃ©s.

*   **`name`** (`str`) : Le nom du joueur (unique sur le serveur).
*   **`password`** (`str`) : Le mot de passe du compte (hachÃ© lors du stockage).
*   **`role`** (`PlayerRole`, optionnel) : Le rÃ´le du joueur. Par dÃ©faut `PlayerRole.PLAYER`.
*   **`managed_groups`** (`list`, optionnel) : Une liste d'IDs de groupes gÃ©rÃ©s par ce joueur (si le rÃ´le est `GROUP_ADMIN`).
*   **`**kwargs`** : Attributs personnalisÃ©s pour le joueur.

#### PropriÃ©tÃ©s
*   Toutes les propriÃ©tÃ©s de `Player`.
*   **`password`** : Le mot de passe du compte (retourne le hash bcrypt).
*   **`role`** : Le rÃ´le du joueur (`PlayerRole.PLAYER`, `PlayerRole.GROUP_ADMIN`, ou `PlayerRole.SERVER_ADMIN`).
*   **`managed_groups`** : Liste des IDs de groupes que le joueur peut gÃ©rer.

---

### `Observer(name, **kwargs)`
ReprÃ©sente un observateur.

*   **`name`** (`str`) : Le nom de l'observateur.
*   **`**kwargs`** : Attributs personnalisÃ©s pour l'observateur.

#### PropriÃ©tÃ©s
*   **`ID`** : L'ID unique de l'observateur (lecture seule).
*   **`name`** : Le nom de l'observateur.
*   **`attributes`** : Un dictionnaire des attributs personnalisÃ©s de l'observateur.

---

### `GameGroup(name, admin_password=None, **kwargs)`
ReprÃ©sente un groupe de parties sur un serveur.

*   **`name`** (`str`) : Le nom du groupe.
*   **`admin_password`** (`str`, optionnel) : Un mot de passe pour les actions administratives sur ce groupe.
*   **`**kwargs`** : Attributs supplÃ©mentaires pour le groupe.

#### MÃ©thodes
*   `add_game(game)` : Ajoute un objet `Game` au groupe.
*   `remove_game(game_id)` : Retire une partie du groupe par son ID.

#### PropriÃ©tÃ©s
*   **`ID`** : L'ID unique du groupe (lecture seule).
*   **`name`** : Le nom du groupe.
*   **`games`** : Une liste d'objets `Game` actuellement dans le groupe.
*   **`attributes`** : Un dictionnaire d'attributs personnalisÃ©s pour le groupe.

---

### `PlayerRole` (Enum)
Une Ã©numÃ©ration pour le rÃ´le d'un joueur persistant.

*   `PlayerRole.PLAYER` : Un joueur standard qui peut rejoindre et participer Ã  des parties.
*   `PlayerRole.GROUP_ADMIN` : Un joueur qui peut gÃ©rer les parties au sein des groupes qui lui sont assignÃ©s. Ce rÃ´le inclut toutes les permissions d'un `PLAYER`.
*   `PlayerRole.SERVER_ADMIN` : Un joueur avec un accÃ¨s administratif complet au serveur. Ce rÃ´le englobe le rÃ´le de `GROUP_ADMIN`, lui-mÃªme pouvant Ã©galement jouer le rÃ´le de `PLAYER`.

---

### `GameState` (Enum)
Une Ã©numÃ©ration reprÃ©sentant le statut actuel d'une partie.

*   `GameState.PENDING` : La partie a Ã©tÃ© crÃ©Ã©e mais n'a pas encore commencÃ©. Cet Ã©tat est dÃ©diÃ© Ã  l'attente des joueurs. Les joueurs peuvent rejoindre ou quitter la partie.
*   `GameState.PAUSING` : La partie est actuellement en pause. Cet Ã©tat est utilisÃ© lorsqu'une partie qui Ã©tait en cours est temporairement suspendue.
*   `GameState.IN_PROGRESS` : La partie est actuellement active. Les coups peuvent Ãªtre jouÃ©s et la logique du tour par tour est appliquÃ©e.
*   `GameState.FINISHED` : La partie est terminÃ©e. Plus aucun coup ne peut Ãªtre jouÃ© et les rÃ©sultats sont dÃ©finitifs.

---

## Classes RÃ©seau

Ces classes gÃ¨rent l'architecture client-serveur.

### `GameServer(host='0.0.0.0', port=65432, password=None, admin_password=None, use_tls=False, tls_domain="localhost", tls_cert=None, tls_key=None, tls_self_signed=True, logging_host=None, logging_port=None, name=None, unencrypted_port=None, hidden=False, persistence_type=None, persistence_path=None)`
GÃ¨re les sessions de jeu et les requÃªtes rÃ©seau. Tous les mots de passe (serveur, admin, parties et joueurs) sont hachÃ©s de maniÃ¨re sÃ©curisÃ©e avec `bcrypt` lorsqu'ils sont stockÃ©s de maniÃ¨re persistante.

*   **`host`** (`str`) : L'adresse de l'hÃ´te sur laquelle s'Ã©couter. Utilisez `'0.0.0.0'` pour le rendre accessible sur le rÃ©seau local.
*   **`port`** (`int`) : Le port TCP sur lequel Ã©couter les commandes de jeu.
*   **`password`** (`str`, optionnel) : Un mot de passe global pour protÃ©ger le serveur.
*   **`admin_password`** (`str`, optionnel) : Un mot de passe pour l'accÃ¨s administrateur.
*   **`use_tls`** (`bool`, optionnel) : Si `True`, active le chiffrement TLS v1.3 pour toutes les communications. Par dÃ©faut `False`.
*   **`tls_domain`** (`str`, optionnel) : Nom de domaine Ã  inclure dans le certificat gÃ©nÃ©rÃ©. Par dÃ©faut `"localhost"`.
*   **`tls_cert`** (`str`, optionnel) : Chemin vers un fichier de certificat PEM. Ce fichier doit soit Ãªtre une "chaÃ®ne complÃ¨te" (incluant le certificat de domaine et les certificats intermÃ©diaires), soit Ãªtre accompagnÃ© d'un fichier de "chaÃ®ne" correspondant dans le mÃªme rÃ©pertoire (ex: `cert.pem` et `chain.pem`, ou `ECC-cert.pem` et `ECC-chain.pem`). Si seulement l'un de `tls_cert` ou `tls_key` est fourni alors que `tls_self_signed` est `False`, le serveur ne dÃ©marrera pas.
*   **`tls_key`** (`str`, optionnel) : Chemin vers un fichier de clÃ© privÃ©e PEM. Si seulement l'un de `tls_cert` ou `tls_key` est fourni alors que `tls_self_signed` est `False`, le serveur ne dÃ©marrera pas.
*   **`tls_self_signed`** (`bool`, optionnel) : Si `True`, gÃ©nÃ¨re un certificat auto-signÃ© si `tls_cert` ou `tls_key` est manquant. Si `False`, `tls_cert` et `tls_key` doivent Ãªtre fournis tous les deux. Par dÃ©faut `True`.
*   **`logging_host`** (`str`, optionnel) : L'adresse de l'hÃ´te d'un serveur de logging pour envoyer les logs.
*   **`logging_port`** (`int`, optionnel) : Le port du serveur de logging.
*   **`name`** (`str`, optionnel) : Un nom pour l'instance du serveur.
*   **`unencrypted_port`** (`int`, optionnel) : Port pour les connexions non chiffrÃ©es lorsque le TLS est activÃ©.
*   **`hidden`** (`bool`, optionnel) : Si `True`, le serveur ne rÃ©pondra pas aux requÃªtes de dÃ©couverte rÃ©seau. Par dÃ©faut `False`.
*   **`persistence_type`** (`str`, optionnel) : Le type de persistance Ã  utiliser (ex: `'json'`). Par dÃ©faut `None` (pas de persistance).
*   **`persistence_path`** (`str`, optionnel) : Le chemin vers le fichier ou le rÃ©pertoire oÃ¹ les donnÃ©es de jeu et de compte doivent Ãªtre stockÃ©es.

#### MÃ©thodes
*   `start()` : DÃ©marre le serveur dans un processus d'arriÃ¨re-plan.
*   `stop()` : ArrÃªte le serveur.

---

### `GameClient(host='127.0.0.1', port=65432, password=None, use_tls=False, auth_user=None, auth_password=None)`
Le point d'entrÃ©e principal pour qu'un client se connecte Ã  un `GameServer`.

*   **`host`** (`str`) : L'adresse IP du serveur.
*   **`port`** (`int`) : Le port TCP du serveur.
*   **`password`** (`str`, optionnel) : Le mot de passe global du serveur.
*   **`use_tls`** (`bool`, optionnel) : Si `True`, le client se connectera en utilisant TLS. Par dÃ©faut `False`.
*   **`auth_user`** (`str`, optionnel) : Le nom d'un compte joueur persistant.
*   **`auth_password`** (`str`, optionnel) : Le mot de passe du compte joueur persistant.

#### MÃ©thodes
*   `discover_servers(timeout=2)` (mÃ©thode statique) : Scanne le rÃ©seau local Ã  la recherche d'instances de `GameServer` en cours d'exÃ©cution.
    *   **Retourne** : Une `list` de tuples `(host, port, name)` reprÃ©sentant les serveurs dÃ©couverts.
*   `create_game(group_id=None, **game_options)` : Demande au serveur la crÃ©ation d'une nouvelle partie.
    *   **`group_id`** (`str`, optionnel) : L'ID du groupe dans lequel la partie doit Ãªtre crÃ©Ã©e.
    *   **`**game_options`** : Options de configuration de la partie. Celles-ci correspondent aux arguments du constructeur de la classe `Game` :
        *   `name` (`str`) : Le nom de la session de jeu.
        *   `max_players` (`int`) : Le nombre maximum de joueurs autorisÃ©s.
        *   `max_observers` (`int`) : Le nombre maximum d'observateurs autorisÃ©s.
        *   `turn_based` (`bool`) : Indique si le jeu est au tour par tour.
        *   `password` (`str`) : Mot de passe requis pour que les joueurs rejoignent.
        *   `observer_password` (`str`) : Mot de passe spÃ©cifique pour les observateurs.
        *   Tout autre argument nommÃ© sera stockÃ© en tant qu'attribut personnalisÃ© dans la propriÃ©tÃ© `attributes` de la partie.
    *   **Retourne** : Un objet proxy `RemoteGame`.
*   `list_games()` : Retourne toutes les parties actives (statut diffÃ©rent de `GameState.FINISHED`).
    *   **Retourne** : Un `dict` où les clés sont les IDs de partie (`str`) et les valeurs sont des dictionnaires contenant les propriétés de la partie :
        *   `game_id` (`str`) : L'ID unique de la session de jeu.
        *   `name` (`str`) : Le nom de la session de jeu.
        *   `state` (`GameState`) : L'état actuel de la partie (par exemple, `GameState.PENDING`, `GameState.IN_PROGRESS`).
        *   `attributes` (`dict`) : Attributs personnalisés de la partie.
        *   `players_count` (`int`) : Nombre de joueurs actuellement dans la partie.
        *   `max_players` (`int`) : Nombre maximum de joueurs autorisés.
        *   `observers_count` (`int`) : Nombre d'observateurs actuellement dans la partie.
        *   `max_observers` (`int`) : Nombre maximum d'observateurs autorisés.
        *   `custom_state` (`dict`) : L'état personnalisé de la partie.
        *   `start_time` (`str`) : L'heure de dÃ©but au format ISO.
        *   `end_time` (`str`) : L'heure de fin au format ISO (si terminÃ©e).
*   `list_users()` : Retourne une liste des utilisateurs actuellement connectÃ©s au serveur.
    *   **Retourne** : Une `list` de chaÃ®nes contenant les noms et rÃ´les des utilisateurs connectÃ©s.
*   `create_group(name, admin_password=None, **attributes)` : Demande au serveur la crÃ©ation d'un nouveau groupe de jeux.
    *   **Retourne** : Un objet proxy `RemoteGroup`.
*   `list_groups()` : Retourne tous les groupes de jeux sur le serveur.
    *   **Retourne** : Un `dict` oÃ¹ les clÃ©s sont les IDs de groupe (`str`) et les valeurs sont des objets `RemoteGroup`.
*   `create_account(name, password, role=PlayerRole.PLAYER, managed_groups=None, **attributes)` : CrÃ©e un compte joueur persistant sur le serveur.
    *   **Erreur** : `UserAlreadyExistsError` si un compte avec le mÃªme nom existe dÃ©jÃ .
    *   **Retourne** : Un `dict` représentant les données du joueur créé :
        *   `player_id` (`str`) : L'ID unique du compte.
        *   `name` (`str`) : Le nom du compte.
        *   `role` (`PlayerRole`) : Le rôle assigné.
        *   `attributes` (`dict`) : Les attributs personnalisés du joueur.
        *   `managed_groups` (`list`) : Liste des IDs de groupes que le joueur peut gérer.
*   `get_server_admin()` : Retourne une instance de `ServerAdmin` utilisant les identifiants actuels du client.
    *   **Erreur** : `AuthenticationError` si le client n'est pas authentifiÃ© avec un compte persistant ou n'a pas les droits `SERVER_ADMIN`.
*   `get_group_admin(group_id)` : Retourne une instance de `GroupAdmin` pour le groupe spÃ©cifiÃ© utilisant les identifiants actuels du client.
    *   **Erreur** : `AuthenticationError` si le client n'est pas authentifiÃ© avec un compte persistant ou n'a pas les droits d'administration pour le groupe spÃ©cifiÃ©.
*   `register_remote_game(game_id)` : CrÃ©e et retourne un objet `RemoteGame` associÃ© Ã  l'ID de jeu spÃ©cifiÃ©.
    *   **`game_id`** (`str`) : L'ID de la partie Ã  associer au `RemoteGame`.
    *   **Retourne** : Un objet `RemoteGame`.
*   `unregister_remote_game(remote_game)` : DÃ©truit un objet `RemoteGame` et nettoie ses ressources internes.
    *   **`remote_game`** (`RemoteGame`) : L'objet `RemoteGame` Ã  dÃ©truire.
*   `set_logging_for_client(host, port, name=None)` : Configure le client pour envoyer ses logs Ã  un serveur de logging distant.

---

### `ServerAdmin(host='127.0.0.1', port=65432, admin_password=None, use_tls=False, auth_user=None, auth_password=None)`
Une classe client pour les administrateurs pour gÃ©rer un `GameServer` (hÃ©rite de `GameClient`).

*   Tous les arguments et paramÃ¨tres de connexion de `GameClient`.
*   **`admin_password`** (`str`, optionnel) : Le mot de passe administrateur du serveur (global).

#### MÃ©thodes
*   Toutes les mÃ©thodes de `GameClient`.
*   `list_all_server_games()` : RÃ©cupÃ¨re un dictionnaire de toutes les parties sur le serveur (y compris celles avec `GameState.FINISHED`) organisÃ© par ID.
    *   **Retourne** : Un `dict` avec le mÃªme format que `GameClient.list_games()`.
*   `get_server_info()` : Retourne des informations sur le serveur.
    *   **Retourne** : Un `dict` avec les clÃ©s suivantes :
        *   `name` (`str`) : Le nom assignÃ© Ã  l'instance du serveur.
        *   `host` (`str`) : L'adresse hÃ´te sur laquelle le serveur Ã©coute.
        *   `port` (`int`) : Le port TCP principal du serveur.
        *   `unencrypted_port` (`int`) : Le port pour les connexions non chiffrÃ©es (si le TLS est activÃ©).
        *   `use_tls` (`bool`) : `True` si le chiffrement TLS est activÃ©.
        *   `tls_domain` (`str`) : Le nom de domaine utilisÃ© pour le certificat TLS.
        *   `tls_self_signed` (`bool`) : `True` si le serveur utilise un certificat auto-signÃ©.
        *   `logging_host` (`str`) : L'hÃ´te du serveur de logging distant.
        *   `logging_port` (`int`) : Le port du serveur de logging distant.
        *   `hidden` (`bool`) : `True` si le serveur est cachÃ© de la dÃ©couverte rÃ©seau.
        *   `uptime` (`float`) : DurÃ©e en secondes depuis le dÃ©marrage du serveur.
        *   `cert_expiration` (`str`) : Date d'expiration du certificat TLS (format ISO), ou `None`.
        *   `logging_active` (`bool`) : `True` si le logging cÃ´tÃ© serveur est actuellement activÃ©.
        *   `persistent_players_active` (`bool`) : `True` si la crÃ©ation de nouveaux comptes persistants est autorisÃ©e.
        *   `connected_clients` (`int`) : Nombre actuel de connexions clients actives.
*   `kick_player(game_id, player_id)` : Retire un joueur d'une partie spÃ©cifique par son ID. Le `group_id` sera automatiquement rÃ©solu Ã  partir du `game_id` s'il n'est pas explicitement fourni (utilisÃ© pour l'autorisation).
*   `kick_observer(game_id, observer_id)` : Retire un observateur d'une partie spÃ©cifique par son ID. Le `group_id` sera automatiquement rÃ©solu Ã  partir du `game_id` s'il n'est pas explicitement fourni (utilisÃ© pour l'autorisation).
*   `list_all_players()` : Liste tous les joueurs actuellement connus par le serveur.
    *   **Retourne** : Un `dict` oÃ¹ les clÃ©s sont les ID des joueurs (`str`) et les valeurs sont des dictionnaires contenant :
        *   `name` (`str`) : Le nom du joueur.
        *   `attributes` (`dict`) : Les attributs personnalisÃ©s du joueur.
        *   `games` (`dict`) : Un dictionnaire oÃ¹ les clÃ©s sont les ID des parties (`str`) et les valeurs sont les noms des parties (`str`), reprÃ©sentant les parties dans lesquelles le joueur est actuellement prÃ©sent.
        *   `connected` (`bool`) : `True` si le joueur est actuellement connectÃ© Ã  une session de jeu.
        *   `is_persistent` (`bool`) : `True` s'il s'agit d'un compte persistant.
*   `stop_server()` : Demande l'arrÃªt du serveur.
*   `restart_server()` : Demande le redÃ©marrage du serveur (efface toutes les parties actuelles).
*   `set_logging_for_server(host, port)` : Configure le serveur pour envoyer ses logs Ã  un serveur de logging distant Ã  l'adresse et au port spÃ©cifiÃ©s.
*   `set_logging_enabled(enabled)` : Active (`True`) ou dÃ©sactive (`False`) le logging sur le serveur.
*   `set_server_password(new_password)` : DÃ©finit un nouveau mot de passe pour le serveur.
*   `set_admin_password(new_password)` : DÃ©finit un nouveau mot de passe administrateur pour le serveur.
*   `remove_group(group_id)` : Supprime un groupe de jeux du serveur par son ID.
*   `set_persistent_players_enabled(enabled)` : Active (`True`) ou dÃ©sactive (`False`) la crÃ©ation de comptes de joueurs persistants sur le serveur. En cas de dÃ©sactivation, les joueurs persistants crÃ©Ã©s prÃ©cÃ©demment restent actifs et utilisables.
*   `set_server_hidden(hidden)` : DÃ©finit le serveur comme cachÃ© (`True`) ou visible (`False`) pour la dÃ©couverte rÃ©seau.
*   `update_persistent_player(name, role=None, managed_groups=None, password=None, **attributes)` : Met Ã  jour les informations d'un joueur persistant.
*   `remove_persistent_player(name)` : Supprime un compte de joueur persistant du serveur.

---

### `GroupAdmin(group_id, host='127.0.0.1', port=65432, group_admin_password=None, use_tls=False, auth_user=None, auth_password=None)`
Une classe cliente pour que les administrateurs de groupe gÃ¨rent les parties au sein d'un `GameGroup` spÃ©cifique (hÃ©rite de `GameClient`).

*   Tous les arguments et paramÃ¨tres de connexion de `GameClient`.
*   **`group_id`** (`str`) : L'ID unique du groupe Ã  gÃ©rer.
*   **`group_admin_password`** (`str`, optionnel) : Le mot de passe administratif pour ce groupe.

#### MÃ©thodes
*   Toutes les mÃ©thodes de `GameClient`.
*   `list_all_group_games()` : RÃ©cupÃ¨re un dictionnaire de toutes les parties appartenant Ã  ce groupe (y compris celles avec `GameState.FINISHED`) organisÃ© par ID.
    *   **Retourne** : Un `dict` avec le mÃªme format que `GameClient.list_games()`.
*   `kick_player(game_id, player_id)` : Retire un joueur d'une partie spÃ©cifique dans le groupe par son ID.
*   `kick_observer(game_id, observer_id)` : Retire un observateur d'une partie spÃ©cifique dans le groupe par son ID.
*   `set_group_admin_password(new_password)` : DÃ©finit un nouveau mot de passe administrateur pour ce groupe.

---

### `RemoteGroup`
Un objet proxy reprÃ©sentant un groupe de jeux en cours d'exÃ©cution sur le serveur.

*Vous ne crÃ©ez gÃ©nÃ©ralement pas cet objet directement, mais vous l'obtenez via `client.create_group()` ou `client.list_groups()`.*

#### MÃ©thodes
*   `create_game(**game_options)` : CrÃ©e une nouvelle partie au sein de ce groupe. Supporte les mÃªmes `game_options` que `GameClient.create_game()`.
    *   **Retourne** : Un objet proxy `RemoteGame`.
*   `list_games()` : Retourne les parties actives appartenant Ã  ce groupe (Ã©tat diffÃ©rent de `GameState.FINISHED`).
    *   **Retourne** : Un `dict` oÃ¹ les clÃ©s sont les IDs de partie (`str`) et les valeurs sont des dictionnaires contenant les propriÃ©tÃ©s de la partie (mÃªme format que `GameClient.list_games()`).

#### PropriÃ©tÃ©s
*   **`group_id`** : L'ID unique du groupe.
*   **`name`** : Le nom du groupe.
*   **`attributes`** : Un dictionnaire d'attributs personnalisÃ©s pour le groupe.

---

### `RemoteGame`
Un objet proxy représentant une partie en cours d'exécution sur le serveur.

*Vous ne créez généralement pas cet objet directement, mais vous l'obtenez via `client.create_game()` ou `client.register_remote_game()`.*

#### Méthodes
*   `add_player(player, password=None)` : Ajoute un `Player` ou un `PersistentPlayer` à la partie distante. Le mot de passe est requis si la partie est protégée. Si le joueur est un `PersistentPlayer`, les attributs fournis dans l'objet `player` seront fusionnés avec les attributs globaux du compte pour cette session de jeu.
*   `add_observer(observer, password=None)` : Ajoute un `Observer` ou un `PersistentPlayer` à la partie distante. Le mot de passe est requis si `observer_password` (ou `password`) est défini pour la partie. Si l'observateur est un `PersistentPlayer`, les attributs fournis dans l'objet `observer` seront fusionnés avec les attributs globaux du compte pour cette session de jeu.
*   `set_state(new_state)` : Écrase le dictionnaire `custom_state` de la partie sur le serveur.
*   `configure_logging(host, port, name=None)` : Configure le proxy de jeu distant pour envoyer des logs à un serveur de logging distant.
*   (Les autres méthodes sont identiques à la classe `Game` locale.)

#### PropriÃ©tÃ©s
*   **`state`** : Retourne l'Ã©tat actuel de la partie distante.
    *   **Retourne** : Un `dict` avec :
        *   `status` (`GameState`) : La valeur enum de l'Ã©tat du jeu.
        *   `custom` (`dict`) : Le dictionnaire `custom_state` du jeu.
*   **`observers`** : Retourne les observateurs actuellement dans la partie.
    *   **Retourne** : Une `list` d'objets `Observer`.
*   **`players`** : Retourne les joueurs actuellement dans la partie.
    *   **Retourne** : Une `list` d'objets `Player`.

## Serveur de Logging Autonome

Le package `multiplayer` inclut un serveur de logging autonome qui peut Ãªtre utilisÃ© pour recevoir et afficher les logs de plusieurs instances de `GameServer`.

### `multiplayer-log-server [--port PORT] [--color-mode MODE]`
DÃ©marre le serveur de logging autonome.

*   **`--port`** (`int`, optionnel) : Le port TCP sur lequel Ã©couter. Par dÃ©faut `5000`.
*   **`--color-mode`** (`str`, optionnel) : Le mode de coloration pour les logs. Les options sont :
    *   `level` : Colore les logs en fonction de leur criticitÃ© (ex: INFO est vert, ERROR est rouge). C'est le mode par dÃ©faut.
    *   `origin` : Colore les logs en fonction du nom du logger (ex: `GameServer`, `GameClient`, `ServerAdmin`, etc.). Cela aide Ã  diffÃ©rencier les messages provenant de diffÃ©rentes sources.

## Serveur de Jeu Autonome

### `multiplayer-server [OPTIONS]`
DÃ©marre un serveur de jeu autonome.

*   **`--host`** (`str`) : Adresse de l'hÃ´te sur laquelle Ã©couter. Par dÃ©faut `0.0.0.0`.
*   **`--port`** (`int`) : Port sur lequel Ã©couter. Par dÃ©faut `65432`.
*   **`--password`** (`str`) : Mot de passe global du serveur.
*   **`--admin-password`** (`str`) : Mot de passe administratif.
*   **`--use-tls`** : Active le chiffrement TLS v1.3.
*   **`--tls-domain`** (`str`) : Nom de domaine pour le certificat. Par dÃ©faut `localhost`.
*   **`--tls-cert`** (`str`) : Chemin vers un fichier de certificat PEM.
*   **`--tls-key`** (`str`) : Chemin vers un fichier de clÃ© privÃ©e PEM.
*   **`--tls-cert-dir`** (`str`) : Chemin vers un rÃ©pertoire contenant des certificats PEM (`cert.pem`, `RSA-cert.pem`, ou `ECC-cert.pem`) et des clÃ©s. C'est particuliÃ¨rement utile pour les volumes Docker.
*   **`--tls-self-signed`** : GÃ©nÃ¨re un certificat auto-signÃ© si les fichiers sont manquants (par dÃ©faut).
*   **`--no-self-signed`** : DÃ©sactive la gÃ©nÃ©ration automatique de certificats auto-signÃ©s.
*   **`--unencrypted-port`** (`int`) : Port pour les connexions non-cryptÃ©es. Uniquement pertinent lorsque `--use-tls` est activÃ©. Cela permet au serveur d'Ãªtre joignable Ã  la fois via TLS et en clair sur des ports diffÃ©rents.
*   **`--name`** (`str`) : Nom lisible par l'homme pour l'instance du serveur.
*   **`--hidden`** : Cache le serveur de la dÃ©couverte rÃ©seau.
*   **`--persistence`** (`str`) : Type de persistance pour les joueurs et les parties. Choix : `none` (par dÃ©faut), `json`, `sqlite`.
*   **`--persistence-path`** (`str`) : Chemin vers le fichier de persistance (ex: `server_data.json` ou `server_data.db`). Si le fichier n'existe pas, il sera créé automatiquement lors de la première utilisation. Si le répertoire n'existe pas ou n'est pas accessible en écriture, le serveur ne démarrera pas.

### Détails de la persistance

Lors de l'utilisation d'un stockage persistant (JSON ou SQLite) :
*   **IDs comme Clés** : Les joueurs et les parties sont stockés en utilisant leur UUID unique comme clé primaire au lieu de leurs noms.
*   **Joueurs Volatils** : Les joueurs non persistants (ceux créés pour une seule partie) sont également stockés dans un groupe dédié `volatile_players`. Seuls leur ID, leur nom et leurs attributs sont conservés.
*   **Fermeture de Compte** : La suppression d'un joueur persistant ne supprime pas son enregistrement. À la place, un horodatage `closed_at` est ajouté. Un compte fermé ne peut plus être utilisé pour l'authentification.
*   **Données de Partie** : Les parties incluent obligatoirement des listes `players` et `observers`, contenant les IDs des participants.

## Fonctions Utilitaires

### Suggestions de Noms

Le package fournit des fonctions utilitaires pour suggÃ©rer des noms de parties et de joueurs basÃ©s sur diffÃ©rentes catÃ©gories.

#### CatÃ©gories pour les Parties
*   **`cities`** : Grandes villes du monde.
*   **`countries`** : Nations souveraines.
*   **`rivers`** : Fleuves importants du monde.
*   **`seas_oceans`** : Principales Ã©tendues d'eau salÃ©e.
*   **`planets_moons`** : Corps cÃ©lestes de notre systÃ¨me solaire.

#### CatÃ©gories pour les Joueurs
*   **`roman_gods`** : DivinitÃ©s de la mythologie romaine.
*   **`greek_gods`** : DivinitÃ©s de la mythologie grecque antique.
*   **`egyptian_gods`** : DivinitÃ©s de la mythologie Ã©gyptienne antique.
*   **`european_kings`** : Monarques europÃ©ens historiques (hommes).
*   **`european_queens`** : Monarques europÃ©ens historiques (femmes).

#### `register_name_category(category_name, data, category_type)`
Enregistre une nouvelle catÃ©gorie personnalisÃ©e pour les suggestions de noms.

*   **`category_name`** (`str`) : Le nom de la nouvelle catÃ©gorie.
*   **`data`** (`list`, `str` ou `Path`) : Une liste de noms, ou un chemin vers un fichier texte/CSV (un nom par ligne, ou premiÃ¨re colonne du CSV).
*   **`category_type`** (`str`) : `"game"` ou `"player"`.

#### `unregister_name_category(category_name)`
Supprime une catÃ©gorie personnalisÃ©e. Retourne `True` en cas de succÃ¨s.

#### `get_available_categories(category_type="all")`
Retourne une liste des catÃ©gories de suggestions de noms disponibles.

*   **`category_type`** (`str`) : `"all"`, `"game"`, ou `"player"`.

#### `suggest_game_name(category=None)`
SuggÃ¨re un nom alÃ©atoire pour une partie. Si `category` est `None`, une catÃ©gorie liÃ©e aux parties est choisie alÃ©atoirement.

#### `suggest_player_name(category=None)`
SuggÃ¨re un nom alÃ©atoire pour un joueur. Si `category` est `None`, une catÃ©gorie liÃ©e aux joueurs est choisie alÃ©atoirement.

## Exceptions

*   **`MultiplayerError`** : Exception de base pour toutes les erreurs spÃ©cifiques au module.
*   **`GameLogicError`** : Pour les erreurs dans les rÃ¨gles du jeu.
*   **`PlayerLimitReachedError`** : LevÃ©e lors de l'ajout d'un joueur Ã  une partie pleine.
*   **`ObserverLimitReachedError`** : LevÃ©e lors de l'ajout d'un observateur Ã  une partie ayant atteint sa limite d'observateurs.
*   **`GameNotFoundError`** : LevÃ©e lorsqu'un client demande un `id` de partie qui n'existe pas sur le serveur.
*   **`NetworkError`** : Exception de base pour les problÃ¨mes liÃ©s au rÃ©seau.
*   **`ConnectionError`** : LevÃ©e lorsqu'un client ne parvient pas Ã  se connecter au serveur.
*   **`ServerError`** : LevÃ©e pour les erreurs gÃ©nÃ©riques signalÃ©es par le serveur.
*   **`AuthenticationError`** : LevÃ©e pour les Ã©checs d'authentification par mot de passe du serveur et de la partie.
*   **`PlayerAlreadyInGameError`** : LevÃ©e lorsqu'on tente d'ajouter un joueur ou un observateur qui est dÃ©jÃ  prÃ©sent dans la partie.
*   **`KickedError`** : LevÃ©e lorsqu'un joueur ou un observateur a Ã©tÃ© Ã©jectÃ© de la partie par un administrateur.
*   **`UserAlreadyExistsError`** : LevÃ©e lors de la tentative de crÃ©ation d'un `PersistentPlayer` avec un nom dÃ©jÃ  utilisÃ©.
*   **`GroupNotFoundError`** : LevÃ©e lorsqu'un `id` de groupe n'est pas trouvÃ© sur le serveur.

## Exemples

### 1. Partie locale simple
CrÃ©ation d'une session de jeu basique en local sans serveur.

```python
from multiplayer.game import Game, Player

# CrÃ©er une partie et des joueurs
game = Game(name="Ma partie d'Ã©checs", turn_based=True)

# Initialiser l'Ã©tat de dÃ©part du jeu
game.custom_state = {"plateau": "standard", "demi_coups": 0}

alice = Player("Alice")
bob = Player("Bob")

# Ajouter les joueurs et dÃ©marrer
game.add_player(alice)
game.add_player(bob)
game.start()

print(f"Partie '{game.name}' dÃ©marrÃ©e avec l'Ã©tat : {game.state}")
```

### 2. Connexion Ã  un serveur et crÃ©ation de compte
Connexion Ã  un serveur de jeu distant et configuration d'un compte persistant.

```python
from multiplayer.client import GameClient
from multiplayer.data import PlayerRole

client = GameClient(host="localhost", port=65432)

# CrÃ©er un compte persistant
account = client.create_account(
    name="Charlie", 
    password="mot_de_passe_sur", 
    role=PlayerRole.PLAYER
)
print(f"Compte crÃ©Ã© pour {account['name']} avec le rÃ´le {account['role']}")
```

### 3. Gestion de groupe et de partie (Admin)
CrÃ©ation d'un groupe et d'une session de jeu en tant qu'administrateur.

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

# CrÃ©er un groupe et une partie Ã  l'intÃ©rieur
group = admin.create_group("Tournoi A")
remote_game = group.create_game(name="Match Final", max_players=2)

print(f"Partie créée avec l'ID : {remote_game.game_id}")
```

### 4. Jeu au tour par tour avec observateurs
Gestion d'une partie au tour par tour avec des spectateurs sur le serveur.

```python
from multiplayer.client import GameClient
from multiplayer.game import Player

client = GameClient(host="localhost", port=65432)

# RÃ©cupÃ©rer la liste des parties actives sur le serveur
active_games = client.list_games()
print(f"Parties actives sur le serveur : {list(active_games.keys())}")

if active_games:
    # Rejoindre la premiÃ¨re partie active en tant que joueur
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

### 5. AvancÃ© : TLS, attributs personnalisÃ©s et journalisation
Utilisation du chiffrement, des mÃ©tadonnÃ©es et du serveur de journalisation autonome.

```python
from multiplayer.client import GameClient
from multiplayer.game import Game

# Se connecter via TLS
client = GameClient(host="game.example.com", port=65432, use_tls=True)

# CrÃ©er une partie avec des mÃ©tadonnÃ©es personnalisÃ©es
game_options = {
    "name": "Ligue Pro",
    "difficulty": "expert",
    "map": "valles_marineris"
}
remote_game = client.create_game(**game_options)

# Si le client est configurÃ© pour envoyer des logs Ã  un serveur,
# le proxy de jeu distant les propagera automatiquement.
client.set_logging_for_client("logserver.example.com", 5000)
remote_game.configure_logging("logserver.example.com", 5000)
```

### 6. Gestion du serveur
Cet exemple montre comment lancer et gÃ©rer un serveur de jeu.

```python
import time
from multiplayer.server import GameServer

# Initialiser le serveur
# host : "0.0.0.0" pour Ã©couter sur toutes les interfaces
# port : 65432 (par dÃ©faut)
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

# Lancer le serveur (s'exÃ©cute dans un processus sÃ©parÃ©)
server.start()

try:
    print("Le serveur est en cours d'exÃ©cution. Appuyez sur Ctrl+C pour arrÃªter.")
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("ArrÃªt du serveur...")
finally:
    # ArrÃªter proprement le serveur
    server.stop()
```
