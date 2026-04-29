import time
import re
import json
import subprocess
import select
import threading
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

# ==============================================================================
# CONFIGURACIÓN DEL AGENTE
# Aquí se definen todos los parámetros de conexión y rutas de logs.
# Edita esta sección si cambias de dispositivo o de entorno.
# ==============================================================================
CLIENT_ID  = "Pi4-Felix"
ENDPOINT   = "aj4wsdnimoej8-ats.iot.eu-north-1.amazonaws.com"
CA_PATH    = "/home/lopex/pi4-felix/root-CA.crt"
CERT_PATH  = "/home/lopex/pi4-felix/Pi4-Felix.cert.pem"
KEY_PATH   = "/home/lopex/pi4-felix/Pi4-Felix.private.key"

# Topics MQTT: canales donde se publican los eventos y la telemetría
TOPIC_EVENTOS    = "seguridad/cliente1/eventos"     # Alertas inmediatas (SSH, FTP)
TOPIC_TELEMETRIA = "seguridad/cliente1/telemetria"  # Resúmenes periódicos (Web + Logs)

# Rutas de los archivos de log del sistema que se monitorizan
LOG_FTP    = "/var/log/vsftpd.log"
LOG_APACHE = "/var/log/apache2/access.log"

# Intervalo en segundos para el envío periódico de resúmenes
INTERVALO_ENVIO = 30

# ==============================================================================
# ESTRUCTURAS DE DATOS COMPARTIDAS (entre hilos)
# Estas listas acumulan eventos hasta que el hilo periódico las envía y vacía.
# Son accedidas por múltiples hilos, por eso se protegen con un Lock.
# ==============================================================================
lock = threading.Lock()
accesos_web_pendientes  = []   # Peticiones HTTP capturadas del log de Apache
eventos_ssh_pendientes  = []   # Fallos SSH capturados del journal
eventos_ftp_pendientes  = []   # Fallos FTP capturados del log vsftpd

# Diccionario para detectar ataques de diccionario FTP:
# { "ip": [timestamp1, timestamp2, ...] }
intentos_fallidos_ftp = {}
UMBRAL_INTENTOS = 10    # Número de intentos para considerar ataque
VENTANA_TIEMPO  = 30   # Ventana de tiempo en segundos para contar intentos

# ==============================================================================
# EXPRESIONES REGULARES
# Cada regex extrae los campos relevantes de cada tipo de log.
# ==============================================================================
regex_ftp    = r"\[(\w+)\] FAIL LOGIN: Client \"::ffff:(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\""
regex_apache = r"^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) .+\"GET (.*) HTTP"
regex_ssh    = r"Failed password for (?:invalid user )?(\S+) from (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"

# ==============================================================================
# CONEXIÓN CON AWS IoT CORE
# Se usa mTLS (certificados mutuos) para autenticar el dispositivo de forma segura.
# ==============================================================================
def iniciar_mqtt():
    """Crea y devuelve un cliente MQTT autenticado con AWS IoT Core."""
    cliente = AWSIoTMQTTClient(CLIENT_ID)
    cliente.configureEndpoint(ENDPOINT, 8883)
    cliente.configureCredentials(CA_PATH, KEY_PATH, CERT_PATH)
    cliente.connect()
    print(f"[AWS] Conectado como '{CLIENT_ID}'")
    return cliente

mqtt_client = iniciar_mqtt()

def publicar(topic, payload):
    """Serializa el payload a JSON y lo publica en el topic indicado."""
    mensaje = json.dumps(payload)
    mqtt_client.publish(topic, mensaje, 1)
    print(f"[AWS] Publicado en '{topic}': {mensaje}")

# ==============================================================================
# HILO PERIÓDICO: envío de resúmenes cada INTERVALO_ENVIO segundos
# Este hilo corre en paralelo al bucle principal y se encarga de:
#   - Enviar todos los accesos web acumulados
#   - Enviar todos los eventos SSH acumulados
#   - Enviar todos los eventos FTP acumulados (los que NO superaron el umbral)
# Usa un Lock para evitar condiciones de carrera al vaciar las listas.
# ==============================================================================
def hilo_envio_periodico():
    """Envía resúmenes consolidados de logs cada INTERVALO_ENVIO segundos."""
    while True:
        time.sleep(INTERVALO_ENVIO)
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        with lock:
            # --- Resumen de accesos web ---
            if accesos_web_pendientes:
                payload = {
                    "timestamp"        : timestamp,
                    "sensor"           : CLIENT_ID,
                    "tipo"             : "RESUMEN_ACCESOS_WEB",
                    "total_peticiones" : len(accesos_web_pendientes),
                    "detalles"         : accesos_web_pendientes[:10]  # Máx 10 para no saturar
                }
                publicar(TOPIC_TELEMETRIA, payload)
                accesos_web_pendientes.clear()

            # --- Resumen de eventos SSH ---
            if eventos_ssh_pendientes:
                payload = {
                    "timestamp"      : timestamp,
                    "sensor"         : CLIENT_ID,
                    "tipo"           : "RESUMEN_FALLOS_SSH",
                    "total_intentos" : len(eventos_ssh_pendientes),
                    "detalles"       : eventos_ssh_pendientes[:10]
                }
                publicar(TOPIC_TELEMETRIA, payload)
                eventos_ssh_pendientes.clear()

            # --- Resumen de eventos FTP (no críticos) ---
            if eventos_ftp_pendientes:
                payload = {
                    "timestamp"      : timestamp,
                    "sensor"         : CLIENT_ID,
                    "tipo"           : "RESUMEN_FALLOS_FTP",
                    "total_intentos" : len(eventos_ftp_pendientes),
                    "detalles"       : eventos_ftp_pendientes[:10]
                }
                publicar(TOPIC_TELEMETRIA, payload)
                eventos_ftp_pendientes.clear()

# ==============================================================================
# BUCLE PRINCIPAL DE MONITORIZACIÓN
# Lee continuamente los tres orígenes de logs:
#   1. Archivo vsftpd.log (FTP)
#   2. Archivo apache2/access.log (Web)
#   3. Proceso journalctl en tiempo real (SSH)
# ==============================================================================
def monitorizar():
    """Bucle principal: lee logs y publica alertas inmediatas o acumula para el resumen."""

    # Arrancar el hilo periódico como daemon (se cierra solo si el proceso principal acaba)
    hilo = threading.Thread(target=hilo_envio_periodico, daemon=True)
    hilo.start()

    # Abrir los archivos de log y posicionarse al final para leer solo nuevas líneas
    f_ftp = open(LOG_FTP,    "r")
    f_web = open(LOG_APACHE, "r")
    f_ftp.seek(0, 2)
    f_web.seek(0, 2)

    # Lanzar journalctl en modo seguimiento para capturar logs SSH del sistema
    proc_ssh = subprocess.Popen(
        ['journalctl', '-u', 'ssh', '-f', '-n', '0'],
        stdout=subprocess.PIPE,
        text=True
    )

    print(f"--- Agente SOC activo | Alertas inmediatas + Resumen cada {INTERVALO_ENVIO}s ---")

    try:
        while True:

            # ------------------------------------------------------------------
            # 1. FTP: detectar fallos de login
            # Si una IP acumula >= UMBRAL_INTENTOS en VENTANA_TIEMPO → ALERTA INMEDIATA
            # El resto se acumula para el resumen periódico
            # ------------------------------------------------------------------
            linea_ftp = f_ftp.readline()
            if linea_ftp:
                match = re.search(regex_ftp, linea_ftp)
                if match:
                    user, ip = match.groups()
                    ahora = time.time()

                    # Registrar intento y limpiar los que han caducado
                    if ip not in intentos_fallidos_ftp:
                        intentos_fallidos_ftp[ip] = []
                    intentos_fallidos_ftp[ip].append(ahora)
                    intentos_fallidos_ftp[ip] = [
                        t for t in intentos_fallidos_ftp[ip] if ahora - t < VENTANA_TIEMPO
                    ]

                    if len(intentos_fallidos_ftp[ip]) >= UMBRAL_INTENTOS:
                        # Supera el umbral → alerta inmediata de ataque de diccionario
                        publicar(TOPIC_EVENTOS, {
                            "evento"    : "ATAQUE_DICCIONARIO_FTP",
                            "ip"        : ip,
                            "intentos"  : len(intentos_fallidos_ftp[ip]),
                            "prioridad" : "ALTA",
                            "timestamp" : time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                        })
                        intentos_fallidos_ftp[ip] = []  # Resetear contador tras la alerta
                    else:
                        # Por debajo del umbral → acumular para resumen
                        with lock:
                            eventos_ftp_pendientes.append({
                                "ip": ip, "user": user, "t": ahora
                            })

            # ------------------------------------------------------------------
            # 2. WEB (Apache): acumular peticiones para el resumen periódico
            # No se generan alertas inmediatas de tráfico web normal
            # ------------------------------------------------------------------
            linea_web = f_web.readline()
            if linea_web:
                match_web = re.search(regex_apache, linea_web)
                if match_web:
                    ip_web, ruta = match_web.groups()
                    with lock:
                        accesos_web_pendientes.append({
                            "ip": ip_web, "ruta": ruta, "t": time.time()
                        })

            # ------------------------------------------------------------------
            # 3. SSH: alerta inmediata por cada fallo de autenticación
            # También se acumula en la lista para el resumen periódico
            # ------------------------------------------------------------------
            if select.select([proc_ssh.stdout], [], [], 0.01)[0]:
                linea_ssh = proc_ssh.stdout.readline()
                match_ssh = re.search(regex_ssh, linea_ssh)
                if match_ssh:
                    user_ssh, ip_ssh = match_ssh.groups()
                    evento = {
                        "ip"        : ip_ssh,
                        "user"      : user_ssh,
                        "timestamp" : time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    }
                    # Alerta inmediata
                    publicar(TOPIC_EVENTOS, {
                        **evento,
                        "evento"    : "FALLO_SSH",
                        "prioridad" : "MEDIA"
                    })
                    # También acumular para resumen
                    with lock:
                        eventos_ssh_pendientes.append(evento)

            time.sleep(0.1)  # Pequeña pausa para no saturar la CPU

    except KeyboardInterrupt:
        print("\n[*] Agente detenido por el usuario.")
        mqtt_client.disconnect()

# ==============================================================================
# PUNTO DE ENTRADA
# ==============================================================================
if __name__ == "__main__":
    monitorizar()
