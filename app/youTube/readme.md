# 📥 Descargador de Videos (YouTube, X/Twitter, Instagram)

Este proyecto es una aplicación web desarrollada con **Flask** y **yt-dlp** que permite descargar videos y audios de **YouTube, X (Twitter) e Instagram**.

## 🚀 Características

✅ Descarga videos o audios de **YouTube, X (Twitter) e Instagram**  
✅ Interfaz moderna y responsiva en **HTML, CSS y JavaScript**  
✅ Uso de **yt-dlp** para extraer enlaces de descarga  
✅ Implementación sencilla con **Flask**  

---

## 📂 **Estructura del Proyecto**

📦 descargador-videos │── 📂 templates/ │ ├── index.html # Interfaz del usuario │── app.py # Lógica backend con Flask y yt-dlp │── requirements.txt # Dependencias del proyecto │── README.md # Instrucciones y documentación


### 📜 **Explicación de Archivos**

#### 🔹 `apiDescargas.py`
- Es el **backend** del proyecto.
- Usa **Flask** para servir la interfaz y procesar las descargas.
- Usa **yt-dlp** para obtener enlaces de descarga desde YouTube, X y Instagram.
- Contiene una función `get_platform(url)` para detectar la plataforma del enlace.

#### 🔹 `templates/index.html`
- Es la **interfaz web** del usuario.
- Tiene un campo para ingresar la URL del video y botones para obtener la vista previa y la descarga.
- Usa **JavaScript** para enviar peticiones al backend.

#### 🔹 `requirements.txt`
- Lista las dependencias necesarias para ejecutar el proyecto.
- Incluye `Flask` y `yt-dlp`.

---

## 🔧 **Cómo Instalar y Ejecutar el Proyecto**

### 1️⃣ **Clonar el Repositorio**
```sh
git clone https://github.com/tuusuario/descargador-videos.git
cd descargador-videos



2️⃣ Instalar Dependencias
Asegúrate de tener Python 3 instalado, luego ejecuta:

pip install -r requirements.txt
3️⃣ Ejecutar el Servidor
sh
Copy
Edit
python app.py