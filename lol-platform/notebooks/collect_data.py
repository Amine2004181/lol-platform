#Le flux complet du script en entier:
#Partie 1 → imports des bibliothèques
#Partie 2 → configuration (clé API, région...)
#Partie 3 → récupère les joueurs Challenger
#Partie 4 → récupère le PUUID de chaque joueur
#Partie 5 → récupère la liste des matchs
#Partie 6 → récupère les détails de chaque match
#Partie 7 → prépare la liste vide rows[]
#Partie 8 → remplit rows[] avec 1000 lignes de données
#Partie 9 → sauvegarde rows[] dans matches.csv ✅




import requests #Pour envoyer des demandes à Riot sur internet
import os #Pour lire la clé API dans le fichier .env
import time #Pour faire des pauses entre les requêtes
import csv #Pour créer et écrire dans un fichier CSV
from dotenv import load_dotenv #Pour charger le fichier .env

# Partie 2 : Configuration

load_dotenv() #charger le contenu de .env
API_KEY = os.getenv("RIOT_API_KEY") # getenv est une fct de os qui lit une variable , os.: ce qui va etre affiché aprés(.) appartient à la librairie os , ("RIOT_API_KEY"): la variable qui est dans .env
HEADERS = {"X-Riot-Token": API_KEY} #{}: un dictionnaire pour crée un vocabulaire(association une nouvelle valeur à quelque chose)  pour contacter Riot , le badge est nécessaire c'est celui qui contient la clé , Riot demande le X-Riot-Token , on a associé la valeur de clé à lui
REGION = "euw1" # Serveur des joueurs
REGION_MATCH ="europe" # Serveur des matchs

# Partie 3 : Récupérer les joueurs Challenger

def get_challengers_players(): # Fonction qui récupère la liste des joueurs du classement Challenger
 # ():la fct n'a besoin d'aucune information pour fonctionner , (:):c.a.d le code de la fct commence à la ligne suivante
 # Comme une rectte que j'écris et j'ulitiserai pas mal de fois aprés

 url = f"https://{REGION}.api.riotgames.com/lol/league/v4/challengerleagues/by-queue/RANKED_SOLO_5x5" # Construit l'URL de l'API Riot pour récupérer les joueurs Challenger

 # f" ": c'est à dire que le texte à l'intérieur peut contenir des variables qui seront remplacé automatiquement par leurs valeurs attribués avant
 # /lol/league/v4/challengerleagues/by-queue: lien pour avoir les joueurs challengers
 # RANKED_SOLO_5x5 : Le code Riot pour les paries solo duo uniquement

 response= requests.get(url , headers=HEADERS) # la réponse sera une demande des données de  lien des matchs avec mon badge

 data=response.json() # les données recues(data) seront laréponse qui sera transformée en dictionnaire python lisible

 if "status" in data: # Si la réponse contient une erreur au lieu des données attendues
   raise Exception(f"❌ Erreur API Riot: {data['status']} — Vérifie ta clé API dans .env") # Stoppe le script et affiche un message d'erreur clair

 players = data["entries"] # entries(mot clé de riot) contient des infos de joueurs:summoner Id ,...

 print(f"✅ {len(players)} joueurs Challenger trouvés") # affiche le nombre de joueurs trouvés , {len(players)}: compte le nombre de joueurs

 return players # la recette est terminé , il sera servi à table

# Partie 4 : Récupérer le PUUID d'un joueur

#summonerId  →  identifiant interne Riot (ancien système)
#PUUID       →  identifiant universel du joueur (nouveau système)

def get_puuid(summoner_id): #() ne sont pas vide , c.a.d on doit donner l'information qui est dans () pour que la fct fonctionne

 url = f"https://{REGION}.api.riotgames.com/lol/summoner/v4/summoners/{summoner_id}" # Construit l'URL pour récupérer les infos du joueur via son summonerId

 response = requests.get(url , headers=HEADERS) # Envoie la requête à l'API Riot et récupère la réponse

 return response.json().get("puuid") # .get() est plus sécurisé — si Riot ne renvoie pas de PUUID, le programme ne plante pas au contraire de get []
#On en a besoin car l'endpoint des matchs n'accepte que le PUUID, pas le summonerId.

# Partie 5 : Récupérer la liste des ids(identifiants) des matchs

def get_matches(puuid, total=500): # Fonction qui récupère jusqu'à "total" ids de matchs pour un joueur donné

 # Riot limite count à 100 par requête → on fait plusieurs requêtes avec start pour paginer
 all_ids = [] # Liste qui contiendra tous les ids de matchs récupérés
 start = 0 # Index de départ pour la pagination
 while len(all_ids) < total: # Continue tant qu'on n'a pas atteint le nombre de matchs demandé
   count = min(100, total - len(all_ids))  # max 100 par requête
   url = f"https://{REGION_MATCH}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start={start}&count={count}&queue=420" # Construit l'URL paginée pour récupérer les ids de matchs (queue 420 = ranked solo/duo)
   response = requests.get(url, headers=HEADERS) # Envoie la requête à l'API Riot
   data = response.json() # Convertit la réponse en objet python (liste d'ids ou dict d'erreur)
   if isinstance(data, dict) and "status" in data: # Vérifie si la réponse est une erreur plutôt qu'une liste d'ids
     print(f"⚠️ Erreur API get_matches: {data['status']}")
     break # Arrête la boucle en cas d'erreur
   if not data:  # Plus de matchs disponibles
     break # Arrête la boucle, il n'y a plus de matchs à récupérer
   all_ids.extend(data) # Ajoute les nouveaux ids récupérés à la liste totale
   start += count # Avance l'index de pagination pour la requête suivante
   time.sleep(1.2)  # Pause entre chaque requête pour éviter le rate limit
 return all_ids # Renvoie la liste complète des ids de matchs récupérés

# Partie 6 : Récupérer les détails du match

def get_match_details(match_id, retries=3): # Fonction qui récupère les détails d'un match, avec 3 tentatives en cas d'échec

 url = f"https://{REGION_MATCH}.api.riotgames.com/lol/match/v5/matches/{match_id}" # Construit l'URL pour récupérer les détails du match

 for attempt in range(retries): # Boucle de tentatives (jusqu'à "retries" essais)
   try: # Essaie d'envoyer la requête, au cas où la connexion échoue
     response = requests.get(url, headers=HEADERS) # Envoie la requête à l'API Riot
     data = response.json() # Convertit la réponse en dictionnaire python
     if isinstance(data, dict) and "status" in data: # Vérifie si la réponse contient une erreur API
       print(f"⚠️ Erreur API get_match_details: {data['status']}")
       return {} # Renvoie un dictionnaire vide car le match n'a pas pu être récupéré
     return data # Renvoie les données du match si tout s'est bien passé
   except Exception as e: # Si la requête échoue (problème réseau, timeout...)
     print(f"⚠️ Connexion échouée ({attempt+1}/{retries}) pour {match_id} : {e}")
     time.sleep(3)  # Attendre 3s avant de réessayer

 return {}  # Après 3 tentatives, on abandonne ce match

# Partie 7 : La collecte principale

players = get_challengers_players() # Récupère la liste des joueurs Challenger

players = players[:100]  # Prends les 100 premiers joueurs

# Reprendre depuis le dernier joueur traité en cas d'interruption
os.makedirs("data/raw", exist_ok=True) # Crée le dossier data/raw s'il n'existe pas déjà
PROGRESS_FILE = "data/raw/progress.txt" # Chemin du fichier qui garde en mémoire le dernier joueur traité
CSV_FILE = "data/raw/matches.csv" # Chemin du fichier CSV où seront sauvegardées les données collectées

if os.path.exists(PROGRESS_FILE): # Si un fichier de progression existe déjà (collecte précédente interrompue)
  with open(PROGRESS_FILE) as f: # Ouvre le fichier de progression en lecture
    start_index = int(f.read().strip()) # Lit le numéro du dernier joueur traité
  print(f"🔄 Reprise depuis le joueur {start_index + 1}/100") # Informe qu'on reprend la collecte là où elle s'était arrêtée
else: # Si aucun fichier de progression n'existe
  start_index = 0 # On repart du tout premier joueur

# Écrire l'en-tête du CSV seulement si on repart de zéro
FIELDNAMES = ["champion", "kills", "deaths", "assists", "victoire", "role", "match_id"] # Noms des colonnes du fichier CSV
if start_index == 0: # Si on démarre une nouvelle collecte (et non une reprise)
  with open(CSV_FILE, "w", newline="", encoding="utf-8") as f: # Ouvre (ou crée) le CSV en écriture, en effaçant le contenu existant
    writer = csv.DictWriter(f, fieldnames=FIELDNAMES) # Crée un écrivain CSV basé sur les colonnes définies
    writer.writeheader() # Écrit la ligne d'en-tête (les noms des colonnes) dans le CSV

# Partie 8 : La double boucle

 #La partie 8 parcourt les joueurs Challenger, récupère leurs matchs, et extrait les données de chaque participant pour les stocker.

# Récupérer l'id de match de chaque joueur
for i, player in enumerate(players): # Parcourt chaque joueur avec son index i

    if i < start_index:  # Sauter les joueurs déjà traités
      continue # Passe directement au joueur suivant

    print(f"joueur {i+1}/{len(players)}en cours...") # Affiche la progression de la collecte

    puuid = player["puuid"] # Récupère le puuid du joueur

    if not puuid: # Si le puuid est manquant ou introuvable
      continue  # si le puuid n'est pas trouvé , on passe au joueur qui suit

    time.sleep(1.2)  # Sans sleep → 100 requêtes en 5 secondes → Riot bloque ❌
#                      Avec sleep → 1 requête toutes les 1.2s  → Riot accepte ✅

    match_ids = get_matches(puuid, total=500)  # Récupération des ids des matchs

    if match_ids == [] and not puuid:  # Vérifie si c'est une erreur 401
      pass # Cas déjà couvert par le test 401 ci-dessous, rien à faire ici
    # Arrêt immédiat si la clé API est invalide
    if not match_ids: # Si aucun id de match n'a été récupéré
      # Tester si c'est bien une erreur 401 et pas juste 0 matchs
      test = requests.get( # Envoie une requête test avec un seul match demandé
        f"https://{REGION_MATCH}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?count=1", # URL de test
        headers=HEADERS # Envoie le badge d'authentification avec la requête test
      ).json() # Convertit la réponse de test en dictionnaire python
      if isinstance(test, dict) and test.get("status", {}).get("status_code") == 401: # Vérifie si l'erreur est bien un code 401 (clé API invalide/expirée)
        print("❌ Clé API expirée (401) — arrêt du script. Renouvelle ta clé et relance.")
        exit(1) # Arrête complètement le script

    # Récupérer les détails des matchs
    rows = []  # Lignes pour ce joueur uniquement
    for match_id in match_ids: # Parcourt chaque id de match du joueur
      time.sleep(1.2)  # Pause pour éviter le rate limit (429)
      match = get_match_details(match_id) # Récupère les détails complets du match
      if "info" not in match: # Si le match n'a pas pu être récupéré correctement
        continue  # Si erreur, on passe au match suivant
      participants = match["info"]["participants"] # Liste des 10 participants du match
      for p in participants: # Parcourt chaque participant du match
        rows.append({ # Ajoute une nouvelle ligne de données pour ce participant
           "champion": p["championName"], # Nom du champion joué
           "kills": p["kills"], # Nombre d'éliminations réalisées
           "deaths": p["deaths"], # Nombre de morts
           "assists": p["assists"], # Nombre d'assistances
           "victoire": 1 if p["win"] else 0, # 1 si le participant a gagné, 0 sinon
           "role": p["teamPosition"], # Rôle/poste joué (TOP, JUNGLE, MID, ADC, SUPPORT)
           "match_id": match_id # Id du match correspondant
        })

    # Sauvegarder les lignes de ce joueur immédiatement dans le CSV
    if rows: # S'il y a des données à sauvegarder pour ce joueur
      with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:  # "a" = append, ne repart pas de zéro
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES) # Crée un écrivain CSV basé sur les colonnes définies
        writer.writerows(rows) # Ajoute toutes les lignes de ce joueur dans le CSV
      print(f"  ✅ {len(rows)} lignes sauvegardées pour joueur {i+1}")

    # Sauvegarder la progression
    with open(PROGRESS_FILE, "w") as f: # Ouvre le fichier de progression en écriture
      f.write(str(i + 1))  # Prochain joueur à traiter

# Partie 9 : Fin de la collecte
# Les données ont été sauvegardées au fur et à mesure dans le CSV après chaque joueur

# Supprimer le fichier de progression — collecte terminée avec succès
if os.path.exists(PROGRESS_FILE): # Si le fichier de progression existe encore
  os.remove(PROGRESS_FILE) # Le supprime car la collecte s'est terminée avec succès

print(f"✅ Collecte terminée ! Données sauvegardées dans {CSV_FILE}") # Affiche un message final confirmant la fin de la collecte


