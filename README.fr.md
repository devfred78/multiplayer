[English](README.md) | [Español](README.es.md) | **Français**

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
*   **État de Jeu Personnalisé :** Un dictionnaire flexible (`custom_state`) pour synchroniser n'importe quelle donnée spécifique au jeu.
*   **Sécurité à Plusieurs Niveaux :** Supporte les mots de passe pour le serveur global et par partie, avec un chiffrement TLS v1.3 optionnel.
*   **Découverte Automatique de Serveurs :** Les clients peuvent trouver automatiquement les serveurs en cours d'exécution sur le réseau local.
*   **Suggestions de Noms Extensibles :** Inclut une fonction utilitaire pour suggérer des noms créatifs pour les parties et les joueurs.
*   **Parties Multiples :** Le serveur peut gérer plusieurs sessions de jeu simultanément.
*   **Gestion Robuste des Erreurs :** Un ensemble clair d'exceptions personnalisées pour la logique de jeu et les problèmes réseau.

## Installation

Ce module nécessite la bibliothèque `cryptography` pour ses fonctionnalités de sécurité.

```sh
pip install multiplayer-0.1.0-py3-none-any.whl
```
*Remplacez `multiplayer-0.1.0-py3-none-any.whl` par le nom réel du fichier téléchargé.*

## Utilisation

### État de Jeu Personnalisé

Une fonctionnalité clé est la capacité de gérer votre propre état de jeu. Le `custom_state` est un simple dictionnaire que vous pouvez lire et écrire, parfait pour les scores, les positions ou toute autre donnée.

```python
# Sur un client
partie.set_state({
    "plateau": [["X", "O", ""], ["", "X", ""], ["O", "", ""]],
    "tour": "joueur2"
})

# Sur un autre client
etat_actuel = partie.state
print(etat_actuel["tour"])
# > "joueur2"
```

### Utilisation Locale

Vous pouvez utiliser la classe `Game` directement, y compris avec un mot de passe pour la validation locale.

```python
from multiplayer import Game, Player, suggest_game_name

partie = Game(password="mot_de_passe_local")
partie.add_player(Player("Alice"), password="mot_de_passe_local")
partie.start()
```

### Utilisation en Réseau (Client-Serveur)

#### Configuration du Serveur
```python
from multiplayer import GameServer

# Démarrer un serveur sécurisé
serveur = GameServer(
    host='0.0.0.0',
    port=12345,
    password="mon_mot_de_passe_serveur",
    use_tls=True
)
serveur.start()
```

#### Utilisation du Client
```python
from multiplayer import GameClient, Player, suggest_game_name

# 1. Découvrir et se connecter au serveur
serveurs = GameClient.discover_servers()
if not serveurs:
    print("Aucun serveur trouvé.")
else:
    host, port = serveurs[0]
    client = GameClient(
        host=host,
        port=port,
        password="mon_mot_de_passe_serveur",
        use_tls=True
    )

    # 2. Créer une partie privée
    partie_privee = client.create_game(
        name=suggest_game_name(),
        password="mon_mot_de_passe_partie"
    )

    # 3. Un joueur rejoint et définit l'état initial
    partie_privee.add_player(Player("Charlie"), password="mon_mot_de_passe_partie")
    partie_privee.set_state({"score": 0})
    partie_privee.start()
```

## Gestion des Erreurs

Le module fournit un ensemble d'exceptions personnalisées, y compris `AuthenticationError` pour les mots de passe du serveur et des parties.

```python
from multiplayer import GameClient
from multiplayer.exceptions import ConnectionError, AuthenticationError

try:
    # ... connexion au client ...

    # Essayer de rejoindre une partie avec le mauvais mot de passe
    partie.add_player(Player("Eve"), password="mauvais_mot_de_passe")

except AuthenticationError as e:
    print(f"L'authentification a échoué comme prévu : {e}")
except ConnectionError as e:
    print(f"Une erreur de connexion ou de découverte est survenue : {e}")
```

## Contribuer

Nous accueillons les contributions ! Veuillez consulter nos [Directives de Contribution](CONTRIBUTING.fr.md) pour plus de détails.

## Lancer les Tests

Pour lancer les tests unitaires, vous devez avoir `pytest` d'installé.

```sh
pip install pytest
```

Ensuite, vous pouvez lancer les tests depuis la racine du projet :

```sh
pytest
```

## Licence

Ce projet est sous licence MIT - voir le fichier [LICENSE.md](LICENSE.md) pour plus de détails.
