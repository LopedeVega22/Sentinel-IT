# Changelog de Cambios y Estado del Proyecto (Sentinel-IT)

Este documento mantiene un registro vivo de las implementaciones, correcciones y evoluciones arquitectónicas del proyecto SOC Autónomo (Sentinel-IT). Su propósito es servir de punto de lectura automatizado para que la IA asistente comprenda el estado actual del repositorio sin requerir depender de memoria volátil.

## [Actual] - Últimos cambios (Abril 2026)

### 1. Validación End-to-End del Bucle de Mitigación SOC
- **Pruebas de Comunicación:** Se han desarrollado y testeado scripts de simulación de comunicación entre el nodo Coordinador (Raspberry Pi 5) y el nodo Edge (Raspberry Pi 4).
- **Feedback Loop Database:** Se validó la correcta inserción en SQLite (`soc_alerts.db`) de comandos de seguridad y sus resultados de ejecución (éxito/error).
- **Serialización de Datos:** Mejora en el dashboard web para que refleje de manera precisa los eventos y el estado de mitigación mediante actualización de serialización.

### 2. Refinamiento de la Interfaz (Dashboard SOC)
- **Live Threat Feed:** Se ha corregido el layout de la tabla en tiempo real.
- **Raw Log Viewer:** Se implementó un modal premium interactivo (Glassmorphism) con resaltado de sintaxis para visualizar logs en bruto.
- **Mapeo de Datos:** Los datos críticos de incidentes (timestamps, logs en crudo, comandos de mitigación) se renderizan correctamente para el operador.

### 3. Solución de Crashes del Agente IA y Tooling
- **KeyError / Context Variable Not Found:** Se refactorizó el system prompt del agente de triaje para eliminar plantillas en formato JSON (ej. `{IP}`) que el framework ADK intentaba procesar incorrectamente como variables de contexto.
- **Tool Hallucination:** Se ajustó la configuración del agente local (usando Gemma 4:e2b vía Ollama) para asegurar que use estrictamente las herramientas registradas (`register_alert`, `block_ip`, `execute_remote_command`) sin alucinar la herramienta "SOC_Root_Agent".

### 4. Sistema Dual-Agent y Procesamiento JSON
- **Arquitectura Dual:** Se probó exitosamente el flujo entre el Triage Agent (que emite comandos de mitigación) y el Feedback Agent (que procesa la telemetría de respuesta y cierra el bucle).
- **JSON Agnostic:** El coordinador y el agente autónomo fueron adaptados para procesar eventos de seguridad y telemetría estructurados de forma nativa en JSON (XSS, SQLi), en lugar de limitarse solo a logs SSH antiguos (auth.log).
