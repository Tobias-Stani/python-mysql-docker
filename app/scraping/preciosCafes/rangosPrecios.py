import requests
import os
import time
from dotenv import load_dotenv
from unidecode import unidecode

load_dotenv(dotenv_path='/home/tobi/develop/scraping/.env.local')

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# URLs de las APIs
urls = [
    "http://localhost:5002/preciosAvo",
    "http://localhost:5002/preciosDelirante"
]

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

def obtener_productos():
    all_products = []
    for url in urls:
        try:
            response = requests.get(url)
            response.raise_for_status()
            products = response.json()
            all_products.extend(products)
        except Exception as e:
            print(f"Error al obtener datos de {url}: {e}")
    return all_products


def extract_price(price_str):
    return float(price_str.replace("$", "").replace(",", "").strip())

# Función para filtrar productos según el rango de precio
def filter_products_by_price(products, min_price, max_price):
    return [product for product in products if min_price <= extract_price(product['price']) <= max_price]

# Función para ordenar los productos por precio (de menor a mayor)
def ordenar_por_precio(products):
    return sorted(products, key=lambda x: extract_price(x['price']))

# Función para verificar si un valor es numérico
def es_numero(valor):
    try:
        float(valor)
        return True
    except ValueError:
        return False


def process_message(message):
    text = message['text']
    chat_id = message['chat']['id']

    text = unidecode(text.lower().strip())

    text = text.replace("cafes", "cafe").replace("café", "cafe")

    # Comprobar si el mensaje contiene la palabra clave "cafe entre"
    if "cafe entre" in text:
        try:
            parts = text.split()
            min_price_str = parts[2]  
            max_price_str = parts[4]  

            if not es_numero(min_price_str) or not es_numero(max_price_str):
                enviar_mensaje_telegram("Por favor, asegúrate de ingresar números válidos para los precios.", chat_id)
                return

            min_price = float(min_price_str)
            max_price = float(max_price_str)

            if min_price <= 0 or max_price <= 0:
                enviar_mensaje_telegram("Los precios deben ser mayores a 0.", chat_id)
                return


            if min_price > max_price:
                enviar_mensaje_telegram("El precio mínimo no puede ser mayor que el precio máximo.", chat_id)
                return

            all_products = obtener_productos()

            filtered_products = filter_products_by_price(all_products, min_price, max_price)

            sorted_products = ordenar_por_precio(filtered_products)

            if sorted_products:
                response_message = f"<b>Cafés en el rango de ${min_price} a ${max_price}:</b>\n"
                for product in sorted_products:
                    response_message += f"🔹 <b>{product['name']}</b> - {product['price']}\n<a href='{product['url']}'>Ver producto</a>\n"
            else:
                response_message = f"No se encontraron cafés en el rango de ${min_price} a ${max_price}."

            enviar_mensaje_telegram(response_message, chat_id)

        except Exception as e:
            enviar_mensaje_telegram("Hubo un error procesando tu solicitud. Asegúrate de que el formato sea correcto: 'cafe entre <precio_min> y <precio_max>'.", chat_id)
            print(f"Error al procesar el mensaje: {e}")
    else:
        enviar_mensaje_telegram("Por favor, ingrese un rango de precios con el formato: 'cafe entre <precio_min> y <precio_max>'", chat_id)


def main():
    offset = None
    while True:
        updates = get_updates(offset)
        if updates['result']:
            for update in updates['result']:
                message = update['message']
                process_message(message)
                offset = update['update_id'] + 1  
        time.sleep(1)  

def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    params = {'offset': offset}
    response = requests.get(url, params=params)
    return response.json()

if __name__ == '__main__':
    main()
