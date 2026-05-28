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
  - `request_mitigation_approval(device, mitigation_command, rationale, revert_command="")` — propuesta de mitigación. Solo SAFE_READ se publica directo; LOW/HIGH/CRITICAL quedan en cuarentena (`status='PENDING'`) para revisión humana en el dashboard. Si el agente conoce un rollback real, lo pasa en `revert_command`; si no lo conoce, lo deja vacío.

### 2.2 SOC_Feedback_Agent (`src/agents/feedback_agent/feedback_agent.py`)

- **Rol:** Analista QA. Solo recibe **respuestas** de comandos ya ejecutados en el edge.
- **Modelo:** misma configuración que el triage.
- **Tools expuestas:**
  - `update_alert_status(device, command_result, mitigation_status)` — actualiza la última fila del dispositivo con `EXITO` o `FALLO`. **Obligatoria una sola vez por feedback.**
  - `execute_diagnostic_command` — si necesita más contexto tras un fallo.
  - `request_mitigation_approval` — si el comando original falló, puede proponer una alternativa. **Esa propuesta vuelve a pasar por el Policy Engine**, por lo que en la práctica reabre el ciclo aunque el agente que propone sea el de feedback (no es necesario reencolar al triage). Igual que triage, debe adjuntar `revert_command` solo cuando el rollback sea concreto.

### 2.3 Runner ADK y sesión única

- Ambos agentes corren bajo `google.adk.runners.Runner`, compartiendo un único `InMemorySessionService` y una sesión creada al arrancar el coordinador.
- Cada agente tiene su propio `Runner`: `_runner_triage`, `_runner_feedback`.
- Esto se inicializa una sola vez ### 2.4 Cola asíncrona (`asyncio.Queue`) con Procesamiento Inmediato

Definida en `main_coordinator.py:79`. Una por agente (`_triage_queue`, `_feedback_queue`). Permite el procesamiento de eventos en tiempo real:

- **Procesamiento Inmediato**: El primer evento que entra se procesa a los 0ms de llegar mediante `runner.run_async()`.
- **Encolamiento**: Si llega un nuevo evento mientras la IA está ocupada con una inferencia, este se guarda en la cola y se procesa secuencialmente tan pronto termine la inferencia actual.
- **Backpressure**: Para evitar el consumo desmedido de memoria ante ráfagas, las colas están acotadas a `queue.max_size` (config.yml, default 100). Si la cola se llena, los nuevos eventos se descartan de forma segura.

### 2.5 Persistencia de eventos pendientes por fallo de IA remota

El coordinador no considera que un evento se haya perdido solo porque el modelo remoto falle. Si `runner.run_async()` lanza un error de cuota/gasto de Gemini (`429 RESOURCE_EXHAUSTED`), `main_coordinator.py` no descarta el evento: lo guarda en SQLite mediante `src/tools/pending_ai_events.py`.

Flujo aplicado:

1. El evento llega por MQTT y entra en `_triage_queue` o `_feedback_queue`.
2. El worker intenta procesarlo con el agente ADK correspondiente.
3. Si Gemini devuelve `429 RESOURCE_EXHAUSTED`, se crea una fila en `pending_ai_events` con `status='PENDING_AI_RETRY'`.
4. `_pending_ai_retry_worker()` revisa periodicamente los pendientes vencidos y los reintenta con el mismo agente.
5. Si el reintento funciona, la fila pasa a `PROCESSED`; si vuelve a fallar, aumenta `retry_count` y retrasa `next_retry_at`.

Esto mantiene el diseno decidido para el proyecto:

- No hay fallback automatico a modelo local.
- No se cambia de modelo a escondidas.
- El evento queda retenido y visible hasta que pueda procesarse o hasta que el operador limpie el sistema.

Backoff actual:

| Intento fallido | Siguiente reintento |
|-----------------|---------------------|
| 1 | 1 minuto |
| 2 | 5 minutos |
| 3 | 15 minutos |
| 4+ | 1 hora |

### 2.6 Policy Engine (resumen del acoplamiento)

El motor (`src/tools/policy_engine.py`) interviene en **dos puntos** del flujo de agentes:

1. **Capa 1 – Clasificación previa:** cuando el triage llama a `request_mitigation_approval` o a `execute_diagnostic_command`, el motor clasifica el comando y decide si es lectura directa (`SAFE_READ`) o cuarentena HITL.
2. **Capa 2 – Auditoría:** cada decisión queda en `audit_log` mediante `policy_engine.audit(...)`.

La autenticidad del comando ya no depende de una caché reactiva de despachos: PI-5 firma cada payload con Ed25519 y PI-4 verifica firma, expiración y nonce antes de ejecutar.

## 3. Topics MQTT consumidos y producidos

| Topic | Dirección | Quién publica | Consumidor en PI-5 |
|-------|-----------|---------------|--------------------|
| `seguridad/<device>/telemetria` | PI-4 → PI-5 | Sensor PI-4 | `process_event` → `_enqueue_from_thread` → `triage_queue` |
| `seguridad/<device>/evento` | PI-4 → PI-5 | Sensor PI-4 | `process_event` → `_enqueue_from_thread` → `triage_queue` |
| `seguridad/<device>/respuesta` | PI-4 → PI-5 | Sensor PI-4 (tras ejecutar o rechazar firma) | `process_event` → normalización → `_enqueue_from_thread` → `feedback_queue` |
| `seguridad/<device>/comando` | PI-5 → PI-4 | `execute_diagnostic_command` / `_auto_execute_low` / dashboard HITL | El sensor PI-4 verifica firma y ejecuta |

El enrutamiento por sufijo de topic está en `main_coordinator.py:281`:

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
      │                       │ (procesado al instante)                 │                │                  │
      │                       │─────────────────────▶│                  │                │                  │
      │                       │ Runner.run_async()   │                  │                │                  │
      │                       │                      │ register_alert   │                │                  │
      │                       │                      │ request_mitigation_approval(cmd) │                  │
      │                       │                      │──────────────────▶│ classify(cmd) │                  │
      │                       │                      │   SAFE_READ directo; LOW/HIGH/CRITICAL a HITL       │
      │                       │                      │◀──────────────────│ decidir flujo │                  │
      │                       │ publish seguridad/X/comando             │                │                  │
      │                       │ + firma Ed25519      │                  │                │                  │
      │◀──────────────────────│                      │                  │                │                  │
      │ ejecuta y responde    │                      │                  │                │                  │
      │──────────────────────▶│                      │                  │                │                  │
      │ seguridad/X/respuesta │                      │                  │                │                  │
      │                       │ normaliza feedback ─────────────────────▶│                │                  │
      │                       │ encola en feedback_queue                │                │                  │
      │                       │──────────────────────────────────────────────────────────│─────────────────▶│
      │                       │                      │                  │                │  update_alert_status
      │                       │                      │                  │                │   (EXITO o FALLO)
      │                       │                      │                  │                │       │
      │                       │                      │   si FALLO: feedback puede llamar request_mitigation_approval
      │                       │                      │   con un comando alternativo → vuelve a publicar a PI-4
```

Caso anómalo (firma inválida):

```
PI-4 sensor          PI-5 coordinator        Policy Engine     Triage Agent
      │ comando con firma inválida                              │
      │ no ejecuta shell; publica rejected_signature             │
      │──────────────────────▶│ normaliza feedback ─────────────▶│
      │                       │ feedback_agent registra RECHAZADO_FIRMA
```

## 5. Reglas críticas que cumple cada agente

### Triage
- Llamar `register_alert` **exactamente una vez** por amenaza confirmada.
- Después de `request_mitigation_approval` debe **parar** la ejecución de tools (queda en cuarentena humana si es LOW/HIGH/CRITICAL, o se despacha directo solo si era SAFE_READ).
- Si propone una mitigación reversible, debe incluir `revert_command` con el comando exacto que la deshace. Para comandos sin rollback seguro sin estado previo (`kill`, scripts arbitrarios, cambios de permisos sin snapshot, borrados, etc.), debe dejarlo vacío: el dashboard no inventará una reversión.
- Si recibe un log con `attack_vector="INTRUSION-COMMAND-INJECTION"`, no propone nuevos comandos sobre ese dispositivo: el razonamiento debe orientarse a rotar credenciales/certificados.

### Feedback
- Llamar `update_alert_status` **exactamente una vez** por evento de respuesta.
- Si `status="error"` puede proponer una alternativa via `request_mitigation_approval`. Si no tiene alternativa, termina su turno con un texto resumen.

## 6. Configuración relevante

`config.yml`:
- `queue.max_size` (default 100) — límite de backpressure por cola de agente.
- `queue.ai_retry_poll_seconds` (default 30) - frecuencia con la que el worker busca eventos `PENDING_AI_RETRY`.
- `queue.ai_retry_batch_size` (default 5) - maximo de pendientes a reintentar por ciclo.
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
│       ├── pending_ai_events.py       # persistencia y retry de eventos no procesados por 429
│       └── policy_engine.py           # classify, decide, audit
└── tests/
    └── test_agent_flow.py             # Test E2E real (MQTT)
```
