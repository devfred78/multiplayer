[English](../README.md) | [Español](README.es.md) | **Français**

# Gestionnaire de Jeu Multijoueur

> **Une Note sur l'Origine de ce Projet**
>
> Ce projet est principalement le résultat d'une série d'expérimentations utilisant Gemini Code Assist pour la génération de code et la gestion des erreurs. Plutôt que de l'utiliser sur des exemples académiques, il m'a semblé plus intéressant de l'appliquer à un projet qui pourrait répondre à un besoin pratique réel.
>
> C'est donc la raison d'être de `multiplayer` : vous pouvez décortiquer le code pour voir comment Gemini (avec mes directives) l'a construit, ou vous pouvez ignorer tout cela et simplement utiliser cette bibliothèque pour vos propres besoins !

Ce module Python fournit un cadre simple et flexible pour gérer des parties multijoueurs, à la fois localement et sur un réseau.

Pour une description technique détaillée de toutes les classes et fonctions, consultez la [Référence de l'API](REFERENCE.fr.md).

## Fonctionnalités

*   **Local et Réseau :** Utilisez-le dans un seul processus ou dans une architecture client-serveur.
*   **État de Jeu Combiné :** Un système flexible pour synchroniser à la fois le statut de base du jeu (ex: `in_progress`) et des données de jeu personnalisées.
*   **Support des Observateurs :** Possibilité d'ajouter des observateurs qui peuvent voir l'état du jeu sans y participer en tant que joueurs.
*   **Rôle d'Administrateur :** Nouvelle classe `GameAdmin` pour gérer le serveur, expulser des joueurs/observateurs et surveiller l'état du serveur.
*   **Sécurité à Plusieurs Niveaux :** Supporte les mots de passe serveur, administrateur et par partie, avec un chiffrement TLS v1.3 optionnel.
*   **Découverte Automatique de Serveurs :** Les clients peuvent trouver automatiquement les serveurs en cours d'exécution sur le réseau local.
*   **Suggestions de Noms Extensibles :** Inclut une fonction utilitaire pour suggérer des noms créatifs pour les parties et les joueurs.
*   **Parties Multiples :** Le serveur peut gérer plusieurs sessions de jeu simultanément, et la liste des parties est maintenant filtrée pour cacher les parties terminées.
*   **Gestion Robuste des Erreurs :** Un ensemble clair d'exceptions personnalisées pour la logique de jeu et les problèmes réseau.

## Installation

Ce module nécessite la bibliothèque `cryptography` pour ses fonctionnalités de sécurité.

```sh
pip install multiplayer-0.1.0-py3-none-any.whl
```
*Remplacez `multiplayer-0.1.0-py3-none-any.whl` par le nom réel du fichier téléchargé.*

## Utilisation

### Gestion de l'État de Jeu

Une fonctionnalité clé est la capacité de gérer votre propre état de jeu en parallèle du statut de base.

```python
# Sur un client, définissez un état personnalisé
partie.set_state({
    "plateau": [["X", "O", ""], ["", "X", ""], ["O", "", ""]],
    "tour": "joueur2"
})

# Sur un autre client, récupérez l'état combiné
etat_complet = partie.state
print(f"Statut de la partie : {etat_complet['status']}")
# > Statut de la partie : in_progress

print(f"Tour actuel : {etat_complet['custom']['tour']}")
# > Tour actuel : joueur2
```

### Utilisation Locale

Vous pouvez utiliser la classe `Game` directement, y compris avec un mot de passe pour la validation locale.

```python
from multiplayer import Game, Player, suggest_game_name

game = Game(name="Ma Super Partie", password="local_game_pass")
game.add_player(Player("Alice"), password="local_game_pass")
game.start()
```
