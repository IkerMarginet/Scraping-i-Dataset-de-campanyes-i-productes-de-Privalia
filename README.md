# Scraper de Privalia 🛍️📊

Aquest projecte és un Web Scraper automatitzat dissenyat per extreure dades sobre campanyes i productes de la plataforma de vendes privades [Privalia](https://es.privalia.com/). Ha estat desenvolupat com a part de la **Pràctica 1 (PRACT1)** de l'assignatura *Tipologia i Cicle de vida de les dades* del Màster en Data Science.

## 👥 Integrants del grup
- **Iker Marginet Ballester**
- **Albert Pérez Costa**

## 📝 Descripció

L'objectiu principal d'aquesta eina és la creació d'un *dataset* estructurat (basa de dades) apte per a l'anàlisi de dades, extraient:
- **Campanyes actuals**: Noms de camps (marques), nombre de productes totals i únics, categories disponibles i data de finalització.
- **Productes**: Identificadors, noms, preus originals i rebaixats, percentatge de descompte, colors, disponibilitat de talles, imatges associades i subcategories o seccions.

El projecte fa ús de tècniques de *web scraping* combinant la interacció amb navegadors (degut a la naturalesa altament dinàmica de la web principal i els múltiples *scrolls* necessaris per carregar els objectes a causa del *lazy loading*) amb l'anàlisi estàtic del DOM.

## 🗂️ Estructura i Descripció dels Arxius del Repositori

```text
privalia-scraping/
├── dataset/                     # Directori on es desen els resultats en brut de les dades extretes
│   ├── privalia_campaigns.csv   # Dataset amb el meta-registre de les marques i campanyes recollides
│   └── privalia_products.csv    # Dataset amb els detalls exhaustius de tota la roba i productes
├── docs/                        # Documentació tècnica i arxius auxiliars generats pel codi
│   └── imatges/                 # Captures de pantalla i HTML de depuració
├── source/                      # Codi font central (Scripts complets de l'aplicació en Python)
│   ├── main.py                  # Script principal exclusiu d'entrada que orquestra la feina del scraper
│   ├── config.py                # Arxiu de paràmetres, límits i credencials (configuració)
│   ├── crawler.py               # Lògica d'automatització robòtica i del navegador per Selenium
│   ├── parser.py                # Mòdul pel sanejament de strings i mapeig d'etiquetes amb BeautifulSoup
│   └── storage.py               # Mòdul de gestió de fitxers i funcions d'escriptura als llistats CSV
├── requirements.txt             # Llistat de biblioteques base i dependències (BeautifulSoup, Selenium)
└── README.md                    # Fitxer informatiu i manual de repositori (aquest actual arxiu)
```

## ⚙️ Requisits

L'entorn requereix tenir instal·lat **Python 3.8+** a la teva màquina local i instal·lar les llibreries del llistat de requeriments de base.

Dependències i llibreries clau:
- `selenium` (per controlar les interaccions del navegador web i rendir l'HTML)
- `beautifulsoup4` (per al processament i mapeig ràpid dels arbres i etiquetes de l'HTML)

*\*Nota:* Selenium requereix la interacció amb el teu propi navegador local (per exemple Chrome, Edge) i utilitzarà els seus propis Webdrivers que avui dia se solen carregar o autogestionar.

## 🚀 Instal·lació

1. **Clona o adquireix aquest repositori / carpeta**.
2. **Navega a la carpeta principal del projecte** des del teu intèrpret o línia de comandes:
   ```bash
   cd privalia-scraping
   ```
3. *(Opcional)* **Crea un entorn virtual (venv), altament recomanat**:
   ```bash
   # Creació entorn
   python -m venv venv
   
   # Activació de l'entorn (Windows)
   venv\Scripts\activate
   
   # Activació de l'entorn (Mac/Linux)
   source venv/bin/activate
   ```
4. **Instal·la les dependències**:
   ```bash
   pip install -r requirements.txt
   ```
5. **Configuració Extra**: Pots editar el fitxer `source/config.py` directament per a canviar i gestionar el compte d'accés (per defecte usuari base per realitzar proves) i modificar així els diferents límits de l'scraper o els retards generats: com a `MAX_CAMPAIGNS_TO_VISIT`, `MAX_PRODUCTS_PER_CAMPAIGN_TO_VISIT` i més.

## 🖥️ Ús, Paràmetres i Exemples Replicables

L'execució se centralitza en l'ús del fitxer principal `main.py` de la carpeta pròpia de `source` mentre que les adaptacions prèvies depenen absolutament de `config.py`.

### Paràmetres del Script
Abans d'executar l'aplicació, obre l'arxiu `source/config.py` on podràs controlar estretament variables que actuaran com a paràmetres clau introduïts a l'hora del disseny:

* **Credencials de servei:** `PRIVALIA_EMAIL` i `PRIVALIA_PASSWORD` estableixen el mètode d'autenticació inicialment demanat i necessari del sistema. 
* **Paràmetres d'Escaneig i Paginació:**
  * `MAX_CAMPAIGNS_TO_VISIT`: Nombre màxim de campanyes global (marques) a processar seqüencialment des de la pàgina principal.
  * `MAX_SUBPAGES_PER_CAMPAIGN`: Límit del topall per a les quantitats de subcategories ("Vestits", "Sabates") a desplaçar.
  * `MAX_PRODUCTS_PER_CAMPAIGN_TO_VISIT`: Límits del topall per escollir l'acumulat absolut de productes parsejats sobre tota l'activitat d'una campanya.
* **Tolerància i Control d'Avaries:** `REQUEST_DELAY_SECONDS` incrementa o rebaixa el descans entre processos. `TIMEOUT_SECONDS` establirà els blocs tolerats.

### Exemple 1: Execució massiva programada per defecte

Per dur a terme aquest exemple es farà ús de formats relaxats basats en voler capturar màxima informació, el codi ve així pel cap baix. Fent via al terminal per on es vulgui actuar:

```bash
python source/main.py
```

**(Al terminal intern se'ns demanarà si volem mode de depuració. Al escriure `n` el procés iniciarà del zero en mode silenciós i net i exportarà només els fets capturats, un darrera un altre cap als nostres fitxers dataset CSV fins acabar els màxims designats)**

### Exemple 2: Execució ràpida delimitada al testeig (1 Campanya, 5 Productes)

Viatgem i ens adrecem cap a dins de `source/config.py` per afegir i canviar les limitacions variables des de l'inici del fitxer a valors controlats:

```python
MAX_CAMPAIGNS_TO_VISIT = 1
MAX_PRODUCTS_PER_CAMPAIGN_TO_VISIT = 5
```

Llavors tornant per guardar el daltibaix encenem altra volta utilitzant mode de depuració (`s` a la pregunta de selecció inicial interactiva) afegint un control més de traça d'assessorament:

```bash
python source/main.py
```
*(Es farà i desaran 1 única campanya global juntament amb només un total màx de 5 productes i exportarà captures HTML en directe a `docs/imatges` per si calia fer un diagnòstic de visualització)*


## 📊 Dataset i DOI de Zenodo

El *dataset* generat durant aquesta pràctica i vinculat al procediment avaluatori roman penjat d'acord amb els compromisos pel projecte educatiu sota un registre i preservació lliure des de la plataforma de dades obertes d'investigació tipus Zenodo per assegurar la possibilitat d'explorar, fer servir i fomentar tot un procés replicable.

* **DOI de Zenodo Dataset**: `[Substituir amb el link de Zenodo DOI quan es generi, ex: 10.5281/zenodo.1234567]`

## ⚖️ Consideracions Ètiques y d'Ús

Les dades recavades són únicament dirigides a ús pedagògic orientat i estrictes a les indicacions d'assignatures pràctiques universitàries. 
S'han utilitzat retards d'execuciò intencis i obligatoris en la descàrrega mitjançant pauses constants temporitzades que limiten els problemes de sobresaturació al tràfic de la pàgina servidora evitant per darrere danys a aquesta plataforma. Tot plegat permetent emular constantment i fidel al trànsit que causaria directament des del ratolí un o diversos usuaris de ritme estàndard, evitant aturades tècniques o dades massives sense consentiment en el cas d'ús.

---
**PRACT1 - Tipologia i Cicle de vida de les dades | Master en Data Science**
