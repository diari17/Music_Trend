import os
from dotenv import load_dotenv

load_dotenv()

# Credentials Last.fm
LASTFM_API_KEY       = os.getenv("LASTFM_API_KEY")
LASTFM_SHARED_SECRET = os.getenv("LASTFM_SHARED_SECRET")
LASTFM_BASE_URL      = "https://ws.audioscrobbler.com/2.0/"

# Dossier de sauvegarde des données brutes
RAW_DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "raw")

# Paramètres d'extraction
EXTRACT_LIMIT = 50       # résultats par page
NB_PAGES      = 5        # pages à paginer par endpoint

# Pays ciblés
COUNTRIES = ["France", "United States", "United Kingdom", "Senegal"]

# Genres / tags musicaux à analyser
TARGET_TAGS = [
    "pop", "hip-hop", "rock", "afrobeats",
    "electronic", "jazz", "rnb", "latin",
    "soul", "dancehall"
]