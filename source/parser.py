from bs4 import BeautifulSoup


def clean_text(value):
    if not value:
        return ""
    return " ".join(value.strip().split())


def parse_campaign_list(html_content):
    """
    Extreu campanyes des de la home.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    campaigns = []
    seen_urls = set()

    # Buscar enllaços que semblin campanyes/catàlegs
    links = soup.find_all("a", href=True)

    for a in links:
        href = a["href"].strip()
        text = clean_text(a.get_text(" ", strip=True))

        if not href:
            continue

        # Completar URL relativa
        if href.startswith("/"):
            href = "https://es.privalia.com" + href

        # Heurística
        if "/catalog/" in href or "/gr/" in href:
            if href not in seen_urls and text:
                campaigns.append(
                    {
                        "name": text,
                        "url": href,
                        "sector": "",
                        "end_date": "",
                    }
                )
                seen_urls.add(href)

    return campaigns


def parse_product_list(html_content, campaign_data):
    """
    Extreu productes des del catàleg d'una campanya.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    products = []
    seen_urls = set()

    links = soup.find_all("a", href=True)

    for a in links:
        href = a["href"].strip()
        text = clean_text(a.get_text(" ", strip=True))

        if not href:
            continue

        if href.startswith("/"):
            href = "https://es.privalia.com" + href

        # Heurística: enllaços interns que semblin producte
        if href not in seen_urls and ("/product/" in href or "/p/" in href or "/gr/" in href):
            product = {
                "campaign_name": campaign_data.get("name", ""),
                "campaign_sector": campaign_data.get("sector", ""),
                "campaign_end_date": campaign_data.get("end_date", ""),
                "product_name": text or "Sense nom",
                "product_url": href,
            }
            products.append(product)
            seen_urls.add(href)

    return products


def parse_product_detail_page(html_content, base_product_data):
    """
    Extreu informació de detall d'un producte.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    detail_product = base_product_data.copy()

    # Nom del producte
    if not detail_product.get("product_name") or detail_product.get("product_name") == "Sense nom":
        h1 = soup.find("h1")
        if h1:
            detail_product["product_name"] = clean_text(h1.get_text())

    # Descripció
    meta_desc = soup.find("meta", attrs={"name": "description"})
    detail_product["description"] = (
        meta_desc.get("content", "") if meta_desc else ""
    )

    # Color: placeholder
    detail_product["color"] = ""

    # Talles disponibles: placeholder
    detail_product["available_sizes"] = ""

    # Preus: placeholders
    detail_product["original_price"] = ""
    detail_product["discount_price"] = ""
    detail_product["discount_percentage"] = ""

    return detail_product