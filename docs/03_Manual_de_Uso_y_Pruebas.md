# Manual de Testeo y Dashboard (Simulación)

Este manual te guiará durante la presentación o defensa de tu TFG para provocar métricas e incidentes que tu red de sensores y tu modelo de IA Gemini puedan analizar y reaccionar.

## 1. El Dashboard Web SOC

El cuadro de mandos está programado en Python (Flask) como una ventana viva al historial interactivo de tu red defensiva.

- **URL de acceso:** `http://<IP_DE_LA_RASPBERRY_PI5>:5000`
- **¿Qué muestra?:** Extrae datos de la base de datos local precompilada (`soc_data.db` que creamos en el build del contenedor Docker). Vas a ver el total de logs parseados, el porcentaje de incidentes considerados críticos por tu Google ADK, y la actividad reciente en tiempo real de qué se está bloqueando.

### Reversión de Falsos Positivos
La IA no está autorizada para borrar bloqueos por sí misma. A la derecha de cada incidente reportado como "Bloqueo Activo Emitido", tendrás un botón en rojo **(Revertir)**. Si lo pulsas, el Dashboard enviará un cohete MQTT cifrado hacia el Sensor en problemas borrando del IPTables esa IP banneada y restaurando el estado original del sensor. El log de la web pasará a poner "REVERTIDO".

---

## 2. El Simulador de Ataques (Cómo inyectar tráfico hostil)

En la raíz del código (`simulador_ataque.py`), dispones de un binario que ejecuta un asalto por fuerza bruta con el módulo `paramiko` para hacer chillar las sirenas del SOC.

### Requisitos locales
Si estás en tu PC personal apuntando al clúster, instala antes parametrización básica:
```bash
pip install paramiko
```

### Arranque del ataque
Edita o arranca el script apuntando a uno de tus nodos sensores (`pi4-felix`):
```bash
python simulador_ataque.py
```
El script lanzará una ráfaga ininterrumpida de combinaciones (usuario admin, root, contraseñas 1234...).
Aquí entra la magia matemática de ADK.

## 3. ¿Cómo evalúa el ataque el Cerebro Pi5?

La Raspberry Pi 4 se dará cuenta de estos fallos repetidos en su módulo `.service` y escupirá todos los mensajes de error SSH por MQTT al nodo Pi 5.

**El pipeline de respuesta de la IA (soc_agent.py):**
1. **[TRAFICO BENIGNO]**: Entra una conexión normal tuya, el modelo comprueba el hash interno, escribe un veredicto positivo por pantalla y no toca ni notifica base de datos.
2. **[ACTIVIDAD SOSPECHOSA]**: El simulador inyecta algo raro. El ADK usa internamente la herramienta `registrar_alerta` en SQLite sin bloquear nada, hasta tener más certeza contextual.
3. **[ATAQUE CONFIRMADO]**: Tras las iteraciones de `paramiko`, el LLM concluye un índice alto de Gravedad Crítica. La herramienta `bloquear_ip(dispositivo, IP)` se dispara automáticamente publicando instrucciones devuelta a AWS, baneando al objetivo y apareciendo reluciente en rojo en el Dashboard Web de la defensa principal.
