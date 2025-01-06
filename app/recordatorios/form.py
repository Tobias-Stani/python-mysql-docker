from flask import Flask, render_template, request
import mysql.connector

app = Flask(__name__)

db_config = {
    'host': 'localhost',
    'user': 'user',
    'password': 'password',
    'database': 'mi_base',
    'port': 3305
}


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        titulo = request.form["titulo"]
        frecuencia = request.form["frecuencia"]

        # Guardar en la base de datos
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        query = "INSERT INTO recordatorios (titulo, frecuencia) VALUES (%s, %s)"
        cursor.execute(query, (titulo, frecuencia))
        connection.commit()
        cursor.close()
        connection.close()

        return "¡Recordatorio guardado!"
    return render_template("formulario.html")

if __name__ == "__main__":
    app.run(debug=True)
