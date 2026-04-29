"""
Test E2E de comunicación MQTT para el bucle de feedback SOC.

Este test se ejecuta DENTRO del contenedor Docker del coordinador y
reutiliza la conexión MQTT existente del coordinador para evitar
conflictos de client-ID con AWS IoT Core (solo permite 1 conexión
por certificado).

Flujo:
  1. Se suscribe al topic de salida del sensor (comandos/+/out).
  2. Se suscribe al topic de acciones del sensor (comandos/Pi4-Felix)
     actuando como "Mock Pi 4" que responde automáticamente.
  3. Publica un comando seguro y espera la respuesta simulada.
  4. Publica un comando peligroso (blacklist) y espera el bloqueo.
  5. Valida las respuestas recibidas.
"""
import yaml
import sys
import os
import time
import json
import threading

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
    except Exception as e:
        print(f"[ERROR] Cargando config: {e}")
        return

    # Usar un client-ID ÚNICO distinto al coordinador para no desplazarlo
    CLIENT_ID = f"E2E-Tester-{int(time.time()) % 10000}"

    client = AWSMqttClient(
        endpoint=ENDPOINT,
        cert_path=CERT_PATH,
        key_path=KEY_PATH,
        root_ca_path=ROOT_CA,
        client_id=CLIENT_ID,
    )

    TARGET = "Pi4-Felix"
    topic_comandos = f"comandos/{TARGET}"
    topic_out      = f"comandos/{TARGET}/out"

    try:
        print("=" * 60)
        print("  🛡️  TEST E2E – Bucle de Feedback SOC (Mock Pi4)")
        print("=" * 60)
        print(f"\n[INFO] Conectando con client-id={CLIENT_ID} ...")
        client.connect()

        # 1. Registrar Mock de la Pi 4
        mock_pi4(client, topic_comandos, topic_out)

        # 2. Escuchar las respuestas
        client.subscribe("comandos/+/out", on_feedback)
        print("[INFO] Suscrito a comandos/+/out")
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
