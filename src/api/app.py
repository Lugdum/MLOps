from fastapi import FastAPI
from pydantic import BaseModel
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Initialiser l'application FastAPI
app = FastAPI()

# Charger le tokenizer et le modèle
tokenizer = AutoTokenizer.from_pretrained("mshenoda/roberta-spam")
model = AutoModelForSequenceClassification.from_pretrained("mshenoda/roberta-spam")

# Définir l'appareil (CPU ou GPU)
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model.to(device)
model.eval()  # Mettre le modèle en mode évaluation

# Classe pour les requêtes de prédiction
class PredictionRequest(BaseModel):
    text: str

# Prétraitement du texte
def preprocess_text(text, tokenizer, max_len=128):
    result = tokenizer.encode_plus(
        text,
        add_special_tokens=True,
        max_length=max_len,
        pad_to_max_length=True,
        return_attention_mask=True,
        truncation=True
    )
    ids = torch.tensor(result['input_ids']).unsqueeze(0).to(device)
    mask = torch.tensor(result['attention_mask']).unsqueeze(0).to(device)
    return ids, mask

# Endpoint pour la prédiction
@app.post("/predict")
async def predict(request: PredictionRequest):
    text = request.text
    ids, mask = preprocess_text(text, tokenizer)
    
    with torch.no_grad():
        output = model(ids, mask)
        logits = output["logits"].squeeze(-1).cpu().numpy()
    
    # Récupérer la classe avec la probabilité la plus élevée
    predicted_label = logits.argmax(axis=-1).item()
    
    # Assumer les labels pour ce modèle
    class_names = ['humain', 'spam']  # Remplace par les vraies classes du modèle si nécessaire
    predicted_class = class_names[predicted_label]

    return {"text": text, "predicted_class": predicted_class, "confidence": float(logits.max())}
