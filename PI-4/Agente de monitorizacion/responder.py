import json
import time
import logging
import sys
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

# --- Logging ---
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/lopex/pi4-felix/responder.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# --- Reusar configuración del agente principal ---
CLIENT_ID  = "Pi4-Felix-responder"
ENDPOINT   = "aj4wsdnimoej8-ats.iot.eu-north-1.amazonaws.com"
CA_PATH    = "/home/lopex/pi4-felix/root-CA.crt"
CERT_PATH  = "/home/lopex/pi4-felix/Pi4-Felix.cert.pem"
KEY_PATH   = "/home/lopex/pi4-felix/Pi4-Felix.private.key"

# Topics
TOPIC_EVENTOS        = "seguridad/cliente1/eventos"
TOPIC_TELEMETRIA     = "seguridad/cliente1/telemetria"
TOPIC_WEB_EVENTOS    = "seguridad/cliente1/web/eventos"

SUBSCRIBE_TOPIC = "seguridad/acciones/#"

def iniciar_mqtt():
    try:
        logger.info("Iniciando conexión MQTT...")
        cliente = AWSIoTMQTTClient(CLIENT_ID)
        cliente.configureEndpoint(ENDPOINT, 8883)
        cliente.configureCredentials(CA_PATH, KEY_PATH, CERT_PATH)
        
        # Aumentar timeout y configurar reconexión automática
        cliente.configureAutoReconnectBackoffTime(1, 32, 20)  # min=1s, max=32s, stable=20s
        cliente.configureConnectDisconnectTimeout(30)  # Timeout de 30 segundos para conectar
        cliente.configureMQTTOperationTimeout(10)  # Timeout para operaciones MQTT
        
        logger.info("Intentando conectar a AWS IoT Core...")
        cliente.connect()
        logger.info(f"[AWS] Responder conectado como '{CLIENT_ID}'")
        print(f"[AWS] Responder conectado como '{CLIENT_ID}'")
        return cliente
    except Exception as e:
        logger.error(f"Error al conectar MQTT: {e}", exc_info=True)
        print(f"[ERROR MQTT] {e}")
        raise

def publicar(cliente, topic, payload):
    try:
        mensaje = json.dumps(payload, ensure_ascii=False)
        cliente.publish(topic, mensaje, 1)
        logger.debug(f"[AWS] Publicado en '{topic}': {mensaje}")
        print(f"[AWS] Publicado en '{topic}': {mensaje}")
    except Exception as e:
        logger.error(f"Error al publicar en {topic}: {e}", exc_info=True)

def procesar_accion(cliente, topic, payload):
    # payload esperado: JSON con campos: accion, comando, motivo
    action = payload.get("accion") or payload.get("action")
    response = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sensor": CLIENT_ID,
        "action_received": action,
        "original_topic": topic,
    }

    # Lógica simple: si la acción menciona "web" publicar en web eventos,
    # si indica ftp/ssh publicar en eventos generales, si no, en telemetría.
    destino = TOPIC_TELEMETRIA
    text = (action or "").lower()
    if "web" in text or payload.get("target") == "web":
        destino = TOPIC_WEB_EVENTOS
        response["nota"] = "Respuesta dirigida a web/eventos"
    elif "ftp" in text or "ssh" in text or payload.get("target") in ("ftp", "ssh"):
        destino = TOPIC_EVENTOS
        response["nota"] = "Respuesta dirigida a eventos"
    else:
        response["nota"] = "Respuesta telemetría por defecto"

    # Adjuntar detalles si vienen
    if "params" in payload:
        response["params"] = payload["params"]

    publicar(cliente, destino, response)

    # Si la acción es ejecutar comando, procesarlo
    if action == "ejecutar_comando" or action == "execute_command":
        comando = payload.get("comando") or payload.get("command")
        motivo = payload.get("motivo") or payload.get("reason")
        if not comando:
            publicar(cliente, TOPIC_TELEMETRIA, {**response, "error": "no_command"})
            return

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
        publicar(cliente, "seguridad/cliente1/respuestas", resultado_payload)


def ejecutar_comando_seguro(comando):
    """Ejecuta un comando si pasa la lista blanca básica.
    Devuelve dict con exitcode, stdout, stderr, timed_out, allowed.
    """
    import shlex, subprocess

    # Lista blanca: comandos permitidos (binarios o palabras clave)
    WHITELIST = ["iptables", "php", "ufw", "systemctl", "ip"]

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
    except subprocess.TimeoutExpired as e:
        return {"allowed": True, "error": "timeout", "timed_out": True}
    except Exception as e:
        return {"allowed": True, "error": str(e)}

def on_message(client, userdata, message):
    try:
        payload = json.loads(message.payload)
    except Exception:
        try:
            payload = json.loads(message.payload.decode("utf-8"))
        except Exception:
            payload = {"raw": str(message.payload)}

    logger.info(f"[MQTT] Mensaje recibido en {message.topic}: {payload}")
    print(f"[MQTT] Mensaje recibido en {message.topic}: {payload}")
    procesar_accion(client, message.topic, payload)

def main():
    logger.info("=== Iniciando Responder ===")
    cliente = None
    try:
        cliente = iniciar_mqtt()
        # Iniciar el loop de manejo de eventos en background
        # CRÍTICO: Sin esto, el cliente MQTT se desconecta después de suscribirse
        logger.info("Iniciando loop de eventos MQTT...")
        cliente.loop_start()
        
        cliente.subscribe(SUBSCRIBE_TOPIC, 1, callback=on_message)
        logger.info(f"[Responder] Suscrito a '{SUBSCRIBE_TOPIC}' — esperando mensajes...")
        print(f"[Responder] Suscrito a '{SUBSCRIBE_TOPIC}' — esperando mensajes...")

        # Mantener el proceso vivo mientras el loop de eventos corre en background
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("[Responder] Detenido por usuario")
        print("[Responder] Detenido por usuario")
    except Exception as e:
        logger.error(f"Error en main(): {e}", exc_info=True)
        print(f"[ERROR] {e}")
    finally:
        if cliente:
            try:
                logger.info("Deteniendo loop de eventos...")
                cliente.loop_stop()
                cliente.disconnect()
                logger.info("Desconectado")
            except Exception as e:
                logger.error(f"Error al desconectar: {e}")

if __name__ == "__main__":
    main()
