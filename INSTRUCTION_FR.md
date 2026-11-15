# Instructions pour le développement de la version 3 de multiplayer

Ce document fournit les instructions pour le développement de la version 3 du module de multiplayer. Il décrit les conventions de codage, les dépendances et les spécifications techniques nécessaires pour assurer la compatibilité et la cohérence entre les différents modules du package.

La version du module est indépendante de la version du protocole d'échanges entre le client et le serveur. Le protocole est en version 2, révision 2.1 : la version majeure (`2`) est transmise dans le champ `version` de chaque message et garantit la compatibilité entre programmes, tandis que la révision (`2.1`) indique les fonctionnalités disponibles et est annoncée par le serveur (voir le paragraphe "Versionnement et extensibilité" du [Protocole d'échanges entre le client et le serveur](PROTOCOLE_FR.md)).

## Règles générales

### Conventions sur les commentaires et les docstrings

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

- Toutes les propriétés de type "ID" (identifiants) doivent être des chaînes de caractères alphanumériques et doivent être générées de manière unique à l'instanciation, en utilisant la fonction `uuid.uuid4()` du module uuid. Elles doivent être en lecture seule. Font exception à cette règle de génération les objets reconstruits à partir de la représentation d'un objet existant (restauration d'une sauvegarde, méthodes `from_dict`), qui conservent l'ID d'origine, ainsi que les copies qui représentent un même objet (par exemple l'attribut `option` de la classe `OptionEntry`) : deux objets portant le même ID désignent alors le même objet.
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

#### `UserRole` (Enum)
Une énumération pour le rôle d'un compte utilisateur.

*   `UserRole.PLAYER` : Un utilisateur standard qui peut rejoindre et participer à des parties.
*   `UserRole.GROUP_ADMIN` : Un utilisateur qui peut gérer les parties au sein des groupes qui lui sont assignés. Ce rôle inclut toutes les permissions d'un `PLAYER`.
*   `UserRole.SERVER_ADMIN` : Un utilisateur avec un accès administratif complet au serveur. Ce rôle englobe le rôle de `GROUP_ADMIN` (pour tous les groupes du serveur), lui-même pouvant également jouer le rôle de `PLAYER`.

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

#### `OptionType` (Enum)
Une énumération représentant les types d'options qui permettent de configurer des paramètres de personnalisation des joueurs. Ces options sont typiquement utilisées pour construire un formulaire de personnalisation par un processus client.

*   `OptionType.CHECK` : Une option de type booléen, qui peut typiquement être représentée par une case à cocher.
*   `OptionType.RANGE` : Une option de type numérique, dont la valeur est comprise dans un intervalle spécifié, qui peut être représentée par une barre de défilement ou un champ de saisie numérique.
*   `OptionType.LIST` : Une option de type liste, qui peut typiquement être représentée par une liste déroulante.
*   `OptionType.TEXT` : Une option de type texte, qui peut être représentée par un champ de saisie de texte.

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

#### Classe `UserNotFoundError`
Cette classe est dérivée de `MultiplayerError` et est utilisée pour signaler une tentative d'utilisation d'un compte utilisateur (ou de son ID) qui n'existe pas. Cette exception retourne dans son message l'ID erroné (si fourni).

#### Classe `PlayerNotFoundError`
Cette classe est dérivée de `MultiplayerError` et est utilisée pour signaler une tentative d'utilisation d'un joueur (ou d'un ID de joueur) qui n'existe pas. Cette exception retourne dans son message l'ID erroné (si fourni).

#### Classe `PlayerNotFoundInGameError`
Cette classe est dérivée de `PlayerNotFoundError` et est utilisée pour signaler une tentative de retirer un joueur **d'une partie où il n'est pas présent**. Cette exception retourne dans son message l'ID du joueur erroné (si fourni).

#### Classe `PasswordError`
Cette classe est dérivée de `MultiplayerError` et est utilisée pour signaler une tentative d'utilisation d'un mot de passe incorrect.

#### Classe `GameIsFullError`
Cette classe est dérivée de `MultiplayerError` et est utilisée pour signaler une tentative d'ajouter un joueur ou un observateur à une partie qui est déjà pleine.

#### Classe `GameAlreadyStartedError`
Cette classe est dérivée de `MultiplayerError` et est utilisée pour signaler une tentative de démarrage d'une partie qui est déjà en cours.

#### Classe `NotEnoughPlayersError`
Cette classe est dérivée de `MultiplayerError` et est utilisée pour signaler une tentative de démarrage d'une partie dont le nombre de joueurs est inférieur au minimum requis (paramètre `min_players` de la classe `Game`).

#### Classe `GameIsFinishedError`
Cette classe est dérivée de `MultiplayerError` et est utilisée pour signaler une tentative de modification d'une partie qui est terminée.

#### Classe `GameNotStartedError`
Cette classe est dérivée de `MultiplayerError` et est utilisée pour signaler une tentative de mise en pause, de redémarrage, d'arrêt ou d'évolution de jeu (passage au tour suivant par exemple) d'une partie qui n'est pas encore démarrée.

#### Classe `GameAlreadyPausedError`
Cette classe est dérivée de `MultiplayerError` et est utilisée pour signaler une tentative de mise en pause d'une partie qui est déjà en pause.

#### Classe `GameNotPausedError`
Cette classe est dérivée de `MultiplayerError` et est utilisée pour signaler une tentative de reprise d'une partie qui n'est pas en pause.

#### Classe `GameNotTurnBasedError`
Cette classe est dérivée de `MultiplayerError` et est utilisée pour signaler une tentative d'action spécifique au tour par tour d'une partie qui n'est pas gérée au tour par tour.

#### Classe `GameNotFoundError`
Cette classe est dérivée de `MultiplayerError` et est utilisée pour signaler une tentative de recherche d'une partie qui n'existe pas. Cette exception retourne dans son message l'ID de la partie erronée (si fourni).

#### Classe `GameNotFoundInGroupError`
Cette classe est dérivée de `GameNotFoundError` et est utilisée pour signaler une tentative de suppression d'une partie d'un groupe qui ne contient pas cette partie. Cette exception retourne dans son message l'ID de la partie erronée (si fourni).

#### Classe `GameHasPlayersError`
Cette classe est dérivée de `MultiplayerError` et est utilisée pour signaler une tentative d'opération sur une partie qui n'est possible que tant qu'aucun joueur ne l'a rejointe (par exemple la création ou le remplacement de la factory de joueurs). La présence d'observateurs n'est pas prise en compte. Cette exception retourne dans son message l'ID de la partie concernée.

#### Classe `PlayerFactoryNotDefinedError`
Cette classe est dérivée de `MultiplayerError` et est utilisée pour signaler une tentative d'utilisation de la factory de joueurs d'une partie qui n'en dispose pas (attribut `player_factory` à `None`), par exemple avec la méthode `create_and_join_player` de la classe `Game`. Cette exception retourne dans son message l'ID de la partie concernée.

#### Classe `UnsupportedFeatureError`
Cette classe est dérivée de `MultiplayerError` et est utilisée par la classe `GameClient` pour signaler une tentative d'utilisation d'une fonctionnalité du protocole que le serveur ne propose pas (par exemple la fonctionnalité `player_factory` auprès d'un serveur de révision 2.0). Elle est levée avant l'envoi de la requête correspondante. Cette exception retourne dans son message le nom de la fonctionnalité concernée et la révision annoncée par le serveur.

#### Classe `OptionError`
Cette classe est dérivée de `MultiplayerError` et sert de classe de base commune aux exceptions liées aux options de personnalisation des joueurs (`OptionValueAlreadyGivenError`, `LackingOptionError`, `InvalidOptionValueError` et `OptionAlreadyExistsError`). Elle n'est pas destinée à être levée directement, mais permet d'intercepter en une seule fois toutes les erreurs liées aux options (`except OptionError`), sans les confondre avec les autres erreurs du module.

#### Classe `OptionValueAlreadyGivenError`
Cette classe est dérivée de `OptionError` et est utilisée pour signaler une tentative d'introduction d'un objet contenant une option dont la valeur a déjà été utilisée, alors qu'elle est censée être unique dans le contexte. Cette exception retourne dans son message l'ID de l'option concernée et la valeur en cause.

Elle présente les attributs suivants, renseignés à sa création:

| Nom | Type | Description |
|-----|------|-------------|
| `option_id` | str | L'ID de l'option concernée. |
| `value` | any | La valeur déjà utilisée. |

#### Classe `LackingOptionError`
Cette classe est dérivée de `OptionError` et est utilisée pour signaler qu'aucune valeur n'est disponible pour une option obligatoire dans le contexte : soit l'objet introduit ne porte pas de valeur pour cette option, soit aucune valeur n'a été fournie pour cette option et il n'existe plus de valeur possible. Cette exception retourne dans son message l'ID de l'option manquante et la raison de l'erreur.

Elle présente les attributs suivants, renseignés à sa création:

| Nom | Type | Description |
|-----|------|-------------|
| `option_id` | str | L'ID de l'option concernée. |
| `reason` | str | La raison de l'erreur : `"ABSENT_FROM_PLAYER"` si l'objet `Player` introduit dans une partie ne porte pas de valeur pour cette option (ou porte la valeur `None`, considérée comme une absence de valeur), ou `"NO_AVAILABLE_VALUE"` si aucune valeur n'a été fournie pour cette option lors de la création d'un joueur et qu'il n'existe plus de valeur possible (valeur proposée à `None`). |

#### Classe `InvalidOptionValueError`
Cette classe est dérivée à la fois de `OptionError` et de `ValueError`, et est utilisée pour signaler une valeur d'option incorrecte, lors de la création d'un joueur par une factory ou lors de l'introduction d'un joueur dans une partie dotée d'une factory. Le fait de dériver de `ValueError` permet au code qui intercepte cette exception standard de continuer à fonctionner. Cette exception retourne dans son message l'ID de l'option concernée, la valeur en cause et la raison de l'erreur.

Elle présente les attributs suivants, renseignés à sa création:

| Nom | Type | Description |
|-----|------|-------------|
| `option_id` | str | L'ID de l'option concernée (ou la clé fournie, si elle ne correspond à aucune option). |
| `value` | any | La valeur en cause. |
| `reason` | str | La raison de l'erreur : `"UNKNOWN_OPTION"` (la clé fournie ne correspond à aucune option), `"INCOMPATIBLE_TYPE"` (la valeur n'est pas acceptée pour le type de l'option, selon les règles de conversion de la classe `Option`) ou `"INVALID_VALUE"` (la valeur est en dehors des bornes `min_value` / `max_value`, ne correspond pas à un incrément `step`, ou est absente de `choices`). |

#### Classe `OptionAlreadyExistsError`
Cette classe est dérivée de `OptionError` et est utilisée pour signaler une tentative d'introduction d'une option qui est déjà présente. Cette exception retourne dans son message l'ID de l'option déjà présente. Cette exception est également levée lorsqu'une option similaire est déjà présente. La similitude est définie soit par l'égalité des ID des options, soit par l'égalité entre le nom de l'option introduite et la clé figée d'une option déjà présente (voir la méthode `add_option` de la classe `PlayerFactoryTemplate`).

### Contenu du fichier src/multiplayer/game.py

Ce fichier contient la logique principale de gestion des parties. Il définit les classes et les fonctions nécessaires pour la création, la gestion et la résolution des parties.
On y trouve en particulier les classes suivantes:

#### Classe `Option`
Cette classe représente une option dans le contexte du jeu. Une option est un paramètre de personnalisation dont la valeur est choisie lors de la création d'un joueur, au moyen d'une factory de joueurs. Elle peut être de différents types, tels que booléen, numérique, texte, etc. Chaque option est définie par un type et des paramètres spécifiques.

Elle s'instancie avec les paramètres suivants:

| Nom     | Type     | Description          | Obligatoire | Valeur par défaut |
|---------|----------|----------------------|-------------|-------------------|
| `name`  | str   | Le nom de l'option. Il s'agit d'une chaîne de caractères qui identifie l'option. | Oui | - |
| `option_type`  | OptionType    | Le type de l'option.  | Oui | - |
| `description` | str | Une description de l'option. Il s'agit d'une chaîne de caractères qui décrit l'option. | Non | "" (chaîne vide)|
| `default` | bool\|int\|float\|str\|`None` | La valeur par défaut de l'option. `None` signifie "première valeur disponible" (voir le paragraphe "Valeur par défaut `None`" ci-dessous). | Non | `None` |
| `min_value`   | float\|int\|`None`  | La valeur minimale de l'option. Uniquement utile pour les options de type `OptionType.RANGE`. Ignoré sinon. `None` signifie qu'il n'y a pas de minimum.| Non | `None` |
| `max_value`   | float\|int\|`None`  | La valeur maximale de l'option. Uniquement utile pour les options de type `OptionType.RANGE`. Ignoré sinon. `None` signifie qu'il n'y a pas de maximum. | Non | `None` |
| `step`  | float\|int  | Le pas de l'option. Définit l'incrément entre les valeurs possibles pour l'option de type `OptionType.RANGE` (voir le paragraphe "Valeurs possibles d'une option `OptionType.RANGE`" ci-dessous). | Non | 1 |
| `choices` | list[str]\|tuple[str, ...] | Les valeurs possibles de l'option. Uniquement utile pour l'option de type `OptionType.LIST`. Ignoré sinon. | Non | [] (liste vide) |

Les noms des paramètres `option_type`, `min_value` et `max_value` évitent de masquer les fonctions intégrées de Python `type`, `min` et `max`. Les représentations sous forme de dictionnaire (méthode `to_dict`), utilisées par la sauvegarde et par le protocole réseau, conservent en revanche les clés `type`, `min` et `max`.

À la création de l'option, les contrôles suivants sont effectués. En cas d'échec, l'exception indiquée est levée et l'option n'est pas créée:

| Cas | Exception |
|-----|-----------|
| `option_type` n'est pas un membre de l'énumération `OptionType` | `TypeError` |
| `min_value` et `max_value` sont tous deux définis, et `min_value` est supérieur à `max_value` | `ValueError` |
| `step` est inférieur ou égal à 0 | `ValueError` |
| `choices` contient un élément qui n'est pas une chaîne de caractères | `TypeError` |
| `choices` contient un doublon | `ValueError` |
| L'option est de type `OptionType.LIST` et `choices` est vide | `ValueError` |
| `default` (s'il ne contient pas de constante d'exécution et ne vaut pas `None`) n'est pas accepté pour le type de l'option, selon les règles de conversion ci-dessous | `TypeError` |
| `default` (s'il ne contient pas de constante d'exécution et ne vaut pas `None`) n'est pas une valeur possible de l'option : en dehors des bornes `min_value` / `max_value`, ne correspondant pas à un incrément `step`, ou absente de `choices` | `ValueError` |

Si `default` contient des constantes d'exécution (voir le paragraphe "Constantes d'exécution" ci-dessous), les contrôles suivants s'appliquent à la place du contrôle de la valeur par défaut, qui n'est possible qu'après évaluation:
- si une constante n'est pas reconnue, une exception `ValueError` est levée ;
- si une constante est utilisée dans un type d'option qui ne l'autorise pas, ou d'une manière non autorisée pour ce type d'option, une exception `TypeError` est levée ;
- si `%%RANDOM_NUMBER%%` est utilisée dans une option `OptionType.RANGE` dont `min_value` ou `max_value` vaut `None`, une exception `ValueError` est levée.

Elle présente les attributs suivants:

| Nom     | Type     | Description          | Modifiable     | Précision d'implémentation     |
|---------|----------|----------------------|----------------|--------------------------------|
| `ID`    | str      | L'identifiant unique de l'option     | Non            | S'initialise automatiquement avec la valeur de `uuid.uuid4()`.                              |
| `name`  | str      | Nom de l'option     | Oui            | S'initialise automatiquement avec le nom fourni à la création de l'option                              |
| `description` | str      | Description de l'option     | Oui            | S'initialise automatiquement avec la description fournie à la création de l'option                              |
| `option_type`  | OptionType    | Le type de l'option. | Non     | Prend la valeur du type fourni à la création de l'option                              |
| `choices` | tuple[str, ...]      | Les choix possibles pour l'option     | Non            | Prend la valeur des choix fournis à la création de l'option, copiés dans un tuple : l'attribut ne peut donc pas être modifié, et une modification ultérieure de la liste fournie à la création est sans effet sur l'option.                              |
| `min_value` | float\|int\|`None`      | La valeur minimale pour l'option     | Non            | Prend la valeur minimale fournie à la création de l'option, convertie selon le caractère entier ou décimal de l'option.                              |
| `max_value` | float\|int\|`None`      | La valeur maximale pour l'option     | Non            | Prend la valeur maximale fournie à la création de l'option, convertie selon le caractère entier ou décimal de l'option.                              |
| `step` | float\|int      | La valeur de l'incrément pour l'option     | Non            | Prend la valeur de l'incrément fournie à la création de l'option                              |
| `default` | bool\|int\|float\|str\|`None`      | La valeur par défaut pour l'option     | Non            | Prend la valeur par défaut fournie à la création de l'option, convertie selon les règles de conversion, sans évaluation des éventuelles constantes d'exécution qu'elle contient.                              |

La classe `Option` présente les méthodes suivantes:

- `evaluate_default`: fournit la valeur par défaut de l'option, après évaluation des éventuelles constantes d'exécution qu'elle contient.
  - Paramètres:
    - `context` (dict[str, str]\|`None`): le contexte fournissant la valeur des constantes (voir le paragraphe "Constantes d'exécution"). Optionnel. Valeur par défaut: `None` (équivalent à un dictionnaire vide).
    - `exclusions` (list\|`None`): liste de valeurs à ne pas retenir lors d'un tirage aléatoire (`%%RANDOM_NUMBER%%` pour une option `OptionType.RANGE`, `%%RANDOM_CHOICE%%` pour une option `OptionType.LIST`) : le tirage s'effectue uniquement parmi les valeurs possibles qui ne figurent pas dans cette liste. Sans effet sur les autres constantes. Optionnel. Valeur par défaut: `None` (aucune exclusion).
  - Précision d'implémentation: si `default` vaut `None`, la méthode retourne la première valeur disponible, selon le paragraphe "Valeur par défaut `None`" (sans tenir compte du paramètre `exclusions`, la règle de la valeur suivante étant appliquée par la factory). Si `default` ne contient aucune constante d'exécution, la méthode retourne `default` tel quel. Le contexte fourni n'est pas modifié par la méthode.
  - Valeur de retour: la valeur par défaut évaluée. Pour un tirage aléatoire, `None` si toutes les valeurs possibles figurent dans `exclusions`.

- `to_dict`: fournit une représentation de l'option sous forme de dictionnaire, composé uniquement de types simples (chaînes de caractères, nombres, booléens, `None`, listes). Cette représentation est commune à la sauvegarde (voir le fichier `save.py`) et aux échanges réseau (voir le [Protocole d'échanges entre le client et le serveur](PROTOCOLE_FR.md), paragraphe "Représentation d'une option").
  - Paramètres: Aucun.
  - Valeur de retour: un objet `dict` présentant les éléments suivants:

    | Clé | Valeur |
    |-----|--------|
    | `option_id` | L'ID de l'option. |
    | `type` | Le nom du membre de l'énumération `OptionType` de l'attribut `option_type` (ex: `"RANGE"`). |
    | `name` | Le nom actuel de l'option. |
    | `description` | La description de l'option. |
    | `default` | La valeur brute de l'attribut `default`, sans évaluation des éventuelles constantes d'exécution. |
    | `min` | La valeur de l'attribut `min_value`. |
    | `max` | La valeur de l'attribut `max_value`. |
    | `step` | La valeur de l'attribut `step`. |
    | `choices` | Les choix possibles (attribut `choices`), sous forme de liste. |

- `from_dict` (méthode de classe): crée une option à partir d'une représentation sous forme de dictionnaire, au format retourné par la méthode `to_dict`. Cette méthode est utilisée pour la restauration d'une sauvegarde et pour la création d'options à partir des données reçues par le serveur.
  - Paramètres:
    - `data` (dict): la représentation de l'option. Les clés `name` et `type` sont obligatoires. Les autres clés sont optionnelles et prennent, si elles sont absentes, les valeurs par défaut des paramètres correspondants du constructeur (`description`, `default`, `min` pour `min_value`, `max` pour `max_value`, `step`, `choices`). Obligatoire.
  - Précision d'implémentation: si la clé `option_id` est présente, l'option créée conserve cet ID ; sinon, un nouvel ID est généré avec `uuid.uuid4()`. Tous les contrôles effectués à la création d'une option s'appliquent. Les clés inconnues sont ignorées. Le dictionnaire fourni n'est pas modifié.
  - Exceptions émises:
    - `TypeError` ou `ValueError`: dans les mêmes cas que lors de la création d'une option, ainsi que si une clé obligatoire est absente (`ValueError`) ou si la valeur de `type` n'est pas le nom d'un membre de l'énumération `OptionType` (`ValueError`).
  - Valeur de retour: l'objet `Option` créé.

##### Règles de conversion des valeurs

Les règles suivantes s'appliquent de manière identique à la valeur par défaut (à la création de l'option), aux valeurs fournies lors de la création d'un joueur (méthode `create_player` de la classe `PlayerFactory`) et aux valeurs contrôlées lors de l'introduction d'un joueur dans une partie (méthode `join_game_as_player` de la classe `Game`):

| Type d'option | Valeurs acceptées | Conversion |
|---------------|-------------------|------------|
| `OptionType.CHECK` | `bool` uniquement. | Aucune. |
| `OptionType.RANGE` | `int`, `float`, ou chaîne de caractères représentant un nombre (ex: `"3.0"`). Les valeurs `bool` sont refusées, bien que `bool` soit une sous-classe de `int` en Python. | Vers `int` si l'option est entière (`"3.0"` donne `3`, mais `"3.5"` ou `3.5` sont refusés), vers `float` si l'option est décimale (voir le paragraphe suivant). |
| `OptionType.LIST` | Chaîne de caractères uniquement. | Aucune. |
| `OptionType.TEXT` | Chaîne de caractères uniquement. | Aucune. |

Une valeur qui n'est pas acceptée est de type incompatible : selon le contexte, elle provoque l'exception `TypeError` (à la création de l'option) ou l'exception `InvalidOptionValueError` avec `reason` à `"INCOMPATIBLE_TYPE"` (lors de la création ou de l'introduction d'un joueur). C'est toujours la valeur convertie qui est retenue : elle est stockée dans l'objet `Player`, et c'est elle qui est comparée pour le contrôle d'unicité.

##### Valeurs possibles d'une option `OptionType.RANGE`

Les valeurs possibles d'une option `OptionType.RANGE` sont les valeurs de la forme `référence + k × step` (où `k` est un entier relatif) comprises entre `min_value` et `max_value` (lorsqu'ils sont définis). La référence est `min_value` s'il est défini, et `0` sinon.

Une option `OptionType.RANGE` est **entière** si `step`, ainsi que `min_value`, `max_value` et `default` lorsqu'ils sont définis (et que `default` ne contient pas de constante d'exécution), sont tous de type `int` : ses valeurs sont alors de type `int`. Dans le cas contraire, l'option est **décimale** : ses valeurs sont de type `float`, et l'appartenance d'une valeur à la grille définie par `step`, comme l'égalité de deux valeurs, est évaluée avec une tolérance (fonction `math.isclose`), afin de s'affranchir des erreurs d'arrondi des nombres à virgule flottante.

##### Valeur par défaut `None`

Une valeur par défaut à `None` signifie "première valeur disponible". Lors du calcul de la valeur proposée (voir la méthode `get_option` de la classe `PlayerFactory`), elle est remplacée par:

| Type d'option | Valeur retenue |
|---------------|----------------|
| `OptionType.CHECK` | `False` |
| `OptionType.RANGE` | `min_value` s'il est défini, sinon la valeur possible la plus proche de `0` (en privilégiant la valeur positive en cas d'égalité) |
| `OptionType.LIST` | Le premier élément de `choices` |
| `OptionType.TEXT` | `""` (chaîne vide) |

Si cette valeur est exclue, la règle de la valeur suivante s'applique (voir la méthode `get_option` de la classe `PlayerFactory`).

##### Constantes d'exécution

Il est possible d'utiliser des constantes d'exécution, dont la valeur est calculée à l'exécution du programme, pour définir la valeur par défaut d'une option (paramètre `default`).

Ces constantes sont reconnues car leur nom, composé de lettres majuscules et du caractère `_`, est entouré de deux doubles caractères "pourcentage" (`%%CONSTANTE%%`, c'est-à-dire le motif `%%[A-Z_]+%%`). Le reste de la chaîne de caractères n'est pas interprété : un caractère `%` isolé, ou une séquence ne correspondant pas à ce motif, est conservé tel quel.

Les constantes d'exécution reconnues sont les suivantes:

| Nom        | Type produit | Source | Description  |
|------------|--------------|--------|--------------|
| `%%CURRENT_TIME%%` | str | Bibliothèque | La date et l'heure locales au moment de l'évaluation, au format ISO 8601, à la seconde près, avec le décalage horaire (ex: `"2026-11-15T12:34:56+01:00"`). |
| `%%RANDOM_NUMBER%%` | int | Bibliothèque | Pour une option `OptionType.TEXT` : un nombre entier tiré au hasard entre 0 et 100 inclus. Pour une option `OptionType.RANGE` : une valeur tirée au hasard parmi les valeurs possibles de l'option (voir ci-dessous). |
| `%%RANDOM_CHOICE%%` | str | Bibliothèque | Pour une option `OptionType.LIST` uniquement : une valeur tirée au hasard parmi les choix possibles de l'option (voir ci-dessous). |
| `%%GAMENAME%%` | str | Factory | Le nom de la partie à laquelle la factory est associée (attribut `name` de l'objet `Game`). Si la partie n'a pas de nom (attribut `name` à `None`), la constante est remplacée par une chaîne vide (`""`). |
| `%%USERNAME%%` | str | Contexte | Le nom de l'utilisateur pour lequel le joueur est créé (attribut `username` de l'objet `User`). |
| `%%SERVERNAME%%` | str | Contexte | Le nom du serveur (attribut `name` de l'objet `GameServer`). |
| `%%CLIENTADDRESS%%` | str | Contexte | L'adresse IP (IPv4 ou IPv6) du client. |
| `%%SERVERADDRESS%%` | str | Contexte | L'adresse IP (IPv4 ou IPv6) du serveur. |

La colonne "Source" indique qui fournit la valeur de la constante:
- Bibliothèque : la valeur est calculée par la bibliothèque `multiplayer` elle-même, au moment de l'évaluation.
- Factory : la valeur est fournie par l'objet `PlayerFactory` qui procède à l'évaluation, à partir de la partie à laquelle il est associé.
- Contexte : la valeur est fournie par l'appelant, au travers d'un dictionnaire de contexte (voir ci-dessous). Côté serveur, c'est l'objet `GameServer` qui construit ce contexte à partir de la session et de la connexion de l'utilisateur concerné.

Le **contexte** est un dictionnaire de type `dict[str, str]`, dont les clés sont les noms des constantes sans les caractères `%%` (par exemple `{"USERNAME": "alice", "CLIENTADDRESS": "192.168.1.12"}`), et les valeurs sont les valeurs à leur substituer. Une constante présente dans le contexte prend toujours la valeur du contexte, y compris s'il s'agit d'une constante normalement fournie par la bibliothèque ou par la factory : cela permet notamment d'obtenir des résultats reproductibles lors des tests unitaires (par exemple en fixant `CURRENT_TIME` ou `RANDOM_NUMBER`). Une constante de source "Contexte" absente du contexte est remplacée par une chaîne vide (`""`).

Les règles d'utilisation des constantes dépendent du type de l'option:

| Type d'option | Utilisation autorisée dans `default` |
|---------------|--------------------------------------|
| `OptionType.TEXT` | Remplacement libre au sein de la chaîne de caractères : une ou plusieurs constantes peuvent être combinées avec du texte (ex: `"Joueur_%%RANDOM_NUMBER%%"`). Le résultat de l'évaluation est une chaîne de caractères. `%%RANDOM_CHOICE%%` n'est pas autorisée. |
| `OptionType.RANGE` | Uniquement la chaîne exacte `"%%RANDOM_NUMBER%%"`, sans autre texte. Les paramètres `min_value` et `max_value` doivent alors être tous deux définis (différents de `None`). La valeur est tirée au hasard parmi les valeurs possibles de l'option, c'est-à-dire comprises entre `min_value` et `max_value` et correspondant à un incrément `step`. |
| `OptionType.LIST` | Uniquement la chaîne exacte `"%%RANDOM_CHOICE%%"`, sans autre texte. La valeur est tirée au hasard parmi les éléments de `choices`. |
| `OptionType.CHECK` | Aucune constante autorisée. |

Les constantes ne sont pas autorisées dans les autres paramètres de l'option (`min_value`, `max_value`, `step`, `choices`, `name`, `description`).

Les constantes sont conservées sans évaluation dans l'objet `Option` (l'attribut `default` retourne toujours la valeur brute, par exemple `"Joueur_%%RANDOM_NUMBER%%"`), ainsi que lors de la copie des options dans un modèle ou dans une factory. Elles ne sont évaluées qu'au moment du calcul de la valeur proposée d'une option, par la méthode `evaluate_default`, appelée par les méthodes `get_option` et `create_player` de la classe `PlayerFactory`. Chaque évaluation est indépendante : deux évaluations successives peuvent donner des résultats différents (date et heure, tirages aléatoires). Il est donc recommandé au processus client de transmettre explicitement à la méthode `create_player` la valeur proposée qu'il a présentée à l'utilisateur, plutôt que de laisser la factory procéder à une nouvelle évaluation.

#### Classe `OptionEntry`
Cette classe décrit une option telle qu'elle est enregistrée dans un modèle (`PlayerFactoryTemplate`) ou dans une factory (`PlayerFactory`) : l'option elle-même, accompagnée des paramètres qui lui ont été associés lors de son ajout au modèle. Ces paramètres n'appartiennent pas à l'objet `Option`, une même option pouvant être ajoutée à plusieurs modèles avec des paramètres différents.

Les objets `OptionEntry` sont créés par les classes `PlayerFactoryTemplate` et `PlayerFactory`, et retournés par leurs méthodes `get_option`. Ils ne sont pas destinés à être instanciés directement par l'usager de la bibliothèque `multiplayer`.

Un objet `OptionEntry` est immuable : aucun de ses attributs n'est modifiable, et il ne donne pas accès aux objets internes du modèle ou de la factory.

Elle présente les attributs suivants:

| Nom | Type | Description | Modifiable | Précision d'implémentation |
|-----|------|-------------|------------|----------------------------|
| `option` | `Option` | L'option concernée. | Non | Il s'agit d'une copie de l'objet `Option` détenu par le modèle ou la factory : sa modification est sans effet sur le modèle ou la factory. Cette copie représente la même option, et non une option nouvelle : elle conserve donc l'ID de l'option d'origine (voir la convention sur les ID). Elle se distingue en cela des copies effectuées lors de la création d'une factory, qui constituent de nouvelles options et reçoivent un nouvel ID. |
| `unicity` | bool | La valeur du paramètre `unicity` associé à l'option. | Non | - |
| `player_attribute` | str\|`ParameterFamily` | La valeur du paramètre `player_attribute` associé à l'option. | Non | - |
| `key` | str | La clé figée de l'option. | Non | - |

La classe `OptionEntry` présente les méthodes suivantes:

- `to_dict`: fournit une représentation de l'option enregistrée sous forme de dictionnaire, commune à la sauvegarde et aux échanges réseau.
  - Paramètres: Aucun.
  - Valeur de retour: un objet `dict` composé des éléments retournés par la méthode `to_dict` de l'attribut `option`, complétés des éléments suivants:

    | Clé | Valeur |
    |-----|--------|
    | `unicity` | La valeur de l'attribut `unicity`. |
    | `target` | `"ATTRIBUTE"` si `player_attribute` est une chaîne de caractères, `"STATIC"` s'il vaut `ParameterFamily.STATIC`, `"DYNAMIC"` s'il vaut `ParameterFamily.DYNAMIC`. |
    | `attribute` | La valeur de `player_attribute` lorsque `target` vaut `"ATTRIBUTE"` (ex: `"name"`), `None` sinon. |
    | `key` | La clé figée de l'option. |

- `from_dict` (méthode de classe): crée un objet `OptionEntry` à partir d'une représentation sous forme de dictionnaire, au format retourné par la méthode `to_dict`. Cette méthode est principalement utilisée par les méthodes `from_dict` des classes `PlayerFactoryTemplate` et `PlayerFactory`.
  - Paramètres:
    - `data` (dict): la représentation de l'option enregistrée. Les éléments de l'option elle-même sont traités par la méthode `from_dict` de la classe `Option`. La clé `target` est obligatoire, ainsi que la clé `attribute` lorsque `target` vaut `"ATTRIBUTE"`. La clé `unicity` est optionnelle (`False` si absente). La clé `key` est optionnelle : si elle est absente, la clé figée est le nom de l'option. Obligatoire.
  - Précision d'implémentation: le paramètre `player_attribute` est reconstruit à partir de `target` et `attribute` (`"STATIC"` donne `ParameterFamily.STATIC`, `"DYNAMIC"` donne `ParameterFamily.DYNAMIC`, `"ATTRIBUTE"` donne la valeur de `attribute`). Les contrôles appliqués par la méthode `add_option` de la classe `PlayerFactoryTemplate` à `player_attribute` s'appliquent. Le dictionnaire fourni n'est pas modifié.
  - Exceptions émises:
    - `TypeError` ou `ValueError`: dans les mêmes cas que la méthode `from_dict` de la classe `Option` et que les contrôles de `player_attribute` de la méthode `add_option`, ainsi que si `target` est absent ou ne vaut pas `"ATTRIBUTE"`, `"STATIC"` ou `"DYNAMIC"` (`ValueError`).
  - Valeur de retour: l'objet `OptionEntry` créé.

#### Classe `Player`
Cette classe représente un joueur dans le contexte du jeu. C'est l'entité qui participe effectivement aux parties. Alors qu'un compte `User` gère l'accès et les permissions, l'objet `Player` porte les attributs liés au jeu (nom, score, état, etc.). Typiquement, un objet `Player` est créé juste avant une partie, et est détruit après la fin de celle-ci. Ce comportement reste cependant un choix d'implémentation, la bibliothèque `multiplayer` ne gérant pas la création ni la destruction des objets `Player` à l'instanciation et la fin d'un objet `Game` (la destruction peut néanmoins être gérée dans le cadre de la fonction de nettoyage automatique de la classe `GameServer`, voir le paragraphe associé).

Elle s'instancie avec les paramètres suivants:

| Nom        | Type     | Description  | Obligatoire | Valeur par défaut |
|------------|----------|--------------|-------------|-------------------|
| `name`     | str      | Le nom du joueur.  | Non   | "Player"                 |
| `**kwargs` | variable | Paramètres optionnels pour personnaliser le joueur. Chaque paramètre doit se présenter sous la forme d'un tuple `(famille, valeur_initiale)` dont `famille` est un objet `ParameterFamily` qui spécifie le caractère statique ou dynamique du paramètre, et `valeur_initiale` sa valeur initiale. Le choix de la famille se fait à la convenance de l'utilisateur, pour l'aider à classer les informations, mais n'a aucun impact sur le traitement interne (les familles sont toutes traitées de la même manière). | Non         | -                 |

Elle présente les attributs suivants:

| Nom             | Type | Description | Modifiable | Précision d'implémentation |
|-----------------|------|-------------|------------|----------------------------|
| `ID`            | str  | L'identifiant unique du joueur.  | Non        | S'initialise automatiquement avec la valeur de `uuid.uuid4()`.  |
| `name`          | str  | Le nom du joueur. | Oui        | S'initialise automatiquement avec le nom fourni lors de la création du joueur.|
| `static_state`  | dict | Attributs personnalisés du joueur, dont la vocation est de stocker des informations qui ne changent pas ou peu pendant la partie.  | Oui  | S'initialise automatiquement avec les paramètres spécifiés comme appartenant à la famille `ParameterFamily.STATIC`, mais peut être complété par la suite par tout autre paramètre au choix de l'utilisateur. Par exemple, si `Player` est instancié avec `Player(name="Mon nom", color=(ParameterFamily.STATIC, "white"), score=(ParameterFamily.DYNAMIC, 0))`, alors `static_state` est égal à `{"color":"white"}`. |
| `dynamic_state` | dict | Attributs personnalisés du joueur, dont la vocation est de stocker des informations qui peuvent être modifiées souvent pendant la partie. | Oui        | S'initialise automatiquement avec les paramètres spécifiés comme appartenant à la famille `ParameterFamily.DYNAMIC`, mais peut être complété par la suite par tout autre paramètre au choix de l'utilisateur. Par exemple, si `Player` est instancié avec `Player(name="Mon nom", color=(ParameterFamily.STATIC, "white"), score=(ParameterFamily.DYNAMIC, 0))`, alors `dynamic_state` est égal à `{"score":0}`.    |

Chaque objet `Player` créé (ou restauré depuis une sauvegarde) est enregistré dans un registre global, indexé par son ID. C'est ce registre qui permet de désigner un joueur par son seul ID, par exemple dans les méthodes `join_game_as_player` et `join_game_as_observer` de la classe `Game`.

La classe `Player` présente les méthodes suivantes:

- `get_by_id` (méthode de classe): permet de retrouver un joueur existant à partir de son ID.
  - Précision d'implémentation: Le registre ne conserve que des références faibles (`weakref.WeakValueDictionary`) : il n'empêche pas la destruction d'un objet `Player` qui n'est plus utilisé par ailleurs.
  - Paramètres:
    - `player_id` (str): l'ID du joueur recherché. Obligatoire.
  - Valeur de retour: L'objet `Player` correspondant, ou `None` si aucun joueur existant ne porte cet ID.

#### Classe `PlayerFactoryTemplate`
Lors de la création d'une partie, il est possible de définir la manière dont les joueurs seront créés, les paramètres qu'ils devront traiter, ainsi que les valeurs qu'il sera possible de leur affecter avant le démarrage de la partie. Par exemple, pour un jeu d'échecs, le joueur qui souhaite rejoindre la partie doit pouvoir décider s'il jouera les blancs ou les noirs.
Il est également possible de faire évoluer et restreindre les valeurs possibles au fur et à mesure que les joueurs rejoignent la partie. Par exemple, toujours dans le cadre d'un jeu d'échecs, si un joueur a choisi de jouer les blancs, alors le second joueur ne pourra jouer que les noirs.
Pour cela, il conviendra de créer un objet `PlayerFactoryTemplate`, et de lui affecter des objets `Option` qui définiront les paramètres, les valeurs possibles, ainsi que les valeurs par défaut. Cet objet `PlayerFactoryTemplate` pourra ensuite être utilisé par un objet `Game` pour créer en son sein (c'est-à-dire dans l'espace de nom de l'objet `Game`) un objet `PlayerFactory`, qui sera, lui, utilisé pour accompagner la création des objets `Player` à affecter à la partie en tant que joueurs. Une factory est propre à une partie : elle détermine les valeurs encore disponibles à partir de la liste des joueurs de cette partie (notamment pour gérer les choix "uniques", tels que la couleur - blanc ou noir - affectée pour une partie d'échecs). C'est pourquoi elle est créée au sein de l'objet `Game`. Le modèle, lui, est indépendant de toute partie et se situe dans l'espace de nom global : il peut servir à créer les factories de plusieurs parties.

La classe `PlayerFactoryTemplate` s'instancie avec les paramètres suivants:

| Nom        | Type | Description      | Obligatoire | Valeur par défaut |
|------------|------|------------------|-------------|-------------------|
| `name`     | str  | Nom du modèle | Oui           | -                 |

Ce paramètre `name` permet à un utilisateur d'identifier le modèle, par exemple dans la liste des modèles détenus par un serveur (voir le registre des modèles de factory de la classe `GameServer`, et la requête `FACTORY_TEMPLATE_LIST` du [Protocole d'échanges entre le client et le serveur](PROTOCOLE_FR.md)). En usage local, la bibliothèque `multiplayer` ne tient aucun registre des modèles : il appartient à l'usager de conserver les modèles qu'il crée. Même si ce n'est pas obligatoire, il est **fortement** recommandé de fournir un nom unique pour chaque modèle.

Elle présente les attributs suivants:

| Nom        | Type | Description                     | Modifiable | Précision d'implémentation |
|------------|------|---------------------------------|------------|----------------------------|
| `ID`       | str  | Identifiant unique du modèle| Non          | S'initialise automatiquement avec la valeur de `uuid.uuid4()`.                          |
| `name`     | str  | Nom du modèle               | Oui          | S'initialise automatiquement avec le nom fourni lors de la création du modèle.|
| `options`    | list[tuple[str,str]] | Liste des ID et noms des options du modèle, sous forme de tuples (ID, nom)  | Non          | Une nouvelle liste est créée à chaque demande de lecture de cet attribut, dont une éventuelle modification n'a aucun impact sur les options contenues dans le modèle.                              |


La classe `PlayerFactoryTemplate` présente les méthodes suivantes:

- `add_option`: permet d'ajouter une option au modèle.
  - Description: ajoute une option au modèle. Le modèle enregistre une copie de l'objet `Option` fourni, et non l'objet lui-même : une modification ultérieure de l'objet fourni (par exemple de son attribut `name` ou `description`) est sans effet sur le modèle. Cette copie représente la même option et conserve donc son ID (voir la convention sur les ID). Vérifie qu'une option similaire n'est pas déjà présente dans le modèle. La similitude est définie soit par l'égalité des ID des options, soit par l'égalité entre le nom actuel de l'option à ajouter (qui deviendra sa clé figée) et la clé figée d'une option déjà présente dans le modèle. Pour les options déjà présentes, c'est leur clé figée qui est prise en compte, et non leur nom (les deux ne pouvant différer que pour une option reconstruite par une méthode `from_dict`). En cas de similitude, une exception `OptionAlreadyExistsError` est levée.
  - Paramètres (dans cet ordre):
    - `option` (`Option`): l'objet `Option` à ajouter au modèle. Obligatoire.
    - `player_attribute` (str|`ParameterFamily`): l'attribut de l'objet `Player` associé à cette option. Obligatoire. Selon le choix de ce paramètre, l'option sera intégrée à l'objet `Player` généré soit dans les attributs `static_state` (`ParameterFamily.STATIC`), soit dans les attributs `dynamic_state` (`ParameterFamily.DYNAMIC`), soit associée à l'attribut dont le nom correspond à la chaîne de caractères spécifiée (un seul cas possible pour l'instant: `"name"`). L'attribut `name` de l'objet `Player` étant une chaîne de caractères, seules les options de type `OptionType.TEXT` et `OptionType.LIST` peuvent lui être associées.
    - `unicity` (bool): Si `True`, alors une valeur de cette option portée par un joueur de la partie ne peut pas être portée par un autre joueur de cette même partie. La valeur redevient disponible dès que le joueur qui la porte est retiré de la partie. Pour une option associée à `ParameterFamily.DYNAMIC`, c'est la valeur courante portée par le joueur qui est prise en compte : si elle évolue en cours de partie, les valeurs exclues évoluent en conséquence. L'unicité n'est garantie qu'au moment où le joueur rejoint la partie (méthode `join_game_as_player` de la classe `Game`) : une modification ultérieure de la valeur portée par un joueur (attribut `name`, `static_state` ou `dynamic_state`) n'est pas contrôlée, et peut donc aboutir à ce que deux joueurs portent la même valeur. Il est de la responsabilité de l'usager de la bibliothèque `multiplayer` de préserver l'unicité après l'introduction des joueurs, si elle est nécessaire au jeu. Pour une option unique associée à l'attribut `name`, le nom par défaut d'un objet `Player` (`"Player"`) est une valeur comme une autre : un joueur portant ce nom l'interdit aux joueurs suivants. Il est donc recommandé de donner à une telle option une valeur par défaut variable, par exemple `"%%USERNAME%%"` ou `"Joueur_%%RANDOM_NUMBER%%"`. Optionnel. `False` par défaut.
  - Exceptions émises:
    - `TypeError` si l'objet fourni n'est pas une instance de `Option`.
    - `TypeError` si `player_attribute` n'est ni une chaîne de caractères, ni un membre de l'énumération `ParameterFamily`.
    - `ValueError` si `player_attribute` est une chaîne de caractères autre que `"name"`.
    - `TypeError` si `player_attribute` vaut `"name"` et que l'option n'est pas de type `OptionType.TEXT` ou `OptionType.LIST`.
    - `OptionAlreadyExistsError` si une option similaire est déjà présente dans le modèle.
  - Valeur de retour: Aucune.

> Précision d'implémentation:
> - Le remplacement silencieux ne concerne que l'attribut `name` de l'objet `Player` : si `player_attribute` vaut `"name"` et qu'une autre option du modèle est déjà associée à `name`, alors l'ancienne option est remplacée par la nouvelle option silencieusement. L'ancienne option est alors retirée du modèle (de la même manière que par l'utilisation de la méthode `del_option`). Pour ce contrôle de similitude, l'option remplacée n'est pas comparée sur sa clé figée (la nouvelle option peut donc porter le même nom que l'option qu'elle remplace), mais l'est toujours sur son ID.
> - Pour `ParameterFamily.STATIC` et `ParameterFamily.DYNAMIC`, aucun remplacement n'a lieu : un même modèle peut contenir autant d'options associées à une même famille que nécessaire, chacune étant identifiée par sa clé figée. Une option dont le nom correspond à la clé figée d'une option déjà présente provoque l'exception `OptionAlreadyExistsError` (voir le contrôle de similitude ci-dessus).
> - Si `player_attribute` vaut une chaîne de caractères, alors la valeur choisie de l'option sera attribuée telle quelle à cet attribut (un seul cas possible pour l'instant: `name`).
> - Si `player_attribute` vaut `ParameterFamily.STATIC` ou `ParameterFamily.DYNAMIC`, alors l'option sera ajoutée en tant que champ dans les dictionnaires correspondants de l'objet `Player` généré (`static_state` ou `dynamic_state`), sous la forme:
>
> | Clé     | Valeur     |
> |---------|------------|
> | Valeur de l'attribut `name` de l'option | valeur choisie de l'option |
>
> - Chaque option reçoit, au moment de l'appel à `add_option`, une clé figée : il s'agit de la valeur de l'attribut `name` de l'option à cet instant. Une modification ultérieure de l'attribut `name` de l'option n'a aucun effet sur cette clé. Pour les options associées à `ParameterFamily.STATIC` ou `ParameterFamily.DYNAMIC`, c'est cette clé qui est utilisée dans `static_state` ou `dynamic_state`, pour la création des joueurs comme pour les vérifications effectuées par la partie. Pour toutes les options, c'est également cette clé qui sert au contrôle de similitude : deux options d'un même modèle ne peuvent donc jamais partager la même clé figée. Le modèle enregistrant une copie de l'option fournie, et ne proposant aucun moyen de renommer une option qu'il contient, la clé figée d'une option ajoutée par `add_option` reste égale à son nom. Elle ne peut en différer que pour une option reconstruite à partir d'une représentation fournissant explicitement sa clé (méthodes `from_dict`, par exemple lors de la restauration d'une sauvegarde).

- `get_option`: fournit une option spécifique du modèle.
  - Paramètres:
    - `option_id` (str): l'ID de l'option à obtenir. Obligatoire.
  - Exceptions émises:
    - `KeyError` si l'option n'existe pas dans le modèle.
  - Valeur de retour: un objet `OptionEntry` décrivant l'option demandée, avec ses paramètres `unicity` et `player_attribute` et sa clé figée.

- `del_option`: supprime une option du modèle.
  - Paramètres:
    - `option_id` (str): l'ID de l'option à supprimer. Obligatoire.
  - Exceptions émises:
    - `KeyError` si l'option n'existe pas dans le modèle.
  - Valeur de retour: Aucune.

- `to_dict`: fournit une représentation du modèle sous forme de dictionnaire, commune à la sauvegarde et aux échanges réseau.
  - Paramètres: Aucun.
  - Valeur de retour: un objet `dict` présentant les éléments suivants:

    | Clé | Valeur |
    |-----|--------|
    | `template_id` | L'ID du modèle. |
    | `name` | Le nom du modèle. |
    | `options` | La liste des options du modèle, dans leur ordre d'ajout, chacune sous la forme retournée par la méthode `to_dict` de la classe `OptionEntry`. |

- `from_dict` (méthode de classe): crée un modèle à partir d'une représentation sous forme de dictionnaire, au format retourné par la méthode `to_dict`. Cette méthode est utilisée pour la restauration d'une sauvegarde, et par le serveur pour la création et la modification de modèles à partir des données reçues des clients.
  - Paramètres:
    - `data` (dict): la représentation du modèle. La clé `name` est obligatoire. La clé `options` est optionnelle (aucune option si absente). La clé `template_id` est optionnelle. Obligatoire.
  - Précision d'implémentation: si la clé `template_id` est présente, le modèle créé conserve cet ID ; sinon, un nouvel ID est généré. Chaque option est reconstruite par la méthode `from_dict` de la classe `OptionEntry`, puis ajoutée au modèle dans l'ordre de la liste, selon les règles de la méthode `add_option` (contrôle de similitude, remplacement d'une option associée à l'attribut `name`), mais en conservant son ID et sa clé figée lorsqu'ils sont fournis. La création est atomique : si l'une des options est rejetée, aucun modèle n'est créé. Le dictionnaire fourni n'est pas modifié.
  - Exceptions émises:
    - `TypeError` ou `ValueError`: si les données sont mal formées, ou dans les mêmes cas que la méthode `from_dict` de la classe `OptionEntry`.
    - `OptionAlreadyExistsError`: si deux options de la liste partagent le même ID ou la même clé figée.
  - Valeur de retour: l'objet `PlayerFactoryTemplate` créé.

#### Classe `PlayerFactory`

Cette classe permet de créer des objets `Player` à partir d'options pré-établies. Cette classe est particulièrement utile pour définir les caractéristiques des joueurs selon le type de jeu auquel ils vont participer. Par exemple, pour un jeu d'échecs, les joueurs sont caractérisés par la couleur blanche ou noire, s'excluant mutuellement (il ne peut pas y avoir 2 joueurs de même couleur). Ces contraintes peuvent être implémentées dans une instance de `PlayerFactory`, et servir à générer les objets `Player` compatibles avec le jeu d'échecs porté par un objet `Game` auquel l'objet `PlayerFactory` aura été associé.

Un objet `PlayerFactory` n'est typiquement utilisé pour créer des objets `Player` que dans le cadre d'une partie en particulier. Ainsi, un objet `PlayerFactory` ne devrait s'instancier que dans l'espace de nom d'un objet `Game`, et jamais dans l'espace de nom global. En réalité, l'objet `PlayerFactory` ne devrait être créé qu'avec la méthode `create_player_factory` de l'objet `Game` dans lequel on souhaite l'intégrer.

L'utilisateur y accède aux options au travers de l'attribut `options` (pour obtenir les ID et noms des options) et par la méthode `get_option` (pour obtenir l'option dans son intégralité, avec ses paramètres `unicity` et `player_attribute`, sa clé figée, sa liste d'exclusion et la valeur proposée). Cela permet à l'utilisateur de choisir une valeur pour chaque option. Les valeurs choisies sont ensuite transmises en une seule fois, en paramètre de la méthode `create_player`, qui crée l'objet `Player` correspondant.

La factory ne conserve aucune valeur en cours de saisie : chaque appel à `create_player` est indépendant des autres. Plusieurs utilisateurs peuvent ainsi préparer simultanément leur joueur à partir de la même factory, sans que leurs choix n'interfèrent.

La liste des joueurs de la partie (attribut `players` de l'objet `Game` associé) est l'unique référence pour déterminer les valeurs exclues : la factory ne réserve aucune valeur. Un objet `Player` créé par la factory n'est pris en compte dans les exclusions qu'à partir du moment où il a effectivement rejoint la partie par la méthode `join_game_as_player`, et cesse de l'être dès qu'il en est retiré. C'est la méthode `join_game_as_player` qui effectue la vérification définitive des contraintes de la factory. Pour que les choix d'un utilisateur soient immédiatement pris en compte dans les valeurs proposées aux suivants, il est recommandé de créer les joueurs au moyen de la méthode `create_and_join_player` de la classe `Game`, qui enchaîne la création du joueur et son introduction dans la partie en une seule opération.

> Précision d'implémentation: les valeurs exclues ne sont pas stockées, mais calculées à chaque fois qu'elles sont nécessaires (méthodes `get_option` et `create_player`). Pour chaque option créée avec `unicity` à `True`, les valeurs exclues sont les valeurs de cette option portées par les objets `Player` présents dans l'attribut `players` de la partie associée (les observateurs sont ignorés). La valeur portée par un joueur est lue selon le paramètre `player_attribute` de l'option : dans l'attribut `name` du joueur, ou dans `static_state` / `dynamic_state` à la clé figée lors de l'ajout de l'option au modèle (voir la méthode `add_option` de la classe `PlayerFactoryTemplate`). Un joueur ne portant pas de valeur pour cette option, ou portant la valeur `None`, est ignoré pour cette option.

La classe `PlayerFactory` s'instancie avec les paramètres suivants:

| Nom        | Type | Description      | Obligatoire | Valeur par défaut |
|------------|------|------------------|-------------|-------------------|
| `template` | `PlayerFactoryTemplate` | Le modèle dont la factory copie les options, ainsi que leurs paramètres `unicity` et `player_attribute`, et leurs clés figées. | Oui | - |
| `game_id`  | str  | L'ID de l'objet `Game` auquel la factory est associée. La partie est retrouvée au travers de la méthode de classe `Game.get_by_id`. | Oui | - |

Ces paramètres sont fournis par la méthode `create_player_factory` de la classe `Game`, qui est le seul moyen prévu pour créer un objet `PlayerFactory`.

> Précision d'implémentation: à l'instanciation, les objets `Option` du modèle sont copiés dans la factory (ils ne sont pas partagés), de même que leurs paramètres `unicity` et `player_attribute` et leurs clés figées. Une modification ultérieure du modèle (ajout, suppression ou remplacement d'option) ou des objets `Option` qu'il contient n'est pas répercutée sur la factory, et inversement. Chaque option copiée reçoit un nouvel ID, généré avec `uuid.uuid4()` : les ID des options de la factory sont donc distincts de ceux des options du modèle, et doivent être obtenus au travers de l'attribut `options` de la factory.

Elle présente les attributs suivants:

| Nom        | Type | Description                     | Modifiable | Précision d'implémentation |
|------------|------|---------------------------------|------------|----------------------------|
| `ID`       | str  | Identifiant unique de la factory| Non        | S'initialise automatiquement avec la valeur de `uuid.uuid4()`.                          |
| `options`    | list[tuple[str,str]] | Liste des ID et noms des options de la factory, sous forme de tuples (ID, nom)  | Non        | Une nouvelle liste est créée à chaque demande de lecture de cet attribut, dont une éventuelle modification n'a aucun impact sur les options contenues dans la factory.                              |

La classe `PlayerFactory` présente les méthodes suivantes:

- `get_option`: fournit une option spécifique de la factory.
  - Paramètres:
    - `option_id` (str): l'ID de l'option à obtenir. Obligatoire.
    - `context` (dict[str, str]\|`None`): le contexte fournissant la valeur des constantes d'exécution pour le calcul de la valeur proposée (voir le paragraphe "Constantes d'exécution" de la classe `Option`). Optionnel. Valeur par défaut: `None`.
  - Exceptions émises:
    - `KeyError` si l'option n'existe pas dans la factory.
  - Valeur de retour: un objet `dict` présentant les éléments suivants:

    | Clé    | Valeur  |
    |--------|---------|
    | `entry`| un objet `OptionEntry` décrivant l'option demandée, avec ses paramètres `unicity` et `player_attribute` et sa clé figée. |
    | `exclusions`| la liste des valeurs exclues pour cette option, calculée au moment de l'appel à partir des joueurs présents dans la partie. Liste vide pour une option créée avec `unicity` à `False`. |
    | `proposed_value`| la valeur proposée pour cette option, calculée au moment de l'appel (voir ci-dessous). Elle peut servir à pré-remplir un formulaire de saisie, et c'est elle qui est utilisée par `create_player` si aucune valeur n'est fournie pour cette option. |

> Précision d'implémentation: la valeur proposée est la valeur par défaut de l'option, telle que retournée par la méthode `evaluate_default` de l'objet `Option`. Celle-ci est appelée avec le contexte fourni, complété par la factory de la constante `GAMENAME` (nom de la partie associée) si elle n'y figure pas déjà, et avec les valeurs exclues de l'option (paramètre `exclusions`), de sorte qu'un tirage aléatoire ne retienne jamais une valeur exclue. Si la valeur par défaut ainsi évaluée s'avère être une valeur exclue (selon les exclusions calculées au moment de l'appel), alors la valeur proposée est la valeur suivante, déterminée selon le type de l'option:
>
> | Type d'option | Valeur suivante |
> |---------------|-----------------|
> | `OptionType.LIST` | Le premier élément non exclu de `choices`, en parcourant les choix à partir de celui qui suit la valeur par défaut, puis en reprenant au début de la liste. |
> | `OptionType.RANGE` | La première valeur possible non exclue, en parcourant les valeurs possibles par ordre croissant à partir de la valeur par défaut, jusqu'à `max_value`, puis si nécessaire par ordre décroissant en dessous de la valeur par défaut, jusqu'à `min_value`. Lorsque l'une des bornes n'est pas définie, la recherche aboutit toujours, les valeurs exclues étant en nombre fini. |
> | `OptionType.CHECK` | L'autre valeur booléenne. |
> | `OptionType.TEXT` | `""` (chaîne vide). |
>
> S'il n'y a plus de valeur possible (toutes les valeurs sont exclues, ou la chaîne vide est elle-même exclue pour une option `OptionType.TEXT`), alors la valeur proposée est `None`.
>
> Les valeurs sont comparées aux valeurs exclues après application des règles de conversion de la classe `Option`, selon les règles suivantes, qui s'appliquent également au contrôle d'unicité effectué par la méthode `join_game_as_player` de la classe `Game`:
>
> | Type d'option | Règle de comparaison |
> |---------------|----------------------|
> | `OptionType.RANGE` | Égalité numérique : `3` et `3.0` sont égaux. Pour une option décimale, l'égalité est évaluée avec une tolérance (fonction `math.isclose`). |
> | `OptionType.CHECK` | Égalité stricte. |
> | `OptionType.LIST` | Égalité stricte. |
> | `OptionType.TEXT` | Égalité insensible à la casse et aux espaces de début et de fin de chaîne : `"Alice"`, `"alice"` et `" ALICE "` sont considérés comme identiques. La valeur portée par le joueur reste néanmoins celle qui a été choisie, sans transformation. |

- `create_player`: génère un objet `Player` à partir des valeurs choisies pour les options de la factory.
  - Paramètres:
    - `values` (dict[str, any]): les valeurs choisies, sous la forme d'un dictionnaire dont les clés sont les ID des options de la factory (tels que fournis par l'attribut `options`) et les valeurs sont les valeurs choisies pour ces options. Il n'est pas nécessaire de fournir une valeur pour chaque option : une option absente du dictionnaire prend sa valeur proposée (voir la méthode `get_option`). Une valeur `None` signifie "pas de choix" : l'option correspondante est traitée comme si elle était absente du dictionnaire, et prend donc sa valeur proposée. Optionnel. Valeur par défaut: dictionnaire vide (toutes les options prennent leur valeur proposée).
    - `context` (dict[str, str]\|`None`): le contexte fournissant la valeur des constantes d'exécution, utilisé pour calculer la valeur proposée des options absentes du dictionnaire `values` (voir la méthode `get_option`). Les valeurs fournies dans `values` ne sont jamais évaluées comme des constantes d'exécution : une chaîne telle que `"%%USERNAME%%"` y est une valeur ordinaire. Elles sont en revanche converties selon les règles de conversion de la classe `Option`. Optionnel. Valeur par défaut: `None`.
  - Exceptions émises:
    - `InvalidOptionValueError` si une clé du dictionnaire `values` ne correspond à aucune option de la factory (`reason` à `"UNKNOWN_OPTION"`), si une valeur fournie n'est pas compatible avec le type attendu pour l'option correspondante (`reason` à `"INCOMPATIBLE_TYPE"`), ou si une valeur fournie n'est pas valide pour l'option correspondante (`reason` à `"INVALID_VALUE"`).
    - `OptionValueAlreadyGivenError` si une valeur fournie pour une option créée avec `unicity` à `True` fait partie des valeurs exclues au moment de l'appel.
    - `LackingOptionError` si une option absente du dictionnaire `values` n'a pas de valeur proposée (valeur proposée à `None`), avec `reason` à `"NO_AVAILABLE_VALUE"`.
  - Valeur de retour: un objet `Player`.

> Précision d'implémentation: la méthode ne modifie pas l'état de la factory. La création d'un objet `Player` ne réserve aucune valeur : l'objet créé n'est pris en compte dans les exclusions qu'une fois ajouté à la partie par la méthode `join_game_as_player`. Deux appels successifs ou simultanés à `create_player` avec la même valeur pour une option unique peuvent donc tous deux réussir : c'est lors de l'introduction des joueurs dans la partie que le second sera refusé (exception `OptionValueAlreadyGivenError`). Le dictionnaire `values` fourni n'est pas modifié par la méthode.

- `to_dict`: fournit une représentation de la factory sous forme de dictionnaire, utilisée pour la sauvegarde de la partie à laquelle elle est associée.
  - Paramètres: Aucun.
  - Valeur de retour: un objet `dict` présentant les éléments suivants:

    | Clé | Valeur |
    |-----|--------|
    | `factory_id` | L'ID de la factory. |
    | `options` | La liste des options de la factory, dans leur ordre de définition, chacune sous la forme retournée par la méthode `to_dict` de la classe `OptionEntry`. |

- `from_dict` (méthode de classe): recrée une factory à partir d'une représentation sous forme de dictionnaire, au format retourné par la méthode `to_dict`, sans passer par un modèle. Cette méthode est réservée à la restauration d'une partie sauvegardée : en dehors de ce cas, une factory doit être créée par la méthode `create_player_factory` de la classe `Game`.
  - Paramètres:
    - `data` (dict): la représentation de la factory. Obligatoire.
    - `game_id` (str): l'ID de la partie à laquelle la factory est associée. Obligatoire.
  - Précision d'implémentation: la factory et ses options conservent les ID et les clés figées fournis. Chaque option est reconstruite par la méthode `from_dict` de la classe `OptionEntry`. Le dictionnaire fourni n'est pas modifié.
  - Exceptions émises:
    - `TypeError` ou `ValueError`: si les données sont mal formées, ou dans les mêmes cas que la méthode `from_dict` de la classe `OptionEntry`.
    - `OptionAlreadyExistsError`: si deux options de la liste partagent le même ID ou la même clé figée.
  - Valeur de retour: l'objet `PlayerFactory` créé.

#### Classe `Game`
Cette classe représente une partie de jeu. Elle s'instancie avec les paramètres suivants:

| Nom                 | Type        | Description | Obligatoire | Valeur par défaut |
|---------------------|-------------|-------------|-------------|-------------------|
| `name`              | str\|`None` | Le nom de la partie.  | Non  | `None` |
| `max_players`       | int\|`None` | Nombre maximal de joueurs. Si `None`, alors il n'y a pas de limite. Si 0 ou négatif, alors aucun joueur n'est autorisé.| Non | `None` |
| `max_observers`     | int\|`None` | Nombre maximal d'observateurs. Si `None`, alors il n'y a pas de limite. Si 0 ou négatif, alors aucun observateur n'est autorisé.  | Non  | `None` |
| `password`          | str\|`None` | Mot de passe de la partie. Si `None`, alors la partie est publique (aucun mot de passe n'est nécessaire pour accéder à la partie). | Non  | `None`|
| `observer_password` | str\|`None` | Mot de passe des observateurs. Si `None`, alors les observateurs utilisent le mot de passe de la partie, défini par le paramètre `password`. Si celui-ci vaut également `None`, alors les observateurs peuvent accéder à la partie sans mot de passe. | Non | `None` |
| `turn_based`        | bool        | `True` si le jeu est au tour par tour, `False` pour un jeu simultané. | Non  | `False` |
| `min_players`       | int         | Nombre minimal de joueurs pour que la partie puisse démarrer. Si 0 (ou négatif), alors la partie peut démarrer même sans aucun joueur. S'il est supérieur à `max_players`, cela revient à avoir `min_players = max_players` : il faut exactement le nombre maximal de joueurs pour démarrer la partie. | Non | `0` |
| `**kwargs`          | variable    | Paramètres optionnels pour personnaliser la partie. Chaque paramètre doit se présenter sous la forme d'un tuple `(famille, valeur_initiale)` dont `famille` est un objet `ParameterFamily` qui spécifie le caractère statique ou dynamique du paramètre, et `valeur_initiale` sa valeur initiale. Le choix de la famille se fait à la convenance de l'utilisateur, pour l'aider à classer les informations, mais n'a aucun impact sur le traitement interne (les familles sont toutes traitées de la même manière). | Non  | - |

La classe présente les attributs suivants:

| Nom             | Type            | Description  | Modifiable | Précision d'implémentation |
|-----------------|-----------------|--------------|------------|----------------------------|
| `ID`            | str             | L'identifiant unique de la partie. | Non | S'initialise automatiquement avec la valeur de `uuid.uuid4()`.|
| `name`          | str\|`None`     | Le nom de la partie. `None` si la partie n'a pas de nom. | Oui        | S'initialise avec le paramètre `name`. |
| `hash`          | str\|`None`     | Le hash du mot de passe de la partie. `None` si la partie est publique (sans mot de passe).| Non  | Le hash est automatiquement généré à partir de `password` avec `bcrypt`. |
| `observer_hash` | str\|`None`     | Le hash du mot de passe de l'observateur. `None` si aucun mot de passe d'observation n'est défini. | Non  | Le hash est automatiquement généré à partir de `observer_password` avec `bcrypt`.|
| `turn_based`    | bool            | `True` si le jeu est au tour par tour, `False` pour un jeu simultané. | Non  | -  |
| `min_players`   | int             | Nombre minimal effectif de joueurs pour que la partie puisse démarrer (0 signifie aucun minimum). | Non | S'initialise avec le paramètre `min_players`. Si cette valeur est supérieure à `max_players` (lorsqu'il ne vaut pas `None`), c'est `max_players` qui est retourné. |
| `player_factory`    | `PlayerFactory`\|`None` | Fabrique de joueurs pour aider à la création des joueurs de la partie, et contrôler leurs paramètres lors de leur introduction dans la partie. Si `None`, alors il n'y a ni aide à la création des joueurs, ni contrôle de leurs paramètres lors de leur introduction dans la partie. | Non | Se crée à partir de la méthode `create_player_factory`. |
| `players`       | Tuple[str] | Tuple (liste non mutable) des ID des objets `Player` représentant les joueurs de la partie. L'ordre dans lequel sont présentés les joueurs correspond à l'ordre dans lequel les joueurs prennent leurs tours dans une partie au tour par tour. Certains jeux autorisent le changement d'ordre en cours de partie. Des méthodes spécifiques sont donc à disposition pour réaliser ces changements. Ne pas essayer de modifier l'ordre directement dans cet attribut. | Non | La variable interne correspondante ( `_players`) est une liste qui est transformée en tuple pour son affichage public au travers de l'attribut `players`. |
| `observers`     | Tuple[str] | Tuple (liste non mutable) des ID des objets `Player` représentant les observateurs de la partie. | Non  | La variable interne correspondante ( `_observers`) est une liste qui est transformée en tuple pour son affichage public au travers de l'attribut `observers`. |
| `current_player`| str        | ID de l'objet `Player` représentant le joueur dont le tour est en cours. N'a de sens que pour les parties à tour par tour. | Non  | - |
| `game_state`    | `GameState` | État actuel de la partie. | Non  | - |
| `static_state`  | dict | Attributs personnalisés de la partie, dont la vocation est de stocker des informations qui ne changent pas ou peu pendant la partie.  | Oui  | S'initialise automatiquement avec les paramètres spécifiés comme appartenant à la famille `ParameterFamily.STATIC`, mais peut être complété par la suite par tout autre paramètre au choix de l'utilisateur. Par exemple, si `Game` est instancié avec `Game([...], style=(ParameterFamily.STATIC, "blitz"), score=(ParameterFamily.DYNAMIC, "0-0"))`, alors `static_state` est égal à `{"style":"blitz"}`. |
| `dynamic_state` | dict | Attributs personnalisés de la partie, dont la vocation est de stocker des informations qui peuvent être modifiées souvent pendant la partie. | Oui        | S'initialise automatiquement avec les paramètres spécifiés comme appartenant à la famille `ParameterFamily.DYNAMIC`, mais peut être complété par la suite par tout autre paramètre au choix de l'utilisateur. Par exemple, si `Game` est instancié avec `Game([...], style=(ParameterFamily.STATIC, "blitz"), score=(ParameterFamily.DYNAMIC, "0-0"))`, alors `dynamic_state` est égal à `{"score":"0-0"}`.    |

Chaque objet `Game` créé (ou restauré depuis une sauvegarde) est enregistré dans un registre global, indexé par son ID. C'est ce registre qui permet de désigner une partie par son seul ID, par exemple dans la méthode `add_game` de la classe `GameGroup`.

> Précision d'implémentation: l'attribut `player_factory`, lorsqu'il est défini, facilite la création des joueurs de la partie, en permettant de créer des joueurs personnalisés à partir de la classe `PlayerFactory` plutôt que de créer des joueurs par défaut à partir de la classe `Player`. Son utilisation n'est pas obligatoire, et les objets `Player` créés à partir de cette factory doivent être traités comme n'importe quel autre objet `Player`: ils doivent être intégrés à la partie en utilisant la méthode `join_game_as_player`. La méthode `create_player` de la factory ne les intègre pas automatiquement à la partie. Pour créer un joueur et l'intégrer à la partie en une seule opération, il convient d'utiliser la méthode `create_and_join_player`.
> Toutefois, si `player_factory` est défini, alors l'ajout de joueurs par la méthode `join_game_as_player` vérifie que l'objet `Player` transmis répond bien aux contraintes de la factory, sur les options qui y sont spécifiées : présence de l'option, compatibilité du type de la valeur, validité de la valeur, et unicité de la valeur parmi les joueurs de la partie pour les options créées avec le paramètre `unicity` à `True`. Le détail de ces vérifications, et des exceptions levées, est décrit dans la méthode `join_game_as_player`. La liste des joueurs de la partie est l'unique référence pour l'unicité des valeurs : retirer un joueur de la partie rend automatiquement ses valeurs à nouveau disponibles. Ces vérifications ne sont effectuées qu'au moment de l'introduction d'un joueur : l'unicité n'est donc garantie qu'au moment du `join`, et une modification ultérieure des valeurs portées par les joueurs n'est pas contrôlée.

La classe `Game` présente les méthodes suivantes:

- `get_by_id` (méthode de classe): permet de retrouver une partie existante à partir de son ID.
  - Précision d'implémentation: Le registre ne conserve que des références faibles (`weakref.WeakValueDictionary`) : il n'empêche pas la destruction d'un objet `Game` qui n'est plus utilisé par ailleurs.
  - Paramètres:
    - `game_id` (str): l'ID de la partie recherchée. Obligatoire.
  - Valeur de retour: L'objet `Game` correspondant, ou `None` si aucune partie existante ne porte cet ID.
- `change_password`: permet de changer le mot de passe de la partie. Le paramètre `hash` de l'instance courante est mis à jour avec le nouveau mot de passe via `bcrypt`
    - Paramètres:
      - `new_password` (str): le nouveau mot de passe à utiliser pour la partie. Obligatoire.
    - Valeur de retour:
      - Aucune.

- `create_player_factory`: permet de créer une factory de joueur à partir d'un modèle.
  - Description: Cette méthode permet de créer une factory de joueur à partir d'un modèle, ou de remplacer une factory de joueur existante. Si le modèle est `None`, alors la factory est supprimée. Une fois créée, la factory est stockée dans l'attribut `player_factory` de l'instance courante. Cette méthode n'est utilisable que tant que la partie n'a pas démarré (`game_state` à `GameState.PENDING`) : la création, le remplacement et la suppression de la factory sont interdits une fois la partie démarrée, en pause ou terminée. De plus, la création ou le remplacement de la factory (paramètre `template` différent de `None`) ne sont autorisés que si la partie ne compte encore aucun joueur : la présence d'observateurs n'empêche pas l'opération. Ainsi, tous les joueurs de la partie sont nécessairement vérifiés au regard des contraintes de la factory lors de leur introduction. La suppression de la factory (paramètre `template` à `None`) reste possible lorsque la partie compte déjà des joueurs, tant qu'elle est à l'état `GameState.PENDING`. Dans tous les cas d'interdiction, l'attribut `player_factory` n'est pas modifié.
  - Précision d'implémentation: la factory est instanciée avec le modèle fourni et l'ID de l'instance courante (paramètres `template` et `game_id` de la classe `PlayerFactory`). Les observateurs étant ignorés dans le calcul des valeurs exclues, leur présence éventuelle au moment de la création de la factory est sans effet sur celle-ci.
  - Paramètres:
    - `template` (`PlayerFactoryTemplate`|`None`): le modèle à utiliser pour créer la factory. Obligatoire.
  - Exceptions émises:
    - `TypeError`: si le paramètre `template` n'est pas de type `PlayerFactoryTemplate` ou `None`.
    - `GameAlreadyStartedError`: levée si la partie est en cours (`GameState.IN_PROGRESS` ou `GameState.PAUSING`).
    - `GameIsFinishedError`: levée si la partie est terminée (`GameState.FINISHED`).
    - `GameHasPlayersError`: levée si le paramètre `template` n'est pas `None` et que la partie compte déjà au moins un joueur.
  - Valeur de retour:
      - Aucune.

- `join_game_as_player`: permet de rejoindre une partie en tant que joueur.
  - Description: Cette méthode permet à un joueur de rejoindre une partie en spécifiant son ID ou son objet `Player` et éventuellement un mot de passe si la partie est privée. Elle lance une exception si le joueur n'existe pas ou si le mot de passe est incorrect. Si l'attribut `player_factory` est défini, alors l'objet `Player` est vérifié, et n'est ajouté que s'il répond bien aux contraintes de la factory, sur les options qui y sont spécifiées (les options non traitées par la factory sont ignorées). Pour chacune de ces options, la valeur portée par le joueur (lue dans son attribut `name`, ou dans `static_state` / `dynamic_state` à la clé figée de l'option) fait l'objet des vérifications suivantes, dans cet ordre :
    1. Présence : si la valeur est absente de l'objet `Player`, ou si elle vaut `None` (ce qui est considéré comme une absence de valeur), l'exception `LackingOptionError` est levée, avec `reason` à `"ABSENT_FROM_PLAYER"`.
    2. Type : si la valeur n'est pas acceptée pour le type de l'option, selon les règles de conversion de la classe `Option`, l'exception `InvalidOptionValueError` est levée, avec `reason` à `"INCOMPATIBLE_TYPE"`.
    3. Validité : si la valeur n'est pas valide pour l'option (en dehors des bornes `min_value` / `max_value`, ne correspondant pas à un incrément `step`, ou absente de `choices`), l'exception `InvalidOptionValueError` est levée, avec `reason` à `"INVALID_VALUE"`.
    4. Unicité : pour les options créées avec le paramètre `unicity` à `True`, si la valeur se retrouve dans un autre objet `Player` déjà introduit en tant que joueur (les observateurs sont ignorés dans cette vérification), l'exception `OptionValueAlreadyGivenError` est levée.

    Dans tous ces cas, le joueur n'est pas ajouté.
  - Précision d'implémentation: En cas de succès, la méthode ajoute l'ID de l'objet `Player` à la liste `_players` de l'instance courante. Les vérifications liées à la factory et l'ajout du joueur à la liste `_players` doivent être effectués de manière atomique (par exemple sous la protection d'un verrou), afin que deux joueurs portant la même valeur d'une option unique ne puissent pas être ajoutés simultanément.
  - Paramètres:
    - `player` (`Player`|str): le joueur qui rejoint la partie. Il s'agit soit de l'objet `Player` correspondant au joueur, soit une chaîne de caractères correspondant à son ID. Obligatoire.
    - `password` (str\|`None`): mot de passe pour rejoindre la partie. Si la partie est publique, alors il faut indiquer `None`. Optionnel. Valeur par défaut: `None`.
  - Exceptions émises:
    - `PlayerNotFoundError`: levée si le joueur spécifié n'existe pas.
    - `PasswordError`: levée si le mot de passe est incorrect.
    - `GameIsFullError`: levée si le nombre maximal de joueurs est atteint, et que l'ajout d'un nouveau joueur est impossible.
    - `OptionValueAlreadyGivenError`: levée si l'objet `Player` que l'on tente d'introduire présente une valeur d'option déjà présente avec la même valeur dans un autre objet `Player` déjà introduit en tant que joueur.
    - `LackingOptionError`: levée si l'objet `Player` que l'on tente d'introduire ne porte pas de valeur pour une option spécifiée dans la factory (`reason` à `"ABSENT_FROM_PLAYER"`).
    - `InvalidOptionValueError`: levée si l'objet `Player` que l'on tente d'introduire porte, pour une option spécifiée dans la factory, une valeur dont le type n'est pas compatible avec celui de l'option (`reason` à `"INCOMPATIBLE_TYPE"`), ou une valeur non valide pour cette option (`reason` à `"INVALID_VALUE"`).
  - Valeur de retour: Aucune.

- `create_and_join_player`: permet de créer un joueur à partir de la factory de la partie, et de l'ajouter immédiatement à la partie en tant que joueur.
  - Description: Cette méthode enchaîne, en une seule opération, l'appel à la méthode `create_player` de l'attribut `player_factory` et l'appel à la méthode `join_game_as_player` avec l'objet `Player` ainsi créé. Les deux étapes étant réalisées ensemble, un joueur créé par cette méthode est soit ajouté à la partie, soit abandonné : il ne peut pas exister de joueur créé mais pas encore introduit, dont les valeurs ne seraient pas prises en compte dans les exclusions de la factory. Cette méthode est le moyen recommandé de créer des joueurs lorsque la partie dispose d'une factory. Les méthodes `create_player` de la factory et `join_game_as_player` restent néanmoins utilisables séparément.
  - Précision d'implémentation: la création du joueur et son introduction dans la partie sont effectuées sous la protection du même verrou que celui utilisé par la méthode `join_game_as_player`, de sorte qu'aucun autre joueur ne puisse être ajouté entre le calcul des exclusions et l'ajout du joueur. Si l'introduction échoue (quelle qu'en soit la raison), l'objet `Player` créé n'est pas retourné et n'est référencé nulle part : il est alors détruit, et disparaît du registre global des joueurs (qui ne conserve que des références faibles). En cas de succès, l'ID de l'objet `Player` est ajouté à la liste `_players` de l'instance courante, comme avec la méthode `join_game_as_player`.
  - Paramètres:
    - `values` (dict[str, any]): les valeurs choisies pour les options de la factory, sous la même forme que le paramètre `values` de la méthode `create_player` de la classe `PlayerFactory`. Optionnel. Valeur par défaut: dictionnaire vide (toutes les options prennent leur valeur proposée).
    - `password` (str\|`None`): mot de passe pour rejoindre la partie. Si la partie est publique, alors il faut indiquer `None`. Optionnel. Valeur par défaut: `None`.
    - `context` (dict[str, str]\|`None`): le contexte fournissant la valeur des constantes d'exécution, transmis tel quel à la méthode `create_player` de la factory. Optionnel. Valeur par défaut: `None`.
  - Exceptions émises:
    - `PlayerFactoryNotDefinedError`: levée si l'attribut `player_factory` vaut `None`.
    - Toutes les exceptions de la méthode `create_player` de la classe `PlayerFactory` (`InvalidOptionValueError`, `OptionValueAlreadyGivenError`, `LackingOptionError`).
    - Toutes les exceptions de la méthode `join_game_as_player` (`PasswordError`, `GameIsFullError`, `OptionValueAlreadyGivenError`, `LackingOptionError`, `InvalidOptionValueError`), à l'exception de `PlayerNotFoundError`, sans objet ici puisque le joueur vient d'être créé.
  - Valeur de retour: l'objet `Player` créé et ajouté à la partie. Il appartient à l'appelant de le rattacher, le cas échéant, au compte utilisateur concerné (attribut `players_id` de la classe `User`).

- `remove_player`: permet de retirer un joueur de la partie.
  - Description: Cette méthode permet de retirer un joueur de la partie en spécifiant son ID ou son objet `Player`. Elle lance une exception si le joueur n'est pas trouvé dans la partie.
  - Précision d'implémentation: En cas de succès, la méthode retire l'ID de l'objet `Player` de la liste `_players` de l'instance courante. Si l'attribut `player_factory` est défini, aucun traitement supplémentaire n'est nécessaire : les valeurs exclues étant calculées à partir des joueurs présents dans la partie, les valeurs d'options portées par le joueur retiré redeviennent automatiquement disponibles dans la factory.
  - Paramètres:
    - `player` (`Player`|str): le joueur à retirer de la partie. Il s'agit soit de l'objet `Player` correspondant au joueur, soit une chaîne de caractères correspondant à son ID. Obligatoire.
  - Exceptions émises:
    - `PlayerNotFoundInGameError`: levée si le joueur spécifié n'est pas trouvé dans la partie.
  - Valeur de retour: Aucune.

- `join_game_as_observer`: permet de rejoindre une partie en tant qu'observateur.
  - Description: Cette méthode permet à un joueur de rejoindre une partie en tant qu'observateur. Elle lance une exception si la partie est privée et que le mot de passe est incorrect.
  - Précision d'implémentation: En cas de succès, la méthode ajoute l'ID de l'objet `Player` à la liste `_observers` de l'instance courante.
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
  - Précision d'implémentation: En cas de succès, la méthode retire l'ID de l'objet `Player` de la liste `_observers` de l'instance courante.
  - Paramètres:
    - `player` (`Player`|str): le joueur qui quitte la partie en tant qu'observateur. Il s'agit soit de l'objet `Player` correspondant au joueur, soit une chaîne de caractères correspondant à son ID. Obligatoire.
  - Exceptions émises:
    - `PlayerNotFoundInGameError`: levée si le joueur spécifié n'est pas trouvé dans la partie.
  - Valeur de retour: Aucune.

- `start`: permet de démarrer une partie.
  - Description: Cette méthode permet de démarrer une partie. Elle lance une exception si la partie est déjà en cours, si elle est terminée, ou si elle ne compte pas assez de joueurs. En cas de succès, la méthode passe l'attribut `game_state` à la valeur `GameState.IN_PROGRESS`.
  - Précision d'implémentation: Le statut `GameState.PAUSING` est aussi considéré comme une partie en cours. Le nombre de joueurs est comparé à l'attribut `min_players` ; avec la valeur par défaut (0), la partie peut démarrer sans aucun joueur.
  - Paramètres:
    - Aucun.
  - Exceptions émises:
    - `GameAlreadyStartedError`: levée si la partie est déjà en cours.
    - `GameIsFinishedError`: levée si la partie est terminée.
    - `NotEnoughPlayersError`: levée si le nombre de joueurs est inférieur à `min_players`.
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
Cette classe permet de regrouper plusieurs parties dans un seul objet. Elle permet de gérer les parties en parallèle et de les manipuler en tant que groupe. Elle s'instancie avec les paramètres suivants:

| Nom                 | Type        | Description | Obligatoire | Valeur par défaut |
|---------------------|-------------|-------------|-------------|-------------------|
| `name`              | str         | Le nom du groupe de parties.| Oui | - |
| `**kwargs`          | variable    | Paramètres optionnels pour personnaliser le groupe. | Non  | - |

La classe présente les attributs suivants:

| Nom             | Type            | Description  | Modifiable | Précision d'implémentation |
|-----------------|-----------------|--------------|------------|----------------------------|
| `ID`            | str             | L'identifiant unique du groupe. | Non | S'initialise automatiquement avec la valeur de `uuid.uuid4()`.|
| `name`          | str             | Le nom du groupe. | Oui        | - |
| `games`       | Tuple[str] | Tuple (liste non mutable) des ID des objets `Game` représentant les parties du groupe. | Non | La variable interne correspondante ( `_games`) est une liste qui est transformée en tuple pour son affichage public au travers de l'attribut `games`. |
| `parameters` | dict | Paramètres de personnalisation du groupe | Oui        | S'initialise automatiquement avec les paramètres spécifiés dans `kwargs`, mais peut être complété par la suite par tout autre paramètre au choix de l'utilisateur. |


La classe `GameGroup` présente les méthodes suivantes:

- `add_game`: permet d'ajouter une partie au groupe. La partie est ajoutée à la fin de la liste des parties du groupe. 
  - Description: Cette méthode permet d'ajouter une partie au groupe en spécifiant son ID ou son objet `Game` et éventuellement un mot de passe administrateur de groupe. Elle lance une exception si la partie n'existe pas ou si le mot de passe est incorrect. 
  - Précision d'implémentation: En cas de succès, la méthode ajoute l'ID de l'objet `Game` à la liste `_games` de l'instance courante.
  - Paramètres:
    - `game` (`Game`|str): l'instance de la partie à ajouter, ou une chaîne de caractères représentant l'ID de la partie à ajouter. Obligatoire.
  - Valeur de retour:
    - Aucune.
  - Exceptions émises:
    - `GameNotFoundError`: levée si la partie spécifiée n'existe pas.
- `remove_game`: permet de retirer une partie du groupe. La partie est retirée de la liste des parties du groupe.
  - Paramètres:
    - `game` (`Game`|str): l'instance de la partie à retirer, ou une chaîne de caractères représentant l'ID de la partie à retirer. Obligatoire.
  - Précision d'implémentation: En cas de succès, la méthode retire l'ID de l'objet `Game` de la liste `_games` de l'instance courante.
  - Valeur de retour:
    - Aucune.
  - Exceptions émises:
    - `GameNotFoundInGroupError`: levée si la partie spécifiée n'est pas présente dans le groupe.

#### Classe `User`
Cette classe représente un compte utilisateur. Celui-ci permet d'accéder à diverses capacités selon son niveau d'accès (authentification). Un utilisateur est une entité distincte du joueur : l'utilisateur gère les identifiants et les droits, tandis que le joueur gère la présence dans le jeu.

Un utilisateur peut participer à plusieurs parties simultanément, en tant que joueur comme en tant qu'observateur. Chaque participation nécessite la création d'un objet `Player` distinct, chacun rattaché au compte utilisateur au travers de l'attribut `players_id`. Un même objet `Player` ne peut en effet participer qu'à une seule partie.

Elle s'instancie avec les paramètres suivants:

| Nom        | Type | Description                     | Obligatoire | Valeur par défaut  |
|------------|------|---------------------------------|-------------|--------------------|
| `username` | str  | Le nom d'utilisateur du compte. | Oui         | -                  |
| `password` | str  | Le mot de passe du compte.      | Oui         | -                  |
| `email`    | str  | L'adresse e-mail du compte.     | Non         | `""` (chaîne vide) |


Si un objet `User` est instancié avec un `username` déjà utilisé dans une instance existante de `User`, une exception `UserAlreadyExistsError` est levée et l'instanciation échoue.

La classe présente les attributs suivants:

| Nom         | Type         | Description  | Modifiable | Précision d'implémentation  |
|-------------|--------------|--------------|------------|-----------------------------|
| `ID`        | str          | L'identifiant unique du compte utilisateur. | Non | S'initialise automatiquement avec la valeur de `uuid.uuid4()`.|
| `username`  | str          | Le nom d'utilisateur du compte.  | Non  | -|
| `hash`      | str          | Le hash du mot de passe du compte.| Non  | Le hash est automatiquement généré à partir de `password` avec `bcrypt`.|
| `email`     | str          | L'adresse e-mail du compte. | Oui  | -|
| `role`      | `UserRole` | Le rôle du compte (ie: son niveau de permission).  | Oui  | - |
| `groups_id` | List[str]    | Les identifiants des groupes pour lesquels le compte est administrateur. Uniquement utile si `role == UserRole.GROUP_ADMIN`. Une exception `GroupNotFoundError` est levée si un des identifiants ne correspond pas à un groupe existant. Dans ce cas la valeur de `groups_id` n'est pas mise à jour. | Non (mais mutable) | Initialisé avec une liste vide, cet attribut peut être complété et modifié grace aux méthodes de `list` telles que `append`, `extend`, `pop`, ... Comme il s'agit d'un attribut en lecture seule, la ré-affectation est interdite. |
| `players_id`    | List[str]     | Les identifiants des objets `Player` actifs (c'est-à-dire associés à une partie non terminée, soit en tant que joueur, soit en tant qu'observateur) créés lors d'une session où l'utilisateur s'est connecté. | Non (mais mutable) | Il est de la responsabilité de l'usager de la bibliothèque `multiplayer` de vérifier régulièrement cette liste, et en supprimer les identifiants des objets `Player` qui ne sont plus associés qu'à des parties terminées. Néanmoins, lorsque la fonction de persistance est activée, la sauvegarde des objets `User` effectue une vérification et un nettoyage de cette liste avant sauvegarde. Ainsi, lors de la restauration, cette liste devrait normalement être propre et cohérente avec les objets `Player` effectivement associés à des parties non terminés, ou associés à aucune partie (cas d'un objet `Player` en attente d'affectation d'une partie). |

La classe `User` présente les méthodes suivantes:

- `change_password`: permet de changer le mot de passe du compte utilisateur. Le paramètre `hash` de l'instance courante est mis à jour avec le nouveau mot de passe via `bcrypt`
    - Paramètres:
      - `new_password` (str): le nouveau mot de passe à utiliser pour le compte utilisateur. Obligatoire.
    - Valeur de retour:
      - Aucune.

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

Ce fichier contient la logique de sauvegarde et de restauration des objets instanciés à partir des classes `Player`, `User`, `Game`, `GameGroup` et `PlayerFactoryTemplate`. Les objets `Option` et `PlayerFactory` ne sont pas sauvegardés de manière autonome : ils le sont au sein de l'objet qui les contient (voir le paragraphe "Sauvegarde des options, des modèles et des factories" ci-dessous). Il définit la classe `Save`, dont chaque instance représente un fichier de sauvegarde et fait le lien entre un tampon en mémoire et un fichier persistant (document JSON ou base de données SQLite).

#### Classe `Save`
Cette classe permet de sauvegarder, de mettre à jour et de restaurer les objets du module. Les objets sont d'abord enregistrés dans un tampon en mémoire, puis écrits dans le fichier uniquement lors de l'appel explicite à la méthode `flush`. Elle s'instancie avec les paramètres suivants:

| Nom           | Type                | Description | Obligatoire | Valeur par défaut |
|---------------|---------------------|-------------|-------------|-------------------|
| `file_path`   | `Path`              | Le chemin du fichier de sauvegarde. | Oui | - |
| `save_format` | `SaveFormat`\|str   | Le format de sauvegarde. Il s'agit soit d'un membre de l'énumération `SaveFormat`, soit d'une chaîne de caractères (`"json"` ou `"sqlite"`). | Oui | - |

Comportement à l'instanciation:
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
  - Précision d'implémentation: avant la sauvegarde d'un objet `User`, une vérification est effectuée pour nettoyer la liste des identifiants des objets `Player` qui ne sont plus associés à aucune partie non terminée.
  - Paramètres:
    - `obj` (`Player`|`User`|`Game`|`GameGroup`|`PlayerFactoryTemplate`): l'instance à sauvegarder. Obligatoire. Un objet `Option` ou `PlayerFactory` fourni directement n'est pas pris en charge, et provoque l'exception `SaveError`.
  - Exceptions émises:
    - `SaveError`: levée si l'objet n'est pas une instance d'une classe prise en charge.
  - Valeur de retour: Aucune.

- `load`: permet de charger toutes les instances d'une classe donnée.
  - Description: Reconstruit et retourne la liste des instances de la classe demandée à partir du tampon en mémoire.
  - Paramètres:
    - `target` (str\|type): la classe à charger ou son nom (`Player`, `User`, `Game`, `GameGroup` ou `PlayerFactoryTemplate`). Obligatoire.
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

#### Sauvegarde des options, des modèles et des factories

Les objets `Option`, `PlayerFactoryTemplate` et `PlayerFactory` sont sauvegardés selon les règles suivantes.

**Objets `Option`**: ils ne sont jamais sauvegardés de manière autonome, mais uniquement au sein du modèle ou de la factory qui les contient. Au sein d'un modèle ou d'une factory, chaque option est sérialisée avec les paramètres qui lui ont été associés lors de son ajout au modèle, sous la forme retournée par la méthode `to_dict` de la classe `OptionEntry`:
- les éléments de l'option elle-même (`option_id`, `type`, `name`, `description`, `default`, `min`, `max`, `step`, `choices`), tels que retournés par la méthode `to_dict` de la classe `Option`. La valeur par défaut est sauvegardée brute, sans évaluation des éventuelles constantes d'exécution (ex: `"Joueur_%%RANDOM_NUMBER%%"`). La valeur `None` est représentée par `null` en JSON et `NULL` en SQLite ;
- les paramètres associés : `unicity`, `target` et `attribute` (représentation du paramètre `player_attribute`, qui permet de distinguer sans ambiguïté un attribut de l'objet `Player` d'une famille `ParameterFamily`), et `key` (clé figée).

Cette représentation est identique à celle utilisée dans les échanges réseau (voir le [Protocole d'échanges entre le client et le serveur](PROTOCOLE_FR.md), paragraphe "Représentation d'une option").

**Objets `PlayerFactoryTemplate`**: ils sont sauvegardés de manière autonome, comme les objets `Player`, `User`, `Game` et `GameGroup`, indexés par leur classe et leur ID. Chaque modèle est sérialisé avec son ID, son nom (`name`), et la liste ordonnée de ses options (avec, pour chacune, les éléments décrits ci-dessus), sous la forme retournée par la méthode `to_dict` de la classe `PlayerFactoryTemplate`, et restauré par sa méthode `from_dict`.

**Objets `PlayerFactory`**: ils ne sont jamais sauvegardés de manière autonome, mais uniquement au sein de l'objet `Game` auquel ils sont associés, dans l'élément `player_factory` de la partie. Cet élément vaut `null` (JSON) ou `NULL` (SQLite) lorsque la partie ne dispose pas de factory. Sinon, la factory est sérialisée avec son ID et la liste ordonnée de ses options (avec, pour chacune, les éléments décrits ci-dessus), sous la forme retournée par la méthode `to_dict` de la classe `PlayerFactory`, et restaurée par sa méthode `from_dict`. Les éléments suivants ne sont pas sauvegardés:
- l'ID de la partie associée, qui est celui de la partie dans laquelle la factory est sauvegardée ;
- le modèle à partir duquel la factory a été créée : les options de la factory étant des copies indépendantes de celles du modèle, la factory se suffit à elle-même, et sa restauration ne dépend pas de la présence du modèle dans la sauvegarde ;
- les valeurs exclues des options, qui ne sont jamais stockées mais calculées à partir des joueurs de la partie : elles sont donc automatiquement cohérentes après restauration, dès lors que les joueurs de la partie sont restaurés.

> Précision d'implémentation:
> - Lors de la restauration, tous les ID (des modèles, des factories et des options) sont restaurés à l'identique, sans nouvelle génération par `uuid.uuid4()`. Il en va de même des clés figées, qui sont restaurées telles quelles, même si elles diffèrent du nom actuel de l'option.
> - La restauration d'une option applique les mêmes contrôles que sa création (voir la classe `Option`), au travers des méthodes `from_dict`. Si les données restaurées sont incohérentes (type d'option inconnu, valeur de `target` ou de `attribute` non reconnue, valeur par défaut incompatible avec l'option, clés figées en double, etc.), les exceptions levées par les méthodes `from_dict` (`TypeError`, `ValueError`, `OptionAlreadyExistsError`) sont chaînées dans une exception `SaveError`.
> - La restauration d'un objet `Game` comportant une factory recrée directement l'objet `PlayerFactory` à partir des données sauvegardées, au moyen de la méthode `from_dict` de la classe `PlayerFactory`, sans passer par la méthode `create_player_factory` : les contrôles liés à l'état de la partie et à la présence de joueurs (exceptions `GameAlreadyStartedError`, `GameIsFinishedError` et `GameHasPlayersError`) ne s'appliquent donc pas à la restauration.
> - Compatibilité ascendante : un fichier de sauvegarde produit avant l'introduction de ces objets doit rester lisible. Une partie sauvegardée sans élément `player_factory` est restaurée avec `player_factory` à `None`, et un fichier ne contenant aucun modèle donne une liste vide lors du chargement de la classe `PlayerFactoryTemplate`.

### Contenu du fichier src/multiplayer/server.py

Ce fichier contient la logique de gestion des serveurs multijoueur.

#### Classe `GameServer`
La classe `GameServer` est responsable de la gestion des connexions et des communications avec les clients dans un environnement multijoueur. Elle assure la coordination des actions et la diffusion des informations aux clients connectés.

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
| `persistence_periodicity` | `int` | La durée en secondes entre chaque sauvegarde cyclique de la persistance (0 pour désactiver la sauvegarde périodique) | Non | 0 |
| `garbage_collection_periodicity` | `int` | La durée en secondes entre chaque effacement des objets "Player" qui ne sont associés qu'à des parties terminées, ou qui ne sont associés à aucune partie et ne sont plus accessibles (voir le paragraphe « Nettoyage automatique ») | Non | 900 |

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
  2. Un client envoie un message de découverte à cette adresse multicast. Voir le [Protocole d'échanges entre le client et le serveur](PROTOCOLE_FR.md) pour la description du protocole utilisé.
  3. Tous les serveurs abonnés au groupe multicast reçoivent le message.
  4. À la réception de ce message, chaque serveur vérifie que les données reçues correspondent aux attentes et répond directement au client en unicast UDP. Voir le [Protocole d'échanges entre le client et le serveur](PROTOCOLE_FR.md) pour la description du protocole utilisé.
- **Persistance**: La persistance permet de sauvegarder les données du serveur sur le disque dur, et de les restaurer lors du redémarrage du serveur. Par défaut, la persistance est désactivée (paramètre `persistence_mode=None`). Lorsque la persistance est activée, les données du serveur sont sauvegardées dans un fichier défini par le paramètre `persistence_path`. Le fichier est sauvegardé périodiquement si `persistence_periodicity > 0`, à chaque fois que le serveur est arrêté, et restauré lors du redémarrage du serveur. Il peut être également sauvegardé ou rechargé à la demande (voir les commandes de niveau **administrateur** dans le [Protocole d'échanges entre le client et le serveur](PROTOCOLE_FR.md)). Il est possible d'activer 2 modes de persistance :
  - `persistence_mode=SaveFormat.JSON` : permet de sauvegarder les données du serveur dans un fichier JSON. Par défaut (si `persistence_path=None`), le fichier est défini par `Path("data/server_data.json")`. Le fichier (ainsi que les répertoires y accédant) est créé automatiquement s'il n'existe pas déjà.
  - `persistence_mode=SaveFormat.SQLITE` : permet de sauvegarder les données du serveur dans une base de données SQLITE. Par défaut (si `persistence_path=None`), le fichier est défini par `Path("data/server_data.db")`. La base de données (ainsi que les répertoires y accédant) est créée automatiquement si elle n'existe pas déjà.
- **Nettoyage automatique** : Le serveur effectue périodiquement un nettoyage des objets `Player` qui ne sont associés qu'à des parties terminées. Les objets `Player` associés à aucune partie (cas des objets nouvellement créés en attente d'affectation de partie) ne sont, eux, pas concernés par ce nettoyage, tant qu'ils restent rattachés à une session ouverte ou listés dans l'attribut `players_id` d'un utilisateur. Un objet `Player` associé à aucune partie et qui n'est plus accessible (par exemple le joueur d'un client non authentifié dont la session a été fermée) est en revanche supprimé. La fréquence de ce nettoyage est définie par le paramètre `garbage_collection_periodicity` (en secondes).
- **Version et révision du protocole**: le serveur transmet la version majeure du protocole (`2`) dans le champ `version` de chaque message, et refuse tout message portant une autre version majeure. Il annonce sa révision du protocole (`"2.1"`) et la liste des fonctionnalités qu'il propose (`["player_factory"]`) dans la réponse à la requête `PROTOCOL_INFO`, utilisable au niveau `OPEN` avant toute authentification, ainsi que sa révision dans le champ `revision` de la réponse de découverte (`DISCOVERY_RESPONSE`). La révision et la liste des fonctionnalités sont définies par des constantes du module `server.py`, mises à jour à chaque nouvelle révision du protocole.
- **Modèles de factory de joueurs**: le serveur détient un registre des modèles de factory (objets `PlayerFactoryTemplate`), indexé par leur ID et commun à l'ensemble du serveur. Ces modèles sont exposés aux clients par les requêtes `FACTORY_TEMPLATE_LIST` et `FACTORY_TEMPLATE_GET` (niveau `BASE`), et gérés par les requêtes `FACTORY_TEMPLATE_CREATE`, `FACTORY_TEMPLATE_UPDATE` et `FACTORY_TEMPLATE_DELETE` (niveau `ADMIN`), décrites dans le [Protocole d'échanges entre le client et le serveur](PROTOCOLE_FR.md). Lorsque la persistance est activée, le registre est sauvegardé et restauré avec les autres données du serveur (classe `PlayerFactoryTemplate` de l'objet `Save`), y compris lors des sauvegardes et rechargements à la demande. La création, la modification et la suppression d'un modèle sont enregistrées dans le journal d'audit du serveur. Un modèle est appliqué à une partie uniquement lors de sa création (champ `factory_template_id` de la requête `GAME_CREATE`), par la méthode `create_player_factory` de la classe `Game` : la modification ou la suppression ultérieure du modèle est sans effet sur les parties déjà créées.
- **Création des joueurs à partir de la factory d'une partie**: les requêtes `GAME_FACTORY_GET` et `GAME_FACTORY_JOIN` s'appuient respectivement sur la méthode `get_option` de la classe `PlayerFactory` et sur la méthode `create_and_join_player` de la classe `Game`. Pour chacune de ces requêtes, le serveur construit lui-même le contexte d'évaluation des constantes d'exécution (voir le paragraphe "Constantes d'exécution" de la classe `Option`) à partir de la session et de la connexion du client : `USERNAME` (nom de l'utilisateur authentifié de la session, absent sinon), `CLIENTADDRESS` (adresse IP du client), `SERVERNAME` (attribut `name` du serveur) et `SERVERADDRESS` (adresse IP locale de la connexion). Le contexte n'est jamais accepté depuis le client. Les représentations des options transmises aux clients sont obtenues par la méthode `to_dict` des objets `OptionEntry` (et, pour la requête `FACTORY_TEMPLATE_GET`, par la méthode `to_dict` de l'objet `PlayerFactoryTemplate`). Pour la requête `FACTORY_TEMPLATE_CREATE`, le serveur crée le modèle au moyen de la méthode `from_dict` de la classe `PlayerFactoryTemplate`, sans fournir d'ID : le modèle et ses options reçoivent de nouveaux ID, et la clé figée de chaque option est son nom. Pour la requête `FACTORY_TEMPLATE_UPDATE`, le serveur construit de la même manière un nouveau modèle, en lui fournissant l'ID du modèle existant (`template_id`) et, si les options ne sont pas fournies, la représentation des options existantes ; en cas de succès, ce nouveau modèle remplace l'ancien dans le registre. Ces deux opérations sont ainsi atomiques : en cas d'erreur, le registre n'est pas modifié. Les exceptions levées par les méthodes `from_dict` sont traduites en codes d'erreur `INVALID_OPTION` (`TypeError`, `ValueError`) et `OPTION_ALREADY_EXISTS` (`OptionAlreadyExistsError`). Les exceptions levées par la bibliothèque sont traduites en codes d'erreur du protocole de la manière suivante, les attributs des exceptions alimentant le champ `details` de la réponse : `InvalidOptionValueError` donne `INVALID_OPTION_VALUE` (avec `option_id`, `value` et `reason`), `OptionValueAlreadyGivenError` donne `OPTION_VALUE_ALREADY_GIVEN` (avec `option_id` et `value`), `LackingOptionError` donne `LACKING_OPTION` (avec `option_id` et `reason`), et `PlayerFactoryNotDefinedError` donne `NO_PLAYER_FACTORY`. Le serveur tient également à jour, pour chaque partie dotée d'une factory, la liste des sessions abonnées à la notification `GAME_FACTORY_UPDATED`, et leur envoie cette notification à chaque arrivée ou départ d'un joueur dans la partie.

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
- `save_persistence`: Lance une sauvegarde de persistance immédiate.
  - Description: Déclenche immédiatement la sauvegarde des données persistantes du serveur sur le support configuré. Cette méthode est sans effet si la persistance n'est pas activée.
  - Paramètres: aucun
  - Retour: aucun

### Contenu du fichier src/multiplayer/client.py

Ce fichier contient la logique de gestion des clients multijoueur.

#### Classe `GameClient`
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
| `session_user` | `User\|None` | L'utilisateur associé à la session actuelle | Non | Mis à jour automatiquement lors de l'authentification de l'utilisateur. |
| `server_revision` | str\|`None` | La révision du protocole annoncée par le serveur (ex: `"2.1"`). `"2.0"` si le serveur ne prend pas en charge la requête `PROTOCOL_INFO`. `None` tant que le client n'est pas connecté. | Non | Mis à jour automatiquement par la méthode `connect`. |
| `server_features` | tuple[str, ...] | Les fonctionnalités optionnelles du protocole proposées par le serveur (ex: `("player_factory",)`). Tuple vide si le serveur ne prend pas en charge la requête `PROTOCOL_INFO`, ou tant que le client n'est pas connecté. | Non | Mis à jour automatiquement par la méthode `connect`. |

##### Méthodes

La classe `GameClient` présente les méthodes suivantes:

- `discover` (méthode de classe): Recherche les serveurs disponibles sur le réseau local.
  - Description: Envoie un message de découverte multicast en UDP et collecte les réponses des serveurs actifs.
  - Paramètres:
    - `timeout` (float): Temps d'attente maximum pour la réception des réponses (en secondes). Optionnel. Valeur par défaut: 2.0.
    - `multicast_group` (str): L'adresse multicast à utiliser. Optionnel. Valeur par défaut: `"239.255.0.1"`.
    - `multicast_port` (int): Le port multicast à utiliser. Optionnel. Valeur par défaut: 65434.
  - Valeur de retour: Une liste de dictionnaires, chaque dictionnaire contenant les informations d'un serveur découvert (nom, host, port, etc.), y compris sa révision du protocole (clé `revision`, qui vaut `"2.0"` si le serveur ne l'annonce pas).
- `connect`: Établit la connexion TCP avec le serveur.
  - Description: Tente d'ouvrir une connexion avec le serveur en utilisant les paramètres `host`, `port` et `use_tls` (ainsi que `tls_ca_path` si fourni, sinon utilise les certificats racines du système). Une fois la connexion établie, envoie une requête `PROTOCOL_INFO` pour renseigner les attributs `server_revision` et `server_features`. Si le serveur répond par le code d'erreur `UNKNOWN_TYPE` (serveur de révision 2.0), `server_revision` prend la valeur `"2.0"` et `server_features` un tuple vide, sans que la connexion échoue.
  - Paramètres: Aucun.
  - Valeur de retour: Aucun.
  - Exceptions émises:
    - `ConnectionError`: si la connexion échoue.
- `disconnect`: Ferme la connexion avec le serveur.
  - Description: Ferme proprement la connexion TCP actuelle.
  - Paramètres: Aucun.
  - Valeur de retour: Aucun.
- `login`: S'authentifie auprès du serveur.
  - Description: Envoie une requête d'authentification avec les identifiants fournis. En cas de succès, le client récupère les informations de l'utilisateur.
  - Paramètres:
    - `username` (str): Le nom d'utilisateur. Obligatoire.
    - `password` (str): Le mot de passe. Obligatoire.
  - Valeur de retour: L'instance `User` correspondant à l'utilisateur authentifié.
  - Exceptions émises:
    - `PasswordError`: si le mot de passe est incorrect.
    - `UserNotFoundError`: si l'utilisateur n'existe pas.
- `create_player`: Crée un joueur de session sur le serveur.
  - Description: Envoie une requête `PLAYER_CREATE` et, en cas de succès, crée localement un objet `Player` reflétant le joueur créé, avec l'ID attribué par le serveur. Si un utilisateur est authentifié, le serveur ajoute le joueur créé à la liste `players_id` de son compte, et l'objet `User` local de la session (attribut `session_user`) est mis à jour de la même manière. Les attributs personnalisés sont transmis au serveur, qui les range dans le dictionnaire choisi par le client (`static_state` ou `dynamic_state`), et sont également reportés dans l'objet `Player` local.
  - Paramètres:
    - `name` (str): Le nom du joueur à créer. Obligatoire.
    - `is_default` (bool): Si `True`, le joueur créé devient le joueur par défaut de la session. Optionnel. Valeur par défaut: `True`.
    - `static_attributes` (dict\|`None`): Les attributs personnalisés à ranger dans le dictionnaire `static_state` du joueur (champ `static_attributes` de la requête). Optionnel. Valeur par défaut: `None` (aucun attribut).
    - `dynamic_attributes` (dict\|`None`): Les attributs personnalisés à ranger dans le dictionnaire `dynamic_state` du joueur (champ `dynamic_attributes` de la requête). Optionnel. Valeur par défaut: `None` (aucun attribut).
  - Précision d'implémentation: les champs `static_attributes` et `dynamic_attributes` ont été introduits par la révision 2.1 du protocole. Auprès d'un serveur de révision 2.0 (attribut `server_revision` à `"2.0"`), qui ignorerait ces champs, les attributs dynamiques sont transmis dans le champ `attributes`, qui leur est équivalent ; les attributs statiques ne pouvant pas être transmis, la méthode lève alors l'exception `UnsupportedFeatureError` si `static_attributes` est fourni, sans envoyer la requête.
  - Valeur de retour: L'objet `Player` local correspondant au joueur créé.
  - Exceptions émises:
    - `UnsupportedFeatureError`: si `static_attributes` est fourni et que le serveur est de révision 2.0 (la requête n'est alors pas envoyée).
    - `MultiplayerError` (ou une sous-classe): si le serveur refuse la création.
    - `ConnectionError`: si le client n'est pas connecté.
- `update_player`: Modifie un joueur de la session sur le serveur.
  - Description: Envoie une requête `PLAYER_UPDATE` pour renommer le joueur, vider ses dictionnaires `static_state` et `dynamic_state`, ou les deux. La remise à zéro des attributs permet de réutiliser pour une autre partie un joueur qui a quitté sa partie ; le serveur la refuse tant que le joueur participe à une partie.
  - Paramètres:
    - `player_id` (str): L'ID du joueur à modifier. Obligatoire.
    - `name` (str\|`None`): Le nouveau nom du joueur. Optionnel. Valeur par défaut: `None` (nom inchangé).
    - `reset_state` (bool): Si `True`, les attributs personnalisés du joueur sont vidés. Optionnel. Valeur par défaut: `False`.
  - Valeur de retour: Un dictionnaire contenant les données de la réponse du serveur.
  - Exceptions émises:
    - `ValueError`: si ni nouveau nom ni remise à zéro ne sont demandés (la requête n'est alors pas envoyée).
    - `MultiplayerError` (ou une sous-classe): si le serveur refuse la modification.
    - `ConnectionError`: si le client n'est pas connecté.
- `create_game`: Crée une partie sur le serveur.
  - Description: Envoie une requête `GAME_CREATE`. Permet notamment de doter la partie d'une factory de joueurs, construite à partir d'un modèle détenu par le serveur (paramètre `factory_template_id`, voir la méthode `list_factory_templates`). Le modèle ne peut être choisi qu'à la création de la partie.
  - Paramètres:
    - `name` (str): Le nom de la partie. Obligatoire.
    - `min_players` (int): Le nombre minimal de joueurs pour démarrer la partie. Optionnel. Valeur par défaut: `0`.
    - `max_players` (int\|`None`): Le nombre maximal de joueurs (`None` pour illimité). Optionnel. Valeur par défaut: `None`.
    - `max_observers` (int\|`None`): Le nombre maximal d'observateurs (`None` pour illimité). Optionnel. Valeur par défaut: `None`.
    - `turn_based` (bool): `True` si la partie se joue au tour par tour. Optionnel. Valeur par défaut: `False`.
    - `password` (str\|`None`): Le mot de passe pour rejoindre la partie (`None` pour une partie publique). Optionnel. Valeur par défaut: `None`.
    - `group_id` (str\|`None`): L'ID du groupe dans lequel créer la partie. Optionnel. Valeur par défaut: `None`.
    - `group_password` (str\|`None`): Le mot de passe du groupe, si nécessaire. Optionnel. Valeur par défaut: `None`.
    - `factory_template_id` (str\|`None`): L'ID du modèle de factory de joueurs à appliquer à la partie (`None` pour une partie sans factory). Nécessite la fonctionnalité `player_factory` du protocole : si ce paramètre est fourni et que la fonctionnalité ne figure pas dans l'attribut `server_features`, l'exception `UnsupportedFeatureError` est levée et la requête n'est pas envoyée. Optionnel. Valeur par défaut: `None`.
    - `attributes` (dict\|`None`): Les attributs personnalisés de la partie. Optionnel. Valeur par défaut: `None`.
  - Précision d'implémentation: les paramètres valant `None` ne sont pas transmis dans la requête, à l'exception de `max_players` et `max_observers`, transmis explicitement à `null` pour signifier l'absence de limite.
  - Valeur de retour: L'ID de la partie créée.
  - Exceptions émises:
    - `UnsupportedFeatureError`: si `factory_template_id` est fourni et que le serveur ne propose pas la fonctionnalité `player_factory` (la requête n'est alors pas envoyée).
    - `MultiplayerError` (ou une sous-classe): si le serveur refuse la création, par exemple si le modèle indiqué n'existe pas (code `FACTORY_TEMPLATE_NOT_FOUND`).
    - `ConnectionError`: si le client n'est pas connecté.
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
- `save_persistence`: Demande une sauvegarde de persistance immédiate au serveur.
  - Description: Envoie une requête `SERVER_PERSISTENCE_SAVE` au serveur pour déclencher une sauvegarde immédiate. Requiert le niveau d'accès administrateur `ADMIN` du protocole, c'est-à-dire un compte utilisateur de rôle `UserRole.SERVER_ADMIN`.
  - Paramètres: Aucun.
  - Valeur de retour: Un dictionnaire contenant les données de la réponse du serveur.
  - Exceptions émises:
    - `MultiplayerError` (ou une sous-classe): si le serveur retourne une erreur.
    - `ConnectionError`: si le client n'est pas connecté.

Les méthodes suivantes facilitent l'utilisation des modèles de factory et des factories de joueurs des parties. Chacune envoie la requête correspondante du protocole et retourne un dictionnaire contenant les données de la réponse du serveur (champ `payload`). Elles nécessitent toutes la fonctionnalité `player_factory` du protocole (révision 2.1) : avant d'envoyer la requête, chacune vérifie que cette fonctionnalité figure dans l'attribut `server_features`. Toutes peuvent lever les exceptions suivantes:
- `UnsupportedFeatureError`: si le serveur ne propose pas la fonctionnalité `player_factory` (la requête n'est alors pas envoyée) ;
- `MultiplayerError` (ou une sous-classe): si le serveur retourne une erreur ;
- `ConnectionError`: si le client n'est pas connecté.

- `list_factory_templates`: Récupère la liste des modèles de factory disponibles sur le serveur.
  - Description: Envoie une requête `FACTORY_TEMPLATE_LIST`. Permet notamment de proposer à l'utilisateur le choix d'un modèle lors de la création d'une partie.
  - Paramètres: Aucun.
- `get_factory_template`: Récupère la définition complète d'un modèle de factory.
  - Description: Envoie une requête `FACTORY_TEMPLATE_GET`.
  - Paramètres:
    - `template_id` (str): L'ID du modèle. Obligatoire.
- `create_factory_template`: Crée un modèle de factory sur le serveur.
  - Description: Envoie une requête `FACTORY_TEMPLATE_CREATE`. Requiert le niveau d'accès `ADMIN` du protocole.
  - Paramètres:
    - `name` (str): Le nom du modèle. Obligatoire.
    - `options` (list[dict]): La liste des options du modèle, chacune décrite par un dictionnaire au format défini par la requête `FACTORY_TEMPLATE_CREATE` (`type`, `name`, `description`, `default`, `min`, `max`, `step`, `choices`, `unicity`, `target`, `attribute`). Obligatoire.
- `update_factory_template`: Modifie un modèle de factory existant.
  - Description: Envoie une requête `FACTORY_TEMPLATE_UPDATE`. Requiert le niveau d'accès `ADMIN` du protocole.
  - Paramètres:
    - `template_id` (str): L'ID du modèle à modifier. Obligatoire.
    - `name` (str\|`None`): Le nouveau nom du modèle. Optionnel. Valeur par défaut: `None` (nom inchangé).
    - `options` (list[dict]\|`None`): La nouvelle liste complète des options. Optionnel. Valeur par défaut: `None` (options inchangées).
  - Exceptions émises (en plus de celles listées ci-dessus):
    - `ValueError`: si `name` et `options` valent tous deux `None` (la requête n'est alors pas envoyée).
- `delete_factory_template`: Supprime un modèle de factory du serveur.
  - Description: Envoie une requête `FACTORY_TEMPLATE_DELETE`. Requiert le niveau d'accès `ADMIN` du protocole.
  - Paramètres:
    - `template_id` (str): L'ID du modèle à supprimer. Obligatoire.
- `get_game_factory`: Récupère la factory de joueurs d'une partie, pour construire le formulaire de création d'un joueur.
  - Description: Envoie une requête `GAME_FACTORY_GET`. La réponse fournit, pour chaque option, les valeurs déjà prises (`exclusions`) et la valeur proposée (`proposed_value`). Une consultation réussie abonne la session à la notification `GAME_FACTORY_UPDATED` de la partie, qu'il est possible de traiter avec la méthode `on_notification`.
  - Paramètres:
    - `game_id` (str): L'ID de la partie. Obligatoire.
    - `password` (str\|`None`): Le mot de passe de la partie, si elle est privée. Optionnel. Valeur par défaut: `None`.
    - `group_password` (str\|`None`): Le mot de passe d'un groupe protégé contenant la partie, si nécessaire. Optionnel. Valeur par défaut: `None`.
- `join_game_with_factory`: Crée un joueur à partir de la factory d'une partie et le fait rejoindre la partie en une seule opération.
  - Description: Envoie une requête `GAME_FACTORY_JOIN`. Il est recommandé de transmettre explicitement dans `values` les valeurs présentées à l'utilisateur, y compris les valeurs proposées qu'il n'a pas modifiées.
  - Paramètres:
    - `game_id` (str): L'ID de la partie. Obligatoire.
    - `values` (dict[str, any]\|`None`): Les valeurs choisies, indexées par l'ID des options de la factory. Optionnel. Valeur par défaut: `None` (toutes les options prennent leur valeur proposée).
    - `password` (str\|`None`): Le mot de passe de la partie, si elle est privée. Optionnel. Valeur par défaut: `None`.
    - `group_password` (str\|`None`): Le mot de passe d'un groupe protégé contenant la partie, si nécessaire. Optionnel. Valeur par défaut: `None`.
    - `is_default` (bool\|`None`): Si `True`, le joueur créé devient le joueur par défaut de la session. Si `None`, le champ n'est pas transmis et la règle du serveur s'applique (le joueur devient le joueur par défaut s'il s'agit du premier joueur de la session). Optionnel. Valeur par défaut: `None`.

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
  - Peut utiliser l'option `--fix` pour corriger automatiquement les erreurs de style et de conformité.

- `local_game.py`: lance une démonstration locale visible d'une partie multijoueur:
  - Ouvre une fenêtre de console pour le serveur local et une fenêtre pour chaque joueur.
  - Accepte en argument le nombre de joueurs; la valeur par défaut est `2`.
  - Chaque joueur se connecte au serveur, rejoint la même partie et simule plusieurs échanges et tours à une vitesse lisible par un humain.
  - Termine la partie normalement, puis arrête proprement le serveur.
  - Utilisation:
    - `uv run python scripts/local_game.py`: lance une partie avec deux joueurs.
    - `uv run python scripts/local_game.py 4`: lance une partie avec quatre joueurs.
