import requests
import os
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env
load_dotenv(dotenv_path='/home/tobi/develop/scraping/.env.local') 

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

enviar_mensaje_telegram("¡Hola! Soy Entradas")
