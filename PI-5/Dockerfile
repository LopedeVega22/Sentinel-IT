# Utilizar una imagen oficial de Python ligera
FROM python:3.13-slim

# Evitar que Python escriba archivos .pyc en disco y enviar streams directo a terminal (mejor para logs docker)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

WORKDIR /app

# Instalar dependencias necesarias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar configuración central (y .env, db, certificados)
COPY . .

# Crear directorio para la base de datos y inicializar esquema
RUN mkdir -p /app/data && python3 src/database.py

# Exponer el puerto del Dashboard Web Flask (leído en config, usualmente 5000)
EXPOSE 5000

# Script puente para iniciar ambos procesos (Agent + Dashboard) 
# Si el proyecto escala, se separan en dos contenedores Docker distintos, 
# pero aquí usamos shell o un wrapper para lanzarlos en background.
COPY scripts/start_services.sh .
RUN chmod +x start_services.sh

CMD ["./start_services.sh"]
