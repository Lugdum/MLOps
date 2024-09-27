import multiprocessing
from flask import Flask, request, jsonify, render_template, redirect, url_for
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from flasgger import Swagger
from flask_httpauth import HTTPBasicAuth
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, verify_jwt_in_request, set_access_cookies
import torch
import logging
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import requests
import time
from collections import deque

app = Flask(__name__)

# Configuration Swagger pour utiliser JWT Bearer Token
app.config['SWAGGER'] = {
    'title': 'Spam Detector API',
    'uiversion': 3,
    'securityDefinitions': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': 'JWT Authorization header using the Bearer scheme. Example: "Authorization: Bearer {token}"'
        }
    },
    'security': [{'Bearer': []}]
}

swagger = Swagger(app)

# Configurer JWT
app.config['JWT_SECRET_KEY'] = 'super-secret-key'
jwt = JWTManager(app)

# Configurer HTTPAuth
auth = HTTPBasicAuth()

# Charger le modèle et le tokenizer
tokenizer = AutoTokenizer.from_pretrained("mshenoda/roberta-spam")
model = AutoModelForSequenceClassification.from_pretrained("mshenoda/roberta-spam")
model.eval()

# Logger pour les requêtes utilisateur
user_logger = logging.getLogger('user_logger')
user_logger.setLevel(logging.INFO)
user_handler = logging.FileHandler('/app/logs/app.log')
user_formatter = logging.Formatter('%(asctime)s - %(message)s')
user_handler.setFormatter(user_formatter)
user_logger.addHandler(user_handler)

# Logger pour les requêtes de métriques
metrics_logger = logging.getLogger('metrics_logger')
metrics_logger.setLevel(logging.INFO)
metrics_handler = logging.FileHandler('/app/logs/metrics.log')
metrics_formatter = logging.Formatter('%(asctime)s - %(message)s')
metrics_handler.setFormatter(metrics_formatter)
metrics_logger.addHandler(metrics_handler)

# Initialiser les métriques
total_request_count = 0
request_count_in_interval = 0
error_count = 0

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

# Authentification basique avec rôle
@auth.verify_password
def verify_password(username, password):
    if username in users and users[username]['password'] == password:
        return username

@auth.get_user_roles
def get_user_roles(user):
    return [users[user]["role"]]

# Route pour générer un token JWT
@app.route('/login', methods=['POST'])
@auth.login_required
def login():
    """
    Générer un token JWT après authentification
    ---
    tags:
      - Authentification
    description: Utilisez cette route pour obtenir un token JWT en envoyant vos identifiants sous forme Basic Auth.
    responses:
      200:
        description: Un token JWT valide
        schema:
          type: object
          properties:
            access_token:
              type: string
              example: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
      401:
        description: Authentification échouée
    """
    username = auth.current_user()
    access_token = create_access_token(identity=username)
    return jsonify(access_token=access_token)

# Route pour prédire avec JWT
@app.route('/predict', methods=['POST'])
@jwt_required()
def predict():
    """
    Prédire si un texte est un spam ou non.
    ---
    tags:
      - Classification
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        description: Le texte à classifier sous forme d'objet JSON
        schema:
          type: object
          properties:
            text:
              type: string
              example: "Ceci est un message spam"
    responses:
      200:
        description: Le résultat de la prédiction
        schema:
          type: object
          properties:
            text:
              type: string
              example: "Ceci est un message spam"
            prediction:
              type: string
              example: "spam"
      400:
        description: Une erreur est survenue lors de la prédiction
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Une erreur est survenue"
      403:
        description: Accès refusé (pour un utilisateur sans permission)
    """
    global total_request_count, request_count_in_interval
    current_user = get_jwt_identity()
    user_role = users[current_user]["role"]
    
    if "predict" not in roles_permissions[user_role]:
        return jsonify({"error": "Access denied"}), 403
    
    try:
        # Mettre à jour les compteurs de requêtes
        total_request_count += 1
        request_count_in_interval += 1
        
        # Extraire le texte de la requête
        data = request.json
        text = data.get("text", "")
        
        # Prétraiter et faire une prédiction
        inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            prediction = torch.argmax(logits, dim=-1).item()

        # Loguer la requête et la réponse
        user_logger.info(f"Requête de {current_user}: {text}, Réponse: {'spam' if prediction == 1 else 'humain'}")
        
        return jsonify({"text": text, "prediction": "spam" if prediction == 1 else "humain"})
    
    except Exception as e:
        global error_count
        error_count += 1
        user_logger.error(f"Erreur pour la requête de {current_user}: {e}")
        return jsonify({"error": "Une erreur est survenue"}), 400

@app.route('/logs', methods=['GET'])
@jwt_required()
def get_logs():
    """
    Obtenir les logs du serveur (admin uniquement).
    ---
    tags:
      - Logs
    security:
      - Bearer: []
    responses:
      200:
        description: Les logs du serveur
        schema:
          type: object
          properties:
            logs:
              type: string
              example: "Requête de 192.168.1.1: Ceci est un spam, Réponse: spam"
      403:
        description: Accès refusé (si l'utilisateur n'a pas les permissions nécessaires)
      500:
        description: Erreur lors de la lecture des logs
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Erreur lors de la lecture du fichier de logs"
    """
    current_user = get_jwt_identity()
    user_role = users[current_user]["role"]
    
    if "logs" not in roles_permissions[user_role]:
        return jsonify({"error": "Access denied"}), 403
    
    try:
        with open('/app/logs/app.log', 'r') as log_file:
            logs = log_file.read()
        return jsonify({"logs": logs})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/clear_logs', methods=['DELETE'])
@jwt_required()
def clear_logs():
    """
    Effacer les logs du serveur (admin uniquement).
    ---
    tags:
      - Logs
    security:
      - Bearer: []
    responses:
      200:
        description: Les logs ont été effacés avec succès
      403:
        description: Accès refusé (si l'utilisateur n'a pas les permissions nécessaires)
      500:
        description: Erreur lors de l'effacement des logs
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Erreur lors de l'effacement des logs"
    """
    current_user = get_jwt_identity()
    user_role = users[current_user]["role"]

    if "logs" not in roles_permissions[user_role]:
        return jsonify({"error": "Access denied"}), 403

    try:
        # Vider le contenu du fichier de logs
        open('/app/logs/app.log', 'w').close()
        open('/app/logs/metrics.log', 'w').close()

        return jsonify({"message": "Les logs ont été effacés avec succès."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/metrics', methods=['GET'])
@jwt_required()
def metrics():
    """
    Obtenir les métriques de l'API (admin uniquement).
    ---
    tags:
      - Metrics
    security:
      - Bearer: []
    responses:
      200:
        description: Les métriques de l'API
        schema:
          type: object
          properties:
            total_request_count:
              type: integer
              example: 150
            request_count_in_interval:
              type: integer
              example: 10
            error_count:
              type: integer
              example: 2
      403:
        description: Accès refusé (si l'utilisateur n'a pas les permissions nécessaires)
    """
    current_user = get_jwt_identity()
    user_role = users[current_user]["role"]
    
    if "metrics" not in roles_permissions[user_role]:
        return jsonify({"error": "Access denied"}), 403
    
    # Loguer les requêtes de métriques séparément
    metrics_logger.info(f"Requête de métrique de {current_user}")

    global total_request_count, request_count_in_interval, error_count

    metric_data = {
        "total_request_count": total_request_count,
        "request_count_in_interval": request_count_in_interval,
        "error_count": error_count
    }

    # Réinitialiser le compteur de requêtes dans l'intervalle
    request_count_in_interval = 0

    return jsonify(metric_data)

# Initialiser l'application Dash avec Flask
dash_app = dash.Dash(__name__, server=app, routes_pathname_prefix='/dash/')

# Stocker les métriques pour Dash (noms différents)
dash_total_request_counts = deque(maxlen=20)
dash_interval_request_counts = deque(maxlen=20)
dash_error_counts = deque(maxlen=20)
dash_timestamps = deque(maxlen=20)

# Layout du dashboard Dash
dash_app.layout = html.Div(children=[
    html.H1(children='Monitoring de l\'API Flask'),

    dcc.Graph(id='total-request-count-graph'),
    dcc.Graph(id='interval-request-count-graph'),
    dcc.Graph(id='error-count-graph'),

    dcc.Interval(
        id='interval-component',
        interval=2*1000,  # Mettre à jour toutes les 2 secondes
        n_intervals=0
    )
])

# Middleware pour protéger l'accès à Dash avec JWT
@app.before_request
def protect_dash():
    path = request.path

    # Ne pas protéger les requêtes Dash internes
    if path.startswith('/dash/_dash'):
        return  # Autoriser ces requêtes sans vérification

    if path.startswith('/dash'):
        jwt_token = request.cookies.get('access_token')
        if jwt_token:
            try:
                # Vérification du JWT
                verify_jwt_in_request(locations=["cookies"])
            except Exception:
                # Rediriger vers la page de login si le token est invalide
                return redirect(url_for('login_dash'))
        else:
            # Si le token est absent, rediriger vers la page de login
            return redirect(url_for('login_dash'))

# Route pour la connexion à Dash
@app.route('/login_dash', methods=['GET', 'POST'])
def login_dash():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username in users and users[username]['password'] == password:
            access_token = create_access_token(identity=username)
            response = redirect('/dash/')
            response.set_cookie('access_token', access_token)
            set_access_cookies(response, access_token)
            return response
        else:
            return render_template('login.html', error="Identifiants incorrects")

    return render_template('login.html')

# Fonction pour obtenir les métriques via l'API Flask
def get_metrics():
    jwt_token = request.cookies.get('access_token')
    headers = {"Authorization": f"Bearer {jwt_token}"}
    response = requests.get("http://localhost:8000/metrics", headers=headers)
    return response.json() if response.status_code == 200 else None

# Callback pour mettre à jour les graphiques dans Dash
@dash_app.callback(
    [Output('total-request-count-graph', 'figure'),
     Output('interval-request-count-graph', 'figure'),
     Output('error-count-graph', 'figure')],
    [Input('interval-component', 'n_intervals')]
)
def update_graph(n):
    data = get_metrics()

    if data:
        total_request_count = data['total_request_count']
        request_count_in_interval = data['request_count_in_interval']
        error_count = data['error_count']
    else:
        total_request_count = 0
        request_count_in_interval = 0
        error_count = 0

    dash_timestamps.append(time.strftime('%H:%M:%S'))
    dash_total_request_counts.append(total_request_count)
    dash_interval_request_counts.append(request_count_in_interval)
    dash_error_counts.append(error_count)

    total_figure = {
        'data': [{'x': list(dash_timestamps), 'y': list(dash_total_request_counts), 'type': 'line', 'name': 'Total Requests'}],
        'layout': {'title': 'Nombre Total de Requêtes'}
    }

    interval_figure = {
        'data': [{'x': list(dash_timestamps), 'y': list(dash_interval_request_counts), 'type': 'bar', 'name': 'Requests per Interval'}],
        'layout': {'title': 'Requêtes par Intervalle'}
    }

    error_figure = {
        'data': [{'x': list(dash_timestamps), 'y': list(dash_error_counts), 'type': 'line', 'name': 'Error Count'}],
        'layout': {'title': 'Nombre d\'Erreurs'}
    }

    return total_figure, interval_figure, error_figure


# --- Lancer Flask et Dash sur des ports distincts ---
def run_flask():
    app.run(host='0.0.0.0', port=8000)

def run_dash():
    dash_app.run_server(debug=True, host='0.0.0.0', port=8050)

if __name__ == '__main__':
    flask_process = multiprocessing.Process(target=run_flask)
    dash_process = multiprocessing.Process(target=run_dash)

    flask_process.start()
    dash_process.start()

    flask_process.join()
    dash_process.join()