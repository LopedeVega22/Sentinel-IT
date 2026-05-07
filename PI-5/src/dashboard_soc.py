import os
import sqlite3
import yaml
import logging
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import check_password_hash, generate_password_hash
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from aws_connector import AWSMqttClient

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
try:
    ENDPOINT = config['aws']['endpoint']
    CLIENT_ID = "Dashboard-SOC-Pi5"
    CERT_PATH = os.path.join(BASE_DIR, config['aws']['cert_path'].replace('./', ''))
    KEY_PATH = os.path.join(BASE_DIR, config['aws']['key_path'].replace('./', ''))
    ROOT_CA = os.path.join(BASE_DIR, config['aws']['root_ca'].replace('./', ''))
    TOPIC_ACTIONS_BASE = config['mqtt']['topic_actions_base']
    
    mqtt_client = AWSMqttClient(
        endpoint=ENDPOINT,
        cert_path=CERT_PATH,
        key_path=KEY_PATH,
        root_ca_path=ROOT_CA,
        client_id=CLIENT_ID
    )
    mqtt_client.connect()
    logger.info("[INFO] MQTT dashboard connection established.")
except Exception as e:
    mqtt_init_error = str(e)
    logger.warning(f"[WARNING] MQTT not available: {e}")

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
        
        c.execute("SELECT COUNT(*) FROM logs WHERE status = 'APPROVED'")
        blocks = c.fetchone()[0]
        
        c.execute("SELECT timestamp FROM logs ORDER BY id DESC LIMIT 1")
        last = c.fetchone()
        last_time = last[0] if last else "No activity"
        
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
    """Generates a graph topology of attackers, sensors, and the coordinator from recent logs."""
    try:
        conn = _get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT dispositivo, ip_origen, COUNT(*) as weight
            FROM logs
            WHERE ip_origen IS NOT NULL AND dispositivo IS NOT NULL
            GROUP BY dispositivo, ip_origen
            ORDER BY weight DESC
            LIMIT 15
        """)
        rows = c.fetchall()
        conn.close()

        nodes = []
        links = []
        
        # Base node: PI-5 Coordinator (Category 0)
        nodes.append({"id": "PI-5", "name": "PI-5 Coordinator", "category": 0, "symbolSize": 45, "itemStyle": {"color": "#3b82f6", "shadowBlur": 15, "shadowColor": "#3b82f6"}})
        
        devices = set()
        attackers = set()
        
        for device, ip, weight in rows:
            if device not in devices:
                devices.add(device)
                nodes.append({"id": device, "name": device, "category": 1, "symbolSize": 30, "itemStyle": {"color": "#10b981", "shadowBlur": 10, "shadowColor": "#10b981"}})
                # Link device to coordinator
                links.append({"source": device, "target": "PI-5", "lineStyle": {"width": 2, "color": "rgba(16, 185, 129, 0.4)", "type": "dashed"}})
            
            if ip not in attackers:
                attackers.add(ip)
                nodes.append({"id": ip, "name": ip, "category": 2, "symbolSize": 20, "itemStyle": {"color": "#ef4444"}})
            
            # Link attacker to device
            links.append({"source": ip, "target": device, "value": weight, "lineStyle": {"width": max(1.5, min(weight/2, 4)), "color": "rgba(239, 68, 68, 0.6)", "curveness": 0.2}})
            
        # If no logs, just show coordinator
        if not rows:
            nodes.append({"id": "PI-4 (Demo)", "name": "PI-4 Sensor", "category": 1, "symbolSize": 30, "itemStyle": {"color": "#10b981"}})
            links.append({"source": "PI-4 (Demo)", "target": "PI-5", "lineStyle": {"width": 2, "color": "rgba(16, 185, 129, 0.4)", "type": "dashed"}})
            
        return {"nodes": nodes, "links": links}
    except Exception as e:
        logger.error(f"[ERROR] Topology query failed: {e}")
        return {"nodes": [{"id": "PI-5", "name": "PI-5 Coordinator", "category": 0, "symbolSize": 45}], "links": []}

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

import socket
from datetime import datetime

def get_sys_info():
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory().percent
        
        # Uptime
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        now = datetime.now()
        uptime_diff = now - boot_time
        days, remainder = divmod(uptime_diff.total_seconds(), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, _ = divmod(remainder, 60)
        uptime_str = f"{int(days)}d {int(hours)}h {int(minutes)}m"
        
        # Local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_local = s.getsockname()[0]
        s.close()
    except Exception:
        cpu = "N/A"
        ram = "N/A"
        uptime_str = "Error"
        ip_local = "N/A"
        
    return {
        "cpu": cpu,
        "ram": ram,
        "uptime": uptime_str,
        "ip_local": ip_local
    }

@app.route('/')
@auth.login_required
def index():
    data = get_logs()
    total, criticals, blocks, last_seen = get_db_stats()
    vector_stats = get_vector_stats()
    unique_vectors = get_unique_vectors()
    threat_level = get_threat_level()
    mqtt_status = "connected" if mqtt_client else "disconnected"
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
    mqtt_status = "connected" if mqtt_client else "disconnected"
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
    if not mqtt_client or getattr(mqtt_client, 'connection', None) is None:
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
            
            # Send the command to the IoT Edge device
            topic = f"{TOPIC_ACTIONS_BASE}{device}"
            action_payload = {
                "accion": "ejecutar_comando",
                "comando": final_command,
                "motivo": f"Manual approval from dashboard for IP {blocked_ip}"
            }
            logger.info(f"[INFO] Sending approved mitigation to {topic}: {final_command}")
            mqtt_client.publish(topic, action_payload)
            
            new_action = str(action_taken) + " [EJECUTADO]"
            c.execute("UPDATE logs SET status = 'APPROVED', accion_tomada = ? WHERE id = ?", (new_action, log_id))
            message = "Comando ejecutado exitosamente."
        
        elif action == 'reject':
            new_action = str(action_taken) + " [RECHAZADO]"
            c.execute("UPDATE logs SET status = 'REJECTED', accion_tomada = ? WHERE id = ?", (new_action, log_id))
            message = "Mitigacion rechazada."
            
        else:
            conn.close()
            return jsonify({"status": "error", "message": "Invalid action"}), 400
            
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": message})
        
    except Exception as e:
        logger.error(f"[ERROR] Failed to process mitigation approval: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/revert/<int:log_id>', methods=['POST'])
@auth.login_required
def revert_action(log_id):
    """Reverts a block action by sending the inverse iptables command via MQTT."""
    if not mqtt_client or getattr(mqtt_client, 'connection', None) is None:
        logger.error(f"[ERROR] No active MQTT connection for revert: {mqtt_init_error}")
        return jsonify({"status": "error", "message": "MQTT client not connected"}), 500
        
    try:
        conn = _get_connection()
        c = conn.cursor()
        c.execute("SELECT ip_origen, accion_tomada, dispositivo, pending_command, status FROM logs WHERE id = ?", (log_id,))
        row = c.fetchone()
        
        if not row:
            conn.close()
            return jsonify({"status": "error", "message": "Log not found"}), 404
            
        blocked_ip, action_taken, device, pending_command, status = row
        
        if status != 'APPROVED' or not pending_command or pending_command.strip() == '':
            conn.close()
            return jsonify({"status": "error", "message": "No approved command to revert"}), 400
            
        # Derive inverse command dynamically from the stored pending_command
        revert_command = pending_command.replace(' -A ', ' -D ').replace(' --append ', ' --delete ')
        if revert_command == pending_command:
            # Fallback: if no iptables pattern matched, prepend a comment for manual review
            revert_command = f"# REVERT: {pending_command}"
        reason = f"Manual revert from dashboard for IP {blocked_ip}"
        
        topic = f"{TOPIC_ACTIONS_BASE}{device}"
        action_payload = {
            "accion": "ejecutar_comando",
            "comando": revert_command,
            "motivo": reason
        }
        
        logger.info(f"[INFO] Sending revert to {topic}: {revert_command}")
        mqtt_client.publish(topic, action_payload)
        
        new_action = str(action_taken) + " [REVERTIDO]"
        c.execute("UPDATE logs SET accion_tomada = ?, status = 'REVERTED' WHERE id = ?", (new_action, log_id))
        conn.commit()
        conn.close()
        
        return redirect(url_for('index'))
        
    except Exception as e:
        logger.error(f"[ERROR] Failed to revert action {log_id}: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    logger.info(f"[INFO] Dashboard SOC started on {WEB_HOST}:{WEB_PORT}")
    app.run(host=WEB_HOST, port=WEB_PORT, debug=False)