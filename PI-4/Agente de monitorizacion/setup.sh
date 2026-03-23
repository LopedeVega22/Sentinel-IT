#!/bin/bash

# ==============================================================================
# Script de Autodiagnóstico e Instalación para Raspberry Pi 4 (Sensor)
# ==============================================================================
# Este script prepara el entorno de la Pi 4 instalando dependencias,
# configurando iptables y desplegando el servicio systemd del agente SOC.

echo "==========================================="
echo "   🛡️  Configuración SOC - Nodo Sensor Pi4 "
echo "==========================================="

# 1. Comprobación de privilegios
if [ "$EUID" -ne 0 ]; then
  echo "❌ Por favor, ejecuta este script como root (sudo ./setup.sh)"
  exit 1
fi

echo "[*] Autodiagnóstico de Sistema Operativo..."
# Comprobar si Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "[-] Python3 no encontrado. Instalando..."
    apt-get update && apt-get install -y python3 python3-pip
else
    echo "[✓] Python3 detectado."
fi

# Comprobar iptables
if ! command -v iptables &> /dev/null; then
    echo "[-] iptables no encontrado. Instalando..."
    apt-get update && apt-get install -y iptables
else
    echo "[✓] iptables detectado."
fi

echo "\n[*] Instalando dependencias de Python (PyYAML, awsiotsdk)..."
pip3 install pyyaml awsiotsdk --break-system-packages

echo "\n[*] Comprobando archivos de Certificados AWS IoT..."
if [ ! -f "Pi4-felix.cert.pem" ] || [ ! -f "Pi4-felix.private.key" ] || [ ! -f "root-CA.crt" ]; then
    echo "⚠️  ADVERTENCIA: No se han encontrado todos los certificados de AWS IoT en este directorio."
    echo "Asegúrate de tener Pi4-felix.cert.pem, Pi4-felix.private.key y root-CA.crt antes de arrancar el servicio."
else
    echo "[✓] Archivos de certificados detectados."
fi

echo "\n[*] Configurando e instalando Daemon Systemd (soc-sensor.service)..."
if [ -f "soc-sensor.service" ]; then
    # Actualizar la ruta del ExecStart en el fichero de servicio para usar la ruta actual
    CURRENT_DIR=$(pwd)
    sed -i "s|/home/pi/TFG/pi4-felix|$CURRENT_DIR|g" soc-sensor.service
    
    cp soc-sensor.service /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable soc-sensor.service
    systemctl restart soc-sensor.service
    
    echo "[✓] Servicio soc-sensor configurado y arrancado con éxito."
    echo "Puedes ver los logs con: sudo journalctl -u soc-sensor -f"
else
    echo "❌ Error: No se encuentra soc-sensor.service en el directorio."
fi

echo "\n==========================================="
echo " ✅ Instalación y Diagnóstico Completados."
echo "==========================================="
