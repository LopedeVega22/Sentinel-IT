---
title: "Visión General del Sistema - Sentinel-IT (PI-5)"
author: "Daniel Alarcon"
date: "2026-05-17"
tags: ["overview", "architecture", "pi5", "edge-cloud-core", "mqtt", "adk"]
---

# Visión General del Sistema

## 1. Propósito

Este documento describe la **arquitectura global** de Sentinel-IT desde la perspectiva del coordinador SOC (PI-5): qué piezas existen, cómo encajan y cuál es el camino de un incidente desde que se detecta en el sensor edge hasta que se resuelve en el dashboard.

No entra en el detalle de cada subsistema — para eso están los docs hermanos. Aquí se construye el mapa mental que permite navegarlos.

## 2. Modelo Edge-Cloud-Core

Sentinel-IT sigue un patrón distribuido con tres niveles físicos:

```
┌──────────────────┐      ┌──────────────────────┐      ┌────────────────────┐
│  PI-4 (Edge)     │      │  AWS IoT Core        │      │  PI-5 (Core)       │
│  Sensor          │◄────►│  (Broker MQTT mTLS)  │◄────►│  Coordinador SOC   │
│  - Monitoriza    │      │                      │      │  - Triage IA       │
│    Apache/SSH/   │      │  Topics:             │      │  - Feedback IA     │
│    FTP           │      │  seguridad/<dev>/*   │      │  - Policy Engine   │
│  - Ejecuta       │      │                      │      │  - SQLite          │
│    comandos      │      │  Policy IAM con      │      │  - Dashboard Flask │
│    aprobados     │      │  3 client_ids        │      │  - Operador humano │
└──────────────────┘      └──────────────────────┘      └────────────────────┘
```

- **Edge (PI-4):** recolección + ejecución. No tiene autonomía, solo captura logs y obedece comandos.
- **Cloud (AWS IoT Core):** broker MQTT autenticado por mTLS. Único punto de tránsito entre nodos. Detalles en [funcionamiento_mqtt.md](funcionamiento_mqtt.md).
- **Core (PI-5):** cerebro del SOC. Ejecuta los agentes IA, mantiene el estado en SQLite y expone la interfaz humana.

El modelo es deliberadamente asimétrico: el edge es tonto y reemplazable; toda la lógica de decisión vive en el core. Si un PI-4 se cae, solo se pierde un sensor; si se compromete, no puede ejecutar acciones que el core no haya autorizado.

## 3. Componentes del Coordinador (PI-5)

```
PI-5/
├── src/
│   ├── main_coordinator.py     ← Punto de entrada. MQTT + colas + dispatcher
│   ├── aws_connector.py        ← Wrapper del SDK awsiotsdk (publish/subscribe mTLS)
│   ├── dashboard_soc.py        ← Flask: rutas, auth, refresco AJAX, HITL endpoints
│   ├── database.py             ← Bootstrap del esquema SQLite + triggers de audit_log
│   ├── agents/
│   │   ├── triage_agent/       ← LlmAgent ADK que analiza eventos entrantes
│   │   └── feedback_agent/     ← LlmAgent ADK que evalúa respuestas tras ejecutar
│   ├── tools/
│   │   ├── iot_tools.py        ← execute_diagnostic_command, request_mitigation_approval
│   │   ├── db_tools.py         ← register_alert, update_alert_status, rotate_old_logs
│   │   └── policy_engine.py    ← Motor de clasificación + audit
│   └── templates/
│       └── index.html          ← Single-page dashboard (glassmorphism)
├── config.yml                  ← Configuración centralizada (AWS, MQTT, queue, retention)
├── docker-compose.yml          ← Servicios: coordinator + (opcional) local-ai-engine
├── Dockerfile                  ← Imagen Python con dependencias ADK + awsiotsdk
├── soc_manager.sh              ← CLI interactivo para levantar/monitorizar/purgar
└── tests/                      ← Tests unitarios + E2E (ver Testing_Guide.md)
```

### 3.1 Capa de transporte (`aws_connector.py`)

Cliente MQTT sobre `awsiotsdk` con tres responsabilidades:

- Establecer una conexión TLS mutua con AWS IoT Core usando los certificados de `./certificados/`.
- `publish(topic, payload)` — serializa a JSON y publica con QoS 1.
- `subscribe(topic, callback)` — registra callbacks por patrón de topic (soporta wildcards `+` y `#`).

Es el único componente que toca el broker. Si AWS IoT cambia de SDK o pasa a usar HTTPS/WebSocket, este es el único archivo que debe adaptarse.

### 3.2 Orquestación (`main_coordinator.py`)

Punto de entrada del coordinador. Responsabilidades en orden de ejecución:

1. Carga `config.yml`.
2. Inicializa logging rotativo y el cliente MQTT.
3. Crea **dos `Runner` de ADK** (uno por agente) compartiendo un único `InMemorySessionService` y una sesión.
4. Crea **dos `asyncio.Queue`** independientes (triage / feedback) acotadas para backpressure.
5. Inicia los workers asíncronos correspondientes que consumen de las colas.
6. Suscribe el callback `process_event` a los tres topics de entrada (`telemetria`, `evento`, `respuesta`).
7. Ejecuta el event loop de asyncio indefinidamente.

`process_event` clasifica el mensaje por sufijo del topic, normaliza las respuestas de PI-4 y encola en la cola correspondiente de forma thread-safe usando `_enqueue_from_thread`. Detalles del flujo y el código de las colas en [Agent_Architecture.md](Agent_Architecture.md).

### 3.3 Agentes IA (`agents/`)

Dos `LlmAgent` ADK, cada uno con sus tools propias. Ver [Agent_Architecture.md](Agent_Architecture.md) para la especificación completa.

- **Triage:** consume telemetría/eventos → decide si registrar alerta, pedir diagnóstico o proponer mitigación.
- **Feedback:** consume respuestas de PI-4 → marca la mitigación como EXITO o FALLO; si falla, puede proponer una alternativa.

Ambos comparten el mismo modelo configurable vía `AI_MODE`:

- `AI_MODE=local` → Ollama vía LiteLLM en `http://local-ai-engine:11434` (el segundo servicio del `docker-compose.yml`, perfil `local-ai`).
- Cualquier otro valor → Vertex/Gemini API directa (requiere `GEMINI_API_KEY` en `.env`).

### 3.4 Tools (`tools/`)

Las **únicas** funciones que los agentes pueden invocar. Toda acción con efecto fuera del proceso pasa por aquí.

| Tool | Definida en | Efecto |
|------|-------------|--------|
| `register_alert(...)` | `db_tools.py` | INSERT en `logs` con `status='LOGGED'` |
| `update_alert_status(...)` | `db_tools.py` | UPDATE de `estado_mitigacion` en la fila más reciente |
| `execute_diagnostic_command(...)` | `iot_tools.py` | Publica en `seguridad/<device>/comando` si el Policy Engine lo clasifica SAFE_READ |
| `request_mitigation_approval(..., revert_command="")` | `iot_tools.py` | Clasifica + despacha solo SAFE_READ o cuarentena PENDING cualquier LOW/HIGH/CRITICAL; guarda rollback explícito si se proporciona |

Cada vez que se publica un comando, PI-5 lo firma con Ed25519. PI-4 verifica firma, expiración y nonce antes de ejecutar; si falla, responde con `rejected_signature`.

### 3.5 Motor de Políticas (`tools/policy_engine.py`)

Capa transversal — no la invoca el agente directamente sino las tools y el dashboard. Dos responsabilidades:

1. **Clasificar comandos** en SAFE_READ/LOW/HIGH/CRITICAL antes de publicar.
2. **Escribir audit log inmutable** (`audit_log` con triggers que abortan UPDATE/DELETE).

Especificación completa: [funcionamiento_policy_engine.md](funcionamiento_policy_engine.md).

### 3.6 Persistencia (`database.py`)

Bootstrap de SQLite con dos tablas: `logs` (incidentes) y `audit_log` (auditoría append-only). Modo WAL habilitado para permitir lectura/escritura concurrente entre el thread MQTT y el dashboard Flask. Esquema y detalles en [Database_Schema.md](Database_Schema.md).

### 3.7 Dashboard (`dashboard_soc.py` + `templates/index.html`)

Flask + HTTP Basic Auth. Sirve:

- Página única con feed de logs, métricas, gráficas de vectores y vista radar de topología.
- Endpoint AJAX `/api/data` que refresca cada 5 s.
- Endpoint `/api/mitigate/approve` para el flujo HITL.
- Endpoint `/revert/<id>` para deshacer mitigaciones aprobadas usando `revert_command`, una inversa derivable segura o un comando editado por el operador.

Especificación completa: [Dashboard_Architecture.md](Dashboard_Architecture.md).

## 4. Ciclo de vida de un incidente

Caso canónico — fuerza bruta SSH contra el PI-4:

```
1. PI-4: fail2ban / monitor detecta intento de login fallido repetido.
2. PI-4 publica:  seguridad/Pi4-Felix/evento   { "raw_log": "...", "ip": "1.2.3.4" }
3. PI-5: process_event lo recibe y encola en triage_queue de forma thread-safe.
4. El triage_task lo saca de la cola inmediatamente (0ms de latencia artificial) y lo envía al SOC_Triage_Agent.
5. Triage analiza con Gemini, decide que es un ataque y llama tools en orden:
     a) register_alert(...)                  → fila en logs con status='LOGGED'
     b) request_mitigation_approval(
          "sudo iptables -A INPUT -s 1.2.3.4 -j DROP",
          rationale="brute-force SSH",
          revert_command="sudo iptables -D INPUT -s 1.2.3.4 -j DROP")
6. Policy Engine clasifica el comando como LOW (iptables -A contra IP concreta).
7. _quarantine_for_hitl() guarda el comando con status='PENDING' y audit(QUARANTINE).
8. Dashboard muestra el botón "Revisar Mitigación"; el operador aprueba o rechaza.
9. Si aprueba, /api/mitigate/approve re-clasifica, firma el payload, publica en seguridad/Pi4-Felix/comando y audit(APPROVE).
10. PI-4 verifica firma Ed25519, expiración y nonce; si todo cuadra, ejecuta iptables.
11. PI-4 publica:  seguridad/Pi4-Felix/respuesta  { "comando": "...", "status": "success" }
12. PI-5 normaliza la respuesta y la encola en feedback_queue.
13. El feedback_task lo saca de la cola inmediatamente y el SOC_Feedback_Agent llama update_alert_status('EXITO', ...).
14. El dashboard muestra la fila con badge verde [EXITO] en el siguiente refresh (5 s).
15. El operador, si lo desea, pulsa REVERTIR; se calcula el comando inverso (-A → -D),
    se vuelve a publicar y se audita como REVERT.
```

Caso de mitigación destructiva (HIGH/CRITICAL):

```
5'. Triage propone "sudo systemctl restart apache2" (HIGH).
6'. Policy Engine: _quarantine_for_hitl → UPDATE status='PENDING'.
7'. Dashboard pinta la fila con banner amarillo y botón "Revisar Mitigación".
8'. Operador abre el modal, edita o no el comando, pulsa Aprobar.
9'. /api/mitigate/approve re-clasifica el comando final.
    - Si la edición lo elevó a CRITICAL y falta confirm_critical → 400 needs_confirmation.
    - Si OK → firma Ed25519 + publish + audit(APPROVE) + status='APPROVED'.
10'. Resto idéntico al caso LOW desde el paso 10.
```

Caso anómalo (PI-4 recibe un comando sin firma válida):

```
1''. PI-4: verify_payload falla por firma, expiración o nonce repetido.
2''. PI-4 no ejecuta shell y publica status='rejected_signature'.
3''. PI-5 normaliza el feedback y el SOC_Feedback_Agent registra RECHAZADO_FIRMA.
```

## 5. Cómo encaja AWS IoT Core

AWS IoT Core es **solo broker**. No tiene lógica de aplicación. Aporta:

- **mTLS:** autenticación mutua. Cada `client_id` lleva su par cert/key.
- **Policy IAM:** restringe qué `client_id` puede conectar y a qué prefijo de topic. En el proyecto sólo están autorizados `Pi5-dani`, `Pi4-felix` y `Dashboard-SOC-Pi5`, todos limitados al prefijo `seguridad/*`.
- **Pub/Sub QoS 1:** "at least once". Suficiente para este caso de uso; el reprocesado de un evento idéntico no rompe nada porque `register_alert` añade y los comandos firmados llevan nonce anti-replay.

No se usa ni Device Shadow ni Rules Engine ni Jobs. Todo el routing vive en el coordinador. Detalles del esquema de topics y de la Policy en [funcionamiento_mqtt.md](funcionamiento_mqtt.md).

## 6. Decisiones arquitectónicas relevantes

| Decisión | Justificación |
|----------|---------------|
| **Dual-agent (triage + feedback)** en vez de un único agente | Separa "qué hacer con un evento nuevo" de "qué hacer con la respuesta de una mitigación". Distintos prompts, distintas tools obligatorias, distintos contextos. |
| **Procesamiento inmediato con colas asíncronas** | Elimina delays artificiales procesando eventos al instante (0ms de latencia) y encolando ráfagas secuencialmente para el LLM. |
| **Policy Engine centralizado en PI-5** | Permite cambiar la política sin tocar PI-4. PI-4 ejecuta lo que llega; toda decisión vive en el core. |
| **Audit log inmutable con triggers SQLite** | Garantía forense: ni la propia aplicación puede modificar el registro de decisiones. Mapea con NIST AU-2 e ISO 27001 A.12.4. |
| **HITL para cualquier escritura** | Solo las lecturas `SAFE_READ` se despachan sin fricción; cualquier comando `LOW`, `HIGH` o `CRITICAL` requiere decisión humana. |
| **InMemorySessionService de ADK** | Las sesiones del ADK son efímeras dentro de un único proceso. Si el coordinador reinicia, se crea una sesión nueva — el estado relevante vive en SQLite, no en la sesión. |

## 7. Archivos por rol

| Rol | Archivos principales |
|-----|----------------------|
| Punto de entrada | `PI-5/src/main_coordinator.py` |
| Cliente MQTT | `PI-5/src/aws_connector.py` |
| Agentes IA | `PI-5/src/agents/{triage,feedback}_agent/*.py` |
| Tools de agente | `PI-5/src/tools/{iot,db}_tools.py` |
| Motor de políticas | `PI-5/src/tools/policy_engine.py` |
| Persistencia | `PI-5/src/database.py` |
| Interfaz humana | `PI-5/src/dashboard_soc.py` + `src/templates/index.html` |
| Configuración | `PI-5/config.yml`, `.env` |
| Despliegue | `PI-5/docker-compose.yml`, `PI-5/Dockerfile`, `PI-5/soc_manager.sh` |
| Tests | `PI-5/tests/*.py` |

## 8. Glosario rápido

- **ADK** — Google Agent Development Kit. Framework de orquestación de agentes LLM con tools tipadas.
- **HITL** — Human-in-the-Loop. Modelo donde la IA propone y el humano aprueba acciones destructivas.
- **mTLS** — TLS mutuo. Cliente y servidor se autentican con certificados.
- **Policy Engine** — Motor que clasifica cada comando antes de publicarlo y audita decisiones.
- **Ed25519 command signing** — Firma de payloads desde PI-5 y verificación preventiva en PI-4 antes de ejecutar.
- **asyncio.Queue / Procesamiento Inmediato** — Procesar los eventos de seguridad tan pronto como llegan usando workers asíncronos y colas acotadas.

## 9. Siguientes pasos

Si has llegado hasta aquí, ya tienes el mapa. Para profundizar:

1. **Cómo viajan los mensajes** → [funcionamiento_mqtt.md](funcionamiento_mqtt.md).
2. **Qué hace cada agente exactamente** → [Agent_Architecture.md](Agent_Architecture.md).
3. **Por qué un comando se ejecuta solo o pide aprobación** → [funcionamiento_policy_engine.md](funcionamiento_policy_engine.md).
4. **El modal de aprobación humano** → [HITL_Architecture.md](HITL_Architecture.md).
5. **El propio dashboard** → [Dashboard_Architecture.md](Dashboard_Architecture.md).
6. **Esquema de tablas y triggers** → [Database_Schema.md](Database_Schema.md).
7. **Cómo probar el sistema** → [Testing_Guide.md](Testing_Guide.md).
8. **Cómo desplegarlo** → [Configuration_and_Deployment.md](Configuration_and_Deployment.md).
