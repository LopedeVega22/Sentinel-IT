import time
import re
import json
import subprocess
import select
import threading
import logging
import sys
import queue
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import signing

# ==============================================================================
# LOGGING
# ==============================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/home/lopex/pi4-felix/agente_soc.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)
 
# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================
CLIENT_ID = "Pi4-Felix"
ENDPOINT  = "aj4wsdnimoej8-ats.iot.eu-north-1.amazonaws.com"
CA_PATH   = "/home/lopex/pi4-felix/root-CA.crt"
CERT_PATH = "/home/lopex/pi4-felix/Pi4-Felix.cert.pem"
KEY_PATH  = "/home/lopex/pi4-felix/Pi4-Felix.private.key"
# Clave publica Ed25519 del coordinador PI-5. Solo verifica; nunca firma.
# El compañero PI-5 entrega el .pub generado por scripts/generate_signing_keys.py.
SIGNING_PUB_PATH = "/home/lopex/pi4-felix/sentinel_pi5_signing.pub"
 
# Topics
TOPIC_EVENTOS    = "seguridad/Pi4-Felix/evento"
TOPIC_TELEMETRIA = "seguridad/Pi4-Felix/telemetria"
TOPIC_RESPUESTAS = "seguridad/Pi4-Felix/respuesta"
TOPIC_ACCIONES   = "seguridad/Pi4-Felix/comando"
 
# Logs del sistema
LOG_FTP    = "/var/log/vsftpd.log"
LOG_APACHE = "/var/log/apache2/access.log"
LOG_WEB    = "/var/www/html/sentinelti.com/logs/activity_logs.json"
 
INTERVALO_ENVIO = 30
 
# ==============================================================================
# ESTADO COMPARTIDO
# ==============================================================================
lock = threading.Lock()
accesos_web_pendientes    = []
eventos_ssh_pendientes    = []
eventos_ftp_pendientes    = []
eventos_appweb_pendientes = []
 
intentos_fallidos_ftp = {}
UMBRAL_INTENTOS_FTP   = 10
VENTANA_TIEMPO_FTP    = 30
 
intentos_fallidos_web     = {}
UMBRAL_FUERZA_BRUTA_WEB   = 5
VENTANA_FUERZA_BRUTA_WEB  = 60
 
# ==============================================================================
# REGEXES
# ==============================================================================
regex_ftp    = r"\[(\w+)\] FAIL LOGIN: Client \"::ffff:(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\""
regex_apache = r"^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) .+\"GET (.*) HTTP"
regex_ssh    = r"Failed password for (?:invalid user )?(\S+) from (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
 
# ==============================================================================
# PATRONES DE ATAQUE
# ==============================================================================
PATRONES_SQLI = ["UNION SELECT", "' OR ", "1=1", "-- -", "DROP TABLE", "INSERT INTO"]
PATRONES_XSS  = ["<script", "javascript:", "onerror=", "onload=", "<br>", "<b>", "<i>", "<img"]
 
 
# ==============================================================================
# CLIENTE MQTT (único, compartido por todo el agente)
# ==============================================================================
def iniciar_mqtt() -> AWSIoTMQTTClient:
    logger.info("Conectando a AWS IoT Core...")
    cliente = AWSIoTMQTTClient(CLIENT_ID, cleanSession=True)
    cliente.configureEndpoint(ENDPOINT, 8883)
    cliente.configureCredentials(CA_PATH, KEY_PATH, CERT_PATH)
    cliente.configureAutoReconnectBackoffTime(1, 32, 20)
    cliente.configureConnectDisconnectTimeout(30)
    cliente.configureMQTTOperationTimeout(10)
    cliente.connect()
    logger.info(f"Conectado como '{CLIENT_ID}'")
    return cliente
 
mqtt_client = iniciar_mqtt()
 
# Cola thread-safe para publicaciones.
# El callback del SDK corre en su hilo interno — publicar desde ahí causa
# publishTimeoutException porque el SDK no puede atender la publicación
# mientras está despachando el mensaje entrante. La solución: encolar el
# mensaje y publicarlo desde un hilo dedicado independiente al SDK.
_publish_queue: queue.Queue = queue.Queue()
 
def _hilo_publicador():
    """Consume la cola y publica en MQTT desde un hilo independiente al SDK."""
    while True:
        topic, mensaje = _publish_queue.get()
        try:
            mqtt_client.publish(topic, mensaje, 1)
            logger.info(f"[PUB] {topic} → {mensaje[:200]}")
        except Exception as e:
            logger.error(f"Error publicando en {topic}: {e}", exc_info=True)
        finally:
            _publish_queue.task_done()
 
def publicar(topic: str, payload: dict):
    """Encola un mensaje para publicación (seguro desde cualquier hilo, incluido el del SDK)."""
    mensaje = json.dumps(payload, ensure_ascii=False)
    _publish_queue.put((topic, mensaje))
 
# ==============================================================================
# EJECUCIÓN DE COMANDOS
# ==============================================================================
def ejecutar_comando_seguro(comando: str) -> dict:
    """Ejecuta cualquier comando recibido. Devuelve exitcode, stdout, stderr."""
    try:
        proc = subprocess.run(
            comando, shell=True, capture_output=True, text=True, timeout=30
        )
        return {
            "exitcode":  proc.returncode,
            "stdout":    proc.stdout[:4000],
            "stderr":    proc.stderr[:4000],
            "timed_out": False,
        }
    except subprocess.TimeoutExpired:
        return {"error": "timeout", "timed_out": True}
    except Exception as e:
        return {"error": str(e)}
 
# ==============================================================================
# CALLBACK MQTT — recibe acciones del modelo de IA
# El SDK de AWSIoTPythonSDK llama a esta función automáticamente.
# NO manipular el cliente interno de paho; solo usar subscribe(callback=...).
# ==============================================================================
def on_accion(client, userdata, message):
    """Procesa mensajes recibidos en seguridad/Pi4-Felix/comando"""
    import uuid
    exec_id = uuid.uuid4().hex[:6]
    try:
        raw = message.payload
        payload = json.loads(raw if isinstance(raw, str) else raw.decode("utf-8"))
    except Exception:
        payload = {"raw": str(message.payload)}
 
    logger.info(f"[ACCION:{exec_id}] topic={message.topic} payload={payload}")

    if not isinstance(payload, dict):
        logger.warning("Payload no es un dict, ignorando.")
        return

    # --- Verificacion criptografica de origen (Ed25519) ---
    # Solo ejecutamos ordenes firmadas por PI-5. Comprometer PI-4 no permite
    # forjar comandos: aqui solo tenemos la clave publica.
    ok, motivo_firma = signing.verify_payload(payload)
    if not ok:
        ts_now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        logger.error(f"[ACCION:{exec_id}] COMANDO RECHAZADO POR FIRMA: {motivo_firma}")
        publicar(TOPIC_RESPUESTAS, {
            "timestamp": ts_now,
            "sensor":    CLIENT_ID,
            "tipo":      "RESULTADO_COMANDO",
            "accion":    payload.get("accion") or payload.get("action", ""),
            "comando":   payload.get("comando") or payload.get("command", ""),
            "status":    "rejected_signature",
            "resultado": {"error": motivo_firma, "exitcode": -1},
            "original_topic": message.topic,
        })
        return

    accion  = payload.get("accion") or payload.get("action", "")
    comando = payload.get("comando") or payload.get("command")
    motivo  = payload.get("motivo") or payload.get("reason", "")
    ts      = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
 
    # --- Ejecutar comando remoto ---
    if accion in ("ejecutar_comando", "execute_command"):
        if not comando:
            logger.warning("Acción ejecutar_comando sin campo 'comando'")
            publicar(TOPIC_RESPUESTAS, {
                "timestamp": ts, "sensor": CLIENT_ID,
                "tipo": "ERROR_COMANDO", "error": "no_command",
                "original_topic": message.topic,
            })
            return
 
        logger.info(f"Ejecutando comando: {comando} | motivo: {motivo}")
        resultado = ejecutar_comando_seguro(comando)
 
        publicar(TOPIC_RESPUESTAS, {
            "timestamp": ts,
            "sensor":    CLIENT_ID,
            "tipo":      "RESULTADO_COMANDO",
            "accion":    accion,
            "comando":   comando,
            "motivo":    motivo,
            "resultado": resultado,
            "original_topic": message.topic,
        })
 
    # --- Otras acciones: reenviar confirmación al topic correspondiente ---
    else:
        texto = accion.lower()
        if "web" in texto or payload.get("target") == "web":
            destino = "seguridad/cliente1/web/eventos"
        elif any(k in texto for k in ("ftp", "ssh")):
            destino = TOPIC_EVENTOS
        else:
            destino = TOPIC_TELEMETRIA
 
        publicar(destino, {
            "timestamp":      ts,
            "sensor":         CLIENT_ID,
            "tipo":           "ACCION_RECIBIDA",
            "accion":         accion,
            "original_topic": message.topic,
            "params":         payload.get("params"),
        })
 
# ==============================================================================
# ANÁLISIS DE EVENTOS DE LA APP WEB
# ==============================================================================
def detectar_sqli(evento: dict) -> dict | None:
    detalles = evento.get("details", {})
    if not isinstance(detalles, dict):
        return None
    email = detalles.get("email", "")
    for patron in PATRONES_SQLI:
        if patron.upper() in email.upper():
            return {
                "evento": "SQL_INJECTION", "prioridad": "CRITICA",
                "sensor": CLIENT_ID, "timestamp": evento["timestamp"],
                "ip": evento.get("ip"), "usuario": evento.get("user_name"),
                "email_raw": email, "patron": patron,
            }
    return None
 
def detectar_xss(evento: dict) -> dict | None:
    detalles = evento.get("details", {})
    if not isinstance(detalles, dict):
        return None
    comentario = detalles.get("comentario", "")
    for patron in PATRONES_XSS:
        if patron.lower() in comentario.lower():
            return {
                "evento": "XSS_DETECTADO", "prioridad": "ALTA",
                "sensor": CLIENT_ID, "timestamp": evento["timestamp"],
                "ip": evento.get("ip"), "usuario": evento.get("user_name"),
                "rol": evento.get("role"), "comentario": comentario,
                "patron": patron,
            }
    return None
 
def detectar_fuerza_bruta_web(evento: dict) -> dict | None:
    if evento.get("action") != "login_fallido":
        return None
    ip = evento.get("ip", "desconocida")
    try:
        t = time.mktime(time.strptime(evento["timestamp"], "%Y-%m-%d %H:%M:%S"))
    except Exception:
        t = time.time()
 
    ahora = time.time()
    intentos_fallidos_web.setdefault(ip, []).append(t)
    intentos_fallidos_web[ip] = [
        ts for ts in intentos_fallidos_web[ip] if ahora - ts < VENTANA_FUERZA_BRUTA_WEB
    ]
    if len(intentos_fallidos_web[ip]) >= UMBRAL_FUERZA_BRUTA_WEB:
        intentos_fallidos_web[ip] = []
        return {
            "evento": "FUERZA_BRUTA_LOGIN_WEB", "prioridad": "ALTA",
            "sensor": CLIENT_ID, "timestamp": evento["timestamp"],
            "ip": ip, "intentos": UMBRAL_FUERZA_BRUTA_WEB,
        }
    return None
 
def analizar_evento_web(evento: dict) -> dict | None:
    accion = evento.get("action", "")
    if accion == "login_exitoso":
        return detectar_sqli(evento)
    if accion == "nueva_sugerencia":
        return detectar_xss(evento)
    if accion == "login_fallido":
        return detectar_fuerza_bruta_web(evento)
    return None
 
# ==============================================================================
# HILO: monitor de activity_logs.json
# ==============================================================================
def cargar_logs_web() -> list:
    try:
        with open(LOG_WEB, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []
 
def hilo_monitor_web():
    logs_actuales = cargar_logs_web()
    ultimo_total  = len(logs_actuales)
    logger.info(f"[WEB] Monitor activo | {ultimo_total} eventos históricos ignorados")
 
    while True:
        time.sleep(1)
        logs_nuevos = cargar_logs_web()
        total_nuevo = len(logs_nuevos)
        if total_nuevo <= ultimo_total:
            continue
 
        n_nuevos     = total_nuevo - ultimo_total
        nuevos       = logs_nuevos[:n_nuevos]
        ultimo_total = total_nuevo
        logger.info(f"[WEB] {n_nuevos} evento(s) nuevo(s)")
 
        for evento in reversed(nuevos):
            alerta = analizar_evento_web(evento)
            if alerta:
                publicar(TOPIC_EVENTOS, alerta)
            else:
                with lock:
                    eventos_appweb_pendientes.append({
                        "timestamp": evento.get("timestamp"),
                        "action":    evento.get("action"),
                        "user":      evento.get("user_name"),
                        "role":      evento.get("role"),
                        "ip":        evento.get("ip"),
                    })
 
# ==============================================================================
# HILO: envío periódico de resúmenes
# ==============================================================================
def hilo_envio_periodico():
    while True:
        time.sleep(INTERVALO_ENVIO)
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        with lock:
            if accesos_web_pendientes:
                publicar(TOPIC_TELEMETRIA, {
                    "timestamp": ts, "sensor": CLIENT_ID,
                    "tipo": "RESUMEN_ACCESOS_WEB",
                    "total_peticiones": len(accesos_web_pendientes),
                    "detalles": accesos_web_pendientes[:10],
                })
                accesos_web_pendientes.clear()
 
            if eventos_ssh_pendientes:
                publicar(TOPIC_TELEMETRIA, {
                    "timestamp": ts, "sensor": CLIENT_ID,
                    "tipo": "RESUMEN_FALLOS_SSH",
                    "total_intentos": len(eventos_ssh_pendientes),
                    "detalles": eventos_ssh_pendientes[:10],
                })
                eventos_ssh_pendientes.clear()
 
            if eventos_ftp_pendientes:
                publicar(TOPIC_TELEMETRIA, {
                    "timestamp": ts, "sensor": CLIENT_ID,
                    "tipo": "RESUMEN_FALLOS_FTP",
                    "total_intentos": len(eventos_ftp_pendientes),
                    "detalles": eventos_ftp_pendientes[:10],
                })
                eventos_ftp_pendientes.clear()
 
            if eventos_appweb_pendientes:
                conteo = {}
                for ev in eventos_appweb_pendientes:
                    accion = ev.get("action", "desconocida")
                    conteo[accion] = conteo.get(accion, 0) + 1
                publicar(TOPIC_TELEMETRIA, {
                    "timestamp": ts, "sensor": CLIENT_ID,
                    "tipo": "RESUMEN_ACTIVIDAD_APP_WEB",
                    "total": len(eventos_appweb_pendientes),
                    "por_accion": conteo,
                    "detalles": eventos_appweb_pendientes[:10],
                })
                eventos_appweb_pendientes.clear()
 
# ==============================================================================
# BUCLE PRINCIPAL
# ==============================================================================
def monitorizar():
    # Cargar la clave publica antes de suscribirse: preferimos fallar al
    # arrancar a procesar comandos sin verificar.
    signing.load_public_key(SIGNING_PUB_PATH)

    # Suscripción a acciones del modelo de IA
    # El SDK gestiona el loop en background; solo pasar callback aquí.
    mqtt_client.subscribe(TOPIC_ACCIONES, 1, callback=on_accion)
    logger.info(f"Suscrito a '{TOPIC_ACCIONES}' — esperando acciones del modelo IA")
 
    # Hilos auxiliares
    threading.Thread(target=_hilo_publicador,     daemon=True, name="publicador").start()
    threading.Thread(target=hilo_envio_periodico, daemon=True, name="periodico").start()
    threading.Thread(target=hilo_monitor_web,     daemon=True, name="monitor-web").start()
 
    # Abrir logs y posicionarse al final
    f_ftp = open(LOG_FTP,    "r")
    f_web = open(LOG_APACHE, "r")
    f_ftp.seek(0, 2)
    f_web.seek(0, 2)
 
    # Journalctl para SSH en tiempo real
    proc_ssh = subprocess.Popen(
        ["journalctl", "-u", "ssh", "-f", "-n", "0"],
        stdout=subprocess.PIPE,
        text=True,
    )
 
    logger.info("=== Agente SOC activo ===")
    logger.info(f"Resúmenes periódicos cada {INTERVALO_ENVIO}s")
 
    try:
        while True:
            # --- FTP ---
            linea_ftp = f_ftp.readline()
            if linea_ftp:
                match = re.search(regex_ftp, linea_ftp)
                if match:
                    user, ip = match.groups()
                    ahora = time.time()
                    intentos_fallidos_ftp.setdefault(ip, []).append(ahora)
                    intentos_fallidos_ftp[ip] = [
                        t for t in intentos_fallidos_ftp[ip]
                        if ahora - t < VENTANA_TIEMPO_FTP
                    ]
                    if len(intentos_fallidos_ftp[ip]) >= UMBRAL_INTENTOS_FTP:
                        publicar(TOPIC_EVENTOS, {
                            "evento": "ATAQUE_DICCIONARIO_FTP", "ip": ip,
                            "intentos": len(intentos_fallidos_ftp[ip]),
                            "prioridad": "ALTA",
                            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        })
                        intentos_fallidos_ftp[ip] = []
                    else:
                        with lock:
                            eventos_ftp_pendientes.append({"ip": ip, "user": user, "t": ahora})
 
            # --- Apache ---
            linea_web = f_web.readline()
            if linea_web:
                match_web = re.search(regex_apache, linea_web)
                if match_web:
                    ip_web, ruta = match_web.groups()
                    with lock:
                        accesos_web_pendientes.append({"ip": ip_web, "ruta": ruta, "t": time.time()})
 
            # --- SSH ---
            if select.select([proc_ssh.stdout], [], [], 0.01)[0]:
                linea_ssh = proc_ssh.stdout.readline()
                match_ssh = re.search(regex_ssh, linea_ssh)
                if match_ssh:
                    user_ssh, ip_ssh = match_ssh.groups()
                    evento = {
                        "ip": ip_ssh, "user": user_ssh,
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    }
                    publicar(TOPIC_EVENTOS, {
                        **evento, "evento": "FALLO_SSH", "prioridad": "MEDIA",
                    })
                    with lock:
                        eventos_ssh_pendientes.append(evento)
 
            time.sleep(0.1)
 
    except KeyboardInterrupt:
        logger.info("Agente detenido por el usuario.")
    finally:
        try:
            # Esperar a que la cola de publicación se vacíe antes de desconectar
            _publish_queue.join()
            mqtt_client.disconnect()
            logger.info("Desconectado de AWS IoT Core.")
        except Exception as e:
            logger.error(f"Error al desconectar: {e}")
 
# ==============================================================================
# PUNTO DE ENTRADA
# ==============================================================================
if __name__ == "__main__":
    monitorizar()