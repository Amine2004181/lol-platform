import pandas as pd # Pour charger et manipuler le tableau de données
import os # Pour créer des dossiers
import joblib # Pour sauvegarder le modèle entraîné sur le disque
from sklearn.model_selection import train_test_split # Pour séparer les données en entraînement/test
from sklearn.ensemble import RandomForestClassifier # Le modèle de classification qu'on va entraîner
from sklearn.metrics import accuracy_score # Pour mesurer la précision du modèle

#Partie 1 : Charger les matchups préparés par clean_data.py

df = pd.read_csv("data/processed/matchups.csv") # Charge le fichier de duels enrichis
print(f"le nombre de lignes est : {len(df)}") # Affiche le nombre de duels disponibles pour l'entraînement

#Partie 2 : Encoder le rôle en nombre (le modèle ne comprend pas le texte)

tous_les_roles = sorted(df["role"].unique()) # Liste triée des rôles uniques (TOP, JUNGLE, MIDDLE, BOTTOM, UTILITY)
id_par_role = {}  # Dictionnaire : nom du rôle -> son id (un nombre)

for i, role in enumerate(tous_les_roles): # Parcourt la liste avec un compteur i (0, 1, 2, ...)
    id_par_role[role] = i # Associe ce numéro au nom du rôle

df["role_id"] = df["role"].map(id_par_role) # Ajoute une colonne role_id en remplaçant chaque nom de rôle par son numéro

#Partie 3 : Choisir les features (les colonnes utilisées par le modèle) et la cible à prédire

features = [ # Liste des colonnes que le modèle va utiliser pour apprendre
    "champion_1_id", "champion_2_id", "role_id",
    "champion_1_winrate", "champion_1_games",
    "champion_2_winrate", "champion_2_games",
    "duel_winrate", "duel_games"
]

X = df[features] # X = les features (les infos qu'on donne au modèle)
y = df["victoire_champion_1"] # y = la cible (ce que le modèle doit deviner : 1 ou 0)

#Partie 4 : Séparer les données en entraînement (80%) et test (20%)

X_train, X_test, y_train, y_test = train_test_split( # Coupe les données en 2 groupes
    X, y, # Les features et la cible à couper
    test_size=0.2, # 20% des données servent uniquement à tester le modèle (jamais vues pendant l'entraînement)
    random_state=42 # Nombre fixe pour que le découpage soit toujours le même à chaque exécution
)

print(f"le nombre de lignes d'entraînement est : {len(X_train)}") # Affiche la taille du jeu d'entraînement
print(f"le nombre de lignes de test est : {len(X_test)}") # Affiche la taille du jeu de test

#Partie 5 : Entraîner le modèle

modele = RandomForestClassifier( # Crée un modèle de type "forêt d'arbres de décision"
    n_estimators=200, # Nombre d'arbres dans la forêt (plus il y en a, plus c'est précis mais plus c'est lent)
    max_depth=10, # Profondeur maximale de chaque arbre (limite le sur-apprentissage)
    random_state=42, # Nombre fixe pour que l'entraînement soit reproductible
    n_jobs=-1 # Utilise tous les coeurs du processeur disponibles pour aller plus vite
)

modele.fit(X_train, y_train) # Entraîne le modèle sur les données d'entraînement

#Partie 6 : Évaluer le modèle

predictions = modele.predict(X_test) # Demande au modèle de deviner le résultat sur les données de test
precision = accuracy_score(y_test, predictions) # Compare les prédictions aux vraies réponses
print(f"la precision du modele est : {precision:.2%}") # Affiche le pourcentage de bonnes prédictions

#Partie 7 : Sauvegarder le modèle et l'encodage des rôles

os.makedirs("models", exist_ok=True) # Crée le dossier models s'il n'existe pas déjà
joblib.dump(modele, "models/counterpick_model.joblib") # Sauvegarde le modèle entraîné sur le disque

role_encoding_df = pd.DataFrame({ # Crée un petit tableau à partir du dictionnaire id_par_role
    "role": list(id_par_role.keys()), # Colonne des noms de rôles
    "role_id": list(id_par_role.values()) # Colonne des ids correspondants
})
role_encoding_df.to_csv("models/role_encoding.csv", index=False) # Sauvegarde la correspondance rôle <-> id

print("Fichier models/counterpick_model.joblib cree") # Confirme que le modèle a bien été sauvegardé
print("Fichier models/role_encoding.csv cree") # Confirme que l'encodage des rôles a bien été sauvegardé
