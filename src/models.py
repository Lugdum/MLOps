from transformers import AutoTokenizer, AutoModelForSequenceClassification


# Charger le modèle et le tokenizer
tokenizer = AutoTokenizer.from_pretrained("mshenoda/roberta-spam")
model = AutoModelForSequenceClassification.from_pretrained("mshenoda/roberta-spam")
model.eval()