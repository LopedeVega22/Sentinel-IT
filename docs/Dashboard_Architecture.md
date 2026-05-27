---
title: "Arquitectura del Dashboard SOC - Sentinel-IT (PI-5)"
author: "Daniel Alarcon"
date: "2026-05-17"
tags: ["dashboard", "flask", "hitl", "ui", "topology", "revert"]
---

# Arquitectura del Dashboard SOC

## 1. Propósito

Este documento describe la **interfaz humana** del coordinador SOC: el dashboard web servido por Flask en `src/dashboard_soc.py` + `src/templates/index.html`. Cubre rutas, autenticación, refresco AJAX, panel de incidentes, gráfica radar de topología y los endpoints HITL (aprobar / rechazar / revertir).

No describe la lógica del modal HITL en sí — eso está en [HITL_Architecture.md](HITL_Architecture.md). Tampoco describe la clasificación que ocurre dentro de `approve_mitigation` — eso vive en [funcionamiento_policy_engine.md](funcionamiento_policy_engine.md).

## 2. Stack y arranque

| Componente | Versión / configuración |
|------------|-------------------------|
| Framework | Flask + `flask-httpauth` |
| Auth | HTTP Basic con credenciales en `.env` (`DASHBOARD_USER` / `DASHBOARD_PASSWORD` o `DASHBOARD_PASSWORD_HASH`) |
| Front-end | Plantilla única `index.html` (Jinja2) + JS vanilla para refresco AJAX |
| Gráficas | ECharts (CDN) — barras de vectores, gauge de threat level, grafo de topología |
| Servidor | `app.run()` con `WEB_HOST` y `WEB_PORT` desde `config.yml` (por defecto `0.0.0.0:5000`) |
| Persistencia | SQLite WAL leído en cada petición (no hay caché — el feed es siempre fresco) |
| MQTT | Cliente `Dashboard-SOC-Pi5` independiente; **solo publica**, no se suscribe |

El cliente MQTT se inicializa al arrancar el módulo. Si AWS IoT está caído, el dashboard arranca igual y los endpoints HITL devuelven `500 MQTT client not connected` hasta que se restaure la conexión. El resto de la interfaz (visualización de logs, métricas) sigue funcionando porque lee solo de SQLite.

## 3. Rutas

| Ruta | Método | Decorador auth | Función |
|------|--------|----------------|---------|
| `/` | GET | `@auth.login_required` | Render de la página principal con todos los datos pre-cargados |
| `/api/data` | GET | `@auth.login_required` | JSON con todo el estado del dashboard (consumido por el polling) |
| `/api/mitigate/approve` | POST | `@auth.login_required` | Aprobar o rechazar una mitigación PENDING |
| `/revert/<int:log_id>` | POST | `@auth.login_required` | Revertir una mitigación previamente APPROVED |

No hay más endpoints. Cualquier funcionalidad nueva (export, filtrado avanzado, ack masivo) requeriría un endpoint nuevo y se considera fuera del alcance MVP.

## 4. Modelo de datos servido (`/api/data`)

`/api/data` devuelve un único JSON con todo lo que la página necesita. Es un compromiso deliberado: una petición cada 5 s es más simple que múltiples endpoints granulares.

```json
{
  "logs":            [ { id, device, service, raw_log, source_ip, severity,
                         verdict, action, mitigation_status, status,
                         pending_command, rationale, timestamp,
                         revert_command } ],   // 20 últimas
  "total_logs":      1234,
  "total_criticals": 12,
  "total_blocks":    45,         // status='APPROVED'
  "last_seen":       "2026-05-17 18:23:11",
  "vector_stats":    [ { name: "SSH",  count: 89, percentage: 38.2 },
                       { name: "HTTP", count: 54, percentage: 23.1 } ],
  "unique_vectors":  6,
  "threat_level":    73,         // 0-100, fórmula ponderada
  "mqtt_status":     "connected" | "disconnected",
  "sys_info":        { cpu, ram, uptime, ip_local, ai_model },
  "topology":        { nodes, links, flow_lines, stats }
}
```

### 4.1 Threat level

Heurística en `get_threat_level()`:

```python
level = ((criticals * 3) + (highs * 2) + mediums) / total * 25
return min(round(level), 100)
```

Pondera las críticas con peso 3 y las altas con peso 2 respecto al total de logs. Multiplicar por 25 sirve para mover el umbral psicológico (un sistema con 100% de criticas saturaría el gauge en 75; el cap a 100 lo cierra). No pretende ser una métrica científica — es un indicador visual.

### 4.2 Vector stats

Agrupa por la columna `servicio` (etiqueta que pone el agente en `register_alert`, e.j. `SSH`, `HTTP`, `MYSQL`, `PORT-SCAN`). El front muestra las 8 más frecuentes en una barra horizontal apilada.

### 4.3 Topología radar

`get_topology_data()` construye un grafo hub-spoke con coordenadas **fijas** (no fuerza física):

- **PI-5** en el centro (300, 200) con color azul.
- **PI-4** a la izquierda (100, 200) con color verde. Se renderiza como un único nodo consolidado aunque la BD tenga varios sensores; el MVP asume un solo PI-4.
- **Atacantes** (hasta 10 IPs distintas con más hits) repartidos en un arco a la derecha del PI-5, con radio `ARC_RADIUS=160`. Cada nodo tiene tamaño proporcional al número de eventos (clamp 14-28).
- **Enlaces:**
  - PI-4 ↔ PI-5: línea cian discontinua (canal MQTT).
  - Atacante → PI-4: línea roja con curvatura 0.15, anchura proporcional al volumen de ataques.
- **`flow_lines`:** misma información que `links` pero en formato compatible con la animación de partículas de ECharts.

Si la query falla, devuelve un grafo mínimo con solo PI-5 y PI-4 — el front nunca se queda sin nodos.

### 4.4 Sys info

`get_sys_info()` lee CPU/RAM/uptime con `psutil` y la IP local detectando la ruta a `8.8.8.8` (no abre conexión TCP real, solo le pregunta al kernel qué interfaz usaría). Cada métrica tiene un `try/except` independiente para que un fallo aislado no anule el resto.

## 5. Flujo de la página

```
GET /
 ├─ auth.login_required (HTTP Basic)
 ├─ get_logs()            ← 20 últimos incidentes
 ├─ get_db_stats()        ← total / críticos / bloqueos / último timestamp
 ├─ get_vector_stats()    ← distribución por servicio
 ├─ get_unique_vectors()  ← cardinalidad
 ├─ get_threat_level()    ← gauge 0-100
 ├─ get_sys_info()        ← métricas del host
 ├─ get_topology_data()   ← grafo radar
 └─ render_template('index.html', ...)

cada 5 s en el navegador:
GET /api/data
 ├─ misma carga de datos
 └─ JSON → JS actualiza DOM sin recargar
```

El template `index.html` renderiza una primera vez con datos inyectados por Jinja2 (vista inicial sin esperar AJAX). A partir de ahí, todo se refresca por polling JSON.

## 6. Autenticación

```python
auth = HTTPBasicAuth()
_AUTH_USER      = os.environ.get('DASHBOARD_USER', 'admin')
_AUTH_PASS_HASH = os.environ.get('DASHBOARD_PASSWORD_HASH', '')

# Si no hay hash pre-computado, hashear DASHBOARD_PASSWORD al arrancar.
# Si tampoco hay password en texto plano → modo dev (acceso libre con warning).
```

Esto deja tres modos:

1. **Producción:** `DASHBOARD_USER` + `DASHBOARD_PASSWORD_HASH` (hash generado con `werkzeug.security.generate_password_hash`).
2. **Despliegue rápido:** `DASHBOARD_USER` + `DASHBOARD_PASSWORD` (texto plano) — se hashea al arrancar pero queda en memoria. Útil para pruebas, no recomendado en producción.
3. **Dev sin password:** ninguna variable — acceso libre con warning en logs. Pensado para `docker compose up` rápido en local.

El usuario tiene que pasar las credenciales en cada petición (HTTP Basic) y el navegador las cachea en la sesión. No hay logout explícito (limitación de Basic Auth) — para invalidar la sesión hay que reiniciar el navegador.

## 7. Endpoint HITL: `/api/mitigate/approve`

```
POST /api/mitigate/approve
{
  "log_id":            123,
  "action":            "approve" | "reject",
  "final_command":     "sudo iptables -A INPUT -s 1.2.3.4 -j DROP",
  "confirm_critical":  true   // solo si la re-clasificación dio CRITICAL
}
```

Lógica resumida (código en `dashboard_soc.py:510` aprox):

```
1. Validar parámetros y leer la fila de logs.
2. Si action='approve':
     a) policy_engine.classify(final_command)   ← obligatorio re-validar
     b) Si nivel = CRITICAL y NO confirm_critical:
          audit(REJECT_CRITICAL_UNCONFIRMED)
          return 400 { status: "needs_confirmation", risk_level, reasons }
     c) mqtt.publish(seguridad/<device>/comando, payload, wait_for_ack=True)
        ├─ Bloquea hasta recibir PUBACK del broker (timeout 5 s).
        └─ Si la conexion esta caida o AWS rechaza el publish:
              return 502 { status: "error", message: "MQTT publish failed: <err>" }
              (la BD NO se toca; la fila sigue PENDING para reintentar)
        audit(APPROVE)
     d) UPDATE logs SET status='APPROVED',
                       estado_mitigacion=NULL,    ← resetea para esperar feedback de PI-4
                       accion_tomada += '[EJECUTADO]'
     e) return 200 { status:'dispatching', log_id }   ← NO 'success' todavia
        (el front polleara /api/mitigate/status/<id> hasta ver phase='executed')
3. Si action='reject':
     audit(REJECT)
     UPDATE logs SET status='REJECTED', accion_tomada += '[RECHAZADO]'
```

**Re-clasificación obligatoria:** aunque el agente IA propuso el comando original con nivel LOW, el humano puede haberlo editado en el modal antes de pulsar Aprobar. Si el comando editado escala a CRITICAL, el endpoint exige `confirm_critical: true` en el JSON. Esto es **doble red**: el front pinta el checkbox rojo cuando el banner lo marca CRITICAL, pero el back re-valida igualmente porque un cliente malicioso podría saltarse la validación del JS.

Detalle del modal (banner por color, checkbox CRITICAL, edición inline): [HITL_Architecture.md](HITL_Architecture.md). Detalle de cuándo escalan los niveles: [funcionamiento_policy_engine.md](funcionamiento_policy_engine.md).

## 8. Endpoint REVERT: `/revert/<id>`

Reverso operativo de una mitigación previamente aprobada por HITL o de una lectura `SAFE_READ` despachada directamente.

```
POST /revert/123
```

Lógica:

```
1. Leer la fila: ip_origen, accion_tomada, dispositivo, pending_command, status, revert_command.
2. Si NO está bloqueada (status != 'APPROVED' y no contiene 'bloque'): 400.
3. Seleccionar el comando de reversión:
     - Si el operador envió `command` en el JSON, usar ese valor editado.
     - Si la fila tiene `revert_command`, usar ese rollback explícito.
     - Si no hay rollback guardado, intentar derivar solo patrones seguros: `iptables -A/-I/--append/--insert` → `-D/--delete`, `ufw deny/reject/allow` → `ufw delete ...`, y `systemctl/service start|stop|enable|disable` → operación contraria.
     - Si no se puede derivar, devolver 400 si el comando queda vacío. El frontend deja el textarea editable vacío para que el operador escriba el rollback real.
     - Se rechaza cualquier comando que empiece por `#`; nunca se publica un comentario como reversión.
4. Re-clasificar el comando inverso con policy_engine.classify(...).
5. mqtt.publish(seguridad/<device>/comando, payload, wait_for_ack=True)
   ├─ Misma garantia que approve: espera PUBACK; si falla, return 502 sin tocar BD.
   audit(REVERT)
6. UPDATE logs SET status='REVERTED',
                  pending_command=<comando revert enviado>,
                  estado_mitigacion=NULL,        ← resetea para esperar feedback de PI-4
                  accion_tomada += '[REVERTIDO]'.
7. return 200 { status:'dispatching', log_id }   ← el front pollea igual que approve
```

La columna `pending_command` se rellena cuando entra en cuarentena HITL y también cuando se despacha directamente una acción `SAFE_READ` desde `iot_tools.py`. La columna `revert_command` guarda el rollback exacto si el agente lo pudo proponer al crear la mitigación. Si no existe rollback explícito, el dashboard solo deriva inversiones conservadoras; no inventa comandos genéricos.

**Retry loop:** la UPDATE final se reintenta hasta 3 veces con `sleep(1)` ante `database is locked` (escenario plausible si llega un INSERT desde el coordinator en paralelo). Ver detalles del modo WAL en [Database_Schema.md](Database_Schema.md).

## 8.1 Endpoint STATUS: `/api/mitigate/status/<log_id>` (GET)

Cierra el bucle de feedback operativo del HITL. Tras aprobar o revertir un comando, el front no recibe un toast definitivo de inmediato — recibe `status='dispatching'` y arranca un poll a este endpoint cada 1 s hasta 30 s.

```
GET /api/mitigate/status/123
→ 200 {
    log_id: 123,
    row_status: "APPROVED",
    phase: "awaiting_pi4" | "executed" | "failed" | "feedback",
    accion_tomada: "...",
    estado_mitigacion: null | "[EXITO] output..." | "[FALLO] ..."
  }
```

**Cómo se calcula `phase`:**

| `estado_mitigacion` | `phase` | Significado para el front |
|---|---|---|
| `NULL` o `""` | `awaiting_pi4` | Aún sin respuesta de PI-4 → sigue polleando |
| contiene `[EXITO]` | `executed` | PI-4 ejecutó OK → toast verde, refresca tabla, detiene poll |
| contiene `[FALLO]` | `failed` | PI-4 reportó error → toast rojo con detalle, detiene poll |
| otro contenido | `feedback` | Hay feedback pero sin marca clara → toast neutro |

**Quién rellena `estado_mitigacion`:** la vía rápida es `main_coordinator.process_event` → `mark_mitigation_result(log_id, ...)` en cuanto llega `seguridad/<device>/respuesta`. La vía asíncrona compatible es `feedback_agent` → `update_alert_status` cuando procesa el mensaje en su cola asíncrona — solo escribe si la rápida no llegó antes (la rápida prefija con `[EXITO]/[FALLO]`; la lenta concatena con `||`).

**Por qué este endpoint es de solo lectura:** no muta nada. Es seguro pollearlo agresivamente.

## 9. Refresco AJAX

JavaScript en `index.html` ejecuta `fetch('/api/data')` cada 5 segundos y actualiza:

- Stats numéricas (total, críticos, bloqueos, threat level).
- Tabla de los 20 últimos logs (re-render completo, no diff).
- Barras de vectores y gauge.
- Topología radar (los nodos quedan fijos, solo se refrescan los pesos de los enlaces).
- Indicador de estado MQTT (`connected` / `disconnected`).

No usa WebSockets ni SSE. Polling es suficiente para los volúmenes del MVP (decenas de eventos por minuto en el peor escenario) y simplifica el stack.

## 10. Reglas críticas

- **Nunca se suscribe a MQTT:** el dashboard solo publica. Toda la información para mostrar viene de SQLite. Esto evita carreras entre el thread MQTT del coordinador y el de Flask.
- **WAL siempre:** todas las conexiones a SQLite hacen `PRAGMA journal_mode=WAL` para permitir lecturas concurrentes con la escritura del coordinator.
- **Re-clasificación tras edición humana:** `approve_mitigation` siempre re-pasa el comando final por `policy_engine.classify`, sin asumir que coincide con el original.
- **No invalidar mitigaciones de PI-4 directamente:** si una mitigación falla (PI-4 reporta `status='error'`), eso lo gestiona de forma asíncrona el `feedback_agent` — el dashboard no toca la BD por esa razón.
- **Logs rotativos:** `/tmp/dashboard_soc.log` con `RotatingFileHandler` (5 MB × 3 archivos). En despliegue Docker se mapea al host vía volumen.

## 11. Configuración relevante

`config.yml`:

```yaml
web:
  host: "0.0.0.0"
  port: 5000

database:
  db_path: "data/soc_data.db"

mqtt:
  topic_publish_comando: "seguridad/{device}/comando"
```

`.env`:

```
DASHBOARD_USER=admin
DASHBOARD_PASSWORD=cambiame_en_produccion       # o
DASHBOARD_PASSWORD_HASH=pbkdf2:sha256:...$...   # generado con werkzeug
GEMINI_API_KEY=...                              # solo si AI_MODE != local
```

Despliegue completo: [Configuration_and_Deployment.md](Configuration_and_Deployment.md).

## 12. Archivos involucrados

```
PI-5/
├── src/
│   ├── dashboard_soc.py        # Lógica Flask completa
│   └── templates/
│       └── index.html          # Vista única (Jinja2 + JS de polling)
├── config.yml                  # web.host, web.port, mqtt.topic_publish_comando
└── tests/
    └── test_dashboard_api.py   # Smoke test del endpoint /api/data
```
