from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import json

app = Flask(__name__)

# Inicializar Selenium y hacer scraping
def setup_driver():
    service = Service(ChromeDriverManager().install())
    options = Options()
    options.add_argument("--headless")  # Ejecutar en segundo plano sin abrir ventana del navegador
    return webdriver.Chrome(service=service, options=options)

def search_coffee(driver):
    url = "https://fuegotostadores.com/cafe-de-especialidad/"
    driver.get(url)
    products = []
    try:
        # Obtener los elementos de precio, título y enlaces
        price_spans = driver.find_elements(By.CSS_SELECTOR, "span.js-price-display.item-price")
        product_titles = driver.find_elements(By.CSS_SELECTOR, "a.js-item-name.item-name")
        product_links = driver.find_elements(By.CSS_SELECTOR, "a.js-item-name.item-name")

        if not price_spans or not product_titles or not product_links:
            print("No se encontraron precios, nombres o enlaces de productos.")
            return []

        for idx, (span, title, product_link) in enumerate(zip(price_spans, product_titles, product_links)):
            product_name = title.text
            product_href = product_link.get_attribute("href")
            price = span.text

            # Agregar los datos al arreglo de productos
            products.append({
                "name": product_name,
                "price": price,
                "url": product_href
            })
    except Exception as e:
        print("Error al extraer información de la página:", e)

    return products


@app.route('/preciosFuego', methods=['GET'])
def precios_delirante():
    # Configurar el driver de Selenium
    driver = setup_driver()
    
    try:
        # Llamar a la función de scraping y obtener los datos
        products = search_coffee(driver)
        if products:
            return jsonify(products), 200  # Devuelve los productos en formato JSON
        else:
            return jsonify({"message": "No se encontraron productos."}), 404
    finally:
        driver.quit()  # Cerrar el driver una vez terminado el scraping


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)
