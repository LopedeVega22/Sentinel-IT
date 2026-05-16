import os
import re
import yaml
import logging
import sqlite3
import time

from tools import policy_engine

# Definir rutas absolutas basadas en la ubicación de este script
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CONFIG_PATH = os.path.join(BASE_DIR, 'config.yml')

try:
    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)
    # Plantilla "seguridad/{device}/comando" — {device} se reemplaza al publicar
    TOPIC_PUBLISH_COMANDO = config['mqtt']['topic_publish_comando']
    DB_PATH = os.path.join(BASE_DIR, config['database']['db_path'])
except Exception:
    TOPIC_PUBLISH_COMANDO = "seguridad/{device}/comando"
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

    Filtrado por el Policy Engine: solo se publica directo si el motor lo
    clasifica como SAFE_READ. Cualquier otro nivel (LOW/HIGH/CRITICAL) se
    redirige automaticamente al flujo HITL via request_mitigation_approval
    con la razon de la clasificacion adjunta.

    Args:
        device: ID del dispositivo objetivo.
        command: Comando Bash a ejecutar (ej. `grep 'Failed' /var/log/auth.log`).
        reason: Justificacion del comando.
    """
    if _iot_client is None:
        logger.error("[ERROR] Cliente IoT no inicializado.")
        return {"status": "error", "message": "IoT Client not initialized"}

    decision = policy_engine.decide(command)
    cls = decision.classification

    if not decision.allow_direct:
        # No es lectura pura. Redirigimos al HITL con la razon del motor.
        redirected_reason = (
            f"[{cls.level.label()}] {reason} | Motor de politicas: "
            f"{'; '.join(cls.reasons)}"
        )
        logger.info(
            f"[POLICY] Comando '{command}' clasificado como {cls.level.label()} -> "
            f"redirigido a HITL."
        )
        return request_mitigation_approval(device, command, redirected_reason)

    try:
        response_topic = TOPIC_PUBLISH_COMANDO.replace("{device}", device)
        action_payload = {
            "accion": "ejecutar_comando",
            "comando": command,
            "motivo": reason
        }
        _iot_client.publish(response_topic, action_payload)
        policy_engine.record_dispatch(command, device, log_id=None)
        policy_engine.audit(
            event_type="DISPATCH",
            device=device,
            command=command,
            classification=cls,
            decision_reason=reason,
        )
        logger.info(f"[AGENT] Comando de diagnostico enviado a {device}: {command}")
        return {
            "status": "action_sent",
            "target": device,
            "command": command,
            "type": "diagnostic",
            "risk_level": cls.level.label(),
        }
    except Exception as e:
        logger.error(f"[ERROR] Error en execute_diagnostic_command: {e}")
        return {"status": "error", "message": str(e)}

def request_mitigation_approval(device: str, mitigation_command: str, rationale: str) -> dict:
    """
    Pone en cuarentena un comando que no es lectura pura para aprobacion humana en el dashboard.

    El nivel de riesgo lo determina el Policy Engine y se inyecta como
    prefijo en el rationale (`[NIVEL] ...`) para que el front lo muestre
    al humano con un codigo de color.

    Args:
        device: ID del dispositivo objetivo.
        mitigation_command: Comando Bash a ejecutar tras aprobacion.
        rationale: Justificacion para el humano de por que se debe ejecutar.
    """
    try:
        # Sanitizar: eliminar comentarios de bash al final del comando (ej. "# (Comando inferido)")
        mitigation_command = re.sub(r'\s*#\s*\(.*?\)\s*$', '', mitigation_command).strip()

        cls = policy_engine.classify(mitigation_command)
        # Si la razon viene ya prefijada por execute_diagnostic_command no
        # duplicamos el tag.
        if rationale.lstrip().startswith("[" + cls.level.label() + "]"):
            decorated_rationale = rationale
        else:
            decorated_rationale = f"[{cls.level.label()}] {rationale}"

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
                """, (mitigation_command, decorated_rationale,
                      f"Requiere Aprobacion: {mitigation_command}",
                      f"\nRequiere Aprobacion: {mitigation_command}", device))
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

        policy_engine.audit(
            event_type="QUARANTINE",
            device=device,
            command=mitigation_command,
            classification=cls,
            decision_reason=rationale,
        )

        logger.info(
            f"[AGENT] Mitigacion puesta en PENDING_APPROVAL para {device} "
            f"({cls.level.label()}): {mitigation_command}"
        )
        return {
            "status": "pending_approval",
            "risk_level": cls.level.label(),
            "message": (
                f"Comando en cuarentena ({cls.level.label()}). Se ha solicitado "
                f"aprobacion al administrador. No debes hacer nada mas sobre esta alerta."
            ),
        }
    except Exception as e:
        logger.error(f"[ERROR] Error en request_mitigation_approval: {e}")
        return {"status": "error", "message": str(e)}
