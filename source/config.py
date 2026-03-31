import os

BASE_URL = "https://es.privalia.com/gr/home/default"
LOGIN_URL = "https://es.privalia.com/gr/home/default"
BASE_DOMAIN = "https://es.privalia.com"

PRIVALIA_EMAIL = os.getenv("PRIVALIA_EMAIL", "uoctests00@gmail.com")
PRIVALIA_PASSWORD = os.getenv("PRIVALIA_PASSWORD", "T8asdkj.Lksdo'?")

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)

MAX_CAMPAIGNS_TO_VISIT = 5
MAX_SUBPAGES_PER_CAMPAIGN = 5
MAX_PRODUCTS_PER_CAMPAIGN_TO_VISIT = 10

REQUEST_DELAY_SECONDS = 1
TIMEOUT_SECONDS = 20

# Carpeta on hi ha aquest fitxer: source/
SOURCE_DIR = os.path.dirname(os.path.abspath(__file__))

# Arrel del projecte: una carpeta per sobre de source/
PROJECT_ROOT = os.path.dirname(SOURCE_DIR)

# Carpetes fora de source/
DATA_DIR = os.path.join(PROJECT_ROOT, "dataset")
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")
DEBUG_DIR = os.path.join(DOCS_DIR, "imatges")

CAMPAIGNS_CSV = os.path.join(DATA_DIR, "privalia_campaigns.csv")
PRODUCTS_CSV = os.path.join(DATA_DIR, "privalia_products.csv")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(DOCS_DIR, exist_ok=True)
os.makedirs(DEBUG_DIR, exist_ok=True)