from flask import Flask, request, jsonify
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from flasgger import Swagger
import torch
import logging

app = Flask(__name__)

# Ajouter Swagger
swagger = Swagger(app)

# Charger le modèle et le tokenizer
tokenizer = AutoTokenizer.from_pretrained("mshenoda/roberta-spam")
model = AutoModelForSequenceClassification.from_pretrained("mshenoda/roberta-spam")
model.eval()

# Compteurs pour les métriques
total_request_count = 0
request_count_in_interval = 0
error_count = 0

# Configurer les logs
logging.basicConfig(filename='app.log', level=logging.INFO)

@app.route('/predict', methods=['POST'])
def predict():
    """
    Prédire si un texte est un spam ou non.
    ---
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
            prediction:
              type: string
    """
    global total_request_count, request_count_in_interval, error_count
    total_request_count += 1
    request_count_in_interval += 1

    # Récupérer l'IP de l'utilisateur
    user_ip = request.remote_addr

    # Extraire le texte de la requête
    try:
        data = request.json
        text = data.get("text", "")
        
        # Prétraiter et faire une prédiction
        inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            prediction = torch.argmax(logits, dim=-1).item()

        # Loguer la requête et la réponse
        logging.info(f"Requête de {user_ip}: {text}, Réponse: {'spam' if prediction == 1 else 'humain'}")
        
        return jsonify({"text": text, "prediction": "spam" if prediction == 1 else "humain"})
    
    except Exception as e:
        # Compter l'erreur et loguer
        error_count += 1
        logging.error(f"Erreur pour la requête de {user_ip}: {e}")
        return jsonify({"error": "Une erreur est survenue"}), 400

@app.route('/metrics', methods=['GET'])
def metrics():
    """
    Obtenir les métriques de l'API.
    ---
    responses:
      200:
        description: Les métriques de l'API
        schema:
          type: object
          properties:
            total_request_count:
              type: integer
            request_count_in_interval:
              type: integer
            error_count:
              type: integer
    """
    global request_count_in_interval
    
    # Retourner les métriques et réinitialiser les requêtes pour l'intervalle
    metrics_data = {
        "total_request_count": total_request_count,
        "request_count_in_interval": request_count_in_interval,
        "error_count": error_count
    }
    
    # Réinitialiser le compteur des requêtes dans l'intervalle
    request_count_in_interval = 0
    
    return jsonify(metrics_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
