# Referencia Técnica de Arquitectura: Sentinel-IT

Este documento sirve como la referencia técnica oficial para el proyecto Sentinel-IT, delineando los componentes internos, la arquitectura de la infraestructura y los mecanismos de comunicación del sistema SOC Autónomo.

Su objetivo es proveer información estructurada y precisa para que tanto evaluadores (Tribunal del TFG) como agentes automatizados (IA) comprendan la topología completa sin requerir un recorrido de instalación paso a paso.

---

## 1. Visión General de la Arquitectura (Topología)

El sistema Sentinel-IT sigue un modelo distribuido Edge-Cloud-Core con responsabilidades estrictamente separadas:

*   **Nodo Sensor (Edge - Raspberry Pi 4):** Actúa como el punto de recolección en tiempo real. Monitoriza aplicaciones web vulnerables, captura intrusiones locales y ejecuta comandos defensivos dictaminados por el coordinador.
*   **Nodo Coordinador (Core - Raspberry Pi 5):** Es el "cerebro" del SOC. Centraliza la información, ejecuta la lógica del Inteligencia Artificial (LLM) y gestiona la persistencia y la interfaz visual.
*   **Capa de Tránsito (AWS IoT Core):** Intermediario seguro en la nube que conecta ambos nodos mediante colas de mensajería (Pub/Sub).

**Flujo de Vida del Dato:**
1. Intrusión detectada en Nodo Sensor.
2. Formateo y publicación a AWS IoT Core vía MQTT.
3. El Coordinador consume el log e invoca al Triage Agent (IA).
4. El Agente decide la mitigación y publica un comando de vuelta.
5. El Sensor ejecuta la defensa (ej. dropear IP) y reporta el éxito.
6. El Feedback Agent (IA) procesa el reporte y el Dashboard visualiza el evento cerrado.

---

## 2. Capa de Comunicaciones y Seguridad (AWS IoT Core)

Las comunicaciones son bidireccionales, asíncronas y están aseguradas de extremo a extremo.

### Protocolo MQTT y Árbol de Topics
El sistema utiliza tópicos específicos para enrutar el tráfico:
*   `seguridad/logs`: Empleado por los Sensores para enviar telemetría en formato JSON hacia el Coordinador.
*   `seguridad/acciones`: Empleado por el Coordinador para inyectar comandos de mitigación hacia los Sensores.
*   `seguridad/estado`: Empleado por los Sensores para confirmar el resultado de la mitigación.

### Autenticación mTLS (Mutual TLS)
Para prevenir interceptaciones y *spoofing* de dispositivos, se exige autenticación mutua:
*   Cada dispositivo requiere una identidad generada en AWS (`root-CA.crt`, `<device>.cert.pem`, `<device>.private.key`).
*   Los certificados se montan en tiempo de ejecución en entornos Docker aislando las claves privadas de la base del código.

### Políticas IAM (`Policy.json`)
El documento de políticas JSON define los privilegios mínimos (Principle of Least Privilege). Impide que un nodo comprometido acceda a canales no autorizados.
*   **Sensores:** Permiso exclusivo para publicar en `seguridad/logs` y `seguridad/estado`, y suscribirse a `seguridad/acciones`.
*   **Coordinador:** Acceso completo a suscripciones y publicaciones del prefijo `seguridad/#`.

---

## 3. Referencia del Nodo Coordinador (Raspberry Pi 5)

Este nodo central alberga los servicios de inteligencia y control.

### Motor de IA (Google Gemini ADK)
Basado en el Agent Development Kit (ADK) de Google y alimentado por Gemini (vía API). Implementa un patrón **Dual-Agent**:
1.  **Triage Agent:** Analiza los payloads de `seguridad/logs`. Utiliza *Tool Calling* explícito para invocar funciones como `register_alert(ip, gravedad, tipo)` o `block_ip(ip)`. Tiene instrucciones restrictivas para evitar "alucinaciones" (ej. inventar direcciones IP).
2.  **Feedback Agent:** Revisa las confirmaciones de mitigación que regresan del nodo sensor y actualiza el estado (ej. de `PENDING` a `MITIGATED`).

### Mecanismo de Micro-batching (Gestión de Colas)
Para prevenir el agotamiento de cuotas (Rate-limiting) de la API de Google, el sistema acumula ráfagas de logs en una cola (Queue) interna. Un *worker thread* consume y procesa los logs periódicamente o cuando se alcanza el tamaño máximo de bloque, optimizando el consumo del modelo.

### Base de Datos (SQLite WAL)
El estado de la red y las alertas se almacena en `soc_alerts.db`.
*   **Estructura Relacional:** Tablas que asocian identificadores de incidentes con direcciones IP infractoras, gravedad y estado de mitigación.
*   **Write-Ahead Logging (WAL):** Se activa el modo WAL (`PRAGMA journal_mode=WAL`) para permitir lecturas y escrituras concurrentes. Es crítico, ya que el *Thread* MQTT y el Dashboard Flask acceden a la base simultáneamente.

### Dashboard Web (Flask)
Interfaz en tiempo real para operadores de SOC.
*   **Servidor Asíncrono:** Rutas API ligeras (`/api/data`) que retornan JSON.
*   **Diseño (Glassmorphism):** Front-end responsivo con efectos translúcidos orientados a proveer un entorno visual premium sin recargar recursos de la Raspberry Pi.

---

## 4. Referencia del Nodo Sensor (Raspberry Pi 4 / Edge)

Un cliente IoT ligero desplegado en las fronteras de red.

### Monitorización de Telemetría (`agente_monitor.py`)
Encargado de vigilar archivos de acceso (ej. logs de Apache/Nginx o logs simulados) e inyectar *parsers* dinámicos que agrupan los metadatos en un payload JSON unificado antes de su publicación. Garantiza una ingesta estándar de datos que el LLM puede digerir de forma determinista.

### Ejecutor de Comandos Flexibles (`ejecutor_comandos.py`)
Módulo seguro y asilado que intercepta las respuestas en `seguridad/acciones`. 
Al validar que el comando proviene de una autoridad legítima (Coordinador), invoca procesos de sistema operativo subyacente (ej. inserciones de reglas `iptables`, binarios personalizados) y captura la salida estándar (`STDOUT`/`STDERR`) para confirmar el resultado al coordinador.

---

## 5. Mapa de Configuración y Despliegue

La portabilidad del sistema recae en sus archivos de manifiesto.

### Configuración YAML (`config.yml`)
Archivo centralizado que desacopla el código del entorno:
*   Mapea los endpoints REST/MQTT de AWS.
*   Define las rutas de los certificados (esperados en `./certificados/`).
*   Configura parámetros de latencia, logging y timeouts.

### Contenerización (`Dockerfile` y `docker-compose.yml`)
El coordinador está plenamente virtualizado.
*   **`Dockerfile`:** Define una base liviana de Python, instala librerías pesadas como el SDK de AWS IoT y el ADK de Google.
*   **`docker-compose.yml`:** Inyecta en el contenedor los volúmenes externos en modo solo lectura (`ro`), como la carpeta `certificados/` y archivos env ocultos (`.env`). Garantiza que si el contenedor falla o es reconstruido, el estado y las identidades persisten.

### Scripts de Gestión
*   `soc_manager.sh`: Utilidad CLI para encapsular los comandos en la Pi 5. Permite levantar, monitorear y purgar los contenedores sin memorizar sintaxis compleja.
*   `setup.sh`: Script en los nodos sensores para instalar dependencias APT/Pip y configurar los servicios Systemd del demonio monitor.

---

## 6. Módulo de Testing y Simulaciones (`tests/`)

Se incorporan pruebas unitarias y de integración directa dentro del repositorio (y dentro del contenedor del coordinador).

*   **`test_flexible_command.py`:** Asegura que el Coordinador emite correctamente el JSON con la estructura esperada de comandos al invocar el Action Manager.
*   **`test_feedback_loop.py`:** Ejecuta un pipeline completo "Mockeando" (simulando) la nube de AWS para asegurar que el pipeline local entre la IA de Triage, la base de datos y la IA de Feedback funciona sin colisiones. Permite comprobar regresiones antes del paso a producción.
