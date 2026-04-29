# Análisis Profundo del TFG: SOC Autónomo Distribuido

> **Generado:** 15 de Marzo de 2026

Este documento detalla el funcionamiento técnico del Trabajo de Fin de Grado (TFG), analizando la arquitectura, la lógica de los nodos y el sistema de respuesta ante incidentes.

## 1. Arquitectura del Sistema

El sistema se basa en un paradigma de **Seguridad Perimetral Distribuida** utilizando dos nodos Raspberry Pi comunicados de forma segura a través de **AWS IoT Core**.

```
Casa 1 (Félix)                AWS Cloud              Casa 2 (Dani - TU PI)
─────────────────             ──────────             ──────────────────────────────────
 /var/log/auth.log  →  Pi4  ──MQTT──►  IoT Core ──MQTT──►  Pi5 → Agente ADK (Gemini)
                                                                     ↓          ↓
                                                             SQLite DB    Dashboard Flask
                            ←──MQTT──  IoT Core ◄──MQTT──  Pi5 ← [bloquear_ip / cmd]
                       Pi4 ← iptables -A ...
```

---

## 2. Análisis del Nodo "Sensor" (Pi 4 - Félix, Casa del Compañero)

Este nodo actúa como la "primera línea de defensa". Su función es puramente reactiva y de monitorización.

### Componentes Clave (`pi4-felix/`)
| Archivo | Función |
|---|---|
| `agente_monitor.py` | Monitorización de `/var/log/auth.log` en tiempo real (`tail -F`) |
| `aws_connector.py` | Wrapper de conexión MQTT a AWS IoT Core con TLS |
| `config.yml` | Configuración: endpoint, certificados, topics MQTT |
| `soc-sensor.service` | Servicio systemd para arranque automático |

### Flujo de datos
1. **Detección**: Filtra líneas con `sshd` + `Failed password` o `Invalid user`.
2. **Envío**: Publica en JSON al topic `seguridad/logs/Pi4-Felix/ssh`.
3. **Recepción de órdenes**: Suscrito a `seguridad/acciones/Pi4-Felix`.
4. **Blacklist de seguridad**: Filtra comandos peligrosos (`rm`, `reboot`, `shutdown`, etc.) antes de ejecutarlos.
5. **Mitigación**: Ejecuta `iptables -A INPUT -s <IP> -j DROP` para bloquear atacantes.

> **⚠️ Nota**: En el código actual (`agente_monitor.py`, línea 82), la línea de baneo real con `iptables` está **comentada** como simulación. Para producción, debe descomentarse.

---

## 3. Análisis del Nodo "Coordinador" (Pi 5 - Dani, **Tu Casa**)

Es el "cerebro" del sistema. Aquí reside la inteligencia artificial, la base de datos y el dashboard.

### Componentes Clave (`pi5-dani/`)
| Archivo/Directorio | Función |
|---|---|
| `main_coordinator.py` | Orquestador principal: recibe logs, invoca al agente ADK |
| `agents/soc_agent/soc_agent.py` | Definición del `LlmAgent` con Gemini 2.5 Flash |
| `tools/db_tools.py` | Herramienta ADK: `registrar_alerta()` en SQLite |
| `tools/iot_tools.py` | Herramienta ADK: `bloquear_ip()` y `ejecutar_comando_remoto()` |
| `dashboard_soc.py` | Dashboard Flask con KPIs y botón de reversión (Flask) |
| `aws_connector.py` | Wrapper MQTT reutilizable |
| `soc_data.db` | Base de datos SQLite de incidentes |
| `soc-coordinator.service` | Servicio systemd para el coordinador |
| `soc-dashboard.service` | Servicio systemd para el dashboard web |

### Lógica del Agente SOC (Google ADK + Gemini 2.5 Flash)

El agente sigue un sistema de **triage de 3 niveles**:

| Nivel | Condición | Herramientas usadas |
|---|---|---|
| 🟢 Benigno | Actividad normal, cronjobs | Ninguna (respuesta de texto) |
| 🟡 Sospecha | Comportamiento inusual | `registrar_alerta`, opcionalmente `ejecutar_comando_remoto` |
| 🔴 Ataque Activo | Fuerza bruta, usuarios prohibidos | `registrar_alerta` (Crítica) + `bloquear_ip` |

### Mecanismo "Human-in-the-Loop"
El Dashboard incluye un botón de **reversión** (`POST /revert/<log_id>`) que:
1. Consulta la IP bloqueada en SQLite.
2. Envía por MQTT el comando `iptables -D INPUT -s <IP> -j DROP` al Pi 4.
3. Actualiza el registro en la DB a `accion_tomada = "... [REVERTIDO]"`.

---

## 4. Seguridad y Persistencia

### Base de Datos SQLite (`soc_data.db`)
- **WAL Mode** (`PRAGMA journal_mode=WAL`): Permite lecturas concurrentes entre el Dashboard y el Coordinador sin bloqueos.
- **Sincronización normal** para mayor rendimiento.
- **Rotación automática** (implementada el 2026-03-15): Los registros con más de 30 días y ya resueltos se archivan automáticamente.

### AWS IoT Policies (Mínimo Privilegio)
- **Pi 4**: Puede publicar en `seguridad/logs/+/+` y suscribirse a `seguridad/acciones/Pi4-Felix`.
- **Pi 5**: Puede suscribirse a `seguridad/logs/+/+` y publicar en `seguridad/acciones/+`.
- Comunicación cifrada con **TLS 1.2+** (certificados X.509 de AWS IoT).

### Endpoint AWS IoT Core
```
aj4wsdnimoej8-ats.iot.eu-north-1.amazonaws.com
Región: eu-north-1 (Estocolmo)
Account ID: 582997418897
```

---

## 5. Mejoras Implementadas (2026-03-15)

### Rotación de Logs de Base de Datos
Se añadió la función `rotar_logs_antiguos()` en `tools/db_tools.py` y una nueva sección `retention` en `config.yml`:

- **Retención máxima**: 30 días (configurable en `config.yml`).
- **Criterio**: Solo se eliminan registros con acción "Solo Registro" (no bloqueos activos).
- **Invocación automática**: Se llama desde `registrar_alerta()` antes de insertar nuevos datos.
- **Log**: Informa cuántos registros fueron purgados en cada limpieza.

```yaml
# config.yml - nueva sección añadida
retention:
  max_days: 30
  purge_on_insert: true
```

---

## 6. Despliegue y Validación en Producción (2026-03-15)

### 6.1 Transferencia de Certificados

Los certificados AWS IoT se transfirieron desde Windows (`D:\descargas`) a la Pi 5 via `scp`, renombrando los ficheros para que coincidan con `config.yml`:

| Archivo descargado | Nombre en la Pi |
|---|---|
| `08402f70...certificate.crt` | `Pi5-dani.cert.pem` |
| `08402f70...private.pem.key` | `Pi5-dani.private.key` |
| `AmazonRootCA1.pem` | `root-CA.crt` |

### 6.2 Incidencias Resueltas

| # | Incidencia | Causa | Solución |
|---|---|---|---|
| 1 | `AWS_ERROR_MQTT_UNEXPECTED_HANGUP` en el coordinador | Certificado `08402f70...` en estado **Inactive** en AWS Console | Activar el certificado en **IoT Core → Security → Certificates → Activate** |
| 2 | Dashboard MQTT no conecta (`Dashboard-SOC-Pi5`) | `client_id` no estaba en la política de `iot:Connect` | Añadido `client_id/Dashboard-SOC-Pi5` en la política → versión 4 creada |
| 3 | Botón Revertir devuelve error 500 | Query SQL usaba columna `nodo_origen` que no existe; el campo real es `dispositivo` | Corregido en `dashboard_soc.py` línea 118 |

### 6.3 Política AWS IoT Final (versión 4, activa)

Nombre: `Pi5-dani-Policy` — client IDs permitidos para `iot:Connect`:

- `${iot:Connection.Thing.ThingName}` (comodín por ThingName)
- `Pi5-dani` — Coordinador SOC
- `Pi4-felix` — Sensor (Pi 4 del compañero)
- `Dashboard-SOC-Pi5` — Cliente MQTT del Dashboard (añadido hoy)

### 6.4 Prueba de Extremo a Extremo (Validada ✅)

Se validó el flujo completo inyectando un log simulado desde el **AWS IoT MQTT Test Client** al topic `seguridad/logs/Pi4-Felix/ssh`:

```
[21:50:49] [AWS IoT] Recibido Log desde Pi4-Felix-Sensor
[21:50:49] 🧠 [CEREBRO] Entregando log al Agente SOC (ADK)...
[21:50:53] 📥 [AGENTE] registrar_alerta → IP 85.204.15.99 (gravedad: CRÍTICA)
[21:50:53] 🚨 [AGENTE] bloquear_ip → Orden enviada a Pi4-Felix-Sensor
[21:50:59] 🤖 Transacción completada. Respuestas recibidas: 1
```

Resultado en el Dashboard: nuevo registro con gravedad **CRÍTICA**, acción **Bloqueo Activo Emitido**.

Botón Revertir (tras el fix): envía correctamente `sudo iptables -D INPUT -s <IP> -j DROP` al Pi 4 vía MQTT y marca el registro como `[REVERTIDO]` en la base de datos.

### 6.5 Estado Final de Servicios

```
soc-coordinator.service   → active (running) — Pi5-dani conectado a AWS IoT
soc-dashboard.service     → active (running) — http://192.168.1.170:5000
                                                Dashboard-SOC-Pi5 conectado a AWS IoT
```
