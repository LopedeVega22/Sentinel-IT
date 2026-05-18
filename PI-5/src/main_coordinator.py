# main_coordinator.py
import time
import json
import os
import yaml
import logging
import traceback
import threading
from logging.handlers import RotatingFileHandler
from aws_connector import AWSMqttClient
from agents.triage_agent.triage_agent import triage_agent
from agents.feedback_agent.feedback_agent import feedback_agent
from tools.iot_tools import init_iot_tools
from tools import policy_engine
from tools.db_tools import register_alert, mark_mitigation_result

# ADK imports (google-adk >= 0.3)
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Load centralized YAML configuration
with open("config.yml", "r") as f:
    config = yaml.safe_load(f)

# --- AWS IoT Configuration ---
ENDPOINT             = config['aws']['endpoint']
CLIENT_ID            = config['aws']['client_id']
CERT_PATH            = config['aws']['cert_path']
KEY_PATH             = config['aws']['key_path']
ROOT_CA              = config['aws']['root_ca']
TOPIC_SUBSCRIBE_TELEMETRIA = config['mqtt']['topic_subscribe_telemetria']
TOPIC_SUBSCRIBE_EVENTOS    = config['mqtt']['topic_subscribe_eventos']
TOPIC_SUBSCRIBE_RESPUESTAS = config['mqtt']['topic_subscribe_respuestas']

# --- Batch Configuration ---
BATCH_MAX_SIZE      = config.get('batch', {}).get('max_size', 10)
BATCH_FLUSH_INTERVAL = config.get('batch', {}).get('flush_interval', 15)

# --- Logging Configuration ---
LOG_FILE_PATH    = config['logging']['file_path']
LOG_LEVEL_STR    = config['logging']['level']
LOG_MAX_BYTES    = config['logging']['max_bytes']
LOG_BACKUP_COUNT = config['logging']['backup_count']

numeric_level = getattr(logging, LOG_LEVEL_STR.upper(), logging.INFO)
logger = logging.getLogger("CoordinatorSOC")
logger.setLevel(numeric_level)

handler = RotatingFileHandler(LOG_FILE_PATH, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# --- Initialize ADK Runner once at startup ---
import asyncio

APP_NAME = "soc_coordinator"
USER_ID  = "soc_admin"

_session_service = InMemorySessionService()
_runner_triage = Runner(
    app_name=APP_NAME,
    agent=triage_agent,
    session_service=_session_service,
)

_runner_feedback = Runner(
    app_name=APP_NAME,
    agent=feedback_agent,
    session_service=_session_service,
)

# Pre-create the session at startup (ADK requires it to exist before use)
_session = asyncio.run(
    _session_service.create_session(app_name=APP_NAME, user_id=USER_ID)
)
logger.info(f"[INFO] ADK Session created: {_session.id}")


# ===========================================================================
# Dual-Trigger Microbatch Queue
# ===========================================================================
class LogBatchQueue:
    """
    Thread-safe queue that accumulates incoming logs and flushes them
    to the ADK agent in batches. Flush triggers:
      1. Queue reaches max_size logs  (volume trigger)
      2. flush_interval seconds pass  (time trigger)
    Whichever condition is met first.
    """

    def __init__(self, max_size: int, flush_interval: int):
        self._queue: list[dict] = []
        self._lock = threading.Lock()
        self._max_size = max_size
        self._flush_interval = flush_interval
        self._last_flush = time.time()

    def add(self, device: str, raw_log: str):
        """Enqueue a log entry. If max_size is reached, return True to signal immediate flush."""
        with self._lock:
            self._queue.append({"device": device, "raw_log": raw_log})
            return len(self._queue) >= self._max_size

    def flush(self) -> list[dict]:
        """Atomically drain the queue and return all pending entries."""
        with self._lock:
            batch = list(self._queue)
            self._queue.clear()
            self._last_flush = time.time()
            return batch

    def size(self) -> int:
        with self._lock:
            return len(self._queue)

    def seconds_since_flush(self) -> float:
        return time.time() - self._last_flush

    @property
    def flush_interval(self) -> int:
        return self._flush_interval


# Global batch queues
_triage_queue = LogBatchQueue(max_size=BATCH_MAX_SIZE, flush_interval=BATCH_FLUSH_INTERVAL)
_feedback_queue = LogBatchQueue(max_size=BATCH_MAX_SIZE, flush_interval=BATCH_FLUSH_INTERVAL)


def _format_batch_message(batch: list[dict], queue_type: str) -> str:
    """Formats a list of log entries into a single message for the ADK agent."""
    event_type = "Log" if queue_type == "triage" else "Feedback"
    
    if len(batch) == 1:
        entry = batch[0]
        return f"Nuevo {event_type} proveniente del dispositivo '{entry['device']}':\n{entry['raw_log']}"

    lines = [f"Batch de {len(batch)} eventos ({event_type}) interceptados. Analiza CADA uno individualmente:\n"]
    for i, entry in enumerate(batch, 1):
        lines.append(f"[{i}] Dispositivo: {entry['device']} | Data: {entry['raw_log']}")
    return "\n".join(lines)


def _process_batch(batch: list[dict], runner: Runner, queue_type: str):
    """Sends a batch of logs to the ADK agent as a single message."""
    try:
        message = _format_batch_message(batch, queue_type)
        logger.info(f"[{queue_type.upper()}] Flushing {len(batch)} event(s) to ADK agent...")

        response_stream = runner.run(
            user_id=USER_ID,
            session_id=_session.id,
            new_message=types.Content(role="user", parts=[types.Part(text=message)])
        )

        responses = []
        for event in response_stream:
            content = getattr(event, 'content', None)
            if content and getattr(content, 'parts', None):
                for part in content.parts:
                    text = getattr(part, 'text', None)
                    if text:
                        responses.append(text)

        logger.info(f"[{queue_type.upper()}] Transaction complete. Responses: {len(responses)}")

    except Exception as e:
        logger.error(f"[{queue_type.upper()}] Error processing batch: {e}")
        logger.error(traceback.format_exc())


def _batch_dispatcher(queue: LogBatchQueue, runner: Runner, queue_type: str):
    """
    Background daemon thread. Checks the queue every second and flushes
    when either the volume threshold or time threshold is reached.
    """
    logger.info(f"[{queue_type.upper()}] Dispatcher started (max_size={BATCH_MAX_SIZE}, interval={BATCH_FLUSH_INTERVAL}s)")
    while True:
        time.sleep(1)
        try:
            queue_size = queue.size()
            if queue_size == 0:
                continue

            time_trigger = queue.seconds_since_flush() >= queue.flush_interval
            size_trigger = queue_size >= BATCH_MAX_SIZE

            if time_trigger or size_trigger:
                trigger_reason = "SIZE" if size_trigger else "TIMER"
                logger.info(f"[{queue_type.upper()}] Trigger: {trigger_reason} (queue={queue_size})")
                batch = queue.flush()
                if batch:
                    _process_batch(batch, runner, queue_type)
        except Exception as e:
            logger.error(f"[{queue_type.upper()}] Dispatcher error: {e}")
            logger.error(traceback.format_exc())


# ===========================================================================
# MQTT Callback
# ===========================================================================
def process_event(topic, payload, **kwargs):
    """AWS IoT Callback: Receives the raw log and enqueues it for batch processing."""
    try:
        data = json.loads(payload.decode('utf-8'))

        # Handle double-serialized JSON
        if isinstance(data, str):
            data = json.loads(data)

        # Detectar el nombre del dispositivo origen (soporte legacy y nuevo)
        source_device = data.get("dispositivo") or data.get("sensor") or "Desconocido"
        
        # Si el payload es un JSON completo sin envoltura de `raw_log`, tratar todo el JSON como el log a parsear
        if "raw_log" in data and isinstance(data["raw_log"], str):
            raw_log = data.get("raw_log", "")
        else:
            raw_log = json.dumps(data, indent=2, ensure_ascii=False)
            
        # Las respuestas a comandos llegan a `seguridad/<device>/respuesta` y se enrutan
        # al feedback_agent. Telemetría y eventos van al triage_agent.
        queue_type = "feedback" if topic.endswith("/respuesta") else "triage"

        # --- Capa 3 del Policy Engine: round-trip verification ---
        # Antes de encolar un feedback al feedback_agent, comprobamos que el
        # comando que dice haberse ejecutado en PI-4 fue emitido desde aqui.
        # Si no, levantamos un incidente INTRUSION-COMMAND-INJECTION y NO lo
        # tratamos como feedback (de lo contrario, contaminariamos el estado
        # de las mitigaciones legitimas con resultados de ordenes ajenas).
        if queue_type == "feedback":
            executed_cmd = data.get("comando") or data.get("command") or ""
            if executed_cmd:
                match = policy_engine.match_feedback(executed_cmd, source_device)
                if match is None:
                    logger.warning(
                        f"[POLICY] Round-trip ANOMALY desde {source_device}: comando "
                        f"'{executed_cmd}' no fue emitido por el coordinador."
                    )
                    try:
                        register_alert(
                            device=source_device,
                            attack_vector="INTRUSION-COMMAND-INJECTION",
                            source_ip="127.0.0.1",
                            severity="Critica",
                            verdict=(
                                "El sensor reporto la ejecucion de un comando que "
                                "el coordinador nunca emitio. Posible inyeccion via "
                                "credenciales filtradas o suplantacion."
                            ),
                            raw_log=raw_log,
                        )
                    except Exception as alert_err:
                        logger.error(f"[POLICY] No se pudo registrar la alerta INTRUSION: {alert_err}")
                    policy_engine.audit(
                        event_type="ANOMALY",
                        device=source_device,
                        command=executed_cmd,
                        classification=None,
                        decision_reason="Comando no presente en cache de despachos",
                    )
                    return  # No encolamos: se ha tratado como incidente, no como feedback.

                # Round-trip OK: escribimos estado_mitigacion DIRECTAMENTE en la
                # fila original (log_id conocido por el dispatch cache). Esto
                # es la "via rapida" que permite al dashboard ver el resultado
                # en el siguiente poll (~1 s) sin esperar al flush del batch
                # del feedback_agent ni a la latencia del LLM. El agente sigue
                # recibiendo el evento para su analisis posterior.
                if match.get("log_id") is not None:
                    pi4_status = (data.get("status") or "").lower()
                    if pi4_status in ("success", "ok", "exito", "éxito"):
                        mitigation_status = "EXITO"
                    elif pi4_status in ("error", "fail", "failed", "fallo"):
                        mitigation_status = "FALLO"
                    else:
                        mitigation_status = "EXITO" if not data.get("error") else "FALLO"
                    output = (
                        data.get("output")
                        or data.get("salida")
                        or data.get("resultado")
                        or ""
                    )
                    try:
                        mark_mitigation_result(
                            log_id=match["log_id"],
                            mitigation_status=mitigation_status,
                            command_result=str(output)[:2000],
                        )
                    except Exception as fast_err:
                        logger.error(f"[POLICY] Fast-path mitigation update fallo: {fast_err}")

        queue = _feedback_queue if queue_type == "feedback" else _triage_queue

        logger.info(f"[MQTT] [{queue_type.upper()}] Event received from {source_device} on topic {topic} — queued")

        # Enqueue the log — if threshold reached, signal immediate flush
        should_flush = queue.add(source_device, raw_log)
        if should_flush:
            logger.info(f"[{queue_type.upper()}] Volume threshold reached ({BATCH_MAX_SIZE}) — triggering immediate flush")

    except Exception as e:
        logger.error(f"[MQTT] Error in process_event: {e}")
        logger.error(traceback.format_exc())


# --- Program Entry Point ---
if __name__ == "__main__":

    global_iot_client = AWSMqttClient(
        endpoint=ENDPOINT,
        cert_path=CERT_PATH,
        key_path=KEY_PATH,
        root_ca_path=ROOT_CA,
        client_id=CLIENT_ID
    )

    try:
        global_iot_client.connect()

        # Inject IoT client into ADK tools (Dependency Injection)
        init_iot_tools(global_iot_client)

        # Start the batch dispatcher daemon threads
        triage_thread = threading.Thread(target=_batch_dispatcher, args=(_triage_queue, _runner_triage, "triage"), daemon=True)
        feedback_thread = threading.Thread(target=_batch_dispatcher, args=(_feedback_queue, _runner_feedback, "feedback"), daemon=True)
        triage_thread.start()
        feedback_thread.start()

        global_iot_client.subscribe(TOPIC_SUBSCRIBE_TELEMETRIA, process_event)
        global_iot_client.subscribe(TOPIC_SUBSCRIBE_EVENTOS,    process_event)
        global_iot_client.subscribe(TOPIC_SUBSCRIBE_RESPUESTAS, process_event)

        logger.info("[INFO] Autonomous SOC (ADK Powered) Active.")
        logger.info(f"[INFO] Batch mode: max_size={BATCH_MAX_SIZE}, flush_interval={BATCH_FLUSH_INTERVAL}s")
        logger.info("[INFO] Awaiting security logs via AWS IoT MQTT...")

        while True:
            time.sleep(1)

    except Exception as e:
        logger.critical(f"[CRITICAL] Fatal error in Coordinator: {e}")
        logger.critical(traceback.format_exc())