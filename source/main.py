import time
from config import BASE_URL, OUTPUT_CSV, MAX_CAMPAIGNS_TO_VISIT, MAX_PRODUCTS_PER_CAMPAIGN_TO_VISIT
from crawler import PrivaliaCrawler
from parser import parse_campaign_list, parse_product_list, parse_product_detail_page
from storage import save_to_csv

def main():
    print("Iniciando el scraper de Privalia...")
    
    crawler = PrivaliaCrawler()
    
    try:
        # 1. Login
        crawler.login()
        
        all_products_data = []
        
        # 2. Descobriment d'enllaços (Llegir Home per extreure les Campanyes actives)
        print(f"\nCarregant pàgina principal per descobrir campanyes: {BASE_URL}")
        home_html = crawler.get_html(BASE_URL)
        campaigns = parse_campaign_list(home_html)
        
        if not campaigns:
            print("No s'han trobat campanyes a la Home. Verifica el parser de parse_campaign_list()")
            # Dades Dummy per veure el flux quan ho provis:
            campaigns = [{'name': 'Campaña Test', 'url': 'https://es.privalia.com/gr/catalog/897409', 'sector': 'Moda'}]
            print("Usant url de prova...")

        # Limitar la quantitat per proves
        campaigns_to_visit = campaigns[:MAX_CAMPAIGNS_TO_VISIT]
        
        # 3. Iterar per cada campanya descoberta
        for camp in campaigns_to_visit:
            camp_url = camp.get('url')
            print(f"\n--- Entrant a la campanya: {camp.get('name', camp_url)} ---")
            
            camp_html = crawler.get_html(camp_url)
            # Extreure llista de productes d'aquesta campanya
            base_products = parse_product_list(camp_html, camp)
            
            if not base_products:
                print("No s'han trobat productes en aquesta campanya. Faltan els selectors TODO.")
                # Dades Dummy
                base_products = [{'product_url': 'https://es.privalia.com/gr/...', 'product_name': 'Test'}]
            
            base_products_to_visit = base_products[:MAX_PRODUCTS_PER_CAMPAIGN_TO_VISIT]
            
            # 4. Iterar sobre cada producte dins de la campanya (per extreure color, talles, etc)
            for product in base_products_to_visit:
                prod_url = product.get('product_url')
                if prod_url and prod_url.startswith("http"):
                    print(f"  Analitzant producte: {prod_url}")
                    prod_html = crawler.get_html(prod_url)
                    
                    # Afegeix el detall complet que vols a la proposta (talles, colors, descompte total)
                    complete_product_data = parse_product_detail_page(prod_html, product)
                    all_products_data.append(complete_product_data)
                    
                    # Complexitat: Pauses per no saturar el servidor (Punt avaluat)
                    time.sleep(2)
                else:
                    all_products_data.append(product)
            
            time.sleep(3)
            
        # 5. Desar els resultats
        if all_products_data:
            save_to_csv(all_products_data, OUTPUT_CSV)
            print(f"\nScraping completat. Dades guardades per {len(all_products_data)} productes a {OUTPUT_CSV}")
        else:
            print("\nScraping finalitzat pero sense dades. Revisa els TODO del parser.")
            
    except Exception as e:
        print(f"Ocurrió un error general durante la ejecución: {e}")
        
    finally:
        crawler.close()

if __name__ == "__main__":
    main()