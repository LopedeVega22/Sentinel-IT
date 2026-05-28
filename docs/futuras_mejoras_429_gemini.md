# Futuras mejoras diferidas tras incidente Gemini 429

**Estado:** DIFERIDO. No forma parte del arreglo inmediato del fallo observado el 2026-05-28.

## Contexto

Durante la ejecucion del SOC, el coordinador proceso correctamente alertas SQLi/XSS, propuso mitigaciones HITL y registro feedback de PI-4. El fallo operativo principal no estuvo en MQTT ni en las mitigaciones, sino en el proveedor IA remoto: Gemini devolvio `429 RESOURCE_EXHAUSTED` por superar el limite mensual de gasto del proyecto.

El arreglo inmediato debe limitarse a resiliencia de eventos pendientes y visibilidad del fallo API. Las siguientes mejoras quedan aparcadas para no desviar el objetivo del proyecto ni cambiar el comportamiento inteligente del agente.

## Mejoras diferidas

1. **Dashboard en modo produccion**
   - Sustituir el servidor Flask de desarrollo por `gunicorn` u otro WSGI cuando se exponga fuera de un entorno controlado.
   - Mantener reverse proxy con TLS si el dashboard sale de la LAN.
   - Mantener autenticacion obligatoria con `DASHBOARD_PASSWORD` o `DASHBOARD_PASSWORD_HASH`.

2. **Higiene de secretos en comandos y logs**
   - Futuro: evitar contrasenas inline en comandos largos, redactarlas en dashboard/logs o moverlas a mecanismos mas seguros.
   - No se implementa ahora: se acepta temporalmente el hardcodeo porque no es la causa del fallo actual.

3. **Separacion de sesiones ADK por agente**
   - Crear sesiones independientes para `SOC_Triage_Agent` y `SOC_Feedback_Agent` si los avisos `Event from an unknown agent` generan ruido operativo o problemas de trazabilidad.
   - No afecta directamente al fallo `429`, pero mejoraria limpieza de logs y diagnostico.

4. **Auditoria avanzada de aprobaciones HITL**
   - Registrar operador, IP origen, timestamp y version final editada del comando en cada aprobacion.
   - Mantener el diseno actual de comandos ricos y recomendaciones flexibles; no convertir el sistema en acciones parametrizadas cerradas.

## Decisiones explicitas

- No se anade fallback automatico a modelos locales: si falla la API, el sistema debe indicarlo claramente y dejar el evento pendiente.
- No se reemplazan recomendaciones libres por acciones parametrizadas: el objetivo del proyecto es que el agente razone con opciones recomendadas y proponga comandos adaptados al contexto.
- No se elimina el uso de comandos largos encadenados: se mantienen porque forman parte del enfoque de mitigacion integral supervisada por HITL.
