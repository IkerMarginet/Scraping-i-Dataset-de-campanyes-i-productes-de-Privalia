import os
import time
from datetime import datetime

from config import (
    BASE_URL,
    CAMPAIGNS_CSV,
    PRODUCTS_CSV,
    MAX_CAMPAIGNS_TO_VISIT,
    MAX_PRODUCTS_PER_CAMPAIGN_TO_VISIT,
    REQUEST_DELAY_SECONDS,
)
from crawler import PrivaliaCrawler
from parser import (
    parse_campaign_list,
    parse_product_list,
    parse_product_detail_page,
)
from storage import save_campaigns, save_product_incremental


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

    crawler = PrivaliaCrawler()

    if os.path.exists(PRODUCTS_CSV):
        try:
            os.remove(PRODUCTS_CSV)
        except Exception:
            pass

    try:
        crawler.login()

        print(f"\nS'està carregant la pàgina principal per descobrir campanyes: {BASE_URL}")
        home_html = crawler.get_html(
            BASE_URL,
            wait_seconds=5,
            scroll=True,
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

        campaigns_data = []
        for camp in campaigns_to_visit:
            campaigns_data.append({
                "campaign_url": camp.get("url", ""),
                "brand_name": camp.get("name", "").strip(),
                "sector": camp.get("sector", ""),
                "end_date_text": camp.get("end_date", ""),
                "extraction_timestamp": extraction_ts
            })

        save_campaigns(campaigns_data, CAMPAIGNS_CSV)

        for camp_index, camp in enumerate(campaigns_to_visit, start=1):
            camp_url = camp.get("url", "")
            camp_name = camp.get("name", "").strip() or camp_url

            print(
                f"\n--- [{camp_index}/{len(campaigns_to_visit)}] "
                f"S'està processant la campanya: {camp_name} ---"
            )

            if not camp_url.startswith("http"):
                continue

            camp_html = crawler.get_html(
                camp_url,
                wait_seconds=5,
                scroll=True,
                debug_prefix=f"02_campaign_{camp_index}" if save_debug else None
            )

            base_products = parse_product_list(camp_html, camp)
            print(f"  Productes trobats: {len(base_products)}")

            if not base_products:
                time.sleep(REQUEST_DELAY_SECONDS)
                continue

            base_products_to_visit = base_products[:MAX_PRODUCTS_PER_CAMPAIGN_TO_VISIT]

            for prod_index, product in enumerate(base_products_to_visit, start=1):
                prod_url = product.get("product_url", "")
                print(f"    [{prod_index}/{len(base_products_to_visit)}] Analitzant producte...")

                if not prod_url.startswith("http"):
                    continue

                prod_html = crawler.get_html(
                    prod_url,
                    wait_seconds=4,
                    scroll=False,
                    debug_prefix=f"03_product_{camp_index}_{prod_index}" if save_debug else None
                )

                complete_data = parse_product_detail_page(prod_html, product)

                product_item = {
                    "product_url": prod_url,
                    "campaign_url": camp_url,
                    "product_name": complete_data.get("product_name", ""),
                    "description": complete_data.get("description", ""),
                    "original_price": complete_data.get("original_price", ""),
                    "discount_price": complete_data.get("discount_price", ""),
                    "discount_percentage": complete_data.get("discount_percentage", ""),
                    "color": complete_data.get("color", ""),
                    "sizes_status": complete_data.get("available_sizes", "")
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