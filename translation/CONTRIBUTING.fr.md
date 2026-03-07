[English](../CONTRIBUTING.md) | [Español](CONTRIBUTING.es.md) | **Français**

# Comment Contribuer à Multiplayer

Nous sommes ravis que vous souhaitiez contribuer au projet `multiplayer` ! Votre aide est très appréciée. En contribuant, vous pouvez aider à rendre cette bibliothèque encore meilleure.

Veuillez noter que ce projet est publié avec un [Code de Conduite du Contributeur](CODE_OF_CONDUCT.fr.md). En participant à ce projet, vous acceptez de respecter ses termes.

## Table des Matières
* [Signaler des Bugs](#signaler-des-bugs)
* [Suggérer des Améliorations](#suggérer-des-améliorations)
* [Votre Première Contribution de Code](#votre-première-contribution-de-code)
* [Processus de Pull Request](#processus-de-pull-request)

## Signaler des Bugs

Si vous trouvez un bug, veuillez vous assurer qu'il n'a pas déjà été signalé en cherchant sur GitHub dans la section [Issues](https://github.com/devfred78/multiplayer/issues).

Si vous ne trouvez pas d'issue ouverte traitant du problème, [ouvrez-en une nouvelle](https://github.com/devfred78/multiplayer/issues/new). Assurez-vous d'inclure un **titre et une description clairs**, autant d'informations pertinentes que possible, et un **exemple de code** ou un **cas de test exécutable** démontrant le comportement attendu qui ne se produit pas.

## Suggérer des Améliorations

Si vous avez une idée pour une nouvelle fonctionnalité ou une amélioration d'une fonctionnalité existante, veuillez ouvrir un issue pour en discuter. Cela nous permet de coordonner nos efforts et d'éviter le travail en double.

1.  Recherchez dans les [issues](https://github.com/devfred78/multiplayer/issues) pour voir si l'amélioration a déjà été suggérée.
2.  Sinon, [ouvrez un nouvel issue](https://github.com/devfred78/multiplayer/issues/new), en fournissant une description claire et détaillée de l'amélioration proposée et de ses avantages.

## Votre Première Contribution de Code

Prêt à contribuer du code ? Voici comment configurer `multiplayer` pour le développement local.

1.  **Faites un fork du dépôt** sur GitHub.
2.  **Clonez votre fork** localement :
    ```sh
    git clone https://github.com/votre-utilisateur/multiplayer.git
    ```
3.  **Configurez votre environnement.** Nous recommandons d'utiliser un environnement virtuel :
    ```sh
    cd multiplayer
    python -m venv .venv
    source .venv/bin/activate  # Sur Windows, utilisez `.venv\Scripts\activate`
    ```
4.  **Installez les dépendances**, y compris les outils de développement et de test :
    ```sh
    pip install -e .[dev]
    ```
5.  **Créez une nouvelle branche** pour vos modifications :
    ```sh
    git checkout -b nom-de-votre-fonctionnalite-ou-correctif
    ```
6.  Faites vos modifications !

## Processus de Pull Request

1.  Assurez-vous que votre code respecte le style existant pour maintenir la cohérence.
2.  Exécutez les tests pour vous assurer que vos modifications ne cassent rien :
    ```sh
    pytest
    ```
3.  Ajoutez de nouveaux tests pour votre fonctionnalité si applicable.
4.  Mettez à jour la documentation (`README.md`, `REFERENCE.md`, etc.) si vous avez modifié l'API ou ajouté de nouvelles fonctionnalités.
5.  Validez vos modifications avec un message de commit clair et descriptif.
6.  Poussez votre branche vers votre fork sur GitHub :
    ```sh
    git push origin nom-de-votre-fonctionnalite-ou-correctif
    ```
7.  **Soumettez un Pull Request** vers la branche `main` du dépôt original de `multiplayer`. Fournissez un titre et une description clairs pour votre PR, en expliquant le "quoi" et le "pourquoi" de vos modifications.

Merci pour votre contribution !
