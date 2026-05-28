---
title: "Guía de Troubleshooting — Sentinel-IT (PI-5)"
author: "Daniel Alarcon"
date: "2026-05-19"
tags: ["troubleshooting", "debug", "mqtt", "docker", "errors", "502", "dns"]
---

# Guía de Troubleshooting

## 1. Propósito

Este documento recoge los **errores conocidos** del coordinador SOC (PI-5), su diagnóstico y solución. Está pensado para que, cuando algo falle, no haya que adivinar: se busca el síntoma en la tabla y se sigue el procedimiento.

No cubre errores del sensor PI-4 (ver [PI4_Referencia_Tecnica.md](PI4_Referencia_Tecnica.md)) ni problemas de la consola AWS IoT (eso es infraestructura cloud).

> **Regla de oro**: si un error se resuelve pero no se documenta aquí, se va a repetir y va a costar el doble. Añade una entrada cada vez que encuentres un problema nuevo.

---

## 2. Diagnóstico rápido: ¿Dónde miro primero?

```
¿El contenedor arranca?
  NO  → Sección 3.1 (Docker no arranca)
  SÍ  → ¿La web carga en el navegador?
          NO  → Sección 3.2 (Dashboard no responde)
          SÍ  → ¿Los datos se actualizan cada 5s?
                  NO  → Sección 3.3 (API /api/data falla)
                  SÍ  → ¿El botón "Aprobar" funciona?
                          NO  → Sección 3.4 (Error 502 en HITL)
                          SÍ  → ¿Llegan eventos de PI-4?
                                  NO  → Sección 3.5 (MQTT sin eventos)
                                  SÍ  → El sistema funciona correctamente
```

---

## 3. Errores conocidos y soluciones

### 3.1 Docker no arranca / crash-loop

#### Síntoma
```
soc-coordinator-pi5 exited with code 1
```
O el contenedor se reinicia en bucle (`docker ps` muestra `Restarting`).

#### Diagnóstico
```bash
docker logs soc-coordinator-pi5 --tail 50
```

#### Causas y soluciones

| Log del error | Causa | Solución |
|---------------|-------|----------|
| `FileNotFoundError: certificados/Pi5-dani.cert.pem` | Faltan certificados AWS IoT | Copiar los 3 archivos `.cert.pem`, `.private.key`, `root-CA.crt` a `PI-5/certificados/` |
| `FileNotFoundError: .env` | Falta el archivo `.env` | Copiar `.env.example` a `.env` y rellenar `GEMINI_API_KEY` |
| `ModuleNotFoundError: google.adk` | Dependencias no instaladas | `docker compose build --no-cache` para reconstruir la imagen |
| `AWS_IO_DNS_QUERY_FAILED` | DNS no disponible al arrancar | Ver sección 3.6 |
| `signing init failed` | Falta la clave de firma Ed25519 | `python scripts/generate_signing_keys.py` y reiniciar |

---

### 3.2 Dashboard no responde (no carga en navegador)

#### Síntoma
El navegador muestra "Conexión rechazada" o "ERR_CONNECTION_REFUSED" al acceder a `http://<ip-pi5>:5000`.

#### Diagnóstico
```bash
# ¿Está el contenedor corriendo?
docker ps | grep soc-coordinator

# ¿Flask arrancó?
docker logs soc-coordinator-pi5 | grep "Dashboard SOC started"

# ¿El puerto está mapeado?
docker port soc-coordinator-pi5
```

#### Causas y soluciones

| Situación | Causa | Solución |
|-----------|-------|----------|
| Contenedor no aparece en `docker ps` | Crash-loop | Ver sección 3.1 |
| No hay línea "Dashboard SOC started" | Flask no arrancó (error de import o config) | Revisar `docker logs` buscando `Traceback` |
| El puerto no está mapeado | Error en `docker-compose.yml` | Verificar que `ports: ["5000:5000"]` existe |
| "Dashboard SOC started" aparece pero no se accede | Firewall del host bloquea el puerto | `sudo ufw allow 5000/tcp` o equivalente |
| Se accede por IP pero no por hostname | Resolución DNS local | Usar la IP directamente: `http://192.168.1.X:5000` |

---

### 3.3 API `/api/data` falla

#### Síntoma
El dashboard carga pero los KPIs muestran 0 y la tabla está vacía, o la consola del navegador muestra errores de red en `/api/data`.

#### Diagnóstico
```bash
# Probar desde la propia Pi:
curl -u admin:PASSWORD http://localhost:5000/api/data | python3 -m json.tool
```

#### Causas y soluciones

| Situación | Causa | Solución |
|-----------|-------|----------|
| HTTP 401 Unauthorized | Credenciales incorrectas | Verificar `DASHBOARD_USER` y `DASHBOARD_PASSWORD` en `.env` |
| HTTP 500 Internal Server Error | Error en la BD | Revisar logs: `docker logs soc-coordinator-pi5 \| grep "ERROR"` |
| `sqlite3.OperationalError: no such table: logs` | BD no inicializada | Reiniciar el contenedor (ejecuta `database.py` al arrancar) |
| Datos vacíos (JSON con todo a 0) | No han llegado eventos de PI-4 | Verificar que PI-4 está publicando — ver sección 3.5 |

---

### 3.4 Error 502 al aprobar mitigación (HITL)

> ⚠️ **Este fue el error más problemático del 19/05/2026.** Se documenta con detalle extra para que no se repita.

#### Síntoma
Al pulsar "Aprobar y Ejecutar" en el modal HITL del dashboard:
- Toast rojo: "Error: MQTT publish failed: ..."
- En los logs del contenedor:
  ```
  [ERROR] Publish HITL fallo, no se actualiza DB:
  POST /api/mitigate/approve HTTP/1.1" 502
  ```

#### Anatomía del error

```
┌─────────────────────────────────────────────────────────────────────┐
│                     FLUJO NORMAL (funciona)                        │
│                                                                    │
│  Browser → POST /api/mitigate/approve                              │
│         → get_mqtt_client() → mqtt_client.is_alive() == True       │
│         → signing.sign_payload(payload)                            │
│         → mqtt_client.publish(topic, payload, wait_for_ack=True)   │
│         → publish_future.result(timeout=5) → PUBACK recibido       │
│         → UPDATE logs SET status='APPROVED'                        │
│         → 200 {status: 'dispatching'}                              │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    FLUJO ROTO (502) — antes del fix                │
│                                                                    │
│  Browser → POST /api/mitigate/approve                              │
│         → get_mqtt_client()                                        │
│           → mqtt_client is not None ✓                              │
│           → mqtt_client.connection is not None ✓  ← FALSO POSITIVO│
│           → (el socket TCP/TLS está muerto pero el objeto Python   │
│              sigue existiendo → conexión "zombie")                 │
│         → mqtt_client.publish(topic, payload, wait_for_ack=True)   │
│         → publish_future.result(timeout=5) → EXCEPCIÓN VACÍA      │
│         → except pub_err: f"...{pub_err}" → "" (sin mensaje)      │
│         → 502 {status: 'error'}                                    │
│         → BD NO SE TOCA → la fila queda en PENDING                 │
└─────────────────────────────────────────────────────────────────────┘
```

#### Causa raíz

La conexión MQTT del dashboard (`client_id: Dashboard-SOC-Pi5`) se desconectaba silenciosamente tras un corte transitorio de red o DNS. El SDK de `awscrt` no marcaba `self.connection = None` al perder la conexión — el objeto seguía existiendo pero con el socket muerto internamente.

El check en `get_mqtt_client()`:
```python
# ANTES (roto):
if mqtt_client is not None and getattr(mqtt_client, 'connection', None) is not None:
    return mqtt_client  # ← devuelve un cliente zombie
```

Devolvía `True` para una conexión muerta → el publish fallaba → 502.

#### Solución aplicada (commit `c00d61a`)

```python
# DESPUÉS (correcto):
if mqtt_client is not None and mqtt_client.is_alive():
    return mqtt_client

# Si el cliente existe pero está muerto, desconectar y reconectar:
if mqtt_client is not None:
    mqtt_client.disconnect()
    mqtt_client = None
# ... reconexión con backoff exponencial ...
```

Métodos añadidos a `AWSMqttClient`:
- **`is_alive()`**: comprueba el handle nativo `_binding` del SDK — si es `None`, la conexión fue liberada.
- **`disconnect()`**: llama `connection.disconnect()` y pone `self.connection = None`.

#### Si vuelve a pasar

1. Verificar en los logs si aparece `[WARNING] MQTT dashboard client is zombie`:
   ```bash
   docker logs soc-coordinator-pi5 | grep zombie
   ```
2. Si aparece, el fix está funcionando (detecta y reconecta).
3. Si no aparece y sigue el 502, posiblemente el endpoint de AWS IoT esté caído o los certificados hayan expirado:
   ```bash
   # Verificar conectividad desde dentro del contenedor:
   docker exec -it soc-coordinator-pi5 python3 -c "
   from aws_connector import AWSMqttClient
   c = AWSMqttClient(
       endpoint='aj4wsdnimoej8-ats.iot.eu-north-1.amazonaws.com',
       cert_path='/app/certificados/Pi5-dani.cert.pem',
       key_path='/app/certificados/Pi5-dani.private.key',
       root_ca_path='/app/certificados/root-CA.crt',
       client_id='Dashboard-SOC-test'
   )
   c.connect()
   print('OK: conexión exitosa')
   print('is_alive:', c.is_alive())
   c.disconnect()
   "
   ```

---

### 3.5 No llegan eventos de PI-4

#### Síntoma
El dashboard funciona pero no aparecen eventos nuevos. El agente IA dice "Awaiting security logs via AWS IoT MQTT...".

#### Diagnóstico
```bash
# ¿El coordinador está suscrito?
docker logs soc-coordinator-pi5 | grep "Suscrito a:"
# Debe mostrar:
# [INFO] Suscrito a: seguridad/+/telemetria
# [INFO] Suscrito a: seguridad/+/evento
# [INFO] Suscrito a: seguridad/+/respuesta

# ¿PI-4 está publicando?
# (Desde la Pi-4):
sudo systemctl status agente_monitor
```

#### Causas y soluciones

| Situación | Causa | Solución |
|-----------|-------|----------|
| No hay líneas "Suscrito a:" | Conexión MQTT falló al arrancar | Reiniciar el contenedor; revisar logs para DNS/cert errors |
| Hay suscripciones pero no llegan mensajes | PI-4 no está publicando | Verificar que el agente de PI-4 está corriendo |
| PI-4 publica pero PI-5 no recibe | Topic mismatch | Verificar que PI-4 publica en `seguridad/<device>/telemetria` (no otro path) |
| Todo OK pero eventos llegan con retraso | Latencia de red o inferencia del LLM | Comportamiento normal — el procesamiento es inmediato y asíncrono, pero la inferencia de la IA puede tardar unos segundos. |

---

### 3.6 AWS_IO_DNS_QUERY_FAILED

#### Síntoma
```
[WARNING] MQTT connect attempt 1/6 failed: AWS_IO_DNS_QUERY_FAILED
[WARNING] MQTT connect attempt 2/6 failed: AWS_IO_DNS_QUERY_FAILED
...
```

#### Causa
El resolver DNS del contenedor Docker no puede resolver el endpoint de AWS IoT (`aj4wsdnimoej8-ats.iot.eu-north-1.amazonaws.com`). Esto ocurre típicamente:
1. Al arrancar el contenedor cuando la red del host aún no está lista.
2. Si el DNS del router local tiene problemas transitorios.
3. Si Docker no hereda correctamente la configuración DNS del host.

#### Solución

**Ya implementada** en `docker-compose.yml`:
```yaml
services:
  soc-coordinator-pi5:
    dns:
      - 8.8.8.8
      - 1.1.1.1
```

Y en `main_coordinator.py`:
```python
# Retry con backoff exponencial (6 intentos, delay inicial 2s)
get_mqtt_client(max_attempts=6, initial_delay=2.0)
```

Si persiste tras los 6 intentos (~30s de espera total), el proceso arranca sin MQTT y lo reintenta en cada request del dashboard.

**Diagnóstico adicional**:
```bash
# Desde dentro del contenedor:
docker exec -it soc-coordinator-pi5 nslookup aj4wsdnimoej8-ats.iot.eu-north-1.amazonaws.com

# Desde el host:
nslookup aj4wsdnimoej8-ats.iot.eu-north-1.amazonaws.com
```

---

### 3.7 Firma rechazada por PI-4 (RECHAZADO_FIRMA)

#### Síntoma
En los logs del coordinador:
```
[INFO] Feedback registrado en DB (Dispositivo: Pi4-Felix | Status: RECHAZADO_FIRMA)
```

#### Causas y soluciones

| Causa | Diagnóstico | Solución |
|-------|------------|----------|
| Claves desincronizadas | Se generaron nuevas claves pero no se copiaron a PI-4 | Copiar `sentinel_pi5_signing.pub` a PI-4 y reiniciar ambos |
| Relojes desincronizados | `iat`/`exp` fuera de ventana | Verificar NTP: `timedatectl status` en ambos Pi. La ventana es 60s |
| Nonce repetido | Replay attack (o bug) | Si no es un ataque, verificar que no hay dos coordinadores publicando al mismo tiempo |

---

### 3.8 El agente IA no responde / tarda mucho

#### Síntoma
Los eventos se encolan pero el log muestra que el triage tarda >30s por evento.

#### Diagnóstico
```bash
docker logs soc-coordinator-pi5 | grep "Transaction complete"
# Observar el tiempo entre "[TRIAGE] Flushing X event(s)" y "[TRIAGE] Transaction complete"
```

#### Causas y soluciones

| Situación | Causa | Solución |
|-----------|-------|----------|
| Latencia >5s con `AI_MODE=api` | Gemini API lenta (red, quota) | Verificar cuota de API en Google Cloud Console |
| Latencia >30s con `AI_MODE=local` | Ollama con modelo demasiado grande | Usar modelo más pequeño: `AI_MODEL=ollama/gemma4:2b` |
| `Event from an unknown agent` en logs | Warning de ADK (no es un error) | Ignorar — es un warning del SDK de ADK que no afecta funcionalidad |

---

### 3.9 Gemini API devuelve `429 RESOURCE_EXHAUSTED`

#### Sintoma

En los logs del coordinador aparece:

```text
429 RESOURCE_EXHAUSTED
Your project has exceeded its monthly spending cap
```

O una linea resumida del coordinador:

```text
Fallo modelo API: Gemini ha superado cuota/gasto. Evento guardado como PENDING_AI_RETRY
```

#### Causa

La API remota de Gemini no acepta nuevas inferencias porque el proyecto ha superado su limite de gasto/cuota. MQTT puede seguir funcionando y el dashboard puede seguir respondiendo, pero los agentes ADK no pueden analizar nuevos eventos hasta que la API vuelva a estar disponible.

#### Comportamiento actual

El evento no se pierde. El coordinador lo guarda en SQLite, tabla `pending_ai_events`, con:

- `status='PENDING_AI_RETRY'`
- `queue_type='triage'` o `queue_type='feedback'`
- `raw_log` con el evento completo que no pudo analizarse
- `next_retry_at` calculado con backoff

El worker `_pending_ai_retry_worker()` reintenta mas tarde con el mismo modelo API. No cambia automaticamente a modelo local.

#### Diagnostico

```bash
docker exec -it soc-coordinator-pi5 python3 -c "
import sqlite3
conn = sqlite3.connect('/app/data/soc_data.db')
for row in conn.execute(\"SELECT id, device, queue_type, status, retry_count, next_retry_at FROM pending_ai_events ORDER BY id DESC LIMIT 10\"):
    print(row)
conn.close()
"
```

Tambien puede consultarse desde el dashboard/API: `/api/data` incluye el campo `pending_ai_events` con el contador de pendientes.

#### Solucion

1. Revisar el limite de gasto/cuota del proyecto Gemini.
2. Mantener `AI_MODEL=gemini-3-flash-preview` si se quiere evitar alias movibles y modelos mas caros.
3. Reiniciar el contenedor solo si se ha cambiado `.env`.
4. Esperar a que el worker procese los `PENDING_AI_RETRY` cuando la API vuelva a responder.

#### Limpieza manual

Si quieres dejar el entorno limpio, usa:

```text
SOC Manager -> 5) Desinstalar SOC -> 3) Borrar solo logs y registros
```

Esa opcion borra `logs` y `pending_ai_events`, para que no queden eventos antiguos reintentandose despues de limpiar el historial visible.

---

## 4. Cómo verificar que todo funciona

Checklist rápida para validar que el sistema está operativo:

```bash
# 1. ¿Contenedor corriendo?
docker ps | grep soc-coordinator-pi5
# Debe mostrar: Up X minutes (healthy)

# 2. ¿Dashboard accesible?
curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/
# Debe mostrar: 200

# 3. ¿MQTT conectado?
curl -s -u admin:PASSWORD http://localhost:5000/api/data | python3 -c "
import json, sys
d = json.load(sys.stdin)
print('MQTT:', d.get('mqtt_status', 'N/A'))
print('Logs:', d.get('total_logs', 0))
print('Threat:', d.get('threat_level', 0))
"

# 4. ¿Agente IA activo?
docker logs soc-coordinator-pi5 --tail 5 | grep "Autonomous SOC"
# Debe mostrar: [INFO] Autonomous SOC (ADK Powered) Active.
```

---

## 5. Comandos útiles de emergencia

```bash
# Reiniciar todo sin perder datos:
cd PI-5 && docker compose restart

# Reconstruir imagen (tras cambio de código):
cd PI-5 && docker compose up -d --build

# Ver logs en tiempo real:
docker logs -f soc-coordinator-pi5

# Acceder al contenedor:
docker exec -it soc-coordinator-pi5 bash

# Ver estado de la BD:
docker exec -it soc-coordinator-pi5 python3 -c "
import sqlite3
conn = sqlite3.connect('/app/data/soc_data.db')
c = conn.cursor()
c.execute('SELECT COUNT(*) FROM logs')
print(f'Total logs: {c.fetchone()[0]}')
c.execute('SELECT COUNT(*) FROM logs WHERE status = \"PENDING\"')
print(f'Pending HITL: {c.fetchone()[0]}')
conn.close()
"

# Forzar reconexión MQTT del dashboard (reinicia solo el proceso Flask):
docker exec -it soc-coordinator-pi5 pkill -f dashboard_soc
# (start_services.sh lo relanza automáticamente en el próximo restart)
```

---

## 6. Añadir un nuevo error a este documento

Cuando encuentres un error nuevo que te cueste más de 10 minutos resolver:

1. **Documenta el síntoma**: ¿Qué ves? ¿Qué log aparece?
2. **Documenta la causa raíz**: ¿Por qué pasa?
3. **Documenta la solución**: ¿Qué hiciste para arreglarlo?
4. **Añade una entrada** en la sección 3 con la misma estructura.
5. **Commit el cambio** con el tag `docs:` en el mensaje.

> La documentación de errores no es opcional. Un error no documentado es un error que se repetirá.
