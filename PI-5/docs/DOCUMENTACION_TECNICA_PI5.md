# Sentinel IT — Documentación Técnica del Nodo Coordinador (PI-5)

> **TFG ASIR 2026 — Salesianos de Atocha**
> Autores: Daniel Alarcón Perea · Félix Tejedor Zapatero
> Este documento complementa al manual de despliegue y profundiza en los fundamentos
> teóricos y en la implementación técnica del coordinador SOC (Raspberry Pi 5).

---

## Índice

0. [Resumen ejecutivo](#0-resumen-ejecutivo)
1. [Protocolo MQTT — Fundamentos teóricos](#1-protocolo-mqtt--fundamentos-teóricos)
2. [MQTT en Sentinel IT](#2-mqtt-en-sentinel-it)
3. [Google ADK — Fundamentos teóricos](#3-google-adk--fundamentos-teóricos)
4. [ADK en Sentinel IT](#4-adk-en-sentinel-it)
5. [Arquitectura completa de la Raspberry Pi 5](#5-arquitectura-completa-de-la-raspberry-pi-5)
6. [Diagrama de síntesis del sistema](#6-diagrama-de-síntesis-del-sistema)
7. [Imágenes necesarias para integrar](#7-imágenes-necesarias-para-integrar)

---

## 0. Resumen ejecutivo

Sentinel IT es una plataforma distribuida de seguridad compuesta por dos nodos Raspberry Pi (PI-4 y PI-5) que operan en redes físicamente separadas y se comunican a través de la nube mediante el protocolo **MQTT sobre TLS** usando **AWS IoT Core** como *broker*. La PI-4 actúa como nodo protegido (servidor de cara al usuario con web, FTP, SSH y base de datos), mientras que la **PI-5 es el coordinador inteligente** que recibe la telemetría y los eventos de seguridad, los analiza mediante **agentes de IA construidos con Google ADK** (Agent Development Kit), y responde automáticamente con acciones de mitigación (bloqueos de firewall, cierre de sesiones, ejecución remota de scripts).

Este documento explica en profundidad:

- **Cómo funciona MQTT** y por qué se eligió frente a alternativas como HTTP o WebSockets.
- **Cómo funciona ADK**, el framework de agentes de Google, y cómo se ha aplicado al caso de un SOC autónomo.
- **Cómo está construida la PI-5 por dentro**: arquitectura de hilos, sistema de *batching*, base de datos SQLite, dashboard web y contenedores Docker.

---

## 1. Protocolo MQTT — Fundamentos teóricos

### 1.1 ¿Qué es MQTT?

**MQTT** (*Message Queuing Telemetry Transport*) es un protocolo de mensajería ligero, binario, orientado a publicación/suscripción, que funciona sobre TCP/IP (normalmente sobre el puerto 1883, o 8883 para TLS). Fue creado en **1999 por Andy Stanford-Clark (IBM) y Arlen Nipper (Arcom)** para monitorizar oleoductos con conexiones satelitales de muy baja velocidad. Desde 2014 es estándar abierto de **OASIS** y desde 2016 estándar **ISO/IEC 20922**.

Sus tres propiedades clave lo han convertido en el estándar *de facto* de IoT:

| Propiedad | Implicación |
|-----------|-------------|
| **Ligero** | La cabecera mínima de un paquete MQTT son 2 bytes. HTTP ronda los 200-800 bytes de *overhead*. |
| **Asíncrono** | Nadie espera a nadie. Un dispositivo puede publicar sin saber si hay alguien escuchando. |
| **Desacoplado** | Emisor y receptor no se conocen directamente: hablan a través de un *broker*. |

### 1.2 Modelo Publish/Subscribe (frente a cliente-servidor)

MQTT no sigue el modelo clásico cliente-servidor de HTTP. En HTTP, el cliente abre una conexión, hace una petición y espera una respuesta síncrona:

```
     ┌────────┐    GET /api/data    ┌────────┐
     │ Client │ ──────────────────▶ │ Server │
     │        │ ◀────────────────── │        │
     └────────┘    200 OK + JSON    └────────┘
          (acoplado, síncrono, punto a punto)
```

En MQTT hay un tercer actor — el **broker** — que desacopla productores (publishers) y consumidores (subscribers):

```
                          ┌──────────────────┐
                          │     BROKER       │
                          │  (AWS IoT Core)  │
                          │                  │
                          │  Topic: logs/#   │
                          │  Topic: alert/*  │
                          └───┬──────┬───┬───┘
                              │      │   │
           PUBLISH            │      │   │   SUBSCRIBE
         ┌────────┐           │      │   │       ┌──────────┐
         │ Sensor │───────────┘      │   └───────│  Panel A │
         │  PI-4  │                  │           └──────────┘
         └────────┘                  │           ┌──────────┐
         ┌────────┐                  └───────────│  Panel B │
         │ Sensor │──────────────────┐           └──────────┘
         │  PI-X  │                  │           ┌──────────┐
         └────────┘                  └───────────│  Logger  │
                                                 └──────────┘
```

**Ventajas del modelo pub/sub**:

1. **Escalabilidad**: añadir un subscriber nuevo no requiere tocar al publisher.
2. **Resiliencia**: si un subscriber se cae, los mensajes siguen llegando a los demás.
3. **Anonimato**: el publisher no sabe quién lo está escuchando.
4. **Multiplexación**: un publisher puede alimentar a N suscriptores sin coste extra.
5. **Filtrado**: los suscriptores solo reciben los topics que les interesan.

<!-- IMAGEN: Comparativa visual pub/sub vs request-response. Se puede hacer una captura del esquema arquitectónico de HiveMQ para referencia. -->

### 1.3 Componentes del protocolo

| Componente | Descripción |
|------------|-------------|
| **Broker** | Servidor central que recibe los mensajes de los publishers y los redirige a los subscribers. Mantiene la lista de suscripciones, gestiona los niveles de QoS y se encarga de la autenticación. Ejemplos: AWS IoT Core, Mosquitto, HiveMQ, EMQX. |
| **Client / Publisher** | Cualquier dispositivo que envía un mensaje a un *topic*. |
| **Client / Subscriber** | Cualquier dispositivo que se suscribe a uno o más *topics* para recibir mensajes. |
| **Topic** | Cadena jerárquica separada por `/` (p.ej. `casa/salon/temperatura`). No hay que crearlos: un topic existe en cuanto alguien publica o se suscribe. |
| **Message / Payload** | Contenido del mensaje. Es un array de bytes opaco para el broker. En la práctica suele ser JSON, pero podría ser texto plano, Protobuf, CBOR, etc. |

### 1.4 Topics y jerarquía

Los topics son jerárquicos, separados por el carácter `/`. A diferencia de una URL, **no tienen que empezar por `/`** y tampoco pueden contener espacios. Son **case-sensitive**.

Ejemplo de una jerarquía típica para una casa domótica:

```
casa/
├── salon/
│   ├── temperatura
│   ├── humedad
│   └── luz
├── cocina/
│   ├── temperatura
│   └── consumo_electrico
└── garaje/
    └── puerta/estado
```

#### Wildcards

Al suscribirse (no al publicar) se pueden usar dos comodines:

| Wildcard | Significado | Ejemplo | Captura |
|----------|-------------|---------|---------|
| `+` | Un único nivel de jerarquía | `casa/+/temperatura` | `casa/salon/temperatura`, `casa/cocina/temperatura`. NO `casa/salon/luz`. |
| `#` | Cero o más niveles; solo al final | `casa/#` | TODO lo que empiece por `casa/`. |

**Importante**: los wildcards *solo* valen para suscribir. Al publicar, el topic debe ser concreto.

### 1.5 Niveles de QoS (Quality of Service)

MQTT ofrece **tres niveles de garantía de entrega** que se negocian por mensaje:

#### QoS 0 — "At most once" (0 o 1 entregas)

El publisher envía el mensaje y se olvida. Ni el broker lo confirma ni se reintenta. Es el más rápido pero puede perder mensajes.

```
  Publisher                    Broker
     │                           │
     │────── PUBLISH ──────────▶│
     │                           │
   (fin)                       (fin)
```

**Usos**: telemetría de alta frecuencia donde perder un mensaje no importa (sensores que envían cada segundo).

#### QoS 1 — "At least once" (1 o más entregas)

El publisher envía el mensaje y espera un `PUBACK`. Si no llega, retransmite. Puede haber **mensajes duplicados** (el receptor debe ser idempotente o filtrar duplicados usando el `PacketId`).

```
  Publisher                    Broker
     │                           │
     │────── PUBLISH ──────────▶│
     │                           │    (reintenta si no llega PUBACK)
     │◀───── PUBACK ────────────│
     │                           │
   (fin)                       (fin)
```

**Usos**: la mayoría de casos reales. Garantiza entrega tolerando duplicados. **Es el nivel que usa Sentinel IT.**

#### QoS 2 — "Exactly once" (exactamente 1 entrega)

Handshake de cuatro pasos. Garantiza que el mensaje llega una sola vez.

```
  Publisher                    Broker
     │                           │
     │────── PUBLISH (QoS 2) ──▶│
     │◀───── PUBREC ────────────│
     │────── PUBREL ───────────▶│
     │◀───── PUBCOMP ───────────│
     │                           │
   (fin)                       (fin)
```

**Usos**: transacciones financieras, comandos industriales críticos. Es el más caro (más paquetes, más estado).

#### Comparativa

| QoS | Garantía | Overhead | Cuándo usarlo |
|-----|----------|----------|----------------|
| 0 | No garantiza nada | 1 paquete | Telemetría constante, fire-and-forget |
| 1 | Al menos una entrega | 2 paquetes | Uso general (Sentinel IT) |
| 2 | Exactamente una entrega | 4 paquetes | Transacciones críticas, comandos únicos |

### 1.6 Otras características del protocolo

- **Retained messages**: al publicar con el flag `retain=true`, el broker guarda el último mensaje de un topic y se lo entrega automáticamente a cualquier subscriber que llegue después. Útil para "último estado conocido" (p.ej. si un nuevo dashboard se conecta, recibir inmediatamente el último valor de temperatura).
- **Last Will & Testament (LWT)**: al conectar, un cliente puede registrar un mensaje que el broker publicará *en su nombre* si detecta que se ha desconectado de forma no limpia. Útil para notificar a otros sistemas que un nodo ha caído.
- **Clean Session / Persistent Session**: si un subscriber se desconecta, ¿debe el broker guardarle los mensajes pendientes para cuando vuelva? Con `clean_session=false` sí. En Sentinel IT se usa sesión persistente para que los mensajes no se pierdan durante un reinicio de PI-5.
- **Keep Alive**: el cliente promete enviar al menos un paquete cada N segundos (normalmente un `PINGREQ`). Si no lo hace, el broker considera que está muerto y puede lanzar el LWT.

### 1.7 Seguridad: TLS y mTLS

MQTT por sí mismo no cifra nada. La seguridad se añade en dos capas:

#### Capa de transporte — TLS

En lugar de TCP plano en puerto 1883 se usa **TLS sobre TCP en el puerto 8883**. Esto cifra el canal y autentica al broker (cliente verifica que el broker es quien dice ser mediante su certificado X.509 firmado por una CA).

#### Autenticación mutua — mTLS (lo que usa Sentinel IT)

No basta con que el cliente confíe en el broker. **Queremos que el broker también verifique al cliente**. Con mTLS cada cliente presenta su propio certificado X.509 firmado por una CA que el broker reconoce.

Flujo del handshake mTLS:

```
   Cliente (PI-5)                                   Broker (AWS IoT)
       │                                                   │
       │──────────── 1. ClientHello ─────────────────────▶│
       │                                                   │
       │◀─── 2. ServerHello + Certificado del broker ─────│
       │                                                   │
       │      verifica con Root CA (root-CA.crt)          │
       │                                                   │
       │────── 3. Certificado del cliente (Pi5.cert) ────▶│
       │           + firma con clave privada              │
       │                                                   │
       │                 verifica que el cert está         │
       │                 firmado por la CA de AWS y       │
       │                 asociado a una Policy que         │
       │                 permite la operación              │
       │                                                   │
       │◀──────────── 4. Conexión TLS establecida ────────│
       │                                                   │
       │══════════ MQTT sobre TLS (cifrado) ═══════════════│
```

En AWS IoT Core, cada dispositivo (*Thing*) tiene asociados:

1. **Un certificado X.509** (`Pi5-dani.cert.pem`) firmado por la CA de AWS.
2. **Una clave privada** (`Pi5-dani.private.key`) que solo vive en el dispositivo.
3. **Una Policy IoT** que define qué puede hacer ese certificado (conectar con qué `ClientId`, publicar y suscribirse a qué topics).

<!-- IMAGEN: Captura del dashboard de AWS IoT Core en "Security > Certificates" mostrando un certificado activo asociado a un Thing. -->

---

## 2. MQTT en Sentinel IT

### 2.1 Elección del broker: AWS IoT Core

Evaluamos tres alternativas antes de escoger AWS IoT Core:

| Broker | Pros | Contras | Decisión |
|--------|------|---------|----------|
| **Mosquitto local** | Gratuito, open-source, fácil de instalar | Requiere que las dos Pi estén en la misma red o abrir puertos al exterior. No hay TLS por defecto. Gestión manual de certificados. | ❌ |
| **HiveMQ Cloud Free** | Gratuito hasta 100 conexiones, TLS de serie | El plan gratuito limita a 10 MB/mes, sin política granular de permisos | ❌ |
| **AWS IoT Core** | mTLS nativo, políticas IAM por topic, ilimitado en el plan gratuito (500 000 mensajes/mes), consola visual, MQTT test client integrado | Curva de aprendizaje de AWS, región obligatoria, requiere CLI/Console | ✅ |

AWS IoT Core aporta además tres ventajas decisivas:

1. **No requiere que ambas Pi estén en la misma red.** Cada una se conecta a la nube desde su propia red doméstica (una en casa de Daniel, otra en casa de Félix). Esto simula fielmente un escenario real donde el SOC y los sensores están geográficamente distribuidos.
2. **Política IAM por topic** (ver sección 2.6).
3. **Integración natural con otros servicios AWS** (Lambda, S3, CloudWatch) si se quisiera escalar el proyecto.

### 2.2 Topología de topics del proyecto

La arquitectura de topics está diseñada en dos canales:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           AWS IoT Core Broker                           │
│                                                                         │
│  ┌───────────────────────────┐        ┌──────────────────────────────┐ │
│  │    CANAL DE ENTRADA       │        │     CANAL DE SALIDA          │ │
│  │    (PI-4 → PI-5)          │        │     (PI-5 → PI-4)            │ │
│  │                           │        │                              │ │
│  │ seguridad/clientel/       │        │ comandos/{device}            │ │
│  │   ├── telemetria          │        │   (acciones a ejecutar)      │ │
│  │   └── eventos             │        │                              │ │
│  │                           │        │ comandos/{device}/out        │ │
│  │                           │        │   (feedback del comando)     │ │
│  └───────────┬───────────────┘        └────────────┬─────────────────┘ │
└──────────────┼─────────────────────────────────────┼────────────────────┘
               │                                     │
    ┌──────────┴───────────┐            ┌───────────┴──────────┐
    │       PI-4           │            │        PI-5          │
    │   (Nodo Protegido)   │            │    (Coordinador)     │
    │                      │            │                      │
    │  PUBLISH:            │            │  SUBSCRIBE:          │
    │   seguridad/...      │            │   seguridad/#        │
    │                      │            │   comandos/+/out     │
    │  SUBSCRIBE:          │            │                      │
    │   comandos/Pi4-...   │            │  PUBLISH:            │
    │                      │            │   comandos/Pi4-...   │
    │  PUBLISH (feedback): │            │                      │
    │   comandos/Pi4-../out│            │                      │
    └──────────────────────┘            └──────────────────────┘
```

### 2.3 Suscripciones de la PI-5

La PI-5 se suscribe a **dos filtros wildcard** al arrancar. En [src/main_coordinator.py:259-260](PI-5/src/main_coordinator.py#L259-L260):

```python
global_iot_client.subscribe(TOPIC_SUBSCRIBE_LOGS, process_event)       # "seguridad/#"
global_iot_client.subscribe(TOPIC_SUBSCRIBE_COMMANDS_OUT, process_event) # "comandos/+/out"
```

| Filtro | Qué captura |
|--------|-------------|
| `seguridad/#` | **Todo** lo que publique PI-4 sobre seguridad: telemetría, eventos, logs crudos. El `#` hace que sea agnóstico a cuántos subniveles crezca PI-4 en el futuro. |
| `comandos/+/out` | El *feedback* de los comandos ejecutados. El `+` permite que exista más de un dispositivo (p.ej. mañana se añade `Pi7-juan`) sin cambiar nada. |

### 2.4 Formato de mensajes

Todos los mensajes son JSON serializados en UTF-8. Hay cuatro formas canónicas:

#### a) Telemetría periódica (PI-4 → PI-5)

Resúmenes cada X segundos de la actividad observada. Sirven para construir métricas y no para disparar alertas.

```json
{
  "timestamp": "2026-04-15T17:43:42Z",
  "sensor": "Pi4-Felix",
  "tipo": "RESUMEN_ACCESOS_WEB",
  "total_peticiones": 5,
  "detalles": [
    {"ip": "192.168.1.210", "ruta": "/index.php", "t": 1776274986},
    {"ip": "192.168.1.210", "ruta": "/login.php", "t": 1776275011}
  ]
}
```

#### b) Evento de seguridad (PI-4 → PI-5)

Un evento discreto que requiere atención del agente.

```json
{
  "ip": "192.168.1.133",
  "user": "usuariofalso",
  "timestamp": "2026-03-09T19:04:47Z",
  "evento": "FALLO_SSH",
  "prioridad": "MEDIA"
}
```

O con etiquetado de ataque explícito:

```json
{
  "sensor": "Pi4-Felix",
  "timestamp": "2026-04-15T17:42:41Z",
  "evento": "SQL_INJECTION",
  "ip": "192.168.1.134",
  "user": "a@a.com' UNION SELECT 1...",
  "prioridad": "ALTA"
}
```

#### c) Acción de mitigación (PI-5 → PI-4)

Publicadas por la PI-5 cuando el agente decide intervenir. Se envían al topic `comandos/{device}`:

```json
{
  "accion": "bloquear_ip",
  "ip": "203.0.113.45",
  "motivo": "Ataque de fuerza bruta SSH detectado (5 intentos fallidos a root en 30s)"
}
```

O un comando bash arbitrario:

```json
{
  "accion": "ejecutar_comando",
  "comando": "php /var/www/html/sentinelti.com/cerrar_sesion_admin.php --cerrar-usuario 1",
  "motivo": "Session hijacking detectado: IP 192.168.1.210 accediendo a admin.php sin login previo"
}
```

#### d) Feedback de ejecución (PI-4 → PI-5)

La PI-4 responde al `comandos/{device}/out` después de ejecutar el comando:

```json
{
  "sensor": "Pi4-Felix",
  "command": "sudo iptables -A INPUT -s 203.0.113.45 -j DROP",
  "status": "success",
  "output": "",
  "timestamp": "2026-04-15T17:43:55Z"
}
```

<!-- IMAGEN: Captura del MQTT test client de AWS IoT Core mostrando un mensaje real de evento recibido. Se entra desde IoT Core > Test > MQTT test client, se suscribe a "seguridad/#" y se hace screenshot cuando llegue un mensaje. -->

### 2.5 Autenticación mTLS y creación de identidades

Cada Raspberry Pi se registró en AWS IoT Core como un **Thing** con los siguientes artefactos:

```
AWS IoT Core > Manage > Things
│
├── Pi4-Felix                            (Raspberry Pi 4 - Nodo protegido)
│   ├── Certificate: Pi4-Felix.cert.pem
│   ├── Private Key: Pi4-Felix.private.key
│   ├── Public Key:  Pi4-Felix.public.key
│   └── Policy:      Pi4-Felix-Policy
│
├── Pi5-dani                             (Raspberry Pi 5 - Coordinador)
│   ├── Certificate: Pi5-dani.cert.pem
│   ├── Private Key: Pi5-dani.private.key
│   └── Policy:      Sentinel-IT-Policy
│
└── Dashboard-SOC-Pi5                    (Cliente MQTT del dashboard)
    └── (comparte certificado con Pi5-dani pero usa ClientId distinto)
```

El archivo `root-CA.crt` es la cadena de certificados raíz de Amazon (`AmazonRootCA1.pem`) que permite al cliente verificar la autenticidad del broker.

El flujo para crear un Thing nuevo (resumen del procedimiento de AWS):

1. En la consola de AWS IoT Core → **Manage → Things → Create single thing**.
2. Seleccionar **Auto-generate a new certificate**.
3. Descargar los tres archivos: certificado, clave privada, clave pública.
4. Descargar el Root CA de Amazon (AmazonRootCA1).
5. Activar el certificado.
6. Asociarle la Policy (ver siguiente sección).
7. Asociar el certificado al Thing.

<!-- IMAGEN: Captura de la lista de Things en AWS IoT Core > Manage > Things, mostrando Pi4-Felix y Pi5-dani activos. -->

<!-- IMAGEN: Captura del detalle de un certificado en AWS IoT Core con estado "Active" y el Thing/Policy asociados. -->

### 2.6 Política IAM (Policy.json) — principio de mínimo privilegio

La Policy define qué puede hacer cada certificado. Aplicamos el **principio de mínimo privilegio**: solo se permite lo estrictamente necesario, sobre los topics concretos del proyecto, para los ClientIds concretos.

Contenido de [Policy.json](PI-5/Policy.json):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "iot:Connect",
      "Resource": [
        "arn:aws:iot:eu-north-1:582997418897:client/Pi5-dani",
        "arn:aws:iot:eu-north-1:582997418897:client/Pi4-felix",
        "arn:aws:iot:eu-north-1:582997418897:client/Dashboard-SOC-Pi5"
      ]
    },
    {
      "Effect": "Allow",
      "Action": ["iot:Publish", "iot:Receive", "iot:RetainPublish"],
      "Resource": [
        "arn:aws:iot:eu-north-1:582997418897:topic/seguridad/*",
        "arn:aws:iot:eu-north-1:582997418897:topic/comandos/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": "iot:Subscribe",
      "Resource": [
        "arn:aws:iot:eu-north-1:582997418897:topicfilter/seguridad/*",
        "arn:aws:iot:eu-north-1:582997418897:topicfilter/comandos/*"
      ]
    }
  ]
}
```

Interpretación:

| Statement | Qué permite | Qué bloquea implícitamente |
|-----------|-------------|-----------------------------|
| `iot:Connect` | Solo los tres ClientIds listados. | Cualquiera con el certificado que intente usar otro ClientId. |
| `iot:Publish/Receive` | Publicar/recibir solo en `seguridad/*` y `comandos/*`. | Publicar en `$aws/*`, `test/*`, `admin/*`, etc. |
| `iot:Subscribe` | Suscribirse solo a esos dos árboles. | Espiar cualquier otro topic ajeno al proyecto. |

Obsérvese que la Policy usa `topic/` para Publish/Receive y `topicfilter/` para Subscribe — esta distinción es propia de IAM en AWS IoT Core.

### 2.7 Implementación del cliente MQTT — análisis de `aws_connector.py`

El archivo [src/aws_connector.py](PI-5/src/aws_connector.py) encapsula toda la interacción con AWS IoT en una clase `AWSMqttClient`. Se apoya en el SDK oficial `awsiotsdk` (paquete `awsiot` + `awscrt`).

```python
class AWSMqttClient:
    def __init__(self, endpoint, cert_path, key_path, root_ca_path, client_id):
        self.endpoint = endpoint          # Ej. "aj4wsdnimoej8-ats.iot.eu-north-1.amazonaws.com"
        self.cert_path = cert_path        # Certificado X.509 del dispositivo
        self.key_path = key_path          # Clave privada asociada al certificado
        self.root_ca_path = root_ca_path  # CA raíz de Amazon
        self.client_id = client_id        # Identificador único del cliente MQTT
        self.connection = None
```

**Conexión mTLS** ([aws_connector.py:23-39](PI-5/src/aws_connector.py#L23-L39)):

```python
mqtt_connection = mqtt_connection_builder.mtls_from_path(
    endpoint=self.endpoint,
    cert_filepath=self.cert_path,
    pri_key_filepath=self.key_path,
    ca_filepath=self.root_ca_path,
    client_id=self.client_id,
    clean_session=False,       # Sesión persistente: no perder mensajes si nos reconectamos
    keep_alive_secs=30         # Ping al broker cada 30 s
)
connect_future = mqtt_connection.connect()
connect_future.result()        # Bloquea hasta confirmar la conexión
```

Puntos clave:

- `mtls_from_path` construye la conexión TLS con autenticación mutua desde archivos en disco. Internamente configura el contexto OpenSSL con los tres archivos.
- `clean_session=False` garantiza que si PI-5 se reinicia, el broker mantendrá los mensajes pendientes asociados a su `client_id`.
- `keep_alive_secs=30` fija el intervalo máximo entre pings. Si la Pi lleva más de 30 s sin enviar nada, mandará un `PINGREQ` para demostrar que sigue viva.

**Publicación** ([aws_connector.py:41-55](PI-5/src/aws_connector.py#L41-L55)):

```python
def publish(self, topic, payload_dict):
    message_json = json.dumps(payload_dict)
    self.connection.publish(
        topic=topic,
        payload=message_json,
        qos=mqtt.QoS.AT_LEAST_ONCE   # QoS 1
    )
```

**Suscripción** ([aws_connector.py:57-71](PI-5/src/aws_connector.py#L57-L71)):

```python
def subscribe(self, topic, callback_function):
    subscribe_future, packet_id = self.connection.subscribe(
        topic=topic,
        qos=mqtt.QoS.AT_LEAST_ONCE,
        callback=callback_function   # Función invocada por cada mensaje que llegue
    )
    subscribe_future.result()
```

La función `callback_function` es ejecutada **en un hilo del pool del SDK** cada vez que llega un mensaje, con la firma `(topic, payload, **kwargs)`. En Sentinel IT ese callback es [process_event()](PI-5/src/main_coordinator.py#L203) (analizado en la sección 5).

### 2.8 Justificación de QoS 1

Se eligió `AT_LEAST_ONCE` (QoS 1) frente a QoS 0 o 2 por un balance entre fiabilidad y coste:

- **Frente a QoS 0**: un ataque puede estar contenido en un único mensaje. Perderlo porque la red parpadea no es aceptable en un SOC.
- **Frente a QoS 2**: el *overhead* de los 4 paquetes de handshake multiplica el tráfico por 2. Como las herramientas de la base de datos (`register_alert`, `update_alert_status`) son **idempotentes a nivel lógico** (si llega dos veces una orden de bloqueo para la misma IP, la segunda es inofensiva), los duplicados de QoS 1 no son un problema.

---

## 3. Google ADK — Fundamentos teóricos

### 3.1 ¿Qué es ADK?

**ADK** (*Agent Development Kit*) es un framework open-source publicado por **Google en abril de 2025** para construir agentes de IA. Se instala como un paquete Python (`google-adk`) y es el mismo framework que usa Google internamente para productos como **Agentspace** y **Google Agent Builder**.

La filosofía de ADK es tratar a los agentes como **workflows deterministas con un LLM en el núcleo**. Frente a otros frameworks como LangChain (que propone un estilo más libre y encadenado) o AutoGPT (que da al LLM control total), ADK propone:

1. **Código Python primero**: los agentes, las herramientas y los flujos son código normal.
2. **Deterministas donde puedes, LLM donde debes**: la lógica de orquestación es código fijo; el LLM solo interviene cuando hace falta razonar.
3. **Rico en primitivas**: tiene clases específicas para *multi-agent*, *sequential*, *parallel*, *loop*, etc.
4. **Agnóstico del modelo**: funciona con Gemini nativo, modelos de Vertex AI, y **LiteLLM** (adaptador que expone +100 modelos — OpenAI, Anthropic, Ollama, Mistral, etc. — con una API unificada).

### 3.2 Componentes clave

La arquitectura mínima de una aplicación ADK se compone de cuatro piezas:

```
   ┌─────────────┐
   │    RUNNER   │  ← Orquestador: coordina LLM, sesión y tools
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐      ┌───────────────────┐
   │    AGENT    │─────▶│  SessionService   │  ← Memoria: historial de mensajes
   │  (LlmAgent) │      └───────────────────┘
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐
   │    TOOLS    │  ← Funciones Python que el LLM puede invocar
   └─────────────┘
```

#### Agent / LlmAgent

Un `Agent` en ADK es la unidad lógica de razonamiento. `LlmAgent` es la implementación más usada: un agente cuyo núcleo es un LLM que razona en lenguaje natural.

Se define con:

- `name`: identificador único.
- `model`: el modelo subyacente (Gemini, LiteLLM-wrapped, etc.).
- `description`: frase corta que describe qué hace. Se usa cuando varios agentes conviven y uno debe delegar a otro.
- `instruction`: el *system prompt*. Es la parte más importante — define el comportamiento.
- `tools`: lista de funciones que el agente puede llamar.

#### Runner

El `Runner` es el ejecutor. Recibe un mensaje del usuario, lo inyecta en la sesión, invoca al LLM, recoge las respuestas, ejecuta los *tool calls* si los hay, vuelve a invocar al LLM con los resultados, y así hasta que el LLM emita una respuesta final en texto.

El ciclo de ejecución:

```
  ┌────────────┐
  │  Mensaje   │
  │  entrante  │
  └─────┬──────┘
        ▼
  ┌────────────┐     ┌──────────────┐
  │  Runner    │────▶│  Session:    │
  │            │     │  + user msg  │
  └─────┬──────┘     └──────────────┘
        ▼
  ┌────────────┐
  │    LLM     │  ← recibe (instruction + sesión + tool schemas)
  │  razona    │
  └─────┬──────┘
        │
        ├──► decide: ¿llamar a una tool?
        │           │
        │           ▼
        │    ┌────────────┐
        │    │ ejecuta    │
        │    │ la función │
        │    │ Python     │
        │    └─────┬──────┘
        │          │
        │          ▼
        │    ┌─────────────┐
        │    │ resultado   │──┐
        │    │ → sesión    │  │
        │    └─────────────┘  │
        │                     │
        │◀────────────────────┘
        │  (el LLM razona otra vez con el nuevo contexto)
        │
        └──► emite respuesta final en texto
                     │
                     ▼
                  (END)
```

Este ciclo puede repetirse varias veces dentro de una sola invocación de `runner.run()`. Por eso los prompts llevan reglas como "después de llamar a `block_ip`, STOP": para evitar bucles infinitos.

#### SessionService

La `Session` es el equivalente a la memoria de una conversación. Guarda los mensajes del usuario, las respuestas del LLM y los resultados de las tools. Se pasa al LLM como contexto en cada invocación.

ADK ofrece tres implementaciones:

| Implementación | Descripción | Uso |
|----------------|-------------|-----|
| `InMemorySessionService` | En memoria RAM, se pierde al reiniciar | Testing y prototipos. **Es la que usamos.** |
| `DatabaseSessionService` | Persistencia en SQLite/Postgres | Producción con historial auditable |
| `VertexAiSessionService` | Gestionada en Vertex AI | Integración con ecosistema Google Cloud |

#### Tools

Una *tool* es una función Python normal que ADK expone al LLM. **ADK extrae automáticamente** del código Python:

- El nombre → nombre de la tool.
- La firma y los *type hints* → schema JSON.
- La docstring → descripción y descripciones de parámetros.

Ejemplo de cómo ve el LLM una tool:

```python
# Código Python en src/tools/iot_tools.py
def block_ip(device: str, ip: str, reason: str) -> dict:
    """
    Ordena el bloqueo de una IP en el firewall del dispositivo remoto.
    Esta herramienta debe usarse ante ataques confirmados.

    Args:
        device: ID del dispositivo objetivo (ej. Pi4-dani).
        ip: Direccion IPv4/IPv6 a neutralizar.
        reason: Justificacion concisa del bloqueo basada en el analisis.
    """
    ...
```

ADK transforma esto automáticamente en un esquema JSON que el modelo puede interpretar:

```json
{
  "name": "block_ip",
  "description": "Ordena el bloqueo de una IP en el firewall del dispositivo remoto...",
  "parameters": {
    "type": "object",
    "properties": {
      "device": {"type": "string", "description": "ID del dispositivo objetivo (ej. Pi4-dani)."},
      "ip":     {"type": "string", "description": "Direccion IPv4/IPv6 a neutralizar."},
      "reason": {"type": "string", "description": "Justificacion concisa del bloqueo..."}
    },
    "required": ["device", "ip", "reason"]
  }
}
```

Cuando el LLM decide llamar a la tool, emite una respuesta estructurada del tipo:

```json
{
  "tool_call": {
    "name": "block_ip",
    "arguments": {
      "device": "Pi4-Felix",
      "ip": "203.0.113.45",
      "reason": "Ataque fuerza bruta SSH: 10 fallos en 15 s desde esta IP"
    }
  }
}
```

ADK intercepta esa respuesta, ejecuta la función real `block_ip(device="Pi4-Felix", ip=...)`, captura el valor devuelto y lo re-inyecta en la siguiente invocación al LLM para que pueda razonar sobre el resultado.

### 3.3 Integración con modelos — Gemini nativo, LiteLLM y Ollama

ADK acepta `model` con tres formas:

1. **String con nombre de modelo Google**: `"gemini-2.5-flash"` → usa la API de Google AI directamente con `GEMINI_API_KEY`.
2. **Instancia de `LiteLlm`**: `LiteLlm(model="ollama/gemma3:4b")` → usa LiteLLM como capa de traducción hacia cualquier modelo.
3. **String de modelo Vertex**: `"projects/.../locations/.../publishers/google/models/..."` → para Vertex AI.

LiteLLM es crucial para Sentinel IT porque permite conmutar entre Gemini (nube) y Ollama (local) sin cambiar el código del agente, solo la variable de entorno `AI_MODE`.

### 3.4 `description` vs `instruction`

Dos campos muy importantes del `LlmAgent` que se confunden a menudo:

| Campo | Destinatario | Uso |
|-------|--------------|-----|
| `description` | Otros agentes que necesiten decidir si delegar a este. | "Level 1 Analyst specialized in parsing logs and applying firewall blocks". |
| `instruction` | El propio LLM en cada invocación (es el *system prompt*). | Instrucciones detalladas: cómo pensar, qué tools usar, cuándo parar. |

En un sistema con un solo agente como el Triage, `description` casi no importa. Cobra valor cuando se construye un *multi-agent* donde un router/orquestador decide a qué subagente delegar.

### 3.5 ¿Por qué ADK y no otro framework?

Comparativa rápida con alternativas:

| Framework | Ventaja | Desventaja | Para Sentinel IT |
|-----------|---------|------------|------------------|
| **LangChain** | Ecosistema masivo, integraciones | API inestable, curva de aprendizaje alta, *overhead* | Sobredimensionado |
| **LlamaIndex** | Pensado para RAG | No está pensado para agentes de acción | No encaja |
| **AutoGen (Microsoft)** | Multi-agent muy potente | Más complejo, foco en conversación entre agentes | Excesivo |
| **ADK (Google)** | Simple, Pythonic, soporte oficial de Gemini, LiteLLM integrado | Nuevo (2025), comunidad más pequeña | ✅ Ideal |
| **Código a mano** | Control total | Reinventar la rueda: tool calling, sesiones, streaming... | Demasiado trabajo |

ADK encaja por tres razones:

1. **Gemini 2.5 es uno de los mejores modelos gratuitos para tool calling** (la API de Google AI tiene un plan gratuito razonable), y ADK es su framework nativo.
2. **LiteLLM integrado** permite pasar a Ollama sin cambiar líneas de código — crítico para la demo en local.
3. **La estructura mental** ("agente = prompt + tools + sesión") es la más limpia para explicar el proyecto en la defensa.

---

## 4. ADK en Sentinel IT

### 4.1 Arquitectura de doble agente — Triage + Feedback

En lugar de tener un solo agente omnisciente, hemos dividido la responsabilidad en dos agentes especializados. Esto sigue el principio de separación de responsabilidades y el patrón **"Level 1 / Level 2 analyst"** de los SOC reales:

```
                    ┌──────────────────────────────────────────┐
                    │              AWS IoT Core                │
                    └─┬────────────────────────────┬───────────┘
                      │                            │
       eventos        │                            │  feedback
       seguridad/#    │                            │  comandos/+/out
                      ▼                            ▼
              ┌──────────────┐            ┌──────────────┐
              │  Cola Triage │            │Cola Feedback │
              │  (BatchQueue)│            │  (BatchQueue)│
              └───────┬──────┘            └───────┬──────┘
                      │                           │
                      ▼                           ▼
         ┌─────────────────────┐      ┌─────────────────────┐
         │  AGENTE L1 TRIAGE   │      │  AGENTE L2 FEEDBACK │
         │  (SOC_Triage_Agent) │      │(SOC_Feedback_Agent) │
         │                     │      │                     │
         │  Tools:             │      │  Tools:             │
         │   • register_alert  │      │   • update_alert_.. │
         │   • block_ip        │      │   • execute_remote_.│
         │   • execute_remote_.│      │                     │
         └─────────┬───────────┘      └──────────┬──────────┘
                   │                             │
                   ▼                             ▼
           ┌──────────────┐             ┌──────────────┐
           │  SQLite BD   │             │  SQLite BD   │
           │  (INSERT)    │             │  (UPDATE)    │
           └──────────────┘             └──────────────┘
```

**Responsabilidades del Triage (L1)**:

- Clasificar logs crudos.
- Decidir si hay ataque.
- Registrar en BD mediante `register_alert`.
- Ordenar mitigación (`block_ip` o `execute_remote_command`).

**Responsabilidades del Feedback (L2)**:

- Leer la salida del comando ejecutado en PI-4.
- Decidir si funcionó.
- Actualizar el registro con `update_alert_status`.
- Si falló, puede reintentar con un comando alternativo.

**Por qué separarlos en lugar de un único agente**:

1. **Prompts más cortos y afilados** → mejor precisión, menos tokens.
2. **Herramientas reducidas** → menos probabilidad de que el LLM llame la tool equivocada.
3. **Trazabilidad**: cada agente genera sus propios logs, se ve claramente quién hizo qué.
4. **Escalabilidad**: mañana puede añadirse un tercer agente (L3 — reportes ejecutivos) sin tocar los otros dos.

### 4.2 Configuración híbrida local/API

Los dos agentes comparten exactamente la misma lógica de inicialización, gobernada por dos variables de entorno del archivo `.env`:

```bash
# Modo local (Ollama en Docker)
AI_MODE=local
AI_MODEL=ollama/gemma3:4b

# Modo API (Gemini en la nube)
AI_MODE=api
AI_MODEL=gemini-2.5-flash
GEMINI_API_KEY=AIza...
```

El código de [triage_agent.py](PI-5/src/agents/triage_agent/triage_agent.py#L22-L29) lee ambas y decide qué backend usar:

```python
if ai_mode == "local":
    os.environ["OLLAMA_API_BASE"] = "http://local-ai-engine:11434"
    model_config = LiteLlm(model=ai_model_name)      # Wrapping vía LiteLLM
else:
    model_config = ai_model_name                     # String directo para Gemini API
```

El nombre del host `local-ai-engine` corresponde al contenedor Docker del servicio Ollama definido en [docker-compose.yml](PI-5/docker-compose.yml#L29-L36). Gracias a la red interna de Docker, los dos contenedores se ven por nombre.

### 4.3 Análisis del prompt del Triage Agent

El prompt de [src/agents/triage_agent/triage_agent.py](PI-5/src/agents/triage_agent/triage_agent.py#L36-L85) está cuidadosamente estructurado en cinco bloques:

#### Bloque 1 — "IoT Environment Specification"

Contexto fijo de la infraestructura (firewall iptables, comandos permitidos, directorios sensibles). El LLM tiene que saber **qué herramientas existen en el sistema** para poder dar instrucciones correctas:

```
- block_ip: sudo iptables -A INPUT -s <IP> -j DROP
- unblock_ip: sudo iptables -D INPUT -s <IP> -j DROP
- Directorios de interés: /etc/shadow, /var/www/html, /opt/sentinel-it/scripts
```

#### Bloque 2 — "Forensic Chain-of-Thought"

Le indica al LLM **cómo razonar antes de actuar**, en tres preguntas:

1. **Who & Where**: extraer la IP origen y el dispositivo atacado.
2. **What & How**: ¿es un log de texto SSH? ¿un JSON con evento etiquetado? ¿telemetría?
3. **Decide Action**: formular la respuesta.

Este patrón fuerza al modelo a estructurar su razonamiento y mejora notablemente la precisión en modelos pequeños (gemma3:4b en Ollama).

#### Bloque 3 — "Mitigation Protocols"

Define **reglas duras** de cuándo actuar:

- Tráfico benigno o telemetría rutinaria → **no hacer nada**, no llamar a `register_alert` para evitar inundar la BD.
- Ataque confirmado → `register_alert` **obligatorio** + `block_ip` o `execute_remote_command`.

#### Bloque 4 — "Surgical Tool Usage"

Instrucciones específicas sobre cómo usar las tools:

- `block_ip` para amenazas identificables por IP.
- `execute_remote_command` cuando se necesite un comando fino (cerrar sesión, reiniciar nginx...). El prompt aclara explícitamente que se tiene **acceso root** a la máquina remota.

#### Bloque 5 — "Critical Execution Rules" (las más importantes)

Son anti-patterns que evitan bugs típicos de agentes LLM:

```
- Call register_alert EXACTLY ONCE for a threat.
- If you call register_alert, your IMMEDIATELY next action should be block_ip
  or execute_remote_command. Do not ask for permission.
- After calling the mitigation tools, YOU MUST STOP tool execution.
- Finish your turn by replying with a regular TEXT message summarizing what you did.
- DO NOT hallucinate tools like `SOC_Root_Agent`. Use ONLY the tools provided.
```

Estas reglas resolvieron problemas reales observados durante el desarrollo:

- Sin "EXACTLY ONCE" el modelo llamaba a `register_alert` varias veces con la misma alerta (duplicados en BD).
- Sin "STOP tool execution" el modelo entraba en bucles tool-calling infinitos.
- Sin "DO NOT hallucinate" el modelo inventaba nombres de tools no registradas (común en modelos pequeños).

### 4.4 El Feedback Agent (Level 2)

El prompt del Feedback es mucho más corto porque su misión es más acotada. Ver [src/agents/feedback_agent/feedback_agent.py](PI-5/src/agents/feedback_agent/feedback_agent.py#L26-L55):

```
### YOUR MISSION:
1. Parse the JSON to identify: sensor, status, output.
2. Action 1: Register Feedback via `update_alert_status`.
3. Action 2: Escalation — if status was "error", try alternative fix.
```

El agente L2 recibe un JSON como:

```json
{
  "sensor": "Pi4-Felix",
  "command": "sudo iptables -A INPUT -s 203.0.113.45 -j DROP",
  "status": "success",
  "output": ""
}
```

Y debe:

1. Extraer el device, el status y el output.
2. Llamar `update_alert_status(device, output, mitigation_status)` donde `mitigation_status` es `"EXITO"` o `"FALLO"`.
3. Si falló, opcionalmente ejecutar un comando correctivo (p.ej. `sudo systemctl restart nginx`).

### 4.5 Las cuatro tools

Vamos a analizar cada tool a fondo. Las tools son el "brazo" del agente: convierten el razonamiento en acciones reales en el mundo.

#### 4.5.1 `register_alert` — persistir en SQLite

Ubicación: [src/tools/db_tools.py:69](PI-5/src/tools/db_tools.py#L69).

```python
def register_alert(device: str, attack_vector: str, source_ip: str,
                   severity: str, verdict: str, raw_log: str) -> dict:
    """
    Registra un incidente de seguridad en la base de datos local.
    """
```

| Parámetro | Ejemplo |
|-----------|---------|
| `device` | `"Pi4-Felix"` |
| `attack_vector` | `"SSH"`, `"NGINX-HTTP"`, `"MYSQL"`, `"PORT-SCAN"` |
| `source_ip` | `"203.0.113.45"` |
| `severity` | `"Baja"`, `"Media"`, `"Alta"`, `"Crítica"` |
| `verdict` | Cadena con el razonamiento del agente ("5 fallos SSH a root en 30s → fuerza bruta") |
| `raw_log` | Log original sin tocar |

Detalles de implementación:

- Antes del insert, llama a `rotate_old_logs()` si la retención está activa, eliminando registros de baja criticidad con más de 30 días.
- Abre la conexión con `PRAGMA journal_mode=WAL` (Write-Ahead Logging) para permitir lectores y escritores en paralelo.
- Política de 5 reintentos con `time.sleep(2)` si la BD está bloqueada (la WAL puede bloquear brevemente durante *checkpoint*).
- Devuelve un `dict` que el LLM lee para saber el resultado: `{"status": "success", "message": "..."}`.

El mensaje de retorno contiene una **instrucción al propio LLM**:

```python
return {"status": "success", "message": "Log guardado correctamente. NO LLAMAR a register_alert de nuevo. Procede con block_ip si es necesario."}
```

Esto es una técnica sutil pero efectiva: el mensaje de la tool actúa como un "recordatorio" inyectado en el contexto del LLM que refuerza las reglas del prompt.

#### 4.5.2 `block_ip` — ordenar bloqueo a PI-4

Ubicación: [src/tools/iot_tools.py:32](PI-5/src/tools/iot_tools.py#L32).

Hace dos cosas en una:

1. **Publica** el JSON de orden de bloqueo al topic `comandos/{device}`:

```python
action_payload = {
    "accion": "bloquear_ip",
    "ip": ip,
    "motivo": reason
}
self._iot_client.publish(response_topic, action_payload)
```

2. **Actualiza la BD** marcando la acción como *"Bloqueo Activo Emitido"*, lo que queda reflejado en la columna `accion_tomada`.

Obsérvese que la tool **no espera** confirmación de ejecución. Esa parte la hace asíncronamente el Feedback Agent cuando llega el mensaje a `comandos/{device}/out`.

#### 4.5.3 `execute_remote_command` — comando arbitrario

Ubicación: [src/tools/iot_tools.py:88](PI-5/src/tools/iot_tools.py#L88).

Es la "navaja suiza" del agente: publica cualquier script bash que el LLM considere oportuno. Ejemplos típicos:

```bash
# Cerrar sesión web de un atacante
php /var/www/html/sentinelti.com/cerrar_sesion_admin.php --cerrar-usuario 1

# Reiniciar nginx si está caído
sudo systemctl restart nginx

# Desbloquear una IP (para acciones de revert)
sudo iptables -D INPUT -s 192.168.1.133 -j DROP

# Listar usuarios activos
who
```

El payload publicado:

```json
{
  "accion": "ejecutar_comando",
  "comando": "php /var/www/html/sentinelti.com/cerrar_sesion_admin.php --cerrar-usuario 1",
  "motivo": "Session hijacking detectado: cookie duplicada en IP 192.168.1.210"
}
```

Esta tool es la más poderosa y la más peligrosa: el agente tiene efectivamente **acceso root remoto** a PI-4. Por eso el prompt incluye de forma explícita:

```
*Constraint*: Provide RAW bash commands only. No markdown formatting inside the command string.
```

#### 4.5.4 `update_alert_status` — cerrar el ciclo

Ubicación: [src/tools/db_tools.py:114](PI-5/src/tools/db_tools.py#L114).

Lo usa el Feedback Agent para registrar si el comando funcionó:

```python
cursor.execute('''
    UPDATE logs
    SET estado_mitigacion = ?
    WHERE id = (
        SELECT id FROM logs
        WHERE dispositivo = ?
        ORDER BY timestamp DESC
        LIMIT 1
    )
''', (f"[{mitigation_status}] {command_result}", device))
```

Actualiza la fila más reciente del dispositivo, grabando el resultado con prefijo `[EXITO]` o `[FALLO]`. Ejemplos de valores finales:

- `[EXITO] ` (cuando el comando devolvió success sin output)
- `[FALLO] iptables: command not found`
- `[EXITO] Sesiones cerradas: 1`

### 4.6 Inyección de dependencias del cliente IoT

Las tools `block_ip` y `execute_remote_command` necesitan publicar en MQTT, pero **no deben tener su propio cliente**: queremos reutilizar la conexión que abre el coordinador principal. Esto se resuelve con un patrón de inyección explícita:

```python
# En src/tools/iot_tools.py
_iot_client = None  # módulo-global

def init_iot_tools(iot_client):
    global _iot_client
    _iot_client = iot_client
```

Y en el coordinador, al arrancar ([main_coordinator.py:251](PI-5/src/main_coordinator.py#L251)):

```python
global_iot_client = AWSMqttClient(...)
global_iot_client.connect()
init_iot_tools(global_iot_client)   # ← inyección
```

A partir de ese momento, cada vez que el agente llame a `block_ip`, dentro de la función `_iot_client` está apuntando al mismo objeto que recibe los mensajes entrantes. Una sola conexión para todo.

### 4.7 Sesiones con `InMemorySessionService`

En [main_coordinator.py:61-77](PI-5/src/main_coordinator.py#L61-L77) vemos la inicialización:

```python
_session_service = InMemorySessionService()
_runner_triage = Runner(
    app_name=APP_NAME,
    agent=triage_agent,
    session_service=_session_service,
)
_session = asyncio.run(
    _session_service.create_session(app_name=APP_NAME, user_id=USER_ID)
)
```

Una **única sesión compartida** por ambos agentes y reutilizada durante toda la vida del coordinador. Esto tiene implicaciones:

- **Pro**: el agente ve el histórico de eventos recientes, lo que le da contexto (por ejemplo, "ya había bloqueado esta IP hace 2 minutos").
- **Contra**: la sesión crece indefinidamente. En producción habría que implementar rotación o usar `DatabaseSessionService` con TTL.

Para un TFG con cargas bajas, `InMemorySessionService` es suficiente.

### 4.8 Ollama local vs Gemini API

| Aspecto | **Ollama local (gemma3:4b)** | **Gemini 2.5 Flash API** |
|---------|-----------------------------|--------------------------|
| **Privacidad** | Los logs nunca salen de la Pi | Google procesa los logs |
| **Coste** | 0 € | Plan gratuito generoso, después pago por token |
| **Latencia** | 5-20 s por respuesta (Pi5 con 8 GB RAM) | 1-3 s |
| **Calidad del razonamiento** | Suficiente para casos sencillos | Notablemente mejor, especialmente con logs largos |
| **Requisitos hardware** | 4-8 GB RAM libres, >10 GB disco para el modelo | Ninguno (solo conexión) |
| **Modo de fallo** | Si Ollama cae, el agente no razona | Si hay corte de internet o cuota agotada, el agente no razona |
| **Auditabilidad** | Control total del entorno | Depende de las garantías de Google |

La conmutación entre ambos se hace cambiando `AI_MODE` en `.env` y reiniciando el contenedor. **Para la defensa del TFG se demostrará en los dos modos**: primero con Gemini para mostrar la calidad máxima, después con Ollama para mostrar que el sistema es operable *air-gapped* (sin internet).

<!-- IMAGEN: Captura de Ollama corriendo (docker exec local-ai-engine ollama list), mostrando el modelo gemma3 descargado. -->

<!-- IMAGEN: Captura de Google AI Studio mostrando la API Key activa (TAPAR la key real). -->

---

## 5. Arquitectura completa de la Raspberry Pi 5

### 5.1 Diagrama de componentes

```
┌────────────────────────────────────────────────────────────────────────────┐
│                          CONTENEDOR DOCKER: soc-coordinator-pi5            │
│                                                                            │
│  ┌──────────────────┐          ┌──────────────────────────────────────┐   │
│  │  start_services  │          │         HILO PRINCIPAL               │   │
│  │       .sh        │──lanza──▶│         (main_coordinator.py)        │   │
│  └──────────────────┘          │                                      │   │
│                                │  • Carga config.yml                  │   │
│                                │  • Inicializa logging rotativo       │   │
│                                │  • Crea AWSMqttClient (mTLS)         │   │
│                                │  • Crea sesión ADK compartida        │   │
│                                │  • Inyecta MQTT en iot_tools         │   │
│                                │  • Se suscribe a topics              │   │
│                                │  • while True: time.sleep(1)         │   │
│                                └──────────────┬───────────────────────┘   │
│                                               │                           │
│                       ┌───────────────────────┼───────────────────────┐  │
│                       │                       │                       │  │
│                       ▼                       ▼                       ▼  │
│           ┌──────────────────┐   ┌──────────────────┐   ┌─────────────────┐│
│           │   HILO CALLBACK  │   │  HILO DISPATCHER │   │  HILO DISPATCHER││
│           │   MQTT (SDK)     │   │    TRIAGE        │   │    FEEDBACK     ││
│           │                  │   │                  │   │                 ││
│           │ process_event()  │──▶│ _batch_dispatcher│   │_batch_dispatcher││
│           │  - encola en     │   │                  │   │                 ││
│           │    BatchQueue    │   │ cada 1s revisa:  │   │ cada 1s revisa: ││
│           │                  │   │  • size≥10?      │   │  • size≥10?     ││
│           │                  │   │  • t≥15s?        │   │  • t≥15s?       ││
│           │                  │   │ → flush →        │   │ → flush →       ││
│           │                  │   │   runner_triage  │   │   runner_feedback││
│           └──────────────────┘   └──────────┬───────┘   └────────┬────────┘│
│                                             │                    │         │
│                                             ▼                    ▼         │
│                                    ┌────────────────┐  ┌────────────────┐  │
│                                    │  ADK Runner    │  │  ADK Runner    │  │
│                                    │  + LLM (Triage)│  │  + LLM (Feed.) │  │
│                                    └───────┬────────┘  └───────┬────────┘  │
│                                            │                   │           │
│                                            ▼                   ▼           │
│                                    ┌────────────────────────────────┐      │
│                                    │    TOOLS (funciones Python)    │      │
│                                    │  • register_alert              │      │
│                                    │  • block_ip                    │      │
│                                    │  • execute_remote_command      │      │
│                                    │  • update_alert_status         │      │
│                                    └──────────┬─────────────────────┘      │
│                                               │                            │
│                   ┌───────────────────────────┼────────────────────────┐  │
│                   ▼                           ▼                        ▼  │
│          ┌────────────────┐        ┌────────────────────┐   ┌────────────┐│
│          │  SQLite (WAL)  │        │  AWS MQTT Publish  │   │   Logging  ││
│          │  soc_data.db   │        │  (comandos/{dev})  │   │  rotativo  ││
│          └────────┬───────┘        └────────────────────┘   └────────────┘│
│                   │                                                       │
│                   │   (lecturas read-only)                                │
│                   ▼                                                       │
│          ┌────────────────────────────────────────────┐                  │
│          │       HILO FLASK (dashboard_soc.py)        │                  │
│          │                                            │                  │
│          │  • Rutas: /  /api/data  /revert/<id>       │                  │
│          │  • Auth: HTTP Basic                        │                  │
│          │  • AJAX polling cada 500 ms                │                  │
│          │  • Puerto 5000 expuesto al host            │                  │
│          └────────────────────────────────────────────┘                  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────┐
│  CONTENEDOR DOCKER: local-ai-engine  │
│  ollama/ollama:latest                │
│  puerto 11434 (API)                  │
│  volumen ollama_data_volume          │
└──────────────────────────────────────┘
```

### 5.2 Flujo end-to-end de un ataque real

Vamos a trazar paso a paso qué pasa cuando un atacante lanza una **inyección SQL** contra la web de PI-4:

```
[T+0.0s]  Atacante (IP 203.0.113.45) envía desde su navegador:
          POST https://auditorsentinelti.com/login.php
          email=admin@cybergard.com' UNION SELECT 1,'Admin',
          '202cb962ac59075b964b07152d234b70','admin' -- -

[T+0.1s]  PI-4 → Apache → loggers.php detecta patrón sospechoso
          en el parámetro 'email' (presencia de "UNION SELECT")

[T+0.2s]  PI-4 → agente_monitor.py publica en AWS IoT:
          Topic: seguridad/clientel/eventos
          Payload: {
            "sensor": "Pi4-Felix",
            "timestamp": "2026-04-15T17:42:41Z",
            "evento": "SQL_INJECTION",
            "ip": "203.0.113.45",
            "user": "admin@cybergard.com' UNION SELECT 1,'Admin'...",
            "prioridad": "ALTA"
          }

[T+0.3s]  AWS IoT Core recibe → reenvía a todos los suscriptores
          del filtro "seguridad/#"

[T+0.4s]  PI-5 → process_event() callback se dispara en un hilo del SDK
          → decide queue_type="triage" (no es feedback)
          → añade {device:"Pi4-Felix", raw_log:"{...JSON...}"} a _triage_queue
          → queue_size=1, no alcanza max_size(10) ni time_trigger(15s) aún

[T+0.5s .. T+15.4s]  Esperan otros eventos o al disparo por tiempo

[T+15.4s] Hilo _batch_dispatcher TRIAGE detecta:
            time_trigger=True (han pasado 15s desde último flush)
          → queue.flush() extrae todos los mensajes acumulados
          → _process_batch(batch, runner_triage, "triage")

[T+15.5s] _format_batch_message construye el mensaje para el LLM:
          "Batch de 3 eventos (Log) interceptados. Analiza CADA uno...
          [1] Dispositivo: Pi4-Felix | Data: {evento:SQL_INJECTION...}
          [2] Dispositivo: Pi4-Felix | Data: {evento:LOGIN_EXITOSO...}
          [3] Dispositivo: Pi4-Felix | Data: {tipo:RESUMEN_...}"

[T+15.6s] runner.run() invoca al LLM (Gemini o Ollama)
          El LLM razona:
            - Evento 1: SQL_INJECTION con prioridad ALTA → ataque confirmado
            - Evento 2: LOGIN_EXITOSO con IP ".134" (admin legítimo) → benigno
            - Evento 3: RESUMEN → no hacer nada

[T+17.2s] El LLM emite su primera tool call:
            register_alert(
              device="Pi4-Felix",
              attack_vector="MYSQL",
              source_ip="203.0.113.45",
              severity="Alta",
              verdict="SQL Injection en login.php mediante UNION SELECT",
              raw_log="{...JSON original...}"
            )

[T+17.3s] db_tools.py ejecuta INSERT en soc_data.db
          → devuelve {"status":"success", "message":"...NO LLAMAR de nuevo..."}

[T+17.4s] El LLM recibe el resultado y emite segunda tool call:
            block_ip(
              device="Pi4-Felix",
              ip="203.0.113.45",
              reason="SQL Injection attempt"
            )

[T+17.5s] iot_tools.py:
          → publica en comandos/Pi4-Felix :
            {"accion":"bloquear_ip","ip":"203.0.113.45","motivo":"..."}
          → actualiza DB: accion_tomada="Bloqueo Activo Emitido"

[T+17.6s] AWS IoT Core reenvía a PI-4 (suscrita a comandos/Pi4-Felix)

[T+17.7s] PI-4 recibe → ejecuta:
          sudo iptables -A INPUT -s 203.0.113.45 -j DROP

[T+17.9s] PI-4 publica feedback:
          Topic: comandos/Pi4-Felix/out
          Payload: {
            "sensor":"Pi4-Felix",
            "command":"sudo iptables...",
            "status":"success",
            "output":""
          }

[T+18.0s] PI-5 process_event() detecta "comandos" + "out" en el topic
          → encola en _feedback_queue

[T+33.0s] Hilo _batch_dispatcher FEEDBACK dispara por tiempo
          → runner_feedback.run()
          → LLM llama update_alert_status("Pi4-Felix", "", "EXITO")

[T+33.2s] DB actualiza estado_mitigacion="[EXITO] "

[T+33.5s] Dashboard (AJAX /api/data cada 500 ms) recibe los nuevos datos
          y refresca:
            - Total incidentes +1
            - Threat Level recalculado
            - Tabla muestra la fila con gravedad "Alta" y acción "Bloqueo..."
```

**Total**: 33 segundos desde que el atacante pulsa "Enviar" hasta que ve su IP bloqueada y el incidente aparece en el dashboard.

<!-- IMAGEN: Captura del log del contenedor (docker compose logs -f soc-coordinator-pi5) mostrando este flujo en tiempo real durante una demo. -->

### 5.3 Modelo de concurrencia

La PI-5 ejecuta **cuatro tipos de hilos** simultáneamente:

| Hilo | Origen | Función | ¿Daemon? |
|------|--------|---------|----------|
| Principal | `main_coordinator.py` | Config, conexión MQTT, loop `while True` | No |
| Callback MQTT | awscrt (pool interno del SDK) | `process_event()` para cada mensaje entrante | Sí |
| Dispatcher Triage | `threading.Thread` | Vacía la cola Triage cada 1s | Sí (daemon=True) |
| Dispatcher Feedback | `threading.Thread` | Vacía la cola Feedback cada 1s | Sí (daemon=True) |
| Flask | `dashboard_soc.py` en proceso separado | Servidor web en el puerto 5000 | No |

Todos los hilos se lanzan al inicio en [main_coordinator.py:254-257](PI-5/src/main_coordinator.py#L254-L257):

```python
triage_thread = threading.Thread(
    target=_batch_dispatcher,
    args=(_triage_queue, _runner_triage, "triage"),
    daemon=True
)
feedback_thread = threading.Thread(
    target=_batch_dispatcher,
    args=(_feedback_queue, _runner_feedback, "feedback"),
    daemon=True
)
triage_thread.start()
feedback_thread.start()
```

**¿Por qué threading y no asyncio?**

1. El SDK de AWS IoT (`awscrt`) usa su propio event loop C++ interno y expone callbacks síncronos. Asyncio no encaja naturalmente.
2. Las operaciones bloqueantes (llamadas al LLM, SQLite) conviven mejor con threads.
3. Para el volumen de mensajes esperado (docenas por minuto, no miles por segundo) threading es más que suficiente.

### 5.4 El patrón `LogBatchQueue` — dual trigger

Uno de los componentes más importantes. Su razón de ser:

**El problema**: si cada log dispara inmediatamente una llamada al LLM, bajo un ataque DDoS el agente se satura (y el coste de API, si usamos Gemini, se dispara).

**La solución**: encolar los logs entrantes y procesarlos en lotes ("batches"). Pero un batch clásico solo flushea cuando se llena, lo que introduce latencia si los ataques son lentos. Por eso implementamos **doble disparador**:

```
┌─────────────────────────────────────┐
│        LogBatchQueue                │
│                                     │
│  ┌────────────────────────────┐     │
│  │  [msg1] [msg2] [msg3] ...  │     │
│  └────────────────────────────┘     │
│                                     │
│  Flush si ALGUNO se cumple:         │
│    ▪ size() >= 10                   │
│    ▪ seconds_since_flush() >= 15    │
└─────────────────────────────────────┘
```

Código en [main_coordinator.py:84-123](PI-5/src/main_coordinator.py#L84-L123):

```python
class LogBatchQueue:
    def __init__(self, max_size: int, flush_interval: int):
        self._queue: list[dict] = []
        self._lock = threading.Lock()      # Thread-safety
        self._max_size = max_size          # 10 (config.yml)
        self._flush_interval = flush_interval  # 15 (config.yml)
        self._last_flush = time.time()

    def add(self, device, raw_log):
        with self._lock:
            self._queue.append({"device": device, "raw_log": raw_log})
            return len(self._queue) >= self._max_size   # True = flushear ya

    def flush(self):
        with self._lock:
            batch = list(self._queue)
            self._queue.clear()
            self._last_flush = time.time()
            return batch
```

Beneficios del patrón:

- **Bajo tráfico**: el hilo dispatcher flushea cada 15 s, aunque solo haya un log.
- **Alto tráfico**: antes de llegar a los 15 s la cola llega a 10 y se dispara inmediatamente.
- **Sin desperdicio**: el LLM ve múltiples eventos en un mismo prompt, puede correlacionarlos ("estas 7 peticiones desde la misma IP son un escaneo").
- **Thread-safe** gracias a `threading.Lock`.

### 5.5 Persistencia en SQLite

#### Schema

Definido en [src/database.py](PI-5/src/database.py):

```sql
CREATE TABLE IF NOT EXISTS logs (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    dispositivo       TEXT,           -- "Pi4-Felix"
    servicio          TEXT,           -- "SSH", "MYSQL", "NGINX-HTTP"
    log_original      TEXT,           -- JSON crudo o texto del log
    ip_origen         TEXT,           -- "203.0.113.45"
    nivel_gravedad    TEXT,           -- "Baja", "Media", "Alta", "Crítica"
    veredicto_ia      TEXT,           -- Razonamiento del LLM
    accion_tomada     TEXT,           -- "Bloqueo Activo Emitido" | "Solo Registro"
    estado_mitigacion TEXT,           -- "[EXITO] ..." o "[FALLO] ..."
    timestamp         DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

El campo `estado_mitigacion` se añade después (migración idempotente con `ALTER TABLE`), lo que permite actualizar PI-5 sin perder datos.

#### WAL mode

Todas las conexiones ejecutan al abrir:

```sql
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
```

**WAL (Write-Ahead Logging)** permite:

- Múltiples **lectores simultáneos** con un escritor activo (el dashboard puede leer mientras el agente escribe).
- Mayor throughput que el modo rollback clásico.
- Durabilidad garantizada a coste de un archivo auxiliar `.db-wal` que crece entre *checkpoints*.

#### Política de retención

En cada `register_alert()`, si `retention.purge_on_insert=true` (config.yml), se llama a `rotate_old_logs()`:

```python
DELETE FROM logs
WHERE accion_tomada = 'Solo Registro'
  AND timestamp <= datetime('now', '-30 days')
```

Solo se borran registros **"Solo Registro"** (eventos sin bloqueo asociado). Los bloqueos activos se conservan indefinidamente para trazabilidad.

#### Política de reintentos

En caso de bloqueo transitorio (SQLite "database is locked"), se reintenta hasta 5 veces con 2 s de espera:

```python
for attempt in range(5):
    try:
        # ... INSERT ...
    except sqlite3.OperationalError as e:
        if "locked" in str(e).lower():
            time.sleep(2)
        else:
            return {"status": "error", "message": str(e)}
```

<!-- IMAGEN: Captura de DB Browser for SQLite abriendo soc_data.db y mostrando varias filas reales con distintos niveles de gravedad. -->

### 5.6 Dashboard Flask

Ubicación: [src/dashboard_soc.py](PI-5/src/dashboard_soc.py). Puerto 5000, expuesto al host.

#### Rutas

| Ruta | Método | Auth | Propósito |
|------|--------|------|-----------|
| `/` | GET | HTTP Basic | Renderiza `index.html` con KPIs y tabla. |
| `/api/data` | GET | HTTP Basic | Devuelve JSON con todos los datos. Consumido por AJAX cada 500 ms. |
| `/revert/<log_id>` | POST | HTTP Basic | Envía el comando inverso `iptables -D` para desbloquear una IP. |

#### Autenticación

HTTP Basic Auth con contraseña hasheada con Werkzeug. Dos modos de configuración:

```bash
# Modo 1: guardar directamente el hash (preferido)
DASHBOARD_USER=admin
DASHBOARD_PASSWORD_HASH=pbkdf2:sha256:600000$...

# Modo 2: contraseña en plano (se hashea al arrancar)
DASHBOARD_USER=admin
DASHBOARD_PASSWORD=mipassword
```

Si no hay ninguna, se imprime un WARNING y se permite acceso libre (útil solo en desarrollo).

#### Cálculo del Threat Level

Heurística ponderada en [dashboard_soc.py:182-213](PI-5/src/dashboard_soc.py#L182-L213):

```
threat_level = min(
    ((criticals * 3) + (highs * 2) + mediums) / total * 25,
    100
)
```

Interpretación:

| Rango | Color UI | Significado |
|-------|----------|-------------|
| 0-25 | Verde | Sin amenazas notables. |
| 26-60 | Amarillo | Actividad sospechosa, vigilancia. |
| 61-100 | Rojo | Incidentes graves, intervención humana. |

#### Función `/revert/<id>`

Dada una fila de la BD con `accion_tomada='Bloqueo Activo Emitido'`, revierte el bloqueo:

```python
revert_command = f"sudo iptables -D INPUT -s {blocked_ip} -j DROP"
topic = f"{TOPIC_ACTIONS_BASE}{device}"
mqtt_client.publish(topic, {
    "accion": "ejecutar_comando",
    "comando": revert_command,
    "motivo": f"Manual revert from dashboard for IP {blocked_ip}"
})
# Marca la fila: accion_tomada += " [REVERTIDO]"
```

Importante: **el dashboard es un cliente MQTT independiente** (`ClientId="Dashboard-SOC-Pi5"`) porque corre en un subproceso distinto al coordinador. Por eso la Policy incluye ese tercer cliente.

<!-- IMAGEN: Captura de la UI del dashboard funcionando, idealmente con varios incidentes reales y el gauge del Threat Level en amarillo o rojo. -->

### 5.7 Docker Compose

Archivo [docker-compose.yml](PI-5/docker-compose.yml). Dos servicios:

#### Servicio 1: `soc-coordinator-pi5`

```yaml
soc-coordinator-pi5:
  build: { context: ., dockerfile: Dockerfile }
  container_name: soc-coordinator-pi5
  restart: unless-stopped
  ports:
    - "5000:5000"                              # Dashboard web
  volumes:
    - soc_data_volume:/app/data                # BD SQLite persistente
    - ./coordinator_soc.log:/app/coordinator_soc.log
    - ./dashboard_soc.log:/app/dashboard_soc.log
    - ./certificados:/app/certificados:ro      # Certs mTLS read-only
    - ./.env:/app/.env:ro                      # Secretos read-only
  environment:
    - TZ=Europe/Madrid
    - GEMINI_API_KEY=${GEMINI_API_KEY}
```

El Dockerfile (Python 3.13-slim) instala `requirements.txt` y ejecuta `scripts/start_services.sh`, que lanza Flask en background + el coordinador en primer plano.

**Volúmenes explicados**:

| Volumen | Tipo | Por qué |
|---------|------|---------|
| `soc_data_volume:/app/data` | Named volume | Persiste la BD a través de reinicios del contenedor. |
| `./coordinator_soc.log:/app/...` | Bind mount | Logs accesibles desde el host para troubleshooting. |
| `./certificados:/app/certificados:ro` | Read-only | Certificados X.509 de mTLS, no modificables desde dentro. |
| `./.env:/app/.env:ro` | Read-only | Secretos inyectados sin que queden en el árbol Git. |

#### Servicio 2: `local-ai-engine` (Ollama)

```yaml
local-ai-engine:
  image: ollama/ollama:latest
  container_name: local-ai-engine
  restart: unless-stopped
  ports:
    - "11434:11434"
  volumes:
    - ollama_data_volume:/root/.ollama
```

Contenedor oficial de Ollama. El volumen `ollama_data_volume` guarda el modelo descargado (gemma3:4b ~ 2.5 GB). El contenedor expone el puerto 11434, que es donde el coordinador apunta `OLLAMA_API_BASE`.

**Descarga inicial del modelo** (una vez):

```bash
docker exec local-ai-engine ollama pull gemma3:4b
```

El script `scripts/pull_local_model.sh` automatiza este paso.

<!-- IMAGEN: Captura de `docker ps` mostrando los 2 contenedores UP con el tiempo de ejecución y los puertos. -->

### 5.8 Logging estructurado

Toda la PI-5 usa `logging` estándar de Python con handler rotativo:

```python
handler = RotatingFileHandler(
    LOG_FILE_PATH,           # /tmp/coordinator_soc.log
    maxBytes=5242880,        # 5 MB por archivo
    backupCount=3            # Mantiene 3 archivos antiguos
)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
```

Resultado: cuando `coordinator_soc.log` llega a 5 MB, se rota a `coordinator_soc.log.1`, y así sucesivamente. Se conservan 5+5+5+5 = 20 MB de histórico máximo, lo que es suficiente para auditoría sin inundar el disco.

Niveles de log usados:

| Nivel | Uso |
|-------|-----|
| `INFO` | Flujo normal: conexión, mensajes recibidos, triggers, tools ejecutadas. |
| `WARNING` | Cosas que no fallan pero avisan: BD ocupada, MQTT desconectado temporalmente, contraseña no definida. |
| `ERROR` | Errores capturados pero no fatales: fallo de una tool, fallo de parseo de un mensaje. |
| `CRITICAL` | Muy rara. Solo para fallos irrecuperables del coordinador. |

### 5.9 Seguridad operacional

Decisiones de seguridad tomadas en el diseño:

| Riesgo | Mitigación | Implementación |
|--------|-----------|-----------------|
| Secretos en Git | Carpeta `certificados/` y `.env` en `.gitignore` | Comprobado; solo se commitea `Policy.json` y `docker-compose.yml`. |
| Dashboard sin autenticar | HTTP Basic Auth obligatorio | Verificación en cada ruta con `@auth.login_required`. |
| Certificados modificables desde el contenedor | Montados `:ro` (read-only) | Línea `./certificados:/app/certificados:ro` en docker-compose. |
| LLM alucinando tools inexistentes | Reglas explícitas en el prompt | Bloque "Critical Execution Rules" del Triage. |
| LLM en bucle infinito de tool calls | Reglas "STOP after X" + ADK Runner tiene límite de iteraciones | Reforzado en prompt + default de ADK. |
| Acceso amplio en AWS | Política IAM con 3 ClientIds y 2 árboles de topics | [Policy.json](PI-5/Policy.json). |
| Base de datos corrompida por concurrencia | WAL mode + retry loop | PRAGMA en cada conexión. |
| Pérdida de mensajes por desconexión momentánea | `clean_session=False` + QoS 1 | Parámetros en `aws_connector.py`. |
| Log infinito | `RotatingFileHandler` con `backupCount` | Máximo 20 MB en disco. |

---

## 6. Diagrama de síntesis del sistema

Visión integrada de los dos nodos y la nube:

```
  ╔═════════════════════════════════════════════════════════════════════════╗
  ║                            AWS IoT Core                                 ║
  ║                  (Broker MQTT + mTLS + IAM Policies)                    ║
  ║                                                                         ║
  ║     Topics:   seguridad/clientel/{telemetria|eventos}                   ║
  ║               comandos/{device}                                         ║
  ║               comandos/{device}/out                                     ║
  ╚════════════╤════════════════════════════════════════╤═══════════════════╝
               │                                        │
               │  eventos/telemetría                    │  acciones
               │  (QoS 1, mTLS)                         │  (QoS 1, mTLS)
               │                                        │
               ▲                                        ▼
  ┌────────────┴────────────┐                  ┌────────┴──────────────────┐
  │        PI-4             │                  │         PI-5              │
  │   (Nodo Protegido)      │                  │      (Coordinador)        │
  │                         │                  │                           │
  │  Servicios expuestos:   │                  │  ┌─────────────────────┐  │
  │  • Apache + Nginx       │                  │  │ Docker Compose      │  │
  │    (puerto 80 proxy     │                  │  │                     │  │
  │     → 8080 backend)     │                  │  │  Contenedor A:      │  │
  │  • vsftpd (FTP)         │                  │  │   soc-coordinator   │  │
  │  • SSH                  │                  │  │   (Python 3.13)     │  │
  │  • MariaDB              │                  │  │   ├─ Coordinator    │  │
  │  • dnsmasq (DNS)        │                  │  │   ├─ Dashboard 5000 │  │
  │                         │                  │  │   ├─ SQLite WAL     │  │
  │  Web honeypot:          │                  │  │   └─ ADK Agents     │  │
  │  • SentinelIT/CyberGard │                  │  │                     │  │
  │    (PHP + MariaDB)      │                  │  │  Contenedor B:      │  │
  │  • Vulnerabilidades:    │                  │  │   local-ai-engine   │  │
  │    SQLi, XSS, session   │                  │  │   (Ollama)          │  │
  │    hijacking            │                  │  │   puerto 11434      │  │
  │                         │                  │  └─────────────────────┘  │
  │  Agente monitor         │                  │                           │
  │  (agente_monitor.py):   │                  │  Base de datos:           │
  │  • vigila syslog, apache│                  │  • soc_data.db (SQLite)   │
  │  • detecta patrones     │                  │                           │
  │  • publica eventos      │                  │  IA:                      │
  │  • ejecuta los comandos │                  │  • AI_MODE=local (Ollama) │
  │    recibidos            │                  │    → gemma3:4b            │
  │                         │                  │  • AI_MODE=api (Gemini)   │
  │  Identidad en AWS IoT:  │                  │    → gemini-2.5-flash     │
  │  ClientId: Pi4-Felix    │                  │                           │
  │  mTLS cert: Pi4-Felix.* │                  │  Identidad en AWS IoT:    │
  │                         │                  │  ClientId: Pi5-dani       │
  │                         │                  │  (+ Dashboard-SOC-Pi5)    │
  └─────────────────────────┘                  └───────────────────────────┘

  ◀──────────────── Físicamente en redes domésticas separadas ──────────────▶
      (casa de Félix)                                   (casa de Daniel)
```

---

## 7. Imágenes necesarias para integrar

Estas son las capturas reales que necesitamos añadir al documento para que quede completo y defendible visualmente. Te indico para cada una **qué debe aparecer** y **dónde ya le dejé el hueco** marcado con `<!-- IMAGEN: ... -->`:

| # | Dónde hacer la captura | Qué debe verse | Sección del documento |
|---|-----------------------|----------------|------------------------|
| 1 | AWS Console → IoT Core → **Manage → Things** | Lista con `Pi4-Felix` y `Pi5-dani` activos | 2.5 |
| 2 | AWS Console → IoT Core → **Security → Certificates** | Un certificado en estado `ACTIVE` con Thing y Policy asociados | 2.5 |
| 3 | AWS Console → IoT Core → **Test → MQTT test client** | Suscríbete a `seguridad/#`, haz que PI-4 publique, captura el mensaje recibido en formato JSON | 2.4 |
| 4 | Opcional — referencia externa | Diagrama QoS handshake de HiveMQ/Mosquitto | 1.5 (ya hay ASCII, puede omitirse) |
| 5 | Navegador en `http://<ip-pi5>:5000` | Dashboard con al menos 5-10 incidentes reales, el gauge del Threat Level coloreado, tabla con filas de distintos colores | 5.6 |
| 6 | Terminal en PI-5 tras `docker compose up -d` | Salida de `docker ps` con los 2 contenedores `soc-coordinator-pi5` y `local-ai-engine` con `Up` y los puertos mapeados | 5.7 |
| 7 | Terminal — `docker exec local-ai-engine ollama list` | Salida mostrando el modelo `gemma3:4b` descargado | 4.8 |
| 8 | Navegador en [Google AI Studio](https://aistudio.google.com/) | Sección de API Keys con al menos una key activa (**TAPAR la cadena real de la key**) | 4.8 |
| 9 | DB Browser for SQLite abriendo `PI-5/data/soc_data.db` | Tabla `logs` con al menos 5 filas reales, mostrando las columnas dispositivo, servicio, ip_origen, nivel_gravedad, accion_tomada, estado_mitigacion | 5.5 |
| 10 | Split screen: terminal con `docker compose logs -f soc-coordinator-pi5` + navegador con el dashboard + terminal ejecutando un ataque simulado (curl con SQLi a PI-4) | Se ve el flujo completo: ataque → log → decisión del agente → bloqueo → aparición en dashboard | 5.2 |

**Instrucciones para añadir cada imagen**:

1. Crea una carpeta `PI-5/docs/img/` si no existe.
2. Guarda cada captura con un nombre descriptivo (p.ej. `01-aws-things-list.png`).
3. En el punto del documento donde ves `<!-- IMAGEN: ... -->`, reemplaza ese comentario por:
   ```markdown
   ![Descripción corta](docs/img/01-aws-things-list.png)
   ```

### Conversión a Word/PDF al final

Cuando tengas todas las imágenes incrustadas y el documento te guste, puedes convertirlo a Word con una sola línea desde PowerShell:

```powershell
pandoc DOCUMENTACION_TECNICA_PI5.md -o DOCUMENTACION_TECNICA_PI5.docx --toc --number-sections
```

O a PDF profesional:

```powershell
pandoc DOCUMENTACION_TECNICA_PI5.md -o DOCUMENTACION_TECNICA_PI5.pdf --toc --number-sections --pdf-engine=xelatex
```

(Requiere instalar Pandoc — https://pandoc.org — y para PDF, además, MiKTeX o TeX Live.)

---

*Fin del documento técnico complementario.*
