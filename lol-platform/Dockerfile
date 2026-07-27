# Image de base : Python 3.13 en version allégée (moins lourde à télécharger)
FROM python:3.13-slim

# Dossier de travail à l'intérieur du conteneur
WORKDIR /app

# On copie d'abord uniquement requirements.txt pour profiter du cache Docker :
# si ce fichier ne change pas, Docker ne réinstalle pas les librairies à chaque build
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# On copie ensuite tout le reste du projet (code, data/processed, models...)
COPY . .

# Ports utilisés par l'API (8000) et par Streamlit (8501)
EXPOSE 8000 8501

# Commande par défaut si l'image est déployée seule (ex: Render, Railway) sans docker-compose.
# Ces hébergeurs imposent leur propre port via la variable $PORT ; on utilise 8000 si elle n'existe pas.
# docker-compose.yml redéfinit sa propre "command:" pour les 2 services locaux, donc pas de conflit.
CMD ["sh", "-c", "uvicorn backend.api:app --host 0.0.0.0 --port ${PORT:-8000}"]
