import time

from config import (
    BASE_URL,
    OUTPUT_CSV,
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
from storage import save_to_csv


def main():
    print("S'està iniciant l'scraper de Privalia...")
    crawler = PrivaliaCrawler()

    try:
        crawler.login()

        all_products_data = []

        print(f"\nS'està carregant la pàgina principal per descobrir campanyes: {BASE_URL}")
        home_html = crawler.get_html(
            BASE_URL,
            wait_seconds=5,
            scroll=True,
            debug_prefix="01_home_after_login"
        )

        campaigns = parse_campaign_list(home_html)
        print(f"Campanyes trobades: {len(campaigns)}")

        if not campaigns:
            crawler.save_current_page("01_home_no_campaigns_found")
            raise RuntimeError(
                "No s'han trobat campanyes reals a la pàgina principal. "
                "Revisa debug/01_home_after_login.html"
            )

        campaigns_to_visit = campaigns[:MAX_CAMPAIGNS_TO_VISIT]

        for camp_index, camp in enumerate(campaigns_to_visit, start=1):
            camp_url = camp.get("url", "")
            camp_name = camp.get("name", "").strip() or camp_url
            print(
                f"\n--- [{camp_index}/{len(campaigns_to_visit)}] "
                f"S'està entrant a la campanya: {camp_name} ---"
            )

            if not camp_url.startswith("http"):
                print("URL de campanya no vàlida, s'ignora.")
                continue

            camp_html = crawler.get_html(
                camp_url,
                wait_seconds=5,
                scroll=True,
                debug_prefix=f"02_campaign_{camp_index}"
            )

            base_products = parse_product_list(camp_html, camp)
            print(f"Productes trobats a la campanya: {len(base_products)}")

            if not base_products:
                crawler.save_current_page(f"02_campaign_{camp_index}_no_products_found")
                print("No s'han trobat productes reals en aquesta campanya.")
                time.sleep(REQUEST_DELAY_SECONDS)
                continue

            base_products_to_visit = base_products[:MAX_PRODUCTS_PER_CAMPAIGN_TO_VISIT]

            for prod_index, product in enumerate(base_products_to_visit, start=1):
                prod_url = product.get("product_url", "")
                print(
                    f"  [{prod_index}/{len(base_products_to_visit)}] "
                    f"S'està analitzant el producte: {prod_url}"
                )

                if not prod_url.startswith("http"):
                    print("  URL de producte no vàlida, s'ignora.")
                    continue

                prod_html = crawler.get_html(
                    prod_url,
                    wait_seconds=4,
                    scroll=False,
                    debug_prefix=f"03_product_{camp_index}_{prod_index}"
                )

                complete_product_data = parse_product_detail_page(prod_html, product)
                all_products_data.append(complete_product_data)

                time.sleep(REQUEST_DELAY_SECONDS)

            time.sleep(REQUEST_DELAY_SECONDS)

        if all_products_data:
            save_to_csv(all_products_data, OUTPUT_CSV)
            print(
                f"\nScraping completat. "
                f"S'han desat dades de {len(all_products_data)} productes a {OUTPUT_CSV}"
            )
        else:
            raise RuntimeError(
                "L'scraping ha finalitzat però no s'han obtingut dades reals de productes. "
                "Revisa els HTML desats a la carpeta /debug."
            )

    except Exception as e:
        print(f"S'ha produït un error general durant l'execució: {e}")

    finally:
        crawler.close()


if __name__ == "__main__":
    main()