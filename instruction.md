# Instructions pour le développement de la version 2 de multiplayer

Ce document fournit les instructions pour le développement de la version 2 du module de multiplayer. Il décrit les conventions de codage, les dépendances et les spécifications techniques nécessaires pour assurer la compatibilité et la cohérence entre les différents modules du package.

## Règles générales

## Conventions sur les commentaires et les docstrings

- Tous les commentaires doivent être écrits en anglais.
- Les modules, les classes et les fonctions doivent faire l'objet de docstrings en anglais et suivre la convention PEP 257 et le style de Google.

### Conventions de nommage

- Les noms de variables, des fonctions et des méthodes doivent être descriptifs (en anglais) et utiliser la convention snake_case.
- Les noms des classes doivent être en CamelCase.
- Les noms des constantes doivent être en MAJUSCULES.
- Les noms des modules doivent être en snake_case.
- Les noms des méthodes privées doivent être précédés d'un underscore (_).
- Les variables de classes privées doivent être précédées de deux underscores (__).
- Les variables doivent être déclarées en premier dans chaque bloc de code.

### Conventions sur les exceptions
- Limiter le nombre de classes d'exceptions personnalisées à un minimum.
- Regrouper les erreurs liées dans un module séparé pour faciliter la maintenance.
- Nommer les exceptions en anglais et utiliser la convention PascalCase avec le suffix "Error".
- Hériter de la classe Exception (ou d'une sous-classe appropriée) du module builtins. Ne pas dériver directement de BaseException.
- Chaîner les exceptions avec `raise ... from ...` pour conserver la cause d'origine.
- Structurer le code avec `try/except/else/finally` pour une gestion efficace des erreurs et de la ressource, dans la mesure du possible selon le schéma suivant:

```
try:
    # Code susceptible de générer des exceptions
except SpecificError as e:
    # traitement ciblé
except Exception as e:
    # fallback générique (évite de masquer toutes les erreurs)
else:
    # Code à exécuter si aucune exception n'est levée
finally:
    # Code à exécuter indépendamment de la présence d'exceptions (nettoyage de fichiers, connexions,...)
```

- Les messages d'erreur doivent être exclusivement en anglais.
- Les messages d'erreur doivent être explicites et, si pertinent, doivent également fournir les valeurs d'entrée qui ont causé l'erreur.
- Les exceptions doivent être enregistrées avec le module logging: logging.exception("Message").
- Dans la docstring, les exceptions doivent être mentionnées (`:raises:` ou `Raises:`). Il faut y décrire les conditions qui les déclenchent.
- L'utilisation de `assert` doit être réservée aux vérifications d'invariants internes, pas à la validation des entrées utilisateur.
- Ne pas utiliser les exceptions pour le contrôle du flux normal (exemple: sortir d'une boucle), car le mécanisme d'exception est plus coûteux que les structures de contrôle classiques.

### Autres conventions

- Toutes les propriétés de type "ID" (identifiants) doivent être des chaînes de caractères alphanumériques et doivent être générées de manière unique à l'instantiation, en utilisant la fonction `uuid.uuid4()` du module uuid. Elles doivent être en lecture seule.
- Tous les objets codés doivent faire l'objet d'un ensemble de tests unitaires pour garantir leur bon fonctionnement. Ces tests doivent couvrir tous les cas possibles d'utilisation des objets et doivent être automatisés. Ils doivent pouvoir être lancés avec `pytest`.
- Le fichier `pyproject.toml` doit être conforme à la spécification du format TOML et aux instructions décrites [ici](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) et doit contenir les informations nécessaires pour la gestion du projet avec `uv`.
- Les fichiers de documentation doivent être écrits en Markdown et doivent être mis à jour régulièrement avec les modifications apportées au code.

## Organisation du code

De manière générale, les fichiers de code doivent être structurés de manière à faciliter la compréhension et la maintenance du code. Les fichiers doivent être divisés en sections logiques et chaque section doit être bien documentée.

Ce chapitre est organisé en sous-chapitres, chacun portant le nom d'un fichier source à implémenter en tant que module du package de multiplayer.

Sauf exception spécifiquement indiquée, les objets à implémenter (fonctions, classes, etc.) sont décrits selon l'effet attendu du point de vue de l'utilisateur de cet objet. Le développeur est libre d'ajouter tous les objets ou fichiers intermédiaires qu'il estime nécessaire pour réaliser cet effet final.

Les fichiers sont organisés selon le format d'un projet Python géré par `uv`, qui reprend la structure de projet standard Python (avec le fichier `pyproject.toml`), en y ajoutant quelques spécificités (telles que le fichier `uv.lock`).

Ainsi, les fichiers sources sont dans le répertoire `src/multiplayer`, les tests unitaires dans `tests/`, les fichiers de distribution dans `dist/`, et quelques scripts de tests plus complexes dans `scripts/`. `pyproject.toml`, `uv.lock`, `README.md`, ainsi que tous les autres fichiers de documentation et de configuration sont, eux, à la racine du projet.

### Contenu du fichier src/multiplayer/__init__.py

Ce fichier contient les imports nécessaires pour le fonctionnement du package de multiplayer. De manière générale, on y indique tous les éléments constants (constantes, énumérations) que les modules de multiplayer utilisent.
On y trouve en particulier les éléments suivants:

#### `PlayerRole` (Enum)
Une énumération pour le rôle d'un compte de joueur.

*   `PlayerRole.PLAYER` : Un joueur standard qui peut rejoindre et participer à des parties.
*   `PlayerRole.GROUP_ADMIN` : Un joueur qui peut gérer les parties au sein des groupes qui lui sont assignés. Ce rôle inclut toutes les permissions d'un `PLAYER`.
*   `PlayerRole.SERVER_ADMIN` : Un joueur avec un accès administratif complet au serveur. Ce rôle englobe le rôle de `GROUP_ADMIN`, lui-même pouvant également jouer le rôle de `PLAYER`.

#### `GameState` (Enum)
Une énumération représentant le statut actuel d'une partie.

*   `GameState.PENDING` : La partie a été créée mais n'a pas encore commencé. Cet état est dédié à l'attente des joueurs. Les joueurs peuvent rejoindre ou quitter la partie.
*   `GameState.PAUSING` : La partie est actuellement en pause. Cet état est utilisé lorsqu'une partie qui était en cours est temporairement suspendue.
*   `GameState.IN_PROGRESS` : La partie est actuellement active.
*   `GameState.FINISHED` : La partie est terminée. Plus aucun coup ne peut être joué et les résultats sont définitifs.

#### `ParameterFamily` (Enum)
Une énumération représentant les familles de paramètres optionnels de personnalisation des joueurs et des parties.

*   `ParameterFamily.STATIC` : Paramètres statiques qui ne changent pas ou peu pendant la partie.
*   `ParameterFamily.DYNAMIC` : Paramètres dynamiques qui peuvent être modifiés souvent pendant la partie.

#### `SaveFormat` (Enum)
Une énumération représentant les formats de stockage pris en charge par un fichier de sauvegarde.

*   `SaveFormat.JSON` : Sauvegarde dans un unique document JSON.
*   `SaveFormat.SQLITE` : Sauvegarde dans une base de données SQLite.

### Contenu du fichier src/multiplayer/exceptions.py

Ce fichier contient les définitions des exceptions personnalisées utilisées dans ce module. Il définit les classes et les fonctions nécessaires pour la gestion des erreurs spécifiques au jeu.
On y trouve en particulier les classes suivantes:

#### Classe `MultiplayerError`
Cette classe est la classe de base pour toutes les exceptions liées au module `multiplayer`. Elle sert de point de départ pour la hiérarchie des exceptions personnalisées.

#### Classe `UserAlreadyExistsError`
Cette classe est dérivée de `MultiplayerError` et est utilisée pour signaler une tentative de création d'un compte utilisateur avec un nom déjà existant.

#### Classe `SaveError`
Cette classe est dérivée de `MultiplayerError` et est utilisée pour signaler qu'un fichier de sauvegarde est incompatible, corrompu, ou ne peut pas être lu ou écrit. Elle est également levée lorsqu'un format de sauvegarde inconnu est demandé, ou qu'une classe non prise en charge est sauvegardée ou chargée.

#### Classe `GroupNotFoundError`
Cette classe est dérivée de `MultiplayerError` et est utilisée pour signaler une tentative d'utilisation d'un groupe (ou d'un ID de groupe) qui n'existe pas. Cette exception retourne dans son message l'ID erroné.

#### Classe `PlayerNotFoundError`
Cette classe est dérivée de `MultiplayerError` et est utilisée pour signaler une tentative d'utilisation d'un joueur (ou d'un ID de joueur) qui n'existe pas. Cette exception retourne dans son message l'ID erroné (si fourni).

#### Classe `PlayerNotFoundInGameError`
Cette classe est dérivée de `PlayerNotFoundError` et est utilisée pour signaler une tentative de retirer un joueur **d'une partie où il n'est pas présent**. Cette exception retourne dans son message l'ID du joueur erroné (si fourni).

#### Classe `PasswordError`:
Cette classe est dérivée de `MultiplayerError` et est utilisée pour signaler une tentative d'utilisation d'un mot de passe incorrect.

#### Classe `GameIsFullError`:
Cette classe est dérivée de `MultiplayerError` et est utilisée pour signaler une tentative d'ajouter un joueur ou un observateur à une partie qui est déjà pleine.

#### Classe `GameAlreadyStartedError`:
Cette classe est dérivée de `MultiplayerError` et est utilisée pour signaler une tentative de démarrage d'une partie qui est déjà en cours.

#### Classe `GameIsFinishedError`:
Cette classe est dérivée de `MultiplayerError` et est utilisée pour signaler une tentative de modification d'une partie qui est terminée.

#### Classe `GameNotStartedError`:
Cette classe est dérivée de `MultiplayerError` et est utilisée pour signaler une tentative de mise en pause, de redémarrage, d'arrêt ou d'évolution de jeu (passage au tour suivant par exemple) d'une partie qui n'est pas encore démarrée.

#### Classe `GameAlreadyPausedError`:
Cette classe est dérivée de `MultiplayerError` et est utilisée pour signaler une tentative de mise en pause d'une partie qui est déjà en pause.

#### Classe `GameNotPausedError`:
Cette classe est dérivée de `MultiplayerError` et est utilisée pour signaler une tentative de reprise d'une partie qui n'est pas en pause.

#### Classe `GameNotByTurnError`:
Cette classe est dérivée de `MultiplayerError` et est utilisée pour signaler une tentative d'action spécifique au tour par tour d'une partie qui n'est pas gérée au tour par tour.

#### Classe `GameNotFoundError`:
Cette classe est dérivée de `MultiplayerError` et est utilisée pour signaler une tentative de recherche d'une partie qui n'existe pas. Cette exception retourne dans son message l'ID de la partie erronée (si fourni).

#### Classe `GameNotFoundInGroupError`:
Cette classe est dérivée de `GameNotFoundError` et est utilisée pour signaler une tentative de suppression d'une partie d'un groupe qui ne contient pas cette partie. Cette exception retourne dans son message l'ID de la partie erronée (si fourni).

### Contenu du fichier src/multiplayer/game.py

Ce fichier contient la logique principale de gestion des parties. Il définit les classes et les fonctions nécessaires pour la création, la gestion et la résolution des parties.
On y trouve en particulier les classes suivantes:

#### Classe `Player`
Cette classe représente un joueur dans le contexte du jeu. C'est l'entité qui participe effectivement aux parties. Alors qu'un compte `User` gère l'accès et les permissions, l'objet `Player` porte les attributs liés au jeu (nom, score, état, etc.). Un client peut posséder plusieurs objets `Player` pendant sa session (par exemple pour gérer plusieurs participants sur le même ordinateur). L'un d'entre eux est désigné comme joueur par défaut. Tout utilisateur authentifié possède un objet `Player` qui lui est propre, qu'il retrouve à chaque connexion et qui devient alors son joueur par défaut. Un client non authentifié peut également disposer d'un ou plusieurs objets `Player` créés pour la durée de sa session.

Elle s'instantie avec les paramètres suivants:

| Nom        | Type     | Description  | Obligatoire | Valeur par défaut |
|------------|----------|--------------|-------------|-------------------|
| `name`     | str      | Le nom du joueur.  | Oui   | -                 |
| `**kwargs` | variable | Paramètres optionnels pour personnaliser le joueur. Chaque paramètre doit se présenter sous la forme d'un tuple `(famille, valeur_initiale)` dont `famille` est un objet `ParameterFamily` qui spécifie le caractère statique ou dynamique du paramètre, et `valeur_initiale` sa valeur initiale. Le choix de la famille se fait à la convenance de l'utilisateur, pour l'aider à classer les informations, mais n'a aucun impact sur le traitement interne (les familles sont toutes traitées de la même manière). | Non         | -                 |

Elle présente les attributs suivants:

| Nom             | Type | Description | Modifiable | Précision d'implémentation |
|-----------------|------|-------------|------------|----------------------------|
| `ID`            | str  | L'identifiant unique du joueur.  | Non        | S'initialise automatiquement avec la valeur de `uuid.uuid4()`.  |
| `name`          | str  | Le nom du joueur. | Oui        | S'initialise automatiquement avec le nom fourni lors de la création du joueur.|
| `static_state`  | dict | Attributs personnalisés du joueur, dont la vocation est de stocker des informations qui ne changent pas ou peu pendant la partie.  | Oui  | S'initialise automatiquement avec les paramètres spécifiés comme appartenant à la famille `ParameterFamily.STATIC`, mais peut être complété par la suite par tout autre paramètre au choix de l'utilisateur. Par exemple, si `Player` est instantié avec `Player(name="Mon nom", color=(ParameterFamily.STATIC, "white"), score=(ParameterFamily.DYNAMIC, 0))`, alors `static_state`est égal à `{"color":"white"}`. |
| `dynamic_state` | dict | Attributs personnalisés du joueur, dont la vocation est de stocker des informations qui peuvent être modifiées souvent pendant la partie. | Oui        | S'initialise automatiquement avec les paramètres spécifiés comme appartenant à la famille `ParameterFamily.DYNAMIC`, mais peut être complété par la suite par tout autre paramètre au choix de l'utilisateur. Par exemple, si `Player` est instantié avec `Player(name="Mon nom", color=(ParameterFamily.STATIC, "white"), score=(ParameterFamily.DYNAMIC, 0))`, alors `dynamic_state` est égal à `{"score":0}`.    |

#### Classe `User`
Cette classe représente un compte utilisateur. Celui-ci permet d'accéder à diverses capacités selon son niveau d'accès (authentification) et de conserver un objet `Player` qui lui est associé. Un utilisateur est une entité distincte du joueur : l'utilisateur gère les identifiants et les droits, tandis que le joueur gère la présence dans le jeu.

Elle s'instantie avec les paramètres suivants:

| Nom        | Type | Description                     | Obligatoire | Valeur par défaut  |
|------------|------|---------------------------------|-------------|--------------------|
| `username` | str  | Le nom d'utilisateur du compte. | Oui         | -                  |
| `password` | str  | Le mot de passe du compte.      | Oui         | -                  |
| `email`    | str  | L'adresse e-mail du compte.     | Non         | `""` (chaîne vide) |


Si un objet `User` est instantié avec un `username` déjà utilisé dans une instance existante de `User`, une exception `UserAlreadyExistsError` est levée et l'instantiation échoue.

La classe présente les attributs suivants:

| Nom         | Type         | Description  | Modifiable | Précision d'implémentation  |
|-------------|--------------|--------------|------------|-----------------------------|
| `ID`        | str          | L'identifiant unique du compte utilisateur. | Non | S'initialise automatiquement avec la valeur de `uuid.uuid4()`.|
| `username`  | str          | Le nom d'utilisateur du compte.  | Non  | -|
| `hash`      | str          | Le hash du mot de passe du compte.| Non  | Le hash est automatiquement généré à partir de `password` avec `bcrypt`.|
| `email`     | str          | L'adresse e-mail du compte. | Oui  | -|
| `role`      | `PlayerRole` | Le rôle du compte (ie: son niveau de permission).  | Oui  | - |
| `groups_id` | List[str]    | Les identifiants des groupes pour lesquels le compte est administrateur. Uniquement utile si `role == PlayerRole.GROUP_ADMIN`. Une exception `GroupNotFoundError` est levée si un des identifiants ne correspond pas à un groupe existant. Dans ce cas la valeur de `groups_id` n'est pas mise à jour. | Non (mais mutable) | Initialisé avec une liste vide, cet attribut peut être complété et modifié grace aux méthodes de `list` telles que `append`, `extend`, `pop`, ... Comme il s'agit d'un attribut en lecture seule, la ré-affectation est interdite. |
| `player`    | `Player`     | Le joueur associé au compte. L'objet `Player` est instantié avec le paramètre `name` égal à l'attribut `username`. Ses attributs peuvent ensuite être modifiés (dont `name`, soit directement via l'objet `Player`, soit via une requête de mise à jour du compte `User`). Lors d'une authentification, ce joueur est automatiquement ajouté à la session du client et devient son joueur par défaut. | Non (mais mutable) | L'objet `Player` instantié est conservé pendant toute la durée de vie de l'instance de `User` qui le contient, et n'est supprimé qu'à la suppression de l'instance de `User`. |

La classe `User` présente les méthodes suivantes:

- `change_password`: permet de changer le mot de passe du compte utilisateur. Le paramètre `hash` de l'instance courante est mis à jour avec le nouveau mot de passe via `bcrypt`
    - Paramètres:
      - `new_password` (str): le nouveau mot de passe à utiliser pour le compte utilisateur. Obligatoire.
    - Valeur de retour:
      - Aucune.


#### Classe `Game`
Cette classe représente une partie de jeu. Elle s'instantie avec les paramètres suivants:

| Nom                 | Type        | Description | Obligatoire | Valeur par défaut |
|---------------------|-------------|-------------|-------------|-------------------|
| `name`              | str\|`None` | Le nom de la partie.  | Non  | `None` |
| `max_players`       | int\|`None` | Nombre maximal de joueurs. Si `None`, alors il n'y a pas de limite. Si 0 ou négatif, alors aucun joueur n'est autorisé.| Non | `None` |
| `max_observers`     | int\|`None` | Nombre maximal d'observateurs. Si `None`, alors il n'y a pas de limite. Si 0 ou négatif, alors aucun observateur n'est autorisé.  | Non  | `None` |
| `password`          | str\|`None` | Mot de passe de la partie. Si `None`, alors la partie est publique (aucun mot de passe n'est nécessaire pour accéder à la partie). | Non  | `None`|
| `observer_password` | str\|`None` | Mot de passe des observateurs. Si `None`, alors les observateurs utilisent le mot de passe de la partie, défini par le paramètre `password`. Si celui-ci vaut également `None`, alors les observateurs peuvent accéder à la partie sans mot de passe. | Non | `None` |
| `turn_based`        | bool        | `True` si le jeu est au tour par tour, `False` pour un jeu simultané. | Non  | `False` |
| `**kwargs`          | variable    | Paramètres optionnels pour personnaliser la partie. Chaque paramètre doit se présenter sous la forme d'un tuple `(famille, valeur_initiale)` dont `famille` est un objet `ParameterFamily` qui spécifie le caractère statique ou dynamique du paramètre, et `valeur_initiale` sa valeur initiale. Le choix de la famille se fait à la convenance de l'utilisateur, pour l'aider à classer les informations, mais n'a aucun impact sur le traitement interne (les familles sont toutes traitées de la même manière). | Non  | - |

La classe présente les attributs suivants:

| Nom             | Type            | Description  | Modifiable | Précision d'implémentation |
|-----------------|-----------------|--------------|------------|----------------------------|
| `ID`            | str             | L'identifiant unique de la partie. | Non | S'initialise automatiquement avec la valeur de `uuid.uuid4()`.|
| `name`          | str             | Le nom de la partie. | Oui        | - |
| `hash`          | str\|`None`     | Le hash du mot de passe de la partie. `None` si la partie est publique (sans mot de passe).| Non  | Le hash est automatiquement généré à partir de `password` avec `bcrypt`. |
| `observer_hash` | str\|`None`     | Le hash du mot de passe de l'observateur. `None` si aucun mot de passe d'observation n'est défini. | Non  | Le hash est automatiquement généré à partir de `observer_password` avec `bcrypt`.|
| `turn_based`    | bool            | `True` si le jeu est au tour par tour, `False` pour un jeu simultané. | Non  | -  |
| `players`       | Tuple[`Player`] | Tuple (liste non mutable) des instances `Player` représentants les joueurs de la partie. L'ordre dans lequel sont présentés les joueurs correspond à l'ordre dans lequel les joueurs prennent leurs tours dans une partie au tour par tour. Certains jeux autorisent le changement d'ordre en cours de partie. Des méthodes spécifiques sont donc à disposition pour réaliser ces changements. Ne pas essayer de modifier l'ordre directement dans cet attribut. | Non | La variable interne correspondante ( `_players`) est une liste qui est transformée en tuple pour son affichage public au travers de l'attribut `players`. |
| `observers`     | Tuple[`Player`] | Tuple (liste non mutable) des instances `Player` représentants les observateurs de la partie. | Non  | La variable interne correspondante ( `_observers`) est une liste qui est transformée en tuple pour son affichage public au travers de l'attribut `observers`. |
| `current_player`| `Player`        | Instance `Player` représentant le joueur dont le tour est en cours. N'a de sens que pour les parties à tour par tour. | Non  | - |
| `game_state`    | `GameState` | État actuel de la partie. | Non  | - |
| `static_state`  | dict | Attributs personnalisés de la partie, dont la vocation est de stocker des informations qui ne changent pas ou peu pendant la partie.  | Oui  | S'initialise automatiquement avec les paramètres spécifiés comme appartenant à la famille `ParameterFamily.STATIC`, mais peut être complété par la suite par tout autre paramètre au choix de l'utilisateur. Par exemple, si `Game` est instantié avec `Game([...], style=(ParameterFamily.STATIC, "blitz"), score=(ParameterFamily.DYNAMIC, "0-0"))`, alors `static_state`est égal à `{"style":"blitz"}`. |
| `dynamic_state` | dict | Attributs personnalisés de la partie, dont la vocation est de stocker des informations qui peuvent être modifiées souvent pendant la partie. | Oui        | S'initialise automatiquement avec les paramètres spécifiés comme appartenant à la famille `ParameterFamily.DYNAMIC`, mais peut être complété par la suite par tout autre paramètre au choix de l'utilisateur. Par exemple, si `Game` est instantié avec `Game([...], style=(ParameterFamily.STATIC, "blitz"), score=(ParameterFamily.DYNAMIC, "0-0"))`, alors `dynamic_state` est égal à `{"score":"0-0"}`.    |

La classe `Game` présente les méthodes suivantes:

- `change_password`: permet de changer le mot de passe de la partie. Le paramètre `hash` de l'instance courante est mis à jour avec le nouveau mot de passe via `bcrypt`
    - Paramètres:
      - `new_password` (str): le nouveau mot de passe à utiliser pour le compte utilisateur. Obligatoire.
    - Valeur de retour:
      - Aucune.
- `join_game_as_player`: permet de rejoindre une partie en tant que joueur.
  - Description: Cette méthode permet à un joueur de rejoindre une partie en spécifiant son ID ou son objet `Player` et éventuellement un mot de passe si la partie est privée. Elle lance une exception si le joueur n'existe pas ou si le mot de passe est incorrect.
  - Précision d'implémentation: En cas de succès, la méthode ajoute l'objet `Player` à la liste `_players` de l'instance courante.
  - Paramètres:
    - `player` (`Player`|str): le joueur qui rejoint la partie. Il s'agit soit de l'objet `Player` correspondant au joueur, soit une chaîne de caractères correspondant à son ID. Obligatoire.
    - `password` (str\|`None`): mot de passe pour rejoindre la partie. Si la partie est publique, alors il faut indiquer `None`. Optionnel. Valeur par défaut: `None`.
  - Exceptions émises:
    - `PlayerNotFoundError`: levée si le joueur spécifié n'existe pas.
    - `PasswordError`: levée si le mot de passe est incorrect.
    - `GameIsFullError`: levée si le nombre maximal de joueurs est atteint, et que l'ajout d'un nouveau joueur est impossible.
  - Valeur de retour: Aucune.

- `remove_player`: permet de retirer un joueur de la partie.
  - Description: Cette méthode permet de retirer un joueur de la partie en spécifiant son ID ou son objet `Player`. Elle lance une exception si le joueur n'est pas trouvé dans la partie.
  - Précision d'implémentation: En cas de succès, la méthode retire l'objet `Player` de la liste `_players` de l'instance courante.
  - Paramètres:
    - `player` (`Player`|str): le joueur à retirer de la partie. Il s'agit soit de l'objet `Player` correspondant au joueur, soit une chaîne de caractères correspondant à son ID. Obligatoire.
  - Exceptions émises:
    - `PlayerNotFoundInGameError`: levée si le joueur spécifié n'est pas trouvé dans la partie.
  - Valeur de retour: Aucune.

- `join_game_as_observer`: permet de rejoindre une partie en tant qu'observateur.
  - Description: Cette méthode permet à un joueur de rejoindre une partie en tant qu'observateur. Elle lance une exception si la partie est privée et que le mot de passe est incorrect.
  - Précision d'implémentation: En cas de succès, la méthode ajoute l'objet `Player` à la liste `_observers` de l'instance courante.
  - Paramètres:
    - `player` (`Player`|str): le joueur qui rejoint la partie en tant qu'observateur. Il s'agit soit de l'objet `Player` correspondant au joueur, soit une chaîne de caractères correspondant à son ID. Obligatoire.
    - `password` (str\|`None`): mot de passe pour rejoindre la partie en tant qu'observateur. Si l'observation de la partie est publique, alors il faut indiquer `None`. Optionnel. Valeur par défaut: `None`.
  - Exceptions émises:
    - `PlayerNotFoundError`: levée si le joueur spécifié n'existe pas.
    - `PasswordError`: levée si la partie est privée et que le mot de passe est incorrect.
    - `GameIsFullError`: levée si le nombre maximal d'observateurs est atteint, et que l'ajout d'un nouvel observateur est impossible.
  - Valeur de retour: Aucune.

- `remove_observer`: permet de retirer un observateur d'une partie.
  - Description: Cette méthode permet à un observateur de quitter une partie. Elle lance une exception si le joueur spécifié n'est pas trouvé dans la partie.
  - Précision d'implémentation: En cas de succès, la méthode retire l'objet `Player` de la liste `_observers` de l'instance courante.
  - Paramètres:
    - `player` (`Player`|str): le joueur qui quitte la partie en tant qu'observateur. Il s'agit soit de l'objet `Player` correspondant au joueur, soit une chaîne de caractères correspondant à son ID. Obligatoire.
  - Exceptions émises:
    - `PlayerNotFoundInGameError`: levée si le joueur spécifié n'est pas trouvé dans la partie.
  - Valeur de retour: Aucune.

- `start`: permet de démarrer une partie.
  - Description: Cette méthode permet de démarrer une partie. Elle lance une exception si la partie est déjà en cours ou si elle est terminée. En cas de succès, la méthode passe l'attribut `game_state` à la valeur `GameState.IN_PROGRESS`.
  - Précision d'implémentation: Le statut `GameState.PAUSING` est aussi considéré comme une partie en cours.
  - Paramètres:
    - Aucun.
  - Exceptions émises:
    - `GameAlreadyStartedError`: levée si la partie est déjà en cours.
    - `GameIsFinishedError`: levée si la partie est terminée.
  - Valeur de retour: Aucune.

- `pause`: permet de mettre en pause une partie.
  - Description: Cette méthode permet de mettre en pause une partie. Elle lance une exception si la partie n'est pas en cours ou si elle est déjà en pause.
  - Précision d'implémentation: En cas de succès, la méthode passe l'attribut `game_state` à la valeur `GameState.PAUSING`.
  - Paramètres:
    - Aucun.
  - Exceptions émises:
    - `GameNotStartedError`: levée si la partie n'est pas en cours.
    - `GameAlreadyPausedError`: levée si la partie est déjà en pause.
  - Valeur de retour: Aucune.
  
- `resume`: permet de reprendre une partie en pause.
  - Description: Cette méthode permet de reprendre une partie en pause. Elle lance une exception si la partie n'est pas en pause.
  - Précision d'implémentation: En cas de succès, la méthode passe l'attribut `game_state` à la valeur `GameState.IN_PROGRESS`.
  - Paramètres:
    - Aucun.
  - Exceptions émises:
    - `GameNotPausedError`: levée si la partie n'est pas en pause.
  - Valeur de retour: Aucune.

- `stop`: permet de terminer une partie.
  - Description: Cette méthode permet de terminer une partie. Elle lance une exception si la partie n'est pas en cours.
  - Précision d'implémentation: En cas de succès, la méthode passe l'attribut `game_state` à la valeur `GameState.FINISHED`.
  - Paramètres:
    - Aucun.
  - Exceptions émises:
    - `GameNotStartedError`: levée si la partie n'est pas en cours.
  - Valeur de retour: Aucune.

- `next_turn`: permet de passer au tour suivant.
  - Description: Dans le cas d'une partie au tour par tour, cette méthode permet de passer au tour suivant. Elle lance une exception si la partie n'est pas en cours ou si elle est terminée. En cas de succès, la méthode passe l'attribut `current_player` au joueur suivant.
  - Paramètres:
    - Aucun.
  - Exceptions émises:
    - `GameNotStartedError`: levée si la partie n'est pas en cours.
    - `GameIsFinishedError`: levée si la partie est terminée.
    - `GameNotTurnBasedError`: levée si la partie n'est pas gérée au tour par tour.
  - Valeur de retour: Aucune.

- `reverse_order`: permet d'inverser l'ordre des joueurs dans une partie au tour par tour.
  - Description: Cette méthode permet d'inverser l'ordre des joueurs dans une partie. Cette inversion d'ordre peut se réaliser dans tout état de la partie autre que `GameState.FINISHED`. Elle lance une exception si la partie est terminée. En cas de succès, la méthode inverse l'ordre des joueurs dans l'attribut `players`.
  - Précision d'implémentation: En cas de succès, la méthode inverse en fait l'ordre dans la liste interne `_players`.
  - Paramètres:
    - Aucun.
  - Exceptions émises:
    - `GameIsFinishedError`: levée si la partie est terminée.
    - `GameNotTurnBasedError`: levée si la partie n'est pas gérée au tour par tour.
  - Valeur de retour: Aucune.

- `set_player_rank`: permet de spécifier le rang d'un joueur dans une partie au tour par tour.
  - Description: Cette méthode permet de spécifier le rang d'un joueur dans une partie au tour par tour. Les autres joueurs gardent le même ordre, leur rang est incrémenté ou décrémenté pour combler la place que le joueur quitte, et pour lui laisser la place qu'il rejoint. Ce changement de rang peut se réaliser dans tout état de la partie autre que `GameState.FINISHED`. Elle lance une exception si la partie est terminée. En cas de succès, la modification de rang apparait dans l'attribut `players`.
  - Précision d'implémentation: En cas de succès, la méthode modifie en fait la liste interne `_players`.
  - Paramètres:
    - `player` (`Player`|str): le joueur à qui on modifie le rang. Il s'agit soit de l'objet `Player` correspondant au joueur, soit une chaîne de caractères correspondant à son ID. Obligatoire.
    - `rank` (int): le nouveau rang du joueur. Obligatoire.
  - Exceptions émises:
    - `IndexError`: levée si le rang spécifié est invalide.
    - `GameIsFinishedError`: levée si la partie est terminée.
    - `GameNotTurnBasedError`: levée si la partie n'est pas gérée au tour par tour.
    - `PlayerNotFoundInGameError`: levée si le joueur spécifié n'est pas trouvé dans la partie.
  - Valeur de retour: Aucune.

#### Classe `GameGroup`
Cette classe permet de regrouper plusieurs parties dans un seul objet. Elle permet de gérer les parties en parallèle et de les manipuler en tant que groupe. Elle s'instantie avec les paramètres suivants:

| Nom                 | Type        | Description | Obligatoire | Valeur par défaut |
|---------------------|-------------|-------------|-------------|-------------------|
| `name`              | str         | Le nom du groupe de parties.| Oui | - |
| `**kwargs`          | variable    | Paramètres optionnels pour personnaliser le groupe. | Non  | - |

La classe présente les attributs suivants:

| Nom             | Type            | Description  | Modifiable | Précision d'implémentation |
|-----------------|-----------------|--------------|------------|----------------------------|
| `ID`            | str             | L'identifiant unique du groupe. | Non | S'initialise automatiquement avec la valeur de `uuid.uuid4()`.|
| `name`          | str             | Le nom ddu groupe. | Oui        | - |
| `games`       | Tuple[`Game`] | Tuple (liste non mutable) des instances `Game` représentants les parties du groupe. | Non | La variable interne correspondante ( `_games`) est une liste qui est transformée en tuple pour son affichage public au travers de l'attribut `games`. |
| `parameters` | dict | Paramètres de personnalisation du groupe | Oui        | S'initialise automatiquement avec les paramètres spécifiés dans `kwargs`, mais peut être complété par la suite par tout autre paramètre au choix de l'utilisateur. |


La classe `GameGroup` présente les méthodes suivantes:

- `add_game`: permet d'ajouter une partie au groupe. La partie est ajoutée à la fin de la liste des parties du groupe. 
  - Description: Cette méthode permet d'ajouter une partie au groupe en spécifiant son ID ou son objet `Game` et éventuellement un mot de passe administrateur de groupe. Elle lance une exception si la partie n'existe pas ou si le mot de passe est incorrect. 
  - Précision d'implémentation: En cas de succès, la méthode ajoute l'objet `Game` à la liste `_games` de l'instance courante.
  - Paramètres:
    - `game` (`Game`|str): l'instance de la partie à ajouter, ou une chaîne de caractères représentant l'ID de la partie à ajouter. Obligatoire.
  - Valeur de retour:
    - Aucune.
  - Exceptions émises:
    - `GameNotFoundError`: levée si la partie spécifiée n'existe pas.
- `remove_game`: permet de retirer une partie du groupe. La partie est retirée de la liste des parties du groupe.
  - Paramètres:
    - `game` (`Game`|str): l'instance de la partie à retirer, ou une chaîne de caractères représentant l'ID de la partie à retirer. Obligatoire.
  - Précision d'implémentation: En cas de succès, la méthode retire l'objet `Game` de la liste `_games` de l'instance courante.
  - Valeur de retour:
    - Aucune.
  - Exceptions émises:
    - `GameNotFoundInGroupError`: levée si la partie spécifiée n'est pas présente dans le groupe.

### Contenu du fichier src/multiplayer/utils.py

Le package fournit des fonctions utilitaires pour suggérer des noms de parties et de joueurs basés sur différentes catégories.


#### Catégories pour les Parties
*   **`cities`** : Grandes villes du monde.
*   **`countries`** : Nations souveraines.
*   **`rivers`** : Fleuves importants du monde.
*   **`seas_oceans`** : Principales étendues d'eau salée.
*   **`planets_moons`** : Corps célestes de notre système solaire.

Précision d'implémentation: 
*   Les catégories sont stockées dans des fichiers texte simples, avec un nom par ligne, dans le répertoire `src/multiplayer/data` (un fichier par catégorie).
*   Les fichiers CSV sont pris en charge pour permettre une structure plus complexe si nécessaire.
*   Les noms sont normalisés pour éviter les doublons et les caractères spéciaux.

#### Catégories pour les Joueurs
*   **`roman_gods`** : Divinités de la mythologie romaine.
*   **`greek_gods`** : Divinités de la mythologie grecque antique.
*   **`egyptian_gods`** : Divinités de la mythologie égyptienne antique.
*   **`european_kings`** : Monarques européens historiques (hommes).
*   **`european_queens`** : Monarques européens historiques (femmes).

Précision d'implémentation: 
*   Les catégories sont stockées dans des fichiers texte simples, avec un nom par ligne, dans le répertoire `src/multiplayer/data` (un fichier par catégorie).
*   Les fichiers CSV sont pris en charge pour permettre une structure plus complexe si nécessaire.
*   Les noms sont normalisés pour éviter les doublons et les caractères spéciaux.

#### Fonction `register_name_category(category_name, data, category_type)`
Enregistre une nouvelle catégorie personnalisée pour les suggestions de noms.

*   **`category_name`** (`str`) : Le nom de la nouvelle catégorie.
*   **`data`** (`list`, `str` ou `Path`) : Une liste de noms, ou un chemin vers un fichier texte/CSV (un nom par ligne, ou première colonne du CSV).
*   **`category_type`** (`str`) : `"game"` ou `"player"`.

#### Fonction `unregister_name_category(category_name)`
Supprime une catégorie personnalisée. Retourne `True` en cas de succès.

#### Fonction `get_available_categories(category_type="all")`
Retourne une liste des catégories de suggestions de noms disponibles.

*   **`category_type`** (`str`) : `"all"`, `"game"`, ou `"player"`.

#### Fonction `suggest_game_name(category=None)`
Suggère un nom aléatoire pour une partie. Si `category` est `None`, une catégorie liée aux parties est choisie aléatoirement.

#### Fonction `suggest_player_name(category=None)`
Suggère un nom aléatoire pour un joueur. Si `category` est `None`, une catégorie liée aux joueurs est choisie aléatoirement.

### Contenu du fichier src/multiplayer/save.py

Ce fichier contient la logique de sauvegarde et de restauration des objets instanciés à partir des classes `Player`, `User`, `Game` et `GameGroup`. Il définit la classe `Save`, dont chaque instance représente un fichier de sauvegarde et fait le lien entre un tampon en mémoire et un fichier persistant (document JSON ou base de données SQLite).

#### Classe `Save`
Cette classe permet de sauvegarder, de mettre à jour et de restaurer les objets du module. Les objets sont d'abord enregistrés dans un tampon en mémoire, puis écrits dans le fichier uniquement lors de l'appel explicite à la méthode `flush`. Elle s'instancie avec les paramètres suivants:

| Nom           | Type                | Description | Obligatoire | Valeur par défaut |
|---------------|---------------------|-------------|-------------|-------------------|
| `file_path`   | `Path`              | Le chemin du fichier de sauvegarde. | Oui | - |
| `save_format` | `SaveFormat`\|str   | Le format de sauvegarde. Il s'agit soit d'un membre de l'énumération `SaveFormat`, soit d'une chaîne de caractères (`"json"` ou `"sqlite"`). | Oui | - |

Comportement à l'instantiation:
*   Si le fichier n'existe pas, il est créé avec une structure vide mais valide.
*   Si le fichier existe déjà, sa structure est contrôlée. S'il est compatible avec le format demandé, son contenu est chargé dans le tampon en mémoire. Sinon, une exception `SaveError` est levée.
*   Si le format de sauvegarde est inconnu, une exception `SaveError` est levée.

La classe présente les attributs suivants:

| Nom           | Type         | Description | Modifiable | Précision d'implémentation |
|---------------|--------------|-------------|------------|----------------------------|
| `file_path`   | `Path`       | Le chemin du fichier de sauvegarde. | Oui | S'initialise à partir du paramètre `file_path`. |
| `save_format` | `SaveFormat` | Le format de stockage utilisé. | Oui | S'initialise à partir du paramètre `save_format`. |

La classe `Save` présente les méthodes suivantes:

- `save`: permet de sauvegarder ou de mettre à jour une instance individuelle dans le tampon en mémoire.
  - Description: L'objet est sérialisé et stocké dans le tampon, indexé par sa classe et son ID. Si un objet de même classe et de même ID existe déjà, il est remplacé. La modification n'est persistée dans le fichier qu'à l'appel de `flush`.
  - Paramètres:
    - `obj` (`Player`|`User`|`Game`|`GameGroup`): l'instance à sauvegarder. Obligatoire.
  - Exceptions émises:
    - `SaveError`: levée si l'objet n'est pas une instance d'une classe prise en charge.
  - Valeur de retour: Aucune.

- `load`: permet de charger toutes les instances d'une classe donnée.
  - Description: Reconstruit et retourne la liste des instances de la classe demandée à partir du tampon en mémoire.
  - Paramètres:
    - `target` (str\|type): la classe à charger ou son nom (`Player`, `User`, `Game` ou `GameGroup`). Obligatoire.
  - Exceptions émises:
    - `SaveError`: levée si la cible ne correspond pas à une classe prise en charge.
  - Valeur de retour: La liste des instances reconstruites de la classe demandée.

- `reset`: permet de réinitialiser le fichier de sauvegarde.
  - Description: Vide le tampon en mémoire et réécrit le fichier de sauvegarde avec une structure vide mais valide.
  - Paramètres:
    - Aucun.
  - Valeur de retour: Aucune.

- `flush`: permet d'écrire effectivement le tampon en mémoire dans le fichier de sauvegarde.
  - Description: Persiste l'ensemble des objets du tampon dans le fichier selon le format choisi. Cette méthode doit être appelée pour rendre les sauvegardes effectives sur le disque.
  - Paramètres:
    - Aucun.
  - Exceptions émises:
    - `SaveError`: levée si les données ne peuvent pas être écrites dans le fichier.
  - Valeur de retour: Aucune.

### Contenu du fichier src/multiplayer/server.py

Ce fichier contient la logique de gestion des serveurs multijoueur.

#### Classe GameServer
La classe `GameServer` est responsable de la gestion des connexions et des communications avec les clients dans un environnement multijoueur. Elle assure la coordination des actions et la diffusion des informations aux joueurs connectés.

##### Paramètres

La classe `GameServer` s'instancie avec les paramètres suivants:

| Nom           | Type                | Description | Obligatoire | Valeur par défaut |
|---------------|---------------------|-------------|-------------|-------------------|
| `host`        | str                 | L'adresse IPv4 sur laquelle le serveur écoute les connexions | Non | `"0.0.0.0"` |
| `port`        | int                 | Le numéro de port sur lequel le serveur écoute les connexions | Non | 65432 |
| `unencrypted_port`        | int\|`None`                 | Le numéro de port non sécurisé pour les connexions non protégées par TLS | Non | `None` |
| `password`    | str\|`None`          | Le mot de passe pour accéder au serveur | Non | `None` |
| `name`        | str          | Le nom du serveur | Non | `""` (chaîne vide) |
| `use_tls`     | bool                | Utiliser le protocole TLS v1.3 pour la communication sécurisée | Non | `False` |
| `tls_self_signed` | bool                | Utiliser un certificat auto-signé pour le TLS | Non | `False` |
| `tls_domain`  | str          | Le nom de domaine utilisé pour la validation du certificat TLS | Non | `"localhost"` |
| `tls_cert_path` | `Path\|None` | Le chemin vers le certificat TLS | Non | `None` |
| `tls_key_path`  | `Path\|None` | Le chemin vers la clé privée TLS | Non | `None` |
| `discoverable` | bool                | Si `True`, permets aux clients de rechercher le serveur sur le réseau local au travers d'une découverte multicast | Non | `False` |
| `multicast_group` | str          | L'adresse multicast utilisée pour la découverte du serveur | Non | `"239.255.0.1"` |
| `multicast_port` | int          | Le numéro de port multicast utilisé pour la découverte du serveur | Non | 65434 |
| `persistence_mode` | `SaveFormat\|None` | Le mode de persistance des données du serveur | Non | `None` |
| `persistence_path` | `Path\|None` | Le chemin vers le fichier de persistance des données du serveur | Non | `None` |
| `garbage_collection_periodicity` | `int` | La durée en secondes entre chaque effacement des objets "Player" orphelins (associés à une session inexistante) | Non | 900 |

Informations complémentaires:
- l’adresse `host` désigne l’adresse IP ou le nom réseau sur lequel le serveur va écouter les connexions entrantes. Si l'on ne souhaite pas que le serveur soit accessible sur le réseau (cas d'un serveur local utilisé uniquement sur la même machine que les clients), alors il faut définir `127.0.0.1` ou `localhost`. Si l'on souhaite au contraire que le serveur soit accessible depuis le réseau sur **toutes** les interfaces réseau du serveur, alors il faut définir `0.0.0.0` (c'est la valeur par défaut). Enfin, si l'on souhaite que le serveur ne soit accessible que depuis une interface réseau spécifique, alors il faut indiquer l'adresse IP de cette interface (utile pour limiter volontairement l'exposition du serveur).
- **Choix des ports**: un port est un entier compris entre 0 et 65535. C'est un numéro qui identifie une **application ou un service** sur une machine. Le port `0` a un sens particulier : il peut demander au système de choisir automatiquement un port libre. Pour un serveur que des clients doivent retrouver facilement, on utilise généralement un port fixe. Par ailleurs, tous les ports ne sont pas équivalents:

| Plage | Nom | Usage |
|---:|---|---|
| `0` à `1023` | Ports bien connus | Services standards : HTTP, HTTPS, SSH… |
| `1024` à `49151` | Ports enregistrés | Applications connues ou services spécifiques |
| `49152` à `65535` | Ports dynamiques / éphémères | Souvent utilisés temporairement par les clients |

  - paramètre `port`: il s'agit du port TCP que le serveur écoute pour les connexions et les messages des clients. Par défaut il vaut 65432, si aucun port n'est spécifié lors de l'instanciation du serveur. L'utilisateur peut spécifier un port différent si nécessaire, il est dans ce cas conseillé de rester dans la plage 49152 à 65535. Dans certains cas particuliers (difficulté à trouver un port de libre par exemple), il est possible de définir le port à 0, mais dans ce cas il est indispensable d'autoriser la découverte réseau, sinon les clients seront dans l'impossibilité de se connecter, la découverte réseau étant le seul moyen de connaître le port que la machine allouera dynamiquement au serveur.
  - paramètre `unencrypted_port`: il s'agit du port TCP que le serveur écoute pour les connexions non sécurisées. Par défaut il vaut `None`, ce qui signifie que le serveur ne propose pas de connexion non sécurisée. Si ce paramètre est défini et différent de `None`, alors il doit être un entier compatible avec la numérotation des ports TCP, et différent de `port`. Dans ce cas, ce port permet d'accéder au serveur sans avoir à utiliser la sécurisation TLS, quand bien même `use_tls=True`.
  - paramètre `multicast_port`: il s'agit du port UDP que le serveur écoute pour les messages multicast. Par défaut il vaut 65434, si aucun port n'est spécifié lors de l'instanciation du serveur. L'utilisateur peut spécifier un port différent si nécessaire, il est dans ce cas conseillé de rester dans la plage 49152 à 65535. Le port **ne doit pas** être 0, le client serait alors dans l'impossibilité de connaitre le **vrai** port fourni dynamiquement par le système d'exploitation du serveur.
- **sécurisation des communications**: le serveur peut être configuré pour utiliser le TLS pour sécuriser les communications entre le serveur et les clients. Pour cela, le serveur doit être instancié avec `use_tls=True`. Dans ce cas, soit le serveur génère et utilise un certificat auto-signé (si `tls_self_signed=True`), soit il faut fournir le chemin vers le certificat TLS (`tls_cert_path`) et la clé privée TLS (`tls_key_path`). Si l'un des deux manque, une exception est levée et le serveur n'est pas instancié. Dans le cas du certificat TLS, il est possible de fournir soit un fichier "Full Chain" (c'est-à-dire contenant le certificat de domaine et les certificats intermédiaires), soit uniquement le fichier "cert", mais dans ce cas il doit exister un fichier "chain" correspondant dans le même répertoire (par exemple `cert.pem` et `chain.pem`, ou `ECC-cert.pem` et `ECC-chain.pem`). Par ailleurs, si `unencrypted_port` n'est pas `None` et est un entier compatible avec la numérotation des ports TCP, et n'est pas égal à `port`, alors ce port permet d'accéder au serveur sans avoir à utiliser la sécurisation TLS, quand bien même `use_tls=True`. Enfin, si `password` est défini et différent de `None`, alors ce mot de passe **doit** être utilisé pour accéder au serveur, en port sécurisé comme en port non sécurisé. Voir la partie Commandes pour avoir les modalités d'utilisation du mot de passe. 
- **Découverte réseau**: un client peut rechercher les serveurs disponibles sur le réseau local. Pour cela, le serveur doit être instancié avec `discoverable=True`. Le principe est ici le suivant:
  1. Un serveur écoute sur l'adresse multicast `multicast_group` et le port UDP `multicast_port`.
  2. Un client envoie un message de découverte à cette adresse multicast. Voir le [Protocole d'échanges entre le client et le serveur](protocole.md) pour la description du protocole utilisé.
  3. Tous les serveurs abonnés au groupe multicast reçoivent le message.
  4. À la réception de ce message, chaque serveur vérifie que les données reçues correspondent aux attentes et répond directement au client en unicast UDP. Voir le [Protocole d'échanges entre le client et le serveur](protocole.md) pour la description du protocole utilisé.
- **Persistance**: La persistance permet de sauvegarder les données du serveur sur le disque dur, et de les restaurer lors du redémarrage du serveur. Par défaut, la persistance est désactivée (paramètre `persistence_mode=None`). Lorsque la persistance est activée, les données du serveur sont sauvegardées dans un fichier défini par le paramètre `persistence_path`. Le fichier est sauvegardé à chaque fois que le serveur est arrêté, et restauré lors du redémarrage du serveur. Il peut être également sauvegardé ou rechargé à la demande (voir les commandes de niveau **administrateur** dans le [Protocole d'échanges entre le client et le serveur](protocole.md)). Il est possible d'activer 2 modes de persistance :
  - `persistence_mode=SaveFormat.JSON` : permet de sauvegarder les données du serveur dans un fichier JSON. Par défaut (si `persistence_path=None`), le fichier est défini par `Path("data/server_data.json")`. Le fichier (ainsi que les répertoires y accédant) est créé automatiquement s'il n'existe pas déjà.
  - `persistence_mode=SaveFormat.SQLITE` : permet de sauvegarder les données du serveur dans une base de données SQLITE. Par défaut (si `persistence_path=None`), le fichier est défini par `Path("data/server_data.db")`. La base de données (ainsi que les répertoires y accédant) est créée automatiquement si elle n'existe pas déjà.
- **Nettoyage automatique** : Le serveur effectue périodiquement un nettoyage des objets `Player` orphelins. Un joueur est considéré comme orphelin s'il est associé à une session client qui n'existe plus (déconnexion) ET qu'il n'est associé à aucun `User`. La fréquence de ce nettoyage est définie par le paramètre `garbage_collection_periodicity` (en secondes).

La classe `GameServer` présente les méthodes suivantes:
- `start`: Lance le serveur en mode asynchrone.
  - Description: Démarre le serveur en mode asynchrone, permettant de gérer les connexions et les requêtes des clients de manière concurrente. Cette méthode doit être appelée pour démarrer le serveur et mettre en place les écouteurs de réseau nécessaires. Si la persistance est activée, alors si le fichier indiqué existe et est compatible avec le format de sauvegarde choisi, les données sont chargées en mémoire et utilisées. Si le fichier n'existe pas, alors il est créé dans l'attente de recevoir les données. S'il n'y a pas de compte administrateur (même après avoir éventuellement chargé les données), alors le serveur créé le compte administrateur `admin` avec le mot de passe `admin`. Bien entendu, il est **très fortement** conseillé de modifier son mot de passe, ou mieux, de créer un nouveau compte administrateur et de supprimer celui-là dès que possible.
  - Paramètres: aucun
  - Retour: aucun
- `stop`: Arrête le serveur.
  - Description: Arrête le serveur en tentant de fermer proprement les connexions et de sauvegarder les données si la persistance est activée.
  - Paramètres: aucun
  - Retour: aucun
- `restart`: Redémarre le serveur.
  - Description: Redémarre le serveur en fermant proprement les connexions, en sauvegardant et en rechargeant les données si la persistance est activée. Similaire à `stop` puis `start`.
  - Paramètres: aucun
  - Retour: aucun

### Contenu du fichier src/multiplayer/client.py

Ce fichier contient la logique de gestion des clients multijoueur.

#### Classe GameClient
La classe `GameClient` est responsable de la connexion et de la communication avec un serveur `GameServer`. Elle permet de découvrir des serveurs sur le réseau, de s'y connecter de manière sécurisée ou non, de s'authentifier et d'échanger des messages (requêtes, réponses et notifications) selon le protocole défini.

##### Paramètres

La classe `GameClient` s'instancie avec les paramètres suivants:

| Nom | Type | Description | Obligatoire | Valeur par défaut |
|---|---|---|---|---|
| `host` | str | L'adresse IPv4 ou le nom d'hôte du serveur | Non | `"127.0.0.1"` |
| `port` | int | Le numéro de port TCP du serveur | Non | 65432 |
| `use_tls` | bool | Utiliser le protocole TLS pour la communication sécurisée | Non | `False` |
| `tls_ca_path` | `Path\|None` | Le chemin vers le certificat de l'autorité de certification (ou le certificat auto-signé du serveur) pour la validation TLS. Si `None`, les certificats de confiance du système sont utilisés. | Non | `None` |

##### Attributs

La classe présente les attributs suivants:

| Nom | Type | Description | Modifiable | Précision d'implémentation |
|---|---|---|---|---|
| `host` | str | L'adresse IPv4 ou le nom d'hôte du serveur | Oui | - |
| `port` | int | Le numéro de port TCP du serveur | Oui | - |
| `tls_ca_path` | `Path\|None` | Le chemin vers le certificat de validation TLS. Si `None`, utilise les certificats du système. | Non | - |
| `is_connected` | bool | Indique si le client est actuellement connecté au serveur | Non | - |
| `session_player` | `Player\|None` | Le joueur par défaut associé à la session actuelle | Non | Mis à jour automatiquement lors de l'authentification ou de la création d'un joueur. |

##### Méthodes

La classe `GameClient` présente les méthodes suivantes:

- `discover` (méthode de classe): Recherche les serveurs disponibles sur le réseau local.
  - Description: Envoie un message de découverte multicast en UDP et collecte les réponses des serveurs actifs.
  - Paramètres:
    - `timeout` (float): Temps d'attente maximum pour la réception des réponses (en secondes). Optionnel. Valeur par défaut: 2.0.
    - `multicast_group` (str): L'adresse multicast à utiliser. Optionnel. Valeur par défaut: `"239.255.0.1"`.
    - `multicast_port` (int): Le port multicast à utiliser. Optionnel. Valeur par défaut: 65434.
  - Valeur de retour: Une liste de dictionnaires, chaque dictionnaire contenant les informations d'un serveur découvert (nom, host, port, etc.).
- `connect`: Établit la connexion TCP avec le serveur.
  - Description: Tente d'ouvrir une connexion avec le serveur en utilisant les paramètres `host`, `port` et `use_tls` (ainsi que `tls_ca_path` si fourni, sinon utilise les certificats racines du système).
  - Paramètres: Aucun.
  - Valeur de retour: Aucun.
  - Exceptions émises:
    - `ConnectionError`: si la connexion échoue.
- `disconnect`: Ferme la connexion avec le serveur.
  - Description: Ferme proprement la connexion TCP actuelle.
  - Paramètres: Aucun.
  - Valeur de retour: Aucun.
- `login`: S'authentifie auprès du serveur.
  - Description: Envoie une requête d'authentification avec les identifiants fournis. En cas de succès, le client récupère les informations de l'utilisateur et son joueur associé.
  - Paramètres:
    - `username` (str): Le nom d'utilisateur. Obligatoire.
    - `password` (str): Le mot de passe. Obligatoire.
  - Valeur de retour: L'instance `User` correspondant à l'utilisateur authentifié.
  - Exceptions émises:
    - `PasswordError`: si le mot de passe est incorrect.
    - `PlayerNotFoundError`: si l'utilisateur n'existe pas.
- `send_request`: Envoie une requête au serveur et attend sa réponse.
  - Description: Méthode de bas niveau permettant d'envoyer n'importe quelle commande supportée par le protocole et de recevoir la réponse correspondante.
  - Paramètres:
    - `command` (str): Le nom de la commande/action à exécuter. Obligatoire.
    - `**kwargs`: Les arguments associés à la commande.
  - Valeur de retour: Un dictionnaire contenant les données de la réponse du serveur.
  - Exceptions émises:
    - `MultiplayerError` (ou une sous-classe): si le serveur retourne une erreur.
- `on_notification`: Enregistre une fonction de rappel pour traiter les notifications.
  - Description: Permet d'associer une fonction à un type de notification spécifique ou à toutes les notifications.
  - Paramètres:
    - `notification_type` (str|None): Le type de notification à écouter (ex: `"GAME_EVENT"`). Si `None`, le callback reçoit toutes les notifications.
    - `callback` (callable): La fonction à appeler, acceptant le dictionnaire de notification en argument.
  - Valeur de retour: Aucun.

Informations complémentaires:
- **Gestion des notifications**: Le client doit être capable de recevoir et de traiter les notifications envoyées spontanément par le serveur. L'implémentation repose sur l'enregistrement de fonctions de rappel (*callbacks*) via la méthode `on_notification`. Lorsqu'une notification arrive, le client identifie les callbacks enregistrés pour ce type (ou les callbacks globaux) et les exécute de manière asynchrone ou séquentielle selon l'architecture choisie.

  **Liste exhaustive des types de notifications (extraits du protocole) :**
  - `SERVER_SHUTDOWN` : Prévient les clients que le serveur va s'arrêter prochainement.
  - `GROUP_GAME_ADDED` : Informe les clients qu'une partie vient d'être ajoutée à un groupe.
  - `GROUP_GAME_REMOVED` : Informe les clients qu'une partie vient d'être retirée d'un groupe.
  - `GROUP_GAME_UPDATED` : Informe les clients qu'une partie d'un groupe a changé d'état ou de propriétés visibles.
  - `GAME_EVENT` : Notifie les participants d'une action effectuée par l'un d'entre eux ou par le serveur.
  - `GAME_STATE_CHANGED` : Informe les clients que l'état global ou personnalisé de la partie a été modifié.
  - `GAME_TURN_CHANGED` : Prévient les clients connectés qu'un nouveau tour commence et identifie le joueur actif.

  **Exemple d'utilisation :**
  ```python
  # Gestion des événements de jeu
  def my_game_handler(notification):
      payload = notification["payload"]
      print(f"Action {payload['action_type']} reçue de {payload['player_id']}")

  client.on_notification("GAME_EVENT", my_game_handler)

  # Gestion globale des notifications (log)
  client.on_notification(None, lambda n: logging.info(f"Notification reçue: {n['type']}"))
  ```

- **Sérialisation**: Le client doit supporter les formats JSON et MessagePack pour les échanges, conformément aux exigences du protocole.

## Workflows

Les workflows Github sont stockés dans `.github/workflows` et sont utilisés pour automatiser les tâches de développement et de déploiement. Les fichiers sont écrits en YAML et suivent un format standardisé pour garantir la cohérence et la lisibilité.

Les workflows à implémenter sont les suivants :
- `lint.yml` : Automatiser la vérification de la qualité du code et de la conformité aux standards. Il s'exécute automatiquement lorsqu'un commit est poussé sur la branche principale (cela inclut également la fusion d'une branche sur la branche principale). Il peut aussi se lancer manuellement, sur la branche de son choix.
- `test.yml` : Automatiser les tests unitaires et de fonctionnalité. Réalise l'ensemble des tests unitaires dans les environnements Windows, Linux et macOS. Il s'exécute automatiquement lorsqu'un commit est poussé sur la branche principale (cela inclut également la fusion d'une branche sur la branche principale). Il peut aussi se lancer manuellement, sur la branche de son choix.
- `release.yml` : Automatiser la création de versions et le déploiement sur les plateformes de distribution. Se lance automatiquement lorsque un tag sous la forme `vX.Y.Z` est créé. Il peut également s'exécuter manuellement, avec dans ce cas le choix de la version à déployer.
- `pypi.yml` : Automatiser le déploiement de la version sur PyPI. S'exécute uniquement manuellement, avec dans ce cas le choix de la version à déployer.

## Scripts

Les scripts sont stockés dans le répertoire `scripts`:

- `check_project.py`: réalise les actions suivantes:
  - Vérifie les modifications apportées au code depuis la branche principale. S'il n'y a pas de modification, ou si les seules modifications apportées l'ont été aux fichiers de documentation, le script s'arrête sans effectuer de vérification.
  - Vérifie la présence de `uv` et l'installe si nécessaire
  - Dans un environnement virtuel Python isolé:
    - Installe l'ensemble des dépendances nécessaires pour le développement
    - Exécute la vérification de la qualité du code et de la conformité aux standards
    - Exécute les tests unitaires et de fonctionnalité
  - Peut utiliser l'option `--fix` pour corriger automatiquement les erreurs de style et de confor