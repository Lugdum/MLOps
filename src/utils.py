import requests
from requests.auth import HTTPBasicAuth

# Simuler une base de données d'utilisateurs avec des rôles
users = {
    "admin": {"password": "adminpass", "role": "admin"},
    "user": {"password": "userpass", "role": "user"},
    "normal": {"password": "normalpass", "role": "normal"}
}

# Définir les rôles et leur accès
roles_permissions = {
    "admin": ["predict", "logs", "metrics"],
    "user": ["predict"],
    "normal": []
}

# Initialiser les métriques
total_request_count = 0
request_count_in_interval = 0
error_count = 0

jwt_token = None

# Fonction pour obtenir un token JWT
def get_jwt_token():
    login_url = "http://localhost:8000/login"
    
    # Envoie les identifiants dans l'en-tête Basic Auth
    response = requests.post(login_url, auth=HTTPBasicAuth('admin', 'adminpass'))
    
    if response.status_code == 200:
        token = response.json().get('access_token')
        if token:
            return token
        else:
            print("Aucun token reçu.")
    else:
        print(f"Erreur lors de l'obtention du token JWT: {response.status_code}")
        return None

# Fonction pour obtenir les métriques via l'API Flask
def get_metrics():
    global jwt_token

    if jwt_token is None:
        jwt_token = get_jwt_token()

    metrics_url = "http://localhost:8000/metrics"
    headers = {"Authorization": f"Bearer {jwt_token}"}

    response = requests.get(metrics_url, headers=headers)

    # Si la requête échoue à cause d'un token invalide, on essaie de régénérer le token
    if response.status_code == 401:
        print("Token expiré ou invalide, régénération du token...")
        jwt_token = get_jwt_token()
        headers = {"Authorization": f"Bearer {jwt_token}"}
        response = requests.get(metrics_url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erreur lors de la récupération des métriques: {response.status_code}")
        return None