#!/bin/bash
# Script wrapper para levantar el Coordinador IA y el Dashboard Flask en el mismo Docker Container.
# Para producción "pura", cada proceso debería ir en un contenedor separado (Microservicios) orquestados con docker-compose.

# Inicializar esquema de BD (debe ejecutarse en runtime, no en build,
# porque el volumen 'soc_data_volume' se monta sobre /app/data y oculta el .db creado en build).
echo "Inicializando esquema de base de datos..."
mkdir -p /app/data
python src/database.py

echo "Iniciando Dashboard Web SOC en segundo plano..."
# Como los scripts se movieron a src/, los ejecutamos desde ese módulo o ruta:
python src/dashboard_soc.py &

echo "Iniciando Agente Coordinador (Google Gemini ADK)..."
python src/main_coordinator.py
