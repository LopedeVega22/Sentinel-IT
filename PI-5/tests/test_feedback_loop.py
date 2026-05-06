"""
Test del ciclo de Feedback: valida que las herramientas del SOC
registran correctamente los incidentes y actualizan la mitigación
en la base de datos SQLite.

Este test NO necesita conexión a Gemini ni a AWS IoT Core.
Llama directamente a las funciones (tools) del agente para
verificar la lógica de negocio de forma offline.
"""
import os
import sys
import sqlite3
import json
import time

# ── Paths ────────────────────────────────────────────────────────────
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "soc_data.db"))


# ── Mock del cliente MQTT ────────────────────────────────────────────
class MockIotClient:
    """Simula el cliente MQTT para interceptar comandos sin red."""
    def __init__(self):
        self.commands_sent = []

    def publish(self, topic, payload):
        self.commands_sent.append({"topic": topic, "payload": payload})
        print(f"  [MOCK MQTT] Publicado en {topic}: {json.dumps(payload, ensure_ascii=False)[:120]}...")

    def subscribe(self, topic, callback):
        print(f"  [MOCK MQTT] Suscrito a {topic} (no-op)")


# ── Helpers ──────────────────────────────────────────────────────────
def query_db(sql, params=()):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return rows


def print_section(title):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


# ── Test principal ───────────────────────────────────────────────────
def run_test():
    print_section("🛡️  TEST OFFLINE – Ciclo de Feedback SOC")

    # Importar herramientas después de fijar el path
    from tools.iot_tools import init_iot_tools, execute_diagnostic_command
    from tools.db_tools import register_alert, update_alert_status

    # 1. Inyectar cliente mock
    mock_iot = MockIotClient()
    init_iot_tools(mock_iot)
    print("\n[PASO 1] Cliente MQTT mock inyectado ✔")

    # 2. Registrar una alerta simulada (usando la firma real de register_alert)
    print("\n[PASO 2] Registrando alerta de ataque RCE...")
    result_alert = register_alert(
        device="Pi4-Test",
        attack_vector="NGINX-HTTP",
        source_ip="10.0.0.55",
        severity="Alta",
        verdict="Inyección de comando detectada vía POST /api/exec. Patrón coincide con RCE.",
        raw_log='{"evento":"RCE_ATTACK","ip":"10.0.0.55","patron":"Command Injection"}',
    )
    print(f"  Resultado: {result_alert}")

    # 3. Enviar un comando remoto (se intercepta por el mock)
    print("\n[PASO 3] Enviando comando remoto a Pi4-Test...")
    result_cmd = execute_diagnostic_command(
        device="Pi4-Test",
        command="sudo systemctl status nginx",
        reason="Comprobar servicio comprometido tras RCE confirmado",
    )
    print(f"  Resultado: {result_cmd}")

    # Verificar que el mock recibió el comando
    if mock_iot.commands_sent:
        print(f"  ✔ Mock interceptó {len(mock_iot.commands_sent)} comando(s)")
    else:
        print("  ❌ El mock NO interceptó ningún comando")

    # 4. Simular respuesta exitosa del sensor → actualizar mitigación
    print("\n[PASO 4] Simulando feedback exitoso → update_alert_status...")
    result_ok = update_alert_status(
        device="Pi4-Test",
        command_result="nginx.service successfully stopped.",
        mitigation_status="EXITO",
    )
    print(f"  Resultado: {result_ok}")

    # 5. Simular respuesta de error → actualizar mitigación
    print("\n[PASO 5] Simulando feedback con error → update_alert_status...")
    result_err = update_alert_status(
        device="Pi4-Test",
        command_result="Failed to stop nginx: Unit nginx.service not loaded.",
        mitigation_status="FALLO",
    )
    print(f"  Resultado: {result_err}")

    # 6. Consultar la base de datos
    print_section("📊  Estado de la Base de Datos")
    try:
        rows = query_db(
            "SELECT id, dispositivo, servicio, accion_tomada, estado_mitigacion "
            "FROM logs ORDER BY id DESC LIMIT 5"
        )
        if rows:
            for r in rows:
                print(
                    f"  ID={r['id']}  disp={r['dispositivo']}  "
                    f"servicio={r['servicio']}  accion={r['accion_tomada']}  "
                    f"estado={r['estado_mitigacion']}"
                )
        else:
            print("  (sin registros)")
    except Exception as e:
        print(f"  Error consultando DB: {e}")

    # 7. Resultado final
    print_section("RESULTADO FINAL")
    alert_ok = result_alert.get("status") == "success"
    cmd_ok = result_cmd.get("status") == "action_sent"
    fb_ok = result_ok.get("status") == "success"
    
    print(f"  register_alert:          {'✅' if alert_ok else '❌'}  {result_alert}")
    print(f"  execute_remote_command:  {'✅' if cmd_ok else '❌'}  mock={len(mock_iot.commands_sent)} cmd(s)")
    print(f"  update_alert_status(ok): {'✅' if fb_ok else '❌'}  {result_ok}")
    print(f"  update_alert_status(err):{'⚠️ ' if result_err.get('status') == 'success' else '❌'}  {result_err}")
    
    all_pass = alert_ok and cmd_ok and fb_ok
    print(f"\n  {'🎉 TODOS LOS TESTS PASARON' if all_pass else '⚠️  Algunos tests fallaron'}")
    print()


if __name__ == "__main__":
    run_test()
