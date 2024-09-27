# Projet de Détection de Spam avec API Flask et Dashboard de Monitoring

Ce projet est une API Flask de détection de spam qui utilise un modèle pré-entraîné avec `transformers`. Il inclut une interface Swagger pour interagir avec l'API et un dashboard de monitoring en temps réel avec `Dash`.

## Prérequis

- **Docker** et **Docker Compose** doivent être installés sur votre machine.

## Installation et Lancement

1. Clonez ce dépôt sur votre machine locale.

   ```bash
   git clone https://github.com/Lugdum/MLOps.git
   cd MLOps
   ```

2. Construisez et démarrez les services avec Docker Compose :

   ```bash
   sudo docker-compose up --build
   ```

   Cela démarrera à la fois l'API Flask et le dashboard Dash.

3. Pour arrêter et supprimer les volumes créés :

   ```bash
   sudo docker-compose down --volumes
   ```

## Utilisation

### Accéder à l'API via Swagger UI

- Sur le PC où l'API est lancée, rendez-vous sur l'URL suivante pour accéder à l'interface Swagger et tester les routes de l'API :

   ```
   http://localhost:8000/apidocs/#/
   ```

- Depuis un autre PC sur le même réseau local, remplacez `localhost` par l'adresse IP du PC hébergeant l'API (ex : `192.168.x.x`).

### Accéder au Dashboard de Monitoring

- Sur le PC où l'API est lancée, rendez-vous sur l'URL suivante pour voir le monitoring en temps réel des requêtes à l'API :

   ```
   http://localhost:8000/dash/
   ```

- Depuis un autre PC sur le même réseau local, remplacez `localhost` par l'adresse IP du PC hébergeant l'API (ex : `192.168.x.x`).
