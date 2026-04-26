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

### Environnement de Test Complet

Un script est disponible pour lancer un environnement de test complet avec :
- Un serveur de log IPC (`IPClogging`) dans une fenêtre séparée.
- Un serveur de jeu.
- Plusieurs instances de clients séparées (2 par défaut) simulant une partie, chacune dans sa propre fenêtre de terminal.

Pour le lancer :
```bash
uv run python scripts/full_test_env.py
```

Pour spécifier le nombre de joueurs :
```bash
uv run python scripts/full_test_env.py --players 3
```
Cela ouvrira plusieurs fenêtres Windows Terminal : une pour le serveur de log et une pour chaque instance de client, vous permettant de voir les interactions et les logs en temps réel.

### Utilisation Locale

Vous pouvez utiliser la classe `Game` directement, y compris avec un mot de passe pour la validation locale.

```python
from multiplayer import Game, Player, suggest_game_name

game = Game(name="Ma Super Partie", password="local_game_pass")
game.add_player(Player("Alice"), password="local_game_pass")
game.start()
```

### Utilisation en Réseau (Client-Serveur)

#### Configuration du Serveur
```python
from multiplayer import GameServer

# Démarrer un serveur sécurisé avec un domaine personnalisé et un certificat auto-signé
server = GameServer(
    host='0.0.0.0',
    port=12345,
    password="mon_mot_de_passe_serveur",
    admin_password="mon_mot_de_passe_admin",
    use_tls=True,
    tls_domain="exemple.com",
    tls_self_signed=True
)
server.start()

# Ou utiliser des fichiers de certificat existants
server = GameServer(
    use_tls=True,
    tls_cert="chemin/vers/cert.pem",
    tls_key="chemin/vers/key.pem",
    tls_self_signed=False
)
```

#### Utilisation Administrateur
```python
from multiplayer import GameAdmin

# Se connecter en tant qu'administrateur
admin = GameAdmin(
    host='localhost',
    port=12345,
    admin_password="mon_mot_de_passe_admin",
    use_tls=True
)

# Gérer le serveur
info = admin.get_server_info()
print(f"Parties actives : {info['games_count']}")

# Vérifier l'expiration du certificat
expiration = admin.get_cert_expiration()
print(f"Le certificat expire le : {expiration}")

# Expulser un joueur si nécessaire
# admin.kick_player(game_id, "nom_du_joueur")

# Arrêter le serveur à distance
# admin.stop_server()
```

#### Utilisation Client
```python
from multiplayer import GameClient, Player, suggest_game_name

# 1. Découvrir et se connecter au serveur
servers = GameClient.discover_servers()
if not servers:
    print("Aucun serveur trouvé.")
else:
    host, port = servers[0]
    client = GameClient(
        host=host,
        port=port,
        password="mon_mot_de_passe_serveur",
        use_tls=True
    )

    # 2. Créer une partie privée
    private_game = client.create_game(
        name=suggest_game_name(),
        password="mon_mot_de_passe_partie"
    )

    # 3. Un joueur rejoint et définit l'état initial
    private_game.add_player(Player("Charlie"), password="mon_mot_de_passe_partie")
    private_game.set_state({"score": 0})
    private_game.start()
```

## Gestion des Erreurs

Le module fournit un ensemble d'exceptions personnalisées, incluant `AuthenticationError` pour les mots de passe du serveur et des parties.

```python
from multiplayer import GameClient
from multiplayer.exceptions import ConnectionError, AuthenticationError

try:
    # ... connexion au client ...

    # Essayer de rejoindre une partie avec le mauvais mot de passe
    game.add_player(Player("Eve"), password="mauvais_mot_de_passe")

except AuthenticationError as e:
    print(f"L'authentification a échoué comme prévu : {e}")
except ConnectionError as e:
    print(f"Une erreur de connexion ou de découverte s'est produite : {e}")
```

## Contribution

Les contributions sont les bienvenues ! Veuillez consulter nos [Directives de contribution](CONTRIBUTING.md) pour plus de détails sur la façon de commencer.

## Exécution des Tests

Pour exécuter les tests unitaires, vous devrez avoir `pytest` installé.

```sh
pip install pytest
```

Ensuite, vous pouvez lancer les tests depuis la racine du projet :

```sh
pytest
```
