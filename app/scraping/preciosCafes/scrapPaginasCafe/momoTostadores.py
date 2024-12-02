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

def search_MomoTostadores(driver):
    url = "https://momotostadores.com/"  
    driver.get(url)
    products = []

    try:
        # Buscar los enlaces de los productos
        product_links = driver.find_elements(By.CSS_SELECTOR, "a.pp-loop-product__link")
        price_elements = driver.find_elements(By.CSS_SELECTOR, "span.price > span.woocommerce-Price-amount.amount bdi")

        if not product_links or not price_elements:
            print("No se encontraron productos o precios en la página.")
            return []

        # Iterar sobre los productos encontrados
        for product_link, price_element in zip(product_links, price_elements):
            product_name = product_link.find_element(By.CSS_SELECTOR, "h3.woocommerce-loop-product__title").text
            product_url = product_link.get_attribute("href")
            price = price_element.text.strip()  # Obtener texto del precio desde el <bdi>

            # Normalizar el precio
            normalized_price = (price)

            # Guardar los productos encontrados
            products.append({
                "name": product_name,
                "price": normalized_price,
                "url": product_url
            })

    except Exception as e:
        print(f"Error al extraer los productos de Momo Tostadores: {e}")

    return products



@app.route('/preciosMomo', methods=['GET'])
def precios_Momo():
    # Configurar el driver de Selenium
    driver = setup_driver()
    
    try:
        # Llamar a la función de scraping y obtener los datos
        products = search_MomoTostadores(driver)
        if products:
            return jsonify(products), 200  # Devuelve los productos en formato JSON
        else:
            return jsonify({"message": "No se encontraron productos."}), 404
    finally:
        driver.quit()  # Cerrar el driver una vez terminado el scraping


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)
