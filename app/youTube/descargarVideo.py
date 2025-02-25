import yt_dlp
from tqdm import tqdm

# Pedimos el enlace del video
url = input("Ingresa el enlace del video de YouTube: ")

# Función para manejar el progreso
def progress_hook(d):
    if d['status'] == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate')
        downloaded = d.get('downloaded_bytes', 0)
        if total:
            progress_bar.n = downloaded
            progress_bar.total = total
            progress_bar.refresh()
    elif d['status'] == 'finished':
        progress_bar.close()
        print("\n✅ Descarga completada")

# Configuración para descargar en la mejor calidad
ydl_opts = {
    'format': 'bestvideo+bestaudio/best',
    'outtmpl': '%(title)s.%(ext)s',  # Guarda con el título original
    'progress_hooks': [progress_hook],  # Agregar la barra de progreso
}

# Inicializar la barra de progreso
progress_bar = tqdm(total=100, unit='B', unit_scale=True, desc="Descargando")

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download([url])
