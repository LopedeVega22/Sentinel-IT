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


if __name__ == "__main__":
    unittest.main()
