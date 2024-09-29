import multiprocessing
from flask import Flask, request, render_template, redirect, url_for
from flasgger import Swagger
from flask_jwt_extended import JWTManager, create_access_token, verify_jwt_in_request, set_access_cookies

from logging_config import configure_logging
from utils import users, init_db, update_metrics
from api.auth import auth
from api.routes import routes_bp
from api.dash_app import create_dash_app

# Initialiser la base de données SQLite
init_db()

# Créer une application Flask
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

# Configurer les logs
user_logger, metrics_logger = configure_logging()

# Enregistrer les routes
app.register_blueprint(routes_bp)

# Authentification basique avec rôle
@auth.verify_password
def verify_password(username, password):
    if username in users and users[username]['password'] == password:
        return username
    else:
        update_metrics(error=1)
        return None

@auth.get_user_roles
def get_user_roles(user):
    return [users[user]["role"]]

# Initialiser l'application Dash avec Flask
dash_app = create_dash_app(app)

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