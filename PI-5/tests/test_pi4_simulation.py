import os
import sys
import json
import time
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from aws_connector import AWSMqttClient
import yaml

# Cargar configuración 
config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config.yml'))
with open(config_path, "r") as f:
    config = yaml.safe_load(f)

ENDPOINT  = config['aws']['endpoint']
CLIENT_ID = "Pi4-felix"  # 🎭 Usamos el DNI de la Pi 4 real permitido en la Policy de AWS para evitar la colisión de IDs con la Pi 5
CERT_PATH = os.path.join(os.path.dirname(__file__), '..', config['aws']['cert_path'])
KEY_PATH  = os.path.join(os.path.dirname(__file__), '..', config['aws']['key_path'])
ROOT_CA   = os.path.join(os.path.dirname(__file__), '..', config['aws']['root_ca'])

TOPIC_LOGS_OUT = "seguridad/Pi4-Sensor-01/logs"
TOPIC_CMD_IN   = "comandos/Pi4-Sensor-01"
TOPIC_FB_OUT   = "comandos/Pi4-Sensor-01/out"

# Callback cuando la Pi 5 (el Coordinator) nos manda un comando por MQTT
def on_command_received(topic, payload, **kwargs):
    print(f"\n[📥 RECIBIDO DE LA PI 5] Topic: {topic}")
    try:
        data = json.loads(payload.decode('utf-8')) if isinstance(payload, bytes) else json.loads(payload)
        
        # El Triage Agent suele mandar un JSON como {"command": "block_ip", "ip": "..."} o {"command": "sudo iptables..."}
        raw_cmd = data.get("command", str(data))
        ip_target = data.get("ip", "")
        
        print(f"👉 La IA de la Pi 5 ha ordenado ejecutar: {raw_cmd} {ip_target}")
        
        # 1. Simular la ejecución en la terminal de la Pi 4
        print(f"   [💻 TERMINAL PI 4] Aplicando orden del coordinador...")
        time.sleep(1) # Simular tiempo de SO
        
        # 2. Fabricar la respuesta realística que enviaría el sensor Pi 4
        response_dict = {
            "sensor": "Pi4-Sensor-01",
            "command": f"{raw_cmd} {ip_target}".strip(),
            "status": "success",
            "output": "Simulacion Exitosa: Reglas aplicadas correctamente en eth0."
        }
        
        # 3. Mandárselo de vuelta al Feedback Agent de la Pi 5
        print(f"   [📤 ENVIANDO FEEDBACK A LA PI 5] -> {TOPIC_FB_OUT}")
        mqtt_client.publish(TOPIC_FB_OUT, json.dumps(response_dict))
        
    except Exception as e:
        print(f"Error procesando comando entrante: {e}")

if __name__ == "__main__":
    print("==================================================================")
    print("   🛡️  SIMULADOR DE NODO EDGE (Raspberry Pi 4) E2E VIA AWS")
    print("==================================================================")
    
    mqtt_client = AWSMqttClient(
        endpoint=ENDPOINT,
        cert_path=CERT_PATH,
        key_path=KEY_PATH,
        root_ca_path=ROOT_CA,
        client_id=CLIENT_ID
    )
    
    # 1. Conectarnos y suscribirnos a las órdenes de la Pi 5
    mqtt_client.connect()
    mqtt_client.subscribe(TOPIC_CMD_IN, on_command_received)
    print(f"✅ Conectado a AWS y escuchando órdenes en: {TOPIC_CMD_IN}")
    
    # 2. Fabricar un Log de Inyección SQL y tirarlo a la red
    fake_attack_log = {
      "evento": "SQL_INJECTION",
      "prioridad": "CRITICA",
      "sensor": "Pi4-Sensor-01",
      "timestamp": "2026-04-16 20:00:00",
      "ip": "100.200.50.1",
      "usuario": "Anon",
      "email_raw": "admin' OR 1=1 --",
      "patron": "OR 1=1"
    }
    
    print(f"\n[💥 PI 4 BAJO ATAQUE] Enviando log de emergencia a la Pi 5...")
    mqtt_client.publish(TOPIC_LOGS_OUT, json.dumps(fake_attack_log))
    
    print("\n⏳ Esperando la respuesta del SOC (Pi 5) a través de AWS... (Pulsa Ctrl+C para salir)")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nApagando simulador.")
