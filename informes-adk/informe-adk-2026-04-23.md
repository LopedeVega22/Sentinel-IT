# 🛡️ Sentinel-IT — Informe semanal ADK & Alternativas
**Fecha:** 23 de abril de 2026
**Versión ADK en uso:** `google-adk[extensions]` >=1.28.1

---

## 📦 Novedades de Google ADK esta semana

### Última versión disponible

- **Versión:** 1.31.1 — **Fecha de publicación:** 21 de abril de 2026
- **PyPI:** https://pypi.org/project/google-adk/
- **GitHub releases:** https://github.com/google/adk-python/releases
- **Changelog oficial:** https://github.com/google/adk-python/blob/main/CHANGELOG.md

### Impacto en Sentinel-IT

| Novedad | Componente afectado en Sentinel-IT | Acción recomendada |
|---------|-----------------------------------|--------------------|
| **Event Compaction** (resumen automático de eventos antiguos vía `EventsCompactionConfig`) | `SOC_Triage_Agent` y `SOC_Feedback_Agent`. El sistema acumula logs continuamente: sin compaction, el contexto crece indefinidamente hasta superar el límite del modelo. | **Implementar ya.** Configurar `EventsCompactionConfig` en el `App` object de cada agente. Crítico para sesiones largas con Ollama, donde el contexto es más limitado. Docs: https://google.github.io/adk-docs/context/compaction/ |
| **Session Rewind** (rollback a una invocación anterior) | `InMemorySessionService` compartido entre ambos agentes. Permite deshacer el estado de una sesión si el agente ejecutó una acción errónea (p.ej. `block_ip` sobre una IP legítima). | **Explorar para depuración.** Útil en demos del TFG: si `SOC_Triage_Agent` bloquea algo incorrectamente, se puede revertir la sesión y mostrar la capacidad de rollback. Documentar en la memoria del TFG. |
| **`on_event_callback` antes de `append_event`** (los callbacks se ejecutan antes de persistir el evento) | `LogBatchQueue` custom. Los events de log ahora pueden modificarse o filtrarse antes de ser registrados en sesión. | **Bajo impacto inmediato.** Podría simplificar el pre-procesamiento de logs antes del batch, pero el sistema actual ya funciona. Marcar como mejora potencial post-TFG. |
| **`memories.ingest_events` en `VertexAiMemoryBankService`** | Solo afecta si se usa Vertex AI (modo cloud). En modo local con Ollama, no aplica. | **Ignorar por ahora.** El proyecto corre en Raspberry Pi con Ollama. Sin impacto. |
| **Workflow/BaseNode graph orchestration** (grafos de agentes con partial resume y lazy scan) | La pipeline triage → feedback podría modelarse como un grafo explícito en lugar de dos agentes independientes. | **Evaluar a largo plazo.** Demasiado cambio para el cierre del TFG, pero arquitectónicamente más correcto. Anotar para futuras versiones. |

### Conclusión sobre novedades ADK

La novedad más accionable esta semana es **Event Compaction**: es directamente aplicable a Sentinel-IT sin reestructurar nada, y resuelve un problema real (crecimiento descontrolado del contexto en sesiones largas de monitorización). La versión 1.28.1 ya está por encima del mínimo requerido para esta feature.

---

## 🔄 Análisis de alternativas a Google ADK

### Frameworks evaluados

**LangGraph** (LangChain) — v0.3.x — ~40k ⭐ GitHub

- **Ventaja concreta para Sentinel-IT:** Permite modelar el flujo triage→feedback como un grafo de estados explícito (nodos, edges condicionales). El "human-in-the-loop" está muy maduro: pausar antes de ejecutar `block_ip` sería trivial de implementar. Muy usado en SOC/SIEM en 2026.
- **Desventaja concreta para Sentinel-IT:** En marzo de 2026 se descubrió una **vulnerabilidad de SQL injection en el checkpoint SQLite de LangGraph** (exactamente el mismo motor de BD que usa Sentinel-IT). Usar LangGraph con SQLite en un entorno de seguridad es un riesgo inaceptable. Además, el modelo de programación (grafos + nodos) es más complejo que el actual `LlmAgent`.
- **¿Merece migración?** No — la vulnerabilidad SQLite es un bloqueante absoluto para un sistema SOC, y la curva de aprendizaje no compensa para un TFG de ASIR.

---

**CrewAI** — v0.11.x — ~27k ⭐ GitHub

- **Ventaja concreta para Sentinel-IT:** El modelo "role-playing" encaja perfectamente: `SOC_Triage_Agent` = analista L1, `SOC_Feedback_Agent` = analista QA L2. La sintaxis es más declarativa y legible que ADK. Es el framework multi-agente de más rápido crecimiento en 2026.
- **Desventaja concreta para Sentinel-IT:** En 2026 se encontraron **4 vulnerabilidades encadenables vía prompt injection** que permiten sandbox escape y RCE. Inaceptable para un sistema que recibe logs de atacantes externos (los logs maliciosos podrían contener payloads de prompt injection). Además, el soporte para Ollama/LiteLLM es menos robusto que en ADK.
- **¿Merece migración?** No — vulnerabilidades de seguridad en el propio framework son incompatibles con un sistema SOC que procesa input adversarial.

---

**Microsoft Agent Framework 1.0** (sucesor de AutoGen + Semantic Kernel) — GA desde abril de 2026

- **Ventaja concreta para Sentinel-IT:** Unifica AutoGen y Semantic Kernel en un único SDK Python. Soporte nativo para MCP, checkpointing, pause/resume, y telemetría enterprise. Session-based state management muy robusto.
- **Desventaja concreta para Sentinel-IT:** Orientado a entornos enterprise (.NET y Python corporativo). El overhead de configuración es elevado. El soporte para Ollama/LiteLLM en Raspberry Pi no está probado. Demasiado pesado para el hardware objetivo.
- **¿Merece migración?** No — overkill para un TFG en Raspberry Pi. Interesante conocerlo de cara al mundo laboral, pero no aporta ventajas prácticas sobre ADK en este contexto.

---

**Pydantic AI** — v1.85.1 (22 abril 2026) — ~16k ⭐ GitHub

- **Ventaja concreta para Sentinel-IT:** Validación de tipos automática en tools Python. Las herramientas `register_alert` y `block_ip` se beneficiarían: si el agente devuelve datos malformados (IP inválida, severity fuera de rango), Pydantic AI reintenta automáticamente con corrección. Integración nativa con Pydantic Logfire para observabilidad. Muy ligero, funciona bien en Raspberry Pi.
- **Desventaja concreta para Sentinel-IT:** No tiene soporte multi-agente nativo (no hay equivalente al sistema triage→feedback sin construirlo manualmente). Menos ecosistema que ADK para casos de uso IoT/MQTT. La integración con Ollama existe pero es menos madura.
- **¿Merece migración?** No (migración completa), pero **sí merece consideración parcial**: podría usarse como librería de validación de outputs dentro del sistema ADK actual, sin reemplazarlo.

---

## 💡 Conclusión de la semana

**Google ADK sigue siendo la mejor opción** para Sentinel-IT: los competidores más atractivos (LangGraph, CrewAI) tienen vulnerabilidades de seguridad activas que los descalifican directamente para un sistema SOC. La acción prioritaria esta semana es **implementar Event Compaction** (`EventsCompactionConfig`) en ambos agentes ADK, ya que resuelve el problema real del crecimiento de contexto en sesiones largas sin coste de migración. Como mejora secundaria, explorar la validación de tipos en las tools actuales inspirándose en el modelo de Pydantic AI.

---

## 🔗 Fuentes consultadas

- [google-adk · PyPI](https://pypi.org/project/google-adk/)
- [Releases · google/adk-python (GitHub)](https://github.com/google/adk-python/releases)
- [ADK Release Notes oficiales](https://google.github.io/adk-docs/release-notes/)
- [Context Compaction — ADK Docs](https://google.github.io/adk-docs/context/compaction/)
- [LangChain/LangGraph SQL injection vulnerability (The Hacker News)](https://thehackernews.com/2026/03/langchain-langgraph-flaws-expose-files.html)
- [CrewAI vulnerabilities expose devices to hacking (SecurityWeek)](https://www.securityweek.com/crewai-vulnerabilities-expose-devices-to-hacking/)
- [Microsoft Agent Framework 1.0 GA (Visual Studio Magazine)](https://visualstudiomagazine.com/articles/2026/04/06/microsoft-ships-production-ready-agent-framework-1-0-for-net-and-python.aspx)
- [Pydantic AI — PyPI](https://pypi.org/project/pydantic-ai/)
- [Building Your First Cybersecurity AI Agent with LangGraph (Medium)](https://medium.com/seercurity-spotlight/building-your-first-cybersecurity-ai-agent-with-langgraph-d27107ac872a)
- [Top 5 AI Agent Frameworks 2026 (Intuz)](https://www.intuz.com/blog/top-5-ai-agent-frameworks-2025)
