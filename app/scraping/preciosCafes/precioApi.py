from flask import Flask, request, jsonify
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)

def setup_driver():
    service = Service(ChromeDriverManager().install())
    options = Options()
    options.add_argument("--headless") 
    return webdriver.Chrome(service=service, options=options)


def normalize_price(price):
    """
    Normaliza el precio eliminando caracteres no numéricos excepto el punto.
    Convierte el precio a un número flotante para consistencia.
    """
    price_cleaned = re.sub(r'[^\d]', '', price)  # Elimina caracteres no numéricos
    return int(price_cleaned)

def search_coffee(driver):
    url = "https://fuegotostadores.com/cafe-de-especialidad/"
    driver.get(url)
    products = []
    try:
        price_spans = driver.find_elements(By.CSS_SELECTOR, "span.js-price-display.item-price")
        product_titles = driver.find_elements(By.CSS_SELECTOR, "a.js-item-name.item-name")
        product_links = driver.find_elements(By.CSS_SELECTOR, "a.js-item-name.item-name")

        if not price_spans or not product_titles or not product_links:
            print("No se encontraron precios, nombres o enlaces de productos.")
            return []

        for span, title, product_link in zip(price_spans, product_titles, product_links):
            product_name = title.text
            product_href = product_link.get_attribute("href")
            price = normalize_price(span.text)

            products.append({
                "name": product_name,
                "price": price,
                "url": product_href
            })
    except Exception as e:
        print("Error al extraer información de la página:", e)

    return products

def search_delirante(driver):
    url = "https://cafedelirante.com.ar/tienda/cafe/"
    driver.get(url)
    products = []
    try:
        price_spans = driver.find_elements(By.CSS_SELECTOR, "span.woocommerce-Price-amount.amount")
        product_titles = driver.find_elements(By.CSS_SELECTOR, "p.name.product-title > a.woocommerce-LoopProduct-link")
        product_links = driver.find_elements(By.CSS_SELECTOR, "p.name.product-title > a.woocommerce-LoopProduct-link")

        if not price_spans or not product_titles or not product_links:
            print("No se encontraron precios, nombres o enlaces de productos.")
            return []

        for span, title, product_link in zip(price_spans, product_titles, product_links):
            product_name = title.text
            product_href = product_link.get_attribute("href")
            price = normalize_price(span.text)

            products.append({
                "name": product_name,
                "price": price,
                "url": product_href
            })
    except Exception as e:
        print("Error al extraer información de la página:", e)

    return products

def search_avo(driver):
    url = "https://www.avocoffeeroasters.com.ar/cafe--prod--1"
    driver.get(url)
    products = []
    try:
        price_spans = driver.find_elements(By.CSS_SELECTOR, "div.price > span")
        product_links = driver.find_elements(By.CSS_SELECTOR, "h4 > a.titprod")

        if not price_spans or not product_links:
            print("No se encontraron precios o enlaces de productos.")
            return []

        for span, product_link in zip(price_spans, product_links):
            product_name = product_link.text
            product_href = product_link.get_attribute("href")
            price = normalize_price(span.text)

            products.append({
                "name": product_name,
                "price": price,
                "url": product_href
            })
    except Exception as e:
        print("Error al extraer información de la página:", e)

    return products

def search_puerto_blast(driver):
    url = "https://cafepuertoblest.com/cafe-especial/?mpage=2"  
    driver.get(url)
    products = []

    try:
        # Buscar todos los productos en la página
        product_elements = driver.find_elements(By.CSS_SELECTOR, "a.item-link")  # Encuentra todos los enlaces de productos

        if not product_elements:
            print("No se encontraron productos en la página.")
            return []

        for product_element in product_elements:
            product_name = product_element.find_element(By.CSS_SELECTOR, "div.js-item-name").text  # Título
            product_url = product_element.get_attribute("href")  # Enlace
            price_element = product_element.find_element(By.CSS_SELECTOR, "span.js-price-display.item-price")  # Precio
            price = normalize_price(price_element.text)  # Normaliza el precio

            # Guardar los productos encontrados
            products.append({
                "name": product_name,
                "price": price,
                "url": product_url
            })

    except Exception as e:
        print("Error al extraer información de la página:", e)

    return products


@app.route('/preciosPuertoBlest', methods=['GET'])
def precios_puerto_blast():
    driver = setup_driver()
    try:
        # Llamar a la función de scraping y obtener los productos
        products = search_puerto_blast(driver)
        if products:
            return jsonify(products), 200  # Devuelve los productos en formato JSON
        else:
            return jsonify({"message": "No se encontraron productos en Café Puerto Blast."}), 404
    finally:
        driver.quit()  # Cerrar el driver una vez terminado el scraping


@app.route('/preciosFuego', methods=['GET'])
def precios_fuego():
    driver = setup_driver()
    try:
        products = search_coffee(driver)
        if products:
            return jsonify(products), 200
        else:
            return jsonify({"message": "No se encontraron productos en Fuego Tostadores."}), 404
    finally:
        driver.quit()

@app.route('/preciosDelirante', methods=['GET'])
def precios_delirante():
    driver = setup_driver()
    try:
        products = search_delirante(driver)
        if products:
            return jsonify(products), 200
        else:
            return jsonify({"message": "No se encontraron productos en Café Delirante."}), 404
    finally:
        driver.quit()

@app.route('/preciosAvo', methods=['GET'])
def precios_avo():
    driver = setup_driver()
    try:
        products = search_avo(driver)
        if products:
            return jsonify(products), 200
        else:
            return jsonify({"message": "No se encontraron productos en Avo Coffee Roasters."}), 404
    finally:
        driver.quit()

@app.route('/productosCombinados', methods=['GET'])
def productos_combinados():
    driver = setup_driver()
    try:
        # Obtener productos de todas las rutas
        fuego_products = search_coffee(driver)
        delirante_products = search_delirante(driver)
        avo_products = search_avo(driver)
        puerto_blast_products = search_puerto_blast(driver)

        # Combinar todos los productos
        all_products = fuego_products + delirante_products + avo_products + puerto_blast_products

        # Añadir el campo 'id' autoincremental
        for idx, product in enumerate(all_products, start=1):
            product['id'] = idx  # Asignar un ID único

        return jsonify(all_products), 200
    finally:
        driver.quit()  # Cerrar el driver una vez terminado el scraping

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5002)
