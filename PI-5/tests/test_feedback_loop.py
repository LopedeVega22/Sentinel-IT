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
    from tools.iot_tools import init_iot_tools, execute_remote_command
    from tools.db_tools import register_alert, update_mitigation_status

    # 1. Inyectar cliente mock
    mock_iot = MockIotClient()
    init_iot_tools(mock_iot)
    print("\n[PASO 1] Cliente MQTT mock inyectado ✔")

    # 2. Registrar una alerta simulada
    print("\n[PASO 2] Registrando alerta de ataque RCE...")
    result_alert = register_alert(
        dispositivo="Pi4-Test",
        tipo_alerta="RCE_ATTACK",
        descripcion="Inyección de comando detectada desde 10.0.0.55",
        log_original='{"evento":"RCE_ATTACK","ip":"10.0.0.55","patron":"Command Injection"}',
    )
    print(f"  Resultado: {result_alert}")

    # 3. Enviar un comando remoto (se intercepta por el mock)
    print("\n[PASO 3] Enviando comando remoto a Pi4-Test...")
    result_cmd = execute_remote_command(
        device="Pi4-Test",
        command="sudo systemctl stop nginx",
    )
    print(f"  Resultado: {result_cmd}")

    # Verificar que el mock recibió el comando
    if mock_iot.commands_sent:
        print(f"  ✔ Mock interceptó {len(mock_iot.commands_sent)} comando(s)")
    else:
        print("  ❌ El mock NO interceptó ningún comando")

    # 4. Simular respuesta exitosa del sensor → actualizar mitigación
    print("\n[PASO 4] Simulando feedback exitoso → update_mitigation_status...")
    result_update = update_mitigation_status(
        dispositivo="Pi4-Test",
        status="success",
        output="nginx.service successfully stopped.",
    )
    print(f"  Resultado: {result_update}")

    # 5. Simular respuesta de error → actualizar mitigación
    print("\n[PASO 5] Simulando feedback con error → update_mitigation_status...")
    result_err = update_mitigation_status(
        dispositivo="Pi4-Test",
        status="error",
        output="Failed to stop nginx: Unit nginx.service not loaded.",
    )
    print(f"  Resultado: {result_err}")

    # 6. Consultar la base de datos
    print_section("📊  Estado de la Base de Datos")
    try:
        rows = query_db(
            "SELECT id, dispositivo, tipo_alerta, accion_tomada, estado_mitigacion "
            "FROM logs ORDER BY id DESC LIMIT 5"
        )
        if rows:
            for r in rows:
                print(
                    f"  ID={r['id']}  disp={r['dispositivo']}  "
                    f"tipo={r['tipo_alerta']}  accion={r['accion_tomada']}  "
                    f"estado={r['estado_mitigacion']}"
                )
        else:
            print("  (sin registros)")
    except Exception as e:
        print(f"  Error consultando DB: {e}")

    # 7. Resultado final
    print_section("RESULTADO FINAL")
    ok = (
        "correctamente" in str(result_alert).lower() or "registrado" in str(result_alert).lower()
    )
    print(f"  register_alert:          {'✅' if ok else '⚠️'}  {result_alert[:80]}")
    print(f"  execute_remote_command:  {'✅' if mock_iot.commands_sent else '❌'}  mock={len(mock_iot.commands_sent)} cmd(s)")
    print(f"  update_mitigation(ok):   {result_update[:80]}")
    print(f"  update_mitigation(err):  {result_err[:80]}")
    print()


if __name__ == "__main__":
    run_test()
