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
import time
import schedule  # Librería para programar tareas

# Cargar las variables de entorno desde el archivo .env
load_dotenv(dotenv_path='/home/tobi/develop/scraping/.env.local')  

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
    options.add_argument("--headless") 
    return Chrome(service=service, options=options)

def login(driver):
    driver.get("https://serviclub.com.ar/4633-espectaculos-")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'h5')))

def findMatch(driver):
    keywords = ["RIVER", "ENTRADA", "ENTRADAS"]
    products = driver.find_elements(By.CLASS_NAME, "product-title-item")
    
    matching_products = []  # Lista para almacenar productos coincidentes

    for product in products:
        product_name = product.text.upper()  # Convertir a mayúsculas para hacer la búsqueda más precisa
        if any(keyword in product_name for keyword in keywords):
            etiqueta = "#ProductoEncontrado"
            mensaje = f"{etiqueta}\n{product_name}"  # Crear mensaje con etiqueta
            matching_products.append(mensaje)  # Agregar a la lista de productos
    
    # Preparar el mensaje final
    if matching_products:
        mensaje = "Se encontraron los siguientes productos:\n\n" + \
                  "\n".join(f"<pre>{producto}</pre>" for producto in matching_products)
    else:
        mensaje = "No se encontraron productos con las palabras clave."
    
    return mensaje

def tarea():
    """Ejecuta la tarea programada."""
    driver = setup_driver()  
    login(driver)  
    
    # Obtener el mensaje de la función findMatch
    resultado = findMatch(driver)

    # Enviar el mensaje completo a Telegram
    enviar_mensaje_telegram(resultado)

    driver.quit()  # Cierra el navegador al finalizar

if __name__ == "__main__":
    print("Ejecutando la tarea única...")
    tarea()  # Ejecutar la tarea inmediatamente

