---
title: "Documentación Sentinel-IT — Índice"
author: "Daniel Alarcon"
date: "2026-05-19"
tags: ["index", "sentinel-it", "pi5", "documentation"]
---

# Documentación Sentinel-IT

Este directorio contiene la documentación técnica del proyecto **Sentinel-IT**, organizada por fases. Cada documento es **autocontenido** y cubre un área concreta del sistema: arquitectura general, MQTT, agentes IA, motor de políticas, HITL, dashboard, base de datos, testing y despliegue.

> **Alcance actual:** la documentación está centrada en el **coordinador SOC (PI-5)**. La parte del sensor edge (PI-4) está cubierta sólo a nivel de referencia rápida en [PI4_Referencia_Tecnica.md](PI4_Referencia_Tecnica.md) y se completará en una fase posterior.

## Cómo leer esta documentación

Si vienes nuevo al proyecto, lee los documentos en el orden de las fases. Si vienes a un punto concreto, salta directo a la fase relevante — cada doc está pensado para sostenerse por sí mismo.

## Fases

| Fase | Documento | Qué cubre |
|------|-----------|-----------| 
| **1. Visión general** | [System_Overview.md](System_Overview.md) | Topología Edge-Cloud-Core, componentes principales, flujo end-to-end de un incidente, mapa de archivos clave |
| **2. Comunicaciones** | [funcionamiento_mqtt.md](funcionamiento_mqtt.md) | Esquema de topics `seguridad/<device>/<categoría>`, AWS IoT Core, mTLS, enrutamiento del coordinador |
| **3. Resiliencia MQTT** | [MQTT_Resilience.md](MQTT_Resilience.md) | Dos clientes MQTT, detección de conexiones zombie, reconexión automática, garantías de entrega |
| **4. Agentes IA** | [Agent_Architecture.md](Agent_Architecture.md) | `SOC_Triage_Agent`, `SOC_Feedback_Agent`, Runner ADK, colas asíncronas, acoplamiento con el motor de políticas |
| **5. Motor de Políticas** | [funcionamiento_policy_engine.md](funcionamiento_policy_engine.md) | Clasificación de riesgo (SAFE_READ/LOW/HIGH/CRITICAL), audit log inmutable |
| **6. Human-in-the-Loop** | [HITL_Architecture.md](HITL_Architecture.md) | Modelo Zero-Trust con escalada de privilegios, ciclo PENDING → APPROVED, modal del dashboard |
| **7. Dashboard SOC** | [Dashboard_Architecture.md](Dashboard_Architecture.md) | Flask + auth, endpoints, refresco AJAX, Live Threat Feed, topología radar, sistema de revertido |
| **8. Persistencia** | [Database_Schema.md](Database_Schema.md) | SQLite WAL, tabla `logs`, tabla `audit_log` con triggers append-only, retención automática |
| **9. Testing** | [Testing_Guide.md](Testing_Guide.md) | Test E2E (`test_agent_flow.py`), unitarios (`test_policy_engine.py`), pruebas MQTT (`test_flexible_command.py`), mocks |
| **10. Despliegue** | [Configuration_and_Deployment.md](Configuration_and_Deployment.md) | `config.yml`, `.env`, Docker Compose, `soc_manager.sh`, perfiles `local-ai` vs Gemini API |
| **11. Trabajo futuro** | [futuras_mejoras.md](futuras_mejoras.md) | Propuestas evaluadas no implementadas, motivación y plan de migración |
| **12. Resiliencia Gemini 429** | [plan_implementacion_resiliencia_gemini_429.md](plan_implementacion_resiliencia_gemini_429.md) | Persistencia `pending_ai_events`, backoff de reintento y limpieza desde SOC Manager |

## Operaciones y mantenimiento

| Documento | Qué cubre |
|-----------|-----------|
| [Troubleshooting.md](Troubleshooting.md) | **Errores conocidos** con diagnóstico paso a paso, causa raíz y solución. Incluye árbol de decisión rápido. |
| [CHANGELOG.md](CHANGELOG.md) | **Registro de cambios** por fecha con hashes de commit, archivos modificados y análisis de causa raíz para cada bugfix. |

## Referencia del nodo edge (PI-4)

| Documento | Estado |
|-----------|--------|
| [PI4_Referencia_Tecnica.md](PI4_Referencia_Tecnica.md) | Referencia rápida del sensor. Se completará en una fase posterior. No tocar desde aquí. |

## Convenciones de los documentos

Todos los docs siguen el mismo formato:

- **Frontmatter YAML** con título, autor, fecha y tags.
- **Sección `1. Propósito`**: alcance del documento y qué *no* cubre (para evitar duplicación con docs hermanos).
- **Secciones numeradas** (componentes, flujo, configuración, reglas críticas, archivos involucrados).
- **Enlaces relativos** al código fuente (`../PI-5/src/...`) y a otros docs (`./xxx.md`).
- **Diagramas en ASCII** cuando ayudan a fijar el flujo. Sin imágenes adjuntas.

> **Regla de mantenimiento**: todo cambio significativo en el código debe reflejarse en la documentación correspondiente. Si introduces un bug fix que te costó más de 10 minutos, añádelo a [Troubleshooting.md](Troubleshooting.md). Si introduces una feature nueva, actualiza el doc de la fase afectada.

## Documentos archivados

El histórico de documentos sustituidos vive en [`basura/docs_desactualizados/`](../basura/docs_desactualizados/). Incluye la documentación técnica monolítica anterior (`DOCUMENTACION_TECNICA_PI5.md`), referencias TFG previas, informes puntuales (`informe-adk-*`, `informe-mejoras-*`) y planes ya cerrados (`*.resolved`). Se conservan por trazabilidad histórica, no como referencia activa.
