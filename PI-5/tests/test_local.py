import json
import time
import yaml
from aws_connector import AWSMqttClient

# Carga de configuracion para la conexion con AWS IoT
with open("config.yml", "r") as f:
    config = yaml.safe_load(f)

print("[INFO] Conectando a AWS IoT Core para inyeccion de log de prueba...")

# Instancia del cliente MQTT simulando un dispositivo remoto
client = AWSMqttClient(
    endpoint=config['aws']['endpoint'],
    cert_path=config['aws']['cert_path'],
    key_path=config['aws']['key_path'],
    root_ca_path=config['aws']['root_ca'],
    client_id="Pi4-felix"
)

client.connect()
time.sleep(2)

# Simulacion de un log de ataque de fuerza bruta SSH
fake_log = {
    "dispositivo": "Pi5-Simulador",
    "raw_log": "Mar 02 20:00:00 localhost sshd[9999]: Failed password for invalid user root from 185.122.9.88 port 3332 ssh2"
}

dest_topic = "seguridad/logs/Pi5-Simulador/ssh"

print(f"[ENVIO] Topic: {dest_topic}")
client.publish(dest_topic, json.dumps(fake_log))

print("[OK] Log enviado correctamente. Verifique el procesamiento en el dashboard.")
time.sleep(1)
