# Arquitectura File-by-File: TFG Central SOC (Coordinador)

Este documento expone cómo se orquesta la magia técnica de la Red SOC central (Nodo coordinador), desglosando visualmente cada archivo, carpeta y su propósito lógico dentro del gran marco de ciberseguridad autónoma basado en IA (ADK).

---

## 🏗️ Árbol Estructural del Coordinador (Pi5-Dani)

```plaintext
pi5-dani/
├── main_coordinator.py        🚀 (Motor Neuronal - Entrada de Logs)
├── dashboard_soc.py           🖥️ (Portal Front-End)
├── aws_connector.py           ☁️ (Telemetría de Red y MQTT)
├── base_datos.py              🗄️ (SQL - Inicializador de Registros)
├── config.yml                 ⚙️ (Tuercas de Configuración Global)
│
├── setup.sh                   🛠️ (Instalador Mágico)
├── start_services.sh          ▶️ (Lanzador Manual de Procesos)
├── soc-coordinator.service    🔄 (Daemon de Background Systemd)
├── soc-dashboard.service      🔄 (Daemon de Background Systemd)
│
├── agents/                    🤖 (Mente IA)
│   └── soc_agent/
│       └── soc_agent.py       (Agente SOC Defensivo)
│
├── tools/                     🔧 (Brazos y Armas del Agente)
│   ├── db_tools.py            (Herramienta IAM IA: Guardar Datos)
│   └── iot_tools.py           (Herramienta IAM IA: Aplicar Bloqueos Activos)
│
├── requirements.txt           📦 (Factura de Materiales Librerías)
├── .env                       🔒 (Secretos de Gemini - No se sube al Repo)
└── Certificados AWS           🔑 (mTLS certificates `.pem`, `.crt`, `.key`)
```

---

## 🔎 Desglose de Archivos: ¿Para qué vale cada uno?

A continuación se explica la función crítica que ejerce cada archivo en el flujo de operaciones:

### Los Pilares Centrales (Raíz)

#### `main_coordinator.py`

* **Para qué vale**: Es el cerebro activo y el punto central de coordinación del nodo SOC.
* **Qué hace**: Establece conexión persistente con **AWS IoT Core** para escuchar ("supscribe") al canal MQTT (`seguridad/logs/+/+`). Cada vez que intercepta un log de cualquier cámara, servidor o dispositivo perimetral, se lo manda de inmediato en formato procesado por parámetros a la IA de Google ADK (`soc_agent`) para que esta última exprese su veredicto.

#### `dashboard_soc.py`

* **Para qué vale**: Es la interfaz gráfica amigable (Web Dashboard).
* **Qué hace**: Sirve una aplicación **Flask HTTP**, expuesta en el puerto estético 5000. Utiliza HTML/CSS dinámico para escudriñar la Base de Datos SQLite en tiempo real y volcar las métricas a pantalla. Permite al humano (analista) observar los bloqueos y entender el razonamiento de la IA frente a ataques.

#### `base_datos.py`

* **Para qué vale**: Instala la infraestructura de persistencia local (SQL).
* **Qué hace**: Ejecuta la creación del "disco duro local" (`soc_data.db`) donde residen todos los logs y tablas de métricas avanzadas creadas por seguridad, reseteándolo o creándolo desde cero según sea necesario. Define las columnas de SQLite (dispositivo, ip_origen, nivel_gravedad, veredicto_ia...).

#### `aws_connector.py`

* **Para qué vale**: El traductor Cloud entre Amazon y la Raspberry.
* **Qué hace**: Actúa como un *Wrapper* (una capa que simplifica) para usar las pesadas librerías `awsiotsdk`. Aplica y usa todos los certificados complejos de autenticación (los que terminan en `.pem` y `.key`) y enmascara operaciones como `connect()`, `publish()` o `subscribe()`.

#### `config.yml`

* **Para qué vale**: El panel de control unificado y evitación de variables *Hard-Coded*.
* **Qué hace**: Contiene todas las URL, nombres lógicos, topologías MQTT (`seguridad/acciones/`), la ruta de logs o el modelo de LLM usado en el Agente (ej: `gemini-3-flash`). Cambiando texto aquí, cambia todo el comportamiento del SOC.

---

### Músculo y Mantenimiento del SO (Scripts Bash)

#### `setup.sh`

* **Qué hace**: "Magia" en autodiagnóstico. Si la placa se quema y pones un nuevo ordenador, ejecutas esto. Él solo baja *Python*, baja *librerías Pip*, instala certificados, levanta los bases de SQLite y arranca dos *Daemons* Background invulnerables para que no tengas que dejar encendida una sesión Putty con la PI5.

#### `start_services.sh`

* **Qué hace**: Opuesto al setup, es para el "analista impaciente". Un script de un doble comando python sencillo que llama `dashboard_soc.py &` (background) y al coordinador en local para ver si un código ha fallado o la UI se rompió haciendo una prueba manual en terminal local.

#### Archivos `.service` (`soc-coordinator.service` / `soc-dashboard.service`)

* **Qué hace**: Son reglas para **Linux Systemd**. Obligan a la Raspberry Pi a pensar: "si la luz falla y me reinicio, según me encienda tengo que recuperar y re-lanzar los comandos Python para encender mi propio software antivirus autónomo de forma sigilosa sin que nadie conecte una pantalla".

---

### Inteligencia Humano-Artificial (Directorios)

#### La carpeta `agents/` -> `soc_agent.py`

* **Para qué vale**: Alberga la psique o la "Mente" Autónoma del Sistema.
* **Qué hace**: Haciendo uso de la reciente librería orientada a agentes `google.adk`, instancia una "personalidad estricta SOC". Su IA local lee las instrucciones *System Prompt*: "Eres un Agente SOC experto. Aquí están los logs. Si es una alerta, bloquea. Si es normal, rinde informe". Tiene potestad delegada de tomar sus propias decisiones sin intervención manual, actuando como filtro TIER 1.

#### La carpeta `tools/`

Son las **"Manos Digitales"** del Agente de IA. Un LLM sabe analizar texto, pero no interactuar con el mundo físico. Estas herramientas (*Tool Calling*) le brindan sus manos:

* **`db_tools.py`**: El Agente usa esta herramienta cuando detecta algo aburrido y dice "Mera alerta menor, usaré *registrar_alerta* para pasarlo a SQLite y el humano lo verá en el frontal Flask."
* **`iot_tools.py`**: El **Arma Defensiva Final**. Si el agente detecta "Burte Force Múltiple o Ataque SQL injection", la IA invoca automáticamente `bloquear_ip(ip, motivo)`. Esto dispara código Python que se comuníca con **MQTT AWS** hacia la Placa Perimetral original, exigiéndole aplicar reglas Iptables que tumban y banean a la MAC o IP Atacante en milisegundos.

---

### Dependencias y Extras

#### `requirements.txt`

* Simplemente lista la hoja de la compra de PIP (El gestor de Python). Qué versiones exactas de `Flask`, `pymqtt` ó `google-generativeai` rigen el programa.

#### `.env` / `Certificados AWS`

* Pese a que son invibles, son las Llaves maestras.
* `.env` salva la ApiKeny del Motor LLM.
* Certificados encriptan todo el tráfico (Seguridad mTLS, Mutua autenticación), validando ante Amazon que esa Raspberry es auténitca y nadie le miente sobre Logs inventados en medio del tráfico.
