# Plan de implementacion: resiliencia ante Gemini 429

## Objetivo

Evitar que el SOC pierda eventos cuando el modelo remoto Gemini falle por cuota o limite de gasto, manteniendo el comportamiento actual del proyecto:

- Sin fallback automatico a modelos locales.
- Sin reemplazar recomendaciones libres por acciones parametrizadas cerradas.
- Sin eliminar comandos largos de mitigacion HITL.

## Causa observada

El coordinador recibio nuevos eventos MQTT y los envio al agente ADK, pero Gemini respondio:

```text
429 RESOURCE_EXHAUSTED
Your project has exceeded its monthly spending cap.
```

Esto significa que el proveedor API no acepto mas inferencias por limite de gasto/cuota. El problema no fue MQTT ni la ejecucion de comandos en PI-4; fue disponibilidad del modelo remoto.

## Cambio de modelo API

Actualizar el modelo configurado para usar Gemini 3 Flash explicitamente:

```env
AI_MODE=api
AI_MODEL=gemini-3-flash-preview
```

Motivo:

- Evitar alias movibles como `gemini-flash-latest`, que pueden cambiar de version y coste sin tocar el codigo.
- Reducir riesgo de consumo inesperado usando el modelo Flash concreto deseado.
- Mantener uso de API remota, sin pasar a modelo local.

Archivos a revisar:

- `PI-5/soc_manager.sh`: opcion de preparacion de entorno para que escriba `AI_MODEL=gemini-3-flash-preview`.
- `docs/Configuration_and_Deployment.md`: ejemplos de `.env`.
- Cualquier `.env` real desplegado en PI-5.

## Persistencia de eventos pendientes

Crear una tabla SQLite para eventos que no pudieron procesarse por fallo del modelo:

```sql
CREATE TABLE IF NOT EXISTS pending_ai_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device TEXT NOT NULL,
    queue_type TEXT NOT NULL,
    raw_log TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING_AI_RETRY',
    error_reason TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    next_retry_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

Cuando `runner.run_async()` falle por `429 RESOURCE_EXHAUSTED`, el evento actual debe guardarse ahi en lugar de perderse.

## Reintento con backoff

Anadir un worker de reintento que:

1. Busque eventos `PENDING_AI_RETRY` cuyo `next_retry_at` ya haya vencido.
2. Los reprocese con el mismo agente correspondiente (`triage` o `feedback`).
3. Si vuelve a fallar por 429, incremente `retry_count` y retrase el siguiente intento.
4. Si se procesa correctamente, marque el evento como `PROCESSED`.

Backoff recomendado:

- 1 minuto tras el primer fallo.
- 5 minutos tras el segundo.
- 15 minutos tras el tercero.
- 1 hora a partir del cuarto.

## Visibilidad operativa

Cuando se detecte el fallo:

- Registrar una linea clara en logs: `Fallo modelo API: Gemini ha superado cuota/gasto. Evento guardado como PENDING_AI_RETRY`.
- Evitar tracebacks repetidos si el error ya fue clasificado.
- Exponer en dashboard un contador o estado de eventos pendientes de IA.

## Limpieza desde SOC Manager

Extender `purge_logs_and_records()` en `PI-5/soc_manager.sh`.

Actualmente limpia la tabla `logs`. Debe limpiar tambien:

```sql
DELETE FROM pending_ai_events;
```

Esto garantiza que:

- `SOC Manager -> 5 -> 3` deja limpio el historial visible y los eventos pendientes.
- La desinstalacion completa con volumenes sigue eliminando todo.
- No quedan eventos antiguos reintentandose tras una limpieza manual.

## Pruebas necesarias

1. Simular un `429 RESOURCE_EXHAUSTED`.
2. Verificar que el evento queda en `pending_ai_events`.
3. Verificar que no se cambia a modelo local.
4. Verificar que el worker reintenta respetando backoff.
5. Verificar que `SOC Manager -> 5 -> 3` borra `logs` y `pending_ai_events`.
6. Verificar que el `.env` generado usa `AI_MODEL=gemini-3-flash-preview`.
