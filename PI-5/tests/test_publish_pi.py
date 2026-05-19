import sys
import os
import yaml
import traceback

# Añadir directorios padre y src a sys.path para importaciones
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from aws_connector import AWSMqttClient

def main():
    # Detectar si estamos dentro del contenedor docker o en host para rutas
    in_docker = os.path.exists("/app/config.yml")
    base_path = "/app" if in_docker else os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    config_file = os.path.join(base_path, "config.yml")
    config = yaml.safe_load(open(config_file))
    
    c = AWSMqttClient(
        endpoint=config['aws']['endpoint'],
        cert_path=os.path.join(base_path, "certificados/Pi5-dani.cert.pem"),
        key_path=os.path.join(base_path, "certificados/Pi5-dani.private.key"),
        root_ca_path=os.path.join(base_path, "certificados/root-CA.crt"),
        client_id='Dashboard-SOC-Pi5'
    )
    
    print("Initiating connection...")
    c.connect()
    print("Connected successfully!")
    
    try:
        print("Attempting publish with wait_for_ack=True...")
        c.publish('seguridad/Pi4-Felix/comando', {'test': 'test'}, wait_for_ack=True)
        print("Publish successful!")
    except Exception as e:
        print("\n--- Exception Caught ---")
        print(f"Type: {type(e)}")
        print(f"Message: '{e}'")
        print("Traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    main()
