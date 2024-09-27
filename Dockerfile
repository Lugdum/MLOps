# Utiliser une image Python légère
FROM python:3.9-slim

# Installer les dépendances du système
RUN apt-get update && apt-get install -y gcc libpq-dev

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier le fichier requirements.txt dans le conteneur
COPY requirements.txt /app/

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le contenu du projet dans le conteneur
COPY . /app

# Exposer les ports pour Flask (8000) et Dash (8050)
EXPOSE 8000
EXPOSE 8050

# Commande pour démarrer les deux serveurs dans le sous-répertoire src/api
CMD ["sh", "-c", "python src/api/app.py & python src/api/monitoring.py"]
