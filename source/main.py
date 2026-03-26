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
    print("Iniciando el scraper de Privalia...")

    crawler = PrivaliaCrawler()

    try:
        # 1. Login
        crawler.login()

        all_products_data = []

        # 2. Llegir home per descobrir campanyes
        print(f"\nCarregant pàgina principal per descobrir campanyes: {BASE_URL}")
        home_html = crawler.get_html(BASE_URL)
        campaigns = parse_campaign_list(home_html)

        if not campaigns:
            print("No s'han trobat campanyes a la Home.")
            campaigns = [
                {
                    "name": "Campaña Test",
                    "url": "https://es.privalia.com/gr/catalog/897409",
                    "sector": "Moda",
                    "end_date": "",
                }
            ]
            print("Usant URL de prova...")

        campaigns_to_visit = campaigns[:MAX_CAMPAIGNS_TO_VISIT]

        # 3. Iterar campanyes
        for camp in campaigns_to_visit:
            camp_url = camp.get("url")
            print(f"\n--- Entrant a la campanya: {camp.get('name', camp_url)} ---")

            camp_html = crawler.get_html(camp_url)
            base_products = parse_product_list(camp_html, camp)

            if not base_products:
                print("No s'han trobat productes en aquesta campanya.")
                base_products = [
                    {
                        "campaign_name": camp.get("name", ""),
                        "campaign_sector": camp.get("sector", ""),
                        "campaign_end_date": camp.get("end_date", ""),
                        "product_name": "Test",
                        "product_url": "https://es.privalia.com/gr/...",
                    }
                ]

            base_products_to_visit = base_products[:MAX_PRODUCTS_PER_CAMPAIGN_TO_VISIT]

            # 4. Iterar productes
            for product in base_products_to_visit:
                prod_url = product.get("product_url")

                if prod_url and prod_url.startswith("http"):
                    print(f"  Analitzant producte: {prod_url}")
                    prod_html = crawler.get_html(prod_url)
                    complete_product_data = parse_product_detail_page(prod_html, product)
                    all_products_data.append(complete_product_data)
                    time.sleep(REQUEST_DELAY_SECONDS)
                else:
                    all_products_data.append(product)

            time.sleep(REQUEST_DELAY_SECONDS)

        # 5. Guardar CSV
        if all_products_data:
            save_to_csv(all_products_data, OUTPUT_CSV)
            print(
                f"\nScraping completat. "
                f"Dades guardades per {len(all_products_data)} productes a {OUTPUT_CSV}"
            )
        else:
            print("\nScraping finalitzat però sense dades. Revisa el parser.")

    except Exception as e:
        print(f"Ocurrió un error general durante la ejecución: {e}")

    finally:
        crawler.close()


if __name__ == "__main__":
    main()