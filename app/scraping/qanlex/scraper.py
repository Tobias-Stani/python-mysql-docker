from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager
import time

def setup_driver():
    """Configura y retorna el driver de Selenium con opciones predeterminadas para evitar problemas de ejecución en contenedores."""
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def esperar_elemento(driver, by, value, timeout=5):
    """Espera hasta que el elemento especificado esté presente y sea interactuable."""
    try:
        return WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )
    except Exception as e:
        print(f"Error al esperar el elemento con {by}={value}: {e}")
        return None

def buscar_parte(driver):
    """Realiza la primera parte del scraping en la página web especificada."""
    url = "http://scw.pjn.gov.ar/scw/home.seam"
    driver.get(url)

    # Esperar y hacer clic en el tab 'porParte'
    tab = esperar_elemento(driver, By.XPATH, '//*[@id="formPublica:porParte:header:inactive"]')
    if tab:
        tab.click()
        print("Tab 'porParte' clickeado correctamente.")
    else:
        print("No se pudo hacer clic en el tab 'porParte'.")
        return

    # Seleccionar "COM" en el <select> de jurisdicción
    jurisdiccion_select = esperar_elemento(driver, By.ID, "formPublica:camaraPartes")
    if jurisdiccion_select:
        select = Select(jurisdiccion_select)
        select.select_by_value("10")
        print("Opción 'COM' seleccionada correctamente.")
    else:
        print("No se pudo encontrar el select de jurisdicción.")
        return

    # Escribir 'residuos' en el campo de búsqueda
    input_element = esperar_elemento(driver, By.XPATH, '//*[@id="formPublica:nomIntervParte"]')
    if input_element:
        input_element.send_keys("residuos")
        print("Texto 'residuos' escrito correctamente en el campo de texto.")
    else:
        print("No se pudo encontrar el campo de texto.")
        return

    # Esperar que el usuario resuelva el CAPTCHA
    print("Por favor, resuelve el CAPTCHA manualmente y luego presiona Enter para continuar.")
    input("Presiona Enter después de resolver el CAPTCHA...")

    # Hacer clic en el botón "Consultar"
    boton_consultar = esperar_elemento(driver, By.ID, "formPublica:buscarPorParteButton")
    if boton_consultar:
        boton_consultar.click()
        print("Botón 'Consultar' clickeado correctamente.")
    else:
        print("No se pudo hacer clic en el botón 'Consultar'.")
        return

    # Esperar que los resultados de la tabla carguen
    time.sleep(3)  # Ajusta este tiempo si es necesario para tu caso

def contar_elementos_y_extraer(driver):
    """Cuenta los elementos de la tabla y los extrae."""
    try:
        # Encontramos la tabla por su clase
        tabla = driver.find_element(By.CLASS_NAME, "table-striped")
        filas = tabla.find_elements(By.TAG_NAME, "tr")
        
        # Excluimos la primera fila de encabezado
        contador = 0
        for fila in filas[1:]:  # Ignoramos la primera fila de encabezado
            celdas = fila.find_elements(By.TAG_NAME, "td")
            if len(celdas) > 0:  # Si la fila tiene celdas
                contador += 1
        
        return contador

    except Exception as e:
        print(f"Error al contar elementos o extraer la tabla: {e}")
        return 0


def hacer_click_siguiente(driver):
    """Intenta hacer clic en el botón 'Siguiente' si está disponible.
    Maneja escenarios en los que el botón cambia, desaparece o no es localizable."""
    try:
        # Intentamos localizar el botón "Siguiente"
        boton_siguiente = driver.find_element(By.XPATH, '//*[@id="j_idt118:j_idt208:j_idt215"]')

        # Verificamos si el botón está visible y habilitado
        if boton_siguiente.is_displayed() and boton_siguiente.is_enabled():
            boton_siguiente.click()
            print("Botón 'Siguiente' clickeado correctamente.")
            return True
        else:
            print("El botón 'Siguiente' no está habilitado o visible. Terminando el scraping.")
            return False

    except Exception:
        # Silenciar el error y retornar False si no se encuentra el botón
        print("El botón 'Siguiente' no se encuentra. Terminando el scraping.")
        return False



def navegar_y_scrapear(driver):
    """Navega por las páginas de la tabla hasta que no se encuentre el botón 'Siguiente' 
    o este desaparezca, y cuenta todos los elementos."""
    total_elementos = 0  # Inicializamos el contador de elementos totales
    
    while True:
        # Contamos los elementos de la página actual
        try:
            tabla = driver.find_element(By.CLASS_NAME, "table-striped")
            filas = tabla.find_elements(By.TAG_NAME, "tr")
            
            # Excluimos la primera fila de encabezado y contamos las filas restantes
            elementos_en_pagina = len(filas) - 1  # Restamos 1 para ignorar la fila de encabezado
            if elementos_en_pagina > 0:
                total_elementos += elementos_en_pagina  # Sumamos al total
                print(f"Elementos en esta página: {elementos_en_pagina}")
            else:
                print("No se encontraron elementos en esta página.")
        except Exception as e:
            # Silenciar errores relacionados con la tabla
            print(f"Error al procesar la tabla en esta página: {e}")
            break

        # Intentamos hacer clic en "Siguiente"
        if not hacer_click_siguiente(driver):
            # Si no se puede hacer clic, terminamos el bucle
            break

        # Esperamos 2 segundos para que la nueva página cargue
        time.sleep(2)
    
    # Imprimimos el total de elementos al final
    print(f"Hay un total de {total_elementos} expedientes.")
    return total_elementos



def main():
    """Función principal que orquesta el proceso de scraping."""
    # Configurar el driver
    driver = setup_driver()

    try:
        # Realizar las acciones de búsqueda
        buscar_parte(driver)

        # Contar los elementos en la tabla y mostrar el total
        total_elementos = navegar_y_scrapear(driver)
        print(f"Total de expedientes encontrados: {total_elementos}")

    finally:
        # Cerrar el driver al final
        driver.quit()

if __name__ == "__main__":
    main()

