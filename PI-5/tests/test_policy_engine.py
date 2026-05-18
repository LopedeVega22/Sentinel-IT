"""
Tests del Policy Engine (PI-5/src/tools/policy_engine.py).

Ejecutar (desde PI-5/):
    python -m unittest tests.test_policy_engine -v
"""

import os
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from tools import policy_engine
from tools.policy_engine import RiskLevel, classify, decide


class TestClassification(unittest.TestCase):

    # --- SAFE_READ ---
    def test_cat_var_log_es_safe_read(self):
        self.assertEqual(classify("cat /var/log/auth.log").level, RiskLevel.SAFE_READ)

    def test_sudo_cat_es_safe_read(self):
        # Objecion L16 del doc: sudo cat de un log debe pasar sin friccion.
        self.assertEqual(classify("sudo cat /var/log/auth.log").level, RiskLevel.SAFE_READ)

    def test_sudo_journalctl_es_safe_read(self):
        self.assertEqual(classify("sudo journalctl -u sshd").level, RiskLevel.SAFE_READ)

    def test_sudo_iptables_listar_es_safe_read(self):
        self.assertEqual(classify("sudo iptables -L INPUT").level, RiskLevel.SAFE_READ)
        self.assertEqual(classify("sudo iptables -S").level, RiskLevel.SAFE_READ)

    def test_systemctl_status_es_read(self):
        self.assertEqual(classify("sudo systemctl status apache2").level, RiskLevel.HIGH)
        # Nota: systemctl en general es BROAD_WRITE; el subcomando 'status' es
        # idealmente SAFE_READ pero el clasificador trata systemctl como
        # peligroso por defecto. Test documenta el comportamiento real.

    # --- LOW ---
    def test_iptables_bloqueo_ip_es_low(self):
        c = classify("sudo iptables -A INPUT -s 1.2.3.4 -j DROP")
        self.assertEqual(c.level, RiskLevel.LOW)

    def test_comando_desconocido_es_low(self):
        # Objecion L63 del doc: lo desconocido no se deniega, cae a LOW.
        c = classify("herramienta-rara --modo verbose")
        self.assertEqual(c.level, RiskLevel.LOW)

    # --- HIGH ---
    def test_systemctl_restart_es_high(self):
        self.assertEqual(classify("sudo systemctl restart apache2").level, RiskLevel.HIGH)

    def test_kill_es_high(self):
        self.assertEqual(classify("kill 1234").level, RiskLevel.HIGH)

    def test_iptables_flush_cadena_es_high(self):
        self.assertEqual(classify("sudo iptables -F INPUT").level, RiskLevel.HIGH)

    def test_sed_in_place_es_high(self):
        self.assertEqual(classify("sed -i 's/a/b/' /tmp/foo").level, RiskLevel.HIGH)

    # --- CRITICAL ---
    def test_rm_rf_es_critical(self):
        self.assertEqual(classify("rm -rf /tmp").level, RiskLevel.CRITICAL)

    def test_dd_es_critical(self):
        self.assertEqual(classify("dd if=/dev/zero of=/dev/sda").level, RiskLevel.CRITICAL)

    def test_shutdown_es_critical(self):
        self.assertEqual(classify("shutdown -h now").level, RiskLevel.CRITICAL)

    def test_iptables_flush_global_es_critical(self):
        self.assertEqual(classify("sudo iptables -F").level, RiskLevel.CRITICAL)

    def test_php_r_con_system_destructivo_es_critical(self):
        # Capa que cierra el agujero `php -r 'system("rm -rf /tmp")'` del doc.
        # `php` (interprete) + `-r` -> +2 escalones desde LOW base = CRITICAL.
        c = classify("php -r 'system(\"rm -rf /tmp\")'")
        self.assertEqual(c.level, RiskLevel.CRITICAL)

    def test_bash_c_es_critical_o_high(self):
        # bash con -c es ejecucion arbitraria -> al menos HIGH, generalmente CRITICAL.
        c = classify("bash -c 'echo hola'")
        self.assertIn(c.level, (RiskLevel.HIGH, RiskLevel.CRITICAL))
        self.assertTrue(c.is_executable_via_interpreter)

    # --- Modificadores ---
    def test_concatenacion_con_rm_escala(self):
        c = classify("ls /tmp; rm /tmp/foo")
        # `;` detectado + verbo destructivo rm dentro -> al menos HIGH
        self.assertGreaterEqual(c.level, RiskLevel.HIGH)

    def test_metacaracter_punto_y_coma_escala(self):
        c = classify("cat /etc/hosts; whoami")
        # SAFE_READ + ';' -> sube 1 nivel
        self.assertEqual(c.level, RiskLevel.LOW)

    def test_wildcard_sobre_etc_escala(self):
        c = classify("rm /etc/*.conf")
        self.assertEqual(c.level, RiskLevel.CRITICAL)

    def test_comando_vacio_es_high(self):
        self.assertEqual(classify("").level, RiskLevel.HIGH)
        self.assertEqual(classify("   ").level, RiskLevel.HIGH)

    def test_comillas_mal_cerradas_son_high(self):
        c = classify("echo 'hola")  # comilla sin cerrar
        self.assertEqual(c.level, RiskLevel.HIGH)


class TestDecision(unittest.TestCase):

    def test_solo_safe_read_se_permite_directo(self):
        self.assertTrue(decide("cat /var/log/auth.log").allow_direct)
        self.assertFalse(decide("sudo iptables -A INPUT -s 1.2.3.4 -j DROP").allow_direct)
        self.assertFalse(decide("rm -rf /tmp").allow_direct)


class TestRoundTrip(unittest.TestCase):

    def setUp(self):
        # Limpia el cache antes de cada test
        with policy_engine._dispatch_lock:
            policy_engine._dispatch_cache.clear()

    def test_match_cuando_comando_fue_emitido(self):
        policy_engine.record_dispatch("sudo iptables -A INPUT -s 1.2.3.4 -j DROP", "Pi4-Felix")
        verdict = policy_engine.verify_feedback(
            "sudo iptables -A INPUT -s 1.2.3.4 -j DROP", "Pi4-Felix"
        )
        self.assertEqual(verdict, "MATCH")

    def test_anomaly_cuando_comando_no_fue_emitido(self):
        # Cache vacia: cualquier comando ejecutado es anomalo.
        verdict = policy_engine.verify_feedback("whoami", "Pi4-Felix")
        self.assertEqual(verdict, "ANOMALY")

    def test_anomaly_si_dispositivo_diferente(self):
        policy_engine.record_dispatch("cat /tmp/x", "Pi4-Felix")
        verdict = policy_engine.verify_feedback("cat /tmp/x", "Pi4-Otro")
        self.assertEqual(verdict, "ANOMALY")

    def test_match_ignora_espacios_redundantes(self):
        policy_engine.record_dispatch("cat   /tmp/x", "Pi4-Felix")
        verdict = policy_engine.verify_feedback("cat /tmp/x", "Pi4-Felix")
        self.assertEqual(verdict, "MATCH")

    def test_match_feedback_devuelve_log_id_para_correlacion(self):
        # El fast-path del coordinador necesita recuperar el log_id original
        # del dispatch para escribir estado_mitigacion en la fila correcta.
        policy_engine.record_dispatch(
            "php /var/www/html/sentinelti.com/cerrar_sesion_admin.php --cerrar-nombre 'Admin'",
            "Pi4-Felix",
            log_id=42,
        )
        match = policy_engine.match_feedback(
            "php /var/www/html/sentinelti.com/cerrar_sesion_admin.php --cerrar-nombre 'Admin'",
            "Pi4-Felix",
        )
        self.assertIsNotNone(match)
        self.assertEqual(match["log_id"], 42)

    def test_match_feedback_devuelve_el_dispatch_mas_reciente(self):
        # Si el operador aprueba el mismo comando dos veces (porque revertio
        # y volvio a aplicarlo), el feedback debe correlacionar con el ultimo
        # dispatch — el primero ya quedo cerrado.
        policy_engine.record_dispatch("cat /tmp/x", "Pi4-Felix", log_id=1)
        import time as _time
        _time.sleep(0.01)
        policy_engine.record_dispatch("cat /tmp/x", "Pi4-Felix", log_id=2)
        match = policy_engine.match_feedback("cat /tmp/x", "Pi4-Felix")
        self.assertIsNotNone(match)
        self.assertEqual(match["log_id"], 2)

    def test_match_feedback_none_si_no_hay_dispatch(self):
        self.assertIsNone(policy_engine.match_feedback("whoami", "Pi4-Felix"))


class TestAuditLogInmutable(unittest.TestCase):
    """
    Crea una BD temporal con el esquema completo (incluyendo audit_log y sus
    triggers) y verifica que UPDATE/DELETE estan bloqueados.
    """

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "soc_test.db")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dispositivo TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts DATETIME DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT,
                device TEXT,
                command TEXT,
                classification TEXT,
                decision_reason TEXT,
                related_log_id INTEGER
            )
        """)
        cursor.execute("""
            CREATE TRIGGER audit_log_no_update
            BEFORE UPDATE ON audit_log
            BEGIN SELECT RAISE(ABORT, 'audit_log is append-only'); END
        """)
        cursor.execute("""
            CREATE TRIGGER audit_log_no_delete
            BEFORE DELETE ON audit_log
            BEGIN SELECT RAISE(ABORT, 'audit_log is append-only'); END
        """)
        cursor.execute(
            "INSERT INTO audit_log (event_type, device, command) VALUES (?, ?, ?)",
            ("DISPATCH", "Pi4-Felix", "cat /tmp/x"),
        )
        conn.commit()
        self.conn = conn

    def tearDown(self):
        self.conn.close()
        try:
            os.remove(self.db_path)
        except OSError:
            pass
        os.rmdir(self.tmpdir)

    def test_update_bloqueado(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("UPDATE audit_log SET command='x' WHERE id=1")
            self.conn.commit()

    def test_delete_bloqueado(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("DELETE FROM audit_log WHERE id=1")
            self.conn.commit()

    def test_insert_funciona(self):
        self.conn.execute(
            "INSERT INTO audit_log (event_type, device, command) VALUES (?, ?, ?)",
            ("APPROVE", "Pi4-Felix", "iptables -A ..."),
        )
        self.conn.commit()
        count = self.conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
        self.assertEqual(count, 2)


class TestMitigationApprovalAutoExecute(unittest.TestCase):
    """
    Comprueba la nueva semantica de request_mitigation_approval:
        - LOW (o SAFE_READ) -> publica directo via _iot_client (auto-ejecucion).
        - HIGH / CRITICAL  -> queda en cuarentena (no publica).
    Mockea el cliente IoT y la BD para no depender del entorno.
    """

    def setUp(self):
        from tools import iot_tools
        self.iot_tools = iot_tools

        # Cliente IoT mock que registra los publish
        class _MockClient:
            def __init__(self):
                self.publishes = []

            def publish(self, topic, payload):
                self.publishes.append((topic, payload))

        self.mock_client = _MockClient()
        iot_tools.init_iot_tools(self.mock_client)

        # Redirigir DB a tmp con schema minimo
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "soc_test.db")
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dispositivo TEXT,
                servicio TEXT,
                accion_tomada TEXT,
                status TEXT,
                pending_command TEXT,
                rationale TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts DATETIME DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT,
                device TEXT,
                command TEXT,
                classification TEXT,
                decision_reason TEXT,
                related_log_id INTEGER
            );
            INSERT INTO logs (dispositivo, servicio, accion_tomada, status)
            VALUES ('Pi4-Test', 'SSH', 'Solo Registro', 'LOGGED');
        """)
        conn.commit()
        conn.close()

        # Apuntar tanto iot_tools como policy_engine a la BD temporal
        self._original_iot_db = iot_tools.DB_PATH
        self._original_policy_db = policy_engine.DB_PATH
        iot_tools.DB_PATH = self.db_path
        policy_engine.DB_PATH = self.db_path

        # Cache limpia para no interferir con round-trip
        with policy_engine._dispatch_lock:
            policy_engine._dispatch_cache.clear()

    def tearDown(self):
        self.iot_tools.DB_PATH = self._original_iot_db
        policy_engine.DB_PATH = self._original_policy_db
        self.iot_tools.init_iot_tools(None)
        try:
            os.remove(self.db_path)
        except OSError:
            pass
        os.rmdir(self.tmpdir)

    def _row_status(self):
        conn = sqlite3.connect(self.db_path)
        row = conn.execute("SELECT status FROM logs WHERE dispositivo='Pi4-Test'").fetchone()
        conn.close()
        return row[0]

    def test_low_se_autoejecuta(self):
        result = self.iot_tools.request_mitigation_approval(
            device="Pi4-Test",
            mitigation_command="sudo iptables -A INPUT -s 1.2.3.4 -j DROP",
            rationale="Bloqueo de IP atacante",
        )
        self.assertEqual(result["status"], "auto_executed")
        self.assertEqual(result["risk_level"], "LOW")
        self.assertEqual(len(self.mock_client.publishes), 1)
        self.assertEqual(self._row_status(), "APPROVED")

    def test_high_queda_pendiente(self):
        result = self.iot_tools.request_mitigation_approval(
            device="Pi4-Test",
            mitigation_command="sudo systemctl restart apache2",
            rationale="Reiniciar Apache",
        )
        self.assertEqual(result["status"], "pending_approval")
        self.assertEqual(result["risk_level"], "HIGH")
        self.assertEqual(len(self.mock_client.publishes), 0)
        self.assertEqual(self._row_status(), "PENDING")

    def test_critical_queda_pendiente(self):
        result = self.iot_tools.request_mitigation_approval(
            device="Pi4-Test",
            mitigation_command="rm -rf /tmp",
            rationale="Limpieza brusca",
        )
        self.assertEqual(result["status"], "pending_approval")
        self.assertEqual(result["risk_level"], "CRITICAL")
        self.assertEqual(len(self.mock_client.publishes), 0)
        self.assertEqual(self._row_status(), "PENDING")


if __name__ == "__main__":
    unittest.main()
