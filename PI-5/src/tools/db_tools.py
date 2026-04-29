import os
import sqlite3
import yaml
import logging
import time

# Calculo de rutas y carga de configuracion global
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CONFIG_PATH = os.path.join(BASE_DIR, 'config.yml')

try:
    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)
    DB_PATH = os.path.join(BASE_DIR, config['database']['db_path'])
    
    # Parametros de retencion para la limpieza automatica
    _RETENTION_MAX_DAYS = config.get('retention', {}).get('max_days', 30)
    _RETENTION_PURGE_ON_INSERT = config.get('retention', {}).get('purge_on_insert', True)
except Exception:
    DB_PATH = os.path.join(BASE_DIR, "soc_data.db")
    _RETENTION_MAX_DAYS = 30
    _RETENTION_PURGE_ON_INSERT = True

logger = logging.getLogger("CoordinatorSOC")

def rotate_old_logs() -> dict:
    """
    Elimina registros antiguos de baja prioridad (Solo Registro) segun la politica de retencion.
    """
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10.0, check_same_thread=False)
        conn.execute('PRAGMA journal_mode=WAL;')
        cursor = conn.cursor()

        # Conteo previo de registros a eliminar
        cursor.execute(
            """
            SELECT COUNT(*) FROM logs
            WHERE accion_tomada = 'Solo Registro'
              AND timestamp <= datetime('now', ?)
            """,
            (f"-{_RETENTION_MAX_DAYS} days",)
        )
        count_before = cursor.fetchone()[0]

        if count_before == 0:
            conn.close()
            return {"status": "ok", "purged": 0}

        # Ejecucion de la limpieza
        cursor.execute(
            """
            DELETE FROM logs
            WHERE accion_tomada = 'Solo Registro'
              AND timestamp <= datetime('now', ?)
            """,
            (f"-{_RETENTION_MAX_DAYS} days",)
        )
        conn.commit()
        conn.close()

        logger.info(f"[INFO] Limpieza de base de datos: {count_before} registros eliminados.")
        return {"status": "ok", "purged": count_before}

    except Exception as e:
        logger.error(f"[ERROR] Error en la rotacion de logs: {e}")
        return {"status": "error", "message": str(e)}

def register_alert(device: str, attack_vector: str, source_ip: str, severity: str, verdict: str, raw_log: str) -> dict:
    """
    Registra un incidente de seguridad en la base de datos local.
    
    Args:
        device: Nombre del dispositivo de origen.
        attack_vector: Etiqueta estricta del protocolo o servicio atacado (ej. SSH, NGINX-HTTP, MYSQL, PORT-SCAN).
        source_ip: IP asociada a la amenaza (MUST strictly be a valid IPv4/IPv6 address).
        severity: Nivel (Baja, Media, Alta, Critica).
        verdict: Resumen conciso del razonamiento logico del agente (chain-of-thought summary).
        raw_log: Texto original literal del log analizado.
    """
    if _RETENTION_PURGE_ON_INSERT:
        rotate_old_logs()

    # Politica de reintentos para manejar bloqueos en SQLite
    for attempt in range(5):
        conn = None
        try:
            conn = sqlite3.connect(DB_PATH, timeout=15.0, check_same_thread=False)
            conn.execute('PRAGMA journal_mode=WAL;')
            conn.execute('PRAGMA synchronous=NORMAL;')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO logs (dispositivo, servicio, log_original, ip_origen, nivel_gravedad, veredicto_ia, accion_tomada)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (device, attack_vector, raw_log, source_ip, severity, verdict, "Solo Registro"))
            conn.commit()
            logger.info(f"[INFO] Alerta registrada para IP: {source_ip}")
            return {"status": "success", "message": "Log guardado correctamente. NO LLAMAR a register_alert de nuevo. Procede con block_ip si es necesario."}
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower() or "readonly" in str(e).lower():
                logger.warning(f"[WARNING] Base de datos ocupada, reintento {attempt+1}/5...")
                time.sleep(2)
            else:
                logger.error(f"[ERROR] Error de base de datos: {e}")
                return {"status": "error", "message": str(e)}
        except Exception as e:
            logger.error(f"[ERROR] Error no contemplado en registro: {e}")
            return {"status": "error", "message": str(e)}
        finally:
            if conn:
                conn.close()
    return {"status": "error", "message": "Database timeout after retries"}

def update_alert_status(device: str, command_result: str, mitigation_status: str) -> dict:
    """
    Actualiza el estado de mitigación del último evento registrado para un dispositivo, 
    permitiendo a los agentes tener feedback sobre si sus defensas funcionaron.
    
    Args:
        device: Nombre del dispositivo origen (ej. 'Pi4-Sensor-01').
        command_result: Salida literal devuelta por la terminal.
        mitigation_status: 'EXITO' si funcionó, 'FALLO' si el sistema devolvió un error.
    """
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10.0, check_same_thread=False)
        conn.execute('PRAGMA journal_mode=WAL;')
        cursor = conn.cursor()
        
        # Actualizamos la fila más reciente (ID más alto) correspondiente a este dispositivo
        cursor.execute('''
            UPDATE logs 
            SET estado_mitigacion = CASE 
                WHEN estado_mitigacion IS NULL THEN ?
                ELSE estado_mitigacion || ? 
            END
            WHERE id = (
                SELECT id FROM logs 
                WHERE dispositivo = ? 
                ORDER BY timestamp DESC 
                LIMIT 1
            )
        ''', (f"[{mitigation_status}] {command_result}", f"\n[{mitigation_status}] {command_result}", device))
        
        rowcount = cursor.rowcount
        conn.commit()
        conn.close()
        
        if rowcount > 0:
            logger.info(f"[INFO] Feedback registrado en DB (Dispositivo: {device} | Status: {mitigation_status})")
            return {"status": "success", "message": "Feedback escrito exitosamente en la base de datos."}
        else:
            return {"status": "warning", "message": "No se encontraron alertas previas para este dispositivo."}
    except Exception as e:
        logger.error(f"[ERROR] Error al actualizar status de alerta: {e}")
        return {"status": "error", "message": str(e)}
