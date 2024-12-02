import sys
import requests

sys.path.append('/home/tobi/develop/python/app')

from botTelegram.telegramBot import enviar_mensaje_telegram

urls = [
    "http://localhost:5002/preciosAvo",
    "http://localhost:5002/preciosDelirante"
]

def extract_price(price_str):
    return float(price_str.replace("$", "").replace(",", "").strip())

all_products = []

# Recorrer las rutas y obtener los datos
for url in urls:
    try:
        response = requests.get(url)
        response.raise_for_status()     
        products = response.json()      
        all_products.extend(products)   
    except Exception as e:
        print(f"Error al obtener datos de {url}: {e}")

# Ordenar los productos por precio
sorted_products = sorted(all_products, key=lambda x: extract_price(x['price']))

# Obtener los 5 productos más baratos
cheapest_products = sorted_products[:5]

# Mostrar los 5 productos más baratos en consola
print("Los 5 productos más baratos:")
mensaje_telegram = "<b>Los 5 productos más baratos:</b>\n"  
for product in cheapest_products:
    product_text = f"🔹 <b>{product['name']}</b> - {product['price']}\n<a href='{product['url']}'>Ver producto</a>\n"
    mensaje_telegram += product_text
    print(f"Nombre: {product['name']}, Precio: {product['price']}, URL: {product['url']}")

# Enviar el mensaje a Telegram
try:
    enviar_mensaje_telegram(mensaje_telegram)
except Exception as e:
    print(f"Error al enviar mensaje a Telegram: {e}")
