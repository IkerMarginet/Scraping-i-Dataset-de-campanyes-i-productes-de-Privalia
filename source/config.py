import os

BASE_URL = "https://es.privalia.com/gr/home/default"
LOGIN_URL = "https://es.privalia.com/gr/home/default" # The login modal appears on the homepage

# Credenciales para el login (asegúrate de no subirlas a repositorios públicos)
PRIVALIA_EMAIL = os.getenv("PRIVALIA_EMAIL", "tu_email@ejemplo.com")
PRIVALIA_PASSWORD = os.getenv("PRIVALIA_PASSWORD", "tu_password")

# User-Agent explícito (es demana validar i gestionar aquest aspecte)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

# Límits per no banyar-se o tardar hores en provar-ho
MAX_CAMPAIGNS_TO_VISIT = 3
MAX_PRODUCTS_PER_CAMPAIGN_TO_VISIT = 5

REQUEST_DELAY_SECONDS = 3
TIMEOUT_SECONDS = 20

# Configuración de salida
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dataset")
OUTPUT_CSV = os.path.join(DATA_DIR, "privalia_dataset.csv")

# Asegurar que el directorio dataset existe
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
