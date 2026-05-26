"""
Test E2E del flujo completo de agentes IA (Triage -> Comando -> Feedback).

Funcionamiento:
  1. Conecta a AWS IoT Core con el client-id 'Dashboard-SOC-Pi5'
     (autorizado por la policy, paralelo al coordinador 'Pi5-dani').
  2. Se hace pasar por la PI-4: publica un log de ataque real en
     'seguridad/<device>/evento' y queda a la escucha en
     'seguridad/<device>/comando' para capturar la orden que emita
     el triage_agent.
  3. Simula dos escenarios consecutivos:
       Caso A (EXITO):  responde con status=success y verifica que
                        el feedback_agent escribe '[EXITO]' en la BD.
       Caso B (FALLO):  responde con status=error y verifica que el
                        feedback_agent escribe '[FALLO]' y opcionalmente
                        propone un comando alternativo (que volveriamos
                        a capturar en /comando).

Requisitos previos:
  * El coordinador (main_coordinator.py) debe estar CORRIENDO en otra
    terminal o contenedor para que los agentes procesen los eventos.
  * La PI-4 NO debe estar conectada al broker (este test se hace pasar
    por ella; si la PI-4 real publica a la vez habria carrera).

Uso:
  cd PI-5
  python tests/test_agent_flow.py
"""

import json
import os
import sqlite3
import sys
import time
from datetime import datetime

import yaml

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from aws_connector import AWSMqttClient

# ---------------------------------------------------------------------------
# Parametros del test
# ---------------------------------------------------------------------------
TEST_DEVICE = "Pi4-Felix"  # cualquier device autorizado por la policy
# Ventana de espera para que el triage agent procese el evento
# (procesamiento inmediato via asyncio.Queue + tiempo de inferencia del LLM)
TRIAGE_WAIT_SECONDS = 45
FEEDBACK_WAIT_SECONDS = 45

# ---------------------------------------------------------------------------
# Carga de configuracion
# ---------------------------------------------------------------------------
CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config.yml"))
with open(CONFIG_PATH, "r") as f:
    config = yaml.safe_load(f)

ENDPOINT = config["aws"]["endpoint"]
CERT_PATH = os.path.join(os.path.dirname(CONFIG_PATH), config["aws"]["cert_path"])
KEY_PATH = os.path.join(os.path.dirname(CONFIG_PATH), config["aws"]["key_path"])
ROOT_CA = os.path.join(os.path.dirname(CONFIG_PATH), config["aws"]["root_ca"])
DB_PATH = os.path.join(os.path.dirname(CONFIG_PATH), config["database"]["db_path"])

# Topics derivados de config
TOPIC_EVENTO = f"seguridad/{TEST_DEVICE}/evento"
TOPIC_RESPUESTA = f"seguridad/{TEST_DEVICE}/respuesta"
TOPIC_COMANDO_LISTEN = f"seguridad/{TEST_DEVICE}/comando"

# Buzon compartido de comandos capturados desde el coordinador
captured_commands = []


# ---------------------------------------------------------------------------
# Utilidades de visualizacion
# ---------------------------------------------------------------------------
def banner(title: str) -> None:
    print("\n" + "=" * 72)
    print(f"  {title}")
    print("=" * 72)


def step(msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


# ---------------------------------------------------------------------------
# Captura de comandos emitidos por el coordinador (simulamos a la PI-4)
# ---------------------------------------------------------------------------
def on_command_from_coordinator(topic, payload, dup=None, qos=None, retain=None, **kwargs):
    try:
        data = json.loads(payload.decode("utf-8"))
        entry = {
            "received_at": time.time(),
            "topic": topic,
            "comando": data.get("comando", ""),
            "accion": data.get("accion", ""),
            "motivo": data.get("motivo", ""),
        }
        captured_commands.append(entry)
        print(f"\n[<-- COMANDO DESDE COORDINADOR] topic={topic}")
        print(f"    accion : {entry['accion']}")
        print(f"    motivo : {entry['motivo']}")
        print(f"    comando: {entry['comando']}")
    except Exception as exc:
        print(f"[ERROR] decodificando comando: {exc}")


# ---------------------------------------------------------------------------
# Helpers de BD para validar el estado tras cada paso
# ---------------------------------------------------------------------------
def fetch_latest_log(device: str) -> dict | None:
    if not os.path.exists(DB_PATH):
        return None
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT id, dispositivo, servicio, ip_origen, nivel_gravedad, "
            "veredicto_ia, accion_tomada, estado_mitigacion, status, "
            "pending_command, rationale, timestamp "
            "FROM logs WHERE dispositivo = ? ORDER BY id DESC LIMIT 1",
            (device,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def print_log_row(row: dict | None) -> None:
    if not row:
        print("    (no hay registros aun para este dispositivo)")
        return
    print(f"    id              : {row['id']}")
    print(f"    timestamp       : {row['timestamp']}")
    print(f"    servicio        : {row['servicio']}")
    print(f"    ip_origen       : {row['ip_origen']}")
    print(f"    nivel_gravedad  : {row['nivel_gravedad']}")
    print(f"    veredicto_ia    : {(row['veredicto_ia'] or '')[:120]}")
    print(f"    accion_tomada   : {(row['accion_tomada'] or '')[:120]}")
    print(f"    status          : {row['status']}")
    print(f"    pending_command : {(row['pending_command'] or '')[:120]}")
    print(f"    estado_mitig    : {(row['estado_mitigacion'] or '')[:200]}")


def wait_for_command(timeout: int, label: str) -> dict | None:
    """Bloquea hasta que el coordinador publique un comando o expire el timeout."""
    step(f"Esperando comando del coordinador (max {timeout}s) tras {label}...")
    start = time.time()
    baseline = len(captured_commands)
    while time.time() - start < timeout:
        if len(captured_commands) > baseline:
            return captured_commands[-1]
        time.sleep(1)
    return None


def wait_for_estado_mitigacion(device: str, marker: str, timeout: int) -> dict | None:
    """Espera a que la fila mas reciente del device contenga 'marker' en estado_mitigacion."""
    step(f"Esperando que la BD muestre '{marker}' (max {timeout}s)...")
    start = time.time()
    while time.time() - start < timeout:
        row = fetch_latest_log(device)
        if row and (row.get("estado_mitigacion") or "").find(marker) >= 0:
            return row
        time.sleep(2)
    return fetch_latest_log(device)


# ---------------------------------------------------------------------------
# Escenarios
# ---------------------------------------------------------------------------
def escenario_a_exito(client: AWSMqttClient) -> bool:
    banner("ESCENARIO A — Comando ejecutado con EXITO")

    # 1) Inyectamos un ataque que el triage deberia clasificar como malicioso
    attack_log = {
        "evento": "SSH_BRUTE_FORCE",
        "prioridad": "ALTA",
        "sensor": TEST_DEVICE,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ip": "203.0.113.45",
        "usuario": "root",
        "intentos": 27,
        "patron": "Failed password for root from 203.0.113.45",
    }
    step(f"Publicando log de ataque -> {TOPIC_EVENTO}")
    client.publish(TOPIC_EVENTO, attack_log)

    # 2) Esperamos a que el triage_agent flushee la cola y emita un comando
    cmd = wait_for_command(TRIAGE_WAIT_SECONDS, "publicar evento de ataque")
    if not cmd:
        print("[FAIL] El coordinador NO emitio comando en el tiempo esperado.")
        print("       Revisa que main_coordinator.py este corriendo y que el modelo IA responda.")
        return False
    print(f"[OK] Comando capturado: {cmd['comando']}")

    # 3) Inspeccion del estado en BD tras el triage
    step("Estado en BD tras triage:")
    print_log_row(fetch_latest_log(TEST_DEVICE))

    # 4) Simulamos la respuesta exitosa de PI-4
    respuesta_ok = {
        "sensor": TEST_DEVICE,
        "comando": cmd["comando"],
        "status": "success",
        "output": f"(simulado) $ {cmd['comando']}\n-- regla aplicada en eth0 --",
    }
    step(f"Simulando respuesta EXITO -> {TOPIC_RESPUESTA}")
    client.publish(TOPIC_RESPUESTA, respuesta_ok)

    # 5) Esperamos a que el feedback_agent escriba EXITO en la BD
    row = wait_for_estado_mitigacion(TEST_DEVICE, "[EXITO]", FEEDBACK_WAIT_SECONDS)
    step("Estado en BD tras feedback:")
    print_log_row(row)

    ok = bool(row and "[EXITO]" in (row.get("estado_mitigacion") or ""))
    print(f"\n  -> {'[PASS]' if ok else '[FAIL]'} Escenario A (EXITO)")
    return ok


def escenario_b_fallo(client: AWSMqttClient) -> bool:
    banner("ESCENARIO B — Comando con FALLO y posible reescalado")

    # 1) Inyectamos otro ataque distinto para forzar una nueva fila
    attack_log = {
        "evento": "SQLI_DETECTED",
        "prioridad": "CRITICA",
        "sensor": TEST_DEVICE,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ip": "198.51.100.99",
        "usuario": "Anon",
        "patron": "' OR 1=1 --",
    }
    step(f"Publicando log de ataque SQLi -> {TOPIC_EVENTO}")
    client.publish(TOPIC_EVENTO, attack_log)

    cmd = wait_for_command(TRIAGE_WAIT_SECONDS, "publicar evento SQLi")
    if not cmd:
        print("[FAIL] No llego comando del coordinador.")
        return False
    print(f"[OK] Comando capturado: {cmd['comando']}")

    # 2) Devolvemos un fallo realista
    respuesta_err = {
        "sensor": TEST_DEVICE,
        "comando": cmd["comando"],
        "status": "error",
        "output": "iptables v1.8.7: unknown option \"--src-range\"\nTry `iptables -h' for more information.",
    }
    step(f"Simulando respuesta FALLO -> {TOPIC_RESPUESTA}")
    client.publish(TOPIC_RESPUESTA, respuesta_err)

    # 3) El feedback_agent deberia marcar FALLO
    row = wait_for_estado_mitigacion(TEST_DEVICE, "[FALLO]", FEEDBACK_WAIT_SECONDS)
    step("Estado en BD tras feedback fallido:")
    print_log_row(row)

    ok_fallo = bool(row and "[FALLO]" in (row.get("estado_mitigacion") or ""))

    # 4) Opcional: comprobamos si el feedback_agent propone un comando alternativo
    step(
        f"Comprobando si el feedback_agent propone una mitigacion alternativa "
        f"(ventana {TRIAGE_WAIT_SECONDS}s)..."
    )
    baseline = len(captured_commands)
    start = time.time()
    alternativa = None
    while time.time() - start < TRIAGE_WAIT_SECONDS:
        if len(captured_commands) > baseline:
            alternativa = captured_commands[-1]
            break
        time.sleep(1)

    if alternativa:
        print(f"[INFO] Mitigacion alternativa propuesta: {alternativa['comando']}")
        print("       (esto reabre el ciclo: PI-5 -> PI-4 -> feedback de nuevo)")
    else:
        print("[INFO] No hubo comando alternativo (el feedback_agent puede haber decidido detenerse).")

    print(f"\n  -> {'[PASS]' if ok_fallo else '[FAIL]'} Escenario B (FALLO marcado en BD)")
    return ok_fallo


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
def main():
    banner("TEST E2E — Flujo Triage / Feedback de Sentinel-IT")
    print(f"  Device suplantado     : {TEST_DEVICE}")
    print(f"  Topic evento (out)    : {TOPIC_EVENTO}")
    print(f"  Topic respuesta (out) : {TOPIC_RESPUESTA}")
    print(f"  Topic comando (in)    : {TOPIC_COMANDO_LISTEN}")
    print(f"  DB de validacion      : {DB_PATH}")
    print(f"  AWS endpoint          : {ENDPOINT}")
    print()
    print("  Pre-requisito: main_coordinator.py debe estar CORRIENDO.")
    print("                 La PI-4 real debe estar DESCONECTADA del broker.")

    client = AWSMqttClient(
        endpoint=ENDPOINT,
        cert_path=CERT_PATH,
        key_path=KEY_PATH,
        root_ca_path=ROOT_CA,
        client_id="Dashboard-SOC-Pi5",  # autorizado en la policy y distinto al coordinador
    )

    try:
        step("Conectando al broker...")
        client.connect()

        step(f"Suscribiendo a {TOPIC_COMANDO_LISTEN} para capturar comandos del coordinador")
        client.subscribe(TOPIC_COMANDO_LISTEN, on_command_from_coordinator)
        time.sleep(2)

        # --- Escenarios ---
        a_ok = escenario_a_exito(client)
        # Pequena pausa para no solapar procesamiento del coordinador
        time.sleep(5)
        b_ok = escenario_b_fallo(client)

        # --- Resumen final ---
        banner("RESUMEN")
        print(f"  Escenario A (EXITO) : {'PASS' if a_ok else 'FAIL'}")
        print(f"  Escenario B (FALLO) : {'PASS' if b_ok else 'FAIL'}")
        print(f"  Comandos capturados : {len(captured_commands)}")
        for i, c in enumerate(captured_commands, 1):
            print(f"    #{i} [{c['accion']}] {c['comando']}")

        if a_ok and b_ok:
            print("\n[SUCCESS] Flujo completo de agentes validado E2E.")
        else:
            print("\n[PARTIAL] Alguno de los escenarios no completo el ciclo.")
            print("           Revisa los logs del coordinador en /tmp/coordinator_soc.log")

    except KeyboardInterrupt:
        print("\n[INFO] Interrumpido por el usuario.")
    except Exception as exc:
        print(f"[ERROR] {exc}")
        raise
    finally:
        try:
            if client.connection:
                client.connection.disconnect().result()
            step("Desconectado del broker.")
        except Exception:
            pass


if __name__ == "__main__":
    main()
