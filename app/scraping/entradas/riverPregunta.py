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

# Cargar las variables de entorno desde el archivo .env
load_dotenv(dotenv_path='/home/tobi/develop/scraping/.env.local')  # Ajusta la ruta a tu archivo .env si es necesario

# Acceder a las variables de entorno
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def enviar_mensaje_telegram(mensaje, chat_id=TELEGRAM_CHAT_ID):
    """Envía un mensaje al canal o chat de Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
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
    options.add_argument("--headless")  
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
            matching_products.append(product.text)  

    if matching_count > 0:
        mensaje = (
            f"🎟️ <b>¡Buenas noticias! Se encontraron {matching_count} entradas disponibles para River:</b>\n\n"
        )
        for product in matching_products:
            mensaje += f"🔹 {product}\n"
        mensaje += "\n⚡ <i>Asegúrate de obtenerlas antes de que se agoten.</i>"
    else:
        mensaje = (
            "❌ <b>No encontramos entradas disponibles para River en este momento.</b>\n\n"
            "💡 <i>Recomendación:</i> Sigue consultando, ya que las entradas pueden reponerse. "
            "También puedes verificar directamente en la plataforma oficial. 🏟️"
        )

    print(mensaje)  
    return mensaje

def get_updates(offset=None):
    """Obtiene las actualizaciones del bot de Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    params = {'offset': offset}
    response = requests.get(url, params=params)
    return response.json()

def obtener_ultimo_update_id():
    """Obtiene el último update_id al iniciar el script para ignorar mensajes antiguos."""
    updates = get_updates()
    if updates.get('result'):
        return updates['result'][-1]['update_id'] 
    return None

def process_message(message):
    """Procesa el mensaje recibido de Telegram."""
    try:
        text = message.get('text', '')  
        chat_id = message['chat']['id']

        # Normalizar el texto del mensaje
        text_lower = text.lower().strip()


        if "hay entradas para river" in text_lower:
            driver = setup_driver()
            try:
                login(driver)
                mensaje = findMatch(driver)  # Obtener mensaje de coincidencias
                enviar_mensaje_telegram(mensaje, chat_id)  # Enviar mensaje a Telegram
            finally:
                driver.quit()
        else:
            # Enviar una lista de comandos válidos
            comandos = (
                "⚙️ <b>Comandos válidos:</b>\n"
                "- <b>¿Hay entradas para River?</b>: Busca entradas relacionadas con River Plate.\n"
                "- <b>Ayuda</b>: Muestra esta lista de comandos.\n"
            )
            enviar_mensaje_telegram(comandos, chat_id)
    except Exception as e:
        print(f"Error al procesar el mensaje: {e}")
        enviar_mensaje_telegram("Hubo un error al procesar tu mensaje. Intenta de nuevo.", message['chat']['id'])

def main():
    offset = obtener_ultimo_update_id()  # Ignorar mensajes antiguos
    if offset:
        offset += 1  # Comenzar con mensajes nuevos

    while True:
        try:
            updates = get_updates(offset)
            if updates.get('result'): 
                for update in updates['result']:
                    message = update.get('message', {})  
                    if message:  
                        process_message(message)  
                        offset = update['update_id'] + 1  
            time.sleep(1) 
        except Exception as e:
            print(f"Error en el ciclo principal: {e}")
            time.sleep(5)  
if __name__ == "__main__":
    main()
