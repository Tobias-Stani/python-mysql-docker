import requests
import os
import time
from dotenv import load_dotenv
from unidecode import unidecode

load_dotenv(dotenv_path='/home/tobi/develop/scraping/.env.local')

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

COMBINED_URL = "http://localhost:5002/productosCombinados"

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
    try:
        response = requests.get(COMBINED_URL)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error al obtener datos de {COMBINED_URL}: {e}")
        return []

def normalizar_numero(valor):
    if ',' in valor:
        return valor.replace(',', '.')
    elif '.' in valor and valor.count('.') == 1:
        return valor.replace('.', '')
    return valor

def es_numero(valor):
    try:
        float(normalizar_numero(valor))
        return True
    except ValueError:
        return False

def filter_products_by_price(products, min_price, max_price):
    return [product for product in products if min_price <= product['price'] <= max_price]

def ordenar_por_precio(products):
    return sorted(products, key=lambda x: x['price'])

def mostrar_ayuda(chat_id):

    mensaje_ayuda = """
🤖 <b><u>Comandos Disponibles para el Bot de Precios de Café:</u></b>

☕ <b>"cafe mas barato"</b> - Encuentra los <u>3 cafés más económicos</u> disponibles.  
☕ <b>"cafe mas caro"</b> - Descubre los <u>3 cafés más costosos</u>.  
☕ <b>"cafe entre X y Y"</b> - Lista cafés en un rango de precio que tú defines.  

<i>Ejemplos:</i>  
🔸 <b>cafe mas barato</b>  
🔸 <b>cafe mas caro</b>  
🔸 <b>cafe entre 500 y 1000</b>  

💡 <b><u>Tip Especial:</u></b> Usa estos comandos tal cual están escritos para obtener los mejores resultados.  
✨ Si tienes dudas, ¡no dudes en probar uno de los ejemplos! 🚀
"""
    enviar_mensaje_telegram(mensaje_ayuda, chat_id)


def process_message(message):
    try:
        text = unidecode(message.get('text', '').lower().strip())  # Normalizar el texto
        chat_id = message['chat']['id']
        
        # Mensaje de bienvenida
        if text == "/start":
            mensaje_bienvenida = """
🤖 <b>¡Hola! Bienvenido al Bot de Precios de Café ☕</b>

Estoy aquí para ayudarte a encontrar los mejores cafés disponibles al precio que necesitas.

<b>Comandos básicos:</b>  
- <b>"cafe mas barato"</b>: Encuentra los cafés más económicos.  
- <b>"cafe mas caro"</b>: Descubre los cafés más costosos.  
- <b>"cafe entre X y Y"</b>: Busca cafés dentro de un rango de precios.  

💡 Usa el comando que más te guste o escribe "ayuda" para ver más detalles. ¡Disfruta! 🚀
"""
            enviar_mensaje_telegram(mensaje_bienvenida, chat_id)
            return  # Detenemos aquí, ya que solo es un mensaje de bienvenida.

        text = text.replace("cafes", "cafe").replace("café", "cafe")

        # Procesar otros comandos
        try:
            if "cafe entre" in text:
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
                        response_message += f"🔹 <b>{product['name']}</b> - ${product['price']}\n<a href='{product['url']}'>Ver producto</a>\n"
                else:
                    response_message = f"No se encontraron cafés en el rango de ${min_price} a ${max_price}."

                enviar_mensaje_telegram(response_message, chat_id)

            elif "cafe mas barato" in text:
                all_products = obtener_productos()
                sorted_products = ordenar_por_precio(all_products)

                if sorted_products:
                    top_3_cheapest = sorted_products[:3]
                    response_message = "<b>Top 3 cafés más baratos:</b>\n"
                    for product in top_3_cheapest:
                        response_message += f"🔹 <b>{product['name']}</b> - ${product['price']}\n<a href='{product['url']}'>Ver producto</a>\n"
                else:
                    response_message = "No se encontraron cafés disponibles."

                enviar_mensaje_telegram(response_message, chat_id)

            elif "cafe mas caro" in text:
                all_products = obtener_productos()
                sorted_products = ordenar_por_precio(all_products)

                if sorted_products:
                    top_3_expensive = sorted_products[-3:]
                    response_message = "<b>Top 3 cafés más caros:</b>\n"
                    for product in top_3_expensive:
                        response_message += f"🔹 <b>{product['name']}</b> - ${product['price']}\n<a href='{product['url']}'>Ver producto</a>\n"
                else:
                    response_message = "No se encontraron cafés disponibles."

                enviar_mensaje_telegram(response_message, chat_id)

            else:
                # Si no se reconoce el comando, mostrar ayuda
                mostrar_ayuda(chat_id)

        except Exception as e:
            # Capturar cualquier error específico del procesamiento
            print(f"Error al procesar el mensaje: {e}")
            mostrar_ayuda(chat_id)

    except Exception as e:
        # Capturar cualquier error general
        print(f"Error general al procesar el mensaje: {e}")
        enviar_mensaje_telegram("Hubo un error al procesar tu mensaje. Por favor, revisa los comandos disponibles.", message['chat']['id'])



def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    params = {'offset': offset}
    response = requests.get(url, params=params)
    return response.json()

def main():
    offset = None
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

if __name__ == '__main__':
    main()