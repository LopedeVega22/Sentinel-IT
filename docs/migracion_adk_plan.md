# Análisis de Potencial: Google ADK en el Proyecto SOC (TFG)

## 1. Situación Actual del Proyecto

Actualmente, el proyecto (específicamente el coordinador en `pi5-dani/main_coordinator.py`) **no utiliza el framework Google ADK (Agent Development Kit)**. En su lugar, emplea la librería estándar de Gemini (`google-generativeai`) para invocar a un único modelo generativo al que se le pasan dos funciones Python (`registrar_alerta` y `bloquear_ip`) como herramientas (function calling).

Aunque el sistema tiene un comportamiento "agéntico" básico (razona y llama a herramientas), **NO está sacando el potencial del Google ADK**, ya que la arquitectura actual omite las ventajas de orquestación, memoria, y depuración que ofrece este nuevo framework.

## 2. Ventajas que aportaría migrar a Google ADK

El Google ADK está diseñado para construir agentes robustos y escalables. Migrar el coordinador SOC al ecosistema ADK aportaría los siguientes beneficios clave:

1. **Interfaz de Depuración y Monitoreo (ADK Web):** ADK provee un comando (`adk web`) que levanta un servidor local donde se pueden analizar en tiempo real los *Eventos*, *Estados* y *Sesiones* del agente. Para un entorno SOC, esto es invaluable, ya que permite ver visualmente y paso a paso por qué el agente decidió bloquear una IP o clasificar un log de cierta manera.
2. **Arquitectura Multi-Agente:** En lugar de tener un único prompt gigante, ADK permite crear múltiples agentes especializados (ej. un *AnalystAgent* que clasifica el ataque y un *ActionAgent* que ejecuta medidas) que colaboran entre sí.
3. **Gestión de Sesiones (Memoria) Nativa:** ADK administra el historial de conversaciones y el estado de forma nativa. Actualmente, el proyecto depende de `chat.send_message()`, el cual mantiene un historial lineal simple que puede desbordarse o perder contexto en ejecuciones prolongadas.
4. **Callbacks:** ADK permite inyectar código en diferentes partes del ciclo de vida del agente (antes de ejecutar, después de ejecutar, etc.), lo que permitiría estructurar el sistema de logging (actual en `logger.info`) de una manera mucho más limpia y estandarizada.

## 3. Modificaciones Necesarias para la Migración

Para implementar Google ADK en el proyecto actual, habría que realizar las siguientes modificaciones estructurales y de código:

### A. Reestructuración de Directorios

ADK exige que los agentes estén contenidos en módulos estructurados. Se debe modificar la estructura en `pi5-dani` para seguir el estándar ADK:

```text
pi5-dani/
├── config.yml
├── .env                  <-- Aquí residirá GEMINI_API_KEY
├── agents/
│   ├── soc_agent/
│   │   ├── __init__.py
│   │   ├── soc_agent.py  <-- Definición del agente principal usando ADK
│   ├── analyst_agent/    <-- (Opcional) Agente especializado en analizar el log
│   │   ├── __init__.py
│   │   ├── analyst.py
├── tools/
│   ├── db_tools.py       <-- Refactorización de registrar_alerta
│   ├── iot_tools.py      <-- Refactorización de bloquear_ip
├── main_coordinator.py   <-- Archivo principal modificado
```

### B. Refactorización de Herramientas (Tools)

Se deben separar las funciones `registrar_alerta` y `bloquear_ip` del archivo principal y adaptarlas a la definición nativa de herramientas del ADK (si la sintaxis del framework es distinta al standard function calling de SDK, adaptando tipados y docstrings estrictos, dado que ADK confía en los docstrings para tomar decisiones de enrutado).

### C. Implementación de los Agentes en ADK

Mover la instanciación de `genai.GenerativeModel(...)` hacia la sintaxis de ADK.

*Ejemplo conceptual de soc_agent.py en ADK:*

```python
# soc_agent.py
from adk.agent import Agent
from tools.db_tools import registrar_alerta
from tools.iot_tools import bloquear_ip
import pydantic # ADK usa a menudo modelos estructurados para output

# Se define el agente
soc_agent = Agent(
    name="SOC_Root_Agent",
    model="gemini-2.0-pro-exp", # Usar el modelo necesario
    description="Agente principal encargado de recibir logs de los edge devices y decidir respuestas.",
    instructions="""Eres un Agente SOC Autónomo operando en un sistema IoT Edge...
    [Tus reglas de operación...]""",
    tools=[registrar_alerta, bloquear_ip]
)
```

### D. Refactorización del Main Coordinator (`main_coordinator.py`)

El archivo principal ya no inicializará el cliente de Gemini directamente, sino que importará y ejecutará el agente ADK.
La función `procesar_evento` (el callback de MQTT) deberá inyectar el mensaje en el estado de la sesión del ADK.

```python
# En main_coordinator.py (pseudocódigo ADK)
from agents.soc_agent.soc_agent import soc_agent

def procesar_evento(topic, payload, **kwargs):
    # ... parsing de msg ...
    mensaje_agente = f"Nuevo Log: {raw_log}"
  
    # Invocación estilo ADK (dependerá de la API exacta de google-adk)
    response = soc_agent.run(mensaje_agente)
    logger.info(f"Respuesta del ADK: {response}")
```

### E. Integración de Callbacks para Logging (Opcional pero recomendado)

Sustituir la escritura manual en los `logger.info("CEREBRO...")` por un sistema de `Callbacks` del ADK, creando una clase o función que se enganche a los eventos (e.g., `on_agent_start`, `on_tool_execute`, `on_agent_finish`) para registrar todo el razonamiento del agente en el archivo rotatorio de logs sin ensuciar la lógica principal del negocio.

### F. Actualizar Dependencias

- Se debe añadir la instalación del paquete `google-adk` (o el nombre oficial exacto del paquete de Python actual para este toolkit) en `requirements.txt`.
- Añadir pasos en `setup.sh` para instalar estas nuevas dependencias.

## 4. Conclusión y Siguientes Pasos

El proyecto actual funciona y demuestra el paradigma de seguridad autónoma. Sin embargo, **una refactorización a Google ADK lo elevaría de un "script de invocación M2M" a una arquitectura empresarial de agentes**. Mejoraría drásticamente la capacidad de observar qué piensa el agente (`adk web`), facilitaría la escalabilidad a múltiples agentes (ej. separar el triaje de la ejecución de bloqueos) y estandarizaría el proyecto según las últimas mejores prácticas documentadas en Google.

Sugiero que el siguiente paso para implementar esta migración sea crear las carpetas de los agentes, trasladar la lógica del `main_coordinator.py` al entorno ADK y validar que las comunicaciones MQTT siguen siendo estables con esta nueva capa de orquestación.
