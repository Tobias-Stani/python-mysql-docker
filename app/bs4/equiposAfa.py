import requests
from bs4 import BeautifulSoup
import json

url = "https://www.afa.com.ar/es/posts/clubes-afiliados-2024"

response = requests.get(url)

if response.status_code == 200:
    # Parsear el contenido HTML con BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Array para almacenar los nombres de los clubes
    clubes = []

    spans = soup.find_all('span', style='font-size:13.5pt')

    for span in spans:
        span_text = span.get_text(strip=True)
        
        # Verificar que el texto no esté vacío
        if span_text:
            clubes.append(span_text)

    # Convertir la lista de clubes a formato JSON 
    json_output = json.dumps(clubes, ensure_ascii=False, indent=4)

    # Imprimir el JSON en consola o devolverlo en algún endpoint
    print(json_output)

else:
    print(f"Error: {response.status_code}")
