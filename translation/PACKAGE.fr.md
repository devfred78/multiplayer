[English](../PACKAGE.md) | [Español](PACKAGE.es.md) | **Français**

# Documentation du Conteneur Multiplayer

Ce guide décrit comment installer, configurer et gérer le conteneur Docker `multiplayer-server`.

## Installation

### Docker Standard
Récupérez l'image depuis le GitHub Container Registry :
```bash
docker pull ghcr.io/devfred78/multiplayer-server:latest
```

### NAS Synology
1. Ouvrez **Docker** (DSM 7.1) ou **Container Manager** (DSM 7.2+).
2. Allez dans **Registre**, recherchez `ghcr.io/devfred78/multiplayer-server-synology`.
3. Téléchargez le tag `latest` ou une version spécifique.

## Configuration

### Arguments de Ligne de Commande
Le serveur accepte les arguments suivants :
- `--host` : Adresse de l'hôte (par défaut : `0.0.0.0`).
- `--port` : Port d'écoute (par défaut : `65432`).
- `--name` : Nom de l'instance du serveur.
- `--password` : Mot de passe global du serveur.
- `--admin-password` : Mot de passe d'administration.
- `--use-tls` : Active le TLS v1.3.
- `--tls-cert-dir` : Répertoire contenant les certificats (mappé sur `/app/certs`).
- `--logging-host` / `--logging-port` : Détails du serveur de logs centralisé.

### Certificats TLS
Pour utiliser vos propres certificats :
1. Créez un répertoire (ex: `./certs`) et placez-y `cert.pem` et `privkey.pem`.
2. Mappez ce répertoire sur `/app/certs` dans le conteneur.
3. Utilisez `--use-tls --tls-cert-dir /app/certs --no-self-signed`.

## Exécution et Gestion

### Lancer le Conteneur
```bash
docker run -d \
  --name multiplayer-server \
  -p 65432:65432 \
  -v /chemin/vers/certs:/app/certs \
  ghcr.io/devfred78/multiplayer-server:latest \
  --port 65432 --use-tls --tls-cert-dir /app/certs
```

### Arrêt et Démarrage
- **Arrêt** : `docker stop multiplayer-server`
- **Démarrage** : `docker start multiplayer-server`
- **Redémarrage** : `docker restart multiplayer-server`

### Interagir avec le Conteneur
- **Logs** : `docker logs -f multiplayer-server`
- **Shell** : `docker exec -it multiplayer-server /bin/sh`

## Spécificités Synology

### DSM 7.1 (Docker)
- **Réseau** : Utilisez le mode `bridge` et mappez le port `65432`.
- **Volume** : Mappez votre dossier de certificats local vers `/app/certs` dans l'onglet **Paramètres du volume**.
- **Environnement** : Les arguments sont passés via le champ **Commande d'exécution** dans les **Paramètres avancés**.

### DSM 7.2 & 7.3 (Container Manager)
- **Projet** : Vous pouvez utiliser un fichier `docker-compose.yml` pour une gestion facilitée.
- **Capacité** : Assurez-vous que le conteneur n'a pas de capacités restreintes bloquées si vous utilisez des ports personnalisés inférieurs à 1024 (non applicable pour le port 65432 par défaut).
- **Web Station** : Si vous souhaitez utiliser un domaine personnalisé avec un Reverse Proxy, configurez-le dans **Web Station** pour pointer vers le port du conteneur.

---
*Pour les détails de l'API, voir [REFERENCE.md](https://github.com/devfred78/multiplayer/blob/main/REFERENCE.md).*
