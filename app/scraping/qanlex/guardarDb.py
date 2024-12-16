import mysql.connector
from mysql.connector import Error
import json
from datetime import datetime
import os  # Para eliminar el archivo

class DatabaseUploader:
    def __init__(self, host, user, password, database):
        """
        Initialize database connection parameters.
        
        :param host: MySQL server host
        :param user: MySQL username
        :param password: MySQL password
        :param database: Database name
        """
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None

    def _connect(self):
        """Establish a connection to the MySQL database."""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            if self.connection.is_connected():
                print("Successfully connected to the database")
        except Error as e:
            print(f"Error connecting to MySQL database: {e}")
            raise

    def _close_connection(self):
        """Close the database connection."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Database connection closed")

    def limpiar_fecha(self, fecha):
        """Limpia el texto de fecha antes de intentar convertirla a formato de fecha."""
        if fecha:
            # Eliminar cualquier texto innecesario antes de la fecha
            fecha = fecha.replace('Fecha:', '').strip()  # Remueve 'Fecha:' y cualquier espacio adicional
        return fecha

    def upload_expedientes(self, scraped_data_file):
        """
        Upload scraped expedientes data to the database.
        
        :param scraped_data_file: JSON file containing scraped data
        """
        try:
            # Ensure database connection
            self._connect()
            cursor = self.connection.cursor()

            # Read scraped data
            with open(scraped_data_file, 'r', encoding='utf-8') as file:
                scraped_data = json.load(file)

            # Prepare and execute SQL for each expediente
            for caso in scraped_data:
                # Insert into expedientes table
                expediente_query = """
                INSERT INTO expedientes 
                (expediente, jurisdiccion, dependencia, situacion_actual, caratula) 
                VALUES (%s, %s, %s, %s, %s)
                """
                expediente_values = (
                    caso.get('expediente', ''),
                    caso.get('jurisdiccion', ''),
                    caso.get('dependencia', ''),
                    caso.get('situacion_actual', ''),
                    caso.get('caratula', '')
                )
                
                cursor.execute(expediente_query, expediente_values)
                expediente_id = cursor.lastrowid

                # Insert movimientos
                if caso.get('registros_tabla'):
                    movimientos_query = """
                    INSERT INTO movimientos 
                    (expediente_id, fecha, tipo, detalle) 
                    VALUES (%s, %s, %s, %s)
                    """
                    movimientos_values = [
                        (expediente_id, 
                         datetime.strptime(self.limpiar_fecha(registro['fecha']), '%d/%m/%Y').date() if registro['fecha'] else None, 
                         registro['tipo'], 
                         registro['detalle']) 
                        for registro in caso.get('registros_tabla', [])
                    ]
                    cursor.executemany(movimientos_query, movimientos_values)

                # Insert participantes (actores y demandados)
                participantes_query = """
                INSERT INTO participantes 
                (expediente_id, tipo, nombre) 
                VALUES (%s, %s, %s)
                """
                participantes_values = []
                
                # Añadir actores
                participantes_values.extend([
                    (expediente_id, 'ACTOR', actor) 
                    for actor in caso.get('actores', [])
                ])
                
                # Añadir demandados
                participantes_values.extend([
                    (expediente_id, 'DEMANDADO', demandado) 
                    for demandado in caso.get('demandados', [])
                ])
                
                if participantes_values:
                    cursor.executemany(participantes_query, participantes_values)

            # Commit the transaction
            self.connection.commit()
            print("Data uploaded successfully!")

            # Eliminar el archivo después de subir los datos
            if os.path.exists(scraped_data_file):
                os.remove(scraped_data_file)  # Elimina el archivo
                print(f"File {scraped_data_file} has been deleted successfully!")

        except Error as e:
            print(f"Error uploading data: {e}")
            # Rollback in case of error
            if self.connection:
                self.connection.rollback()
        
        finally:
            # Close cursor and connection
            if 'cursor' in locals():
                cursor.close()
            self._close_connection()

def main():
    # Configuración de conexión para Docker Compose
    uploader = DatabaseUploader(
        host='172.29.0.2',     # IP del contenedor de base de datos
        user='scraperuser',    # Usuario proporcionado
        password='scraperpass',  # Contraseña proporcionada
        database='scraper_data'  # Nombre de la base de datos
    )

    # Ruta al archivo JSON con los datos scrapeados
    scraped_data_file = 'app/scraping/qanlex/expedientes.json'
    
    # Subir datos
    uploader.upload_expedientes(scraped_data_file)

if __name__ == "__main__":
    main()
