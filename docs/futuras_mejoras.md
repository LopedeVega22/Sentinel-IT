# Futuras mejoras — Sentinel-IT

Documento vivo donde se registran propuestas técnicas evaluadas pero **no implementadas todavía**. Cada entrada incluye motivación, diseño y plan de implementación para retomarse cuando convenga.

---

## 1. Motor de Políticas centralizado en PI-5 (Policy Engine)

**Estado:** ✅ RESUELTO el 2026-05-16 — implementado con el enfoque de **clasificación por nivel de riesgo** (no whitelist cerrada). Detalles completos en [funcionamiento_policy_engine.md](funcionamiento_policy_engine.md). Las dos objeciones marcadas a continuación (`Pregunta:` en la sección de PI-5 y `Esta parte no me convence` al final del bloque Capa 1) están atendidas:

- `sudo cat /var/log/...` y otras lecturas pasan como `SAFE_READ` sin fricción; los comandos destructivos se etiquetan por nivel y el dashboard los pinta con código de color.
- Los verbos desconocidos caen a `LOW` y llegan al humano. Nunca hay DENY automático por "no encajar en una familia".

Lo que sigue es el registro histórico de la motivación original.

### Motivación

El sistema actual de validación de comandos antes de publicarlos por MQTT vive en dos capas independientes y poco coherentes:

- **PI-5** ([iot_tools.py:49](../PI-5/src/tools/iot_tools.py#L49)): blacklist de substrings (`rm `, `kill `, `chmod`, ...)
  Pregunta: ¿Mejor que bloquear determinados comandos, porque esos limita mucho, no sera mejor poner una lista de comandos las cuales necesite verificacion humana desde el dasboard y que haya distintos niveles de peligro en el comando que se vaya a ejecutar manualmente. y que todos los comandos de ver logs archivos etc pueda usarlos sin problema aunque sea un sudo cat?

Problemas concretos:

1. La blacklist por substring es eludible: `php -r 'system("rm -rf /tmp")'` no contiene `rm ` exacto y pasa.
2. La whitelist por token de PI-4 permite cualquier `php` con cualquier argumento, incluido `php -r '...'`.
3. Inconsistencia entre capas: PI-5 permite `sudo cat /etc/shadow` (matches `sudo cat `) pero PI-4 también lo permitiría (`cat` no está en su whitelist... pero el comando ya está aprobado por PI-5 antes de publicar).
4. PI-5 no verifica que el comando que PI-4 dice haber ejecutado coincide con lo que PI-5 envió. Si un cert filtrado publica directo en `seguridad/Pi4-Felix/comando`, PI-4 lo ejecuta y PI-5 no detecta nada anómalo.
5. No hay log de auditoría inmutable que registre quién propuso, quién aprobó y qué pasó al final.

### Diseño propuesto — Policy Engine en PI-5 (sin tocar PI-4)

Módulo nuevo `PI-5/src/tools/policy_engine.py` con cuatro funciones:

| Función                                                         | Responsabilidad                                                                       |
| ---------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| `validate(cmd) → ALLOW_READ \| ALLOW_WRITE_HITL \| DENY`        | Parsea con `shlex` y compara contra un esquema estructurado por familia de comandos |
| `record_dispatch(cmd, device, log_id)`                         | Cachea cada comando emitido (TTL 5 min) + audit_log table                             |
| `verify_feedback(executed_cmd, device) → MATCH \| ANOMALY`     | Compara comando ejecutado vs cache emitidos                                           |
| `classify(cmd) → "diagnostic" \| "mitigation" \| "destructive"` | Sustituye el reparto actual basado en substrings de `sudo`                          |

#### Capa 1 — Validación semántica por familia

```python
COMMAND_FAMILIES = {
    "iptables_query": {
        "intent": "diagnostic",
        "pattern": ["sudo", "iptables", ("-L"|"-S"|"--list"|"--check")],
    },
    "iptables_block_ip": {
        "intent": "mitigation",
        "pattern": ["sudo", "iptables", "-A", "INPUT", "-s", IP, "-j", "DROP"],
        "args": {"IP": r"^\d{1,3}(\.\d{1,3}){3}$"},
    },
    "session_php_close": {
        "intent": "mitigation",
        "pattern": ["php", PHP_PATH, ("--cerrar-usuario" | "--cerrar-nombre"), VALUE],
    },
    "systemctl_status": {
        "intent": "diagnostic",
        "pattern": ["sudo", "systemctl", "status", SERVICE],
        "args": {"SERVICE": r"^(apache2|nginx|vsftpd|mariadb|ssh)$"},
    },
    # ...
}
```

Cualquier comando que no encaje en *una* familia → `DENY` con motivo registrado. (Esta parte no me convence por lo mismo que te dije antes en la pregunta que te hice)

#### Capa 2 — HITL obligatorio para `intent="mitigation"`

`intent=diagnostic` → publicación directa. `intent=mitigation` → forzosamente pasa por `request_mitigation_approval`. El agente IA no puede saltarse el HITL aunque crea que es seguro.

#### Capa 3 — Cache de comandos emitidos + verificación de round-trip

Cada `publish` desde PI-5 se registra con `(comando, device, log_id, ts)` en cache TTL 5 min. Cuando llega un feedback en `seguridad/+/respuesta`:

- Si `executed_cmd` ∈ cache → MATCH.
- Si `executed_cmd` ∉ cache → **ANOMALY**. Se levanta un incidente `INTRUSION-COMMAND-INJECTION` automáticamente.

#### Capa 4 — Audit log inmutable

```sql
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts DATETIME DEFAULT CURRENT_TIMESTAMP,
    event_type TEXT,
    device TEXT,
    command TEXT,
    classification TEXT,
    decision_reason TEXT,
    related_log_id INTEGER
);
-- Trigger para impedir UPDATE/DELETE desde la app
```

### Limitación honesta

Sin cooperación de PI-4 no se puede garantizar criptográficamente que un comando que llega a PI-4 vino de PI-5. La defensa actual es la Policy de AWS IoT (3 client_ids autorizados). El Policy Engine **detecta a posteriori** la anomalía vía round-trip verification.

### Mapeo con estándares para la memoria del TFG

| Hueco                                             | Capa que lo cierra                     | Referencia                  |
| ------------------------------------------------- | -------------------------------------- | --------------------------- |
| Blacklist por substring eludible                  | Capa 1 (parser sintáctico + esquemas) | OWASP Top 10 #3 (Injection) |
| Comandos diagnósticos sin HITL                   | Capa 2 (HITL obligatorio)              | NIST SP 800-53 AC-3         |
| PI-5 no detecta comandos ejecutados que no envió | Capa 3 (round-trip)                    | Defense-in-depth            |
| Sin trazabilidad ordenada                         | Capa 4 (audit_log inmutable)           | ISO 27001 A.12.4, NIST AU-2 |

### Archivos a modificar (~230 LOC, todo en PI-5)

- `PI-5/src/tools/policy_engine.py` — nuevo (~150)
- [iot_tools.py:34-80](../PI-5/src/tools/iot_tools.py#L34) — `execute_diagnostic_command` llama al motor (~20)
- [iot_tools.py:82-138](../PI-5/src/tools/iot_tools.py#L82) — `request_mitigation_approval` añade dispatch al cache (~5)
- [dashboard_soc.py:511-572](../PI-5/src/dashboard_soc.py#L511) — `approve_mitigation` revalida tras edición humana (~10)
- [dashboard_soc.py:574-658](../PI-5/src/dashboard_soc.py#L574) — `revert_action` pasa por el motor (~5)
- `PI-5/src/agents/feedback_agent/feedback_agent.py` — `verify_feedback` + crear log `ANOMALY` (~15)
- [database.py](../PI-5/src/database.py) — crear `audit_log` + trigger anti-modificación (~25)

---

## 2. Saneamiento del flujo MQTT del coordinador

**Estado:** ✅ RESUELTO el 2026-05-15 — sustituido por la migración completa de esquema de topics descrita en [funcionamiento_mqtt.md](funcionamiento_mqtt.md).

### Bug original (registro histórico)

El coordinador tenía dos defectos que se manifestaban juntos:

1. **Topic obsoleto en la suscripción de feedback**: una constante `TOPIC_SUBSCRIBE_COMMANDS_OUT = "comandos/+/out"` apuntaba a un namespace que ya nadie usaba. Nada llegaba por ahí.
2. **Clasificador frágil por substring**: `queue_type = "feedback" if "comandos" in topic and "out" in topic else "triage"`. Como los feedbacks reales viajaban por `seguridad/acciones/<device>/out`, el filtro caía al `else` y todos los feedbacks acababan en la cola del triage_agent.

**Consecuencia observable:** el feedback_agent nunca se ejecutaba. Los feedbacks de PI-4 se procesaban como si fueran logs de ataque entrantes, generando alertas espurias tipo `DESTRUCTIVE-COMMAND-INJECTION` desde `127.0.0.1`.

### Qué se aplicó en su lugar

En vez de un parche mínimo sobre el esquema antiguo, se hizo una migración completa al nuevo esquema `seguridad/<device>/<categoría>`. Detalles completos en [funcionamiento_mqtt.md](funcionamiento_mqtt.md). Resumen:

- **Config** ([config.yml](../PI-5/config.yml)): cuatro claves nuevas (`topic_subscribe_telemetria`, `topic_subscribe_eventos`, `topic_subscribe_respuestas`, `topic_publish_comando`).
- **Coordinador** ([main_coordinator.py:30-32](../PI-5/src/main_coordinator.py#L30)): tres suscripciones estrechas en vez de `seguridad/#` + el topic obsoleto.
- **Clasificador** ([main_coordinator.py:224](../PI-5/src/main_coordinator.py#L224)): `queue_type = "feedback" if topic.endswith("/respuesta") else "triage"`.
- **iot_tools** ([iot_tools.py:34-80](../PI-5/src/tools/iot_tools.py#L34)) y **dashboard** ([dashboard_soc.py:511, 574](../PI-5/src/dashboard_soc.py#L511)): publican en `seguridad/{device}/comando` (plantilla).

### Pendiente menor heredado

Detectado al aplicar la migración pero **no implementado** porque vive en PI-4 (territorio del compañero): en [agente_monitor3.py:194](../PI-4/Agente%20de%20monitorizacion/agente_monitor3.py#L194) la rama `else` de `on_accion` publica confirmaciones `ACCION_RECIBIDA` en el topic legacy `seguridad/cliente1/web/eventos` cuando el texto de la acción contiene `"web"`. El coordinador no escucha ese topic → los mensajes caen al vacío. Fix propuesto (no aplicado): colapsar el if/elif/else en una sola línea que publique siempre a `TOPIC_RESPUESTAS`, ya que semánticamente una confirmación de recepción es una respuesta al SOC. Pasar al compañero para aplicar.

---

## Notas para retomar

- El flujo MQTT (sección 2) **ya está saneado**: las capas 3 y 4 del futuro Policy Engine (cache round-trip + audit_log) ya tienen los topics correctos donde anclarse (`seguridad/+/respuesta` para feedbacks). Ver [funcionamiento_mqtt.md](funcionamiento_mqtt.md).
- Si en el futuro se gana cooperación de PI-4, sustituir la Capa 3 del Policy Engine por firma HMAC + nonce/timestamp (propuesta original previa a centralizar todo en PI-5).
- Pendiente menor en PI-4 ([agente_monitor3.py:194](../PI-4/Agente%20de%20monitorizacion/agente_monitor3.py#L194)) descrito al final de la sección 2 — coordinar con el compañero.
