import streamlit as st
import requests

# Définir l'URL de l'API FastAPI (remplace par l'URL de déploiement si nécessaire)
API_URL = "http://localhost:8000/predict"

# Titre de l'application
st.title("Classification de Spam")

# Input de l'utilisateur : un champ de texte pour entrer le message à tester
input_text = st.text_area("Entrez un message texte pour tester s'il s'agit d'un spam", "")

# Lorsque l'utilisateur clique sur le bouton, envoyer une requête à l'API
if st.button("Prédire"):
    if input_text:
        # Envoyer le texte à l'API FastAPI
        response = requests.post(API_URL, json={"text": input_text})

        if response.status_code == 200:
            result = response.json()
            # Afficher la classe prédite (spam ou humain) et la confiance
            st.write(f"**Classe prédite**: {result['predicted_class']}")
            st.write(f"**Confiance**: {result['confidence']:.4f}")
        else:
            st.write("Erreur lors de la prédiction. Veuillez vérifier que l'API est en cours d'exécution.")
    else:
        st.write("Veuillez entrer un texte à prédire.")
