import os
import re
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

def execute_diagnostic_command(device: str, command: str, reason: str) -> dict:
    """
    Ejecuta un comando de diagnostico o lectura remota en el dispositivo (PI-4).
    BLOQUEARA comandos destructivos o mutadores.
    
    Args:
        device: ID del dispositivo objetivo.
        command: Comando Bash a ejecutar (ej. `grep 'Failed' /var/log/auth.log`).
        reason: Justificacion del comando.
    """
    if _iot_client is None:
        logger.error("[ERROR] Cliente IoT no inicializado.")
        return {"status": "error", "message": "IoT Client not initialized"}

    # Validacion HITL (Read-Only + Excepciones sudo)
    dangerous_keywords = ['rm ', 'kill ', 'reboot', 'chmod', 'chown', 'systemctl stop', 'systemctl restart']
    
    # Check for dangerous keywords
    for keyword in dangerous_keywords:
        if keyword in command:
            return {"status": "blocked", "message": f"Comando bloqueado por seguridad (contiene '{keyword}'). Usa request_mitigation_approval."}

    # Strict sudo check
    if 'sudo ' in command:
        # Allowlist para comandos sudo
        allowed_sudo = [
            'sudo iptables -L', 'sudo iptables -S', 
            'sudo systemctl status', 'sudo journalctl',
            'sudo cat ', 'sudo ls '
        ]
        is_allowed = any(command.startswith(allowed) for allowed in allowed_sudo)
        if not is_allowed:
            return {"status": "blocked", "message": "Comandos 'sudo' no autorizados para lectura. Usa request_mitigation_approval si es una mitigacion."}

    try:
        response_topic = f"{TOPIC_ACTIONS_BASE}{device}"
        action_payload = {
            "accion": "ejecutar_comando",
            "comando": command,
            "motivo": reason
        }
        _iot_client.publish(response_topic, action_payload)
        logger.info(f"[AGENT] Comando de diagnostico enviado a {device}: {command}")
        return {"status": "action_sent", "target": device, "command": command, "type": "diagnostic"}
    except Exception as e:
        logger.error(f"[ERROR] Error en execute_diagnostic_command: {e}")
        return {"status": "error", "message": str(e)}

def request_mitigation_approval(device: str, mitigation_command: str, rationale: str) -> dict:
    """
    Pone en cuarentena un comando de mitigacion destructiva (Sudo/Mutador) a la espera de aprobacion manual en el Dashboard.
    Usa esta herramienta cuando necesites neutralizar una amenaza.
    
    Args:
        device: ID del dispositivo objetivo.
        mitigation_command: Comando Bash destructivo (ej. `sudo iptables -A ...`).
        rationale: Justificacion para el humano de por que se debe ejecutar.
    """
    try:
        # Sanitizar: eliminar comentarios de bash al final del comando (ej. "# (Comando inferido)")
        mitigation_command = re.sub(r'\s*#\s*\(.*?\)\s*$', '', mitigation_command).strip()
        # Guardar en DB el comando en estado PENDING
        for attempt in range(5):
            conn = None
            try:
                conn = sqlite3.connect(DB_PATH, timeout=15.0, check_same_thread=False)
                conn.execute('PRAGMA journal_mode=WAL;')
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE logs 
                    SET status = 'PENDING',
                        pending_command = ?,
                        rationale = ?,
                        accion_tomada = CASE 
                            WHEN accion_tomada = 'Solo Registro' THEN ?
                            ELSE accion_tomada || ? 
                        END
                    WHERE id = (
                        SELECT id FROM logs 
                        WHERE dispositivo = ? 
                        ORDER BY timestamp DESC 
                        LIMIT 1
                    )
                """, (mitigation_command, rationale, f"Requiere Aprobacion: {mitigation_command}", f"\nRequiere Aprobacion: {mitigation_command}", device))
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

        logger.info(f"[AGENT] Mitigacion puesta en PENDING_APPROVAL para {device}: {mitigation_command}")
        return {
            "status": "pending_approval", 
            "message": "Comando en cuarentena. Se ha solicitado aprobacion al administrador. No debes hacer nada mas sobre esta alerta."
        }
    except Exception as e:
        logger.error(f"[ERROR] Error en request_mitigation_approval: {e}")
        return {"status": "error", "message": str(e)}
