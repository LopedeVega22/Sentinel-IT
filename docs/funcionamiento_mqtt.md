# Funcionamiento MQTT — Sentinel-IT

Documento de referencia técnica sobre cómo viajan los mensajes entre PI-4 (sensor) y PI-5 (coordinador) a través de AWS IoT Core. Refleja el estado a partir del 2026-05-15.

## Esquema de topics

Toda la comunicación cuelga del prefijo `seguridad/` (autorizado por la AWS IoT Policy). Bajo ese prefijo, cada dispositivo tiene su propio sub-árbol identificado por su `client_id`, con cuatro categorías:

```
seguridad/<device>/telemetria   ← upstream   (resúmenes periódicos)
seguridad/<device>/evento       ← upstream   (alertas inmediatas)
seguridad/<device>/comando      ← downstream (órdenes del SOC al sensor)
seguridad/<device>/respuesta    ← upstream   (resultado de ejecutar un comando)
```

`<device>` es el `client_id` del sensor (ejemplo actual: `Pi4-Felix`). Cuando se añadan más sensores cada uno tendrá su propio sub-árbol bajo `seguridad/`.

## Diagrama de flujo completo

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                          AWS IoT Core (Broker)                            ║
║                                                                           ║
║   ┌─────────────────────────────────────────────────────────────────┐     ║
║   │  seguridad/Pi4-Felix/telemetria    resúmenes SSH/FTP/Web        │     ║
║   │  seguridad/Pi4-Felix/evento        ataques detectados (SQLi…)   │     ║
║   │  seguridad/Pi4-Felix/comando       órdenes del SOC              │     ║
║   │  seguridad/Pi4-Felix/respuesta     resultado de la ejecución    │     ║
║   └─────────────────────────────────────────────────────────────────┘     ║
║                                                                           ║
╚══════╤════════════════════════════════════════════════════════════════╤═══╝
       │ Policy: client_id ∈ {Pi4-felix}                                │ Policy: client_id ∈
       │                                                                │ {Pi5-dani, Dashboard-SOC-Pi5}
       │                                                                │
┌──────▼────────────────────────────────────┐    ┌──────────────────────▼──────────────────────────┐
│  PI-4 — sensor "Pi4-Felix"                │    │  PI-5 — coordinador (cerebro)                   │
│  agente_monitor3.py                       │    │                                                 │
│                                           │    │  main_coordinator.py (client_id = Pi5-dani)     │
│  PUB → seguridad/Pi4-Felix/telemetria     │───►│  SUB ← seguridad/+/telemetria   ─┐              │
│  PUB → seguridad/Pi4-Felix/evento         │───►│  SUB ← seguridad/+/evento       ─┤→ triage_queue │
│                                           │    │                                  │ (async)       │
│                                           │    │      ↓ (procesamiento inmediato) │             │
│                                           │    │      ↓                           │             │
│                                           │    │  ADK Runner → triage_agent       │             │
│                                           │    │      │                           │             │
│                                           │    │      ├─ register_alert  → BD                  │
│                                           │    │      ├─ exec_diagnostic → PUB                 │
│                                           │    │      └─ request_mitig.  → BD (PENDING)        │
│                                           │    │                                                 │
│  SUB ← seguridad/Pi4-Felix/comando        │◄───│  PUB → seguridad/<device>/comando               │
│  (específico, NO wildcard)                │    │       (desde iot_tools y dashboard HITL)        │
│      ↓                                    │    │                                                 │
│  ejecuta_comando_seguro (whitelist)       │    │                                                 │
│      ↓                                    │    │                                                 │
│  PUB → seguridad/Pi4-Felix/respuesta      │───►│  SUB ← seguridad/+/respuesta  ──→ feedback_queue│
│                                           │    │      ↓                           (async)        │
│                                           │    │  ADK Runner → feedback_agent                    │
│                                           │    │      └─ update_alert_status → BD                │
└───────────────────────────────────────────┘    │                                                 │
                                                  │  dashboard_soc.py (client_id = Dashboard-SOC-Pi5)│
                                                  │  Solo PUBLICA (cuando humano aprueba HITL).     │
                                                  │  Lee BD para mostrar el feed; no se suscribe.   │
                                                  └─────────────────────────────────────────────────┘
```

## Quién publica y se suscribe a qué

| Componente | Client ID | Suscribe a | Publica en |
|---|---|---|---|
| **PI-4** (`agente_monitor3.py`) | `Pi4-Felix` | `seguridad/Pi4-Felix/comando` *(específico)* | `seguridad/Pi4-Felix/telemetria`<br>`seguridad/Pi4-Felix/evento`<br>`seguridad/Pi4-Felix/respuesta` |
| **PI-5 coordinador** (`main_coordinator.py`) | `Pi5-dani` | `seguridad/+/telemetria`<br>`seguridad/+/evento`<br>`seguridad/+/respuesta` | `seguridad/<device>/comando` *(desde iot_tools al ejecutar diagnóstico)* |
| **PI-5 dashboard** (`dashboard_soc.py`) | `Dashboard-SOC-Pi5` | *(nada)* | `seguridad/<device>/comando` *(tras aprobar HITL o revertir)* |

## Configuración centralizada

Todo se controla desde [PI-5/config.yml](../PI-5/config.yml):

```yaml
mqtt:
  topic_subscribe_telemetria: "seguridad/+/telemetria"
  topic_subscribe_eventos:    "seguridad/+/evento"
  topic_subscribe_respuestas: "seguridad/+/respuesta"
  topic_publish_comando:      "seguridad/{device}/comando"
```

El marcador `{device}` se sustituye en tiempo de ejecución por el nombre del sensor objetivo (lo hacen [iot_tools.py](../PI-5/src/tools/iot_tools.py) y [dashboard_soc.py](../PI-5/src/dashboard_soc.py) con `.replace("{device}", device)`).

## Cómo enruta el coordinador los mensajes recibidos

En [main_coordinator.py:process_event](../PI-5/src/main_coordinator.py):

```python
queue_type = "feedback" if topic.endswith("/respuesta") else "triage"
```

- Cualquier mensaje cuyo topic termine en `/respuesta` → cola del **feedback_agent** (`feedback_queue`).
- Todo lo demás (telemetría y eventos) → cola del **triage_agent** (`triage_queue`).

Las colas son asíncronas (`asyncio.Queue`) y procesan cada mensaje al instante (0ms de latencia artificial) a través de un worker dedicado. Para evitar saturación por ráfagas excesivas, se configura un límite de backpressure en `config.yml` → `queue.max_size` (default 100).

## Flujo end-to-end de un incidente

1. **Detección en PI-4**: SSH/FTP/Apache/Web app detecta algo. Si es alerta inmediata (SQLi, brute force…) → `seguridad/Pi4-Felix/evento`. Si es resumen periódico (cada 30 s) → `seguridad/Pi4-Felix/telemetria`.
2. **Recepción en PI-5**: el coordinador captura el mensaje (matches wildcard `seguridad/+/evento` o `…/telemetria`), lo encola de forma thread-safe en `triage_queue`.
3. **Análisis**: de inmediato, el worker asíncrono del `triage_agent` (LLM ADK) consume el mensaje y decide:
   - Tráfico benigno → no hace nada.
   - Ataque confirmado → llama `register_alert` (escribe en BD `logs`).
   - Si hace falta info adicional → `execute_diagnostic_command` → publica en `seguridad/Pi4-Felix/comando` (sin HITL, solo si el comando pasa la blacklist).
   - Si propone mitigación destructiva → `request_mitigation_approval` → escribe en BD con `status='PENDING'`.
4. **HITL (Human in the Loop)**: el dashboard web muestra los `PENDING` en la "Live Threat Feed". Cuando el operador aprueba en el botón "Revisar Mitigación", el dashboard publica el comando en `seguridad/Pi4-Felix/comando`.
5. **Ejecución en PI-4**: el sensor recibe el mensaje en su suscripción específica, lo pasa por `ejecutar_comando_seguro` (whitelist de binarios) y lo ejecuta con timeout 30s.
6. **Respuesta**: PI-4 publica `{"sensor":"Pi4-Felix","status":"success|error","output":"…"}` en `seguridad/Pi4-Felix/respuesta`.
7. **Cierre del bucle**: el coordinador captura la respuesta (matches `seguridad/+/respuesta`), la enruta a `feedback_queue`, el worker del `feedback_agent` la consume inmediatamente, llama a `update_alert_status` y el campo `estado_mitigacion` en la BD se complementa. El dashboard lo muestra inmediatamente en el siguiente refresco (5 s).

## Compatibilidad con la AWS IoT Policy

La Policy actual autoriza:
- **Conexión** con `client_id ∈ {Pi5-dani, Pi4-felix, Dashboard-SOC-Pi5}`.
- **Publicación y suscripción** a topics bajo `seguridad/*`.

Todos los topics del esquema empiezan por `seguridad/`, por lo que **no es necesario modificar la Policy de AWS**.

## Cómo añadir un sensor nuevo

1. Crear un certificado nuevo en AWS IoT y añadir el `client_id` a la Policy (ejemplo: `Pi4-OficinaB`).
2. En el sensor, configurar los topics derivados de ese `client_id`:
   - `seguridad/Pi4-OficinaB/telemetria` (PUB)
   - `seguridad/Pi4-OficinaB/evento` (PUB)
   - `seguridad/Pi4-OficinaB/comando` (SUB, **específico al device**)
   - `seguridad/Pi4-OficinaB/respuesta` (PUB)
3. **En PI-5 no hay que cambiar nada**: las suscripciones `seguridad/+/*` ya capturan al nuevo sensor automáticamente, y `topic_publish_comando` sustituye `{device}` en runtime.

## Tabla de antaño vs ahora

| Categoría | Esquema anterior | Esquema actual |
|---|---|---|
| Telemetría SSH/FTP/Apache | `seguridad/cliente1/telemetria` | `seguridad/Pi4-Felix/telemetria` |
| Eventos SSH/FTP | `seguridad/cliente1/eventos` (plural) | `seguridad/Pi4-Felix/evento` |
| Eventos web | `seguridad/cliente1/web/eventos` (2 niveles) | `seguridad/Pi4-Felix/evento` (fusionado) |
| Telemetría web | `seguridad/cliente1/web/telemetria` (2 niveles) | `seguridad/Pi4-Felix/telemetria` (fusionado) |
| Comandos PI-5 → PI-4 | `seguridad/acciones/<dev>` | `seguridad/<dev>/comando` |
| Respuestas PI-4 → PI-5 | `seguridad/acciones/<dev>/out` (mock) o `seguridad/cliente1/telemetria` (mezclado) | `seguridad/<dev>/respuesta` |
| Suscripción PI-4 | `seguridad/acciones/#` (wildcard) | `seguridad/Pi4-Felix/comando` (específico) |
| Suscripción PI-5 | `seguridad/#` + `comandos/+/out` (obsoleto) | 3 suscripciones específicas sin solapes |

## Beneficios del esquema actual

1. **Jerarquía consistente**: `<root>/<device>/<categoría>`. Cualquier wildcard tiene sentido (`seguridad/Pi4-Felix/+` filtra todo lo de un sensor, `seguridad/+/evento` filtra los eventos de todos).
2. **Cero eco**: el coordinador NO se suscribe al topic donde él mismo publica (`/comando` sin sufijo). MQTT 3.1.1 sin "no-local" enviaba los propios mensajes de vuelta si encajaban con la suscripción; ya no.
3. **Aislamiento entre sensores**: cada PI-4 solo recibe sus propios comandos. Imposible que un comando dirigido a `Pi4-OficinaB` sea ejecutado por error en `Pi4-Felix`.
4. **Routing del coordinador limpio**: `topic.endswith("/respuesta")` es exacto y no se confunde con substrings ambiguos como antes (`"comandos" in topic`).
5. **Compatibilidad mTLS sin cambios**: todos los topics caen dentro del wildcard `seguridad/*` de la AWS IoT Policy existente.

## Modos de publicación: asíncrono vs síncrono (PUBACK)

`AWSMqttClient.publish()` admite dos modos. La diferencia es **quién decide que el mensaje "ya está enviado"**.

| Modo | Parámetro | Quién lo usa | Comportamiento |
|---|---|---|---|
| Asíncrono (fire-and-forget) | `wait_for_ack=False` *(default)* | `iot_tools.py` (agente ADK) | El método encola el publish en el event loop de awscrt y retorna al instante. Si la conexión está caída, el mensaje queda en buffer o se pierde silenciosamente. |
| Síncrono | `wait_for_ack=True` | `dashboard_soc.py` (HITL: aprobar y revertir) | El método espera hasta `ack_timeout` segundos (5 s por defecto) a que el broker devuelva el PUBACK de QoS 1. Si no llega o la conexión falla, lanza excepción y el endpoint Flask devuelve `502 Bad Gateway` al navegador. |

**Por qué la diferencia.** El agente puede tolerar un retraso de varios milisegundos en sus diagnósticos y mitigaciones LOW; lo importante es que el thread del ADK no se bloquee. En cambio, cuando el operador humano aprueba un comando desde el dashboard quiere certeza inmediata: si la conexión MQTT del dashboard está caída o AWS rechaza el publish por política, prefiere ver un toast de error en lugar de un falso "Mitigación aplicada correctamente" seguido de un comando que nunca llega a PI-4.

**Implementación.** El método interno hace `connection.publish(...)` (que devuelve `(future, packet_id)`) y, en modo síncrono, llama a `future.result(timeout=ack_timeout)`. El log distingue ambos casos:

```
[INFO] Mensaje publicado en seguridad/Pi4-Felix/comando                    ← async
[INFO] Mensaje publicado y confirmado (PUBACK) en seguridad/Pi4-Felix/comando ← sync
```

**Comportamiento ante fallo en el HITL.** Si el publish síncrono lanza excepción, `approve_mitigation` y `revert_action` retornan antes de actualizar la BD, de modo que la fila **no** queda marcada como `APPROVED/REVERTED`. El operador puede reintentar sin contaminar la auditoría.

## Verificación end-to-end del HITL (round-trip por `/respuesta`)

El PUBACK síncrono solo garantiza que **AWS** aceptó el comando. Para confirmar que **PI-4 lo ejecutó** se cierra el bucle con la respuesta del sensor (`seguridad/Pi4-Felix/respuesta`).

### Diagrama del round-trip

```
   Operador                Dashboard                  AWS IoT                  PI-4
      │                        │                         │                       │
   1. Approve                  │                         │                       │
      ├───────────────────────►│                         │                       │
      │                        │ 2. publish(QoS1, wait)  │                       │
      │                        ├────────────────────────►│                       │
      │                        │       PUBACK            │                       │
      │                        │◄────────────────────────┤                       │
      │                        │                         │  3. comando           │
      │                        │                         ├──────────────────────►│
      │                        │ 4. UPDATE logs          │                       │
      │                        │    status='APPROVED',   │                       │
      │                        │    estado_mitigacion=∅  │                       │
      │ 5. {dispatching,log_id}│                         │                       │
      │◄───────────────────────┤                         │              ejecuta_comando_seguro
      │                        │                         │                       │
      │   spinner azul         │ 6. poll cada 1s         │                       │
      │  "Esperando PI-4"      │  /api/mitigate/status/N │                       │
      │                        │  ────► phase=awaiting   │                       │
      │                        │                         │  7. /respuesta        │
      │                        │                         │◄──────────────────────┤
      │                        │                         │       (status=success,│
      │                        │                         │        output="...")  │
      │                        │ 8. process_event:       │                       │
      │                        │    match_feedback(...)  │                       │
      │                        │    → log_id=N           │                       │
      │                        │    mark_mitigation_     │                       │
      │                        │     result(N,EXITO,...) │                       │
      │                        │ 9. poll → phase=executed│                       │
      │   toast verde          │◄────────────────────────┤                       │
      │  "PI-4 confirmó"       │                         │                       │
      ▼                        ▼                         ▼                       ▼
```

### Piezas implicadas

| Pieza | Archivo | Función |
|---|---|---|
| Correlación dispatch → fila | [policy_engine.match_feedback](../PI-5/src/tools/policy_engine.py) | Devuelve la entrada de `_dispatch_cache` (incluye `log_id`) cuya cadena normalizada coincide con el comando que reporta PI-4. |
| Escritura inmediata | [db_tools.mark_mitigation_result](../PI-5/src/tools/db_tools.py) | UPDATE `estado_mitigacion` por `log_id` exacto (no "última fila del dispositivo"). |
| Fast-path | [main_coordinator.process_event](../PI-5/src/main_coordinator.py) | Cuando llega `/respuesta`: si `match_feedback` devuelve `log_id`, escribe `[EXITO]`/`[FALLO]` antes de encolar al feedback_agent. |
| Endpoint de polling | [dashboard_soc.mitigation_status](../PI-5/src/dashboard_soc.py) | `GET /api/mitigate/status/<log_id>` → `{phase: awaiting_pi4|executed|failed|feedback, …}`. |
| Polling cliente | `index.html → pollMitigationStatus(logId, 30)` | Llama al endpoint cada 1 s hasta 30 s. Cierra con toast verde, rojo o de timeout. |

### Por qué dos caminos para `/respuesta`

Cuando llega un mensaje en `seguridad/+/respuesta`, el coordinador hace **dos cosas**:

1. **Fast-path síncrono** (sin LLM): si el comando correlaciona con un dispatch reciente, escribe `estado_mitigacion` en la fila exacta. Esto da feedback al operador en ~1 s.
2. **Cola del feedback_agent** (con LLM, procesamiento inmediato asíncrono): el mensaje se encola para el agente de IA, que consume y procesa de inmediato el feedback de forma secuencial sin bloquear el flujo principal.

Los dos caminos no se pisan: el fast-path escribe en `estado_mitigacion` con prefijo `[EXITO]/[FALLO]`; el agente, si llama a `update_alert_status` después, hace `||` (concatenación) y deja constancia de su análisis sin sobrescribir el resultado crudo.

### Fallback: PI-4 no responde

Si el sensor está caído o sin red, la cadena se rompe en el paso 7. El operador ve el spinner azul durante 30 s y al final un toast rojo:

> *"Sin respuesta de PI-4 tras 30s. Revisa la conectividad del sensor."*

La fila queda con `status='APPROVED'` y `estado_mitigacion=NULL`, así que el operador puede volver a abrir el modal y reaprobar o cambiar de estrategia.

## Caso especial pendiente

Al pull del compañero (commit `bd4b36e`) detecto que en [agente_monitor3.py:194](../PI-4/Agente%20de%20monitorizacion/agente_monitor3.py#L194) se mantiene un destino legacy para un caso concreto:

```python
destino = "seguridad/cliente1/web/eventos"
```

Eso publica fuera del nuevo esquema y el coordinador (que escucha solo `seguridad/+/evento`) **no lo captura**. Recomendable revisarlo con el compañero — probablemente debería ser `TOPIC_EVENTOS` (= `seguridad/Pi4-Felix/evento`).
