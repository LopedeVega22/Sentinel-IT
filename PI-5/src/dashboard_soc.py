import os
import sqlite3
import time
import yaml
import logging
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import check_password_hash, generate_password_hash
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from aws_connector import AWSMqttClient
from tools import policy_engine
from tools import signing

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')), '.env'))
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CONFIG_PATH = os.path.join(BASE_DIR, 'config.yml')

# Load settings from YAML config
with open(CONFIG_PATH, "r") as f:
    config = yaml.safe_load(f)

DB_PATH = os.path.join(BASE_DIR, config['database']['db_path'])
WEB_PORT = config['web']['port']
WEB_HOST = config['web']['host']

# Dashboard web panel logging configuration
logger = logging.getLogger("DashboardSOC")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler("/tmp/dashboard_soc.log", maxBytes=5242880, backupCount=3)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.addHandler(logging.StreamHandler())

# MQTT client initialization for remote actions
mqtt_client = None
mqtt_init_error = None
TOPIC_PUBLISH_COMANDO = config['mqtt']['topic_publish_comando']

def get_mqtt_client(max_attempts=4, initial_delay=1.0):
    """
    Devuelve un cliente MQTT vivo. Si la conexion previa cayo o nunca se
    establecio, reintenta con backoff exponencial. La red del entorno
    actual sufre fallos transitorios de DNS (AWS_IO_DNS_QUERY_FAILED) y un
    unico intento no es suficiente: el operador veria un 500 en el HITL.

    El budget total es deliberadamente acotado (~7-15s con 4 intentos) para
    que el endpoint HTTP no se cuelgue indefinidamente.
    """
    global mqtt_client, mqtt_init_error
    if mqtt_client is not None and mqtt_client.is_alive():
        return mqtt_client

    # Si el cliente existe pero está muerto (zombie), lo desconectamos
    # limpiamente para liberar recursos antes de reconectar.
    if mqtt_client is not None:
        logger.warning("[WARNING] MQTT dashboard client is zombie — disconnecting before reconnect.")
        try:
            mqtt_client.disconnect()
        except Exception:
            pass
        mqtt_client = None

    ENDPOINT = config['aws']['endpoint']
    CLIENT_ID = "Dashboard-SOC-Pi5"
    CERT_PATH = os.path.join(BASE_DIR, config['aws']['cert_path'].replace('./', ''))
    KEY_PATH = os.path.join(BASE_DIR, config['aws']['key_path'].replace('./', ''))
    ROOT_CA = os.path.join(BASE_DIR, config['aws']['root_ca'].replace('./', ''))

    signing_key_cfg = config.get('signing', {}) or {}
    SIGNING_KEY_PATH = os.path.join(
        BASE_DIR,
        signing_key_cfg.get('private_key_path', 'certificados/sentinel_pi5_signing.key')
    )
    try:
        signing.load_private_key(SIGNING_KEY_PATH)
    except Exception as e:
        mqtt_init_error = f"signing init failed: {e}"
        logger.error(f"[ERROR] {mqtt_init_error}")
        mqtt_client = None
        return None

    delay = initial_delay
    last_err = None
    for attempt in range(1, max_attempts + 1):
        try:
            candidate = AWSMqttClient(
                endpoint=ENDPOINT,
                cert_path=CERT_PATH,
                key_path=KEY_PATH,
                root_ca_path=ROOT_CA,
                client_id=CLIENT_ID
            )
            candidate.connect()
            mqtt_client = candidate
            mqtt_init_error = None
            logger.info(f"[INFO] MQTT dashboard connection established (attempt {attempt}).")
            return mqtt_client
        except Exception as e:
            last_err = e
            logger.warning(
                f"[WARNING] MQTT connect attempt {attempt}/{max_attempts} failed: {e}"
            )
            if attempt < max_attempts:
                time.sleep(delay)
                delay = min(delay * 2, 8.0)

    mqtt_init_error = str(last_err)
    logger.error(f"[ERROR] MQTT dashboard connection failed after {max_attempts} attempts: {last_err}")
    mqtt_client = None
    return None

# Initial connection attempt (best effort, mas tolerante porque arranca en paralelo con DNS)
get_mqtt_client(max_attempts=6, initial_delay=2.0)

app = Flask(__name__)

# ---------------------------------------------------------------------------
# HTTP Basic Authentication
# Credentials are read from the .env file (DASHBOARD_USER / DASHBOARD_PASSWORD)
# ---------------------------------------------------------------------------
auth = HTTPBasicAuth()

_AUTH_USER = os.environ.get('DASHBOARD_USER', 'admin')
_AUTH_PASS_HASH = os.environ.get('DASHBOARD_PASSWORD_HASH', '')

# If no pre-hashed password exists, check for a plaintext env var and hash it at startup
if not _AUTH_PASS_HASH:
    _plain = os.environ.get('DASHBOARD_PASSWORD', '')
    if _plain:
        _AUTH_PASS_HASH = generate_password_hash(_plain)
    else:
        # Fallback: if no credentials configured, log a warning
        logger.warning("[WARNING] No DASHBOARD_PASSWORD set in .env — dashboard is NOT protected!")

@auth.verify_password
def verify_password(username, password):
    if not _AUTH_PASS_HASH:
        # No password configured — allow access (dev mode)
        return True
    if username == _AUTH_USER and check_password_hash(_AUTH_PASS_HASH, password):
        return username
    return None

# ---------------------------------------------------------------------------
# Database query helpers
# ---------------------------------------------------------------------------

def _get_connection():
    """Returns a read-only SQLite connection with WAL mode."""
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.execute('PRAGMA journal_mode=WAL;')
    return conn


def get_db_stats():
    """Retrieves core security metrics from SQLite."""
    try:
        conn = _get_connection()
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) FROM logs")
        total = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM logs WHERE nivel_gravedad LIKE '%Critic%' OR nivel_gravedad LIKE '%Crític%'")
        criticals = c.fetchone()[0]
        
        try:
            c.execute("SELECT COUNT(*) FROM logs WHERE status = 'APPROVED'")
            blocks = c.fetchone()[0]
        except sqlite3.OperationalError:
            c.execute("SELECT COUNT(*) FROM logs WHERE accion_tomada LIKE '%[EJECUTADO]%' OR accion_tomada LIKE '%Bloqueo%'")
            blocks = c.fetchone()[0]
        
        try:
            c.execute("SELECT timestamp FROM logs ORDER BY id DESC LIMIT 1")
            last = c.fetchone()
            last_time = last[0] if last else "No activity"
        except sqlite3.OperationalError:
            last_time = "No activity"
        
        conn.close()
        return total, criticals, blocks, last_time
    except Exception:
        return 0, 0, 0, "Error DB"


def get_logs():
    """Retrieves the latest registered incidents."""
    try:
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM logs ORDER BY id DESC LIMIT 20")
        data = cursor.fetchall()
        conn.close()
        return data
    except Exception as e:
        logger.error(f"[ERROR] Log query failed: {e}")
        return []


def get_vector_stats():
    """Retrieves attack vector distribution grouped by service column."""
    try:
        conn = _get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT servicio, COUNT(*) as cnt 
            FROM logs 
            WHERE servicio IS NOT NULL AND servicio != ''
            GROUP BY servicio 
            ORDER BY cnt DESC
            LIMIT 8
        """)
        rows = c.fetchall()
        
        c.execute("SELECT COUNT(*) FROM logs WHERE servicio IS NOT NULL AND servicio != ''")
        total = c.fetchone()[0]
        conn.close()
        
        if total == 0:
            return []
        
        result = []
        for name, count in rows:
            pct = round((count / total) * 100, 1)
            result.append({"name": name, "count": count, "percentage": pct})
        return result
    except Exception:
        return []


def get_unique_vectors():
    """Counts distinct attack vectors detected."""
    try:
        conn = _get_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(DISTINCT servicio) FROM logs WHERE servicio IS NOT NULL AND servicio != ''")
        count = c.fetchone()[0]
        conn.close()
        return count
    except Exception:
        return 0


def get_threat_level():
    """
    Calculates a threat index from 0 to 100.
    Formula: ((criticals * 3) + (highs * 2) + mediums) / total * 25, capped at 100.
    This heuristic weights critical events heavily to reflect real operational risk.
    """
    try:
        conn = _get_connection()
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) FROM logs")
        total = c.fetchone()[0]
        if total == 0:
            conn.close()
            return 0
        
        c.execute("SELECT COUNT(*) FROM logs WHERE nivel_gravedad LIKE '%Critic%' OR nivel_gravedad LIKE '%Crític%'")
        criticals = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM logs WHERE nivel_gravedad LIKE '%Alta%' OR nivel_gravedad LIKE '%High%'")
        highs = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM logs WHERE nivel_gravedad LIKE '%Media%' OR nivel_gravedad LIKE '%Medium%'")
        mediums = c.fetchone()[0]
        
        conn.close()
        
        # Threat level heuristic: weighted severity ratio, scaled to 0-100
        level = ((criticals * 3) + (highs * 2) + mediums) / total * 25
        return min(round(level), 100)
    except Exception:
        return 0


def _serialize_logs(data):
    """Converts log tuples to JSON-serializable dicts."""
    result = []
    for row in data:
        # Extraemos con fallback seguro en caso de schemas viejos
        result.append({
            "id": row[0],
            "device": row[1],
            "service": row[2],
            "raw_log": row[3],
            "source_ip": row[4],
            "severity": row[5],
            "verdict": row[6],
            "action": row[7],
            "mitigation_status": row[8] if len(row) > 8 else "",
            "status": row[9] if len(row) > 9 else "LOGGED",
            "pending_command": row[10] if len(row) > 10 else "",
            "rationale": row[11] if len(row) > 11 else "",
            "timestamp": row[12] if len(row) > 12 else (row[9] if len(row) > 9 else "")
        })
    return result

def get_topology_data():
    """
    Generates a fixed-position hub-spoke topology for the Radar Command Center.
    - PI-5 Coordinator: always at center (300, 200)
    - PI-4 Sensor: consolidated single node at left (100, 200)
    - Attackers: distributed in arc to the right of PI-5
    Returns nodes, links, flow_lines (for particle animation), and stats.
    """
    import math

    # Fixed coordinates for the chart (600x400 canvas)
    PI5_X, PI5_Y = 300, 200
    PI4_X, PI4_Y = 100, 200
    ARC_RADIUS = 160  # Distance from PI-5 for attacker nodes

    try:
        conn = _get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT ip_origen, COUNT(*) as weight
            FROM logs
            WHERE ip_origen IS NOT NULL AND dispositivo IS NOT NULL
            GROUP BY ip_origen
            ORDER BY weight DESC
            LIMIT 10
        """)
        rows = c.fetchall()
        conn.close()

        nodes = []
        links = []
        flow_lines = []
        total_hits = 0

        # --- PI-5 Coordinator (hub) ---
        nodes.append({
            "id": "PI-5", "name": "PI-5 Coordinator",
            "x": PI5_X, "y": PI5_Y,
            "symbolSize": 50, "fixed": True,
            "itemStyle": {
                "color": "#3b82f6",
                "shadowBlur": 25,
                "shadowColor": "rgba(59,130,246,0.6)"
            },
            "label": {"show": True, "position": "bottom", "color": "#94a3b8",
                      "fontSize": 11, "fontWeight": 600,
                      "formatter": "PI-5\nCoordinator"}
        })

        # --- PI-4 Sensor (consolidated single node) ---
        nodes.append({
            "id": "PI-4", "name": "PI-4 Sensor",
            "x": PI4_X, "y": PI4_Y,
            "symbolSize": 35, "fixed": True,
            "itemStyle": {
                "color": "#10b981",
                "shadowBlur": 15,
                "shadowColor": "rgba(16,185,129,0.5)"
            },
            "label": {"show": True, "position": "bottom", "color": "#94a3b8",
                      "fontSize": 11, "fontWeight": 600,
                      "formatter": "PI-4\nSensor"}
        })

        # --- Link PI-4 ↔ PI-5 (MQTT data flow) ---
        links.append({
            "source": "PI-4", "target": "PI-5",
            "lineStyle": {
                "width": 2, "color": "rgba(6,182,212,0.3)",
                "type": "dashed", "curveness": 0
            }
        })
        flow_lines.append({
            "coords": [[PI4_X, PI4_Y], [PI5_X, PI5_Y]],
            "type": "mqtt"
        })

        # --- Attacker nodes from logs (arc to the right of PI-5) ---
        attacker_ips = []
        for ip, weight in rows:
            attacker_ips.append((ip, weight))
            total_hits += weight

        num_attackers = len(attacker_ips)
        if num_attackers > 0:
            angle_step = math.pi / (num_attackers + 1)
            for i, (ip, weight) in enumerate(attacker_ips):
                angle = -math.pi / 2 + angle_step * (i + 1)
                ax = PI5_X + ARC_RADIUS * math.cos(angle)
                ay = PI5_Y + ARC_RADIUS * math.sin(angle)

                # Node size proportional to hit count (min 14, max 28)
                sz = max(14, min(int(12 + weight * 2), 28))

                nodes.append({
                    "id": ip, "name": ip,
                    "x": round(ax, 1), "y": round(ay, 1),
                    "symbolSize": sz, "fixed": True,
                    "itemStyle": {
                        "color": "#ef4444",
                        "shadowBlur": 8,
                        "shadowColor": "rgba(239,68,68,0.4)"
                    },
                    "label": {"show": True, "position": "right",
                              "color": "#f87171", "fontSize": 9,
                              "formatter": ip}
                })

                # Link: attacker → PI-4 (attack traffic)
                link_w = max(1.5, min(weight / 2, 4))
                links.append({
                    "source": ip, "target": "PI-4",
                    "value": weight,
                    "lineStyle": {
                        "width": link_w,
                        "color": "rgba(239,68,68,0.35)",
                        "curveness": 0.15
                    }
                })
                flow_lines.append({
                    "coords": [[round(ax, 1), round(ay, 1)], [PI4_X, PI4_Y]],
                    "type": "attack"
                })

        return {
            "nodes": nodes,
            "links": links,
            "flow_lines": flow_lines,
            "stats": {
                "device_count": 1,  # PI-4 is always the single sensor
                "attacker_count": num_attackers,
                "total_hits": total_hits
            }
        }
    except Exception as e:
        logger.error(f"[ERROR] Topology query failed: {e}")
        return {
            "nodes": [
                {"id": "PI-5", "name": "PI-5 Coordinator", "x": PI5_X, "y": PI5_Y,
                 "symbolSize": 50, "fixed": True,
                 "itemStyle": {"color": "#3b82f6", "shadowBlur": 25, "shadowColor": "rgba(59,130,246,0.6)"},
                 "label": {"show": True, "position": "bottom", "color": "#94a3b8", "fontSize": 11, "fontWeight": 600, "formatter": "PI-5\nCoordinator"}},
                {"id": "PI-4", "name": "PI-4 Sensor", "x": PI4_X, "y": PI4_Y,
                 "symbolSize": 35, "fixed": True,
                 "itemStyle": {"color": "#10b981", "shadowBlur": 15, "shadowColor": "rgba(16,185,129,0.5)"},
                 "label": {"show": True, "position": "bottom", "color": "#94a3b8", "fontSize": 11, "fontWeight": 600, "formatter": "PI-4\nSensor"}}
            ],
            "links": [{"source": "PI-4", "target": "PI-5", "lineStyle": {"width": 2, "color": "rgba(6,182,212,0.3)", "type": "dashed"}}],
            "flow_lines": [{"coords": [[PI4_X, PI4_Y], [PI5_X, PI5_Y]], "type": "mqtt"}],
            "stats": {"device_count": 1, "attacker_count": 0, "total_hits": 0}
        }

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

import socket
from datetime import datetime

def get_sys_info():
    """Retrieves system metrics with independent fallbacks per metric."""
    # CPU
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=0.1)
    except Exception:
        cpu = "N/A"

    # RAM
    try:
        import psutil
        ram = psutil.virtual_memory().percent
    except Exception:
        ram = "N/A"

    # Uptime
    try:
        import psutil
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        now = datetime.now()
        uptime_diff = now - boot_time
        days, remainder = divmod(uptime_diff.total_seconds(), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, _ = divmod(remainder, 60)
        uptime_str = f"{int(days)}d {int(hours)}h {int(minutes)}m"
    except Exception:
        uptime_str = "N/A"

    # Local IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(2)
        s.connect(("8.8.8.8", 80))
        ip_local = s.getsockname()[0]
        s.close()
    except Exception:
        ip_local = "N/A"

    # AI Model name
    ai_model = os.environ.get("AI_MODEL", "N/A")

    return {
        "cpu": cpu,
        "ram": ram,
        "uptime": uptime_str,
        "ip_local": ip_local,
        "ai_model": ai_model
    }


@app.route('/')
@auth.login_required
def index():
    data = get_logs()
    total, criticals, blocks, last_seen = get_db_stats()
    vector_stats = get_vector_stats()
    unique_vectors = get_unique_vectors()
    threat_level = get_threat_level()
    mqtt_status = "connected" if (mqtt_client and mqtt_client.is_alive()) else "disconnected"
    sys_info = get_sys_info()
    topology_data = get_topology_data()
    
    return render_template('index.html', 
                          data=data, 
                          total_logs=total, 
                          total_criticals=criticals,
                          total_blocks=blocks,
                          last_seen=last_seen,
                          vector_stats=vector_stats,
                          unique_vectors=unique_vectors,
                          threat_level=threat_level,
                          mqtt_status=mqtt_status,
                          sys_info=sys_info,
                          topology=topology_data)


@app.route('/api/data')
@auth.login_required
def api_data():
    """JSON endpoint for AJAX auto-refresh. Returns all dashboard data."""
    data = get_logs()
    total, criticals, blocks, last_seen = get_db_stats()
    vector_stats = get_vector_stats()
    unique_vectors = get_unique_vectors()
    threat_level = get_threat_level()
    mqtt_status = "connected" if (mqtt_client and mqtt_client.is_alive()) else "disconnected"
    sys_info = get_sys_info()
    topology_data = get_topology_data()
    
    return jsonify({
        "logs": _serialize_logs(data),
        "total_logs": total,
        "total_criticals": criticals,
        "total_blocks": blocks,
        "last_seen": last_seen,
        "vector_stats": vector_stats,
        "unique_vectors": unique_vectors,
        "threat_level": threat_level,
        "mqtt_status": mqtt_status,
        "sys_info": sys_info,
        "topology": topology_data
    })


@app.route('/api/mitigate/approve', methods=['POST'])
@auth.login_required
def approve_mitigation():
    """Endpoint to approve, edit, or reject a pending mitigation command."""
    get_mqtt_client()
    if not mqtt_client or not mqtt_client.is_alive():
        return jsonify({"status": "error", "message": "MQTT client not connected"}), 500
        
    try:
        data = request.json
        log_id = data.get('log_id')
        action = data.get('action') # 'approve' or 'reject'
        final_command = data.get('final_command', '')

        if not log_id or not action:
            return jsonify({"status": "error", "message": "Missing parameters"}), 400

        conn = _get_connection()
        c = conn.cursor()
        c.execute("SELECT dispositivo, ip_origen, accion_tomada FROM logs WHERE id = ?", (log_id,))
        row = c.fetchone()
        
        if not row:
            conn.close()
            return jsonify({"status": "error", "message": "Log not found"}), 404
            
        device, blocked_ip, action_taken = row
        
        if action == 'approve':
            if not final_command:
                conn.close()
                return jsonify({"status": "error", "message": "No command provided for approval"}), 400

            # Re-clasificacion obligatoria tras edicion humana: el comando que
            # se ejecuta no es necesariamente el que propuso el agente IA.
            classification = policy_engine.classify(final_command)
            confirm_critical = bool(data.get('confirm_critical', False))

            if classification.level == policy_engine.RiskLevel.CRITICAL and not confirm_critical:
                conn.close()
                policy_engine.audit(
                    event_type="REJECT_CRITICAL_UNCONFIRMED",
                    device=device,
                    command=final_command,
                    classification=classification,
                    decision_reason="Falta confirm_critical para nivel CRITICAL",
                    related_log_id=log_id,
                )
                return jsonify({
                    "status": "needs_confirmation",
                    "risk_level": classification.level.label(),
                    "reasons": classification.reasons,
                    "message": (
                        "El comando editado se ha clasificado como CRITICAL. "
                        "Marque la confirmacion de doble riesgo para ejecutarlo."
                    ),
                }), 400

            # Send the command to the IoT Edge device
            topic = TOPIC_PUBLISH_COMANDO.replace("{device}", device)
            action_payload = {
                "accion": "ejecutar_comando",
                "comando": final_command,
                "motivo": f"Manual approval from dashboard for IP {blocked_ip}"
            }
            logger.info(
                f"[INFO] Sending approved mitigation ({classification.level.label()}) "
                f"to {topic}: {final_command}"
            )
            try:
                signed_payload = signing.sign_payload(action_payload)
                mqtt_client.publish(topic, signed_payload, wait_for_ack=True)
            except Exception as pub_err:
                logger.error(f"[ERROR] Publish HITL fallo, no se actualiza DB: {pub_err}")
                conn.close()
                return jsonify({
                    "status": "error",
                    "message": f"MQTT publish failed: {pub_err}"
                }), 502
            policy_engine.audit(
                event_type="APPROVE",
                device=device,
                command=final_command,
                classification=classification,
                decision_reason=f"Aprobado por humano (IP {blocked_ip})",
                related_log_id=log_id,
            )

            new_action = str(action_taken) + " [EJECUTADO]"
            # NOTE: estado_mitigacion se resetea para que el front sepa que
            # estamos esperando la respuesta de PI-4 (round-trip). El
            # coordinador lo rellenara en cuanto llegue el /respuesta.
            c.execute(
                "UPDATE logs SET status = 'APPROVED', accion_tomada = ?, estado_mitigacion = NULL WHERE id = ?",
                (new_action, log_id),
            )
            message = f"Comando despachado ({classification.level.label()}). Esperando confirmacion de PI-4."

        elif action == 'reject':
            new_action = str(action_taken) + " [RECHAZADO]"
            c.execute("UPDATE logs SET status = 'REJECTED', accion_tomada = ? WHERE id = ?", (new_action, log_id))
            policy_engine.audit(
                event_type="REJECT",
                device=device,
                command=final_command or "",
                classification=None,
                decision_reason="Rechazado por humano",
                related_log_id=log_id,
            )
            message = "Mitigacion rechazada."
            
        else:
            conn.close()
            return jsonify({"status": "error", "message": "Invalid action"}), 400
            
        conn.commit()
        conn.close()
        # Para approve devolvemos 'dispatching' (el front debera consultar
        # /api/mitigate/status/<log_id> para saber si PI-4 ejecuto y con que
        # resultado). Para reject devolvemos 'success' directamente porque
        # no hay nada que verificar en el sensor.
        response_status = "dispatching" if action == "approve" else "success"
        return jsonify({
            "status": response_status,
            "message": message,
            "log_id": log_id,
        })

    except Exception as e:
        logger.error(f"[ERROR] Failed to process mitigation approval: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/mitigate/status/<int:log_id>', methods=['GET'])
@auth.login_required
def mitigation_status(log_id):
    """
    Devuelve el estado actual del round-trip HITL para una fila concreta.

    El front lo consulta cada segundo tras aprobar/revertir un comando
    hasta que estado_mitigacion deje de estar vacio (PI-4 ya respondio) o
    se cumpla el timeout del cliente.
    """
    try:
        conn = _get_connection()
        c = conn.cursor()
        c.execute(
            "SELECT status, accion_tomada, estado_mitigacion FROM logs WHERE id = ?",
            (log_id,),
        )
        row = c.fetchone()
        conn.close()
        if not row:
            return jsonify({"status": "error", "message": "Log not found"}), 404
        row_status, action_taken, mitigation_state = row
        has_feedback = bool(mitigation_state and str(mitigation_state).strip())
        if has_feedback:
            ms = str(mitigation_state)
            if "[FALLO]" in ms:
                phase = "failed"
            elif "[EXITO]" in ms:
                phase = "executed"
            else:
                phase = "feedback"
        else:
            phase = "awaiting_pi4"
        return jsonify({
            "log_id": log_id,
            "row_status": row_status,
            "phase": phase,
            "accion_tomada": action_taken,
            "estado_mitigacion": mitigation_state,
        })
    except Exception as e:
        logger.error(f"[ERROR] mitigation_status: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/revert/<int:log_id>', methods=['POST'])
@auth.login_required
def revert_action(log_id):
    """Reverts a block action by sending the inverse iptables command via MQTT."""
    get_mqtt_client()
    if not mqtt_client or not mqtt_client.is_alive():
        logger.error(f"[ERROR] No active MQTT connection for revert: {mqtt_init_error}")
        return jsonify({"status": "error", "message": "MQTT client not connected"}), 500
        
    try:
        conn = _get_connection()
        c = conn.cursor()
        try:
            c.execute("SELECT ip_origen, accion_tomada, dispositivo, pending_command, status FROM logs WHERE id = ?", (log_id,))
            row = c.fetchone()
        except sqlite3.OperationalError:
            c.execute("SELECT ip_origen, accion_tomada, dispositivo FROM logs WHERE id = ?", (log_id,))
            row_partial = c.fetchone()
            if row_partial:
                row = (row_partial[0], row_partial[1], row_partial[2], "", "LOGGED")
            else:
                row = None
        
        if not row:
            conn.close()
            return jsonify({"status": "error", "message": "Log not found"}), 404
            
        blocked_ip, action_taken, device, pending_command, status = row
        action_lower = str(action_taken).lower()
        is_blocked = (status == 'APPROVED') or ('bloque' in action_lower)
        
        if not is_blocked:
            conn.close()
            return jsonify({"status": "error", "message": "No block action to revert"}), 400
            
        # Derive inverse command dynamically from the stored pending_command
        if pending_command and pending_command.strip() != '':
            revert_command = pending_command.replace(' -A ', ' -D ').replace(' --append ', ' --delete ')
            if revert_command == pending_command:
                # Fallback: if no iptables pattern matched, prepend a comment for manual review
                revert_command = f"# REVERT: {pending_command}"
        else:
            revert_command = f"sudo iptables -D INPUT -s {blocked_ip} -j DROP"
            
        reason = f"Manual revert from dashboard for IP {blocked_ip}"

        topic = TOPIC_PUBLISH_COMANDO.replace("{device}", device)
        action_payload = {
            "accion": "ejecutar_comando",
            "comando": revert_command,
            "motivo": reason
        }
        
        revert_classification = policy_engine.classify(revert_command)
        logger.info(
            f"[INFO] Sending revert ({revert_classification.level.label()}) "
            f"to {topic}: {revert_command}"
        )
        try:
            signed_payload = signing.sign_payload(action_payload)
            mqtt_client.publish(topic, signed_payload, wait_for_ack=True)
        except Exception as pub_err:
            logger.error(f"[ERROR] Publish revert fallo: {pub_err}")
            conn.close()
            return jsonify({
                "status": "error",
                "message": f"MQTT publish failed: {pub_err}"
            }), 502
        policy_engine.audit(
            event_type="REVERT",
            device=device,
            command=revert_command,
            classification=revert_classification,
            decision_reason=reason,
            related_log_id=log_id,
        )

        new_action = str(action_taken) + " [REVERTIDO]"
        
        # Retry logic for DB updates to handle "database is locked"
        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                try:
                    # estado_mitigacion se limpia para que el front detecte el
                    # round-trip pendiente del revert (mismo mecanismo que approve).
                    c.execute(
                        "UPDATE logs SET accion_tomada = ?, status = 'REVERTED', estado_mitigacion = NULL WHERE id = ?",
                        (new_action, log_id),
                    )
                except sqlite3.OperationalError as op_err:
                    if "no such column" in str(op_err).lower():
                        c.execute("UPDATE logs SET accion_tomada = ? WHERE id = ?", (new_action, log_id))
                    else:
                        raise op_err
                conn.commit()
                break
            except sqlite3.OperationalError as e:
                if "locked" in str(e).lower() and attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    conn.rollback()
                    raise e
                    
        conn.close()

        return jsonify({
            "status": "dispatching",
            "message": "Revert despachado. Esperando confirmacion de PI-4.",
            "log_id": log_id,
        })
        
    except Exception as e:
        logger.error(f"[ERROR] Failed to revert action {log_id}: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    logger.info(f"[INFO] Dashboard SOC started on {WEB_HOST}:{WEB_PORT}")
    app.run(host=WEB_HOST, port=WEB_PORT, debug=False)