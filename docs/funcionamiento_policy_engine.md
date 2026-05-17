# Funcionamiento del Policy Engine — Sentinel-IT

Documento de referencia técnica sobre cómo el coordinador (PI-5) clasifica y autoriza los comandos que viajan al sensor (PI-4). Refleja el estado a partir del 2026-05-16.

> Sustituye a la sección 1 del documento [futuras_mejoras.md](futuras_mejoras.md), que queda marcada como **RESUELTA** y solo deja constancia histórica de la motivación.

## Por qué existe

La versión anterior tenía dos defectos en la validación de comandos:

1. **Blacklist por substring** en [iot_tools.py:49](../PI-5/src/tools/iot_tools.py#L49) (`'rm '`, `'kill '`, `'chmod'`...). Era eludible (`php -r 'system("rm -rf /tmp")'` no contiene `rm ` exacto) y a la vez demasiado restrictiva: bloqueaba lecturas inocuas como `sudo cat /var/log/auth.log`.
2. **No había trazabilidad ordenada** de quién había propuesto qué, quién lo había aprobado y qué había pasado al final.

El Policy Engine sustituye la blacklist por **clasificación de riesgo en cuatro niveles** y añade dos capas de defensa adicional: verificación de round-trip y log de auditoría inmutable.

## Niveles de riesgo

Cada comando se clasifica con [`policy_engine.classify`](../PI-5/src/tools/policy_engine.py) en uno de cuatro niveles:

| Nivel        | Significado                                                            | Flujo                                                          |
| ------------ | ---------------------------------------------------------------------- | -------------------------------------------------------------- |
| `SAFE_READ`  | Lectura/diagnóstico sin efectos laterales (incluye `sudo cat`, etc.)   | **Ejecución directa**, sin intervención humana                 |
| `LOW`        | Escritura acotada y reversible (`iptables -A` contra una IP, cierre de sesión PHP, verbos desconocidos) | **Auto-ejecución** + opción de revertir desde el dashboard |
| `HIGH`       | Escritura amplia o sobre servicios críticos (`systemctl restart`, `kill`, `sed -i`, `find -delete`) | Revisión humana — banner amarillo en el modal     |
| `CRITICAL`   | Acción destructiva o no reversible (`rm`, `dd`, `mkfs`, `shutdown`, `php -r`, `bash -c`...) | Revisión humana — banner rojo + **checkbox obligatorio** "entiendo el riesgo" |

> **Diseño deliberado**: solo HIGH y CRITICAL interrumpen al operador. LOW se ejecuta inmediatamente porque sus efectos son acotados y existe el botón **REVERTIR** en el dashboard si hace falta deshacerlo. Esto evita que la interfaz pida confirmación constantemente para acciones de mitigación rutinarias (bloqueo de IPs, cierres de sesión).

### Ejemplos por nivel

```text
SAFE_READ:
    cat /var/log/auth.log
    sudo cat /var/log/auth.log               # sudo de un verbo de lectura sigue siendo SAFE_READ
    sudo journalctl -u sshd
    sudo iptables -L INPUT
    ps aux | grep sshd                       # pipe entre dos lecturas no escala

LOW:
    sudo iptables -A INPUT -s 1.2.3.4 -j DROP
    php /opt/sentinel/cerrar_sesion.php --cerrar-nombre dani
    herramienta-desconocida --verbose        # comando no listado: cae a LOW, no se deniega

HIGH:
    sudo systemctl restart apache2
    kill 1234
    sed -i 's/old/new/' /etc/config.conf
    find / -name '*.log' -delete

CRITICAL:
    rm -rf /tmp
    dd if=/dev/zero of=/dev/sda
    shutdown -h now
    sudo iptables -F                         # flush global sin cadena: irreversible
    php -r 'system("rm -rf /tmp")'           # intérprete + verbo destructivo embebido
    ls /tmp; rm /tmp/foo                     # encadenamiento con verbo destructivo
```

### Señales que escalan el nivel

El clasificador parte del verbo principal y aplica reglas aditivas:

1. **Verbo de lectura conocido** → punto de partida `SAFE_READ` (lista en [`_READ_VERBS`](../PI-5/src/tools/policy_engine.py#L91)).
2. **`sudo` + verbo de lectura** → sigue `SAFE_READ`. Respuesta a la objeción de que `sudo cat` se bloqueaba.
3. **`iptables/ip6tables/ufw`** → caso especial ([`_classify_bounded_write`](../PI-5/src/tools/policy_engine.py#L195)):
   - `-L`, `-S`, `--list`, `--check` → `SAFE_READ`.
   - `-A`/`-I`/`-D` contra una IP concreta → `LOW`.
   - `-F` con cadena específica (`INPUT/FORWARD/OUTPUT`) → `HIGH`.
   - `-F` sin cadena → `CRITICAL`.
4. **Verbo destructivo** (`rm`, `dd`, `mkfs`, `shutdown`, `reboot`, `userdel`...) → `CRITICAL`.
5. **Verbo de escritura amplia** (`systemctl`, `kill`, `mount`, `chmod`, `chown`...) → `HIGH`.
6. **Intérprete** (`bash`, `php`, `python`, `perl`, `eval`...) → `LOW` de base.
7. **Verbo desconocido** → `LOW`. **Nunca DENY automático.** Esto es deliberado.

Modificadores que suben el nivel:

- **Intérprete con flag de ejecución en línea** (`bash -c`, `php -r`, `python -c`...) → +2 niveles. Esto cierra el agujero `php -r 'system("rm -rf /tmp")'`.
- **Metacaracteres de shell fuera de comillas** (`;`, `&&`, `||`, backticks, `$(...)`, redirección `>` a fuera de `/tmp` y `/var/log`) → +1.
- **Wildcards en paths sensibles** (`/etc/*`, `/boot/*`, `/sys/*`, `/proc/*`, `/dev/sd*`) → +1.
- **`find -delete` o `find -exec`** → al menos `HIGH`.
- **`sed -i`** → al menos `HIGH` (mutación in-place).
- **Verbo destructivo en cualquier posición del comando** (cubre `ls /tmp; rm foo` y similares) → fuerza `CRITICAL`.

Si el parser falla (comillas mal cerradas, escapes raros) → `HIGH` por defecto. Nunca se deniega automáticamente; siempre llega al humano.

## Flujo completo

```text
                     ┌─────────────────────────────────────┐
                     │  Triage agent  /  Feedback agent    │
                     │  (LlmAgent ADK)                     │
                     └──────────────┬──────────────────────┘
                                    │
              ┌─────────────────────┴─────────────────────┐
              │                                           │
              ▼ execute_diagnostic_command                ▼ request_mitigation_approval
        ┌─────────────────┐                       ┌─────────────────────────┐
        │ SAFE_READ →     │                       │ policy_engine.classify  │
        │   publish MQTT  │                       └──────────┬──────────────┘
        │ otro nivel →    │                                  │
        │   re-encauza a  │              ┌───────────────────┴──────────────────┐
        │ request_…       │              │                                      │
        └────────┬────────┘              ▼ SAFE_READ / LOW                      ▼ HIGH / CRITICAL
                 │                ┌─────────────────────┐              ┌─────────────────────┐
                 │                │ Auto-ejecución      │              │ Cuarentena PENDING  │
                 │                │  - publish MQTT     │              │  - status='PENDING' │
                 │                │  - record_dispatch  │              │  - rationale [NIVEL]│
                 │                │  - status='APPROVED'│              │  - audit(QUARANTINE)│
                 │                │  - audit(AUTO_DISP) │              └──────────┬──────────┘
                 │                └──────────┬──────────┘                         │
                 │                           │                                    ▼
                 │                           │                       ┌─────────────────────────┐
                 │                           │                       │ Dashboard: modal sobrio │
                 │                           │                       │  - banner por nivel     │
                 │                           │                       │  - editar comando       │
                 │                           │                       │  - checkbox si CRITICAL │
                 │                           │                       │  - aprueba o rechaza    │
                 │                           │                       └──────────┬──────────────┘
                 │                           │                                  │
                 │                           │                                  ▼
                 │                           │                       ┌─────────────────────────┐
                 │                           │                       │ /api/mitigate/approve   │
                 │                           │                       │  - RE-clasifica final   │
                 │                           │                       │  - si CRITICAL exige    │
                 │                           │                       │    confirm_critical     │
                 │                           │                       │  - publish + audit      │
                 │                           │                       └──────────┬──────────────┘
                 │                           │                                  │
                 ▼                           ▼                                  ▼
        ┌────────────────────────────────────────────────────────────────────────────────┐
        │  AWS IoT Core → seguridad/<device>/comando                                     │
        └─────────────────────────────────────┬──────────────────────────────────────────┘
                                              ▼
                                       PI-4 ejecuta
                                              │
                                              ▼
                            seguridad/<device>/respuesta
                                              │
                                              ▼
                       ┌────────────────────────────────────────┐
                       │ main_coordinator.process_event         │
                       │  - policy_engine.verify_feedback(cmd)  │
                       │     · MATCH  → feedback_queue          │
                       │     · ANOMALY → register_alert         │
                       │                  (INTRUSION-COMMAND-   │
                       │                   INJECTION, Critica)  │
                       │                + audit(ANOMALY)        │
                       │                + NO encolar feedback   │
                       └────────────────────────────────────────┘
```

Tras una auto-ejecución LOW, la fila queda con `status='APPROVED'` y `pending_command` rellenado, así que el dashboard ofrece automáticamente el botón **REVERTIR** sobre ella (mismo flujo que para una mitigación aprobada manualmente).

### Re-validación tras edición humana

Cuando el humano edita el `final_command` en el modal HITL y pulsa "Aprobar", el endpoint [`approve_mitigation`](../PI-5/src/dashboard_soc.py#L509) vuelve a llamar a `policy_engine.classify` sobre el comando *editado*. Si el nivel resultante es `CRITICAL` y el JSON no incluye `confirm_critical: true`, el endpoint devuelve `400` con `status="needs_confirmation"`. El front muestra el checkbox rojo y solo cuando el humano lo marca conscientemente se reenvía la petición.

Es una doble red:
- Front: bloquea el click si el banner ya marca CRITICAL y el checkbox no está marcado.
- Back: re-valida porque un cliente malicioso podría saltarse la validación del front.

## Verificación round-trip

`policy_engine.record_dispatch(cmd, device, log_id)` guarda en memoria cada comando publicado a MQTT (TTL 5 minutos). Cuando llega un feedback en `seguridad/<device>/respuesta`, [main_coordinator.process_event](../PI-5/src/main_coordinator.py#L204) llama a `policy_engine.verify_feedback(executed_cmd, device)`:

- **MATCH** → el feedback se encola normalmente al `feedback_agent`.
- **ANOMALY** → significa que PI-4 reporta haber ejecutado un comando que el coordinador nunca emitió. Posibles causas:
  - Credenciales (cert/key) filtradas y un atacante publicó directo a `seguridad/<device>/comando`.
  - Suplantación del cliente Pi5-dani.
  - PI-4 está manipulada y miente sobre lo ejecutado.

  En cualquier caso, el coordinador:
  1. Crea una alerta `INTRUSION-COMMAND-INJECTION` con gravedad `Critica`.
  2. Escribe en `audit_log` un evento `ANOMALY`.
  3. **No** encola el feedback al `feedback_agent` (evita contaminar el estado de las mitigaciones legítimas).

### Limitación honesta

Sin firma criptográfica (HMAC + nonce/timestamp), la verificación es **a posteriori**. Detecta la anomalía solo cuando PI-4 *reporta* el comando ejecutado. La defensa real preventiva sigue siendo la Policy de AWS IoT: solo tres `client_id` autorizados pueden conectar (`Pi5-dani`, `Pi4-felix`, `Dashboard-SOC-Pi5`). El round-trip es una capa adicional de **defense in depth**, no una solución completa.

## Audit log inmutable

Tabla [`audit_log`](../PI-5/src/database.py) creada en `database.py`. Columnas:

| Columna           | Contenido                                                       |
| ----------------- | --------------------------------------------------------------- |
| `id`              | autoincrement                                                   |
| `ts`              | timestamp UTC automático                                        |
| `event_type`      | `DISPATCH` / `AUTO_DISPATCH` / `QUARANTINE` / `APPROVE` / `REJECT` / `REJECT_CRITICAL_UNCONFIRMED` / `REVERT` / `ANOMALY` |
| `device`          | dispositivo destino                                             |
| `command`         | texto literal del comando                                       |
| `classification`  | `SAFE_READ` / `LOW` / `HIGH` / `CRITICAL`                       |
| `decision_reason` | razón humana + razones técnicas del clasificador                |
| `related_log_id`  | FK opcional a `logs.id`                                         |

**Triggers anti-modificación:**

```sql
CREATE TRIGGER audit_log_no_update BEFORE UPDATE ON audit_log
BEGIN SELECT RAISE(ABORT, 'audit_log is append-only'); END;

CREATE TRIGGER audit_log_no_delete BEFORE DELETE ON audit_log
BEGIN SELECT RAISE(ABORT, 'audit_log is append-only'); END;
```

Cualquier intento de `UPDATE` o `DELETE` aborta con `IntegrityError`. Ni siquiera la propia aplicación puede modificar el registro a posteriori — esto es lo que da garantía forense.

## Mapeo con estándares (memoria del TFG)

| Hueco que se cierra                                            | Capa que lo cierra                          | Referencia normativa                            |
| -------------------------------------------------------------- | ------------------------------------------- | ----------------------------------------------- |
| Blacklist por substring eludible                               | Clasificación con parser shlex + escalado   | OWASP Top 10 — A03:2021 Injection               |
| Comandos diagnósticos pasaban por blacklist                    | Nivel `SAFE_READ` con `sudo cat` permitido  | NIST SP 800-53 — AC-3 Access Enforcement        |
| Comandos destructivos no exigían confirmación explícita        | Re-validación + `confirm_critical=true`     | NIST SP 800-53 — AC-3, AC-6 Least Privilege     |
| Coordinador no detectaba comandos ejecutados que no emitió     | `verify_feedback` + ANOMALY                 | NIST SP 800-53 — SI-4 Information Monitoring    |
| Sin trazabilidad ordenada de decisiones                        | `audit_log` append-only                     | NIST SP 800-53 — AU-2; ISO 27001 A.12.4 Logging |

## Cómo extender el motor

- **Añadir un verbo de lectura nuevo** (ej. `dmesg`): añadirlo a `_READ_VERBS` en [policy_engine.py](../PI-5/src/tools/policy_engine.py).
- **Añadir un verbo destructivo nuevo**: añadirlo a `_DESTRUCTIVE_VERBS`.
- **Marcar un path adicional como sensible**: añadirlo a `_SENSITIVE_WILDCARD_PATHS`.
- **Cambiar el TTL del cache de round-trip**: editar `_DISPATCH_TTL_SECONDS` (por defecto 300 s).

Los tests unitarios viven en [PI-5/tests/test_policy_engine.py](../PI-5/tests/test_policy_engine.py) y cubren los cuatro niveles, las señales que escalan y la inmutabilidad del `audit_log`. Ejecutar con:

```bash
cd PI-5
python -m unittest tests.test_policy_engine -v
```

## Archivos involucrados

| Archivo                                                                          | Rol                                                                   |
| -------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| [PI-5/src/tools/policy_engine.py](../PI-5/src/tools/policy_engine.py)            | Motor (clasificación, decisión, cache round-trip, audit)              |
| [PI-5/src/tools/iot_tools.py](../PI-5/src/tools/iot_tools.py)                    | `execute_diagnostic_command` y `request_mitigation_approval`: invocan el motor |
| [PI-5/src/dashboard_soc.py](../PI-5/src/dashboard_soc.py)                        | `approve_mitigation` re-clasifica el comando editado; `revert_action` audita |
| [PI-5/src/main_coordinator.py](../PI-5/src/main_coordinator.py)                  | `process_event` hace round-trip verification antes de encolar feedbacks |
| [PI-5/src/agents/triage_agent/triage_agent.py](../PI-5/src/agents/triage_agent/triage_agent.py)       | Prompt actualizado: el agente sabe que el motor clasifica y reencauza |
| [PI-5/src/agents/feedback_agent/feedback_agent.py](../PI-5/src/agents/feedback_agent/feedback_agent.py) | Prompt actualizado: feedbacks que llegan ya pasaron round-trip       |
| [PI-5/src/database.py](../PI-5/src/database.py)                                  | Crea la tabla `audit_log` y sus triggers anti-modificación            |
| [PI-5/src/templates/index.html](../PI-5/src/templates/index.html)                | Modal HITL con banner de color + checkbox CRITICAL                    |
| [PI-5/tests/test_policy_engine.py](../PI-5/tests/test_policy_engine.py)          | 30 tests unitarios                                                    |
