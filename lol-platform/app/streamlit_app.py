import streamlit as st # Librairie pour créer l'interface web
import requests # Pour envoyer des requêtes à l'API FastAPI
import os # Pour lire l'adresse de l'API depuis une variable d'environnement (utile avec Docker)

#Partie 1 : Configuration de la page

st.set_page_config(page_title="LoL Counter-Pick", page_icon="🎮") # Titre et icône affichés dans l'onglet du navigateur
st.title("LoL Counter-Pick") # Grand titre affiché en haut de la page

API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000") # Adresse du serveur FastAPI (127.0.0.1 en local, ou le nom du service Docker en conteneur)

#Partie 2 : Récupérer la liste des champions et des rôles depuis l'API

@st.cache_data(ttl=300) # Garde le résultat en mémoire 5 minutes pour ne pas re-demander à l'API à chaque clic
def charger_champions(): # Va chercher la liste des champions connus auprès de l'API
    reponse = requests.get(f"{API_URL}/champions") # Envoie une requête GET à l'endpoint /champions
    reponse.raise_for_status() # Provoque une erreur si l'API a répondu un code d'erreur
    return reponse.json() # Renvoie la liste des champions (convertie depuis le JSON)

@st.cache_data(ttl=300) # Garde le résultat en mémoire 5 minutes
def charger_roles(): # Va chercher la liste des rôles connus auprès de l'API
    reponse = requests.get(f"{API_URL}/roles") # Envoie une requête GET à l'endpoint /roles
    reponse.raise_for_status() # Provoque une erreur si l'API a répondu un code d'erreur
    return reponse.json() # Renvoie la liste des rôles (convertie depuis le JSON)

try: # On essaie de contacter l'API
    champions = charger_champions() # Récupère la liste des champions
    roles = charger_roles() # Récupère la liste des rôles
except requests.exceptions.ConnectionError: # Si l'API n'est pas démarrée ou injoignable
    st.error("Impossible de contacter l'API. Lance-la avec : uvicorn backend.api:app --port 8000") # Message clair pour l'utilisateur
    st.stop() # Arrête l'exécution du reste de la page (inutile de continuer sans données)

#Partie 3 : Formulaire de sélection

colonne_1, colonne_2 = st.columns(2) # Divise la page en 2 colonnes côte à côte

with colonne_1: # Tout ce qui est dans ce bloc s'affiche dans la colonne de gauche
    champion_1 = st.selectbox("Ton champion", champions) # Liste déroulante pour choisir son propre champion

with colonne_2: # Tout ce qui est dans ce bloc s'affiche dans la colonne de droite
    champion_2 = st.selectbox("Champion adverse", champions, index=1) # Liste déroulante pour choisir le champion adverse

role = st.selectbox("Rôle", roles) # Liste déroulante pour choisir le rôle concerné

#Partie 4 : Appeler l'API et afficher le résultat

if st.button("Prédire"): # Le bloc suivant ne s'exécute que quand l'utilisateur clique sur le bouton
    if champion_1 == champion_2: # Un champion ne peut pas s'affronter lui-même
        st.warning("Choisis deux champions différents.") # Message d'avertissement affiché à l'utilisateur
    else:
        reponse = requests.post(f"{API_URL}/predict", json={ # Envoie une requête POST à l'endpoint /predict
            "champion_1": champion_1, # Le champion choisi par l'utilisateur
            "champion_2": champion_2, # Le champion adverse choisi
            "role": role # Le rôle choisi
        })

        if reponse.status_code != 200: # Si l'API a renvoyé une erreur (ex: nom de champion invalide)
            st.error(reponse.json()["detail"]) # Affiche le message d'erreur renvoyé par l'API
        else:
            resultat = reponse.json() # Convertit la réponse de l'API en dictionnaire python
            probabilite = resultat["probabilite_victoire_champion_1"] # Récupère la probabilité de victoire de champion_1

            st.metric(f"Probabilité de victoire de {champion_1}", f"{probabilite:.1%}") # Affiche un gros chiffre avec le pourcentage
            st.progress(probabilite) # Affiche une barre de progression visuelle de cette probabilité

            if probabilite >= 0.5: # Si la probabilité est en faveur de champion_1
                st.success(f"{champion_1} est favori face à {champion_2} en {role}") # Message positif
            else: # Sinon, c'est champion_2 qui est favori
                st.info(f"{champion_2} est favori face à {champion_1} en {role}") # Message informatif
