from aws_connector import AWSMqttClient
import yaml, time
with open("config.yml") as f:
    c = yaml.safe_load(f)

print("Connecting as Pi5-dani...")
client = AWSMqttClient(
    c["aws"]["endpoint"],
    c["aws"]["cert_path"].replace("./", ""),
    c["aws"]["key_path"].replace("./", ""),
    c["aws"]["root_ca"].replace("./", ""),
    "Pi5-dani"
)
client.connect()
print("Publishing as Pi5-dani...")
try:
    client.publish("seguridad/Pi4-Felix/comando", {"test": 1}, wait_for_ack=True)
    print("Success as Pi5-dani!")
except Exception as e:
    print(f"Failed: {e}")
client.disconnect()

print("\nConnecting as Dashboard-SOC-Pi5...")
client2 = AWSMqttClient(
    c["aws"]["endpoint"],
    c["aws"]["cert_path"].replace("./", ""),
    c["aws"]["key_path"].replace("./", ""),
    c["aws"]["root_ca"].replace("./", ""),
    "Dashboard-SOC-Pi5"
)
client2.connect()
print("Publishing as Dashboard-SOC-Pi5...")
try:
    client2.publish("seguridad/Pi4-Felix/comando", {"test": 1}, wait_for_ack=True)
    print("Success as Dashboard-SOC-Pi5!")
except Exception as e:
    print(f"Failed: {e}")
client2.disconnect()
