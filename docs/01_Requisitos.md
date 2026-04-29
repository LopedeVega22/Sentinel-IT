# 01 - Fase de Requisitos e Inicio

Este documento sirve para anotar las decisiones y requisitos iniciales de nuestro TFG. Como tu coordinador IA, iré actualizando este documento conforme tomemos decisiones.

## Información Pendiente de Definir

1. **Fechas Clave:**
   - Objetivo de finalización interna: *Principios de Junio 2026*
   - Entrega oficial prevista: *Finales de Junio 2026*

2. **Stack Tecnológico Específico:**
   - **Agentes IoT (Raspberry Pi 4 y 5):** Python (usando la librería AWS IoT Device SDK v2 para Python).
   - **Base de Datos (Nodo Coordinador - Pi 5):** SQLite (ligera, gratuita, no requiere servidor dedicado independiente y es perfecta para el volumen de datos de un TFG).
   - **API / Frontend (Nodo Coordinador - Pi 5):** Flask (Python) para servir de forma ligera los datos de SQLite en un Dashboard Web (HTML/JS/CSS).

3. **Alcance y Caso de Uso (Flujo Principal):**
   - **Nodo Protegido (Pi 4):** Actuará como un recolector "tonto" pero seguro. Monitorizará servicios reales (ej. SSH y Nginx) y enviará los **logs en bruto** (*raw logs*) a través de MQTT a AWS IoT Core. No gastará recursos locales en analizar.
   - **Nodo Coordinador (Pi 5):** Recibirá esos logs en bruto desde AWS. Integrará un **Agente de IA (usando Google Gemini 1.5 con filosofía Agentic AI - ADK)** que se encargará de razonar e interpretar los logs en tiempo real.
   - **Visión Avanzada (Para nota de excelencia) - ¡CONSEGUIDA!:**
     - **Autonomía Agentic AI:** El modelo de lenguaje tiene herramientas programadas ("Tools" o Funciones) estipuladas en código. Decide de manera autónoma cuándo llamar a `registrar_alerta` o cuándo llamar a `bloquear_ip`.
     - **Grado de Profesionalización (Enterprise):** Toda la configuración está externalizada (`config.yml` y `.env`). Los logs internos se gestionan mediante `RotatingFileHandler` para evitar saturar las RPi. Todo el bloque puede orquestarse automáticamente vía scripts de Setup, servicios `Systemd` o contenedores `Docker`.
     - **Respuesta Graduada:** La IA decide niveles de acción que envía por AWS IoT a la Pi 4:
       - *Leve:* Notifica al Admin (bot de Telegram / Email) o hace *Rate Limiting*.
       - *Grave:* Bloqueo total temporal de la IP en el Firewall (`iptables`).

4. **Pruebas de Concepto y Defensa:**
   - Hay que definir qué ataques se van a mostrar en directo durante la defensa para disparar las alertas de la IA.
   - Ejemplos tentativos: Fuerza bruta SSH (Hydra), Escaneo Web malicioso (Dirb/Nmap).

5. **Requisitos Académicos:**
   - Formato requerido para la Memoria del TFG.
   - Extensión requerida.
