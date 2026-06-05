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
Cette classe représente un joueur dans le contexte du jeu. Elle s'instantie avec les paramètres suivants:

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
Cette classe représente un compte utilisateur. Celui-ci permet de conserver un profil de joueur et d'accéder à des informations ou des actions selon le niveau de droit dont il dispose, et auquel il a accès via une capacité d'authentification.
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
| `player`    | `Player`     | Le joueur associé au compte. L'objet `Player` est instantié avec le paramètre `name` égal à l'attribut `username`. Ses attributs peuvent ensuite être modifiés (dont `name`). | Non (mais mutable) | L'objet `Player` instantié est conservé pendant toute la durée de vie de l'instance de `User` qui le contient, et n'est supprimé qu'à la suppression de l'instance de `User`. |

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
Cette classe permet de sauvegarder, de mettre à jour et de restaurer les objets du module. Les objets sont d'abord enregistrés dans un tampon en mémoire, puis écrits dans le fichier uniquement lors de l'appel explicite à la méthode `flush`. Elle s'instantie avec les paramètres suivants:

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
  - Peut utiliser l'option `--fix` pour corriger automatiquement les erreurs de style et de conformité aux standards
  - Peut utiliser l'option `--force` pour forcer la vérification même si seule la documentation a été modifiée