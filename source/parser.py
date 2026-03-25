from bs4 import BeautifulSoup

def parse_campaign_list(html_content):
    """
    Toma el HTML de la página principal (Home) y extrae la lista de campanyas/vendes flash actives.
    (Complint amb el punt: Descobriment d'enllaços)
    
    :param html_content: Código HTML de la portada
    :return: Lista de diccionarios con info de campanyes
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    campaigns = []
    
    # TODO: Analitzar els blocs de campanyes a la Home
    # Exemple de camps a extreure definits a la teva proposta:
    # campanya['name'] = Nom de la marca / campanya
    # campanya['sector'] = Sector / Categoria general (Moda, Llar, Bellesa)
    # campanya['end_date'] = Data de finalització ('Acaba en X dies')
    # campanya['url'] = Enllaç per entrar als productes
    
    # Per cada campanya extreta, afegir a la llista: campaigns.append(campanya)
        
    return campaigns

def parse_product_list(html_content, campaign_data):
    """
    Toma el HTML de una campaña/catálogo y extrae los enlaces a los productos individuales.
    
    :param html_content: Código HTML del listado
    :param campaign_data: Diccionario con la info de la campanya actual
    :return: Llista d'enllaços a productes o diccionaris de producte bàsics
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    products = []
    
    # TODO: Extraure la llista de productes del catàleg.
    # Algunes dades es poden treure d'aquí directament, però Talles i Colors potser demanen 
    # entrar a la fitxa de producte amb parse_product_detail_page().
    
    # product = {
    #     'campaign_name': campaign_data.get('name', ''),
    #     'campaign_sector': campaign_data.get('sector', ''),
    #     'campaign_end_date': campaign_data.get('end_date', ''),
    #     'product_name': ...,
    #     'product_url': ...
    # }
    # products.append(product)
        
    return products

def parse_product_detail_page(html_content, base_product_data):
    """
    Extreu la informació de detall des de la URL individual d'un producte,
    imprescindible per als punts avançats com les talles o el color.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Copiem les dades que ens venen de la llista i anem afegint les específiques
    detail_product = base_product_data.copy()
    
    # TODO: Implementar camps sol·licitats a la teva proposta:
    # detail_product['description'] = Descripció del producte (Text)
    # detail_product['original_price'] = Preu original (Numèric)
    # detail_product['discount_price'] = Preu Privalia (Numèric)
    # detail_product['discount_percentage'] = Pot venir donat ("-60%") o calculat a partir dels preus
    # detail_product['available_sizes'] = Llista de talles disponibles vs esgotades
    # detail_product['color'] = Color de l'article (Text)
    
    return detail_product
