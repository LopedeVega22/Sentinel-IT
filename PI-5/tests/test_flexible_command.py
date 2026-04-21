import yaml
import sys
import os
from aws_connector import AWSMqttClient

# Ajuste del path para importacion de modulos locales
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

def test():
    """Prueba de envio de comandos seguros y maliciosos via MQTT."""
    try:
        with open("config.yml", "r") as f:
            config = yaml.safe_load(f)
        
        ENDPOINT = config['aws']['endpoint']
        CLIENT_ID = "Pi4-felix"
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
        print("[INFO] Conectando a AWS IoT Core para testeo de comandos...")
        client.connect()
        
        target = "Pi4-Felix"
        topic = f"{TOPIC_ACTIONS_BASE}{target}"
        
        # Caso 1: Comando de diagnostico seguro
        good_command = {
            "accion": "ejecutar_comando",
            "comando": "ls -l /tmp",
            "motivo": "Verificacion de integracion segura"
        }
        print(f"[ENVIO] Comando seguro a {topic}: ls -l /tmp")
        client.publish(topic, good_command)
        
        # Caso 2: Comando restringido (debe ser bloqueado por la politica del sensor)
        bad_command = {
            "accion": "ejecutar_comando",
            "comando": "sudo rm -rf /etc",
            "motivo": "Verificacion de politicas de seguridad"
        }
        print(f"[ENVIO] Comando restringido a {topic}: sudo rm -rf /etc")
        client.publish(topic, bad_command)
        
        print("[INFO] Pruebas finalizadas. Verifique el filtrado en los logs del dispositivo remoto.")
        
    except Exception as e:
        print(f"[ERROR] Fallo en la simulacion: {e}")

if __name__ == "__main__":
    test()
