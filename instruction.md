# Instructions pour le développement de la version 2 de multiplayer

Ce document fournit les instructions pour le développement de la version 2 du module de multiplayer. Il décrit les conventions de codage, les dépendances et les spécifications techniques nécessaires pour assurer la compatibilité et la cohérence entre les différents modules du package.

## Règles générales

# Conventions sur les commentaires et les docstrings

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

- Toutes les propriétés de type "ID" (identifiants) doivent être des chaînes de caractères alphanumériques et doivent être générées de manière unique à l'instantiation, en utilisant la fonction uuid.uuid4() du module uuid. Elles doivent être en lecture seule.
- Tous les objets codés doivent faire l'objet d'un ensemble de tests unitaires pour garantir leur bon fonctionnement. Ces tests doivent couvrir tous les cas possibles d'utilisation des objets et doivent être automatisés. Ils doivent pouvoir être lancés avec `pytest`.
- Le fichier `pyproject.toml` doit être conforme à la spécification du format TOML et aux instructions décrites [ici](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) et doit contenir les informations nécessaires pour la gestion du projet avec `uv`.
- Les fichiers de documentation doivent être écrits en Markdown et doivent être mis à jour régulièrement avec les modifications apportées au code.

## Organisation du code

De manière générale, les fichiers de code doivent être structurés de manière à faciliter la compréhension et la maintenance du code. Les fichiers doivent être divisés en sections logiques et chaque section doit être bien documentée.

Ce chapitre est organisé en sous-chapitres, chacun portant le nom d'un fichier source à implémenter en tant que module du package de multiplayer.

Sauf exception spécifiquement indiquée, les objets à implémenter (fonctions, classes, etc.) sont décrits selon l'effet attendu du point de vue de l'utilisateur de cet objet. Le développeur est libre d'ajouter tous les objets ou fichiers intermédiaires qu'il estime nécessaire pour réaliser cet effet final.

Les fichiers sont organisés selon le format d'un projet Python géré par `uv`, qui reprend la structure de projet standard Python (avec le fichier `pyproject.toml`), en y ajoutant quelques spécificités (telles que le fichier `uv.lock`).

Ainsi, les fichiers sources sont dans le répertoire `src/multiplayer`, les tests unitaires dans `tests/`, les fichiers de distribution dans `dist/`, et quelques scripts de tests plus complexes dans `scripts/`. `pyproject.toml`, `uv.lock`, `README.md`, ainsi que tous les autres fichiers de documentation et de configuration sont, eux, à la racine du projet.

### Contenu du fichier __init__.py

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

### Contenu du fichier exceptions.py

Ce fichier contient les définitions des exceptions personnalisées utilisées dans ce module. Il définit les classes et les fonctions nécessaires pour la gestion des erreurs spécifiques au jeu.
On y trouve en particulier les classes suivantes:

#### Classe `MultiplayerError`
Cette classe est la classe de base pour toutes les exceptions liées au module `multiplayer`. Elle sert de point de départ pour la hiérarchie des exceptions personnalisées.

#### Classe `UserAlreadyExistsError`
Cette classe est dérivée de `MultiplayerError` et est utilisée pour signaler une tentative de création d'un compte utilisateur avec un nom déjà existant.

#### Classe `GroupNotFoundError`
Cette classe est dérivée de `MultiplayerError` et est utilisée pour signaler une tentative de l'ID d'un groupe qui n'existe pas. Cette exception retourne dans son message l'ID du groupe qui n'a pas été trouvé.

### Contenu du fichier game.py

Ce fichier contient la logique principale de gestion des parties. Il définit les classes et les fonctions nécessaires pour la création, la gestion et la résolution des parties.
On y trouve en particulier les classes suivantes:

#### Classe `Player`
Cette classe représente un joueur dans le contexte du jeu. Elle s'instantie avec les paramètres suivants:

| Nom | Type     | Description | Obligatoire | Valeur par défaut |
| --- |----------|--------| --- | --- |
| `name` | str      | Le nom du joueur. | Oui | - |
| `**kwargs` | variable | Paramètres optionnels pour personnaliser le joueur. Chaque paramètre doit se présenter sous la forme d'un tuple `(famille, valeur_initiale)` dont `famille` est un objet `ParameterFamily` qui spécifie le caractère statique ou dynamique du paramètre, et `valeur_initiale` sa valeur initiale. Le choix de la famille se fait à la convenance de l'utilisateur, pour l'aider à classer les informations, mais n'a aucun impact sur le traitement interne (les familles sont toutes traitées de la même manière). | Non | - |

Elle présente les attributs suivants:

| Nom | Type | Description | Modifiable | Précision d'implémentation                                                                                                                                                                                                                                                                                                                                                                                         |
| --- |------|-------------|------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `ID` | str | L'identifiant unique du joueur.  | Non | S'initialise automatiquement avec la valeur de `uuid.uuid4()`.                                                                                                                                                                                                                                                                                                                                                     |
| `name` | str | Le nom du joueur.  | Oui | S'initialise automatiquement avec le nom fourni lors de la création du joueur.                                                                                                                                                                                                                                                                                                                                     |
| `static_state` | dict | Attributs personnalisés du joueur, dont la vocation est de stocker des informations qui ne changent pas ou peu pendant la partie. | Oui  | S'initialise automatiquement avec les paramètres spécifiés comme appartenant à la famille `ParameterFamily.STATIC`, mais peut être complété par la suite par tout autre paramètre au choix de l'utilisateur. Par exemple, si `Player` est instantié avec `Player(name="Mon nom", color=(ParameterFamily.STATIC, "white"), score=(ParameterFamily.DYNAMIC, 0))`, alors `static_state`est égal à `{"color":"white"}`. |
| `dynamic_state` | dict | Attributs personnalisés du joueur, dont la vocation est de stocker des informations qui peuvent être modifiées souvent pendant la partie. | Oui  | S'initialise automatiquement avec les paramètres spécifiés comme appartenant à la famille `ParameterFamily.DYNAMIC`, mais peut être complété par la suite par tout autre paramètre au choix de l'utilisateur. Par exemple, si `Player` est instantié avec `Player(name="Mon nom", color=(ParameterFamily.STATIC, "white"), score=(ParameterFamily.DYNAMIC, 0))`, alors `dynamic_state` est égal à `{"score":0}`.    |

#### Classe `User`
Cette classe représente un compte utilisateur. Celui-ci permet de conserver un profil de joueur et d'accéder à des informations ou des actions selon le niveau de droit dont il dispose, et auquel il a accès via une capacité d'authentification.
Elle s'instantie avec les paramètres suivants:

| Nom | Type         | Description                                                                                                   | Obligatoire | Valeur par défaut |
| --- |--------------|---------------------------------------------------------------------------------------------------------------| --- | --- |
| `username` | str          | Le nom d'utilisateur du compte.                                                                               | Oui | - |
| `password` | str          | Le mot de passe du compte.                                                                                    | Oui | - |
| `email` | str          | L'adresse e-mail du compte.                                                                                   | Non | - |


Si un objet `User` est instantié avec un `username` déjà utilisé dans une instance existante de `User`, une exception `UserAlreadyExistsError` est levée et l'instantiation échoue.

Elle présente les attributs suivants:

| Nom        | Type         | Description                                                                                                                                                                                                                                                                                            | Modifiable         | Précision d'implémentation                                                                                                                                                                                                         |
|------------|--------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `ID`       | str          | L'identifiant unique du compte utilisateur.                                                                                                                                                                                                                                                            | Non                | S'initialise automatiquement avec la valeur de `uuid.uuid4()`.                                                                                                                                                                     |
| `username` | str          | Le nom d'utilisateur du compte.                                                                                                                                                                                                                                                                        | Non                | -                                                                                                                                                                                                                                  |
| `hash`     | str          | Le hash du mot de passe du compte.                                                                                                                                                                                                                                                                     | Non                | Le hash est automatiquement généré à partir de `password` avec `bcrypt`.                                                                                                                                                           |
| `email`    | str          | L'adresse e-mail du compte.                                                                                                                                                                                                                                                                            | Oui                | -                                                                                                                                                                                                                                  |
| `role`     | `PlayerRole` | Le rôle du compte (ie: son niveau de permission).                                                                                                                                                                                                                                                      | Oui                | -                                                                                                                                                                                                                                  |
| `groups_id` | List[str]    | Les identifiants des groupes pour lesquels le compte est administrateur. Uniquement utile si `role == PlayerRole.GROUP_ADMIN`. Une exception `GroupNotFoundError` est levée si un des identifiants ne correspond pas à un groupe existant. Dans ce cas la valeur de `groups_id` n'est pas mise à jour. | Non (mais mutable) | Initialisé avec une liste vide, cet attribut peut être complété et modifié grace aux méthodes de `list` telles que `append`, `extend`, `pop`, ... Comme il s'agit d'un attribut en lecture seule, la ré-affectation est interdite. |
| `player`   | `Player`     | Le joueur associé au compte. | Non (mais mutable) | -                                                                                                                                                                                                                                  |