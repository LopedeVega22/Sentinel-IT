---
title: "Esquema de Base de Datos - Sentinel-IT (PI-5)"
author: "Daniel Alarcon"
date: "2026-05-17"
tags: ["sqlite", "wal", "audit-log", "schema", "retention"]
---

# Esquema de Base de Datos

## 1. Propósito

Este documento describe la **persistencia** del coordinador SOC: las dos tablas SQLite (`logs` y `audit_log`), el modo WAL, los triggers anti-modificación del log de auditoría, la política de retención y los caminos de acceso desde cada componente.

No describe la lógica de negocio que escribe en estas tablas — eso vive en [funcionamiento_policy_engine.md](funcionamiento_policy_engine.md) (audit) y en los tools `register_alert` / `update_alert_status` (logs).

## 2. Stack

| Item | Valor |
|------|-------|
| Motor | SQLite 3 (builtin de Python `sqlite3`) |
| Modo journal | **WAL** — `PRAGMA journal_mode=WAL` en todas las conexiones |
| Sincronía | `PRAGMA synchronous=NORMAL` en las escrituras del coordinador (más rápido, suficiente con WAL) |
| Ruta | `PI-5/data/soc_data.db` (configurable vía `config.yml → database.db_path`) |
| Bootstrap | `PI-5/src/database.py` — se ejecuta una vez al construir la imagen / al arrancar |
| Persistencia | Volume Docker nombrado `soc_pi5_database_persistent` (sobrevive a rebuild) |

### 2.1 Por qué WAL

El coordinator y el dashboard acceden a la misma DB en paralelo desde threads independientes:

- Thread MQTT del coordinator → `INSERT logs` / `UPDATE logs` / `INSERT audit_log` constantes.
- Thread Flask del dashboard → `SELECT logs` cada 5 s + `UPDATE logs` en HITL/revert.

Sin WAL, las lecturas bloquearían las escrituras y viceversa. WAL deja que lectores y escritores trabajen en paralelo: las escrituras van a un fichero `-wal` separado y los lectores consultan la última imagen consistente. `synchronous=NORMAL` reduce los `fsync()` (asumiendo que un crash entre commits puede perder los últimos KB del WAL, lo cual es aceptable para este caso de uso).

## 3. Tabla `logs`

Contiene cada incidente registrado por los agentes IA. Una fila por amenaza confirmada.

```sql
CREATE TABLE IF NOT EXISTS logs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    dispositivo         TEXT,                    -- e.j. 'Pi4-Felix'
    servicio            TEXT,                    -- e.j. 'SSH', 'HTTP', 'MYSQL', 'PORT-SCAN'
    log_original        TEXT,                    -- raw log capturado por el sensor
    ip_origen           TEXT,                    -- IP del atacante
    nivel_gravedad      TEXT,                    -- 'Baja', 'Media', 'Alta', 'Critica'
    veredicto_ia        TEXT,                    -- chain-of-thought summary del agente
    accion_tomada       TEXT,                    -- 'Solo Registro' | concatenación con tags
    estado_mitigacion   TEXT,                    -- '[EXITO] ...' | '[FALLO] ...'
    status              TEXT DEFAULT 'LOGGED',   -- LOGGED | PENDING | APPROVED | REJECTED | REVERTED
    pending_command     TEXT,                    -- comando bash propuesto / auto-ejecutado
    rationale           TEXT,                    -- '[NIVEL] razón del agente o del motor'
    timestamp           DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 3.1 Ciclo de vida del campo `status`

```
   ┌──────────┐    register_alert    ┌──────────┐
   │   (none) │ ───────────────────► │  LOGGED  │
   └──────────┘                      └────┬─────┘
                                          │
                                          │ request_mitigation_approval
                                          ▼
                              ┌───────────┴──────────┐
                              │                      │
                  LOW/SAFE_READ                  HIGH/CRITICAL
                              │                      │
                              ▼                      ▼
                       ┌──────────┐           ┌──────────┐
                       │ APPROVED │           │ PENDING  │
                       │ (auto)   │           │          │
                       └────┬─────┘           └────┬─────┘
                            │                     │ /api/mitigate/approve
                            │                     ▼
                            │              ┌──────────┐    ┌──────────┐
                            │              │ APPROVED │ ó  │ REJECTED │
                            │              └────┬─────┘    └──────────┘
                            │                   │
                            └─────────┬─────────┘
                                      │ /revert/<id>
                                      ▼
                                ┌──────────┐
                                │ REVERTED │
                                └──────────┘
```

Notas importantes:

- `LOGGED` es el estado inicial tras `register_alert`. Si la amenaza no requería acción, queda así para siempre.
- `PENDING` solo lo escribe `_quarantine_for_hitl()` (HIGH/CRITICAL). El dashboard pinta estas filas con badge amarillo/rojo y botón "Revisar Mitigación".
- `APPROVED` lo escribe **tanto** `_auto_execute_low()` (sin pasar por humano) **como** `approve_mitigation()` (tras HITL). En ambos casos `pending_command` queda relleno, así el botón REVERTIR funciona indistintamente.
- `REJECTED` es terminal: la mitigación no se ejecutó. La fila queda como histórico.
- `REVERTED`: hubo APPROVED previo y el operador deshizo. Si la mitigación inversa falla, eso se refleja en `estado_mitigacion` pero el `status` no vuelve atrás.

### 3.2 Concatenación en `accion_tomada` y `estado_mitigacion`

Estos dos campos son **append-only de facto**. El código no sobrescribe — concatena con `\n`:

```sql
SET accion_tomada = CASE
    WHEN accion_tomada = 'Solo Registro' THEN ?
    ELSE accion_tomada || ?
END
```

Esto permite rastrear la historia operativa de una fila (`Solo Registro` → `Auto-ejecutado [LOW]: iptables -A...` → `[EXITO] OK` → `[REVERTIDO]`) sin tablas adicionales. La auditoría formal vive en `audit_log`, no aquí — este texto es para el operador, no para forense.

### 3.3 Migraciones

`database.py` aplica migraciones de forma idempotente con `ALTER TABLE ADD COLUMN`:

```python
try:
    cursor.execute("ALTER TABLE logs ADD COLUMN status TEXT DEFAULT 'LOGGED'")
    cursor.execute("ALTER TABLE logs ADD COLUMN pending_command TEXT")
    cursor.execute("ALTER TABLE logs ADD COLUMN rationale TEXT")
except sqlite3.OperationalError:
    pass  # Ya existían
```

Cualquier DB creada con el esquema viejo (pre-HITL) se actualiza al arrancar sin perder datos. Si se añaden columnas nuevas, repetir el patrón.

## 4. Tabla `audit_log`

Bitácora forense del Policy Engine. Una fila por **decisión** sobre un comando, no por incidente.

```sql
CREATE TABLE IF NOT EXISTS audit_log (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    ts               DATETIME DEFAULT CURRENT_TIMESTAMP,
    event_type       TEXT,                       -- ver tabla 4.1
    device           TEXT,                       -- e.j. 'Pi4-Felix'
    command          TEXT,                       -- comando bash literal
    classification   TEXT,                       -- 'SAFE_READ' | 'LOW' | 'HIGH' | 'CRITICAL'
    decision_reason  TEXT,                       -- razón humana + reasons técnicas
    related_log_id   INTEGER,                    -- FK opcional a logs.id
    FOREIGN KEY (related_log_id) REFERENCES logs(id)
);
```

### 4.1 Tipos de evento

| `event_type` | Cuándo se escribe | Quién lo escribe |
|--------------|-------------------|------------------|
| `DISPATCH` | Diagnóstico SAFE_READ publicado directamente | `iot_tools.execute_diagnostic_command` |
| `AUTO_DISPATCH` | Mitigación LOW auto-ejecutada | `iot_tools._auto_execute_low` |
| `QUARANTINE` | Mitigación HIGH/CRITICAL puesta en PENDING | `iot_tools._quarantine_for_hitl` |
| `APPROVE` | Humano aprobó una mitigación PENDING | `dashboard_soc.approve_mitigation` |
| `REJECT` | Humano rechazó una mitigación | `dashboard_soc.approve_mitigation` |
| `REJECT_CRITICAL_UNCONFIRMED` | Humano intentó aprobar CRITICAL sin marcar el checkbox | `dashboard_soc.approve_mitigation` |
| `REVERT` | Humano deshizo una mitigación APPROVED | `dashboard_soc.revert_action` |
| `ANOMALY` | Round-trip falló: PI-4 reporta ejecución de un comando que el coordinador no emitió | `main_coordinator.process_event` |

Cualquier dispatch o decisión queda registrada. Si una fila de `audit_log` no tiene contrapartida razonable en el flujo, ha habido un bug — el log es la fuente de verdad.

### 4.2 Triggers anti-modificación

```sql
CREATE TRIGGER IF NOT EXISTS audit_log_no_update
BEFORE UPDATE ON audit_log
BEGIN
    SELECT RAISE(ABORT, 'audit_log is append-only');
END;

CREATE TRIGGER IF NOT EXISTS audit_log_no_delete
BEFORE DELETE ON audit_log
BEGIN
    SELECT RAISE(ABORT, 'audit_log is append-only');
END;
```

Estos triggers se ejecutan **antes** de cualquier UPDATE/DELETE y abortan la transacción con `IntegrityError`. Ni siquiera el propio coordinador, ejecutándose como el usuario que creó la DB, puede modificar registros pasados desde la aplicación. Esta es la garantía forense que mapea con NIST SP 800-53 AU-2 (Audit Events) e ISO 27001 A.12.4 (Logging and Monitoring).

> Para una nuke total, una entidad con acceso al fichero `.db` podría borrar la tabla a nivel de sistema operativo. Eso queda fuera del modelo de amenaza — el modelo asume que el host del coordinador no está comprometido a nivel SO. La defensa contra eso es seguridad del host (SELinux/AppArmor, montaje read-only del binario, etc.), no SQLite.

### 4.3 Cómo consultar el audit log

No hay endpoint del dashboard que lo exponga — el audit_log es para forense, no para la UI operativa. Para consultarlo:

```bash
sqlite3 PI-5/data/soc_data.db "SELECT ts, event_type, device, classification, command FROM audit_log ORDER BY id DESC LIMIT 20;"
```

O desde dentro del contenedor:

```bash
docker exec -it soc-coordinator-pi5 sqlite3 /app/data/soc_data.db \
    "SELECT * FROM audit_log WHERE event_type='ANOMALY';"
```

## 5. Política de retención

`db_tools.rotate_old_logs()` purga filas viejas de baja prioridad. Se ejecuta automáticamente antes de cada INSERT si `retention.purge_on_insert: true` en `config.yml`.

```sql
DELETE FROM logs
WHERE accion_tomada = 'Solo Registro'
  AND timestamp <= datetime('now', '-30 days');
```

Reglas:

- Solo se purgan filas que se quedaron en estado terminal pasivo (`accion_tomada = 'Solo Registro'` → nunca generaron mitigación).
- Filas con cualquier mitigación (`Auto-ejecutado [...]`, `Requiere Revision`, `[EJECUTADO]`, `[REVERTIDO]`...) **nunca** se purgan.
- `audit_log` **no se purga jamás** — los triggers anti-DELETE lo impiden.
- El umbral (30 días por defecto) se controla en `config.yml → retention.max_days`.

Esto evita que la DB crezca indefinidamente con telemetría benigna mientras conserva el rastro completo de cualquier evento que requirió decisión.

## 6. Acceso desde cada componente

| Componente | Operaciones | Notas |
|------------|-------------|-------|
| `main_coordinator.py` | Solo a través de los tools | El coordinador no hace SQL directo, lo delega en `db_tools` / `iot_tools` / `policy_engine` |
| `db_tools.register_alert` | INSERT en `logs` con retry x5 ante `database is locked` | Lleva `rotate_old_logs` integrado si está habilitado |
| `db_tools.update_alert_status` | UPDATE en la fila más reciente del device (`ORDER BY timestamp DESC LIMIT 1`) | Concatenación, nunca sobrescribe |
| `iot_tools._auto_execute_low` | UPDATE con retry x5 (`status='APPROVED'`, `pending_command`, `rationale`) | También llama `policy_engine.audit(AUTO_DISPATCH)` |
| `iot_tools._quarantine_for_hitl` | UPDATE con retry x5 (`status='PENDING'`, ...) | También llama `policy_engine.audit(QUARANTINE)` |
| `policy_engine.audit` | INSERT en `audit_log` | Único punto de escritura del audit log |
| `dashboard_soc._get_connection` | SELECT (read-only) + UPDATE en HITL/revert | Siempre WAL, timeout 10 s |

### 6.1 Reintentos ante `database is locked`

Tanto `register_alert` como las dos vías de `iot_tools` envuelven la UPDATE/INSERT en un bucle con `sleep(2)` y hasta 5 reintentos. Esto absorbe los picos de contención que aparecen cuando llegan muchos eventos a la vez al coordinator mientras el dashboard hace su polling:

```python
for attempt in range(5):
    try:
        conn = sqlite3.connect(DB_PATH, timeout=15.0, check_same_thread=False)
        conn.execute('PRAGMA journal_mode=WAL;')
        # ... operación ...
        break
    except sqlite3.OperationalError as e:
        if "locked" in str(e).lower() or "readonly" in str(e).lower():
            time.sleep(2)
        else:
            break
```

`timeout=15.0` ya da a SQLite 15 s adicionales internamente; el retry externo cubre los casos en los que ni siquiera con WAL el lock cede. En la práctica, con `synchronous=NORMAL` y WAL, los reintentos son raros.

## 7. Backup y restauración

No hay backup automático en el MVP. Para producción, recomendaciones:

- **Snapshot online:** `sqlite3 soc_data.db ".backup '/path/backup.db'"` (consistente con WAL).
- **Volumen Docker:** el volume `soc_pi5_database_persistent` puede copiarse con `docker run --rm -v soc_pi5_database_persistent:/data alpine tar czf /backup.tgz /data`.
- **Solo lectura para forense:** abrir una copia con `sqlite3 -readonly` evita modificaciones accidentales.

`audit_log` se mantiene como append-only incluso en una copia — los triggers viajan con la tabla.

## 8. Esquema completo (referencia rápida)

```sql
-- Tabla 1: incidentes operativos
CREATE TABLE logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dispositivo TEXT,
    servicio TEXT,
    log_original TEXT,
    ip_origen TEXT,
    nivel_gravedad TEXT,
    veredicto_ia TEXT,
    accion_tomada TEXT,
    estado_mitigacion TEXT,
    status TEXT DEFAULT 'LOGGED',
    pending_command TEXT,
    rationale TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabla 2: bitácora forense append-only
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts DATETIME DEFAULT CURRENT_TIMESTAMP,
    event_type TEXT,
    device TEXT,
    command TEXT,
    classification TEXT,
    decision_reason TEXT,
    related_log_id INTEGER,
    FOREIGN KEY (related_log_id) REFERENCES logs(id)
);

CREATE TRIGGER audit_log_no_update BEFORE UPDATE ON audit_log
BEGIN SELECT RAISE(ABORT, 'audit_log is append-only'); END;

CREATE TRIGGER audit_log_no_delete BEFORE DELETE ON audit_log
BEGIN SELECT RAISE(ABORT, 'audit_log is append-only'); END;
```

## 9. Archivos involucrados

```
PI-5/
├── src/
│   ├── database.py              # Bootstrap: CREATE TABLE + CREATE TRIGGER + migraciones
│   ├── tools/
│   │   ├── db_tools.py          # register_alert, update_alert_status, rotate_old_logs
│   │   ├── iot_tools.py         # UPDATE de status / pending_command / rationale
│   │   └── policy_engine.py     # audit() → única función que escribe en audit_log
│   └── dashboard_soc.py         # SELECT del feed + UPDATE de HITL y revert
├── config.yml                   # database.db_path, retention.{max_days, purge_on_insert}
├── data/soc_data.db             # Fichero SQLite (montado en volume Docker)
└── tests/
    └── test_policy_engine.py    # Verifica los triggers de audit_log
```
