import yaml
import sys
import os
import time
import json
import threading
from aws_connector import AWSMqttClient

# Ajuste del path para importacion de modulos locales
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

respuestas_recibidas = []

def on_message_received(topic, payload, **kwargs):
    """Callback para almacenar respuestas del sensor (simuladas o reales)."""
    try:
        data = json.loads(payload.decode('utf-8'))
        respuestas_recibidas.append(data)
        print(f"\n[<-- FEEDBACK RECIBIDO] Topic: {topic}")
        print(f"    - Estado: {data.get('status')}")
        print(f"    - Salida: {data.get('output', '').strip()}")
    except Exception as e:
        print(f"[ERROR] Error decodificando respuesta: {e}")

def mock_pi4_behavior(client, topic_acciones, topic_out):
    """Simula el comportamiento de la Pi 4 para poder testear sin conexión física."""
    def on_mock_action(topic, payload, **kwargs):
        try:
            datos = json.loads(payload.decode('utf-8'))
            comando = datos.get("comando", "")
            print(f"\n[MOCK Pi 4] Recibida peticion de comando: {comando}")
            
            # Simular blacklist
            if "rm -rf" in comando:
                status = "blocked"
                output = "DENEGADA por seguridad (Blacklist simulada)"
            else:
                status = "success"
                output = "Simulacion de STDOUT exitosa"
                
            feedback_payload = {
                "sensor": "Pi4-Felix",
                "accion": datos.get("accion"),
                "comando": comando,
                "status": status,
                "output": output
            }
            time.sleep(1) # Simular tiempo de ejecucion
            print(f"[MOCK Pi 4] Enviando feedback a {topic_out}")
            client.publish(topic_out, feedback_payload)
        except Exception as e:
            print(f"[MOCK ERROR] {e}")
            
    client.subscribe(topic_acciones, on_mock_action)
    print(f"[MOCK Pi 4] Iniciado y escuchando en {topic_acciones}")

def test():
    """Prueba E2E Funcional: Envio de comandos y validacion de respuesta (con Mock de Pi 4)."""
    try:
        with open("config.yml", "r") as f:
            config = yaml.safe_load(f)
        
        ENDPOINT = config['aws']['endpoint']
        CLIENT_ID = "Pi5-dani-Tester"
        CERT_PATH = config['aws']['cert_path']
        KEY_PATH = config['aws']['key_path']
        ROOT_CA = config['aws']['root_ca']
        TOPIC_ACTIONS_BASE = config['mqtt']['topic_actions_base']
        
    except Exception as e:
        print(f"[ERROR] Fallo al cargar configuracion: {e}")
        return

    client = AWSMqttClient(
        endpoint=ENDPOINT,
        cert_path=CERT_PATH,
        key_path=KEY_PATH,
        root_ca_path=ROOT_CA,
        client_id=CLIENT_ID
    )
    
    try:
        print("[INFO] Conectando a AWS IoT Core para test E2E...")
        client.connect()
        
        target = "Pi4-Felix"
        topic_acciones = f"{TOPIC_ACTIONS_BASE}{target}"
        topic_out = f"comandos/{target}/out"
        
        # Iniciar el MOCK de la Pi 4 en background (se registra como callback en el mismo cliente)
        mock_pi4_behavior(client, topic_acciones, topic_out)
        
        # Suscribir al topic donde el sensor mandara la respuesta
        client.subscribe("comandos/+/out", on_message_received)
        print("[INFO] Suscrito a comandos/+/out esperando respuestas.")
        time.sleep(2) # Dar tiempo para suscribirse
        
        # Caso 1: Comando de diagnostico seguro
        good_command = {
            "accion": "ejecutar_comando",
            "comando": "ls -l /tmp",
            "motivo": "Verificacion de integracion segura"
        }
        print(f"\n[--> ENVIO] Comando seguro a {topic_acciones}: ls -l /tmp")
        client.publish(topic_acciones, good_command)
        
        # Esperar la respuesta (maximo 5 segundos)
        print("[INFO] Esperando ejecucion en el sensor (Mock Pi 4)...")
        time.sleep(5)
        
        # Caso 2: Comando restringido (debe ser bloqueado por la politica del sensor)
        bad_command = {
            "accion": "ejecutar_comando",
            "comando": "sudo rm -rf /etc",
            "motivo": "Verificacion de politicas de seguridad"
        }
        print(f"\n[--> ENVIO] Comando restringido a {topic_acciones}: sudo rm -rf /etc")
        client.publish(topic_acciones, bad_command)
        
        # Esperar la respuesta
        print("[INFO] Esperando evaluacion en el sensor (Mock Pi 4)...")
        time.sleep(5)
        
        print("\n================ RESUMEN DEL TEST E2E ================")
        if len(respuestas_recibidas) >= 2:
            print("[SUCCESS] El sensor simulado respondio a ambos comandos correctamente.")
            print("Se ha validado el bus MQTT y la logica de comunicacion sin necesidad de la Pi 4 fisica.")
        else:
            print(f"[WARNING] Solo se recibieron {len(respuestas_recibidas)} respuestas de 2 esperadas.")
            
    except Exception as e:
        print(f"[ERROR] Fallo en la simulacion: {e}")
    finally:
        print("[INFO] Fin de la prueba.")

if __name__ == "__main__":
    test()
