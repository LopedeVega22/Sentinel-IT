import os
import re
import yaml
import logging
import sqlite3
import time

from tools import policy_engine
from tools import signing
from tools.revert_commands import derive_revert_command

# Definir rutas absolutas basadas en la ubicación de este script
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CONFIG_PATH = os.path.join(BASE_DIR, 'config.yml')

try:
    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)
    # Plantilla "seguridad/{device}/comando" — {device} se reemplaza al publicar
    TOPIC_PUBLISH_COMANDO = config['mqtt']['topic_publish_comando']
    DB_PATH = os.path.join(BASE_DIR, config['database']['db_path'])
    _SIGNING_CFG = config.get('signing', {}) or {}
    _SIGNING_KEY_PATH = os.path.join(
        BASE_DIR,
        _SIGNING_CFG.get('private_key_path', 'certificados/sentinel_pi5_signing.key'),
    )
    _SIGNING_TTL = int(_SIGNING_CFG.get('ttl_seconds', signing.DEFAULT_TTL_SECONDS))
except Exception:
    TOPIC_PUBLISH_COMANDO = "seguridad/{device}/comando"
    DB_PATH = os.path.join(BASE_DIR, "soc_data.db")
    _SIGNING_KEY_PATH = os.path.join(BASE_DIR, "certificados", "sentinel_pi5_signing.key")
    _SIGNING_TTL = signing.DEFAULT_TTL_SECONDS

logger = logging.getLogger("CoordinatorSOC")

# Referencia global al cliente IoT, inyectada desde el coordinador principal
_iot_client = None

def init_iot_tools(iot_client):
    """
    Vincula el cliente MQTT activo y carga la clave privada Ed25519 con la que
    se firmaran todos los comandos enviados a los sensores.
    """
    global _iot_client
    _iot_client = iot_client
    try:
        signing.load_private_key(_SIGNING_KEY_PATH)
    except FileNotFoundError:
        logger.critical(
            f"[SIGN] No se encontro la clave privada en {_SIGNING_KEY_PATH}. "
            f"Genera el par con `python scripts/generate_signing_keys.py` antes de arrancar."
        )
        raise


def _publish_signed(device: str, payload: dict) -> None:
    """
    Publica un comando al sensor anadiendo firma Ed25519 + iat/exp/nonce.
    Centraliza el cableado para que execute_diagnostic_command y
    _auto_execute_low compartan exactamente el mismo formato.
    """
    response_topic = TOPIC_PUBLISH_COMANDO.replace("{device}", device)
    signed_payload = signing.sign_payload(payload, ttl_seconds=_SIGNING_TTL)
    _iot_client.publish(response_topic, signed_payload)

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
        action_payload = {
            "accion": "ejecutar_comando",
            "comando": command,
            "motivo": reason
        }
        _publish_signed(device, action_payload)
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

def request_mitigation_approval(
    device: str,
    mitigation_command: str,
    rationale: str,
    revert_command: str = "",
) -> dict:
    """
    Propone un comando de mitigacion. El Policy Engine decide el flujo segun el riesgo:

      * SAFE_READ -> auto-ejecucion (publica directo). El comando queda
        registrado con status='APPROVED' y pending_command relleno.
      * LOW / HIGH / CRITICAL -> queda en cuarentena (status='PENDING') con el
        rationale prefijado por nivel para que el dashboard muestre el banner
        y, en CRITICAL, exija checkbox de confirmacion.

    Args:
        device: ID del dispositivo objetivo.
        mitigation_command: Comando Bash a ejecutar.
        rationale: Justificacion para el humano (o registro de auditoria).
        revert_command: Comando Bash que revierte la mitigacion, si el agente
            puede proponerlo de forma concreta.
    """
    try:
        # Sanitizar: eliminar comentarios de bash al final del comando (ej. "# (Comando inferido)")
        mitigation_command = re.sub(r'\s*#\s*\(.*?\)\s*$', '', mitigation_command).strip()
        revert_command = re.sub(r'\s*#\s*\(.*?\)\s*$', '', revert_command or '').strip()
        if revert_command.lstrip().startswith('#'):
            revert_command = ''
        if not revert_command:
            revert_command = derive_revert_command(mitigation_command)

        cls = policy_engine.classify(mitigation_command)
        auto_execute = cls.level == policy_engine.RiskLevel.SAFE_READ

        # Si la razon viene ya prefijada por execute_diagnostic_command no
        # duplicamos el tag.
        if rationale.lstrip().startswith("[" + cls.level.label() + "]"):
            decorated_rationale = rationale
        else:
            decorated_rationale = f"[{cls.level.label()}] {rationale}"

        if auto_execute:
            return _auto_execute_low(device, mitigation_command, revert_command, decorated_rationale, cls)
        return _quarantine_for_hitl(device, mitigation_command, revert_command, decorated_rationale, cls, rationale)

    except Exception as e:
        logger.error(f"[ERROR] Error en request_mitigation_approval: {e}")
        return {"status": "error", "message": str(e)}


def _auto_execute_low(device: str, command: str, revert_command: str, decorated_rationale: str,
                      cls: 'policy_engine.Classification') -> dict:
    """Publica un comando SAFE_READ directo y deja trazabilidad en la fila."""
    if _iot_client is None:
        logger.error("[ERROR] Cliente IoT no inicializado.")
        return {"status": "error", "message": "IoT Client not initialized"}

    action_payload = {
        "accion": "ejecutar_comando",
        "comando": command,
        "motivo": f"Auto-ejecucion {cls.level.label()}",
    }
    _publish_signed(device, action_payload)

    # Marcar la fila mas reciente del dispositivo como APPROVED para que el
    # dashboard ofrezca el boton REVERTIR (mismo flujo que tras aprobacion HITL).
    for attempt in range(5):
        conn = None
        try:
            conn = sqlite3.connect(DB_PATH, timeout=15.0, check_same_thread=False)
            conn.execute('PRAGMA journal_mode=WAL;')
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE logs
                SET status = 'APPROVED',
                    pending_command = ?,
                    revert_command = ?,
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
            """, (command, revert_command, decorated_rationale,
                  f"Auto-ejecutado [{cls.level.label()}]: {command}",
                  f"\nAuto-ejecutado [{cls.level.label()}]: {command}", device))
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
        event_type="AUTO_DISPATCH",
        device=device,
        command=command,
        classification=cls,
        decision_reason=f"Auto-ejecucion por nivel {cls.level.label()}",
    )

    logger.info(
        f"[AGENT] Mitigacion auto-ejecutada ({cls.level.label()}) en {device}: {command}"
    )
    return {
        "status": "auto_executed",
        "risk_level": cls.level.label(),
        "target": device,
        "command": command,
        "revert_command": revert_command,
        "message": (
            f"Comando ejecutado automaticamente ({cls.level.label()}). "
            f"Puede revertirse desde el dashboard si fuera necesario."
        ),
    }


def _quarantine_for_hitl(device: str, command: str, revert_command: str, decorated_rationale: str,
                         cls: 'policy_engine.Classification', raw_rationale: str) -> dict:
    """Deja un comando HIGH/CRITICAL en estado PENDING a la espera de revision humana."""
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
                    revert_command = ?,
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
            """, (command, revert_command, decorated_rationale,
                  f"Requiere Revision: {command}",
                  f"\nRequiere Revision: {command}", device))
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
        command=command,
        classification=cls,
        decision_reason=raw_rationale,
    )

    logger.info(
        f"[AGENT] Mitigacion en revision humana ({cls.level.label()}) para "
        f"{device}: {command}"
    )
    return {
        "status": "pending_approval",
        "risk_level": cls.level.label(),
        "message": (
            f"Comando en revision humana ({cls.level.label()}). "
            f"No debes hacer nada mas sobre esta alerta."
        ),
    }

def consultar_manual_mitigacion(query: str) -> str:
    """
    Consulta la base de conocimiento local de mitigaciones recomendadas.
    Usa esta herramienta SIEMPRE que necesites buscar el comando Bash exacto 
    y la explicacion para un tipo de ataque especifico.

    Args:
        query: Palabras clave del ataque (ej. 'XSS', 'SSH', 'SQLi', 'Web').
    """
    try:
        import json
        rec_path = os.path.join(BASE_DIR, 'src', 'recommendations.json')
        with open(rec_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        recs = data.get("recomendaciones_mitigacion", [])
        
        query_lower = query.lower()
        matches = []
        for item in recs:
            if query_lower in item.get("ataque", "").lower() or query_lower in item.get("explicacion", "").lower():
                matches.append(item)
        
        # Si no hay match exacto, devolvemos todo el manual para que el LLM decida
        if not matches:
            matches = recs
            
        res_str = []
        for m in matches:
            cmd = m.get("comando", "")
            res_str.append(f"- Ataque: {m.get('ataque', '')}\n  Comando: {cmd}\n  Explicacion: {m.get('explicacion', '')}")
            
        return "\n\n".join(res_str)
    except Exception as e:
        logger.error(f"[ERROR] consultando manual de mitigacion: {e}")
        return f"Error consultando manual: {str(e)}"
