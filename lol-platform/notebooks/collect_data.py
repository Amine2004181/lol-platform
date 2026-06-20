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

def get_matches(puuid, count=10):
 
 url = f"https://{REGION_MATCH}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?count={count}&queue=420"

# /ids :On veut juste les identifiants des matchs, pas tous les détails
# ? :Début des paramètres de la requête
# count={count}Remplacé par 10 — le nombre de matchs voulus
# & :Séparateur entre deux paramètres
# queue=420Le code Riot pour les parties classées Solo/Duo uniquement

 response= requests.get(url , headers=HEADERS)

 return response.json()

# Partie 6 : Récupérer les détails du match

def get_match_details(match_id):
 
 url = f"https://{REGION_MATCH}.api.riotgames.com/lol/match/v5/matches/{match_id}"

 response=requests.get(url, headers=HEADERS)

 return response.json()

# Partie 7 : La collecte principale

players =  get_challengers_players()

players= players[ :100]# Prends les 100 premiers joueurs 

rows = [] # prépares une liste  vide à l'instant qui sera rempli au fur et à mesur après la récupération des données
# rows : la variable qui va stocker toutes les données

# Partie 8 : La double boucle

 #La partie 8 parcourt les joueurs Challenger, récupère leurs matchs, et extrait les données de chaque participant pour les stocker.
 #À la fin de la partie 8, rows contient 1000 lignes comme ça :
#champion  | kills | deaths | assists | victoire | role   | match_id
#Zed       | 10    | 2      | 5       | 1        | MIDDLE | EUW1_123
#Lux       | 3     | 8      | 12      | 0        | MIDDLE | EUW1_123
#Jinx      | 8     | 3      | 7       | 1        | BOTTOM | EUW1_123


# Récupérer l'id de match de chaque joueur 
for i , player in enumerate(players):
    
    print(f"joueur {i+1}/{len(players)}en cours...")

 #Résultat : Joueur 1/10 en cours...
 #           Joueur 2/10 en cours...
 #            ...

    puuid= player["puuid"]

    if not puuid:
      continue  #si le puuid n'est pas trouvé , on passe au joueur qui suit

    time.sleep(1.2) #Sans sleep → 100 requêtes en 5 secondes → Riot bloque ❌
#                   Avec sleep → 1 requête toutes les 1.2s  → Riot accepte ✅

    match_ids=get_matches(puuid , count=100)  #Résultat final : Récupération des id des matchs des joueurs

#Récupérer les détails des match à partir des ids des matchs
    for match_id in match_ids:
      match=get_match_details(match_id)
      if"info" not in match:
        continue #Si Riot renvoie une erreur pour un match (match supprimé, erreur réseau...), on passe au suivant sans planter ✅
      participants= match["info"]["participants"] #on stock tous les infos des joueurs dans ce compatiment qui est appelés participant , et on l'a mis dans infos qui est elle meme un compartiment dans les données de match
      for p in participants:
        rows.append({ #Ajoute un élément à la fin de la liste rows
           "champion": p["championName"],
           "kills": p["kills"],
           "deaths": p["deaths"],
           "assists": p["assists"],
           "victoire": 1 if p["win"] else 0,
           "role": p["teamPosition"],
           "match_id": match_id
        })

# Partie 9 : Sauvegarder en CSV (les données extraits seront sauvegardés grace au fichier csv pour nourir l'IA)

os.makedirs("data/raw",exist_ok=True) # makedirs :Crée un dossier et ses parents si nécessaire
#                                     "data/raw"Le chemin du dossier à créer
#                                      exist_ok=True Si le dossier existe déjà → ne plante pas, continue
with open("data/raw/matches.csv", "w", newline="", encoding="utf-8") as f:
  #with :Ouvre quelque chose et le ferme automatiquement à la fin
  #open(...) :Ouvre ou crée un fichier
  #"data/raw/matches.csv" :Le chemin et nom du fichier à créer
  #"w" :Mode write — écriture (si le fichier existe, il est écrasé)
  # newline="" :Evite les lignes vides entre chaque ligne dans le CSV
  #encoding="utf-8" :Supporte les caractères spéciaux (accents, arabe...)
  #as f :Donne le nom f au fichier ouvert pour l'utiliser ensuite
  writer= csv.DictWriter(f,fieldnames=rows[0].keys())
  #writer :Variable qui représente l'outil d'écriture CSV
  # csv.DictWriter :Un outil qui écrit des dictionnaires dans un fichier CSV
  # f :Le fichier ouvert juste avant
  # fieldnames :Les noms des colonnes du CSV
  # rows[0].keys() :Extrait les noms des colonnes depuis le premier élément de rows
  writer.writeheader #Écrit la première ligne du CSV — les noms des colonnes
  writer.writerows(rows) #Écrit toutes les lignes de rows dans le CSV
  print(f"✅ {len(rows)} lignes sauvegardées dans data/raw/matches.csv")



