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
        ".header-banner__label",
        ".campaign-card__info-sector",
    ]

    for selector in sector_selectors:
        node = card.select_one(selector)
        text = get_text_from_node(node)
        if text:
            return text

    spans = card.find_all("span")
    for s in spans:
        t = get_text_from_node(s)
        if t and 3 < len(t) < 15 and t.isupper():
            return t

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

        if full_url in seen_urls:
            continue

        campaigns.append(
            {
                "name": name,
                "url": full_url,
                "sector": extract_sector_from_card(card),
                "end_date": extract_end_date_from_card(card),
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
                r"(?:color|colores|colour)[:\s]+([a-zA-ZÀ-ÿ0-9 \-/,]+)",
                text,
                flags=re.IGNORECASE,
            )
            if match:
                candidate = clean_text(match.group(1))
                if not re.fullmatch(r"[\d\s,.\-]+", candidate):
                    return candidate

    page_text = clean_text(soup.get_text(" ", strip=True))
    match = re.search(
        r"(?:color|colores|colour)[:\s]+([a-zA-ZÀ-ÿ0-9 \-/,]+)",
        page_text,
        flags=re.IGNORECASE,
    )
    if match:
        candidate = clean_text(match.group(1))
        if not re.fullmatch(r"[\d\s,.\-]+", candidate):
            return candidate

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

    found_sizes = {}

    for selector in selectors:
        for node in soup.select(selector):
            text = get_text_from_node(node)
            if not text or len(text) > 20:
                continue

            cleaned = text.upper().strip()
            if cleaned in common_sizes:
                classes = " ".join(node.get("class", []))
                is_disabled = (
                    node.get("disabled") is not None or
                    "disabled" in classes or
                    "unavailable" in classes or
                    "out-of-stock" in classes or
                    "is-sold-out" in classes
                )

                status = "OUT" if is_disabled else "OK"

                if cleaned not in found_sizes or found_sizes[cleaned] == "OUT":
                    found_sizes[cleaned] = status

    if not found_sizes:
        return ""

    sorted_sizes = sorted(found_sizes.items())
    return ", ".join([f"{s}:{stat}" for s, stat in sorted_sizes])


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