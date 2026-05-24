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

## Organisation du code

De manière générale, les fichiers de code doivent être structurés de manière à faciliter la compréhension et la maintenance du code. Les fichiers doivent être divisés en sections logiques et chaque section doit être bien documentée.

Ce chapitre est organisé en sous-chapitres, chacun portant le nom d'un fichier source à implémenter en tant que module du package de multiplayer.

Sauf exception spécifiquement indiquée, les objets à implémenter (fonctions, classes, etc.) sont décrits selon l'effet attendu du point de vue de l'utilisateur de cet objet. Le développeur est libre d'ajouter tous les objets ou fichiers intermédiaires qu'il estime nécessaire pour réaliser cet effet final.

Les fichiers sont organisés selon le format d'un projet Python géré par `uv`, qui reprend la structure de projet standard Python (avec le fichier `pyproject.toml`), en y ajoutant quelques spécificités (telles que le fichier `uv.lock`).

Ainsi, les fichiers sources sont dans le répertoire `src/multiplayer`, les tests unitaires dans `tests/`, les fichiers de distribution dans `dist/`, et quelques scripts de tests plus complexes dans `scripts/`. `pyproject.toml`, `uv.lock`, `README.md`, ainsi que tous les autres fichiers de documentation sont, eux, à la racine du projet.

## Contenu du fichier __init__.py

Ce fichier contient les imports nécessaires pour le fonctionnement du package de multiplayer. De manière générale, on y indique tous les éléments constants (constantes, énumérations) que les modules de multiplayer utilisent.
On y trouve en particulier les éléments suivants:

### `PlayerRole` (Enum)
Une énumération pour le rôle d'un compte de joueur.

*   `PlayerRole.PLAYER` : Un joueur standard qui peut rejoindre et participer à des parties.
*   `PlayerRole.GROUP_ADMIN` : Un joueur qui peut gérer les parties au sein des groupes qui lui sont assignés. Ce rôle inclut toutes les permissions d'un `PLAYER`.
*   `PlayerRole.SERVER_ADMIN` : Un joueur avec un accès administratif complet au serveur. Ce rôle englobe le rôle de `GROUP_ADMIN`, lui-même pouvant également jouer le rôle de `PLAYER`.

### `GameState` (Enum)
Une énumération représentant le statut actuel d'une partie.

*   `GameState.PENDING` : La partie a été créée mais n'a pas encore commencé. Cet état est dédié à l'attente des joueurs. Les joueurs peuvent rejoindre ou quitter la partie.
*   `GameState.PAUSING` : La partie est actuellement en pause. Cet état est utilisé lorsqu'une partie qui était en cours est temporairement suspendue.
*   `GameState.IN_PROGRESS` : La partie est actuellement active.
*   `GameState.FINISHED` : La partie est terminée. Plus aucun coup ne peut être joué et les résultats sont définitifs.

## Contenu du fichier game.py

Ce fichier contient la logique principale de gestion des parties. Il définit les classes et les fonctions nécessaires pour la création, la gestion et la résolution des parties.
On y trouve en particulier les classes suivantes:

### Classe Player:
Cette classe représente un joueur dans le contexte du jeu.

