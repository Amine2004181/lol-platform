import pandas as pd # Pour charger le tableau de données
import numpy as np # Pour quelques calculs numériques
import torch # Librairie principale pour construire et utiliser des réseaux de neurones
import torch.nn as nn # Contient les briques de base des réseaux de neurones (couches, etc.)
from sklearn.model_selection import train_test_split # Pour séparer les données en entraînement/test
from sklearn.preprocessing import StandardScaler # Pour ramener les features numériques à une échelle comparable
import joblib # Pour sauvegarder le normaliseur (StandardScaler) sur le disque
import os # Pour créer des dossiers
import json # Pour sauvegarder la configuration du modèle (tailles, dimensions...)

#Partie 1 : Charger les matchups préparés par clean_data.py

df = pd.read_csv("data/processed/matchups.csv") # Charge le fichier de duels enrichis
print(f"le nombre de lignes est : {len(df)}") # Affiche le nombre de duels disponibles

#Partie 2 : Encoder le rôle en nombre (même logique que dans train_model.py)

tous_les_roles = sorted(df["role"].unique()) # Liste triée des rôles uniques
id_par_role = {role: i for i, role in enumerate(tous_les_roles)} # Dictionnaire : nom du rôle -> id
df["role_id"] = df["role"].map(id_par_role) # Ajoute la colonne role_id

nombre_champions = int(max(df["champion_1_id"].max(), df["champion_2_id"].max())) + 1 # Le plus grand id de champion + 1 (les ids commencent à 0)
nombre_roles = len(tous_les_roles) # Nombre total de rôles différents

#Partie 3 : Préparer les features numériques et la cible

colonnes_numeriques = [ # Les colonnes numériques utilisées en plus des embeddings
    "champion_1_winrate", "champion_1_games",
    "champion_2_winrate", "champion_2_games",
    "duel_winrate", "duel_games"
]

X_champion_1 = df["champion_1_id"].values # Tableau des ids de champion_1
X_champion_2 = df["champion_2_id"].values # Tableau des ids de champion_2
X_role = df["role_id"].values # Tableau des ids de rôle
X_numerique = df[colonnes_numeriques].values.astype("float32") # Tableau des features numériques
y = df["victoire_champion_1"].values.astype("float32") # La cible à prédire (0 ou 1)

#Partie 4 : Séparer en entraînement (80%) et test (20%)

indices = np.arange(len(df)) # Une liste d'indices [0, 1, 2, ..., n-1]
indices_train, indices_test = train_test_split(indices, test_size=0.2, random_state=42) # Coupe les indices en 2 groupes

scaler = StandardScaler() # Objet qui va centrer (moyenne 0) et réduire (écart-type 1) les features numériques
scaler.fit(X_numerique[indices_train]) # Apprend la moyenne et l'écart-type UNIQUEMENT sur les données d'entraînement
X_numerique = scaler.transform(X_numerique).astype("float32") # Applique cette normalisation à toutes les lignes (train + test)

def vers_tenseurs(indices): # Fonction qui transforme un groupe d'indices en tenseurs PyTorch prêts à l'emploi
    return (
        torch.tensor(X_champion_1[indices], dtype=torch.long), # Les ids de champion_1 de ce groupe
        torch.tensor(X_champion_2[indices], dtype=torch.long), # Les ids de champion_2 de ce groupe
        torch.tensor(X_role[indices], dtype=torch.long), # Les ids de rôle de ce groupe
        torch.tensor(X_numerique[indices], dtype=torch.float32), # Les features numériques de ce groupe
        torch.tensor(y[indices], dtype=torch.float32).unsqueeze(1) # La cible de ce groupe (unsqueeze pour avoir la bonne forme)
    )

champ1_train, champ2_train, role_train, num_train, y_train = vers_tenseurs(indices_train) # Prépare les tenseurs d'entraînement
champ1_test, champ2_test, role_test, num_test, y_test = vers_tenseurs(indices_test) # Prépare les tenseurs de test

print(f"le nombre de lignes d'entrainement est : {len(indices_train)}") # Affiche la taille du jeu d'entraînement
print(f"le nombre de lignes de test est : {len(indices_test)}") # Affiche la taille du jeu de test

#Partie 5 : Définir le réseau de neurones

DIM_EMBEDDING_CHAMPION = 16 # Taille du vecteur qui représente chaque champion
DIM_EMBEDDING_ROLE = 4 # Taille du vecteur qui représente chaque rôle

class CounterPickNet(nn.Module): # Réseau de neurones qui prédit la victoire d'un duel de champions
    def __init__(self, nombre_champions, nombre_roles): # Reçoit le nombre total de champions et de rôles
        super().__init__() # Initialise la classe parente (obligatoire avec PyTorch)

        self.embedding_champion = nn.Embedding(nombre_champions, DIM_EMBEDDING_CHAMPION) # Transforme un id de champion en vecteur de nombres
        self.embedding_role = nn.Embedding(nombre_roles, DIM_EMBEDDING_ROLE) # Transforme un id de rôle en vecteur de nombres

        taille_entree = DIM_EMBEDDING_CHAMPION * 2 + DIM_EMBEDDING_ROLE + len(colonnes_numeriques) # Taille totale une fois tout mis bout à bout

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

modele = CounterPickNet(nombre_champions, nombre_roles) # Crée une instance du réseau

#Partie 6 : Entraîner le réseau

fonction_perte = nn.BCEWithLogitsLoss() # Mesure l'erreur entre la prédiction et la vraie réponse (classification binaire)
optimiseur = torch.optim.Adam(modele.parameters(), lr=0.001) # Algorithme qui ajuste les poids du réseau pour réduire l'erreur

nombre_epochs = 50 # Nombre de fois où le modèle revoit l'intégralité des données d'entraînement

for epoch in range(nombre_epochs): # Répète l'entraînement nombre_epochs fois
    modele.train() # Met le modèle en mode "entraînement"
    optimiseur.zero_grad() # Remet à zéro les gradients calculés au tour précédent

    predictions = modele(champ1_train, champ2_train, role_train, num_train) # Calcule les prédictions sur les données d'entraînement
    perte = fonction_perte(predictions, y_train) # Calcule l'erreur entre prédictions et vraies réponses

    perte.backward() # Calcule comment ajuster chaque poids pour réduire l'erreur
    optimiseur.step() # Applique l'ajustement des poids

    if (epoch + 1) % 5 == 0 or epoch == 0: # N'affiche qu'une ligne toutes les 5 epochs (+ la première) pour ne pas surcharger l'affichage
        print(f"epoch {epoch+1}/{nombre_epochs} - perte : {perte.item():.4f}") # Affiche l'erreur à cette étape

#Partie 7 : Évaluer le modèle sur les données de test

modele.eval() # Met le modèle en mode "évaluation"
with torch.no_grad(): # Désactive le calcul des gradients (inutile pour juste évaluer, donc plus rapide)
    predictions_test = modele(champ1_test, champ2_test, role_test, num_test) # Calcule les prédictions sur les données de test
    predictions_test = torch.sigmoid(predictions_test) # Transforme le score brut en probabilité entre 0 et 1
    predictions_test_binaire = (predictions_test >= 0.5).float() # Transforme la probabilité en 0 ou 1 (seuil à 50%)

precision = (predictions_test_binaire == y_test).float().mean().item() # Calcule le pourcentage de bonnes prédictions
print(f"la precision du modele deep learning est : {precision:.2%}") # Affiche la précision

#Partie 8 : Sauvegarder le modèle et sa configuration

os.makedirs("models", exist_ok=True) # Crée le dossier models s'il n'existe pas déjà
torch.save(modele.state_dict(), "models/deep_model.pt") # Sauvegarde les poids appris du réseau
joblib.dump(scaler, "models/deep_model_scaler.joblib") # Sauvegarde le normaliseur (nécessaire pour préparer les données de la même façon plus tard)

config = { # Dictionnaire qui décrit la forme du réseau, pour pouvoir le recharger plus tard
    "nombre_champions": nombre_champions,
    "nombre_roles": nombre_roles,
    "dim_embedding_champion": DIM_EMBEDDING_CHAMPION,
    "dim_embedding_role": DIM_EMBEDDING_ROLE,
    "colonnes_numeriques": colonnes_numeriques
}
with open("models/deep_model_config.json", "w") as f: # Ouvre un fichier en écriture
    json.dump(config, f) # Écrit la configuration au format JSON

role_encoding_df = pd.DataFrame({"role": list(id_par_role.keys()), "role_id": list(id_par_role.values())}) # Table de correspondance rôle <-> id
role_encoding_df.to_csv("models/role_encoding.csv", index=False) # Sauvegarde (identique à celle de train_model.py)

print("Fichier models/deep_model.pt cree") # Confirme la sauvegarde du modèle
print("Fichier models/deep_model_config.json cree") # Confirme la sauvegarde de la configuration
