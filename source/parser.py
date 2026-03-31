import json
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


def extract_id_from_url(url):
    if not url:
        return ""
    
    # Try to find numeric ID at the end or in a segment
    # Patterns like /catalog/12345 or /campaign/any-name-12345
    match = re.search(r"/(\d+)/?$", url)
    if match:
        return match.group(1)
    
    # Try pattern like /catalog/12345/something
    match = re.search(r"/(?:catalog|campaign|sale|evento|brand|outlet)/([^/?#]+)", url)
    if match:
        segment = match.group(1)
        # If segment ends with -ID, extract ID
        sub_match = re.search(r"-(\d+)$", segment)
        if sub_match:
            return sub_match.group(1)
        return segment
    
    # Fallback to last segment of path
    path = urlparse(url).path.strip("/")
    if path:
        return path.split("/")[-1]
    
    return ""


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




def looks_like_listing_url(url):
    if not url or not is_valid_privalia_url(url) or is_bad_url(url):
        return False

    if looks_like_product_url(url):
        return False

    url_lower = url.lower()

    good_patterns = [
        "/catalog/",
        "/campaign/",
        "/sale/",
        "/evento/",
        "/brand/",
        "/outlet/",
        "/products",
        "/productos",
        "/all-products",
        "/todos",
        "/category/",
        "/categoria/",
        "?category=",
        "&category=",
        "?subcategory=",
        "&subcategory=",
        "?filter",
        "&filter",
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

    match = re.search(r"(-\s*\d{1,2}\s*%)", text)
    if not match:
        return ""

    pct = clean_text(match.group(1)).replace(" ", "")
    try:
        value = int(pct.replace("-", "").replace("%", ""))
    except ValueError:
        return ""

    if 1 <= value <= 95:
        return f"-{value}%"
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


def _safe_float(value):
    try:
        return float(value)
    except Exception:
        return None


def _format_price(value):
    if value is None:
        return ""
    return f"{float(value):.2f}"


def _normalize_price(raw):
    if raw is None:
        return None

    s = str(raw).strip()
    if not s:
        return None

    s = s.replace("\xa0", " ").replace("€", "")
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"\s*,\s*", ",", s)
    s = re.sub(r"\s*\.\s*", ".", s)

    # 18 99 -> 18.99
    if re.fullmatch(r"\d{1,4}\s\d{2}", s):
        left, right = s.split()
        s = f"{left}.{right}"
    elif "," in s and "." in s:
        # 1.299,99 -> 1299.99
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")

    s = re.sub(r"[^0-9.\-]", "", s)

    if s.count(".") > 1:
        parts = s.split(".")
        s = "".join(parts[:-1]) + "." + parts[-1]

    value = _safe_float(s)
    if value is None:
        return None

    if value <= 0 or value > 10000:
        return None

    return round(value, 2)


def _dedupe_keep_order(values):
    out = []
    for v in values:
        if v not in out:
            out.append(v)
    return out


def _extract_price_candidates_from_text(text):
    if not text:
        return []

    txt = str(text).replace("\xa0", " ")
    candidates = []

    patterns = [
        r"€\s*(\d{1,4}\s*[.,]\s*\d{2})",
        r"€\s*(\d{1,4}\s\d{2})",
        r"(\d{1,4}\s*[.,]\s*\d{2})\s*€",
        r"(\d{1,4}\s\d{2})\s*€",
        r"\b(\d{1,4}\s*[.,]\s*\d{2})\b",
        r"\b(\d{1,4}\s\d{2})\b",
    ]

    for pattern in patterns:
        for match in re.findall(pattern, txt, flags=re.IGNORECASE):
            value = _normalize_price(match)
            if value is not None:
                candidates.append(value)

    return _dedupe_keep_order(candidates)


def _walk_json(obj):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from _walk_json(v)
    elif isinstance(obj, list):
        for item in obj:
            yield from _walk_json(item)


def _extract_prices_from_json_scripts(soup):
    pairs = []

    for script in soup.find_all("script"):
        script_type = (script.get("type") or "").lower().strip()
        script_text = script.string or script.get_text("\n", strip=True)

        if not script_text:
            continue

        parsed_objects = []

        if script_type == "application/ld+json":
            try:
                parsed_objects.append(json.loads(script_text))
            except Exception:
                continue
        else:
            lowered = script_text.lower()
            if not any(k in lowered for k in ["price", "saleprice", "originalprice", "regularprice", "listprice"]):
                continue

            # provar a llegir JSON incrustat si existeix
            for match in re.findall(r"\{.*?\}", script_text, flags=re.DOTALL):
                if "price" not in match.lower():
                    continue
                try:
                    parsed_objects.append(json.loads(match))
                except Exception:
                    continue

        for parsed in parsed_objects:
            for item in _walk_json(parsed):
                if not isinstance(item, dict):
                    continue

                keys = {str(k).lower(): v for k, v in item.items()}

                current_price = None
                original_price = None

                for key in ["price", "saleprice", "currentprice", "lowprice", "bestprice"]:
                    if key in keys:
                        current_price = _normalize_price(keys[key])
                        if current_price is not None:
                            break

                for key in ["highprice", "originalprice", "oldprice", "regularprice", "listprice", "wasprice"]:
                    if key in keys:
                        original_price = _normalize_price(keys[key])
                        if original_price is not None:
                            break

                if current_price is not None:
                    pairs.append((original_price, current_price, "json"))
                elif original_price is not None:
                    pairs.append((None, original_price, "json"))

    return pairs


def _candidate_scopes(soup):
    scopes = []
    seen = set()

    def add(node):
        if not node:
            return
        node_id = id(node)
        if node_id not in seen:
            scopes.append(node)
            seen.add(node_id)

    h1 = soup.find("h1")
    if h1:
        current = h1
        for _ in range(4):
            current = current.parent
            if not current:
                break
            add(current)

    selectors = [
        "main",
        "article",
        "[data-testid*='product']",
        "[data-testid*='detail']",
        "[class*='product-detail']",
        "[class*='productDetail']",
        "[class*='product-page']",
        "[class*='productPage']",
        "[class*='details']",
        "[class*='pdp']",
    ]

    for selector in selectors:
        for node in soup.select(selector):
            add(node)

    if not scopes:
        add(soup)

    return scopes


def _extract_prices_from_scope(scope):
    selectors = [
        "[data-testid*='price']",
        "[class*='price']",
        "[class*='pricing']",
        "[class*='discount']",
        "[class*='sale']",
        "[class*='amount']",
        "[class*='current']",
        "[class*='old']",
        "[class*='final']",
        "meta[property='product:price:amount']",
        "meta[itemprop='price']",
    ]

    pairs = []

    for selector in selectors:
        for node in scope.select(selector):
            if node.name == "meta":
                value = _normalize_price(node.get("content", ""))
                if value is not None:
                    pairs.append((None, value, "meta"))
                continue

            text = get_text_from_node(node)
            if not text:
                continue

            prices = _extract_price_candidates_from_text(text)
            if len(prices) >= 2:
                pairs.append((max(prices), min(prices), "local_node"))
            elif len(prices) == 1:
                pairs.append((None, prices[0], "local_node"))

    # també mirar text de l’scope complet, però no de tota la pàgina
    scope_text = get_text_from_node(scope)
    scope_prices = _extract_price_candidates_from_text(scope_text)
    if len(scope_prices) >= 2:
        pairs.append((max(scope_prices), min(scope_prices), "local_text"))
    elif len(scope_prices) == 1:
        pairs.append((None, scope_prices[0], "local_text"))

    return pairs


def _extract_prices_from_scopes(soup):
    pairs = []
    for scope in _candidate_scopes(soup):
        pairs.extend(_extract_prices_from_scope(scope))
    return pairs


def _extract_prices_from_whole_page(soup):
    page_text = clean_text(soup.get_text(" ", strip=True))
    prices = _extract_price_candidates_from_text(page_text)

    pairs = []
    if len(prices) >= 2:
        pairs.append((max(prices), min(prices), "page"))
    elif len(prices) == 1:
        pairs.append((None, prices[0], "page"))

    return pairs


def _source_bonus(source):
    if source == "json":
        return 60
    if source == "meta":
        return 45
    if source == "local_node":
        return 35
    if source == "local_text":
        return 20
    if source == "page":
        return 0
    return 0


def _score_pair(original, current, discount_percentage, source):
    if current is None:
        return -999

    score = _source_bonus(source)

    if 1 <= current <= 5000:
        score += 10

    if original is not None:
        if original >= current:
            score += 10
        else:
            score -= 25

        if original > current:
            ratio = (original - current) / original
            if 0.01 <= ratio <= 0.95:
                score += 15
            else:
                score -= 10

        if discount_percentage:
            try:
                pct = int(discount_percentage.replace("-", "").replace("%", ""))
                calc = round((1 - current / original) * 100) if original else None
                if calc is not None:
                    diff = abs(calc - pct)
                    if diff == 0:
                        score += 40
                    elif diff <= 2:
                        score += 25
                    elif diff <= 5:
                        score += 10
                    else:
                        score -= 30
            except Exception:
                pass

    return score


def _choose_best_prices(pairs, discount_percentage):
    cleaned = []

    for original, current, source in pairs:
        if current is None:
            continue

        if current <= 0 or current > 10000:
            continue

        if original is not None and original < current:
            original, current = current, original

        cleaned.append((original, current, source))

    if not cleaned:
        return None, None

    best = max(cleaned, key=lambda x: _score_pair(x[0], x[1], discount_percentage, x[2]))
    return best[0], best[1]


def _clean_alt_brand_name(text):
    """Retorna el text complet del alt de la imatge, netejat."""
    return clean_text(text)

def extract_campaign_name_from_card(card, anchor):
    # Prioritat 1: InfoBannerSubtitle (el nom de la marca explícit al requadre d'info)
    name_selectors = [
        "span[class*='InfoBannerSubtitle']",
        "[class*='InfoBannerSubtitle']",
    ]
    for selector in name_selectors:
        found = card.select_one(selector)
        if found:
            text = get_text_from_node(found)
            if text and len(text) >= 2:
                cleaned = clean_text(text)
                # Si té més de 3 paraules, probablement és una descripció, no una marca
                if len(cleaned.split()) <= 3:
                    return cleaned

    # Prioritat 2: imatge alt (sol ser "Marca Descripció" o "Marca Marca")
    if anchor:
        img = anchor.find("img")
        if img:
            alt = get_attr(img, "alt")
            if alt and len(alt) >= 2:
                cleaned = _clean_alt_brand_name(alt)
                if cleaned:
                    return cleaned

    # Prioritat 3: article[title] — Privalia hi posa el nom de la marca, però a vegades és genèric
    article_title = get_attr(card, "title")
    if article_title and "Banner #" not in article_title and len(article_title.strip()) > 1:
        cleaned = clean_text(article_title)
        if len(cleaned.split()) <= 3:
            return cleaned

    # Prioritat 4: Altres selectors genèrics
    generic_selectors = [
        "[data-testid*='title']",
        "[data-testid*='name']",
        "h2", "h3", "h4", "strong",
    ]
    for selector in generic_selectors:
        found = card.select_one(selector)
        if found:
            text = get_text_from_node(found)
            if text and len(text) >= 2:
                cleaned = clean_text(text)
                if len(cleaned.split()) <= 3:
                    return cleaned

    if anchor:
        title = get_attr(anchor, "title")
        if title and len(title) >= 2:
            cleaned = clean_text(title)
            if len(cleaned.split()) <= 3:
                return cleaned

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
            # Darrer recurs: extreure l'ID de catàleg de la URL
            catalog_match = re.search(r"/catalog/(\d+)", full_url)
            if catalog_match:
                name = f"Campanya #{catalog_match.group(1)}"
            else:
                continue

        if full_url in seen_urls:
            continue

        campaigns.append(
            {
                "name": name,
                "url": full_url,
                "end_date": extract_end_date_from_card(card),
            }
        )
        seen_urls.add(full_url)

    return campaigns



def parse_campaign_subpages(html_content, campaign_url=""):
    soup = BeautifulSoup(html_content, "html.parser")
    subpages = []
    seen = set()

    def add(url, label=""):
        final_url = absolute_url(url)
        if not looks_like_listing_url(final_url):
            return
        subpages.append({
            "url": final_url,
            "label": clean_text(label),
        })

    # 1. Explorar el CatalogTree (menú lateral oficial)
    catalog_tree = soup.find(["ul", "nav"], attrs={"data-testid": "CatalogTree"})
    if not catalog_tree:
        # Fallback: buscar per facil-iti o classes
        catalog_tree = soup.find(attrs={"data-facil-iti": "catalog--tree-links"})
        
    if catalog_tree:
        for li in catalog_tree.find_all("li"):
            anchor = li.find("a", href=True)
            if anchor:
                # Categoria normal amb link
                href = anchor.get("href", "")
                # Prioritzem el data-testid de l'enllaç si existeix, o el text
                label = clean_text(anchor.get_text(" ", strip=True))
                add(href, label)
            else:
                # Categoria ACTIVA (sense link)
                label = clean_text(li.get_text(" ", strip=True))
                if label and campaign_url:
                    # L'afegim al principi com a activa
                    if campaign_url not in seen:
                        subpages.insert(0, {
                            "url": absolute_url(campaign_url),
                            "label": label
                        })
                        seen.add(absolute_url(campaign_url))

    nav_selectors = [
        "nav a[href]",
        "aside a[href]",
        "[role='navigation'] a[href]",
        "[class*='category'] a[href]",
        "[class*='Category'] a[href]",
        "a[href*='/catalog/']",
        "a[href*='/campaign/']",
    ]

    for selector in nav_selectors:
        for anchor in soup.select(selector):
            href = clean_text(anchor.get("href", ""))
            text = get_text_from_node(anchor)
            add(href, text)

    return subpages

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
    page_text = clean_text(soup.get_text(" ", strip=True))
    discount_percentage = parse_discount(page_text)

    pairs = []
    pairs.extend(_extract_prices_from_json_scripts(soup))
    pairs.extend(_extract_prices_from_scopes(soup))

    # només si encara no hi ha res, fer fallback global
    if not pairs:
        pairs.extend(_extract_prices_from_whole_page(soup))

    original_price, discount_price = _choose_best_prices(pairs, discount_percentage)

    if discount_price is None:
        return "", "", discount_percentage

    if original_price is None and discount_percentage:
        return "", _format_price(discount_price), discount_percentage

    if original_price is not None and discount_price is not None and not discount_percentage:
        pct = round((1 - (discount_price / original_price)) * 100)
        if 1 <= pct <= 95:
            discount_percentage = f"-{pct}%"

    return _format_price(original_price), _format_price(discount_price), discount_percentage


def _is_bad_color_candidate(value):
    if not value:
        return True

    v = clean_text(value)
    if not v:
        return True

    vl = v.lower()
    bad_exact = {
        "menu", "color", "colour", "colores", "selecciona", "elige", "elige tu modelo",
        "escoge tu talla", "escoge", "talla", "modelo", "wishlist", "favoritos"
    }
    if vl in bad_exact:
        return True

    if len(v) > 40:
        return True

    if "http" in vl or "€" in v:
        return True

    if re.fullmatch(r"#[0-9a-fA-F]{3,8}", v):
        return True

    if any(tok in vl for tok in ["rgb(", "rgba(", "hsl(", "hsla(", "var(", "--"]):
        return True

    if " - " in v and len(v.split(" - ")) >= 3:
        return True

    if re.fullmatch(r"[\d\s,./%-]+", v):
        return True

    return False


def _extract_color_from_product_name(name):
    if not name:
        return ""

    parts = [clean_text(x) for x in str(name).split(" - ") if clean_text(x)]
    if len(parts) >= 2:
        candidate = parts[-1]
        if not _is_bad_color_candidate(candidate):
            return candidate

    return ""


def _extract_color_from_label_value_blocks(soup):
    labels = {"color", "colour", "colores"}

    for node in soup.find_all(["div", "span", "p", "dt", "strong", "label", "h2", "h3", "h4"]):
        label_text = clean_text(node.get_text(" ", strip=True)).rstrip(":").lower()
        if label_text not in labels:
            continue

        for sib in list(node.next_siblings)[:5]:
            if getattr(sib, "name", None):
                txt = clean_text(sib.get_text(" ", strip=True))
            else:
                txt = clean_text(str(sib))
            if txt and not _is_bad_color_candidate(txt):
                return txt

        parent = node.parent
        if parent:
            texts = [clean_text(t) for t in parent.stripped_strings]
            try:
                idx = next(i for i, t in enumerate(texts) if t.rstrip(":").lower() in labels)
                for candidate in texts[idx + 1 : idx + 4]:
                    if candidate and not _is_bad_color_candidate(candidate):
                        return candidate
            except StopIteration:
                pass

    return ""


def _extract_color_from_semantic_blocks(soup):
    labels = {"color", "colour", "colores"}
    candidates = []

    for text_node in soup.find_all(string=True):
        label_text = clean_text(text_node)
        if label_text.rstrip(":").lower() not in labels:
            continue

        parent = getattr(text_node, "parent", None)
        if not parent:
            continue

        container = parent.parent if getattr(parent, "parent", None) else parent
        texts = [clean_text(t) for t in container.stripped_strings]
        try:
            idx = next(i for i, t in enumerate(texts) if t.rstrip(":").lower() in labels)
        except StopIteration:
            idx = -1

        if idx >= 0:
            for candidate in texts[idx + 1 : idx + 5]:
                if candidate and not _is_bad_color_candidate(candidate):
                    candidates.append(candidate)

    if candidates:
        candidates = sorted(_dedupe_keep_order(candidates), key=lambda x: (len(x), x))
        return candidates[0]
    return ""


def _extract_color_from_attributes(soup):
    attrs = ["data-color", "data-colour"]

    for node in soup.find_all(True):
        for attr in attrs:
            raw = clean_text(node.get(attr, ""))
            if raw and not _is_bad_color_candidate(raw):
                return raw

        for attr in ["aria-label", "title"]:
            raw = clean_text(node.get(attr, ""))
            if not raw:
                continue
            m = re.search(r"(?:^|\b)(?:color|colour|colores)[:\s-]+([^|;,]+)", raw, flags=re.I)
            if m:
                candidate = clean_text(m.group(1))
                if not _is_bad_color_candidate(candidate):
                    return candidate

        text = get_text_from_node(node)
        if text and len(text) <= 30:
            m = re.search(r"(?:^|\b)(?:color|colour|colores)[:\s-]+([^|;,]+)", text, flags=re.I)
            if m:
                candidate = clean_text(m.group(1))
                if not _is_bad_color_candidate(candidate):
                    return candidate

    return ""


def _extract_color_from_json_scripts(soup):
    for script in soup.find_all("script"):
        script_text = script.string or script.get_text("\n", strip=True)
        if not script_text:
            continue
        lowered = script_text.lower()
        if not any(k in lowered for k in ["color", "colour"]):
            continue

        parsed = []
        stype = (script.get("type") or "").lower()
        if "json" in stype:
            try:
                parsed.append(json.loads(script_text))
            except Exception:
                pass

        if not parsed:
            for match in re.findall(r"\{.*?\}", script_text, flags=re.DOTALL):
                if "color" not in match.lower() and "colour" not in match.lower():
                    continue
                try:
                    parsed.append(json.loads(match))
                except Exception:
                    continue

        for obj in parsed:
            for item in _walk_json(obj):
                if not isinstance(item, dict):
                    continue
                for key, value in item.items():
                    kl = str(key).lower()
                    if kl in {"color", "colour", "colore", "colorname"}:
                        candidate = clean_text(value)
                        if not _is_bad_color_candidate(candidate):
                            return candidate
    return ""


def extract_all_colors_from_detail(soup, fallback_name=""):
    """Extreu TOTS els colors disponibles a partir dels thumbnails de variació.
    Format: 'azul y verde | malva | azul' (un per variant).
    Si no hi ha variants, fa fallback a extract_color_from_detail.
    """
    colors = []
    seen = set()

    # Estructura: data-testid="variation-item-{sku}" > a > img[alt]
    for item in soup.find_all(attrs={"data-testid": re.compile(r"^variation-item-\d+$")}):
        img = item.find("img", alt=True)
        if not img:
            continue
        alt = clean_text(img.get("alt", ""))
        if not alt:
            continue
        # L'alt tés forma "Nom - material - regular fit - color"
        # El color és l'ultima part després del darrer ' - '
        parts = [p.strip() for p in alt.split(" - ") if p.strip()]
        if len(parts) >= 2:
            color = parts[-1]
            if not _is_bad_color_candidate(color) and color not in seen:
                colors.append(color)
                seen.add(color)

    if colors:
        return " | ".join(colors)

    # Fallback: extracció simple del color actual (de la variant seleccionada)
    for fn in (
        _extract_color_from_label_value_blocks,
        _extract_color_from_semantic_blocks,
    ):
        candidate = fn(soup)
        if candidate:
            return candidate

    candidate = _extract_color_from_product_name(fallback_name)
    if candidate:
        return candidate

    for fn in (
        _extract_color_from_attributes,
        _extract_color_from_json_scripts,
    ):
        candidate = fn(soup)
        if candidate:
            return candidate

    return ""



def _size_status_from_node(node, text=""):
    raw = " ".join([
        get_text_from_node(node),
        get_attr(node, "class"),
        get_attr(node, "aria-label"),
        get_attr(node, "title"),
        get_attr(node, "disabled"),
        get_attr(node, "aria-disabled"),
    ]).lower()
    raw += " " + str(text).lower()
    out_words = ["agotado", "sold out", "sin stock", "unavailable", "no disponible", "out of stock", "disabled"]
    almost_words = ["agotándose", "agotandose", "últimas unidades", "ultimas unidades",
                    "casi agotado", "low stock", "last items", "quedan pocas"]
    if any(w in raw for w in out_words):
        return "OUT"
    if any(w in raw for w in almost_words):
        return "ALMOST"
    return "OK"


def _extract_size_tokens(text):
    if not text:
        return []

    txt = clean_text(text)
    if not txt:
        return []

    upper = txt.upper()
    results = []

    for m in re.finditer(r"\b(\d{1,2})\s*\((?:ES|EU|UK|US)\)\s*-\s*\1\s*\((?:ES|EU|UK|US)\)\b", upper):
        token = m.group(1)
        if token not in results:
            results.append(token)

    for m in re.finditer(r"\b(XXXS|XXS|XS|S|M|L|XL|XXL|XXXL)\b", upper):
        token = m.group(1)
        if token not in results:
            results.append(token)

    for m in re.finditer(r"\b(1\d|2\d|3\d|4\d|50|51|52)\b", upper):
        token = m.group(1)
        context = upper[max(0, m.start() - 12) : m.end() + 12]
        if any(x in context for x in ["€", "%", ".", ","]):
            continue
        if token and token not in results:
            results.append(token)

    return results


def _extract_sizes_from_json_scripts(soup):
    found = {}
    relevant_keys = {"size", "sizes", "talla", "tallas", "label", "name", "value"}

    for script in soup.find_all("script"):
        script_text = script.string or script.get_text("\n", strip=True)
        if not script_text:
            continue
        lowered = script_text.lower()
        if not any(k in lowered for k in ["size", "sizes", "talla", "tallas"]):
            continue

        parsed = []
        stype = (script.get("type") or "").lower()
        if "json" in stype:
            try:
                parsed.append(json.loads(script_text))
            except Exception:
                pass

        for obj in parsed:
            for item in _walk_json(obj):
                if not isinstance(item, dict):
                    continue

                text_candidates = []
                for key, value in item.items():
                    if str(key).lower() in relevant_keys and isinstance(value, (str, int, float)):
                        text_candidates.append(str(value))

                status = "OK"
                for key, value in item.items():
                    kl = str(key).lower()
                    if kl in {"available", "availability", "in_stock", "instock", "isavailable"}:
                        sv = str(value).lower()
                        if sv in {"false", "0", "outofstock", "out_of_stock", "soldout"}:
                            status = "OUT"

                for txt in text_candidates:
                    for size in _extract_size_tokens(txt):
                        if size not in found or found[size] == "OUT":
                            found[size] = status

    return found


def _find_size_area_nodes(soup):
    area_nodes = []
    seen = set()

    def add(node):
        if not node:
            return
        node_id = id(node)
        if node_id not in seen:
            area_nodes.append(node)
            seen.add(node_id)

    for selector in ["select", "[role='listbox']", "[role='option']", "option"]:
        for node in soup.select(selector):
            add(node)
            add(node.parent)
            add(getattr(node.parent, "parent", None))

    size_words = {"talla", "tallas", "size", "sizes", "elige tu modelo", "selecciona tu talla", "selecciona talla"}
    for node in soup.find_all(["div", "span", "label", "p", "strong", "h2", "h3", "h4"]):
        txt = clean_text(node.get_text(" ", strip=True)).lower()
        if txt in size_words:
            add(node.parent)
            add(getattr(node.parent, "parent", None))

    return [n for n in area_nodes if n]


def extract_sizes_from_detail(soup):
    found_sizes = {}
    areas = _find_size_area_nodes(soup)

    candidate_nodes = []
    seen = set()
    selectors = ["option", "[role='option']", "li", "button", "label", "span", "div"]

    for area in areas:
        for selector in selectors:
            for node in area.select(selector):
                node_id = id(node)
                if node_id not in seen:
                    candidate_nodes.append(node)
                    seen.add(node_id)

    for node in candidate_nodes:
        texts = [
            get_text_from_node(node),
            get_attr(node, "value"),
            get_attr(node, "aria-label"),
            get_attr(node, "title"),
            get_attr(node, "data-value"),
            get_attr(node, "data-label"),
            get_attr(node, "data-size"),
        ]
        combined = " | ".join([t for t in texts if t])
        if not combined:
            continue

        upper = combined.upper()
        if any(bad in upper for bad in ["ELIGE TU MODELO", "SELECCIONA", "COLOR", "MENU"]):
            continue

        sizes = _extract_size_tokens(combined)
        if not sizes:
            continue

        numeric_sizes = [s for s in sizes if s.isdigit()]
        if len(set(numeric_sizes)) > 5 and node.name in {"div", "span"}:
            continue

        status = _size_status_from_node(node, combined)
        for size in sizes:
            if size not in found_sizes or found_sizes[size] == "OUT":
                found_sizes[size] = status

    if not found_sizes:
        for size, status in _extract_sizes_from_json_scripts(soup).items():
            if size not in found_sizes or found_sizes[size] == "OUT":
                found_sizes[size] = status

    if not found_sizes:
        return ""

    def sort_key(item):
        s = item[0]
        if s.isdigit():
            return (0, int(s))
        return (1, s)

    sorted_sizes = sorted(found_sizes.items(), key=sort_key)
    return ", ".join([f"{s}:{stat}" for s, stat in sorted_sizes])

def extract_image_from_detail(soup):
    # Intentar og:image primer (estàndard SEO)
    og_image = soup.find("meta", property="og:image")
    if og_image and og_image.get("content"):
        return og_image["content"]

    # Buscar la imatge principal del producte
    image_selectors = [
        "[data-testid*='product-image']",
        "[class*='ProductImage'] img",
        "[class*='MainImage'] img",
        ".styles__VariationThumbnail-groot__sc-cfcf0da0-3",
        "img[data-testid*='variation-item']",
        ".styles__MainImg-groot__sc-80bee9f7-1",
        "img[src*='media.veepee.com']"
    ]

    for selector in image_selectors:
        img = soup.select_one(selector)
        if img:
            src = get_attr(img, "src") or get_attr(img, "data-src")
            if src:
                return src

    return ""

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

    detail_product["color"] = extract_all_colors_from_detail(soup, fallback_name=detail_product.get("product_name", ""))
    detail_product["image_url"] = extract_image_from_detail(soup)
    detail_product["sizes_status"] = extract_sizes_from_detail(soup)

    return detail_product