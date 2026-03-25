from config import START_URLS, HEADERS, TIMEOUT_SECONDS, BASE_URL
import requests
from bs4 import BeautifulSoup

def main():
    url = START_URLS[0]
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT_SECONDS)
    r.raise_for_status()

    html = r.text
    print("STATUS:", r.status_code)
    print("LONGITUD HTML:", len(html))

    soup = BeautifulSoup(html, "lxml")

    # mirar el títol de la pàgina
    title = soup.title.get_text(strip=True) if soup.title else "Sense títol"
    print("TITLE:", title)

    # imprimir alguns links
    links = []
    for a in soup.select("a[href]"):
        href = a.get("href")
        if href:
            links.append(href)

    print("Número total de links trobats:", len(links))
    print("Primers 30 links:")
    for link in links[:30]:
        print(link)

if __name__ == "__main__":
    main()