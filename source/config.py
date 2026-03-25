BASE_URL = "https://www.privalia.com/"
START_URLS = [
    "https://es.privalia.com/gr/catalog/897409"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

REQUEST_DELAY_SECONDS = 2
TIMEOUT_SECONDS = 20
MAX_PRODUCTS = 20
OUTPUT_CSV = "dataset/privalia_products_raw.csv"