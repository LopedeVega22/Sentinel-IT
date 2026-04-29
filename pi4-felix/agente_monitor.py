# agente_monitor.py
import time
import subprocess
import os
import json
import yaml
import logging
from logging.handlers import RotatingFileHandler
from aws_connector import AWSMqttClient

# Cargar configuración centralizada
with open("config.yml", "r") as f:
    config = yaml.safe_load(f)

# CONFIGURACIÓN PARA LA PI 4 (FELIX) - Desde config.yml
ENDPOINT = config['aws']['endpoint']
CLIENT_ID = config['aws']['client_id']
CERT_PATH = config['aws']['cert_path']
KEY_PATH = config['aws']['key_path']
ROOT_CA = config['aws']['root_ca']

TOPIC_LOGS_SSH = config['mqtt']['topic_logs']
TOPIC_ACCIONES = config['mqtt']['topic_acciones']

LOG_FILE = config['system']['log_file']

# --- CONFIGURACIÓN DE LÓGICA DE LOGGING ---
LOG_FILE_PATH = config['logging']['file_path']
LOG_LEVEL_STR = config['logging']['level']
LOG_MAX_BYTES = config['logging']['max_bytes']
LOG_BACKUP_COUNT = config['logging']['backup_count']

# Configurar el logger
numeric_level = getattr(logging, LOG_LEVEL_STR.upper(), logging.INFO)
logger = logging.getLogger("SensorSOC")
logger.setLevel(numeric_level)

handler = RotatingFileHandler(LOG_FILE_PATH, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Opcional: también imprimir a la consola para depuración rápida
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

def es_comando_seguro(comando: str) -> bool:
    """Verifica si un comando contiene palabras o herramientas prohibidas."""
    if not comando:
        return False
    
    # Lista negra de comandos peligrosos
    BLACKLIST = [
        "rm", "mkfs", "dd", "fdisk", "parted", "mkswap", 
        "reboot", "shutdown", "halt", "poweroff", 
        "init", "systemctl restart", "systemctl stop",
        ">", ">>", "wget", "curl", "nc", "netcat"
    ]
    
    cmd_lower = comando.lower()
    for trampa in BLACKLIST:
        # Busca coincidencias exactas de palabra o símbolos
        if f" {trampa} " in f" {cmd_lower} " or trampa in [">", ">>"]:
            logger.warning(f"BLOQUEADO POR BLACKLIST: Se detectó '{trampa}' en '{comando}'")
            return False
            
    return True

def procesar_accion_ia(topic, payload, **kwargs):
    """Callback que se ejecuta cuando el Coordinador (Pi5) manda una orden"""
    global cliente_global
    try:
        datos = json.loads(payload.decode('utf-8'))
        logger.info(f"[!] ORDEN RECIBIDA DE LA IA: {datos}")
        
        accion = datos.get("accion")
        resultado_ejecucion = ""
        estado_ejecucion = "PENDING"
        
        if accion == "bloquear_ip":
            ip = datos.get("ip")
            if ip:
                logger.warning(f"[*] Ejecutando bloqueo de IP en IPTables: {ip}")
                # os.system(f"sudo iptables -A INPUT -s {ip} -j DROP")
                logger.info(f"[-] Simulación: iptables -A INPUT -s {ip} -j DROP")
                resultado_ejecucion = f"IP {ip} bloqueada."
                estado_ejecucion = "success"
                
        elif accion == "ejecutar_comando":
            comando = datos.get("comando")
            motivo = datos.get("motivo", "Sin motivo")
            if comando:
                logger.warning(f"[*] Petición de ejecución remota: '{comando}' (Motivo: {motivo})")
                if es_comando_seguro(comando):
                    logger.info(f"[+] Comando aprobado. Ejecutando...")
                    try:
                        resultado = subprocess.run(comando, shell=True, check=True, 
                                                text=True, capture_output=True, timeout=10)
                        logger.info(f"[-] Salida STDOUT:\n{resultado.stdout}")
                        resultado_ejecucion = resultado.stdout
                        estado_ejecucion = "success"
                        if resultado.stderr:
                            logger.warning(f"[-] Salida STDERR:\n{resultado.stderr}")
                    except subprocess.TimeoutExpired:
                        logger.error(f"[!] El comando agotó el tiempo de espera (10s)")
                        resultado_ejecucion = "Timeout (10s)"
                        estado_ejecucion = "error"
                    except subprocess.CalledProcessError as e:
                        logger.error(f"[!] El comando devolvió un código de error {e.returncode}")
                        logger.error(f"[-] STDERR: {e.stderr}")
                        resultado_ejecucion = e.stderr or "Error desconocido"
                        estado_ejecucion = "error"
                else:
                    logger.error(f"[!] Ejecución DENEGADA por seguridad (Blacklist).")
                    resultado_ejecucion = "DENEGADA por seguridad (Blacklist)"
                    estado_ejecucion = "blocked"

        # Enviar feedback al coordinador
        if cliente_global:
            feedback_payload = {
                "sensor": CLIENT_ID,
                "accion": accion,
                "comando": datos.get("comando", ""),
                "status": estado_ejecucion,
                "output": resultado_ejecucion
            }
            topic_out = f"comandos/{CLIENT_ID}/out"
            logger.info(f"[*] Publicando feedback en {topic_out}")
            cliente_global.publish(topic_out, feedback_payload)
            
    except Exception as e:
        logger.error(f"Error procesando la accion: {e}")

def follow_log(filename):
    """Generador que simula el comando 'tail -F' en Python"""
    # Si estamos probando en Windows y el fichero no existe, usamos uno de prueba
    if not os.path.exists(filename):
        logger.warning(f"No existe {filename}. Creando uno de prueba local...")
        with open("auth_test.log", "w") as f:
            f.write("Iniciando log de prueba...\n")
        filename = "auth_test.log"

    with open(filename, "r") as file:
        file.seek(0, os.SEEK_END) # Ir al final del fichero
        while True:
            line = file.readline()
            if not line:
                time.sleep(0.5) # Esperar a que entren nuevos logs
                continue
            yield line

cliente_global = None

def iniciar_agente():
    global cliente_global
    cliente = AWSMqttClient(
        endpoint=ENDPOINT,
        cert_path=CERT_PATH,
        key_path=KEY_PATH,
        root_ca_path=ROOT_CA,
        client_id=CLIENT_ID
    )
    cliente_global = cliente

    try:
        cliente.connect()
        logger.info(f"Agente de Seguridad iniciado en {CLIENT_ID}.")
        
        # Suscribir al canal de acciones para recibir los bloqueos
        cliente.subscribe(TOPIC_ACCIONES, procesar_accion_ia)
        
        logger.info(f"Monitoreando logs SSH en tiempo real: {LOG_FILE}...")
        
        # Leer constantemente el final del archivo auth.log
        for linea_log in follow_log(LOG_FILE):
            # Filtrar: Solo nos interesan líneas relacionadas con sshd, especialmente fallos
            if "sshd" in linea_log and ("Failed password" in linea_log or "Invalid user" in linea_log):
                
                datos = {
                    "dispositivo": CLIENT_ID,
                    "servicio": "ssh",
                    "raw_log": linea_log.strip(),
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                }
                
                # Publicar crudo en AWS
                logger.warning(f"Capturado evento SSH sospechoso -> Enviando a AWS...")
                cliente.publish(TOPIC_LOGS_SSH, datos)

    except Exception as e:
        logger.error(f"Error en el agente SOC: {e}")

if __name__ == "__main__":
    iniciar_agente()
