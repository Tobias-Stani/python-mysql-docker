from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix
import paramiko
import os

load_dotenv()
app = Flask(__name__, template_folder="templates")
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 * 1024  # 2GB

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)


# Credenciales SSH
SSH_HOST = os.getenv("SSH_HOST")
SSH_USER = os.getenv("SSH_USER")
SSH_PASSWORD = os.getenv("SSH_PASSWORD")
UPLOAD_PATH = os.getenv("UPLOAD_PATH")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/test-ssh", methods=["GET"])
def test_ssh():
    """
    Endpoint para probar la conexión SSH.
    Se conecta al servidor y ejecuta el comando 'ls -l'.
    Devuelve el resultado en formato JSON.
    """
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(SSH_HOST, username=SSH_USER, password=SSH_PASSWORD, timeout=5)
        
        stdin, stdout, stderr = client.exec_command("ls -l")  # Ejecuta un comando de prueba
        output = stdout.read().decode()
        
        client.close()
        return jsonify({"success": True, "message": "Conexión exitosa", "output": output})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route("/upload", methods=["POST"])
def upload_file():
    """
    Endpoint para subir múltiples archivos a una carpeta específica en el servidor remoto.
    """
    if "files[]" not in request.files:
        return jsonify({"success": False, "message": "No se encontraron archivos en la solicitud"})
    
    files = request.files.getlist("files[]")
    if not files or files[0].filename == "":
        return jsonify({"success": False, "message": "No se seleccionaron archivos válidos"})
    
    folder = request.form.get("folder", "").strip()  # Obtener la carpeta seleccionada
    remote_path = os.path.join(UPLOAD_PATH, folder) if folder else UPLOAD_PATH  # Usar carpeta o default

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(SSH_HOST, username=SSH_USER, password=SSH_PASSWORD, timeout=5)
        
        sftp = client.open_sftp()

        # Verificar si la carpeta existe, si no, crearla
        try:
            sftp.stat(remote_path)  # Intenta acceder a la carpeta
        except FileNotFoundError:
            sftp.mkdir(remote_path)  # Si no existe, la crea

        # Subir cada archivo en la lista
        uploaded_files = []
        failed_files = []

        for file in files:
            try:
                file_path = os.path.join(remote_path, file.filename)

                # Subir directamente sin guardar en /tmp
                with sftp.file(file_path, 'wb') as remote_file:
                    file.stream.seek(0)  # Asegurar que el puntero del archivo esté al inicio
                    remote_file.write(file.stream.read())  # Escribir los datos directamente

                uploaded_files.append(file.filename)
            except Exception as e:
                failed_files.append({"filename": file.filename, "error": str(e)})

        
        sftp.close()
        client.close()

        if failed_files:
            return jsonify({
                "success": True,
                "partial": True,
                "message": f"Se subieron {len(uploaded_files)} archivos, {len(failed_files)} fallaron",
                "uploaded": uploaded_files,
                "failed": failed_files
            })
        
        return jsonify({
            "success": True,
            "message": f"Se subieron {len(uploaded_files)} archivos a {remote_path}",
            "uploaded": uploaded_files
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route("/list-folders", methods=["GET"])
def list_folders():
    """
    Endpoint para listar las carpetas disponibles en el servidor remoto.
    """
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(SSH_HOST, username=SSH_USER, password=SSH_PASSWORD, timeout=5)
        
        sftp = client.open_sftp()
        folders = [f.filename for f in sftp.listdir_attr(UPLOAD_PATH) if f.st_mode & 0o40000]  # Solo directorios
        sftp.close()
        client.close()

        return jsonify({"success": True, "folders": folders})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route("/create-folder", methods=["POST"])
def create_folder():
    """
    Endpoint para crear una carpeta en la ruta de destino del servidor remoto.
    """
    data = request.json
    folder_name = data.get("folder_name", "").strip()

    if not folder_name:
        return jsonify({"success": False, "message": "El nombre de la carpeta no puede estar vacío"})

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(SSH_HOST, username=SSH_USER, password=SSH_PASSWORD, timeout=5)

        sftp = client.open_sftp()
        folder_path = os.path.join(UPLOAD_PATH, folder_name)

        # 🛑 Verificar si la carpeta base existe antes de crear subcarpetas
        try:
            sftp.stat(UPLOAD_PATH)
        except FileNotFoundError:
            sftp.mkdir(UPLOAD_PATH)  # Crear la carpeta base si no existe

        try:
            sftp.mkdir(folder_path)  # Crear la carpeta nueva
            message = f"Carpeta '{folder_name}' creada exitosamente en {UPLOAD_PATH}"
        except IOError:
            message = f"La carpeta '{folder_name}' ya existe en {UPLOAD_PATH}"

        sftp.close()
        client.close()

        return jsonify({"success": True, "message": message})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route("/list-folder-content", methods=["GET"])
def list_folder_content():
    """
    Endpoint para listar el contenido de una carpeta específica en el servidor remoto.
    Recibe el nombre de la carpeta como parámetro en la URL.
    """
    folder_name = request.args.get("folder", "")
    
    # Determinar la ruta completa (usar la ruta base si no se especifica carpeta)
    remote_path = os.path.join(UPLOAD_PATH, folder_name) if folder_name else UPLOAD_PATH
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(SSH_HOST, username=SSH_USER, password=SSH_PASSWORD, timeout=5)
        
        sftp = client.open_sftp()
        
        try:
            # Listar todos los archivos y carpetas en la ruta
            items = sftp.listdir_attr(remote_path)
            
            # Separar archivos y carpetas, e incluir metadatos
            files = []
            folders = []
            
            for item in items:
                is_dir = bool(item.st_mode & 0o40000)  # Verifica si es un directorio
                entry = {
                    "name": item.filename,
                    "size": item.st_size,
                    "modified": item.st_mtime,
                    "is_directory": is_dir
                }
                
                if is_dir:
                    folders.append(entry)
                else:
                    files.append(entry)
            
            result = {
                "success": True,
                "path": remote_path,
                "folders": folders,
                "files": files,
                "total_items": len(items)
            }
        except FileNotFoundError:
            result = {
                "success": False,
                "message": f"La carpeta '{remote_path}' no existe en el servidor"
            }
        
        sftp.close()
        client.close()
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

if __name__ == "__main__":
    if not os.path.exists("templates"):
        os.makedirs("templates")
    app.run(host="0.0.0.0", port=5000, debug=True)