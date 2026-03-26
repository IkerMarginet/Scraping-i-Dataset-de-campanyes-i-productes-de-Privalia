from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re

BASE_DOMAIN = "https://es.privalia.com"


def clean_text(value):
    if not value:
        return ""
    return " ".join(value.strip().split())


def absolute_url(href):
    if not href:
        return ""
    return urljoin(BASE_DOMAIN, href)


def is_valid_privalia_url(url):
    if not url:
        return False
    parsed = urlparse(url)
    return "privalia.com" in parsed.netloc


def is_bad_url(url):
    """
    Filtra urls que clarament NO són campanyes ni productes.
    """
    if not url:
        return True

    bad_patterns = [
        "/myaccount",
        "/my-orders",
        "/communications",
        "/my-notifications",
        "/profile",
        "/login",
        "/logout",
        "/register",
        "/help",
        "/faq",
        "/contact",
        "/legal",
        "/privacy",
        "/cookies",
        "/terms",
        "/wishlist",
        "/cart",
        "/basket",
        "/checkout",
        "/search",
        "/brands",
        "/invite",
        "/storelocator",
    ]

    url_lower = url.lower()

    if "#" in url_lower:
        return True

    for pattern in bad_patterns:
        if pattern in url_lower:
            return True

    return False


def looks_like_campaign_url(url):
    """
    Heurística per trobar campanyes reals.
    """
    if not url or not is_valid_privalia_url(url) or is_bad_url(url):
        return False

    url_lower = url.lower()

    # Campanyes i catàlegs solen anar per aquí
    good_patterns = [
        "/catalog/",
        "/campaign/",
        "/sale/",
        "/evento/",
        "/brand/",
        "/outlet/",
    ]

    for pattern in good_patterns:
        if pattern in url_lower:
            return True

    return False


def looks_like_product_url(url):
    """
    Heurística per trobar fitxes de producte.
    """
    if not url or not is_valid_privalia_url(url) or is_bad_url(url):
        return False

    url_lower = url.lower()

    good_patterns = [
        "/product/",
        "/p/",
        "/producto/",
        "/detail/",
    ]

    for pattern in good_patterns:
        if pattern in url_lower:
            return True

    return False


def extract_possible_end_date(text):
    if not text:
        return ""

    patterns = [
        r"acaba en\s+[^|]+",
        r"termina en\s+[^|]+",
        r"finaliza en\s+[^|]+",
        r"hasta\s+[^|]+",
    ]

    text_lower = text.lower()
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            return clean_text(match.group(0))

    return ""


def parse_campaign_list(html_content):
    """
    Extreu la llista de campanyes reals des de la home o landing principal.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    campaigns = []
    seen_urls = set()

    links = soup.find_all("a", href=True)

    for a in links:
        href = clean_text(a.get("href", ""))
        full_url = absolute_url(href)

        if not looks_like_campaign_url(full_url):
            continue

        # Text principal del link
        name = clean_text(a.get_text(" ", strip=True))

        # Si el text del link és buit, provar amb imatge o atributs
        if not name:
            img = a.find("img")
            if img:
                name = clean_text(img.get("alt", ""))

        if not name:
            name = clean_text(a.get("title", ""))

        # Evitar links sense nom mínimament útil
        if not name or len(name) < 2:
            continue

        # Intentar recuperar text proper per sector o data
        container_text = ""
        parent = a.parent
        if parent:
            container_text = clean_text(parent.get_text(" ", strip=True))

        end_date = extract_possible_end_date(container_text)

        campaign = {
            "name": name,
            "url": full_url,
            "sector": "",
            "end_date": end_date,
        }

        if full_url not in seen_urls:
            campaigns.append(campaign)
            seen_urls.add(full_url)

    return campaigns


def parse_product_list(html_content, campaign_data):
    """
    Extreu productes d'una campanya.
    Només accepta urls que semblin realment de producte.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    products = []
    seen_urls = set()

    links = soup.find_all("a", href=True)

    for a in links:
        href = clean_text(a.get("href", ""))
        full_url = absolute_url(href)

        if not looks_like_product_url(full_url):
            continue

        name = clean_text(a.get_text(" ", strip=True))

        if not name:
            img = a.find("img")
            if img:
                name = clean_text(img.get("alt", ""))

        if not name:
            name = clean_text(a.get("title", ""))

        if not name:
            name = "Sense nom"

        product = {
            "campaign_name": campaign_data.get("name", ""),
            "campaign_sector": campaign_data.get("sector", ""),
            "campaign_end_date": campaign_data.get("end_date", ""),
            "product_name": name,
            "product_url": full_url,
        }

        if full_url not in seen_urls:
            products.append(product)
            seen_urls.add(full_url)

    return products


def parse_price(text):
    if not text:
        return ""

    text = text.replace("\xa0", " ")
    match = re.search(r"(\d+[.,]?\d*)\s*€", text)
    if match:
        return match.group(1).replace(",", ".")
    return ""


def parse_discount(text):
    if not text:
        return ""

    match = re.search(r"-\s*\d+\s*%", text)
    if match:
        return match.group(0).replace(" ", "")
    return ""


def parse_product_detail_page(html_content, base_product_data):
    """
    Extreu informació de detall d'un producte.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    detail_product = base_product_data.copy()

    # Nom del producte
    if not detail_product.get("product_name") or detail_product["product_name"] == "Sense nom":
        h1 = soup.find("h1")
        if h1:
            detail_product["product_name"] = clean_text(h1.get_text())

    # Descripció
    description = ""

    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc and meta_desc.get("content"):
        description = clean_text(meta_desc.get("content"))

    if not description:
        possible_desc = soup.find(
            lambda tag: tag.name in ["div", "p", "span"]
            and tag.get_text(strip=True)
            and len(clean_text(tag.get_text(" ", strip=True))) > 40
        )
        if possible_desc:
            description = clean_text(possible_desc.get_text(" ", strip=True))

    detail_product["description"] = description

    # Preus: buscar text general de la pàgina
    page_text = clean_text(soup.get_text(" ", strip=True))
    prices = re.findall(r"(\d+[.,]?\d*)\s*€", page_text)

    detail_product["original_price"] = ""
    detail_product["discount_price"] = ""
    detail_product["discount_percentage"] = parse_discount(page_text)

    if len(prices) >= 2:
        detail_product["original_price"] = prices[0].replace(",", ".")
        detail_product["discount_price"] = prices[1].replace(",", ".")
    elif len(prices) == 1:
        detail_product["discount_price"] = prices[0].replace(",", ".")

    # Color
    color = ""
    color_patterns = [
        r"color[:\s]+([a-zA-ZÀ-ÿ0-9 \-]+)",
        r"colores[:\s]+([a-zA-ZÀ-ÿ0-9 \-,]+)",
    ]

    for pattern in color_patterns:
        match = re.search(pattern, page_text, flags=re.IGNORECASE)
        if match:
            color = clean_text(match.group(1))
            break

    detail_product["color"] = color

    # Talles: molt heurístic
    sizes_found = []
    common_sizes = [
        "XS", "S", "M", "L", "XL", "XXL",
        "36", "37", "38", "39", "40", "41", "42", "43", "44", "45"
    ]

    for size in common_sizes:
        if re.search(rf"\b{re.escape(size)}\b", page_text):
            sizes_found.append(size)

    detail_product["available_sizes"] = ", ".join(sorted(set(sizes_found)))

    return detail_product