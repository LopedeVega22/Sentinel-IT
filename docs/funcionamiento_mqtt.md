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
│  PUB → seguridad/Pi4-Felix/evento         │───►│  SUB ← seguridad/+/evento       ─┤→ TRIAGE Q   │
│                                           │    │                                  │             │
│                                           │    │      ↓ batch (10 msgs ó 15 s)    │             │
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
│  PUB → seguridad/Pi4-Felix/respuesta      │───►│  SUB ← seguridad/+/respuesta  ──→ FEEDBACK Q    │
│                                           │    │      ↓                                          │
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

- Cualquier mensaje cuyo topic termine en `/respuesta` → cola del **feedback_agent**.
- Todo lo demás (telemetría y eventos) → cola del **triage_agent**.

Las colas tienen disparador dual: se vacían cuando se acumulan 10 mensajes o pasan 15 segundos sin flush (lo que ocurra primero). Esto se configura en `config.yml` → `batch.max_size` y `batch.flush_interval`.

## Flujo end-to-end de un incidente

1. **Detección en PI-4**: SSH/FTP/Apache/Web app detecta algo. Si es alerta inmediata (SQLi, brute force…) → `seguridad/Pi4-Felix/evento`. Si es resumen periódico (cada 30 s) → `seguridad/Pi4-Felix/telemetria`.
2. **Recepción en PI-5**: el coordinador captura el mensaje (matches wildcard `seguridad/+/evento` o `…/telemetria`), lo encola en `TRIAGE_Q` con el dispositivo origen.
3. **Análisis**: cuando el batch dispara, `triage_agent` (LLM ADK) recibe el lote y decide:
   - Tráfico benigno → no hace nada.
   - Ataque confirmado → llama `register_alert` (escribe en BD `logs`).
   - Si hace falta info adicional → `execute_diagnostic_command` → publica en `seguridad/Pi4-Felix/comando` (sin HITL, solo si el comando pasa la blacklist).
   - Si propone mitigación destructiva → `request_mitigation_approval` → escribe en BD con `status='PENDING'`.
4. **HITL (Human in the Loop)**: el dashboard web muestra los `PENDING` en la "Live Threat Feed". Cuando el operador aprueba en el botón "Revisar Mitigación", el dashboard publica el comando en `seguridad/Pi4-Felix/comando`.
5. **Ejecución en PI-4**: el sensor recibe el mensaje en su suscripción específica, lo pasa por `ejecutar_comando_seguro` (whitelist de binarios) y lo ejecuta con timeout 30s.
6. **Respuesta**: PI-4 publica `{"sensor":"Pi4-Felix","status":"success|error","output":"…"}` en `seguridad/Pi4-Felix/respuesta`.
7. **Cierre del bucle**: el coordinador captura la respuesta (matches `seguridad/+/respuesta`), la enruta a la cola `FEEDBACK_Q`, el `feedback_agent` llama a `update_alert_status` y el campo `estado_mitigacion` en la BD pasa a "EXITO" o "FALLO". El dashboard lo muestra inmediatamente en la siguiente refresco (5 s).

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

## Caso especial pendiente

Al pull del compañero (commit `bd4b36e`) detecto que en [agente_monitor3.py:194](../PI-4/Agente%20de%20monitorizacion/agente_monitor3.py#L194) se mantiene un destino legacy para un caso concreto:

```python
destino = "seguridad/cliente1/web/eventos"
```

Eso publica fuera del nuevo esquema y el coordinador (que escucha solo `seguridad/+/evento`) **no lo captura**. Recomendable revisarlo con el compañero — probablemente debería ser `TOPIC_EVENTOS` (= `seguridad/Pi4-Felix/evento`).
