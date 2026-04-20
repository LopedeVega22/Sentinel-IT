import json
import time
from awscrt import io, mqtt
from awsiot import mqtt_connection_builder

class AWSMqttClient:
    """
    Cliente para la gestion de conexiones MQTT con AWS IoT Core mediante mTLS.
    """
    def __init__(self, endpoint, cert_path, key_path, root_ca_path, client_id):
        self.endpoint = endpoint
        self.cert_path = cert_path
        self.key_path = key_path
        self.root_ca_path = root_ca_path
        self.client_id = client_id
        self.connection = None

    def connect(self):
        """
        Establece la conexion segura con AWS IoT.
        """
        print(f"[INFO] Conectando cliente IoT: {self.client_id}")
        
        mqtt_connection = mqtt_connection_builder.mtls_from_path(
            endpoint=self.endpoint,
            cert_filepath=self.cert_path,
            pri_key_filepath=self.key_path,
            ca_filepath=self.root_ca_path,
            client_id=self.client_id,
            clean_session=False,
            keep_alive_secs=30
        )
        
        # Iniciar conexion asincrona
        connect_future = mqtt_connection.connect()
        connect_future.result() 
        
        self.connection = mqtt_connection
        print(f"[SUCCESS] Cliente [{self.client_id}] conectado con exito.")

    def publish(self, topic, payload_dict):
        """
        Publica un mensaje en formato JSON al topic especificado.
        """
        if not self.connection:
            print("[ERROR] No hay conexion activa.")
            return
        
        message_json = json.dumps(payload_dict)
        self.connection.publish(
            topic=topic,
            payload=message_json,
            qos=mqtt.QoS.AT_LEAST_ONCE
        )
        print(f"[INFO] Mensaje publicado en {topic}")

    def subscribe(self, topic, callback_function):
        """
        Suscribe el cliente a un topic y asigna una funcion de callback.
        """
        if not self.connection:
            print("[ERROR] Sin conexion para suscribir.")
            return

        subscribe_future, packet_id = self.connection.subscribe(
            topic=topic,
            qos=mqtt.QoS.AT_LEAST_ONCE,
            callback=callback_function
        )
        subscribe_future.result()
        print(f"[INFO] Suscrito a: {topic}")

if __name__ == '__main__':
    # Validacion rapida de conectividad
    ENDPOINT = "aj4wsdnimoej8-ats.iot.eu-north-1.amazonaws.com"
    CLIENT_ID = "Pi5-dani-test"
    
    client = AWSMqttClient(
        endpoint=ENDPOINT,
        cert_path="./Pi5-dani.cert.pem", 
        key_path="./Pi5-dani.private.key", 
        root_ca_path="./root-CA.crt", 
        client_id=CLIENT_ID
    )
    
    try:
        client.connect()
        client.publish("seguridad/test", {"status": "ready", "timestamp": time.time()})
        time.sleep(2)
    except Exception as e:
        print(f"[ERROR] Error en la prueba de conexion: {e}")

