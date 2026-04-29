# Guía de Uso Paso a Paso - SOC Coordinador (Nodo Pi 5)

Esta guía explica detalladamente cómo instalar, configurar y poner en marcha el sistema Inteligente SOC Coordinador de tu TFG en la Raspberry Pi 5.

## Requisitos Previos

Antes de ejecutar cualquier script, asegúrate de tener preparados los siguientes elementos en la carpeta del proyecto (`pi5-dani/`):

1. **Sistema Operativo**: Una Raspberry Pi 5 con Raspberry Pi OS u otra distribución de Linux compatible basada en Debian (y conexión a Internet).
2. **Certificados de AWS IoT**: Debes tener ubicados en el directorio raíz los certificados generados desde AWS IoT Core para la comunicación mTLS segura:
   * `Pi5-dani.cert.pem` (Certificado del dispositivo)
   * `Pi5-dani.private.key` (Clave privada)
   * `root-CA.crt` (Autoridad Certificadora Raíz de Amazon)
3. **Clave de IA (Gemini)**: Crea un archivo oculto llamado `.env` en la misma carpeta raíz, y añade la clave API de Google Gemini en su interior:

   ```bash
   GEMINI_API_KEY="tu_clave_api_de_google_aqui"
   ```

## Paso 1: Instalación y Configuración Automática

El sistema cuenta con un script de Bash preparado para instalar todas las dependencias necesarias, inicializar la base de datos y configurar el sistema local como demonios (servicios en segundo plano).

1. Abre un terminal de comandos y sitúate en la carpeta del proyecto.
2. Otorga permisos de ejecución a los scripts si aún no los tienen:

   ```bash
   chmod +x setup.sh start_services.sh
   ```

3. Ejecuta el archivo de configuración en modo administrador:

   ```bash
   sudo ./setup.sh
   ```

**¿Qué hace este script?**

* Escanea para ver si `python3` y `pip` están instalados y los descarga en caso de no estarlo.
* Instala las librerías necesarias definidas en `requirements.txt` (Google ADK, Flask, PyYAML, awsiotsdk, dotenv, etc.).
* Realiza un chequeo de la presencia de tus certificados AWS y variables de entorno `.env`.
* Inicializa la base de datos ejecutando `base_datos.py`, generando un entorno estéril SQLite (`soc_data.db`).
* Instala dos demonios o "daemons" del sistema Linux basándose en `soc-coordinator.service` y `soc-dashboard.service`.
* Activa y arranca dichos servicios para que corran constantemente de fondo, incluso si reinicias la máquina.

## Paso 2: Ejecución del Sistema

### Ejecución Automática (Recomendada)

Si ejecutaste `/setup.sh` satisfactoriamente, **los procesos ya están arrancados en segundo plano**. Se gestionan como servicios de Systemd:

* Para comprobar que el coordinador IA funciona: `sudo systemctl status soc-coordinator`
* Para comprobar que el dashboard web funciona: `sudo systemctl status soc-dashboard`

### Ejecución Manual (Para desarrollo y depuración)

Si prefieres saltarte los demonios y arrancar los procesos manualmente en la propia terminal de VSCode (para ver los logs y salidas en tiempo real, `print` en pantalla, etc.):

* En la carpeta del proyecto ejecuta el wrapper que levanta todo en una sola terminal:

  ```bash
  ./start_services.sh
  ```

* O alternativamente en dos consolas, ejecuta:

  ```bash
  python3 dashboard_soc.py
  ```

  Y en otra ventana:

  ```bash
  python3 main_coordinator.py
  ```

## Paso 3: Monitorización desde el Dashboard Web

Una vez los servicios están corriendo:

1. Abre un navegador web desde cualquier equipo en red con tu Pi5 (o en la propia Pi5).
2. Dirígete a la IP de la Raspberry en el puerto `5000`:

   ```url
   http://localhost:5000
   ```

   *(Cambia `localhost` por la IP local de tu Pi, ej: `http://192.168.1.50:5000`).*
3. En la interfaz web mejorada "Central SOC Inteligente", comprobarás:
   * **KPIs en tiempo real**: Número de logs analizados, eventos bloqueados activamente o la severidad.
   * **Veredictos IA**: Verás las tablas donde la Inteligencia Artificial (Gemini a través del Google ADK) analiza un log en tiempo real y expone por qué es malicioso o seguro.
   * **Alertas Defensivas**: Si ocurre un ataque de fuerza bruta, el campo `Acción Tomada` mostrará el bloqueo instruido a traves de MQTT.
