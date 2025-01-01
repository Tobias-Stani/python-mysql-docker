import os
import pymysql
import schedule
import time
from datetime import datetime, timedelta
import requests


# Cargar variables de entorno desde .env
from dotenv import load_dotenv
load_dotenv(dotenv_path='/home/tobi/develop/scraping/.env.local')

# Configuración de conexión a la base de datos
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Conectar a la base de datos
def conectar_mysql():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )


def enviar_mensaje_telegram(mensaje):
    """Envía un mensaje al canal o chat de Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': mensaje,
        'parse_mode': 'HTML'  
    }
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()  
        if response.status_code == 200:
            print("Mensaje enviado exitosamente a Telegram.")
        else:
            print(f"Error al enviar el mensaje a Telegram. Código de respuesta: {response.status_code}")
            print(f"Respuesta del servidor: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Excepción al enviar el mensaje: {e}")



# Obtener tareas desde la base de datos
def cargar_tareas():
    conn = conectar_mysql()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM tasks")
        tareas = cursor.fetchall()
    conn.close()
    return tareas

# Verificar si es hora de enviar recordatorios
def verificar_tareas():
    conn = conectar_mysql()
    tareas = cargar_tareas()
    hora_actual = datetime.now().time()
    fecha_actual = datetime.now().date()

    for tarea in tareas:
        tarea_hora = datetime.strptime(str(tarea['schedule_time']), "%H:%M:%S").time()

        if hora_actual >= tarea_hora:
            # Verificar si ya se registró hoy
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM task_logs WHERE task_id = %s AND log_date = %s",
                    (tarea['id'], fecha_actual)
                )
                registro = cursor.fetchone()
            
            if not registro:  # No hay registro, enviar mensaje
                mensaje = f"¡Recordatorio! {tarea['name']} ¿Has completado esta tarea? Responde con 'Sí' o 'No'."
                enviar_mensaje_telegram(mensaje)

                # Insertar registro en task_logs
                with conn.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO task_logs (task_id, log_date, status) VALUES (%s, %s, %s)",
                        (tarea['id'], fecha_actual, 'pending')
                    )
                conn.commit()

    conn.close()

# Reintentar tareas pendientes
def gestionar_reintentos():
    conn = conectar_mysql()
    fecha_actual = datetime.now().date()
    hora_actual = datetime.now()

    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT tl.*, t.retry_interval, t.name FROM task_logs tl "
            "JOIN tasks t ON tl.task_id = t.id "
            "WHERE tl.status = 'pending' AND tl.log_date = %s",
            (fecha_actual,)
        )
        tareas_pendientes = cursor.fetchall()

    for tarea in tareas_pendientes:
        tiempo_reintento = tarea['response_time'] + timedelta(minutes=tarea['retry_interval']) if tarea['response_time'] else None

        if not tarea['response_time'] or (tiempo_reintento and hora_actual >= tiempo_reintento):
            mensaje = f"Reintento: {tarea['name']} ¿Has completado esta tarea? Responde con 'Sí' o 'No'."
            enviar_mensaje_telegram(mensaje)

            # Actualizar registro en task_logs
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE task_logs SET retry_count = retry_count + 1, response_time = %s WHERE id = %s",
                    (hora_actual, tarea['id'])
                )
            conn.commit()

    conn.close()

# Configurar los temporizadores
def configurar_temporizadores():
    schedule.every(1).minutes.do(verificar_tareas)
    schedule.every(5).minutes.do(gestionar_reintentos)

# Iniciar el script
if __name__ == "__main__":
    configurar_temporizadores()
    print("Bot de recordatorios en ejecución...")

    while True:
        schedule.run_pending()
        time.sleep(1)
