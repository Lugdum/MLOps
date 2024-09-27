from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

from logging_config import configure_logging
from utils import users, roles_permissions, total_request_count, request_count_in_interval, error_count
from models import tokenizer, model
from api.auth import auth

# Créer un blueprint pour les routes
routes_bp = Blueprint('routes', __name__)

# Configurer les logs
user_logger, metrics_logger = configure_logging()


# Route pour générer un token JWT
@routes_bp.route('/login', methods=['POST'])
@auth.login_required
def login():
    """
    Générer un token JWT après authentification
    ---
    tags:
      - Authentification
    security:
      - BasicAuth: []
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
@routes_bp.route('/predict', methods=['POST'])
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

@routes_bp.route('/logs', methods=['GET'])
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

@routes_bp.route('/clear_logs', methods=['DELETE'])
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

@routes_bp.route('/metrics', methods=['GET'])
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