from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv
import paramiko
import os

load_dotenv()
app = Flask(__name__, template_folder="templates")

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
    Endpoint para subir archivos a una carpeta específica en el servidor remoto.
    """
    if "file" not in request.files:
        return jsonify({"success": False, "message": "No se encontró ningún archivo en la solicitud"})
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "message": "El nombre del archivo es inválido"})
    
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

        file_path = os.path.join(remote_path, file.filename)
        temp_path = f"/tmp/{file.filename}"
        file.save(temp_path)  # Guardar temporalmente en el servidor local
        
        sftp.put(temp_path, file_path)  # Subir archivo al servidor remoto
        sftp.close()
        client.close()

        os.remove(temp_path)  # Eliminar el archivo temporal

        return jsonify({"success": True, "message": f"Archivo {file.filename} subido a {remote_path}"})
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
    data = request.json  # Obtener datos enviados en formato JSON
    folder_name = data.get("folder_name", "").strip()

    if not folder_name:
        return jsonify({"success": False, "message": "El nombre de la carpeta no puede estar vacío"})

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(SSH_HOST, username=SSH_USER, password=SSH_PASSWORD, timeout=5)

        sftp = client.open_sftp()
        folder_path = os.path.join(UPLOAD_PATH, folder_name)

        try:
            sftp.mkdir(folder_path)  # Crear la carpeta en el servidor remoto
            message = f"Carpeta '{folder_name}' creada exitosamente en {UPLOAD_PATH}"
        except IOError:
            message = f"La carpeta '{folder_name}' ya existe en {UPLOAD_PATH}"

        sftp.close()
        client.close()

        return jsonify({"success": True, "message": message})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})



if __name__ == "__main__":
    if not os.path.exists("templates"):
        os.makedirs("templates")
    app.run(host="0.0.0.0", port=5000, debug=True)
