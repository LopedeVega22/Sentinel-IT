import time
import re
import json
import subprocess
import select
import threading
import shlex
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
 
# Topics MQTT
TOPIC_EVENTOS         = "seguridad/cliente1/eventos"          # Alertas inmediatas (SSH, FTP)
TOPIC_TELEMETRIA      = "seguridad/cliente1/telemetria"       # Resúmenes periódicos (SSH, FTP, Web Apache)
TOPIC_WEB_EVENTOS     = "seguridad/cliente1/web/eventos"      # Alertas inmediatas de la app web (SQLi, XSS, fuerza bruta)
TOPIC_WEB_TELEMETRIA  = "seguridad/cliente1/web/telemetria"   # Resumen periódico de actividad de la app web
 
# Rutas de los archivos de log del sistema que se monitorizan
LOG_FTP    = "/var/log/vsftpd.log"
LOG_APACHE = "/var/log/apache2/access.log"
LOG_WEB    = "/var/www/html/sentinelti.com/logs/activity_logs.json"
 
# Intervalo en segundos para el envío periódico de resúmenes
INTERVALO_ENVIO = 30
 
# ==============================================================================
# ESTRUCTURAS DE DATOS COMPARTIDAS (entre hilos)
# ==============================================================================
lock = threading.Lock()
accesos_web_pendientes  = []   # Peticiones HTTP capturadas del log de Apache
eventos_ssh_pendientes  = []   # Fallos SSH capturados del journal
eventos_ftp_pendientes  = []   # Fallos FTP capturados del log vsftpd
eventos_appweb_pendientes = [] # Eventos normales de la app web (para resumen)
 
# Diccionario para detectar ataques de diccionario FTP
intentos_fallidos_ftp = {}
UMBRAL_INTENTOS_FTP = 10
VENTANA_TIEMPO_FTP  = 30
 
# Diccionario para detectar fuerza bruta en el login de la app web
intentos_fallidos_web = {}
UMBRAL_FUERZA_BRUTA_WEB = 5
VENTANA_FUERZA_BRUTA_WEB = 60
 
# ==============================================================================
# EXPRESIONES REGULARES (SSH, FTP, Apache)
# ==============================================================================
regex_ftp    = r"\[(\w+)\] FAIL LOGIN: Client \"::ffff:(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\""
regex_apache = r"^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) .+\"GET (.*) HTTP"
regex_ssh    = r"Failed password for (?:invalid user )?(\S+) from (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
 
# ==============================================================================
# PATRONES DE ATAQUE PARA LA APP WEB
# ==============================================================================
PATRONES_SQLI = ["UNION SELECT", "' OR ", "1=1", "-- -", "DROP TABLE", "INSERT INTO"]
PATRONES_XSS  = ["<script", "javascript:", "onerror=", "onload=", "<br>", "<b>", "<i>", "<img"]
 
# ==============================================================================
# CONEXIÓN CON AWS IoT CORE
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
    mensaje = json.dumps(payload, ensure_ascii=False)
    mqtt_client.publish(topic, mensaje, 1)
    print(f"[AWS] Publicado en '{topic}': {mensaje}")
 
# ==============================================================================
# HILO PERIÓDICO: envío de resúmenes cada INTERVALO_ENVIO segundos
# Gestiona los cuatro buffers: Apache, SSH, FTP y actividad de la app web.
# ==============================================================================
def hilo_envio_periodico():
    """Envía resúmenes consolidados de logs cada INTERVALO_ENVIO segundos."""
    while True:
        time.sleep(INTERVALO_ENVIO)
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
 
        with lock:
            # --- Resumen de accesos web (Apache) ---
            if accesos_web_pendientes:
                payload = {
                    "timestamp"        : timestamp,
                    "sensor"           : CLIENT_ID,
                    "tipo"             : "RESUMEN_ACCESOS_WEB",
                    "total_peticiones" : len(accesos_web_pendientes),
                    "detalles"         : accesos_web_pendientes[:10]
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
 
            # --- Resumen de actividad de la app web SentinelTI ---
            if eventos_appweb_pendientes:
                conteo = {}
                for ev in eventos_appweb_pendientes:
                    accion = ev.get("action", "desconocida")
                    conteo[accion] = conteo.get(accion, 0) + 1
 
                payload = {
                    "timestamp"  : timestamp,
                    "sensor"     : CLIENT_ID,
                    "tipo"       : "RESUMEN_ACTIVIDAD_APP_WEB",
                    "total"      : len(eventos_appweb_pendientes),
                    "por_accion" : conteo,
                    "detalles"   : eventos_appweb_pendientes[:10]
                }
                publicar(TOPIC_WEB_TELEMETRIA, payload)
                eventos_appweb_pendientes.clear()
 
# ==============================================================================
# ANÁLISIS DE EVENTOS DE LA APP WEB
# ==============================================================================
def detectar_sqli(evento):
    """Detecta SQL Injection en el campo email del login."""
    detalles = evento.get("details", {})
    if not isinstance(detalles, dict):
        return None
    email = detalles.get("email", "")
    for patron in PATRONES_SQLI:
        if patron.upper() in email.upper():
            return {
                "evento"    : "SQL_INJECTION",
                "prioridad" : "CRITICA",
                "sensor"    : CLIENT_ID,
                "timestamp" : evento["timestamp"],
                "ip"        : evento.get("ip"),
                "usuario"   : evento.get("user_name"),
                "email_raw" : email,
                "patron"    : patron,
            }
    return None
 
def detectar_xss(evento):
    """Detecta XSS en el campo comentario de sugerencias."""
    detalles = evento.get("details", {})
    if not isinstance(detalles, dict):
        return None
    comentario = detalles.get("comentario", "")
    for patron in PATRONES_XSS:
        if patron.lower() in comentario.lower():
            return {
                "evento"     : "XSS_DETECTADO",
                "prioridad"  : "ALTA",
                "sensor"     : CLIENT_ID,
                "timestamp"  : evento["timestamp"],
                "ip"         : evento.get("ip"),
                "usuario"    : evento.get("user_name"),
                "rol"        : evento.get("role"),
                "comentario" : comentario,
                "patron"     : patron,
            }
    return None
 
def detectar_fuerza_bruta_web(evento):
    """Detecta fuerza bruta en el login web por acumulación de login_fallido por IP."""
    if evento.get("action") != "login_fallido":
        return None
 
    ip = evento.get("ip", "desconocida")
    try:
        t = time.mktime(time.strptime(evento["timestamp"], "%Y-%m-%d %H:%M:%S"))
    except Exception:
        t = time.time()
 
    ahora = time.time()
    if ip not in intentos_fallidos_web:
        intentos_fallidos_web[ip] = []
    intentos_fallidos_web[ip].append(t)
    intentos_fallidos_web[ip] = [
        ts for ts in intentos_fallidos_web[ip] if ahora - ts < VENTANA_FUERZA_BRUTA_WEB
    ]
 
    if len(intentos_fallidos_web[ip]) >= UMBRAL_FUERZA_BRUTA_WEB:
        intentos_fallidos_web[ip] = []
        return {
            "evento"    : "FUERZA_BRUTA_LOGIN_WEB",
            "prioridad" : "ALTA",
            "sensor"    : CLIENT_ID,
            "timestamp" : evento["timestamp"],
            "ip"        : ip,
            "intentos"  : UMBRAL_FUERZA_BRUTA_WEB,
        }
    return None
 
def analizar_evento_web(evento):
    """Devuelve una alerta si el evento es sospechoso, o None si es actividad normal."""
    accion = evento.get("action", "")
 
    if accion == "login_exitoso":
        alerta = detectar_sqli(evento)
        if alerta:
            return alerta
 
    if accion == "nueva_sugerencia":
        alerta = detectar_xss(evento)
        if alerta:
            return alerta
 
    if accion == "login_fallido":
        alerta = detectar_fuerza_bruta_web(evento)
        if alerta:
            return alerta
 
    return None
 
# ==============================================================================
# HILO MONITOR DE LA APP WEB (activity_logs.json)
# El JSON es un array completo que se reescribe con cada nuevo evento.
# Se compara el tamaño del array en cada ciclo para detectar entradas nuevas.
# Los nuevos eventos están al principio porque el log es descendente.
# ==============================================================================
def cargar_logs_web():
    """Lee el archivo JSON de la app y devuelve la lista de eventos, o [] si hay error."""
    try:
        with open(LOG_WEB, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError, OSError):
        return []
 
def hilo_monitor_web():
    """Hilo dedicado a monitorizar activity_logs.json en tiempo real."""
    logs_actuales = cargar_logs_web()
    ultimo_total  = len(logs_actuales)
    print(f"[WEB] Monitor app web activo | {ultimo_total} eventos históricos ignorados")
 
    while True:
        time.sleep(1)
 
        logs_nuevos = cargar_logs_web()
        total_nuevo = len(logs_nuevos)
 
        if total_nuevo <= ultimo_total:
            continue
 
        n_nuevos = total_nuevo - ultimo_total
        nuevos   = logs_nuevos[:n_nuevos]
        ultimo_total = total_nuevo
 
        print(f"[WEB] {n_nuevos} evento(s) nuevo(s) en activity_logs.json")
 
        # Procesar del más antiguo al más reciente
        for evento in reversed(nuevos):
            alerta = analizar_evento_web(evento)
 
            if alerta:
                # Evento sospechoso → alerta inmediata en topic web/eventos
                publicar(TOPIC_WEB_EVENTOS, alerta)
            else:
                # Evento normal → acumular para el resumen periódico
                with lock:
                    eventos_appweb_pendientes.append({
                        "timestamp" : evento.get("timestamp"),
                        "action"    : evento.get("action"),
                        "user"      : evento.get("user_name"),
                        "role"      : evento.get("role"),
                        "ip"        : evento.get("ip"),
                    })
 
# ==============================================================================
# BUCLE PRINCIPAL DE MONITORIZACIÓN (SSH, FTP, Apache)
# ==============================================================================
def ejecutar_comando_seguro(comando):
    """Ejecuta un comando si pasa la lista blanca básica.
    Devuelve dict con exitcode, stdout, stderr, timed_out, allowed.
    """
    # Lista blanca: comandos permitidos (binarios o palabras clave)
    WHITELIST = ["iptables", "php", "ufw", "systemctl", "ip", "whoami", "date", "uptime", "df"]

    # Verificar si alguno de los tokens del comando está en la whitelist
    try:
        tokens = shlex.split(comando)
    except Exception:
        tokens = comando.split()

    allowed = any(tok in WHITELIST or any(tok.startswith(w) for w in WHITELIST) for tok in tokens)
    if not allowed:
        return {"allowed": False, "error": "command_not_whitelisted"}

    try:
        proc = subprocess.run(comando, shell=True, capture_output=True, text=True, timeout=30)
        return {
            "allowed": True,
            "exitcode": proc.returncode,
            "stdout": proc.stdout[:4000],
            "stderr": proc.stderr[:4000],
            "timed_out": False,
        }
    except subprocess.TimeoutExpired:
        return {"allowed": True, "error": "timeout", "timed_out": True}
    except Exception as e:
        return {"allowed": True, "error": str(e)}

def on_message_callback(client, userdata, message):
    """Callback para recibir y procesar comandos desde seguridad/acciones/#"""
    try:
        try:
            payload = json.loads(message.payload)
        except Exception:
            try:
                payload = json.loads(message.payload.decode("utf-8"))
            except Exception:
                payload = {"raw": str(message.payload)}

        print(f"[COMANDO] Recibido en {message.topic}: {payload}")
        
        action = payload.get("accion") or payload.get("action")
        
        # Si la acción es ejecutar comando, procesarlo
        if action == "ejecutar_comando" or action == "execute_command":
            comando = payload.get("comando") or payload.get("command")
            motivo = payload.get("motivo") or payload.get("reason")
            
            if not comando:
                print("[COMANDO] Error: sin field 'comando'")
                return

            print(f"[COMANDO] Ejecutando: {comando}")
            resultado = ejecutar_comando_seguro(comando)
            
            resultado_payload = {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "sensor": CLIENT_ID,
                "tipo": "RESPUESTA_COMANDO",
                "comando": comando,
                "motivo": motivo,
                "resultado": resultado,
            }
            # Publicar en topic de respuestas
            publicar(TOPIC_TELEMETRIA, resultado_payload)
            print(f"[COMANDO] Respuesta publicada: {resultado}")
    except Exception as e:
        print(f"[COMANDO ERROR] {e}")

def hilo_escucha_comandos():
    """Hilo dedicado a suscribirse y escuchar comandos en seguridad/acciones/#"""
    try:
        print("[COMANDOS] Hilo iniciado - suscribiendo a seguridad/acciones/#")
        mqtt_client.subscribe("seguridad/acciones/#", 1, callback=on_message_callback)
        print("[COMANDOS] Suscrito a seguridad/acciones/#")
    except Exception as e:
        print(f"[COMANDOS ERROR] Fallo al suscribirse: {e}")

def monitorizar():
    """Bucle principal: lee logs de sistema y publica alertas o acumula para resumen."""
 
    # Hilo de escucha de comandos
    hilo_cmd = threading.Thread(target=hilo_escucha_comandos, daemon=True)
    hilo_cmd.start()
 
    # Hilo periódico de resúmenes
    hilo_periodico = threading.Thread(target=hilo_envio_periodico, daemon=True)
    hilo_periodico.start()
 
    # Hilo de monitorización de la app web
    hilo_web = threading.Thread(target=hilo_monitor_web, daemon=True)
    hilo_web.start()
 
    # Abrir los archivos de log y posicionarse al final
    f_ftp = open(LOG_FTP,    "r")
    f_web = open(LOG_APACHE, "r")
    f_ftp.seek(0, 2)
    f_web.seek(0, 2)
 
    # Lanzar journalctl para SSH
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
            # ------------------------------------------------------------------
            linea_ftp = f_ftp.readline()
            if linea_ftp:
                match = re.search(regex_ftp, linea_ftp)
                if match:
                    user, ip = match.groups()
                    ahora = time.time()
 
                    if ip not in intentos_fallidos_ftp:
                        intentos_fallidos_ftp[ip] = []
                    intentos_fallidos_ftp[ip].append(ahora)
                    intentos_fallidos_ftp[ip] = [
                        t for t in intentos_fallidos_ftp[ip] if ahora - t < VENTANA_TIEMPO_FTP
                    ]
 
                    if len(intentos_fallidos_ftp[ip]) >= UMBRAL_INTENTOS_FTP:
                        publicar(TOPIC_EVENTOS, {
                            "evento"    : "ATAQUE_DICCIONARIO_FTP",
                            "ip"        : ip,
                            "intentos"  : len(intentos_fallidos_ftp[ip]),
                            "prioridad" : "ALTA",
                            "timestamp" : time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                        })
                        intentos_fallidos_ftp[ip] = []
                    else:
                        with lock:
                            eventos_ftp_pendientes.append({
                                "ip": ip, "user": user, "t": ahora
                            })
 
            # ------------------------------------------------------------------
            # 2. WEB (Apache): acumular peticiones para el resumen periódico
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
                    publicar(TOPIC_EVENTOS, {
                        **evento,
                        "evento"    : "FALLO_SSH",
                        "prioridad" : "MEDIA"
                    })
                    with lock:
                        eventos_ssh_pendientes.append(evento)
 
            time.sleep(0.1)
 
    except KeyboardInterrupt:
        print("\n[*] Agente detenido por el usuario.")
        mqtt_client.disconnect()
 
# ==============================================================================
# PUNTO DE ENTRADA
# ==============================================================================
if __name__ == "__main__":
    monitorizar()
