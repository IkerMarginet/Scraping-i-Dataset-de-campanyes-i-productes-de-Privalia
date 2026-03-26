import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys

from config import (
    PRIVALIA_EMAIL,
    PRIVALIA_PASSWORD,
    LOGIN_URL,
    USER_AGENT,
    TIMEOUT_SECONDS,
)


class PrivaliaCrawler:
    def __init__(self):
        options = webdriver.ChromeOptions()

        # Treu el comentari quan tot funcioni
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

    def _save_debug_files(self, prefix="debug_login"):
        screenshot_name = f"{prefix}.png"
        html_name = f"{prefix}.html"

        self.driver.save_screenshot(screenshot_name)
        with open(html_name, "w", encoding="utf-8") as f:
            f.write(self.driver.page_source)

        print(f"S'han guardat fitxers de debug: {screenshot_name}, {html_name}")

    def _find_first_present(self, selectors, timeout=6):
        for by, selector in selectors:
            try:
                return WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((by, selector))
                )
            except TimeoutException:
                continue
        return None

    def _find_first_visible(self, selectors, timeout=6):
        for by, selector in selectors:
            try:
                return WebDriverWait(self.driver, timeout).until(
                    EC.visibility_of_element_located((by, selector))
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

        # Primer mirar al document principal
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

    def login(self):
        print("Iniciando proceso de login...")
        self.driver.get(LOGIN_URL)
        time.sleep(3)

        # 1. Cookies
        try:
            print("Esperando banner de cookies...")
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
                    print("Cookies aceptadas.")
                    time.sleep(2)
                    break
                except TimeoutException:
                    continue
        except Exception:
            print("No se encontró el banner de cookies o ya estaba aceptado.")

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

        # 2. Obrir login si cal
        print("Comprobando si hay que abrir el login...")
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
                        print("Botón de login pulsado.")
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
            self._save_debug_files("debug_login_no_email")
            raise TimeoutException(
                "No apareció el campo email. Revisa debug_login_no_email.png y .html."
            )

        # 3. Escriure email
        print("Rellenando email...")
        email_input.clear()
        email_input.send_keys(PRIVALIA_EMAIL)
        time.sleep(1)

        # 4. Provar si password ja existeix
        password_input = self._switch_to_frame_with_element(password_selectors)

        # 5. Si no existeix, fer pas intermedi
        if password_input is None:
            print("El password no aparece aún. Probando paso intermedio...")
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
                "No apareció el campo password. Revisa debug_login_no_password.png y .html."
            )

        # 6. Escriure password
        print("Rellenando password...")
        password_input.clear()
        password_input.send_keys(PRIVALIA_PASSWORD)
        time.sleep(1)

        # 7. Enviar login final
        clicked_submit = self._click_first_clickable(submit_selectors, timeout=5)
        if not clicked_submit:
            password_input.send_keys(Keys.ENTER)

        print("Credenciales enviadas.")
        time.sleep(6)
        self.driver.switch_to.default_content()

    def get_html(self, url):
        print(f"Navegando a: {url}")
        self.driver.get(url)
        time.sleep(4)
        return self.driver.page_source

    def close(self):
        if self.driver:
            self.driver.quit()