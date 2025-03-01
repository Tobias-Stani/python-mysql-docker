from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import yt_dlp
import os
import uuid

app = FastAPI()

# Carpeta donde se guardarán los archivos descargados
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Servir archivos estáticos (para descargar después)
app.mount("/downloads", StaticFiles(directory=DOWNLOAD_FOLDER), name="downloads")

def descargar_video(url: str, formato: str) -> str:
    """ Descarga un video o audio y devuelve la ruta del archivo """
    filename = f"{uuid.uuid4()}"  # Nombre único para evitar conflictos

    opciones = {
        "format": "bestaudio/best" if formato == "audio" else "best",
        "outtmpl": f"{DOWNLOAD_FOLDER}/{filename}.%(ext)s",
        "quiet": True,
        "noprogress": True,
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}] if formato == "audio" else []
    }

    try:
        with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(url, download=True)
            filepath = f"{DOWNLOAD_FOLDER}/{filename}.{info['ext'] if formato != 'audio' else 'mp3'}"
            return filepath
    except Exception as e:
        return str(e)

@app.get("/descargar")
def descargar(url: str = Query(..., title="URL del video"), formato: str = Query("video", title="Formato", enum=["video", "audio"])):
    """ Endpoint para descargar un video o audio """
    file_path = descargar_video(url, formato)
    if os.path.exists(file_path):
        return JSONResponse({"mensaje": "Descarga completada", "url": f"/downloads/{os.path.basename(file_path)}"})
    return JSONResponse({"error": "No se pudo descargar el video"}, status_code=500)


