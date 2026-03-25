import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from config import PRIVALIA_EMAIL, PRIVALIA_PASSWORD, LOGIN_URL, USER_AGENT

class PrivaliaCrawler:
    def __init__(self):
        # Configurar las opciones del navegador
        options = webdriver.ChromeOptions()
        # options.add_argument('--headless') # Descomentar para ejecutar sin interfaz gráfica (una vez funcione)
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # Inyectar el User-Agent explícito (Compleix un dels criteris de complexitat)
        options.add_argument(f'user-agent={USER_AGENT}')
        
        # Iniciar el navegador Chrome
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 15)
        
        print(f"Crawler iniciat amb User-Agent: {self.driver.execute_script('return navigator.userAgent')}")

    def login(self):
        """
        Navega a Privalia y realiza el proceso de login automático.
        """
        print("Iniciando proceso de login...")
        self.driver.get(LOGIN_URL)
        
        # 1. Aceptar Cookies
        try:
            print("Esperando banner de cookies...")
            cookie_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Aceptar') or contains(text(), 'Accept')]"))
            )
            cookie_button.click()
            print("Cookies aceptadas.")
            time.sleep(2)
        except TimeoutException:
            print("No se encontró el banner de cookies o ya estaba aceptado.")

        # 2. Rellenar formulario de login
        try:
            print("Buscando campos de login...")
            # Todo: Asegúrate de que estos selectores XPATH/CSS son los correctos analizando la web
            email_input = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@type='email' or @name='email']"))
            )
            password_input = self.driver.find_element(By.XPATH, "//input[@type='password' or @name='password']")
            
            email_input.clear()
            email_input.send_keys(PRIVALIA_EMAIL)
            
            password_input.clear()
            password_input.send_keys(PRIVALIA_PASSWORD)
            
            # Botón de submit
            submit_button = self.driver.find_element(By.XPATH, "//button[@type='submit' or contains(text(), 'Entrar')]")
            submit_button.click()
            
            print("Credenciales enviadas.")
            # Esperar a que el login se complete exitosamente (ej. buscando un elemento de usuario o esperando redirección)
            time.sleep(5)
            
        except TimeoutException as e:
            print("Error: No se pudo encontrar el formulario de login. Revisa los selectores.")
            raise e

    def get_html(self, url):
        """
        Navega a una URL específica (estando ya logueado) y devuelve el HTML.
        """
        print(f"Navegando a: {url}")
        self.driver.get(url)
        # Esperar un poco a que el JS renderice la página
        time.sleep(4)
        return self.driver.page_source

    def close(self):
        """
        Cierra el navegador.
        """
        if self.driver:
            self.driver.quit()
