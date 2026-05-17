---
title: "Arquitectura de Agentes IA - Sentinel-IT (PI-5)"
author: "Daniel Alarcon"
date: "2026-05-16"
tags: ["agents", "adk", "soc", "mqtt", "triage", "feedback", "policy-engine"]
---

# Arquitectura de Agentes IA

## 1. Propósito

Este documento describe **únicamente** el subsistema de agentes IA del coordinador SOC (PI-5): cómo se orquestan `SOC_Triage_Agent` y `SOC_Feedback_Agent`, qué herramientas exponen, cómo se acoplan al broker MQTT (AWS IoT Core) y cómo interactúan con el `Policy Engine`.

No cubre el HITL del dashboard (eso está en `HITL_Architecture.md`), ni la lógica interna del Policy Engine (`funcionamiento_policy_engine.md`), ni el protocolo MQTT global (`funcionamiento_mqtt.md`). Solo el "qué hacen los agentes y cuándo".

## 2. Componentes

### 2.1 SOC_Triage_Agent (`src/agents/triage_agent/triage_agent.py`)

- **Rol:** Analista SOC de Nivel 1. Es el primer agente que toca cualquier log que entra.
- **Modelo:** Configurable vía `AI_MODE` (`local` → Ollama; cualquier otro valor → Vertex/Gemini API).
- **Base de conocimiento:** carga `recommendations.json` al arrancar y lo inyecta literalmente en el `instruction` para tener un catálogo de comandos de referencia.
- **Tools expuestas:**
  - `register_alert(device, attack_vector, source_ip, severity, verdict, raw_log)` — escribe el incidente en SQLite. **Obligatoria una sola vez por amenaza confirmada.**
  - `execute_diagnostic_command(device, command, reason)` — diagnóstico de lectura. El Policy Engine decide: si es SAFE_READ se publica directo a `seguridad/<device>/comando`; cualquier otro nivel se redirige automáticamente al flujo HITL.
  - `request_mitigation_approval(device, mitigation_command, rationale)` — propuesta de mitigación. LOW/SAFE_READ auto-ejecutan, HIGH/CRITICAL quedan en cuarentena (`status='PENDING'`) para revisión humana en el dashboard.

### 2.2 SOC_Feedback_Agent (`src/agents/feedback_agent/feedback_agent.py`)

- **Rol:** Analista QA. Solo recibe **respuestas** de comandos ya ejecutados en el edge.
- **Modelo:** misma configuración que el triage.
- **Tools expuestas:**
  - `update_alert_status(device, command_result, mitigation_status)` — actualiza la última fila del dispositivo con `EXITO` o `FALLO`. **Obligatoria una sola vez por feedback.**
  - `execute_diagnostic_command` — si necesita más contexto tras un fallo.
  - `request_mitigation_approval` — si el comando original falló, puede proponer una alternativa. **Esa propuesta vuelve a pasar por el Policy Engine**, por lo que en la práctica reabre el ciclo aunque el agente que propone sea el de feedback (no es necesario reencolar al triage).

### 2.3 Runner ADK y sesión única

- Ambos agentes corren bajo `google.adk.runners.Runner`, compartiendo un único `InMemorySessionService` y una sesión creada al arrancar el coordinador.
- Cada agente tiene su propio `Runner`: `_runner_triage`, `_runner_feedback`.
- Esto se inicializa una sola vez en `main_coordinator.py` (líneas 64-81).

### 2.4 Cola de microbatch (`LogBatchQueue`)

Definida en `main_coordinator.py:87`. Una por agente (`_triage_queue`, `_feedback_queue`). Acumula logs y los flushea cuando ocurre **lo que pase primero**:

- **Trigger por volumen:** la cola alcanza `batch.max_size` (config.yml, default 10).
- **Trigger por tiempo:** han pasado `batch.flush_interval` segundos (default 15).

Cada cola tiene un hilo daemon (`_batch_dispatcher`) que comprueba estas condiciones cada segundo. Cuando se flushea, los entries se concatenan en un mensaje único que se manda al runner ADK correspondiente.

### 2.5 Policy Engine (resumen del acoplamiento)

El motor (`src/tools/policy_engine.py`) interviene en **tres puntos** del flujo de agentes:

1. **Capa 1 – Clasificación previa:** cuando el triage llama a `request_mitigation_approval` o a `execute_diagnostic_command`, el motor clasifica el comando y decide si auto-ejecuta o cuarentena.
2. **Capa 2 – Caché de despachos:** cada comando publicado al broker se anota en `_dispatch_cache` (TTL 5 min) con `policy_engine.record_dispatch(...)`.
3. **Capa 3 – Verificación round-trip:** al recibir un mensaje en `seguridad/<device>/respuesta`, el coordinador llama a `policy_engine.verify_feedback(executed_cmd, device)`. Si el resultado es `ANOMALY`, **no se encola al feedback_agent**; en su lugar se registra una alerta `INTRUSION-COMMAND-INJECTION` y el flujo se desvía al triage en la siguiente ronda.

## 3. Topics MQTT consumidos y producidos

| Topic | Dirección | Quién publica | Consumidor en PI-5 |
|-------|-----------|---------------|--------------------|
| `seguridad/<device>/telemetria` | PI-4 → PI-5 | Sensor PI-4 | `process_event` → `triage_queue` |
| `seguridad/<device>/evento` | PI-4 → PI-5 | Sensor PI-4 | `process_event` → `triage_queue` |
| `seguridad/<device>/respuesta` | PI-4 → PI-5 | Sensor PI-4 (tras ejecutar) | `process_event` → verify_feedback → `feedback_queue` |
| `seguridad/<device>/comando` | PI-5 → PI-4 | `execute_diagnostic_command` / `_auto_execute_low` | El sensor PI-4 lo recibe y ejecuta |

El enrutamiento por sufijo de topic está en `main_coordinator.py:226`:

```python
queue_type = "feedback" if topic.endswith("/respuesta") else "triage"
```

## 4. Diagrama de secuencia (camino feliz + fallo)

```
PI-4 sensor          PI-5 coordinator        Triage Agent      Policy Engine    PI-4 sensor       Feedback Agent
     │                       │                      │                  │                │                  │
     │  log evento (MQTT)    │                      │                  │                │                  │
     │──────────────────────▶│                      │                  │                │                  │
     │     seguridad/X/evento│                      │                  │                │                  │
     │                       │ encola en triage_queue                  │                │                  │
     │                       │ (flush por volumen o tiempo)            │                │                  │
     │                       │─────────────────────▶│                  │                │                  │
     │                       │  Runner.run(batch)   │                  │                │                  │
     │                       │                      │ register_alert   │                │                  │
     │                       │                      │ request_mitigation_approval(cmd) │                  │
     │                       │                      │──────────────────▶│ classify(cmd) │                  │
     │                       │                      │   LOW/SAFE_READ  │                │                  │
     │                       │                      │◀──────────────────│ auto-ejecutar │                  │
     │                       │ publish seguridad/X/comando             │                │                  │
     │                       │ + record_dispatch    │                  │                │                  │
     │◀──────────────────────│                      │                  │                │                  │
     │ ejecuta y responde    │                      │                  │                │                  │
     │──────────────────────▶│                      │                  │                │                  │
     │ seguridad/X/respuesta │                      │                  │                │                  │
     │                       │ verify_feedback ─── MATCH ─────────────▶│                │                  │
     │                       │ encola en feedback_queue                │                │                  │
     │                       │──────────────────────────────────────────────────────────│─────────────────▶│
     │                       │                      │                  │                │  update_alert_status
     │                       │                      │                  │                │   (EXITO o FALLO)
     │                       │                      │                  │                │       │
     │                       │                      │   si FALLO: feedback puede llamar request_mitigation_approval
     │                       │                      │   con un comando alternativo → vuelve a publicar a PI-4
```

Caso anómalo (Capa 3 detecta INTRUSION):

```
PI-4 sensor          PI-5 coordinator        Policy Engine     Triage Agent
     │ respuesta con comando que jamás se emitió                │
     │──────────────────────▶│ verify_feedback ─── ANOMALY ────▶│
     │                       │ register_alert(INTRUSION-COMMAND-INJECTION)
     │                       │ audit(event_type=ANOMALY)        │
     │                       │ ─── NO se encola al feedback ────│
     │                       │ (el triage lo verá en su próximo batch
     │                       │  como alerta INTRUSION para reaccionar)
```

## 5. Reglas críticas que cumple cada agente

### Triage
- Llamar `register_alert` **exactamente una vez** por amenaza confirmada.
- Después de `request_mitigation_approval` debe **parar** la ejecución de tools (queda en cuarentena humana si es HIGH/CRITICAL, o auto-ejecutado si LOW).
- Si recibe un log con `attack_vector="INTRUSION-COMMAND-INJECTION"`, no propone nuevos comandos sobre ese dispositivo: el razonamiento debe orientarse a rotar credenciales/certificados.

### Feedback
- Llamar `update_alert_status` **exactamente una vez** por evento de respuesta.
- Si `status="error"` puede proponer una alternativa via `request_mitigation_approval`. Si no tiene alternativa, termina su turno con un texto resumen.

## 6. Configuración relevante

`config.yml`:
- `batch.max_size` (default 10) — disparo por volumen.
- `batch.flush_interval` (default 15s) — disparo por tiempo.
- `mqtt.topic_subscribe_*` — patrones de suscripción del coordinador.
- `mqtt.topic_publish_comando` — plantilla con `{device}` que las tools sustituyen al publicar.

Variables de entorno:
- `AI_MODE=local` → usa `ollama/<model>` vía LiteLLM en `http://local-ai-engine:11434`.
- `AI_MODE=api` (o cualquier otra) → usa el `AI_MODEL` directo (Vertex / Gemini).
- `AI_MODEL` → nombre exacto del modelo.

## 7. Cómo probar el flujo

El test `tests/test_agent_flow.py` publica logs reales a `seguridad/<device>/evento`, espera el comando emitido por el coordinador en `seguridad/<device>/comando`, y simula tanto una respuesta `EXITO` como una `FALLO` en `seguridad/<device>/respuesta`. Sirve para validar el ciclo completo sin tener el PI-4 conectado.

## 8. Archivos involucrados

```
PI-5/
├── src/
│   ├── main_coordinator.py            # Orquestación (colas + dispatcher + MQTT)
│   ├── agents/
│   │   ├── triage_agent/
│   │   │   └── triage_agent.py
│   │   └── feedback_agent/
│   │       └── feedback_agent.py
│   └── tools/
│       ├── iot_tools.py               # execute_diagnostic_command, request_mitigation_approval
│       ├── db_tools.py                # register_alert, update_alert_status
│       └── policy_engine.py           # classify, decide, record_dispatch, verify_feedback, audit
└── tests/
    └── test_agent_flow.py             # Test E2E real (MQTT)
```
