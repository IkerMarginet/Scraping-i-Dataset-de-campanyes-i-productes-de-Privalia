import os
import time
from datetime import datetime

from config import (
    BASE_URL,
    CAMPAIGNS_CSV,
    PRODUCTS_CSV,
    MAX_CAMPAIGNS_TO_VISIT,
    MAX_SUBPAGES_PER_CAMPAIGN,
    MAX_PRODUCTS_PER_CAMPAIGN_TO_VISIT,
    REQUEST_DELAY_SECONDS,
)
from crawler import PrivaliaCrawler
from parser import (
    parse_campaign_list,
    parse_product_list,
    parse_product_detail_page,
    parse_campaign_subpages,
    extract_id_from_url,
)
from storage import save_campaigns, save_product_incremental, get_scraped_campaign_urls


def main():
    print("\n" + "=" * 50)
    print("  SCRAPER DE PRIVALIA (Projecte Master Data Science)")
    print("=" * 50 + "\n")

    debug_choice = input("Vols guardar captures de pantalla i HTML de depuració? (s/n, defecte: n): ").lower().strip()
    save_debug = debug_choice == "s"

    if save_debug:
        print(" -> Mode depuració ACTIU. Les imatges es guardaran a /docs/imatges.")
    else:
        print(" -> Mode depuració INACTIU. No es guardaran imatges.")

    duplicate_choice = input("Vols duplicar campanyes ja existents? (s/n, defecte: n): ").lower().strip()
    allow_duplicates = duplicate_choice == "s"

    scraped_urls = set()
    if not allow_duplicates:
        print(" -> Es mantindrà el contingut al csv i només s'afegiran les campanyes que no hi siguin.")
        scraped_urls = get_scraped_campaign_urls(CAMPAIGNS_CSV)
        if scraped_urls:
            print(f" -> S'han detectat {len(scraped_urls)} campanyes ja registrades prèviament.")
    else:
        print(" -> S'afegiran totes les campanyes al CSV existent, generant possibles duplicats.")

    crawler = PrivaliaCrawler()

    # Netejar fitxers anteriors per començar de zero en aquesta sessió
    # Comentat per mantenir históric
    # for csv_file in [PRODUCTS_CSV, CAMPAIGNS_CSV]:
    #     if os.path.exists(csv_file):
    #         try:
    #             os.remove(csv_file)
    #         except Exception:
    #             pass

    try:
        crawler.login()

        print(f"\nS'està carregant la pàgina principal per descobrir campanyes: {BASE_URL}")
        home_html = crawler.get_html(
            BASE_URL,
            wait_seconds=5,
            scroll=True,
            scroll_steps=15,
            debug_prefix="01_home_after_login" if save_debug else None
        )

        campaigns = parse_campaign_list(home_html)
        print(f"Campanyes trobades: {len(campaigns)}")

        if not campaigns:
            crawler.save_current_page("01_home_no_campaigns_found")
            raise RuntimeError(
                "No s'han trobat campanyes reals a la pàgina principal. Revisa els fitxers de debug."
            )

        campaigns_to_visit = campaigns[:MAX_CAMPAIGNS_TO_VISIT]
        extraction_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for camp_index, camp in enumerate(campaigns_to_visit, start=1):
            camp_url = camp.get("url", "")
            camp_name = camp.get("name", "").strip() or camp_url

            if camp_url in scraped_urls:
                print(
                    f"\n--- [{camp_index}/{len(campaigns_to_visit)}] "
                    f"SALTANT campanya (ja existent al csv): {camp_name} ---"
                )
                continue

            print(
                f"\n--- [{camp_index}/{len(campaigns_to_visit)}] "
                f"S'està processant la campanya: {camp_name} ---"
            )

            if not camp_url.startswith("http"):
                continue

            camp_html = crawler.get_html(
                camp_url,
                wait_seconds=2,
                scroll=True,
                scroll_steps=5,
                debug_prefix=f"02_campaign_{camp_index}" if save_debug else None
            )

            discovered_subpages = parse_campaign_subpages(camp_html, campaign_url=camp_url)
            listing_pages = discovered_subpages[:MAX_SUBPAGES_PER_CAMPAIGN]

            # Si no hem detectat cap subpàgina, usem principal com a fallback d'últim recurs
            if not listing_pages:
                listing_pages = [{"url": camp_url, "label": "principal"}]
            # Si per alguna raó la primera no és la nostra URL, l'afegim al principi
            elif listing_pages[0]["url"].rstrip("/") != camp_url.rstrip("/"):
                # Però mirem si ja existeix a la llista
                exists = any(p["url"].rstrip("/") == camp_url.rstrip("/") for p in listing_pages)
                if not exists:
                    listing_pages.insert(0, {"url": camp_url, "label": "principal"})

            print(f"  Subpàgines detectades: {len(discovered_subpages)}")
            sub_labels = [s.get("label", "") for s in discovered_subpages if s.get("label")]
            sub_categories_text = ", ".join(sub_labels)
            

            for subpage in discovered_subpages[:15]:
                label = subpage.get("label", "") or "sense nom"
                print(f"    - {label}: {subpage.get('url', '')}")

            all_products = []
            seen_product_urls = set()
            total_discovered_count = 0

            for page_index, listing in enumerate(listing_pages, start=1):
                listing_url = listing.get("url", "")
                listing_label = listing.get("label", "") or f"subpagina_{page_index}"

                if page_index == 1:
                    listing_html = camp_html
                else:
                    print(f"  Obrint subpàgina [{page_index}/{len(listing_pages)}]: {listing_label}")
                    listing_html = crawler.get_html(
                        listing_url,
                        wait_seconds=2,
                        scroll=True,
                        scroll_steps=5,
                        debug_prefix=(f"02_campaign_{camp_index}_sub_{page_index}" if save_debug else None)
                    )

                page_products = parse_product_list(listing_html, camp)
                total_discovered_count += len(page_products)

                for product in page_products:
                    product["subcategory"] = listing_label
                    prod_url = product.get("product_url", "")
                    if not prod_url or prod_url in seen_product_urls:
                        continue
                    seen_product_urls.add(prod_url)
                    all_products.append(product)

                print(f"    Productes únics acumulats: {len(all_products)}")
                time.sleep(REQUEST_DELAY_SECONDS)

            # Ara que tenim tots els productes comptats, guardem la campanya al CSV
            save_campaigns([{
                "campaign_id": extract_id_from_url(camp_url),
                "campaign_url": camp_url,
                "total_products_count": total_discovered_count,
                "unique_products_count": len(all_products),
                "brand_name": camp.get("name", "").strip(),
                "subcategories": sub_categories_text,
                "end_date_text": camp.get("end_date", ""),
                "extraction_timestamp": extraction_ts
            }], CAMPAIGNS_CSV)

            print(f"  Total: {total_discovered_count} trobats, {len(all_products)} únics.")

            print(f"  Productes totals trobats: {len(all_products)}")

            if not all_products:
                time.sleep(REQUEST_DELAY_SECONDS)
                continue

            base_products_to_visit = all_products[:MAX_PRODUCTS_PER_CAMPAIGN_TO_VISIT]

            for prod_index, product in enumerate(base_products_to_visit, start=1):
                prod_url = product.get("product_url", "")
                print(f"    [{prod_index}/{len(base_products_to_visit)}] Analitzant producte...")

                if not prod_url.startswith("http"):
                    continue

                prod_html = crawler.get_product_html_with_interaction(
                    prod_url,
                    wait_seconds=2,
                    debug_prefix=f"03_product_{camp_index}_{prod_index}" if save_debug else None
                )

                complete_data = parse_product_detail_page(prod_html, product)

                product_item = {
                    "product_id": extract_id_from_url(prod_url),
                    "product_url": prod_url,
                    "campaign_id": extract_id_from_url(camp_url),
                    "campaign_url": camp_url,
                    "product_name": complete_data.get("product_name", ""),
                    "original_price": complete_data.get("original_price", ""),
                    "discount_price": complete_data.get("discount_price", ""),
                    "discount_percentage": complete_data.get("discount_percentage", ""),
                    "color": complete_data.get("color", ""),
                    "sizes_status": complete_data.get("sizes_status", ""),
                    "subcategory": complete_data.get("subcategory", product.get("subcategory", "")),
                    "image_url": complete_data.get("image_url", ""),
                    "extraction_timestamp": extraction_ts
                }

                print(
                    "      -> "
                    f"nom={product_item['product_name'][:60]} | "
                    f"original={product_item['original_price']} | "
                    f"descompte={product_item['discount_price']} | "
                    f"pct={product_item['discount_percentage']}"
                )

                save_product_incremental(product_item, PRODUCTS_CSV)
                time.sleep(REQUEST_DELAY_SECONDS)

            time.sleep(REQUEST_DELAY_SECONDS)

        print("\nScraping completat amb èxit!")

    except Exception as e:
        print(f"S'ha produït un error general: {e}")

    finally:
        crawler.close()


if __name__ == "__main__":
    main()