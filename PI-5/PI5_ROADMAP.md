# Roadmap de Mejoras: Coordinador SOC (PI-5)

Dado que actualmente solo tienes permisos en la PI-5, nos centraremos exclusivamente en endurecer y optimizar el "Cerebro" de la arquitectura. A continuación, se detalla la lista de tareas pendientes. Puedes marcar las casillas `[x]` conforme vayamos completándolas.

## 1. Implementación de Guardarraíles (Seguridad de la IA)

Los "rieles" se deben implementar en dos capas dentro de la PI-5: en las instrucciones del agente y en la validación de las herramientas Python antes de enviarlo por red.

- [ ] **Modificar el Prompt del Triage Agent (`src/agents/triage_agent/triage_agent.py`):**
  - Cambiar las instrucciones para que el agente **tenga terminantemente prohibido** escribir comandos Bash.
  - Forzar a que responda usando parámetros de un modelo de datos estructurado (ej. Acción: `bloquear_puerto`, Objetivo: `80`, en lugar de `sudo iptables...`).
- [ ] **Blindar las herramientas (`src/tools/iot_tools.py`):**
  - Modificar `block_ip` y `execute_remote_command` para que eliminen cualquier intento de inyección de bash.
  - Las herramientas solo deben enviar a AWS el JSON validado y estructurado, actuando como la última barrera de seguridad si la IA alucina.

## 2. Refactorización Estructural (Mejorar Cohesión)

Graphify detectó que el archivo principal tiene una cohesión muy pobre (0.14). Está mezclando infraestructura con lógica de negocio.

- [ ] **Extraer el Gestor de Colas:**
  - Sacar la clase `LogBatchQueue` y el hilo `_batch_dispatcher` de `main_coordinator.py` y moverlos a un nuevo archivo (ej. `src/utils/queue_manager.py`).
- [ ] **Extraer la Configuración MQTT:**
  - Mover la lógica de `process_event` a un controlador específico. Así el `main_coordinator.py` se quedará solo como el punto de entrada limpio (el *glue code*).
- [ ] **Proteger el Parseo JSON:**
  - En `main_coordinator.py`, el doble `json.loads` es frágil. Envolver el segundo parseo en un bloque `try-except` para que el coordinador no sufra un *crash* fatal si recibe un log malformado.

## 3. Persistencia Robusta (Evitar Condiciones de Carrera)

Actualmente, el sistema asume que la última alerta guardada es siempre la que se está mitigando, lo cual fallará bajo un ataque concurrente.

- [ ] **Añadir Identificador Único (`src/tools/db_tools.py`):**
  - Modificar `register_alert` para que genere un identificador único (ej. UUID) para cada ataque y lo devuelva.
- [ ] **Actualización Segura del Feedback:**
  - Modificar `update_alert_status` para que busque ese UUID exacto en lugar de usar `ORDER BY timestamp DESC LIMIT 1`.
- [ ] **Limpiar reglas (Auto-Unban):**
  - Añadir un hilo en el coordinador o un script en la PI-5 que periódicamente limpie alertas o envíe órdenes de desbloqueo a la PI-4 para que sus tablas no se llenen infinitamente.
