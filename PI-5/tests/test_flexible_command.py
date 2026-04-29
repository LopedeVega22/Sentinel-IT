"""
Test E2E de comunicación MQTT para el bucle de feedback SOC.

IMPORTANTE: AWS IoT Core tiene dos restricciones clave:
  1. La Policy solo permite client-IDs: Pi5-dani, Pi4-felix, Dashboard-SOC-Pi5
  2. La Policy solo permite topics bajo: seguridad/*

Por tanto, este test PARA el coordinador principal temporalmente,
usa su client-ID (Pi5-dani) para conectarse, ejecuta las pruebas,
y luego informa de que el coordinador debe reiniciarse.

Alternativa: ejecutar CON el coordinador corriendo pero usando
el client-ID "Dashboard-SOC-Pi5" que también está autorizado.
"""
import yaml
import sys
import os
import time
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from aws_connector import AWSMqttClient

# ── Almacén de feedback ──────────────────────────────────────────────
respuestas_recibidas = []

def on_feedback(topic, payload, **kwargs):
    """Callback que almacena las respuestas del sensor (simuladas)."""
    try:
        data = json.loads(payload.decode("utf-8"))
        respuestas_recibidas.append(data)
        print(f"\n[<-- FEEDBACK RECIBIDO] Topic: {topic}")
        print(f"    - Estado: {data.get('status')}")
        print(f"    - Salida: {data.get('output', '').strip()}")
    except Exception as e:
        print(f"[ERROR] Decodificando respuesta: {e}")


# ── Mock de la Pi 4 ─────────────────────────────────────────────────
BLACKLIST = ["rm -rf", "mkfs", "dd if=", ":(){", "shutdown", "reboot"]

def mock_pi4(client, topic_comandos, topic_out):
    """
    Se suscribe al topic de comandos dirigidos a la Pi 4 y responde
    automáticamente como si fuera el sensor real.
    """
    def handler(topic, payload, **kwargs):
        try:
            datos = json.loads(payload.decode("utf-8"))
            comando = datos.get("comando", "")
            print(f"\n[MOCK Pi4] Recibida orden: {comando}")

            # Evaluar blacklist
            bloqueado = any(b in comando for b in BLACKLIST)
            if bloqueado:
                status = "blocked"
                output = "DENEGADA: comando en Blacklist de seguridad"
            else:
                status = "success"
                output = f"(simulado) $ {comando}\n-- ejecución OK --"

            feedback = {
                "sensor": "Pi4-Felix",
                "accion": datos.get("accion"),
                "comando": comando,
                "status": status,
                "output": output,
            }
            time.sleep(0.5)
            print(f"[MOCK Pi4] Publicando feedback → {topic_out}  status={status}")
            client.publish(topic_out, feedback)
        except Exception as e:
            print(f"[MOCK ERROR] {e}")

    client.subscribe(topic_comandos, handler)
    print(f"[MOCK Pi4] Escuchando en {topic_comandos}")


# ── Test principal ───────────────────────────────────────────────────
def test():
    try:
        with open("config.yml", "r") as f:
            config = yaml.safe_load(f)

        ENDPOINT   = config["aws"]["endpoint"]
        CERT_PATH  = config["aws"]["cert_path"]
        KEY_PATH   = config["aws"]["key_path"]
        ROOT_CA    = config["aws"]["root_ca"]
        TOPIC_ACTIONS_BASE = config["mqtt"]["topic_actions_base"]
    except Exception as e:
        print(f"[ERROR] Cargando config: {e}")
        return

    # Usar Dashboard-SOC-Pi5 ya que es un client-ID autorizado en la Policy
    # y distinto al coordinador principal (Pi5-dani) que puede estar corriendo
    CLIENT_ID = "Dashboard-SOC-Pi5"

    client = AWSMqttClient(
        endpoint=ENDPOINT,
        cert_path=CERT_PATH,
        key_path=KEY_PATH,
        root_ca_path=ROOT_CA,
        client_id=CLIENT_ID,
    )

    TARGET = "Pi4-Felix"
    # Usar los topics autorizados en la Policy (seguridad/*)
    topic_comandos = f"{TOPIC_ACTIONS_BASE}{TARGET}"
    topic_out      = f"{TOPIC_ACTIONS_BASE}{TARGET}/out"

    try:
        print("=" * 60)
        print("  🛡️  TEST E2E – Bucle de Feedback SOC (Mock Pi4)")
        print("=" * 60)
        print(f"\n[INFO] Conectando con client-id={CLIENT_ID} ...")
        client.connect()

        # 1. Registrar Mock de la Pi 4
        mock_pi4(client, topic_comandos, topic_out)

        # 2. Escuchar las respuestas en el topic de salida
        feedback_topic = f"{TOPIC_ACTIONS_BASE}+/out"
        client.subscribe(feedback_topic, on_feedback)
        print(f"[INFO] Suscrito a {feedback_topic}")
        time.sleep(2)

        # ── Caso 1: comando seguro ───────────────────────────────
        cmd_safe = {
            "accion": "ejecutar_comando",
            "comando": "ls -la /tmp",
            "motivo": "Diagnóstico de integridad",
        }
        print(f"\n[--> ENVÍO] Comando seguro → {topic_comandos}")
        client.publish(topic_comandos, cmd_safe)
        print("[INFO] Esperando respuesta del Mock (5 s) ...")
        time.sleep(5)

        # ── Caso 2: comando peligroso ────────────────────────────
        cmd_bad = {
            "accion": "ejecutar_comando",
            "comando": "sudo rm -rf /etc",
            "motivo": "Verificar blacklist",
        }
        print(f"\n[--> ENVÍO] Comando peligroso → {topic_comandos}")
        client.publish(topic_comandos, cmd_bad)
        print("[INFO] Esperando respuesta del Mock (5 s) ...")
        time.sleep(5)

        # ── Resultado ────────────────────────────────────────────
        print("\n" + "=" * 60)
        print("  RESUMEN DEL TEST E2E")
        print("=" * 60)

        if len(respuestas_recibidas) >= 2:
            safe_ok = any(r.get("status") == "success" for r in respuestas_recibidas)
            block_ok = any(r.get("status") == "blocked" for r in respuestas_recibidas)
            if safe_ok and block_ok:
                print("[✅ SUCCESS] Ambos escenarios validados correctamente:")
                print("   - Comando seguro  → ejecutado (success)")
                print("   - Comando peligroso → bloqueado (blocked)")
            else:
                print("[⚠️  PARCIAL] Se recibieron 2 respuestas pero los estados no coinciden.")
        else:
            print(f"[❌ FAIL] Solo {len(respuestas_recibidas)}/2 respuestas recibidas.")

        for i, r in enumerate(respuestas_recibidas, 1):
            print(f"\n  Respuesta #{i}:")
            print(f"    sensor:  {r.get('sensor')}")
            print(f"    comando: {r.get('comando')}")
            print(f"    status:  {r.get('status')}")
            print(f"    output:  {r.get('output', '').strip()}")

    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        try:
            client.connection.disconnect().result()
            print("\n[INFO] Desconectado limpiamente.")
        except:
            pass
        print("[INFO] Fin de la prueba.\n")


if __name__ == "__main__":
    test()
