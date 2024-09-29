# Dockerfile pour l'API Flask et le Dash Monitoring
FROM python:3.9-slim

WORKDIR /app

ENV PYTHONPATH=/app/src

# Installer les dépendances
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copier les fichiers de l'application Flask et Dash
COPY . /app

# Exposer les ports pour Flask (8000) et Dash (8050)
EXPOSE 8000
EXPOSE 8050

# Créer le volume pour la base de données
VOLUME /app/metrics

# Lancer l'application (Flask et Dash sont dans le même app.py)
CMD ["python", "src/api/app.py"]
