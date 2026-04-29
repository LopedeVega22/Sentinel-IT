# 02 - Arquitectura Detallada y Diagrama de Tópicos MQTT

Este documento detalla cómo se van a comunicar internamente la Raspberry Pi 4 (Nodo Protegido) y la Raspberry Pi 5 (Nodo Coordinador) utilizando AWS IoT Core como intermediario.

## 1. Patrón de Comunicación (Publish / Subscribe)

La base del proyecto es el uso de **MQTT sobre TLS (MQTTS)**.

* **Casa 1 (Pi 4):** Solo necesita permisos para **Publicar (Publish)** eventos de logs y **Suscribirse (Subscribe)** al canal de acciones de respuesta.
* **AWS IoT Core:** Actúa como *Broker*. Recibe los mensajes, y mediante su *Rules Engine* los encamina si es necesario, o simplemente los deja accesibles para los suscriptores.
* **Casa 2 (Pi 5):** Necesita permisos para **Suscribirse** a todos los eventos que lleguen de la Pi 4 y **Publicar** las acciones resultantes del análisis de la IA hacia la Pi 4.

## 2. Estructura de Tópicos MQTT (Topics)

Para mantener el sistema organizado (pensando en que en el futuro podría haber múltiples Pi 4 "protegidas"), definiremos unos tópicos jerárquicos:

### 2.1 Envío de Logs (Pi 4 -> AWS -> Pi 5)

* **Tópico:** `seguridad/logs/Pi4-Felix/ssh`
  * Carga útil (Payload JSON): `{"timestamp": "2026-06-01T10:00:00Z", "raw_log": "Failed password for root from 192.168.1.100 port 22 ssh2", "service": "ssh"}`

* **Tópico:** `seguridad/logs/Pi4-Felix/nginx`
  * Carga útil: `{"timestamp": "2026-06-01T10:00:05Z", "raw_log": "192.168.1.100 - - [01/Jun/2026:10:00:05 +0000] \"GET /.env HTTP/1.1\" 404", "service": "nginx"}`

### 2.2 Envío de Acciones de Bloqueo (Pi 5 -> AWS -> Pi 4)

* **Tópico:** `seguridad/acciones/Pi4-Felix`
  * Carga útil: `{"accion": "bloquear_ip", "ip": "192.168.1.100", "motivo": "Múltiples fallos SSH detectados por IA"}`

## 3. Componentes del Software (El Stack en Acción)

### Pi 4 (Nodo Protegido): El "Recolector"

* Un script en **Python** que usa `pyinotify` o `watchdog` para vigilar cambios en los archivos `/var/log/auth.log` (SSH) y `/var/log/nginx/access.log`.

* Cuando hay una línea nueva, usa `AWSIoTPythonSDK` para enviarla al tópico MQTT adecuado.
* Otro hilo del script está suscrito a `seguridad/acciones/Pi4-Felix`. Si recibe un JSON de bloqueo, ejecuta internamente un comando de bash (ej. `sudo iptables -A INPUT -s IP_MALA -j DROP`).

### Pi 5 (Nodo Coordinador): El "Cerebro"

* Un script de Python suscrito a `security/logs/+/+` (recibe de todas las Pi 4 y de todos los servicios).

* Por cada evento, el script despierta al **Agente IA (Gemini 1.5)** pasándole el log como contexto.
* Bajo el paradigma de *Agentic AI*, la IA razona y decide de forma autónoma qué herramienta (función de Python) ejecutar.
* Si detecta amenaza, guarda el incidente en la base de datos **SQLite** usando la tool de registro.
* Si el ataque es crítico (fuerza bruta, SQLi), usa la tool de bloqueo, la cual emite la orden de baneo mediante MQTT al tópico `seguridad/acciones/Pi4-Felix`.
* Se ejecuta en paralelo una instancia de **Flask** que lee de la SQLite y sirve un dashboard web interactivo para monitorizar KPIs.
* Ambos Nodos cuentan con sistemas de Logging profesionales a disco (`.log`) para posibilitar auditorías posteriores.
