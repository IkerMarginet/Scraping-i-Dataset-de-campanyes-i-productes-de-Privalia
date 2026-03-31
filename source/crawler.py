import os
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.keys import Keys

from config import (
    PRIVALIA_EMAIL,
    PRIVALIA_PASSWORD,
    LOGIN_URL,
    USER_AGENT,
    TIMEOUT_SECONDS,
    DEBUG_DIR,
)


class PrivaliaCrawler:
    def __init__(self):
        options = webdriver.ChromeOptions()

        # Descomenta això si després vols executar-ho en segon pla
        # options.add_argument("--headless=new")

        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(f"user-agent={USER_AGENT}")

        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, TIMEOUT_SECONDS)

        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        print(
            "Crawler iniciat amb User-Agent: "
            f"{self.driver.execute_script('return navigator.userAgent')}"
        )

    def _save_debug_files(self, prefix="debug"):
        screenshot_name = os.path.join(DEBUG_DIR, f"{prefix}.png")
        html_name = os.path.join(DEBUG_DIR, f"{prefix}.html")

        self.driver.save_screenshot(screenshot_name)
        with open(html_name, "w", encoding="utf-8") as f:
            f.write(self.driver.page_source)

        print(f"S'han guardat fitxers de depuració: {screenshot_name}, {html_name}")

    def save_current_page(self, prefix):
        self._save_debug_files(prefix)

    def _find_first_present(self, selectors, timeout=6):
        for by, selector in selectors:
            try:
                return WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((by, selector))
                )
            except TimeoutException:
                continue
        return None

    def _click_first_clickable(self, selectors, timeout=5):
        for by, selector in selectors:
            try:
                el = WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable((by, selector))
                )
                self.driver.execute_script("arguments[0].click();", el)
                return True
            except TimeoutException:
                continue
            except Exception:
                continue
        return False

    def _switch_to_frame_with_element(self, selectors):
        self.driver.switch_to.default_content()

        found = self._find_first_present(selectors, timeout=2)
        if found is not None:
            return found

        iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
        for i, frame in enumerate(iframes):
            try:
                self.driver.switch_to.default_content()
                self.driver.switch_to.frame(frame)
                time.sleep(0.5)

                found = self._find_first_present(selectors, timeout=2)
                if found is not None:
                    print(f"Element trobat dins de l'iframe {i}.")
                    return found
            except Exception:
                continue

        self.driver.switch_to.default_content()
        return None

    def _scroll_page(self, max_scrolls=15, step=800, pause=0.8):
        """Scroll incremental per activar el lazy loading de cada secció."""
        current_pos = 0
        for _ in range(max_scrolls):
            current_pos += step
            self.driver.execute_script(f"window.scrollTo(0, {current_pos});")
            time.sleep(pause)
            page_height = self.driver.execute_script("return document.body.scrollHeight")
            if current_pos >= page_height:
                break
        # Tornar al principi
        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(0.5)

    def login(self):
        if not PRIVALIA_EMAIL or not PRIVALIA_PASSWORD:
            raise ValueError(
                "Falten les credencials. Defineix PRIVALIA_EMAIL i PRIVALIA_PASSWORD."
            )

        print("S'està iniciant el procés de login...")
        self.driver.get(LOGIN_URL)
        time.sleep(3)

        try:
            print("S'està esperant el bàner de galetes...")
            cookie_selectors = [
                (
                    By.XPATH,
                    "//button[contains(., 'Aceptar') or contains(., 'Accept') "
                    "or contains(., 'Aceptar todas') or contains(., 'Permitir todas') "
                    "or contains(., 'Allow all') or contains(., 'Consentir')]",
                ),
                (By.CSS_SELECTOR, "button[id*='accept']"),
                (By.CSS_SELECTOR, "button[class*='accept']"),
            ]

            for by, selector in cookie_selectors:
                try:
                    cookie_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    self.driver.execute_script("arguments[0].click();", cookie_button)
                    print("Galetes acceptades.")
                    time.sleep(2)
                    break
                except TimeoutException:
                    continue
        except Exception:
            print("No s'ha trobat el bàner de galetes o ja estava acceptat.")

        email_selectors = [
            (By.CSS_SELECTOR, "input[type='email']"),
            (By.CSS_SELECTOR, "input[name='email']"),
            (By.CSS_SELECTOR, "input[autocomplete='username']"),
            (
                By.XPATH,
                "//input[contains(translate(@placeholder,'EMAILCORREO','emailcorreo'),'email') "
                "or contains(translate(@placeholder,'EMAILCORREO','emailcorreo'),'correo')]",
            ),
        ]

        password_selectors = [
            (By.CSS_SELECTOR, "input[type='password']"),
            (By.CSS_SELECTOR, "input[name='password']"),
            (By.CSS_SELECTOR, "input[autocomplete='current-password']"),
        ]

        open_login_selectors = [
            (
                By.XPATH,
                "//*[self::a or self::button or self::span]"
                "[contains(normalize-space(.), 'Identificarme')]",
            ),
            (
                By.XPATH,
                "//*[self::a or self::button]"
                "[contains(normalize-space(.), 'Iniciar sesión')]",
            ),
            (
                By.XPATH,
                "//*[self::a or self::button]"
                "[contains(normalize-space(.), 'Entrar')]",
            ),
            (
                By.CSS_SELECTOR,
                "a[href*='login'], a[href*='signin'], a[href*='ident'], "
                "button[data-testid*='login']",
            ),
        ]

        continue_selectors = [
            (
                By.XPATH,
                "//button[contains(., 'Continuar') or contains(., 'Seguir') "
                "or contains(., 'Siguiente') or contains(., 'Identificarme') "
                "or contains(., 'Entrar') or contains(., 'Acceder')]",
            ),
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.XPATH, "//input[@type='submit']"),
        ]

        submit_selectors = [
            (
                By.XPATH,
                "//button[contains(., 'Entrar') or contains(., 'Acceder') "
                "or contains(., 'Iniciar sesión') or contains(., 'Identificarme')]",
            ),
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.XPATH, "//input[@type='submit']"),
        ]

        print("S'està comprovant si cal obrir el formulari de login...")
        email_input = self._switch_to_frame_with_element(email_selectors)

        if email_input is None:
            clicked = False
            for by, selector in open_login_selectors:
                elements = self.driver.find_elements(by, selector)
                for el in elements:
                    try:
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block: 'center'});", el
                        )
                        time.sleep(0.5)
                        self.driver.execute_script("arguments[0].click();", el)
                        print("S'ha premut el botó de login.")
                        time.sleep(3)

                        email_input = self._switch_to_frame_with_element(email_selectors)
                        if email_input is not None:
                            clicked = True
                            break
                    except Exception:
                        continue
                if clicked:
                    break

        if email_input is None:
            # En cas d'error crític, guardem sempre per saber què ha passat
            self._save_debug_files("error_login_no_email")
            raise TimeoutException(
                "No ha aparegut el camp de correu electrònic. Revisa debug/debug_login_no_email.*"
            )

        print("S'està omplint el correu electrònic...")
        email_input.clear()
        email_input.send_keys(PRIVALIA_EMAIL)
        time.sleep(1)

        password_input = self._switch_to_frame_with_element(password_selectors)

        if password_input is None:
            print("La contrasenya encara no apareix. S'està provant un pas intermedi...")
            clicked_continue = self._click_first_clickable(continue_selectors, timeout=5)

            if not clicked_continue:
                try:
                    email_input.send_keys(Keys.ENTER)
                    clicked_continue = True
                except Exception:
                    pass

            time.sleep(3)
            password_input = self._switch_to_frame_with_element(password_selectors)

        if password_input is None:
            self._save_debug_files("debug_login_no_password")
            raise TimeoutException(
                "No ha aparegut el camp de contrasenya. Revisa debug/debug_login_no_password.*"
            )

        print("S'està omplint la contrasenya...")
        password_input.clear()
        password_input.send_keys(PRIVALIA_PASSWORD)
        time.sleep(1)

        clicked_submit = self._click_first_clickable(submit_selectors, timeout=5)
        if not clicked_submit:
            password_input.send_keys(Keys.ENTER)

        print("Credencials enviades.")
        time.sleep(6)
        self.driver.switch_to.default_content()

    def get_html(self, url, wait_seconds=2, scroll=False, scroll_steps=5, debug_prefix=None):
        print(f"S'està navegant a: {url}")
        self.driver.get(url)
        time.sleep(wait_seconds)

        if scroll:
            self._scroll_page(max_scrolls=scroll_steps)

        html = self.driver.page_source

        if debug_prefix:
            self._save_debug_files(debug_prefix)

        return html

    def get_product_html_with_interaction(self, url, wait_seconds=3, debug_prefix=None):
        """Navega al producte i clica el desplegable de talles per carregar-les."""
        print(f" -> [Interactuant] {url}")
        self.driver.get(url)
        time.sleep(wait_seconds)

        # Intentar clicar el desplegable de talles
        dropdown_selectors = [
            (By.CSS_SELECTOR, "button[data-testid^='model-dropdown-']"),
            (By.CSS_SELECTOR, "button[role='combobox']"),
            (By.CSS_SELECTOR, "div[class*='ModelDropdown'] button"),
            (By.XPATH, "//button[contains(., 'Elige una talla') or contains(., 'Selecciona')]"),
        ]

        found_dropdown = None
        for by, selector in dropdown_selectors:
            try:
                el = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((by, selector))
                )
                if el.is_displayed():
                    found_dropdown = el
                    print(f"    [INFO] Botó trobat amb: {selector}")
                    break
            except Exception:
                continue

        if found_dropdown:
            try:
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", found_dropdown)
                time.sleep(0.5)
                # Intentar clic directe i si falla JS click
                try:
                    found_dropdown.click()
                except Exception:
                    self.driver.execute_script("arguments[0].click();", found_dropdown)
                
                print("    [OK] Desplegable clicat.")
                
                # Esperar que apareguin els elements de la llista
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "li[role='option'], [data-testid^='model-']"))
                )
                time.sleep(1.5) # Temps per a les animacions i JS
                print("    [OK] Talles detectades al DOM.")
            except Exception as e:
                print(f"    [AVÍS] Error en clicar o esperar talles: {e}")
        else:
            print("    [AVÍS] No s'ha trobat cap botó de talles (potser talla única).")

        html = self.driver.page_source
        if debug_prefix:
            self._save_debug_files(debug_prefix)
        return html

    def close(self):
        if self.driver:
            try:
                self.driver.quit()
                print("El navegador s'ha tancat correctament.")
            except WebDriverException:
                pass