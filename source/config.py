import os

BASE_URL = "https://es.privalia.com/gr/home/default"
LOGIN_URL = "https://es.privalia.com/gr/home/default"

# Millor posar les credencials com a variables d'entorn
# Windows PowerShell:
# $env:PRIVALIA_EMAIL="tu_correo"
# $env:PRIVALIA_PASSWORD="tu_password"
PRIVALIA_EMAIL = os.getenv("PRIVALIA_EMAIL", "uoctests00@gmail.com")
PRIVALIA_PASSWORD = os.getenv("PRIVALIA_PASSWORD", "T8asdkj.Lksdo'?")

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)

MAX_CAMPAIGNS_TO_VISIT = 3
MAX_PRODUCTS_PER_CAMPAIGN_TO_VISIT = 5

REQUEST_DELAY_SECONDS = 3
TIMEOUT_SECONDS = 20

# Carpeta dataset al nivell arrel del projecte
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "dataset")
OUTPUT_CSV = os.path.join(DATA_DIR, "privalia_dataset.csv")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

