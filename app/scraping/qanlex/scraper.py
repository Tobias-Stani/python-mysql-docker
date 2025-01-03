from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json
from datetime import datetime
import os
import time

def setup_driver():
    """Configura y retorna el driver de Selenium con opciones predeterminadas para evitar problemas de ejecución en contenedores."""
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def guardar_datos_json(datos, archivo="expedientes.json"):
    """Guarda los datos extraídos en un archivo JSON, agregándolos a los datos existentes en lugar de sobrescribirlos."""
    # Verificar si el archivo ya existe
    if os.path.exists(archivo):
        # Leer los datos existentes en el archivo
        with open(archivo, "r", encoding="utf-8") as f:
            try:
                datos_existentes = json.load(f)
            except json.JSONDecodeError:
                # Si el archivo está vacío o no tiene formato JSON válido, iniciar con lista vacía
                datos_existentes = []
    else:
        # Si el archivo no existe, iniciamos una lista vacía
        datos_existentes = []

    # Agregar los nuevos datos al conjunto de datos existentes
    datos_existentes.append(datos)

    # Guardar los datos actualizados en el archivo JSON
    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(datos_existentes, f, ensure_ascii=False, indent=4)
    
    print(f"Datos guardados correctamente en {archivo}")

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
    Extrae datos generales (expediente, carátula, y dependencia) de la página web,
    incluyendo las fechas, tipos y detalles de la tabla antes de hacer clic en "Intervinientes".
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

        # **Nuevo código para extraer fechas, tipos y detalles de la tabla**
        try:
            # Esperar a que la tabla esté presente en el DOM
            tabla = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.ID, "expediente:action-table"))
            )

            # Esperar a que las filas de la tabla sean visibles
            filas = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#expediente\\:action-table tr"))
            )

            # Verificar si la tabla está vacía (excluyendo el encabezado)
            if len(filas) <= 1:
                datos["registros_tabla"] = []
                print("La tabla de movimientos está vacía.")
                return datos

            # Lista para almacenar los registros extraídos
            registros_tabla = []

            for fila in filas[1:]:  # Saltar el encabezado
                # Extraer columnas específicas: Fecha, Tipo, Detalle
                celdas = fila.find_elements(By.TAG_NAME, "td")
                if len(celdas) >= 5:  # Verificar que haya suficientes columnas
                    fecha = celdas[2].text.strip()  # Columna de Fecha
                    tipo = celdas[3].text.strip()  # Columna de Tipo
                    detalle = celdas[4].text.strip()  # Columna de Detalle
                    registros_tabla.append({"fecha": fecha, "tipo": tipo, "detalle": detalle})

            # Almacenar en el diccionario principal
            datos["registros_tabla"] = registros_tabla

            # Si no se encontraron registros, imprimir mensaje
            if not registros_tabla:
                print("No se encontraron registros en la tabla.")

        except TimeoutException:
            # Manejar el caso de que la tabla no cargue dentro del tiempo especificado
            datos["registros_tabla"] = []
            print("Tiempo de espera agotado al cargar la tabla de movimientos.")

        except Exception as e:
            # Manejar cualquier otro error inesperado
            datos["registros_tabla"] = []
            print(f"Error al extraer la tabla de movimientos: {e}")

        # Hacer clic en el tab "Intervinientes" usando el texto visible
        intervinientes_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Intervinientes']"))
        )
        intervinientes_tab.click()

        # Esperar que la tabla de participantes esté cargada
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#expediente\\:participantsTable"))
        )

        # Extraer actores y demandados
        actores = []
        demandados = []

        # Encontrar las filas que contienen los participantes (actores y demandados)
        filas = driver.find_elements(By.CSS_SELECTOR, "#expediente\\:participantsTable .rf-dt-r")

        # Recorrer las filas y extraer los datos de actores y demandados
        for fila in filas:
            # Obtener el tipo de participante (actor o demandado)
            tipo = fila.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text.strip()
            
            # Obtener el nombre del participante
            nombre = fila.find_element(By.CSS_SELECTOR, "td:nth-child(2)").text.strip()
            
            # Clasificar como actor o demandado
            if "ACTOR" in tipo:
                actores.append(nombre)
            elif "DEMANDADO" in tipo:
                demandados.append(nombre)

        # Añadir actores y demandados al diccionario de datos
        datos["actores"] = actores
        datos["demandados"] = demandados

        # **Mostrar los datos extraídos de forma estructurada y prolija**
        print("\n--- Datos Extraídos ---")
        print(f"Expediente: {datos['expediente']}")
        print(f"Jurisdicción: {datos['jurisdiccion']}")
        print(f"Dependencia: {datos['dependencia']}")
        print(f"Situación Actual: {datos['situacion_actual']}")
        print(f"Carátula: {datos['caratula']}")

        if datos.get("registros_tabla"):
            print("\nRegistros de la Tabla de Movimientos:")
            for registro in datos["registros_tabla"]:
                print(f"  - Fecha: {registro['fecha']}, Tipo: {registro['tipo']}, Detalle: {registro['detalle']}")
        else:
            print("\nNo se encontraron registros en la tabla de movimientos.")

        print("\nActores:")
        for actor in datos["actores"]:
            print(f"  - {actor}")

        print("\nDemandados:")
        for demandado in datos["demandados"]:
            print(f"  - {demandado}")

        # Guardar los datos en un archivo JSON
        guardar_datos_json(datos)  # Llamamos a la función para guardar los datos en JSON

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