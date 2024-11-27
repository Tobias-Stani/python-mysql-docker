import os
import time
from flask import Flask, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)

def setup_driver():
    service = Service(ChromeDriverManager().install())
    options = Options()
    options.add_argument("--window-size=1250,850")
    options.add_argument("--headless")  
    return webdriver.Chrome(service=service, options=options)

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

        for idx, (span, product_link) in enumerate(zip(price_spans, product_links)):
            product_name = product_link.text
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

@app.route('/preciosAvo', methods=['GET'])
def precios_avo():
    # Configurar el driver de Selenium
    driver = setup_driver()

    try:
        products = search_avo(driver)
        if products:
            return jsonify(products), 200  # Devuelve los productos en formato JSON
        else:
            return jsonify({"message": "No se encontraron productos en Avo."}), 404
    finally:
        driver.quit()  

@app.route('/preciosDelirante', methods=['GET'])
def precios_delirante():
    driver = setup_driver()

    try:
        products = search_delirante(driver)
        if products:
            return jsonify(products), 200  # Devuelve los productos en formato JSON
        else:
            return jsonify({"message": "No se encontraron productos en Café Delirante."}), 404
    finally:
        driver.quit()  

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)
