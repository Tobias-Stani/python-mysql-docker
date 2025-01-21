import requests
import os
from dotenv import load_dotenv
from selenium.webdriver import Chrome
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import schedule
import time
import logging

# Cargar las variables de entorno desde el archivo .env
load_dotenv(dotenv_path='/home/tobi/develop/scraping/.env.local')  

# Configurar el logger para imprimir mensajes en la consola
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

# Acceder a las variables de entorno
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def enviar_mensaje_telegram(mensaje):
    """Envía un mensaje al canal o chat de Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': mensaje,
        'parse_mode': 'HTML'
    }
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        if response.status_code == 200:
            print("Mensaje enviado exitosamente a Telegram.")
        else:
            print(f"Error al enviar el mensaje a Telegram. Código de respuesta: {response.status_code}")
            print(f"Respuesta del servidor: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Excepción al enviar el mensaje: {e}")

def setup_driver():
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1250,850")
    options.add_argument("--headless")  # Ejecuta el navegador en modo headless (sin UI)
    return Chrome(service=service, options=options)

def login(driver):
    driver.get("https://serviclub.com.ar/4633-espectaculos-")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'h5')))

def findMatch(driver):
    keywords = ["RIVER"]  # Palabras clave a buscar
    products = driver.find_elements(By.CLASS_NAME, "product-title-item")
    
    matching_count = 0
    matching_products = []

    for product in products:
        product_name = product.text.upper()
        if any(keyword in product_name for keyword in keywords):
            matching_count += 1
            matching_products.append(product.text)  # Guardar el producto coincidente

    # Preparar el mensaje solo si hay productos coincidentes
    if matching_count > 0:
        mensaje = f"🎟️ <b>Se encontraron {matching_count} productos:</b>\n\n"
        for product in matching_products:
            mensaje += f"- {product}\n"
        logging.info("Productos encontrados: Se enviará un mensaje a Telegram.✅✅✅✅✅✅✅")
        return mensaje  # Devuelve el mensaje si hay coincidencias
    else:
        logging.info("No se encontraron productos con las palabras clave.❌❌❌❌❌❌❌")
        return None  # Devuelve None si no hay coincidencias


def main():
    driver = setup_driver()
    try:
        login(driver)
        mensaje = findMatch(driver)  # Obtener mensaje de coincidencias
        if mensaje:  # Solo enviar mensaje si no es None
            enviar_mensaje_telegram(mensaje)
        else:
            logging.info("No se enviará ningún mensaje a Telegram.")
    finally:
        driver.quit()


# Configurar el cronograma con schedule
schedule.every(3).minutes.do(main)  # Ejecutar cada 15 minutos

if __name__ == "__main__":
    print("Ejecutando la tarea inicial...")
    main()
    print("Programador de tareas iniciado. Ejecutando cada 15 minutos...")
    while True:
        schedule.run_pending()  # Ejecutar tareas programadas
        time.sleep(1)  # Pausar para evitar uso intensivo de CPU