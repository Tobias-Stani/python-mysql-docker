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
    options.add_argument("--window-size=1250,850")
    options.add_argument("--headless")  # Ejecutar en segundo plano sin abrir ventana del navegador
    return webdriver.Chrome(service=service, options=options)

def search_coffee(driver):
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
            price = (price_element.text)  # Normaliza el precio

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
