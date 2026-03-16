# aws_connector.py
import json
import time
from awscrt import io, mqtt
from awsiot import mqtt_connection_builder

class AWSMqttClient:
    def __init__(self, endpoint, cert_path, key_path, root_ca_path, client_id):
        """
        Inicializa el cliente MQTT con los certificados de seguridad.
        """
        self.endpoint = endpoint
        self.cert_path = cert_path
        self.key_path = key_path
        self.root_ca_path = root_ca_path
        self.client_id = client_id
        self.connection = None

    def connect(self):
        """
        Establece la conexión segura mTLS con AWS IoT Core.
        """
        print(f"Iniciando conexión para el dispositivo: {self.client_id}...")
        mqtt_connection = mqtt_connection_builder.mtls_from_path(
            endpoint=self.endpoint,
            cert_filepath=self.cert_path,
            pri_key_filepath=self.key_path,
            ca_filepath=self.root_ca_path,
            client_id=self.client_id,
            clean_session=False,
            keep_alive_secs=30
        )
        connect_future = mqtt_connection.connect()
        connect_future.result() # Esperar a que la conexión sea exitosa
        self.connection = mqtt_connection
        print(f"¡{self.client_id} conectado con éxito a AWS!")

    def publish(self, topic, payload_dict):
        """
        Envía un mensaje JSON a un topic específico.
        """
        if not self.connection:
            print("Error: No hay conexión establecida.")
            return
        message_json = json.dumps(payload_dict)
        self.connection.publish(
            topic=topic,
            payload=message_json,
            qos=mqtt.QoS.AT_LEAST_ONCE
        )
        print(f"Publicado en '{topic}': {message_json}")

    def subscribe(self, topic, callback_function):
        """
        Se suscribe a un topic (útil para recibir órdenes del Coordinador).
        """
        if not self.connection:
            print("Error: No hay conexión establecida.")
            return
        print(f"Suscribiéndose a {topic}...")
        subscribe_future, packet_id = self.connection.subscribe(
            topic=topic,
            qos=mqtt.QoS.AT_LEAST_ONCE,
            callback=callback_function
        )
        subscribe_future.result()
        print(f"Suscrito exitosamente a {topic}")

# --- BLOQUE DE CONFIGURACIÓN PARA PI4-FELIX ---
if __name__ == '__main__':
    ENDPOINT = "aj4wsdnimoej8-ats.iot.eu-north-1.amazonaws.com"
    CLIENT_ID = "Pi4-Felix"
    cliente = AWSMqttClient(
        endpoint=ENDPOINT,
        cert_path="./Pi4-Felix.cert.pem",
        key_path="./Pi4-Felix.private.key",
        root_ca_path="./root-CA.crt",
        client_id=CLIENT_ID
    )
    try:
        cliente.connect()
        # Prueba de vida inicial
        cliente.publish("seguridad/cliente1/eventos", {"estado": "activo", "nodo": "Pi4-Felix"})
        time.sleep(2)
    except Exception as e:
        print(f"Error fatal en Pi4-Felix: {e}")