# Usa una imagen base de Python
FROM python:3.10-slim

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Copia el archivo de dependencias
COPY app/requirements.txt .

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código fuente de la aplicación
COPY app/ .

# Comando por defecto para ejecutar la aplicación
CMD ["python", "main.py"]
