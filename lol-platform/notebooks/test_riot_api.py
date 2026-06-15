import requests
import os
from dotenv import load_dotenv

# Charger la clé API depuis le fichier .env
load_dotenv()
API_KEY = os.getenv("RIOT_API_KEY")
print("Clé chargée :", API_KEY)

# Tester la connexion avec Riot API
url = "https://euw1.api.riotgames.com/lol/status/v4/platform-data"

response = requests.get(url, headers={"X-Riot-Token": API_KEY})

# Afficher le résultat
if response.status_code == 200:
    print("✅ Connexion réussie avec Riot API !")
    print(response.json())
else:
    print(f"❌ Erreur : {response.status_code}")