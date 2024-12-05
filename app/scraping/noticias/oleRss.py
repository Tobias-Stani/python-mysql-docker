import requests
import xml.etree.ElementTree as ET

def fetch_rss_feed(url):
    # Descargar el contenido del feed RSS
    response = requests.get(url)
    response.raise_for_status()  # Verificar si la solicitud fue exitosa

    # Parsear el contenido XML
    root = ET.fromstring(response.content)

    # Extraer los elementos <item>
    items = root.findall(".//item")  # Busca todos los nodos <item>
    for item in items:
        title = item.find("title").text
        description = item.find("description").text
        link = item.find("link").text
        pub_date = item.find("pubDate").text

        # Imprimir los datos extraídos
        print("Título:", title)
        print("Descripción:", description)
        print("Link:", link)
        print("Fecha de publicación:", pub_date)
        print("-" * 50)

if __name__ == "__main__":
    # URL del feed RSS
    rss_url = "https://www.ole.com.ar/rss/river-plate/"  # Cambia a la URL real del RSS
    fetch_rss_feed(rss_url)
