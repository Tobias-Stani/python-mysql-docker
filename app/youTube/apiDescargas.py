from flask import Flask, request, jsonify, render_template
import yt_dlp

app = Flask(__name__, template_folder="templates")

def get_platform(url):
    """Detecta si el enlace es de YouTube, Twitter (X) o Instagram"""
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    elif "twitter.com" in url or "x.com" in url:
        return "twitter"
    elif "instagram.com" in url:
        return "instagram"
    return None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/get_download_link", methods=["POST"])
def get_download_link():
    data = request.json
    url = data.get("url")
    option = data.get("option")

    if not url:
        return jsonify({"success": False, "error": "No se proporcionó URL."})

    platform = get_platform(url)
    if not platform:
        return jsonify({"success": False, "error": "Plataforma no soportada."})

    format_option = "bestaudio/best" if option == "audio" else "best"

    ydl_opts = {
        "format": format_option,
        "quiet": True,
        "noprogress": True,
        "logtostderr": False,
        "cookies": "cookies.txt",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Para Twitter/X, obtener el mejor enlace manualmente
            if platform == "twitter":
                if "formats" in info:
                    best_format = max(info["formats"], key=lambda f: f.get("height", 0))  # Mayor resolución
                    download_url = best_format.get("url", "")
                else:
                    return jsonify({"success": False, "error": "No se pudo extraer la URL de Twitter."})
            else:
                download_url = info.get("url", "")

            if not download_url:
                return jsonify({"success": False, "error": "No se pudo obtener el enlace de descarga."})

            filename = info.get("title", "video") + (".mp3" if option == "audio" else ".mp4")

            # ✅ Devolvemos `text/html` para evitar descargas de JSON
            return jsonify({"success": True, "url": download_url, "filename": filename}), 200, {'Content-Type': 'text/html'}

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == "__main__":
    app.run(debug=True)
