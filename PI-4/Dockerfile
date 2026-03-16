# Imagen base ligera de Python para arquitectura ARM (Raspberry Pi)
FROM python:3.11-slim

# Actualizar sistema e instalar iptables y nano
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    iptables \
    nano \
    && rm -rf /var/lib/apt/lists/*

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar archivos de requerimientos primero para cachear capas de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código del sensor
COPY . .

# Dar permisos de ejecución al entrypoint o mantener como CMD standard
# NOTA: Para comandos iptables reales, el contenedor requiere --cap-add=NET_ADMIN o --privileged
CMD ["python", "agente_monitor.py"]
