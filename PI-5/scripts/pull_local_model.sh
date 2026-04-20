#!/bin/bash
# ==============================================================================
# Script para descargar el modelo local (Gemma 4 E2B) en Ollama
# ==============================================================================

echo "[*] Comprobando si el contenedor 'local-ai-engine' está en ejecución..."

if [ "$(docker ps -q -f name=local-ai-engine)" ]; then
    echo "[*] Contenedor local-ai-engine encontrado. Iniciando descarga del modelo gemma4:e2b..."
    docker exec -it local-ai-engine ollama pull gemma4:e2b
    echo "[+] Modelo descargado exitosamente."
else
    echo "[-] ADVERTENCIA: El contenedor 'local-ai-engine' no está corriendo."
    echo "    Asegúrate de ejecutar 'docker compose up -d' primero en la base del proyecto."
    exit 1
fi
