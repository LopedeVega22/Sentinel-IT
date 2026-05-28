# main_coordinator.py
import asyncio
import time
import json
import os
import yaml
import logging
import traceback
from logging.handlers import RotatingFileHandler
from aws_connector import AWSMqttClient
from agents.triage_agent.triage_agent import triage_agent
from agents.feedback_agent.feedback_agent import feedback_agent
from tools.iot_tools import init_iot_tools
from tools.pending_ai_events import (
    fetch_due_pending_ai_events,
    init_pending_ai_events_schema,
    is_resource_exhausted_error,
    mark_pending_ai_event_processed,
    mark_pending_ai_event_retry,
    save_pending_ai_event,
)

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

_DB_PATH_CFG = config['database']['db_path']
DB_PATH = _DB_PATH_CFG if os.path.isabs(_DB_PATH_CFG) else os.path.join(os.getcwd(), _DB_PATH_CFG)

# --- Queue Configuration ---
QUEUE_MAX_SIZE = config.get('queue', {}).get('max_size', 100)
AI_RETRY_POLL_SECONDS = config.get('queue', {}).get('ai_retry_poll_seconds', 30)
AI_RETRY_BATCH_SIZE = config.get('queue', {}).get('ai_retry_batch_size', 5)

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


# ===========================================================================
# Async Event Queue — Immediate Processing (Producer-Consumer)
# ===========================================================================
# Reference to the running asyncio event loop, set inside main().
# Used by the MQTT callback (which runs in an awscrt thread) to schedule
# work on the event loop in a thread-safe manner.
_loop: asyncio.AbstractEventLoop | None = None

# Queues are created inside main() once the event loop is running.
_triage_queue: asyncio.Queue | None = None
_feedback_queue: asyncio.Queue | None = None


def _enqueue_from_thread(queue: asyncio.Queue, device: str, raw_log: str):
    """
    Thread-safe bridge: schedules a put_nowait on the asyncio event loop.

    The MQTT callback from awscrt runs in a native thread, not in the
    asyncio loop.  `call_soon_threadsafe` is the canonical way to inject
    work from an external thread into a running event loop.
    """
    if _loop is None or _loop.is_closed():
        logger.warning("[QUEUE] Event loop not ready — dropping event")
        return
    try:
        _loop.call_soon_threadsafe(queue.put_nowait, (device, raw_log))
    except asyncio.QueueFull:
        logger.warning(f"[QUEUE] Backpressure! Queue full ({QUEUE_MAX_SIZE}) — dropping event from {device}")
    except Exception as e:
        logger.error(f"[QUEUE] Enqueue error: {e}")


async def _worker(queue: asyncio.Queue, runner: Runner, queue_type: str, session_id: str):
    """
    Single-consumer async worker: pulls events one-by-one from the queue
    and sends them to the ADK agent via run_async.

    - The first event that arrives is processed IMMEDIATELY (zero delay).
    - Subsequent events queue up and are processed as soon as the previous
      one completes.
    - Each agent type (triage / feedback) has its own worker, so they run
      in parallel.  Within a type, events are strictly sequential to
      preserve session context and avoid race conditions on the LLM.
    """
    logger.info(f"[{queue_type.upper()}] Async worker started (queue_max={QUEUE_MAX_SIZE})")
    while True:
        device, raw_log = await queue.get()
        try:
            logger.info(f"[{queue_type.upper()}] Processing event from {device}...")
            response_count = await _run_agent_event(device, raw_log, runner, queue_type, session_id)
            logger.info(f"[{queue_type.upper()}] Event processed ({response_count} responses)")

        except Exception as e:
            if is_resource_exhausted_error(e):
                event_id = save_pending_ai_event(
                    DB_PATH,
                    device=device,
                    queue_type=queue_type,
                    raw_log=raw_log,
                    error_reason=str(e),
                )
                logger.error(
                    f"[{queue_type.upper()}] Fallo modelo API: Gemini ha superado cuota/gasto. "
                    f"Evento guardado como PENDING_AI_RETRY (id={event_id})."
                )
            else:
                logger.error(f"[{queue_type.upper()}] Error processing event: {e}")
                logger.error(traceback.format_exc())
        finally:
            queue.task_done()


async def _run_agent_event(device: str, raw_log: str, runner: Runner, queue_type: str, session_id: str) -> int:
    event_type = "Log" if queue_type == "triage" else "Feedback"
    message = f"Nuevo {event_type} proveniente del dispositivo '{device}':\n{raw_log}"

    response_count = 0
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=session_id,
        new_message=types.Content(role="user", parts=[types.Part(text=message)])
    ):
        content = getattr(event, 'content', None)
        if content and getattr(content, 'parts', None):
            for part in content.parts:
                text = getattr(part, 'text', None)
                if text:
                    response_count += 1
                    logger.info(f"[{queue_type.upper()}] Agent response: {text[:200]}")

    return response_count


async def _pending_ai_retry_worker(session_id: str):
    logger.info(
        f"[AI_RETRY] Pending AI retry worker started "
        f"(poll={AI_RETRY_POLL_SECONDS}s, batch={AI_RETRY_BATCH_SIZE})"
    )
    runners = {
        "triage": _runner_triage,
        "feedback": _runner_feedback,
    }
    while True:
        try:
            due_events = fetch_due_pending_ai_events(DB_PATH, limit=AI_RETRY_BATCH_SIZE)
            for pending in due_events:
                event_id = pending["id"]
                queue_type = pending["queue_type"]
                runner = runners.get(queue_type)
                if runner is None:
                    mark_pending_ai_event_retry(
                        DB_PATH,
                        event_id=event_id,
                        error_reason=f"queue_type desconocido: {queue_type}",
                    )
                    continue

                try:
                    logger.info(
                        f"[AI_RETRY] Reintentando evento pendiente id={event_id} "
                        f"({queue_type}) de {pending['device']}"
                    )
                    response_count = await _run_agent_event(
                        pending["device"],
                        pending["raw_log"],
                        runner,
                        queue_type,
                        session_id,
                    )
                    mark_pending_ai_event_processed(DB_PATH, event_id)
                    logger.info(
                        f"[AI_RETRY] Evento pendiente id={event_id} procesado "
                        f"({response_count} responses)"
                    )
                except Exception as e:
                    if is_resource_exhausted_error(e):
                        mark_pending_ai_event_retry(DB_PATH, event_id, str(e))
                        logger.error(
                            f"[AI_RETRY] Fallo modelo API: Gemini sigue sin cuota/gasto. "
                            f"Evento id={event_id} queda como PENDING_AI_RETRY."
                        )
                    else:
                        mark_pending_ai_event_retry(DB_PATH, event_id, str(e))
                        logger.error(f"[AI_RETRY] Error reintentando evento id={event_id}: {e}")
                        logger.error(traceback.format_exc())
        except Exception as e:
            logger.error(f"[AI_RETRY] Error en worker de reintentos: {e}")
            logger.error(traceback.format_exc())

        await asyncio.sleep(AI_RETRY_POLL_SECONDS)


# ===========================================================================
# Normalizacion del feedback de PI-4
# ===========================================================================
# Truncado del stdout/stderr antes de pasarselo al LLM. PI-4 ya trunca a
# 4000 chars en su lado; aqui bajamos a 2000 para no inflar el contexto.
_OUTPUT_MAX_CHARS = 2000


def _truncate(text: str, limit: int = _OUTPUT_MAX_CHARS) -> str:
    text = text or ""
    return text if len(text) <= limit else text[:limit] + "...[truncado]"


def _normalize_pi4_feedback(data: dict):
    """
    Traduce las distintas formas en que PI-4 puede publicar feedback a un
    dict canonico de 5 campos: sensor, command, status, output, exitcode.

    Devuelve None si el payload no parece feedback reconocible — en ese caso
    el caller se queda con el JSON crudo (mejor que perderlo).
    """
    if not isinstance(data, dict):
        return None

    sensor = data.get("sensor") or data.get("dispositivo") or "Desconocido"
    command = data.get("comando") or data.get("command") or ""
    legacy_status = data.get("status")

    # Caso 1: rechazo por firma (no es ni exito ni fallo de mitigacion).
    if legacy_status == "rejected_signature":
        motivo = ""
        resultado = data.get("resultado")
        if isinstance(resultado, dict):
            motivo = resultado.get("error") or ""
        if not motivo:
            motivo = data.get("output") or ""
        return {
            "sensor": sensor,
            "command": command,
            "status": "rejected_signature",
            "output": _truncate(motivo),
            "exitcode": -1,
        }

    # Caso 2: forma nueva PI-4 v3 con dict 'resultado' anidado.
    resultado = data.get("resultado")
    if isinstance(resultado, dict):
        exitcode = resultado.get("exitcode")
        timed_out = bool(resultado.get("timed_out"))
        stdout = resultado.get("stdout") or ""
        stderr = resultado.get("stderr") or ""
        if timed_out:
            return {
                "sensor": sensor,
                "command": command,
                "status": "error",
                "output": _truncate(stderr or "timeout"),
                "exitcode": int(exitcode) if exitcode is not None else -1,
            }
        if exitcode == 0:
            return {
                "sensor": sensor,
                "command": command,
                "status": "success",
                "output": _truncate(stdout),
                "exitcode": 0,
            }
        return {
            "sensor": sensor,
            "command": command,
            "status": "error",
            "output": _truncate(stderr or stdout),
            "exitcode": int(exitcode) if exitcode is not None else -1,
        }

    # Caso 3: forma legacy plana (status + output sin nesting).
    if legacy_status is not None and "output" in data:
        status_lc = str(legacy_status).strip().lower()
        if status_lc in ("success", "ok", "exito", "éxito"):
            status_norm, exitcode = "success", 0
        elif status_lc in ("error", "fail", "failed", "fallo"):
            status_norm, exitcode = "error", 1
        else:
            status_norm, exitcode = status_lc or "error", -1
        return {
            "sensor": sensor,
            "command": command,
            "status": status_norm,
            "output": _truncate(str(data.get("output") or "")),
            "exitcode": exitcode,
        }

    return None


def _format_normalized_feedback(norm: dict) -> str:
    """Serializa el dict canonico como texto plano `clave: valor` para el LLM."""
    return (
        f"sensor: {norm['sensor']}\n"
        f"command: {norm['command']}\n"
        f"status: {norm['status']}\n"
        f"exitcode: {norm['exitcode']}\n"
        f"output: {norm['output']}"
    )


# ===========================================================================
# MQTT Callback
# ===========================================================================
def process_event(topic, payload, dup=None, qos=None, retain=None, **kwargs):
    """AWS IoT Callback: Receives the raw log and enqueues it for immediate processing."""
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
        # La autenticidad del comando ejecutado se garantiza criptograficamente
        # en PI-4 (firma Ed25519): si el sensor publica un feedback aqui es
        # porque la firma del comando fue valida -> no necesitamos verificar
        # round-trip a posteriori desde el coordinador.
        queue_type = "feedback" if topic.endswith("/respuesta") else "triage"

        # En la rama de feedback normalizamos el payload de PI-4 a un texto
        # plano y predecible para que el LLM no tenga que adivinar shapes.
        if queue_type == "feedback":
            norm = _normalize_pi4_feedback(data)
            if norm is not None:
                raw_log = _format_normalized_feedback(norm)

        queue = _feedback_queue if queue_type == "feedback" else _triage_queue

        logger.info(f"[MQTT] [{queue_type.upper()}] Event received from {source_device} on topic {topic} — queued")

        # Thread-safe enqueue into the asyncio event loop for immediate processing
        _enqueue_from_thread(queue, source_device, raw_log)

    except Exception as e:
        logger.error(f"[MQTT] Error in process_event: {e}")
        logger.error(traceback.format_exc())


# --- Program Entry Point ---
async def main():
    """Async entry point: sets up queues, workers, MQTT, and runs forever."""
    global _loop, _triage_queue, _feedback_queue

    init_pending_ai_events_schema(DB_PATH)

    # Capture the running event loop so the MQTT thread can enqueue work.
    _loop = asyncio.get_running_loop()

    # Create bounded async queues (backpressure)
    _triage_queue = asyncio.Queue(maxsize=QUEUE_MAX_SIZE)
    _feedback_queue = asyncio.Queue(maxsize=QUEUE_MAX_SIZE)

    # Create the ADK session (must be done inside an async context)
    session = await _session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID
    )
    logger.info(f"[INFO] ADK Session created: {session.id}")

    # --- MQTT Connection (sync, with retry backoff) ---
    global_iot_client = AWSMqttClient(
        endpoint=ENDPOINT,
        cert_path=CERT_PATH,
        key_path=KEY_PATH,
        root_ca_path=ROOT_CA,
        client_id=CLIENT_ID
    )

    connected = False
    retry_delay = 2
    max_delay = 60

    logger.info("[INFO] Conectando cliente IoT...")
    while not connected:
        try:
            global_iot_client.connect()
            connected = True
        except Exception as e:
            logger.warning(f"[WARNING] Fallo en la conexion inicial a AWS IoT: {e}. Reintentando en {retry_delay}s...")
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, max_delay)

    try:
        # Inject IoT client into ADK tools (Dependency Injection)
        init_iot_tools(global_iot_client)

        # Launch async workers (one per agent type — they run in parallel)
        triage_task = asyncio.create_task(
            _worker(_triage_queue, _runner_triage, "triage", session.id)
        )
        feedback_task = asyncio.create_task(
            _worker(_feedback_queue, _runner_feedback, "feedback", session.id)
        )
        retry_task = asyncio.create_task(
            _pending_ai_retry_worker(session.id)
        )

        # Subscribe to MQTT topics (callbacks fire in awscrt thread)
        global_iot_client.subscribe(TOPIC_SUBSCRIBE_TELEMETRIA, process_event)
        global_iot_client.subscribe(TOPIC_SUBSCRIBE_EVENTOS,    process_event)
        global_iot_client.subscribe(TOPIC_SUBSCRIBE_RESPUESTAS, process_event)

        logger.info("[INFO] Autonomous SOC (ADK Powered) Active.")
        logger.info(f"[INFO] Async queue mode: max_size={QUEUE_MAX_SIZE} (immediate processing)")
        logger.info("[INFO] Awaiting security logs via AWS IoT MQTT...")

        # Keep the event loop alive. gather() will also propagate worker
        # exceptions if a fatal error occurs in either worker.
        await asyncio.gather(triage_task, feedback_task, retry_task)

    except Exception as e:
        logger.critical(f"[CRITICAL] Fatal error in Coordinator: {e}")
        logger.critical(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(main())
