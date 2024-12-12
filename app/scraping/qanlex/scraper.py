from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import StaleElementReferenceException
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

def hacer_click_siguiente(driver):
    """Intenta hacer clic en el botón 'Siguiente' si está disponible."""
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
        print("El botón 'Siguiente' no se encuentra. Terminando el scraping.")
        return False

def elementos_tabla(driver):
    """Navega por las páginas de la tabla hasta que no se encuentre el botón 'Siguiente' o este desaparezca, y cuenta todos los elementos."""
    total_elementos = 0  # Inicializamos el contador de elementos totales
    
    while True:
        # Esperar a que la tabla se cargue
        try:
            tabla = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "table-striped"))
            )
            filas = tabla.find_elements(By.TAG_NAME, "tr")
            elementos_en_pagina = len(filas) - 1  # Restamos 1 para ignorar la fila de encabezado
            total_elementos += elementos_en_pagina
            print(f"Elementos en esta página: {elementos_en_pagina}")
        except Exception as e:
            print(f"Error al procesar la tabla en esta página: {e}")
            break

        # Intentamos hacer clic en "Siguiente"
        if not hacer_click_siguiente(driver):
            break

        # Esperamos un poco para que la nueva página cargue
        time.sleep(2)

    print(f"Hay un total de {total_elementos} expedientes.")
    return total_elementos


def hacer_click_expediente(driver):
    """Hace clic en el ícono del expediente, utilizando la clase del ícono para acceder al expediente."""
    try:
        # Seleccionamos el ícono de "Ver" (fa-eye) usando su clase
        icono_ver = driver.find_element(By.CLASS_NAME, "fa-eye")
        
        # Verificamos si el ícono es visible y habilitado
        if icono_ver.is_displayed() and icono_ver.is_enabled():
            icono_ver.click()
            print("Se hizo clic en el expediente correctamente.")
            return True
        else:
            print("El ícono de 'Ver' no está habilitado o visible.")
            return False

    except Exception as e:
        print(f"Error al intentar hacer clic en el expediente: {e}")
        return False

def extraer_expediente(driver):
    """
    Extrae datos generales (expediente, carátula, y dependencia) de la página web.
    """
    try:
        # Diccionario para almacenar los datos extraídos
        datos = {}

        # Extraer expediente
        contenedor_expediente = driver.find_element(By.CLASS_NAME, "col-xs-10")
        datos["expediente"] = contenedor_expediente.find_element(By.TAG_NAME, "span").text.strip()

        # Extraer jurisdicción
        jurisdiccion_contenedor = driver.find_element(By.ID, "expediente:j_idt90:detailCamera")
        datos["jurisdiccion"] = jurisdiccion_contenedor.text.strip()

        # Extraer dependencia
        dependencia_contenedor = driver.find_element(By.ID, "expediente:j_idt90:detailDependencia")
        datos["dependencia"] = dependencia_contenedor.text.strip()

        # Extraer situación actual
        situacion_contenedor = driver.find_element(By.ID, "expediente:j_idt90:detailSituation")
        datos["situacion_actual"] = situacion_contenedor.text.strip()

        # Extraer carátula
        caratula_contenedor = driver.find_element(By.ID, "expediente:j_idt90:detailCover")
        datos["caratula"] = caratula_contenedor.text.strip()

        # Hacer clic en el tab "Intervinientes" usando el texto visible (es más robusto que el ID)
        intervinientes_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Intervinientes']"))
        )
        intervinientes_tab.click()
        print("Tab 'Intervinientes' clickeado correctamente.")

        time.sleep(5)

        # Imprimir los datos extraídos para verificar
        print(f"Datos extraídos: {datos}")

        return datos

    except Exception as e:
        print(f"Error al extraer los datos generales: {e}")
        return None

def volver_a_tabla(driver):
    """Hace clic en el botón de 'Volver' para regresar a la tabla de expedientes."""
    try:
        # Localizamos el botón "Volver" usando su clase
        boton_volver = driver.find_element(By.CLASS_NAME, "btn-default")
        
        # Verificamos si el botón es visible y clickeable
        if boton_volver.is_displayed() and boton_volver.is_enabled():
            boton_volver.click()
            print("Volvimos a la tabla correctamente.")
            return True
        else:
            print("El botón 'Volver' no está habilitado o visible.")
            return False
    except Exception as e:
        print(f"Error al intentar volver a la tabla: {e}")
        return False


def navegar_y_extraer(driver):
    """Navega por las páginas de la tabla, hace clic en los expedientes y extrae la información."""
    total_expedientes = 0  # Contador de expedientes extraídos

    while True:
        try:
            # Esperar a que la tabla se cargue completamente
            tabla = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "table-striped"))
            )
            
            # Método para procesar la tabla que maneja elementos obsoletos
            def procesar_tabla():
                nonlocal total_expedientes
                # Re-encontrar las filas cada vez para evitar stale elements
                filas = driver.find_elements(By.TAG_NAME, "tr")[1:]  # Excluir encabezado
                
                for i in range(len(filas)):
                    try:
                        # Re-encontrar la fila en cada iteración
                        filas = driver.find_elements(By.TAG_NAME, "tr")[1:]
                        fila_actual = filas[i]
                        
                        # Buscar el ícono de "Ver" en la fila actual
                        try:
                            icono_ver = fila_actual.find_element(By.CLASS_NAME, "fa-eye")
                        except Exception:
                            print(f"No se encontró ícono en la fila {i}")
                            continue
                        
                        # Hacer clic en el ícono usando JavaScript para mayor confiabilidad
                        driver.execute_script("arguments[0].click();", icono_ver)
                        
                        # Esperar a que cargue la página del expediente
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "col-xs-10"))
                        )
                        
                        # Extraer expediente
                        expediente = extraer_expediente(driver)
                        if expediente:
                            total_expedientes += 1
                            print(f"Expediente {expediente} extraído correctamente.")

                        # Regresar a la tabla
                        volver_a_tabla(driver)
                        
                        # Esperar a que la tabla se recargue
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "table-striped"))
                        )
                        
                    except StaleElementReferenceException:
                        print(f"Elemento obsoleto en la fila {i}, saltando...")
                        continue
                    except Exception as e:
                        print(f"Error procesando fila {i}: {e}")
            
            # Procesar la tabla
            procesar_tabla()

        except Exception as e:
            print(f"Error general al procesar la tabla: {e}")
            break

        # Intentar ir a la siguiente página
        if not hacer_click_siguiente(driver):
            break

        # Pequeña pausa para permitir la carga
        time.sleep(2)
    
    print(f"Se extrajeron un total de {total_expedientes} expedientes.")
    return total_expedientes



def main():
    """Función principal que orquesta el proceso de scraping."""
    # Configurar el driver
    driver = setup_driver()

    try:
        # Realizar las acciones de búsqueda
        buscar_parte(driver)
        
        # Navegar por las páginas de la tabla, hacer clic en los expedientes y extraer información
        navegar_y_extraer(driver)
        
    finally:
        # Cerrar el driver al final
        driver.quit()

if __name__ == "__main__":
    main()  