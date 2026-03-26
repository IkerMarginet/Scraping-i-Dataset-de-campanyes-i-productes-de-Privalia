import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

BASE_DOMAIN = "https://es.privalia.com"


def clean_text(value):
    if not value:
        return ""
    return " ".join(str(value).strip().split())


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
        "/member",
        "/club",
    ]

    url_lower = url.lower()

    if "#" in url_lower:
        return True

    return any(pattern in url_lower for pattern in bad_patterns)


def looks_like_campaign_url(url):
    if not url or not is_valid_privalia_url(url) or is_bad_url(url):
        return False

    url_lower = url.lower()
    good_patterns = [
        "/catalog/",
        "/campaign/",
        "/sale/",
        "/evento/",
        "/brand/",
        "/outlet/",
    ]
    return any(pattern in url_lower for pattern in good_patterns)


def looks_like_product_url(url):
    if not url or not is_valid_privalia_url(url) or is_bad_url(url):
        return False

    url_lower = url.lower()
    good_patterns = [
        "/product/",
        "/p/",
        "/producto/",
        "/detail/",
    ]
    return any(pattern in url_lower for pattern in good_patterns)


def extract_possible_end_date(text):
    if not text:
        return ""

    patterns = [
        r"(acaba en\s+[^|]+)",
        r"(termina en\s+[^|]+)",
        r"(finaliza en\s+[^|]+)",
        r"(hasta\s+[^|]+)",
        r"(ends in\s+[^|]+)",
    ]

    text_lower = text.lower()
    for pattern in patterns:
        match = re.search(pattern, text_lower, flags=re.IGNORECASE)
        if match:
            return clean_text(match.group(1))

    return ""


def parse_discount(text):
    if not text:
        return ""
    match = re.search(r"(-\s*\d+\s*%)", text)
    if match:
        return clean_text(match.group(1)).replace(" ", "")
    return ""


def get_text_from_node(node):
    if not node:
        return ""
    return clean_text(node.get_text(" ", strip=True))


def get_attr(node, attr_name):
    if not node:
        return ""
    return clean_text(node.get(attr_name, ""))


def find_first(node, selectors):
    for selector in selectors:
        found = node.select_one(selector)
        if found:
            return found
    return None


def find_all_candidates(soup, selectors):
    seen = set()
    results = []

    for selector in selectors:
        for node in soup.select(selector):
            node_id = id(node)
            if node_id not in seen:
                results.append(node)
                seen.add(node_id)

    return results


def extract_campaign_name_from_card(card, anchor):
    name_selectors = [
        "[data-testid*='title']",
        "[data-testid*='name']",
        "[class*='title']",
        "[class*='name']",
        "[class*='brand']",
        "h2",
        "h3",
        "h4",
        "strong",
        "span",
        "img[alt]",
    ]

    for selector in name_selectors:
        found = card.select_one(selector)
        if found:
            if found.name == "img":
                alt = get_attr(found, "alt")
                if alt and len(alt) >= 2:
                    return alt
            text = get_text_from_node(found)
            if text and len(text) >= 2:
                return text

    if anchor:
        img = anchor.find("img")
        if img:
            alt = get_attr(img, "alt")
            if alt and len(alt) >= 2:
                return alt

        title = get_attr(anchor, "title")
        if title and len(title) >= 2:
            return title

        anchor_text = get_text_from_node(anchor)
        if anchor_text and len(anchor_text) >= 2:
            return anchor_text

    return ""


def extract_product_name_from_card(card, anchor):
    name_selectors = [
        "[data-testid*='product']",
        "[data-testid*='title']",
        "[data-testid*='name']",
        "[class*='product'] [class*='name']",
        "[class*='product'] [class*='title']",
        "[class*='name']",
        "[class*='title']",
        "h2",
        "h3",
        "h4",
        "strong",
        "img[alt]",
    ]

    for selector in name_selectors:
        found = card.select_one(selector)
        if found:
            if found.name == "img":
                alt = get_attr(found, "alt")
                if alt and len(alt) >= 2:
                    return alt
            text = get_text_from_node(found)
            if text and len(text) >= 2:
                return text

    if anchor:
        img = anchor.find("img")
        if img:
            alt = get_attr(img, "alt")
            if alt and len(alt) >= 2:
                return alt

        title = get_attr(anchor, "title")
        if title and len(title) >= 2:
            return title

        anchor_text = get_text_from_node(anchor)
        if anchor_text and len(anchor_text) >= 2:
            return anchor_text

    return ""


def extract_sector_from_card(card):
    sector_selectors = [
        "[data-testid*='category']",
        "[data-testid*='sector']",
        "[class*='category']",
        "[class*='sector']",
        "[class*='department']",
    ]

    for selector in sector_selectors:
        node = card.select_one(selector)
        text = get_text_from_node(node)
        if text:
            return text

    return ""


def extract_end_date_from_card(card):
    date_selectors = [
        "[data-testid*='end']",
        "[data-testid*='date']",
        "[class*='end']",
        "[class*='date']",
        "[class*='deadline']",
        "time",
    ]

    for selector in date_selectors:
        node = card.select_one(selector)
        text = get_text_from_node(node)
        if text:
            possible = extract_possible_end_date(text) or text
            return clean_text(possible)

    card_text = get_text_from_node(card)
    return extract_possible_end_date(card_text)


def parse_campaign_list(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    campaigns = []
    seen_urls = set()

    campaign_card_selectors = [
        "[data-testid*='campaign']",
        "[data-testid*='catalog']",
        "[data-testid*='sale']",
        "[class*='campaign-card']",
        "[class*='campaignCard']",
        "[class*='catalog-card']",
        "[class*='catalogCard']",
        "[class*='sale-card']",
        "[class*='saleCard']",
        "[class*='brand-card']",
        "[class*='brandCard']",
        "article",
        "section a[href*='/catalog/']",
        "section a[href*='/campaign/']",
        "div a[href*='/catalog/']",
        "div a[href*='/campaign/']",
    ]

    candidate_cards = find_all_candidates(soup, campaign_card_selectors)

    if not candidate_cards:
        candidate_cards = soup.find_all("a", href=True)

    for card in candidate_cards:
        anchor = card if getattr(card, "name", None) == "a" else card.find("a", href=True)
        if not anchor:
            continue

        href = clean_text(anchor.get("href", ""))
        full_url = absolute_url(href)

        if not looks_like_campaign_url(full_url):
            continue

        name = extract_campaign_name_from_card(card, anchor)
        if not name or len(name) < 2:
            continue

        sector = extract_sector_from_card(card)
        end_date = extract_end_date_from_card(card)

        if full_url in seen_urls:
            continue

        campaigns.append(
            {
                "name": name,
                "url": full_url,
                "sector": sector,
                "end_date": end_date,
            }
        )
        seen_urls.add(full_url)

    return campaigns


def parse_product_list(html_content, campaign_data):
    soup = BeautifulSoup(html_content, "html.parser")
    products = []
    seen_urls = set()

    product_card_selectors = [
        "[data-testid*='product']",
        "[data-testid*='grid-item']",
        "[data-testid*='item']",
        "[class*='product-card']",
        "[class*='productCard']",
        "[class*='product-item']",
        "[class*='productItem']",
        "[class*='grid-item']",
        "[class*='gridItem']",
        "article",
        "li",
        "div",
    ]

    candidate_cards = find_all_candidates(soup, product_card_selectors)

    if not candidate_cards:
        candidate_cards = soup.find_all("a", href=True)

    for card in candidate_cards:
        anchor = card if getattr(card, "name", None) == "a" else card.find("a", href=True)
        if not anchor:
            continue

        href = clean_text(anchor.get("href", ""))
        full_url = absolute_url(href)

        if not looks_like_product_url(full_url):
            continue

        if full_url in seen_urls:
            continue

        name = extract_product_name_from_card(card, anchor)
        if not name:
            continue

        products.append(
            {
                "campaign_name": campaign_data.get("name", ""),
                "campaign_sector": campaign_data.get("sector", ""),
                "campaign_end_date": campaign_data.get("end_date", ""),
                "product_name": name,
                "product_url": full_url,
                "original_price": "",
                "discount_price": "",
                "discount_percentage": "",
                "color": "",
                "available_sizes": "",
                "description": "",
            }
        )
        seen_urls.add(full_url)

    return products


def extract_name_from_detail(soup, fallback_name=""):
    selectors = [
        "h1",
        "[data-testid*='product-name']",
        "[data-testid*='title']",
        "[class*='product-name']",
        "[class*='productName']",
        "[class*='title']",
    ]

    node = find_first(soup, selectors)
    if node:
        text = get_text_from_node(node)
        if text:
            return text

    return fallback_name


def extract_description_from_detail(soup):
    selectors = [
        "meta[name='description']",
        "[data-testid*='description']",
        "[class*='description']",
        "[class*='details']",
        "[class*='product-description']",
        "[class*='productDescription']",
    ]

    for selector in selectors:
        node = soup.select_one(selector)
        if not node:
            continue

        if node.name == "meta":
            content = get_attr(node, "content")
            if content:
                return content
        else:
            text = get_text_from_node(node)
            if text and len(text) >= 20:
                return text

    possible_desc = soup.find(
        lambda tag: tag.name in ["div", "p", "span"]
        and tag.get_text(strip=True)
        and len(clean_text(tag.get_text(" ", strip=True))) > 50
    )
    if possible_desc:
        return clean_text(possible_desc.get_text(" ", strip=True))

    return ""


def extract_prices_from_detail(soup):
    selectors_price_block = [
        "[data-testid*='price']",
        "[class*='price']",
        "[class*='pricing']",
        "[class*='discount']",
        "[class*='sale']",
    ]

    price_texts = []
    for selector in selectors_price_block:
        for node in soup.select(selector):
            text = get_text_from_node(node)
            if text and "€" in text:
                price_texts.append(text)

    page_text = clean_text(soup.get_text(" ", strip=True))
    all_text = " | ".join(price_texts) if price_texts else page_text

    prices = re.findall(r"(\d+[.,]?\d*)\s*€", all_text)
    prices = [p.replace(",", ".") for p in prices]

    original_price = ""
    discount_price = ""
    discount_percentage = parse_discount(all_text)

    unique_prices = []
    for price in prices:
        if price not in unique_prices:
            unique_prices.append(price)

    if len(unique_prices) >= 2:
        numeric_prices = []
        for p in unique_prices:
            try:
                numeric_prices.append(float(p))
            except ValueError:
                pass

        if len(numeric_prices) >= 2:
            original_price = str(max(numeric_prices))
            discount_price = str(min(numeric_prices))
        else:
            original_price = unique_prices[0]
            discount_price = unique_prices[1]
    elif len(unique_prices) == 1:
        discount_price = unique_prices[0]

    return original_price, discount_price, discount_percentage


def extract_color_from_detail(soup):
    selectors = [
        "[data-testid*='color']",
        "[class*='color']",
        "[class*='variant']",
    ]

    for selector in selectors:
        for node in soup.select(selector):
            text = get_text_from_node(node)
            if not text:
                continue

            match = re.search(
                r"(?:color|colores)[:\s]+([a-zA-ZÀ-ÿ0-9 \-/,]+)",
                text,
                flags=re.IGNORECASE,
            )
            if match:
                return clean_text(match.group(1))

    page_text = clean_text(soup.get_text(" ", strip=True))
    match = re.search(
        r"(?:color|colores)[:\s]+([a-zA-ZÀ-ÿ0-9 \-/,]+)",
        page_text,
        flags=re.IGNORECASE,
    )
    if match:
        return clean_text(match.group(1))

    return ""


def extract_sizes_from_detail(soup):
    selectors = [
        "[data-testid*='size']",
        "[data-testid*='sizes']",
        "[class*='size']",
        "[class*='sizes']",
        "select option",
        "button",
        "li",
        "span",
    ]

    common_sizes = {
        "XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL",
        "34", "35", "36", "37", "38", "39", "40", "41", "42", "43", "44", "45", "46"
    }

    found_sizes = []

    for selector in selectors:
        for node in soup.select(selector):
            text = get_text_from_node(node)
            if not text or len(text) > 20:
                continue

            cleaned = text.upper().strip()
            if cleaned in common_sizes and cleaned not in found_sizes:
                found_sizes.append(cleaned)

    return ", ".join(found_sizes)


def parse_product_detail_page(html_content, base_product_data):
    soup = BeautifulSoup(html_content, "html.parser")
    detail_product = base_product_data.copy()

    detail_product["product_name"] = extract_name_from_detail(
        soup,
        fallback_name=detail_product.get("product_name", "")
    )
    detail_product["description"] = extract_description_from_detail(soup)

    original_price, discount_price, discount_percentage = extract_prices_from_detail(soup)
    detail_product["original_price"] = original_price
    detail_product["discount_price"] = discount_price
    detail_product["discount_percentage"] = discount_percentage

    detail_product["color"] = extract_color_from_detail(soup)
    detail_product["available_sizes"] = extract_sizes_from_detail(soup)

    return detail_product