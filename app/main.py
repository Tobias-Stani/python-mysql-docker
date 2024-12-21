import mysql.connector
from flask import Flask, jsonify

app = Flask(__name__)

# Configuración de la base de datos
db_config = {
    "host": "db",  # Nombre del servicio definido en docker-compose.yml
    "user": "root",
    "password": "root",
    "database": "mi_base",
}

@app.route('/')
def home():
    return "¡Bienvenido a la aplicación Python-MySQL-Docker!"

@app.route('/data')
def get_data():
    try:
        # Conexión a la base de datos
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM tabla_ejemplo")  # Asegúrate de crear esta tabla
        data = cursor.fetchall()
        return jsonify(data)
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)})
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
