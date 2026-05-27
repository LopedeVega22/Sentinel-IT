import os
import sys
import sqlite3
import tempfile
import unittest
import base64
import types
from unittest.mock import patch, MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# Mock AWSMqttClient before importing dashboard_soc to avoid AWS connection attempts
sys.modules.setdefault('awscrt', types.SimpleNamespace(io=MagicMock(), mqtt=MagicMock()))
sys.modules.setdefault('awsiot', types.SimpleNamespace(mqtt_connection_builder=MagicMock()))
import aws_connector
aws_connector.AWSMqttClient = MagicMock()

# Set environment variables for testing
os.environ['DASHBOARD_USER'] = 'admin'
os.environ['DASHBOARD_PASSWORD'] = 'testpass'

import dashboard_soc
from dashboard_soc import app


class FakeMqttClient:
    def __init__(self):
        self.published = []

    def is_alive(self):
        return True

    def publish(self, topic, payload, wait_for_ack=False):
        self.published.append((topic, payload, wait_for_ack))


def create_temp_logs_db():
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    tmp.close()
    conn = sqlite3.connect(tmp.name)
    conn.execute('''
        CREATE TABLE logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dispositivo TEXT,
            servicio TEXT,
            log_original TEXT,
            ip_origen TEXT,
            nivel_gravedad TEXT,
            veredicto_ia TEXT,
            accion_tomada TEXT,
            estado_mitigacion TEXT,
            status TEXT DEFAULT 'LOGGED',
            pending_command TEXT,
            rationale TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    return tmp.name

class TestDashboardAPI(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        # Create auth header
        auth_string = "admin:testpass"
        self.auth_headers = {
            'Authorization': 'Basic ' + base64.b64encode(auth_string.encode('ascii')).decode('ascii')
        }

    @patch('dashboard_soc.get_logs')
    @patch('dashboard_soc.get_db_stats')
    def test_api_data_returns_200(self, mock_db_stats, mock_logs):
        # Mocking database calls to return empty/default values
        mock_logs.return_value = []
        mock_db_stats.return_value = (0, 0, 0, "No activity")
        
        response = self.client.get('/api/data', headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)
        
        data = response.get_json()
        self.assertIn('logs', data)
        self.assertIn('total_logs', data)
        self.assertIn('threat_level', data)

    @patch('dashboard_soc.get_logs')
    @patch('dashboard_soc.get_db_stats')
    def test_index_returns_200(self, mock_db_stats, mock_logs):
        mock_logs.return_value = []
        mock_db_stats.return_value = (0, 0, 0, "No activity")
        
        response = self.client.get('/', headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Sentinel-IT', response.data)

    def test_revert_derives_delete_command_for_inserted_iptables_rule(self):
        db_path = create_temp_logs_db()
        mqtt = FakeMqttClient()
        dashboard_soc.mqtt_client = mqtt
        try:
            conn = sqlite3.connect(db_path)
            conn.execute(
                '''
                INSERT INTO logs (
                    dispositivo, servicio, log_original, ip_origen, nivel_gravedad,
                    veredicto_ia, accion_tomada, status, pending_command, rationale
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    'Pi4-Felix', 'SSH', '{}', '1.2.3.4', 'Alta',
                    'Ataque', 'Auto-ejecutado [LOW]: bloqueo', 'APPROVED',
                    'sudo iptables -I INPUT -s 1.2.3.4 -j DROP', 'test',
                ),
            )
            conn.commit()
            conn.close()

            with patch('dashboard_soc.DB_PATH', db_path), \
                 patch('dashboard_soc.get_mqtt_client', return_value=mqtt), \
                 patch('dashboard_soc.signing.sign_payload', side_effect=lambda payload: payload), \
                 patch('dashboard_soc.policy_engine.audit'):
                response = self.client.post('/revert/1', headers=self.auth_headers)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(mqtt.published[0][1]['comando'], 'sudo iptables -D INPUT -s 1.2.3.4 -j DROP')
            self.assertFalse(mqtt.published[0][1]['comando'].startswith('#'))
        finally:
            dashboard_soc.mqtt_client = None
            try:
                os.unlink(db_path)
            except OSError:
                pass

    def test_revert_records_the_dispatched_command_for_dashboard_visibility(self):
        db_path = create_temp_logs_db()
        mqtt = FakeMqttClient()
        dashboard_soc.mqtt_client = mqtt
        sent_command = 'sudo iptables -D INPUT -s 1.2.3.4 -j DROP'
        try:
            conn = sqlite3.connect(db_path)
            conn.execute(
                '''
                INSERT INTO logs (
                    dispositivo, servicio, log_original, ip_origen, nivel_gravedad,
                    veredicto_ia, accion_tomada, status, pending_command, rationale
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    'Pi4-Felix', 'SSH', '{}', '1.2.3.4', 'Alta',
                    'Ataque', 'Auto-ejecutado [LOW]: bloqueo', 'APPROVED',
                    'sudo iptables -A INPUT -s 1.2.3.4 -j DROP', 'test',
                ),
            )
            conn.commit()
            conn.close()

            with patch('dashboard_soc.DB_PATH', db_path), \
                 patch('dashboard_soc.get_mqtt_client', return_value=mqtt), \
                 patch('dashboard_soc.signing.sign_payload', side_effect=lambda payload: payload), \
                 patch('dashboard_soc.policy_engine.audit'):
                response = self.client.post(
                    '/revert/1',
                    json={'command': sent_command},
                    headers=self.auth_headers,
                )

            self.assertEqual(response.status_code, 200)
            conn = sqlite3.connect(db_path)
            row = conn.execute('SELECT pending_command FROM logs WHERE id = 1').fetchone()
            conn.close()
            self.assertEqual(row[0], sent_command)
        finally:
            dashboard_soc.mqtt_client = None
            try:
                os.unlink(db_path)
            except OSError:
                pass

if __name__ == '__main__':
    unittest.main()
