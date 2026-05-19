---
title: "Arquitectura de Resiliencia MQTT — Sentinel-IT (PI-5)"
author: "Daniel Alarcon"
date: "2026-05-19"
tags: ["mqtt", "resilience", "reconnection", "zombie", "aws-iot", "dashboard"]
---

# Arquitectura de Resiliencia MQTT

## 1. Propósito

Este documento describe los mecanismos de **tolerancia a fallos** de las conexiones MQTT del coordinador SOC. Cubre las dos conexiones independientes que mantiene PI-5, los modos de fallo conocidos, el sistema de reconexión automática y las garantías de entrega.

No cubre el esquema de topics ni el enrutamiento de mensajes — eso vive en [funcionamiento_mqtt.md](funcionamiento_mqtt.md).

## 2. Las dos conexiones MQTT del PI-5

El coordinador mantiene **dos clientes MQTT independientes** contra AWS IoT Core:

```
┌────────────────────────────────────────────────────────────────┐
│                    CONTENEDOR PI-5                             │
│                                                                │
│  ┌──────────────────────┐   ┌────────────────────────┐        │
│  │  main_coordinator.py │   │   dashboard_soc.py     │        │
│  │                      │   │                        │        │
│  │  Client ID: Pi5-dani │   │  Client ID:            │        │
│  │                      │   │  Dashboard-SOC-Pi5     │        │
│  │  Funciones:          │   │                        │        │
│  │  - Subscribe a 3     │   │  Funciones:            │        │
│  │    topics (tele,     │   │  - Publish HITL        │        │
│  │    evento, respuesta)│   │    (approve/revert)    │        │
│  │  - Publish comandos  │   │  - Publish firmado     │        │
│  │    del agente IA     │   │    wait_for_ack=True   │        │
│  │  - Fire-and-forget   │   │  - Reconexión on-      │        │
│  │                      │   │    demand con backoff   │        │
│  └──────────┬───────────┘   └──────────┬─────────────┘        │
│             │                          │                       │
└─────────────┼──────────────────────────┼───────────────────────┘
              │                          │
              └──────────┬───────────────┘
                         │ mTLS (puerto 8883)
                         ▼
              ┌─────────────────────┐
              │   AWS IoT Core      │
              │   (eu-north-1)      │
              └─────────────────────┘
```

### ¿Por qué dos clientes?

AWS IoT Core solo permite **una conexión activa por `client_id`**. Si el coordinator y el dashboard usaran el mismo ID, se pisarían las sesiones. Además:

- El coordinator necesita **suscripciones persistentes** (`clean_session=False`) para no perder mensajes durante reinicios breves.
- El dashboard solo necesita **publicar bajo demanda** (cuando el operador aprueba/revierte), y requiere `wait_for_ack=True` para confirmar entrega.

## 3. Modos de fallo y mitigaciones

### 3.1 DNS no disponible al arrancar (contenedor Docker)

**Escenario**: Docker arranca el contenedor antes de que el resolver DNS del host esté listo. `mqtt_connection_builder.mtls_from_path()` intenta resolver el endpoint de AWS IoT y falla con `AWS_IO_DNS_QUERY_FAILED`.

**Mitigación**:

```python
# main_coordinator.py — arranque del coordinador
get_mqtt_client(max_attempts=6, initial_delay=2.0)
# Backoff: 2s, 4s, 8s, 8s, 8s, 8s = ~38s de budget máximo
```

```yaml
# docker-compose.yml — DNS de fallback
services:
  soc-coordinator-pi5:
    dns:
      - 8.8.8.8
      - 1.1.1.1
```

Si los 6 intentos fallan, el coordinador arranca sin MQTT y reintenta en cada operación que lo necesite.

### 3.2 Conexión zombie (socket muerto, objeto vivo)

**Escenario**: la conexión MQTT se establece correctamente, pero un corte transitorio de red (WiFi, router, DNS intermitente) mata el socket TCP/TLS subyacente. El SDK de `awscrt` **no** pone `self.connection = None` — el objeto Python sigue existiendo pero las operaciones sobre él fallan silenciosamente.

**Detección** (`AWSMqttClient.is_alive()`):

```python
def is_alive(self):
    if self.connection is None:
        return False
    try:
        binding = getattr(self.connection, '_binding', None)
        if binding is None:
            return False
        return True
    except Exception:
        return False
```

El handle nativo `_binding` es un puntero al objeto C del SDK. Cuando la conexión es liberada internamente (por el event loop de `awscrt` tras detectar la pérdida de socket), este handle se pone a `None`.

**Recuperación** (`get_mqtt_client()`):

```python
def get_mqtt_client(max_attempts=4, initial_delay=1.0):
    global mqtt_client, mqtt_init_error
    
    # Check 1: ¿El cliente existe y está vivo?
    if mqtt_client is not None and mqtt_client.is_alive():
        return mqtt_client
    
    # Check 2: ¿Es un zombie? → desconectar limpiamente
    if mqtt_client is not None:
        logger.warning("[WARNING] MQTT dashboard client is zombie")
        mqtt_client.disconnect()  # Libera recursos, pone connection=None
        mqtt_client = None
    
    # Check 3: Reconectar con backoff exponencial
    for attempt in range(1, max_attempts + 1):
        try:
            candidate = AWSMqttClient(...)
            candidate.connect()
            mqtt_client = candidate
            return mqtt_client
        except Exception as e:
            time.sleep(delay)
            delay = min(delay * 2, 8.0)
    
    return None  # Fallo total — el endpoint HTTP devolverá 500
```

### 3.3 Publish a conexión muerta

**Escenario**: `is_alive()` devuelve `True` pero la conexión muere entre el check y el `publish()`. El `publish_future.result()` lanza una excepción vacía (sin mensaje).

**Mitigación** (en `AWSMqttClient.publish()`):

```python
if wait_for_ack:
    try:
        publish_future.result(timeout=ack_timeout)
    except Exception as e:
        self.connection = None  # Marcar como muerto para reconexión
        error_msg = str(e) if str(e).strip() else "PUBACK timeout or connection lost"
        raise RuntimeError(f"MQTT publish failed: {error_msg}") from e
```

Esto garantiza que:
1. El mensaje de error siempre es descriptivo (nunca vacío).
2. La conexión se marca como muerta para que `get_mqtt_client()` reconecte en el siguiente intento.
3. El endpoint HTTP devuelve 502 con un mensaje útil al frontend.

## 4. Garantías de entrega por flujo

| Flujo | QoS | Modo | Garantía | Si falla |
|-------|-----|------|----------|----------|
| Agente IA → PI-4 (comando automático LOW) | QoS 1 | Fire-and-forget | Encola en event loop; no bloquea | Mensaje puede perderse silenciosamente |
| Dashboard HITL → PI-4 (approve/revert) | QoS 1 | `wait_for_ack=True` | Bloquea hasta PUBACK o timeout 5s | 502 al frontend; BD no se toca; fila queda PENDING |
| PI-4 → PI-5 (telemetría/evento) | QoS 1 | Subscribe callback | Delivery garantizada por AWS IoT | Si PI-5 está offline, AWS IoT retiene hasta `clean_session=False` expira |
| PI-4 → PI-5 (respuesta feedback) | QoS 1 | Subscribe callback | Idem | Idem |

## 5. Flujo de reconexión visual

```
Dashboard: POST /api/mitigate/approve
  │
  ├─ get_mqtt_client()
  │   ├─ mqtt_client != None && is_alive() == True
  │   │   └─ return mqtt_client ✓ (path rápido)
  │   │
  │   ├─ mqtt_client != None && is_alive() == False
  │   │   ├─ log("[WARNING] zombie — disconnecting")
  │   │   ├─ mqtt_client.disconnect()
  │   │   ├─ mqtt_client = None
  │   │   └─ → intentar reconexión (4 intentos, backoff 1-2-4-8s)
  │   │       ├─ ÉXITO → return nuevo_cliente ✓
  │   │       └─ FALLO → return None ✗
  │   │
  │   └─ mqtt_client == None
  │       └─ → intentar conexión nueva (4 intentos)
  │           ├─ ÉXITO → return nuevo_cliente ✓
  │           └─ FALLO → return None ✗
  │
  ├─ mqtt_client == None → HTTP 500 "MQTT client not connected"
  │
  ├─ signing.sign_payload(payload)
  │
  └─ mqtt_client.publish(topic, payload, wait_for_ack=True)
      ├─ is_alive() == False → RuntimeError("zombie state")
      │   └─ except → HTTP 502
      │
      ├─ publish_future.result(timeout=5s)
      │   ├─ PUBACK recibido → UPDATE logs → HTTP 200 {dispatching}
      │   └─ Exception → connection = None → HTTP 502
      │
      └─ (get_mqtt_client() reconectará en el próximo intento)
```

## 6. Configuración relacionada

```yaml
# PI-5/config.yml
aws:
  endpoint: "aj4wsdnimoej8-ats.iot.eu-north-1.amazonaws.com"

# PI-5/docker-compose.yml
services:
  soc-coordinator-pi5:
    dns:
      - 8.8.8.8      # Fallback si el DNS del host falla
      - 1.1.1.1

# Parámetros hardcoded (no configurables aún):
# - max_attempts coordinator: 6
# - max_attempts dashboard: 4
# - initial_delay: 2.0s (coordinator), 1.0s (dashboard)
# - max_delay: 8.0s
# - publish ack_timeout: 5.0s
# - keep_alive_secs: 30
```

## 7. Archivos involucrados

```
PI-5/src/
├── aws_connector.py          # AWSMqttClient: connect, is_alive, disconnect, publish
├── main_coordinator.py       # Conexión del coordinador (Pi5-dani)
├── dashboard_soc.py          # Conexión del dashboard (Dashboard-SOC-Pi5)
│                             # get_mqtt_client() con reconexión
└── tools/
    └── signing.py            # Firma de payloads antes del publish
```
