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

def get_challengers_players():
 # ():la fct n'a besoin d'aucune information pour fonctionner , (:):c.a.d le code de la fct commence à la ligne suivante
 # Comme une rectte que j'écris et j'ulitiserai pas mal de fois aprés

 url = f"https://{REGION}.api.riotgames.com/lol/league/v4/challengerleagues/by-queue/RANKED_SOLO_5x5"

 # f" ": c'est à dire que le texte à l'intérieur peut contenir des variables qui seront remplacé automatiquement par leurs valeurs attribués avant
 # /lol/league/v4/challengerleagues/by-queue: lien pour avoir les joueurs challengers
 # RANKED_SOLO_5x5 : Le code Riot pour les paries solo duo uniquement

 response= requests.get(url , headers=HEADERS) # la réponse sera une demande des données de  lien des matchs avec mon badge

 data=response.json() # les données recues(data) seront laréponse qui sera transformée en dictionnaire python lisible

 if "status" in data:
   raise Exception(f"❌ Erreur API Riot: {data['status']} — Vérifie ta clé API dans .env")

 players = data["entries"] # entries(mot clé de riot) contient des infos de joueurs:summoner Id ,...

 print(f"✅ {len(players)} joueurs Challenger trouvés") # affiche le nombre de joueurs trouvés , {len(players)}: compte le nombre de joueurs 

 return players # la recette est terminé , il sera servi à table

# Partie 4 : Récupérer le PUUID d'un joueur

#summonerId  →  identifiant interne Riot (ancien système)
#PUUID       →  identifiant universel du joueur (nouveau système)

def get_puuid(summoner_id): #() ne sont pas vide , c.a.d on doit donner l'information qui est dans () pour que la fct fonctionne
 
 url = f"https://{REGION}.api.riotgames.com/lol/summoner/v4/summoners/{summoner_id}"

 response = requests.get(url , headers=HEADERS)

 return response.json().get("puuid") # .get() est plus sécurisé — si Riot ne renvoie pas de PUUID, le programme ne plante pas au contraire de get []
#On en a besoin car l'endpoint des matchs n'accepte que le PUUID, pas le summonerId.

# Partie 5 : Récupérer la liste des ids(identifiants) des matchs

def get_matches(puuid, total=500):

 # Riot limite count à 100 par requête → on fait plusieurs requêtes avec start pour paginer
 all_ids = []
 start = 0
 while len(all_ids) < total:
   count = min(100, total - len(all_ids))  # max 100 par requête
   url = f"https://{REGION_MATCH}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start={start}&count={count}&queue=420"
   response = requests.get(url, headers=HEADERS)
   data = response.json()
   if isinstance(data, dict) and "status" in data:
     print(f"⚠️ Erreur API get_matches: {data['status']}")
     break
   if not data:  # Plus de matchs disponibles
     break
   all_ids.extend(data)
   start += count
   time.sleep(1.2)  # Pause entre chaque requête pour éviter le rate limit
 return all_ids

# Partie 6 : Récupérer les détails du match

def get_match_details(match_id, retries=3):

 url = f"https://{REGION_MATCH}.api.riotgames.com/lol/match/v5/matches/{match_id}"

 for attempt in range(retries):
   try:
     response = requests.get(url, headers=HEADERS)
     data = response.json()
     if isinstance(data, dict) and "status" in data:
       print(f"⚠️ Erreur API get_match_details: {data['status']}")
       return {}
     return data
   except Exception as e:
     print(f"⚠️ Connexion échouée ({attempt+1}/{retries}) pour {match_id} : {e}")
     time.sleep(3)  # Attendre 3s avant de réessayer

 return {}  # Après 3 tentatives, on abandonne ce match

# Partie 7 : La collecte principale

players = get_challengers_players()

players = players[:100]  # Prends les 100 premiers joueurs

# Reprendre depuis le dernier joueur traité en cas d'interruption
os.makedirs("data/raw", exist_ok=True)
PROGRESS_FILE = "data/raw/progress.txt"
CSV_FILE = "data/raw/matches.csv"

if os.path.exists(PROGRESS_FILE):
  with open(PROGRESS_FILE) as f:
    start_index = int(f.read().strip())
  print(f"🔄 Reprise depuis le joueur {start_index + 1}/100")
else:
  start_index = 0

# Écrire l'en-tête du CSV seulement si on repart de zéro
FIELDNAMES = ["champion", "kills", "deaths", "assists", "victoire", "role", "match_id"]
if start_index == 0:
  with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
    writer.writeheader()

# Partie 8 : La double boucle

 #La partie 8 parcourt les joueurs Challenger, récupère leurs matchs, et extrait les données de chaque participant pour les stocker.

# Récupérer l'id de match de chaque joueur
for i, player in enumerate(players):

    if i < start_index:  # Sauter les joueurs déjà traités
      continue

    print(f"joueur {i+1}/{len(players)}en cours...")

    puuid = player["puuid"]

    if not puuid:
      continue  # si le puuid n'est pas trouvé , on passe au joueur qui suit

    time.sleep(1.2)  # Sans sleep → 100 requêtes en 5 secondes → Riot bloque ❌
#                      Avec sleep → 1 requête toutes les 1.2s  → Riot accepte ✅

    match_ids = get_matches(puuid, total=500)  # Récupération des ids des matchs

    if match_ids == [] and not puuid:  # Vérifie si c'est une erreur 401
      pass
    # Arrêt immédiat si la clé API est invalide
    if not match_ids:
      # Tester si c'est bien une erreur 401 et pas juste 0 matchs
      test = requests.get(
        f"https://{REGION_MATCH}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?count=1",
        headers=HEADERS
      ).json()
      if isinstance(test, dict) and test.get("status", {}).get("status_code") == 401:
        print("❌ Clé API expirée (401) — arrêt du script. Renouvelle ta clé et relance.")
        exit(1)

    # Récupérer les détails des matchs
    rows = []  # Lignes pour ce joueur uniquement
    for match_id in match_ids:
      time.sleep(1.2)  # Pause pour éviter le rate limit (429)
      match = get_match_details(match_id)
      if "info" not in match:
        continue  # Si erreur, on passe au match suivant
      participants = match["info"]["participants"]
      for p in participants:
        rows.append({
           "champion": p["championName"],
           "kills": p["kills"],
           "deaths": p["deaths"],
           "assists": p["assists"],
           "victoire": 1 if p["win"] else 0,
           "role": p["teamPosition"],
           "match_id": match_id
        })

    # Sauvegarder les lignes de ce joueur immédiatement dans le CSV
    if rows:
      with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:  # "a" = append, ne repart pas de zéro
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writerows(rows)
      print(f"  ✅ {len(rows)} lignes sauvegardées pour joueur {i+1}")

    # Sauvegarder la progression
    with open(PROGRESS_FILE, "w") as f:
      f.write(str(i + 1))  # Prochain joueur à traiter

# Partie 9 : Fin de la collecte
# Les données ont été sauvegardées au fur et à mesure dans le CSV après chaque joueur

# Supprimer le fichier de progression — collecte terminée avec succès
if os.path.exists(PROGRESS_FILE):
  os.remove(PROGRESS_FILE)

print(f"✅ Collecte terminée ! Données sauvegardées dans {CSV_FILE}")



