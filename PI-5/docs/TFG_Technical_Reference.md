# Guía de Referencia Técnica y Teórica: SOC Autónomo (Sentinel-IT)

Esta guía documenta exhaustivamente la arquitectura, mecanismos de defensa, flujo de datos y decisiones de diseño del sistema SOC (Security Operations Center) implementado. Ha sido diseñada para servir de columna vertebral en la redacción de la memoria del TFG. Integra descripciones teóricas estructuradas manteniendo todo tu código y esquemas originales, acompañados de mayor profundidad conceptual.

---

## 1. Contexto Global y Arquitectura General del Sistema

**Sentinel-IT** es un sistema de respuesta ante incidentes automatizado concebido para redes y dispositivos IoT (Internet of Things). Su objetivo primordial es detectar, analizar y mitigar ciberataques de día cero (Zero-Day) de forma autónoma sin necesidad de intervención humana constante o despliegue de personal técnico inmediato, delegando el triaje crítico a un gran modelo de lenguaje (LLM).

El proyecto sigue una arquitectura de **Edge Computing Distribuido** segmentada en dos planos principales interactuando en tiempo real:

* **Sensores Periféricos (Raspberry Pi 4):** Nodos activos que ejecutan servicios reales de red (Servidores Web Nginx, servicios SSH, bases de datos). Actúan en primera línea monitorizando las iteraciones contra sus puertos y enviando un chorro de telemetría ininterrumpido hacia una nube centralizada de comunicaciones. Son "tontos" a nivel analítico pero poseen la autoridad física ("cortafuegos local") para acatar y ejecutar las imposiciones originadas en la mente central.
* **Coordinador IA y Central Hub (Raspberry Pi 5):** El "cerebro". Analiza todo el ecosistema de eventos MQTT, distinguen de manera autónoma si algo es benigno (usuarios válidos o recuento normativo de log) o un comportamiento hostil. Si dictamina un evento malicioso, acciona preventivamente disparos de contención retroactivando los comandos pertinentes a la máquina atacada.

### Ventajas Críticas y Definitorias de este Modelo:

1. **Escalabilidad Horizontal Universal:** Se pueden conectar docenas de sensores a la infraestructura (Raspberry 3, 4, ordenadores Debian externos) sin alterar absolutamente ninguna línea de código de la Pi5.
2. **Aislamiento Cíclico (Air-Gapping):** Si el servidor web u ordenador que actúa de sensor es penetrado gravemente, el Coordinador Pi 5 permanece incomunicado desde la perspectiva local y nunca está comprometido para poder aplicar un protocolo de aislamiento y apagar la red del atacante sin que este consiga escapar al nodo máster.
3. **Offloading de Recursos Computacionales (Cost-Efficiency):** Todo el consumo abrumador de procesador en tareas analíticas de IA, Bases de datos o Servidores Dashboard ocurre en el nodo robusto (Raspberry 5 con refrigeración activa).

---

## 2. Infraestructura Híbrida AWS IoT Core y Comunicaciones MQTT

Todo tráfico y orquestación fluye sin depender de APIs HTTP estándar mediante la infraestructura administrada **AWS IoT Core** utilizando el protocolo estándar **MQTT (Message Queuing Telemetry Transport)**, inmensamente superior por su peso en KB inferior idóneo para redes IOT limitadas.

### Autenticación Criptográfica Robusta (mTLS)

A diferencia del cifrado HTTPS de una página web tradicional -en la que únicamente el cliente corrobora la autenticidad del servidor contra Let's Encrypt-, la tecnología **Mutual TLS (mTLS)** fuerza que ambos bandos acrediten su pasaporte criptográfico. Se provisiona a cada hardware en el recinto local (Pi 4 y Pi 5) de:
* Un identificador de **Certificado X.509 Individual**.
* Una Clave Privada matemáticamente enlazada.
* La validez impuesta por una CA (Certificate Authority) Raíz descargada previamente.

Esto inhabilita absolutamente los ataques *Spoofing* (Alguien falseando ser el Coordinador para enviar la inhabilitación del firewall local en el clúster) o los métodos Sniffing y *Man in the middle*.

### Agnosticismo de Datos: Entendiendo Textos VS JSON Creados
El esquema migró a una arquitectura de jerarquías universales suscribiéndose utilizando canales de Wildcards paramétricos (por ejemplo `#` que abarca todo un árbol: `seguridad/#` en el fichero *config.yml*).
En particular, el Coordinador desarrolló en su capa transaccional Python **Mapeo JSON Dinámico**: Ahora no asume la llegada de simples `auth.log` con "Failed password...", sino que detecta semántica estructurada, transformándola serialmente para digerirla.
Es decir, puede entrar:

```json
{
  "evento": "XSS_DETECTADO",
  "prioridad": "ALTA",
  "sensor": "Pi4-Felix",
  "comentario": "Hola <br> que tal"
}
```

O puede entrar Telemetría plana normal, adaptando en milisegundos todo para el triaje IA.

---

## 3. Inteligencia del SOC: Framework Google ADK y Cadenas de Pensamiento

La magia cerebral del proceso sustituye miles de líneas de reglas SIEM obsoletas o Firewalls con políticas incondicionales empleando en su lugar **Google ADK (Agent Development Kit)**, instruyendo el modelo Generativo mediante el paradigma `LlmAgent`.

### Chain of Thought y Restricción del Bucle de Herramientas (Anti-Alucinaciones)

Se le da control a la IA entregando funciones puras Python (Herramientas, e,g: `register_alert()`). Es extremadamente sensible instruir que el modelo nunca asuma que usar alertas a un nivel no-agresivo está bien, o incurrir en un bug computacional que provoque un círculo en bucle (alucinación repetida infinita).
Así se instruye su raciocinio obligando 3 pasos imperativos en silencio:

```python
soc_agent = LlmAgent(
    name="SOC_Root_Agent",
    model=model_config, 
    instruction="""
    Eres un analista de SOC Nivel 1.
  
    ### PROTOCOLO Y FORENSICS (CHAIN OF THOUGHT):
    1. Quién y Dónde: Evalúa si es una 'ip' externa que ha tocado un host y el 'sensor' exacto de víctimas.
    2. Si es tráfico BENIGNO (telemetría RESUMEN_ACCESOS): No hagas NADA.
    3. Si es ATAQUE CONFIRMADO (SQLi, XSS detectado, Brute force MASIVO): 
       - Registra con 'register_alert' EXACTAMENTE UNA VEZ. Detente ahí.
       - Aplícale 'block_ip' como sentencia de Mitigación al equipo.
       
    Jamás entres en bucles ni alucines herramientas fuera del catálogo.
    """
)
```
Se extrajo la deducción a un motor secuencial muy violento. Si atacas: te bloquean, sin burocracia, sin repasar logs, deteniendo el script y devolviendo el OK de acción mitigada a ADK.

### Puente de IA Cloud-Edge: Escalabilidad contra Privacidad

El repositorio soporta mutar su instinto y su motor sin retocar el código Python en caso de contingencia. A través de la autoverificación del entorno (`.env`):
1. **Modo Remoto (Cloud-Native):** Invoca peticiones nativas sobre **Gemini Flash 2.5**, ganando escalabidad atroz con latencia ínfima perfecta para detener dDoS o intrusiones masivas y agresivas.
2. **Modo Perimetral (Edge-Local Nube Privada):** Usa **Ollama / Gemma local**. Corta íntegramente las tuberías hacia Google aislando la compañía o red del IOT operando lo mismo por IA Open-Source de manera *"air-gapped"* manteniendo 100% control ético de privacidad sin salir al universo internet, redirigiendo la URL del motor Gemini gracias al adaptador *LiteLLM* incrustado en local host.

---

## 4. Estrategia de Optimización: Sistema Dual-Trigger Microbatching

Un riesgo gigantesco implícito con inteligencias artificiales contra redes atacadas es agotar la cuota / billetera financiera o bien colapsar el rate-limit por culpa de bots. Para evitar colapsos producidos por un simple "Ataque Masivo Falso", se construyó un "Parachoques Lógico en Hilos" *Thread-Safe*.

### Concepto de Dispatching en Batcher
La cola `LogBatchQueue` detiene momentáneamente en una variable Python los logs entrantes de AWS en micro paquetes:

* **Trigger 1 (Temporizador):** Vacía la cola en intervalos programados constantes, de ej 15 segs. (Útil ante espionajes esporádicos asíncronos dilatados en tiempo que la IA analiza contextualizando todo).
* **Trigger 2 (Cuantitativo Urgente):** Vacía a presión los bloques si alcanzan tamaño máximo (>10). Responde al segundo y detiene inyecciones letales automáticas.

```python
class LogBatchQueue:
    def add(self, device, raw_log):
        with self._lock: # Crucial para asegurar variables hilos simultáneos
            self._queue.append({"device": device, "raw_log": raw_log})
            return len(self._queue) >= self._max_size

    def flush(self):
        with self._lock:
            batch = list(self._queue) 
            self._queue.clear()       
            self._last_flush = time.time() 
            return batch
```

---

## 5. Panel de Control Táctico SOC v2 (Dashboard Glassmorphism)

Construido en ecosistema Fullstack (Flask / Javascript), rediseñado enfocando conceptos de *Premium CyberSecurity*. Introduce **"Matte Clean / Glassmorphism"**, capas de cristal esmerilado que se perciben por encima de gráficos de estado dinámicos muy reactivos.

### Modales y Evidencias Transparentes (Interacción Usuario)
Más allá del valor pictórico, incluye en la experiencia de UX utilidades de peritaje informático crucial. Todo ataque desmantelado posee botones *Clickables Intereactivos*. En vez de confiar sin fe ciega en la decisión del bot IA, el usuario convoca un plano de Glassmorphism evidenciando 2 puntos:
- Visualiza literalizado el comando en crudo que rebotó hasta atacar la Pi 4 (`sudo iptables -A INPUT -s...`). Evidencia total del script local inyectado.
- Expositiva del cuerpo masivo (JSON nativo) transportado desde las antenas IOT. Transparencia total asumiendo la visibilidad forense y posibilitanto anulación manual.

### Reactividad Asíncrona Front-End `fetch()`
Los métodos antiguos paralizan pestañas F5 en recarga con pausas horribles en la tabla. Ahora el servidor orquesta un tunel REST asíncrono a `/api/data`, parseando miles de métricas recambiando al vuelto del milisegundo en la interfaz sin tocar la barrita de inicio de scroll.
* Incorpora Heurística Aritmética de nivel de amenaza: Incremento no equitativo penalizando x3 el peso de una amenaza considerada *Crítica* en el código fuente.

---

## 6. Proceso de Alta Ingeniería y Profesionalización del Código

Es medular para la calificación justificar el abrumador avance de refabricación (Refactoring) que transformó un borrador en grado corporativo:

1. **Configuración BBDD "Write-Ahead Logging" (Modo WAL):**
   Las librerías base de Python sqlite3 colapsarán ante picos duales con fallos `Database is locked` cuando el Dashboard por un lado interroga el estado, y la IA en paralelo bloquea inserciones. Activando `.execute("PRAGMA journal_mode=WAL")` y deshabilitando revisiones cruzadas de hilos `check_same_thread=False` se otorgó invulnerabilidad técnica y agilidad inmarcesible en escritura y lectura cruzada masiva.
2. **Abstracción Paramétrica Criptografiada:**
   Todas las tablas pasaron del español rígido al genérico léxico Internacional; y los comandos HTTP Basic escondiendo y aislando accesos en encriptaciones de hashes de contraseña en lugar de lecturas planas y débiles.
3. **Validación Dinámica Absoluta de Rutas y Tokens (`.env` Bridge):**
   La lógica para importar librerías ocultas se refinó para buscar interactivamente desde cualquier carpeta sin fallar asumiendo strings limpiados y condicionados que previenen accidentes por caracteres erráticos.

---

## 7. Sugerencias Críticas de Capturas e Ilustraciones para tu Memoria

Las mejores capturas con peso argumentativo son aquellas que desvelan procesos puros corriendo in situ:

1. **Fotograma General del Radar Glassmorphism:** Capturando en gran escala la curva ascendente de ataques frente a colores sobrios del entorno *Dark Mode*, dando sensación de "Centro de Inteligencia".
2. **"Unbox" Forense (Modal Flotante):** Captura centrada de tí haciendo click a uno de los ataques de la pantalla y el sistema evidenciando frente al lente el comando interno de iptables originado sobre Raspberry remota en milisegundo uno. 
3. **El Cerebro Consola-Bash de Ejecución Micro-Batch Híbrido C++:**
   Captura brutal en tu editor PowerShell de un volcado del contenedor `pi5-soc-coordinator`:
   `[INIT] => AI_MODE: 'api'`
   `[BATCH] Flushing 4 log(s) to ADK agent...`
   Sirve como testimonio indiscutible de que el código Batch no es una quimera y ejecuta los bloques con eficiencia protegitendo límites API 429 de Google.
4. **Capturas de AWS Core Payload:** Evidencia gráfica de los MQTT topics enviando el payload masivo desde un mock a `seguridad/#` y viendo como salta al vuelo en SOC en formato binario.
