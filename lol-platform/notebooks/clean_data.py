import pandas as pd # Librairie pour manipuler des tableaux de données (DataFrame)
import os # Pour créer des dossiers et gérer des chemins de fichiers

#Partie 2 : Charger les données

df=pd.read_csv("data/raw/matches.csv") # Charge le CSV collecté et le transforme en DataFrame pandas
print(f"le nombre de lignes est : {len(df)}") # Affiche le nombre de lignes (une ligne = un participant à un match)

#Partie 3 : Créer les matchups (duel de champions par rôle, pour chaque match, avec les 2 points de vue)

# On enlève les lignes sans rôle valide (ex: parties spéciales où teamPosition est vide)
df = df[df["role"].notna() & (df["role"] != "")] # Garde seulement les lignes où role n'est ni vide ni manquant

matchups = []  # Liste qui contiendra une ligne par duel : 2 champions du même rôle, dans le même match

# Dans un match ranked normal, chaque rôle contient exactement 2 joueurs (1 par équipe)
for (match_id, role), group in df.groupby(["match_id", "role"]): # Regroupe les lignes par match puis par rôle
    if len(group) != 2: # Si le groupe n'a pas exactement 2 joueurs (données manquantes, remake...)
        continue  # On ignore ce groupe et on passe au suivant

    joueur_1 = group.iloc[0] # Première ligne du groupe (premier joueur de ce rôle)
    joueur_2 = group.iloc[1] # Deuxième ligne du groupe (adversaire du même rôle)

    victoire_joueur_1 = int(joueur_1["victoire"]) # 1 si joueur_1 a gagné, 0 sinon
    victoire_joueur_2 = int(joueur_2["victoire"]) # 1 si joueur_2 a gagné, 0 sinon

    # Ligne n°1 : le duel vu du point de vue du joueur_1
    matchups.append({
        "match_id": match_id, # Id du match auquel appartient ce duel
        "role": role, # Rôle concerné par ce duel (TOP, JUNGLE, MIDDLE, BOTTOM, UTILITY)
        "champion_1": joueur_1["champion"], # Champion du premier joueur
        "champion_2": joueur_2["champion"], # Champion du deuxième joueur
        "victoire_champion_1": victoire_joueur_1 # 1 si champion_1 a gagné, 0 sinon
    })

    # Ligne n°2 : le MÊME duel, mais vu du point de vue du joueur_2 (on inverse les 2 champions et le résultat)
    matchups.append({
        "match_id": match_id, # Id du match auquel appartient ce duel
        "role": role, # Rôle concerné par ce duel
        "champion_1": joueur_2["champion"], # Cette fois, joueur_2 prend la place de champion_1
        "champion_2": joueur_1["champion"], # Et joueur_1 prend la place de champion_2
        "victoire_champion_1": victoire_joueur_2 # 1 si joueur_2 (maintenant champion_1) a gagné, 0 sinon
    })

print(f"le nombre de matchups créés (avec symétrie) est : {len(matchups)}") # Affiche le nombre total de duels créés (2 par match/rôle)

#Partie 4 : Calculer le winrate et le nombre de parties de chaque champion, par rôle

stats_champion = {}  # Dictionnaire : (role, champion) -> [nombre de victoires, nombre de parties]

for m in matchups: # Parcourt chaque duel déjà créé
    cle = (m["role"], m["champion_1"]) # Clé unique : ce champion, dans ce rôle
    if cle not in stats_champion: # Si on rencontre ce champion/rôle pour la première fois
        stats_champion[cle] = [0, 0] # On initialise son compteur à [0 victoire, 0 partie]
    stats_champion[cle][0] += m["victoire_champion_1"] # Ajoute 1 victoire si le champion a gagné ce duel
    stats_champion[cle][1] += 1 # Ajoute 1 partie dans tous les cas

#Partie 5 : Calculer le winrate et le nombre de parties du duel précis (champion_1 vs champion_2, par rôle)

stats_duel = {}  # Dictionnaire : (role, champion_1, champion_2) -> [nombre de victoires, nombre de parties]

for m in matchups: # Parcourt chaque duel déjà créé
    cle = (m["role"], m["champion_1"], m["champion_2"]) # Clé unique : ce duel précis, dans ce rôle
    if cle not in stats_duel: # Si on rencontre ce duel pour la première fois
        stats_duel[cle] = [0, 0] # On initialise son compteur à [0 victoire, 0 partie]
    stats_duel[cle][0] += m["victoire_champion_1"] # Ajoute 1 victoire si champion_1 a gagné ce duel précis
    stats_duel[cle][1] += 1 # Ajoute 1 partie dans tous les cas

#Partie 6 : Donner un identifiant numérique à chaque champion

tous_les_champions = sorted(set(m["champion_1"] for m in matchups)) # Liste triée de tous les champions, sans doublons
id_par_champion = {}  # Dictionnaire : nom du champion -> son id (un nombre)

for i, champion in enumerate(tous_les_champions): # Parcourt la liste avec un compteur i (0, 1, 2, ...)
    id_par_champion[champion] = i # Associe ce numéro au nom du champion

#Partie 7 : Rassembler toutes les informations sur chaque ligne

for m in matchups: # Parcourt chaque duel une dernière fois pour lui ajouter toutes les nouvelles infos
    victoires_1, parties_1 = stats_champion[(m["role"], m["champion_1"])] # Récupère les stats de champion_1
    victoires_2, parties_2 = stats_champion[(m["role"], m["champion_2"])] # Récupère les stats de champion_2
    victoires_duel, parties_duel = stats_duel[(m["role"], m["champion_1"], m["champion_2"])] # Récupère les stats du duel précis

    m["champion_1_winrate"] = victoires_1 / parties_1 # Winrate de champion_1 dans ce rôle (entre 0 et 1)
    m["champion_1_games"] = parties_1 # Nombre de parties utilisées pour ce winrate
    m["champion_2_winrate"] = victoires_2 / parties_2 # Winrate de champion_2 dans ce rôle
    m["champion_2_games"] = parties_2 # Nombre de parties utilisées pour ce winrate
    m["duel_winrate"] = victoires_duel / parties_duel # Winrate spécifique de champion_1 contre champion_2
    m["duel_games"] = parties_duel # Nombre de fois où ce duel précis a été observé
    m["champion_1_id"] = id_par_champion[m["champion_1"]] # Id numérique de champion_1
    m["champion_2_id"] = id_par_champion[m["champion_2"]] # Id numérique de champion_2

#Partie 8 : Sauvegarder les résultats

matchups_df = pd.DataFrame(matchups) # Transforme la liste finale de duels enrichis en tableau pandas
print(f"le nombre de colonnes final est : {len(matchups_df.columns)}") # Affiche le nombre de colonnes du fichier final

os.makedirs("data/processed", exist_ok=True) # Crée le dossier data/processed s'il n'existe pas déjà
matchups_df.to_csv("data/processed/matchups.csv", index=False) # Écrit les duels enrichis dans un CSV, sans colonne d'index

# Sauvegarder aussi la correspondance nom <-> id des champions, pour la réutiliser plus tard
encodage_df = pd.DataFrame({ # Crée un petit tableau à partir du dictionnaire id_par_champion
    "champion": list(id_par_champion.keys()), # Colonne des noms de champions
    "champion_id": list(id_par_champion.values()) # Colonne des ids correspondants
})
encodage_df.to_csv("data/processed/champion_encoding.csv", index=False) # Écrit la correspondance dans un CSV séparé

# Sauvegarder aussi les statistiques par champion/rôle (utile pour l'API plus tard, sans tout recalculer)
champion_stats_df = pd.DataFrame([ # Transforme le dictionnaire stats_champion en tableau
    {"role": role, "champion": champion, "winrate": victoires / parties, "games": parties} # Une ligne par (rôle, champion)
    for (role, champion), (victoires, parties) in stats_champion.items() # Parcourt chaque entrée du dictionnaire
])
champion_stats_df.to_csv("data/processed/champion_stats.csv", index=False) # Écrit les stats par champion dans un CSV séparé

# Sauvegarder aussi les statistiques par duel précis (utile pour l'API plus tard, sans tout recalculer)
duel_stats_df = pd.DataFrame([ # Transforme le dictionnaire stats_duel en tableau
    {"role": role, "champion_1": champion_1, "champion_2": champion_2, "duel_winrate": victoires / parties, "duel_games": parties} # Une ligne par duel précis
    for (role, champion_1, champion_2), (victoires, parties) in stats_duel.items() # Parcourt chaque entrée du dictionnaire
])
duel_stats_df.to_csv("data/processed/duel_stats.csv", index=False) # Écrit les stats de duel dans un CSV séparé

print("Fichier data/processed/matchups.csv créé") # Confirme que le fichier de matchups a bien été sauvegardé
print("Fichier data/processed/champion_encoding.csv créé") # Confirme que le fichier d'encodage a bien été sauvegardé
print("Fichier data/processed/champion_stats.csv créé") # Confirme que le fichier de stats par champion a bien été sauvegardé
print("Fichier data/processed/duel_stats.csv créé") # Confirme que le fichier de stats de duel a bien été sauvegardé
