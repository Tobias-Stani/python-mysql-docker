import requests

url = "http://localhost:5002/productosCombinados"

response = requests.get(url)

if response.status_code == 200:
    productos = response.json()

    segmentados = {
        "Brasil": [],
        "Colombia": [],
        "Otros": []
    }

    # Clasificar los productos por país
    for producto in productos:
        nombre = producto["name"].lower() 
        if "brasil" in nombre:
            segmentados["Brasil"].append(producto)
        elif "colombia" in nombre:
            segmentados["Colombia"].append(producto)
        else:
            segmentados["Otros"].append(producto)

    # Función para calcular estadísticas
    def calcular_estadisticas(lista_productos):
        if not lista_productos:
            return {"promedio": 0, "bajo": 0, "alto": 0}
        precios = [prod["price"] for prod in lista_productos]
        return {
            "promedio": sum(precios) / len(precios),
            "bajo": min(precios),
            "alto": max(precios)
        }

    # Calcular estadísticas para cada categoría
    estadisticas = {}
    for categoria, lista in segmentados.items():
        estadisticas[categoria] = calcular_estadisticas(lista)

    print("Productos segmentados con estadísticas:")
    for categoria, lista in segmentados.items():
        print(f"\n{categoria}:")
        for prod in lista:
            print(f"  - {prod['name']} (${prod['price']})")
        stats = estadisticas[categoria]
        print(f"  Estadísticas: Promedio=${stats['promedio']:.2f}, Bajo=${stats['bajo']}, Alto=${stats['alto']}")
else:
    print(f"Error al conectarse a la API: {response.status_code}")
