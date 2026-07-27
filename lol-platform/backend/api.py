import json # Pour lire le fichier de configuration du modèle
import joblib # Pour charger le normaliseur (scaler) sauvegardé
import pandas as pd # Pour charger les tables de correspondance et de statistiques
import torch # Pour charger et utiliser le modèle de deep learning
import torch.nn as nn # Contient les briques de base des réseaux de neurones
from fastapi import FastAPI, HTTPException # FastAPI crée le serveur, HTTPException renvoie des erreurs propres
from pydantic import BaseModel # Pour décrire la forme des données envoyées par l'utilisateur

#Partie 1 : Charger les tables de correspondance et de statistiques calculées par clean_data.py

champion_encoding_df = pd.read_csv("data/processed/champion_encoding.csv") # Table nom de champion <-> id
id_par_champion = dict(zip(champion_encoding_df["champion"], champion_encoding_df["champion_id"])) # Dictionnaire nom -> id

role_encoding_df = pd.read_csv("models/role_encoding.csv") # Table nom de rôle <-> id
id_par_role = dict(zip(role_encoding_df["role"], role_encoding_df["role_id"])) # Dictionnaire nom -> id

champion_stats_df = pd.read_csv("data/processed/champion_stats.csv") # Winrate + nombre de parties par (rôle, champion)
stats_champion = { # Dictionnaire (rôle, champion) -> (winrate, games)
    (ligne["role"], ligne["champion"]): (ligne["winrate"], ligne["games"]) # Une entrée par ligne du CSV
    for _, ligne in champion_stats_df.iterrows() # Parcourt chaque ligne du tableau
}

duel_stats_df = pd.read_csv("data/processed/duel_stats.csv") # Winrate + nombre de parties par duel précis
stats_duel = { # Dictionnaire (rôle, champion_1, champion_2) -> (duel_winrate, duel_games)
    (ligne["role"], ligne["champion_1"], ligne["champion_2"]): (ligne["duel_winrate"], ligne["duel_games"]) # Une entrée par ligne du CSV
    for _, ligne in duel_stats_df.iterrows() # Parcourt chaque ligne du tableau
}

#Partie 2 : Recréer l'architecture du réseau de neurones (doit être identique à train_deep_model.py)

with open("models/deep_model_config.json") as f: # Ouvre le fichier de configuration en lecture
    config = json.load(f) # Charge la configuration (tailles, dimensions...) utilisée à l'entraînement

DIM_EMBEDDING_CHAMPION = config["dim_embedding_champion"] # Taille du vecteur qui représente chaque champion
DIM_EMBEDDING_ROLE = config["dim_embedding_role"] # Taille du vecteur qui représente chaque rôle
COLONNES_NUMERIQUES = config["colonnes_numeriques"] # Liste des features numériques attendues par le modèle

class CounterPickNet(nn.Module): # Même réseau de neurones que dans train_deep_model.py
    def __init__(self, nombre_champions, nombre_roles): # Reçoit le nombre total de champions et de rôles
        super().__init__() # Initialise la classe parente (obligatoire avec PyTorch)

        self.embedding_champion = nn.Embedding(nombre_champions, DIM_EMBEDDING_CHAMPION) # Transforme un id de champion en vecteur de nombres
        self.embedding_role = nn.Embedding(nombre_roles, DIM_EMBEDDING_ROLE) # Transforme un id de rôle en vecteur de nombres

        taille_entree = DIM_EMBEDDING_CHAMPION * 2 + DIM_EMBEDDING_ROLE + len(COLONNES_NUMERIQUES) # Taille totale une fois tout mis bout à bout

        self.reseau = nn.Sequential( # Empile plusieurs couches les unes après les autres
            nn.Linear(taille_entree, 64), # Première couche : vers 64 neurones
            nn.ReLU(), # Fonction d'activation : garde seulement les valeurs positives
            nn.Linear(64, 32), # Deuxième couche : vers 32 neurones
            nn.ReLU(), # Nouvelle activation
            nn.Linear(32, 1) # Dernière couche : donne un seul nombre (le score brut de victoire)
        )

    def forward(self, champion_1_id, champion_2_id, role_id, features_numeriques): # Ce qui se passe quand on donne des données au modèle
        vecteur_champion_1 = self.embedding_champion(champion_1_id) # Vecteur représentant champion_1
        vecteur_champion_2 = self.embedding_champion(champion_2_id) # Vecteur représentant champion_2
        vecteur_role = self.embedding_role(role_id) # Vecteur représentant le rôle

        entree_complete = torch.cat([vecteur_champion_1, vecteur_champion_2, vecteur_role, features_numeriques], dim=1) # Colle tous les vecteurs + features ensemble

        return self.reseau(entree_complete) # Fait passer le tout dans le réseau et renvoie le score brut

modele = CounterPickNet(config["nombre_champions"], config["nombre_roles"]) # Crée une instance du réseau avec la bonne taille
modele.load_state_dict(torch.load("models/deep_model.pt", map_location="cpu")) # Charge les poids appris pendant l'entraînement
modele.eval() # Met le modèle en mode "évaluation" (on ne va plus jamais l'entraîner ici)

scaler = joblib.load("models/deep_model_scaler.joblib") # Charge le normaliseur utilisé à l'entraînement

#Partie 3 : Créer le serveur FastAPI

app = FastAPI(title="LoL Counter-Pick API") # Crée l'application qui va recevoir les requêtes

class DemandePrediction(BaseModel): # Décrit ce que l'utilisateur doit envoyer pour demander une prédiction
    champion_1: str # Nom du champion qu'on veut jouer
    champion_2: str # Nom du champion adverse
    role: str # Rôle concerné (TOP, JUNGLE, MIDDLE, BOTTOM, UTILITY)

def recuperer_stats_champion(role, champion): # Va chercher le winrate/games d'un champion dans ce rôle, avec une valeur par défaut
    return stats_champion.get((role, champion), (0.5, 0)) # Si jamais vu, on suppose un winrate neutre de 50% sur 0 partie

def recuperer_stats_duel(role, champion_1, champion_2): # Va chercher le winrate/games du duel précis, avec une valeur par défaut
    return stats_duel.get((role, champion_1, champion_2), (0.5, 0)) # Si ce duel précis n'a jamais été vu, winrate neutre de 50% sur 0 partie

@app.post("/predict") # Déclare l'endpoint /predict, accessible en méthode POST
def predict(demande: DemandePrediction): # FastAPI convertit automatiquement le JSON reçu en objet DemandePrediction
    if demande.champion_1 not in id_par_champion: # Vérifie que le premier champion existe dans nos données
        raise HTTPException(status_code=400, detail=f"champion_1 inconnu : {demande.champion_1}") # Erreur claire si le nom est mal orthographié ou inexistant

    if demande.champion_2 not in id_par_champion: # Vérifie que le deuxième champion existe dans nos données
        raise HTTPException(status_code=400, detail=f"champion_2 inconnu : {demande.champion_2}") # Même vérification pour champion_2

    if demande.role not in id_par_role: # Vérifie que le rôle demandé existe dans nos données
        raise HTTPException(status_code=400, detail=f"role inconnu : {demande.role}") # Erreur claire si le rôle n'est pas un des 5 rôles connus

    champion_1_winrate, champion_1_games = recuperer_stats_champion(demande.role, demande.champion_1) # Stats du champion_1 dans ce rôle
    champion_2_winrate, champion_2_games = recuperer_stats_champion(demande.role, demande.champion_2) # Stats du champion_2 dans ce rôle
    duel_winrate, duel_games = recuperer_stats_duel(demande.role, demande.champion_1, demande.champion_2) # Stats du duel précis

    features_numeriques = [[ # Une seule ligne de features, dans le même ordre que pendant l'entraînement
        champion_1_winrate, champion_1_games,
        champion_2_winrate, champion_2_games,
        duel_winrate, duel_games
    ]]
    features_numeriques = scaler.transform(features_numeriques) # Applique la même normalisation que pendant l'entraînement

    champion_1_id = torch.tensor([id_par_champion[demande.champion_1]], dtype=torch.long) # Id numérique de champion_1, dans un tenseur
    champion_2_id = torch.tensor([id_par_champion[demande.champion_2]], dtype=torch.long) # Id numérique de champion_2, dans un tenseur
    role_id = torch.tensor([id_par_role[demande.role]], dtype=torch.long) # Id numérique du rôle, dans un tenseur
    features_tensor = torch.tensor(features_numeriques, dtype=torch.float32) # Les features numériques normalisées, dans un tenseur

    with torch.no_grad(): # Désactive le calcul des gradients (inutile pour juste prédire, donc plus rapide)
        score_brut = modele(champion_1_id, champion_2_id, role_id, features_tensor) # Calcule le score brut avec le réseau de neurones
        probabilite = torch.sigmoid(score_brut).item() # Transforme le score brut en probabilité entre 0 et 1

    return { # Renvoie le résultat sous forme de JSON
        "champion_1": demande.champion_1,
        "champion_2": demande.champion_2,
        "role": demande.role,
        "probabilite_victoire_champion_1": round(probabilite, 4) # Arrondi à 4 chiffres après la virgule pour un affichage propre
    }

@app.get("/champions") # Déclare un endpoint utile pour l'interface : la liste des champions connus
def liste_champions(): # Renvoie tous les noms de champions disponibles
    return sorted(id_par_champion.keys()) # Liste triée des noms de champions

@app.get("/roles") # Déclare un endpoint utile pour l'interface : la liste des rôles connus
def liste_roles(): # Renvoie tous les noms de rôles disponibles
    return sorted(id_par_role.keys()) # Liste triée des noms de rôles
