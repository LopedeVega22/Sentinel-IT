import os
import yaml
import logging
import sqlite3
import time

# Definir rutas absolutas basadas en la ubicación de este script
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CONFIG_PATH = os.path.join(BASE_DIR, 'config.yml')

try:
    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)
    TOPIC_ACTIONS_BASE = config['mqtt']['topic_actions_base']
    DB_PATH = os.path.join(BASE_DIR, config['database']['db_path'])
except Exception:
    TOPIC_ACTIONS_BASE = "seguridad/acciones/"
    DB_PATH = os.path.join(BASE_DIR, "soc_data.db")

logger = logging.getLogger("CoordinatorSOC")

# Referencia global al cliente IoT, inyectada desde el coordinador principal
_iot_client = None

def init_iot_tools(iot_client):
    """
    Vincula el cliente MQTT activo para permitir la publicacion de acciones desde las herramientas.
    """
    global _iot_client
    _iot_client = iot_client

def block_ip(device: str, ip: str, reason: str) -> dict:
    """
    Ordena el bloqueo de una IP en el firewall del dispositivo remoto.
    Esta herramienta debe usarse ante ataques confirmados.
    
    Args:
        device: ID del dispositivo objetivo (ej. Pi4-dani).
        ip: Direccion IPv4/IPv6 a neutralizar. Excluir subredes a menos que sea critico. MUST be a valid IP format.
        reason: Justificacion concisa del bloqueo basada en el analisis.
    """
    if _iot_client is None:
        logger.error("[ERROR] Cliente IoT no inicializado.")
        return {"status": "error", "message": "IoT Client not initialized"}

    try:
        response_topic = f"{TOPIC_ACTIONS_BASE}{device}"
        action_payload = {
            "accion": "bloquear_ip",
            "ip": ip,
            "motivo": reason
        }
        _iot_client.publish(response_topic, action_payload)
        
        # Actualizacion del log en la base de datos local para reflejar la accion
        for attempt in range(5):
            conn = None
            try:
                # check_same_thread=False y timeout aseguran mayor tolerancia en multihilo/asíncrono
                conn = sqlite3.connect(DB_PATH, timeout=15.0, check_same_thread=False)
                conn.execute('PRAGMA journal_mode=WAL;')
                conn.execute('PRAGMA synchronous=NORMAL;')
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE logs 
                    SET accion_tomada = CASE 
                        WHEN accion_tomada = 'Solo Registro' THEN ?
                        ELSE accion_tomada || ? 
                    END
                    WHERE id = (
                        SELECT id FROM logs 
                        WHERE ip_origen = ? 
                        ORDER BY timestamp DESC 
                        LIMIT 1
                    )
                """, (f"Bloqueo Activo Emitido: {ip}", f"\nBloqueo Activo Emitido: {ip}", ip))
                conn.commit()
                break 
            except sqlite3.OperationalError as db_e:
                if "locked" in str(db_e).lower() or "readonly" in str(db_e).lower():
                    logger.warning(f"[WARNING] DB ocupada en bloqueo IP, reintento {attempt+1}/5...")
                    time.sleep(2)
                else:
                    logger.error(f"[ERROR] Error en actualizacion de bloqueo: {db_e}")
                    break
            except Exception as db_e:
                logger.error(f"[ERROR] Error critico en actualizacion de bloqueo: {db_e}")
                break
            finally:
                if conn:
                    conn.close()
        
        logger.info(f"[AGENT] Accion de bloqueo enviada a {device} para IP: {ip}")
        return {"status": "action_sent", "target": device, "ip": ip}
    except Exception as e:
        logger.error(f"[ERROR] Error en ejecucion de block_ip: {e}")
        return {"status": "error", "message": str(e)}

def execute_remote_command(device: str, command: str, reason: str) -> dict:
    """
    Envia un script de Bash o comando individual para su ejecucion directa en el dispositivo remoto (Raspberry).
    Util para diagnosticos o configuraciones defensivas especificas.
    
    Args:
        device: ID del dispositivo objetivo.
        command: Script Bash en crudo estructurado para ejecucion directa (sin formato markdown ```bash).
        reason: Justificacion tecnica de la accion a ejecutar.
    """
    if _iot_client is None:
        logger.error("[ERROR] Cliente IoT no inicializado.")
        return {"status": "error", "message": "IoT Client not initialized"}

    try:
        response_topic = f"{TOPIC_ACTIONS_BASE}{device}"
        action_payload = {
            "accion": "ejecutar_comando",
            "comando": command,
            "motivo": reason
        }
        _iot_client.publish(response_topic, action_payload)
        
        logger.info(f"[AGENT] Comando remoto enviado a {device}: {command}")
        
        # Guardar en DB el comando enviado
        for attempt in range(5):
            conn = None
            try:
                conn = sqlite3.connect(DB_PATH, timeout=15.0, check_same_thread=False)
                conn.execute('PRAGMA journal_mode=WAL;')
                conn.execute('PRAGMA synchronous=NORMAL;')
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE logs 
                    SET accion_tomada = CASE 
                        WHEN accion_tomada = 'Solo Registro' THEN ?
                        ELSE accion_tomada || ? 
                    END
                    WHERE id = (
                        SELECT id FROM logs 
                        WHERE dispositivo = ? 
                        ORDER BY timestamp DESC 
                        LIMIT 1
                    )
                """, (f"Comando Exec: {command}", f"\nComando Exec: {command}", device))
                conn.commit()
                break 
            except sqlite3.OperationalError as db_e:
                if "locked" in str(db_e).lower() or "readonly" in str(db_e).lower():
                    time.sleep(2)
                else:
                    break
            except Exception:
                break
            finally:
                if conn:
                    conn.close()

        return {"status": "action_sent", "target": device, "command": command}
    except Exception as e:
        logger.error(f"[ERROR] Error en envio de comando remoto: {e}")
        return {"status": "error", "message": str(e)}
