---
title: "Changelog — Sentinel-IT"
author: "Daniel Alarcon"
date: "2026-05-19"
tags: ["changelog", "releases", "history"]
---

# Changelog

Registro de todos los cambios significativos del proyecto. Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

---

## [2026-05-19] — Firma Ed25519, Reconexión MQTT, Rediseño Dashboard

Jornada intensiva de desarrollo: **4 commits en `main`**, más la rama `feature/policy-engine`. Resumen por área funcional.

### ✨ Añadido

#### Firma criptográfica Ed25519 (`97ba24b`)
- **Módulo `PI-5/src/tools/signing.py`**: firma de comandos PI-5 → PI-4 con campos `iat`, `exp`, `nonce` y `sig` (base64 Ed25519 sobre JSON canónico).
- **Script `scripts/generate_signing_keys.py`**: genera par de claves Ed25519 (`.key` privada en PI-5, `.pub` pública en PI-4).
- **Integración en `main_coordinator.py`**: todo payload publicado a `seguridad/{device}/comando` se firma antes del envío.
- **Integración en `dashboard_soc.py`**: los endpoints `/api/mitigate/approve` y `/revert/<id>` firman el payload antes del publish MQTT.
- **Sección `signing` en `config.yml`**: paths de claves y TTL configurable.
- **Tests**: 7 tests de firma + 8 tests del normalizador de feedback — todos verdes.

#### Normalización del feedback del sensor (`97ba24b`)
- `feedback_agent.py` ahora normaliza los tres shapes posibles de respuesta de PI-4 (v3, rejected_signature, legacy plano) a un dict canónico de 5 campos (`sensor`, `command`, `status`, `output`, `exitcode`).

#### Catálogo de recomendaciones ampliado (`97ba24b`)
- `recommendations.json`: nuevas entradas para bloqueo/desbloqueo de IP en HTTP+8080 (proxy + servidor real) y restauración vía restic.

#### Detección de conexiones MQTT zombie (`c00d61a`)
- **`AWSMqttClient.is_alive()`**: comprueba el handle nativo `_binding` del SDK awscrt para detectar conexiones donde el objeto Python existe pero el socket TCP/TLS está muerto.
- **`AWSMqttClient.disconnect()`**: desconexión limpia con cleanup del handle para permitir reconexión.
- **Mensajes de error descriptivos en `publish()`**: si `publish_future.result()` falla con excepción vacía, se reemplaza por `"PUBACK timeout or connection lost"`.

### 🐛 Corregido

#### DNS crash-loop en Docker (`3b5eb3b`)
- **Problema**: el contenedor Docker arrancaba antes de que el resolver DNS del host estuviera listo, provocando `AWS_IO_DNS_QUERY_FAILED` en bucle infinito.
- **Causa raíz**: `main_coordinator.py` intentaba una única conexión MQTT al arrancar — si el DNS fallaba, el proceso moría y Docker lo reiniciaba en bucle.
- **Solución**: 
  - `main_coordinator.py`: retry con backoff exponencial (6 intentos, delay inicial 2s, max 8s).
  - `docker-compose.yml`: configuración DNS explícita (`dns: [8.8.8.8, 1.1.1.1]`) como fallback.
  - `soc_manager.sh`: verificación de conectividad DNS antes de `docker compose up`.

#### Conexión MQTT zombie en dashboard → 502 en HITL (`c00d61a`)
- **Problema**: `POST /api/mitigate/approve` devolvía `502 Bad Gateway` con el mensaje `[ERROR] Publish HITL fallo, no se actualiza DB:` (error vacío).
- **Causa raíz**: la conexión MQTT del dashboard (`Dashboard-SOC-Pi5`) moría tras un corte transitorio de red/DNS. El objeto `self.connection` de Python seguía no siendo `None`, pero el socket TLS subyacente estaba muerto. El check `getattr(mqtt_client, 'connection', None) is not None` en `get_mqtt_client()` devolvía `True` → se intentaba publicar en un cliente muerto → `publish_future.result()` fallaba con excepción vacía → 502.
- **Solución**: 
  - `AWSMqttClient.is_alive()`: health check real a nivel de SDK.
  - `get_mqtt_client()`: detecta zombie, llama `disconnect()`, reconecta con backoff.
  - `publish()`: pre-check con `is_alive()` + wrapper de excepciones con mensajes descriptivos.
  - Todos los endpoints del dashboard migrados de `getattr()` a `is_alive()`.

#### Arreglos varios de Docker (`923c33d`)
- `docker-compose.yml`: ajustes de volúmenes y configuración.
- `dashboard_soc.py`: correcciones en la serialización de logs y manejo de columnas faltantes.
- `agente_monitor3.py` (PI-4): mejoras en el agente de monitorización.

### 🔧 Cambiado

#### Eliminación del sistema INTRUSION-COMMAND-INJECTION (`97ba24b`)
- La detección reactiva de inyección de comandos (caché de despachos `record_dispatch` / `match_feedback` en `policy_engine.py`) fue reemplazada por la firma Ed25519 proactiva. La garantía de autenticidad pasa de ser *a posteriori* (detectar después) a ser *a priori* (verificar antes de ejecutar).

### 📁 Archivos modificados hoy

| Archivo | Tipo de cambio |
|---------|---------------|
| `PI-5/src/aws_connector.py` | Añadidos `is_alive()`, `disconnect()`, mejora en `publish()` |
| `PI-5/src/dashboard_soc.py` | Reconexión MQTT, firma de payloads, checks `is_alive()` |
| `PI-5/src/main_coordinator.py` | Retry DNS, firma de comandos, normalización feedback |
| `PI-5/src/tools/signing.py` | **Nuevo** — módulo de firma Ed25519 |
| `PI-5/src/tools/policy_engine.py` | Eliminada caché de despachos, simplificación |
| `PI-5/src/agents/feedback_agent/feedback_agent.py` | Normalización de feedback |
| `PI-5/src/agents/triage_agent/triage_agent.py` | Integración con firma |
| `PI-5/src/recommendations.json` | Nuevas recomendaciones de mitigación |
| `PI-5/config.yml` | Sección `signing` |
| `PI-5/docker-compose.yml` | DNS explícito, ajustes de volúmenes |
| `PI-5/requirements.txt` | Dependencia `cryptography` |
| `PI-4/Agente de monitorizacion/agente_monitor3.py` | Mejoras en monitorización |
| `scripts/generate_signing_keys.py` | **Nuevo** — generador de claves |
| `PI-5/tests/test_signing.py` | **Nuevo** — tests de firma |
| `PI-5/tests/test_feedback_normalizer.py` | **Nuevo** — tests de normalización |
| `docs/Configuration_and_Deployment.md` | Sección 8: firma Ed25519 |

---

## Convenciones

- Cada entrada incluye el hash corto del commit entre paréntesis.
- Los bugs documentan: **Problema** (síntoma visible), **Causa raíz** (por qué ocurría) y **Solución** (qué se hizo).
- Los archivos **nuevos** se marcan explícitamente.
