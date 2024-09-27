from flask import Flask, request, jsonify
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from flasgger import Swagger
import torch

app = Flask(__name__)

# Ajouter Swagger
swagger = Swagger(app)

# Charger le modèle et le tokenizer
tokenizer = AutoTokenizer.from_pretrained("mshenoda/roberta-spam")
model = AutoModelForSequenceClassification.from_pretrained("mshenoda/roberta-spam")
model.eval()

# Compteur pour suivre le nombre de requêtes
request_count = 0

@app.route('/predict', methods=['POST'])
def predict():
    """
    Prédire si un texte est un spam ou non.
    ---
    parameters:
      - name: text
        in: body
        type: string
        required: true
        description: Le texte à classifier
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
    global request_count
    request_count += 1
    
    # Extraire le texte de la requête
    data = request.json
    text = data.get("text", "")
    
    # Prétraiter et faire une prédiction
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        prediction = torch.argmax(logits, dim=-1).item()
    
    return jsonify({"text": text, "prediction": "spam" if prediction == 1 else "humain"})

@app.route('/metrics', methods=['GET'])
def metrics():
    """
    Obtenir le nombre de requêtes effectuées.
    ---
    responses:
      200:
        description: Le nombre de requêtes
        schema:
          type: object
          properties:
            request_count:
              type: integer
    """
    return jsonify({"request_count": request_count})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
