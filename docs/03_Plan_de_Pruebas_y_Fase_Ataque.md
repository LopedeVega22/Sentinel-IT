# Documento de Pruebas y Simulacro de Ataque (Defensa del TFG)

Este documento detalla el procedimiento paso a paso para ejecutar una demostración técnica en vivo durante la defensa del TFG, probando la efectividad de la arquitectura IoT y la capacidad de respuesta del Agente Inteligente (Gemini).

## Escenario de la Demostración

**Objetivo:** Demostrar cómo el nodo recolector (Pi 4) detecta un ataque de fuerza bruta SSH, cómo el Coordinador de IA (Pi 5) analiza el patrón usando Agentic AI, y cómo ordena un bloqueo físico en la capa de red (Firewall/iptables) del nodo afectado, todo en tiempo real.

**Actores:**

1. **Atacante (Portátil/PC de demostración):** Equipo desde el que se lanza el ataque.
2. **Nodo Protegido (Casa 1 - Raspberry Pi 4):** La víctima del ataque. Lee sus logs en tiempo real.
3. **Coordinador SOC (Casa 2 - Raspberry Pi 5):** El cerebro que aloja el agente de Gemini y el Dashboard.

---

## Preparación del Entorno (Antes de la Demostración)

1. **En la Pi 5 (Coordinador):**
    * Revisar que los certificados AWS y el archivo `.env` con la clave de Gemini estén en el directorio.
    * Asegurarnos de que el entorno en background está running (arrancado vía `setup.sh` o con `docker-compose up -d`).
    * Navegar a `http://<IP_PI5>:5000` en el proyector para visualizar el Dashboard Web.
    * Mantener abierta una terminal leyendo los logs del agente: `tail -f coordinator_soc.log`.
2. **En la Pi 4 (Sensor):**
    * Asegurarse de que el servicio está levantado (vía `setup.sh` o contenedor Docker).
    * Mantener abierta la terminal auditando los logs del atacado: `tail -f sensor_soc.log`.
3. **Visual:** Tener abierto el proyector mostrando el Dashboard, el monitor SOC a un lado, y la consola del Atacante.

---

## Guion del Ataque Simulado (El Día de la Defensa)

### Paso 1: Tráfico Normal (Línea Base)

* *Acción:* El atacante realiza un ping normal o se conecta por SSH introduciendo la contraseña correcta.
* *Expectativa:* La Pi 4 lo registra, pero no es un error. El sistema no dispara alarmas.

### Paso 2: Lanzamiento del Ataque (Fuerza Bruta SSH)

* *Acción:* Desde el equipo Atacante (es mejor usar Linux/Kali o WSL), ejecutamos una herramienta de fuerza bruta como `Hydra` contra la IP de la Pi 4.

    ```bash
    # Comando de ejemplo usando Hydra para atacar al usuario 'pi' en la Pi 4
    hydra -l pi -P passwords_comunes.txt ssh://<IP_PI4> -t 4
    ```

    *(Si no se tiene Hydra, un script en bash que haga 20 intentos de SSH fallidos seguidos con contraseñas aleatorias sirve igual).*

### Paso 3: Observación en Tiempo Real (La Magia)

* **En la Pi 4 (Sensor):** En su terminal, veremos cómo intercepata rápidamente los fallos en `/var/log/auth.log` y muestra mensajes de publicación MQTT hacia AWS.
* **En AWS IoT Core (Transmisión):** Los logs viajan cifrados.
* **En la Pi 5 (Cerebro):** Si estamos leyendo `coordinator_soc.log`, veremos cómo la IA entra en acción de fondo. El agente de Gemini recibe la batería de fallos.
* **El Agente Decide:** Se leerá en el .log de la red central: `[AGENTE] Herramienta 'bloquear_ip' ejecutada! Mandando orden...` porque la IA ha deducido, aplicando heurística de comportamiento de seguridad (Agentic AI), que el patrón obedece a un ataque distribuido.

### Paso 4: Cierre del Bucle (Mitigación)

* La orden viaja de la Pi 5 -> AWS -> Pi 4.
* **En la Pi 4:** Extrae del JSON la IP atacante y automáticamente ejecuta un comando real de sistema operativo (iptables DROP).
* **Comprobación del Atacante:** El portatil del atacante (Hydra) de repente se queda colgado (`Connection timed out`). El ataque ha sido neutralizado físicamente.

### Paso 5: Visualización para Ejecutivos (Dashboard)

* En la pantalla del navegador del tribunal, al refrescar la página (o si implementasteis auto-refresco en el futuro), se verán:
  * Los KPIs aumentados (1 bloqueo nuevo).
  * En la "Base de Datos de Inteligencia", aparecerán los logs de los intentos, catalogados en ROJO (Gravedad: Crítica), detallando que el "Veredicto IA" ha detectado un ataque de fuerza bruta proveniente de origen malicioso, y documentando que la acción definitiva ha sido un "Bloqueo Automático (Ban IP)".

---

## Retorno a la normalidad (Cleanup)

Para poder repetir la prueba o liberar tu propio portátil:
En la Pi 4, ejecutar: `sudo iptables -F` (Flush de las reglas de bloqueo).
Y como opción, borrar la bbdd `soc_data.db` en la Pi 5.
