# 🛡️ Sentinel-IT — Informe semanal de mejoras generales
**Fecha:** 23 de abril de 2026
*Foco: PI-5 (coordinador) | Google ADK se analiza en informe separado.*

---

## 🔴 Urgente (CVEs o breaking changes)

### CVE-2026-33032 — nginx-ui (CVSS 9.8) — ACTIVAMENTE EXPLOTADO
- **Afectado:** nginx-ui (panel de administración web de Nginx), NO el core de nginx.
- **Impacto:** Permite tomar control total del servidor Nginx sin autenticación a través del endpoint MCP. Más de 2.600 instancias expuestas, con explotación activa confirmada.
- **Acción:** Si la PI-4 usa nginx-ui como panel de gestión, actualizar inmediatamente a la versión **2.3.4** (parcheada el 15/03/2026). Si no se usa nginx-ui, no hay impacto.

### CVE-2026-32710 — MariaDB (CVSS 8.6) — Alta severidad
- **Afectado:** MariaDB Community Server (versiones anteriores a 12.2.2, 11.8.5, 11.4.10).
- **Acción:** Actualizar MariaDB en la PI-4 a una de las versiones parcheadas. Ejecutar `mariadb --version` para verificar.

### CVE-2026-1642 / CVE-2026-27654 — nginx core — Severidad media
- Buffer overflows en módulos `ngx_http_dav_module` y `ngx_http_mp4_module`. Impacto limitado si no se usan esos módulos.

---

## ⭐ Mejoras PI-5 (Coordinador)

### ☁️ AWS IoT Core y MQTT

| Mejora | Impacto en Sentinel-IT | Esfuerzo | Prioridad |
|--------|----------------------|----------|-----------|
| **Migrar a MQTT 5** — AWS IoT Core lo soporta con compatibilidad retroactiva desde 2022, SDK Python v2 incluye soporte completo | Permite añadir `User Properties` a los mensajes MQTT para incluir metadatos (device_id, timestamp, severity) sin modificar el payload JSON. Simplifica el routing en las Rules del IoT Core | Medio | Media |
| **Topic Aliases en MQTT 5** — Reduce el overhead de red codificando el nombre del topic como un entero | Para topics frecuentes como `logs/pi4/security`, el ahorro es ~30-50 bytes por mensaje. Útil si el volumen de logs es alto | Bajo | Baja |
| **Session Expiry Interval (MQTT 5)** — Configurable en CONNECT y DISCONNECT | Permite definir exactamente cuánto tiempo sobrevive la sesión si la PI-5 se desconecta, evitando pérdida de mensajes en reinicios del coordinador | Bajo | Media |
| **AWS IoT Greengrass v2.17** — Nucleus lite con solo 4MB de RAM para componentes de Secure Tunneling | Si en el futuro se despliega un agente en la PI-4 vía Greengrass, ahora puede correr como non-root con mucho menos overhead | Bajo | Baja |
| **awsiotsdk 1.28.2** — Versión más reciente (marzo 2026), sin breaking changes desde la >=1.28.2 que ya usa el proyecto | El proyecto ya cumple el requisito mínimo. Verificar que el `requirements.txt` no pinte en una versión anterior | Bajo | Baja |

**Nota técnica:** AWS IoT Core soporta despliegues heterogéneos MQTT 3/5 simultáneamente, por lo que la migración puede hacerse de forma gradual sin romper nada.

---

### ⚙️ Sistema de batching y coordinador

| Mejora | Impacto en Sentinel-IT | Esfuerzo | Prioridad |
|--------|----------------------|----------|-----------|
| **Migrar `LogBatchQueue` a `asyncio`** — En 2026, asyncio supera en 9x el throughput de threading para workloads I/O-bound en edge devices. Un caso real documentado pasó de 5k req/s a 45k req/s migrando de threads a asyncio | El sistema actual usa dos threads daemon con cola thread-safe. Asyncio eliminaría el GIL como cuello de botella y permitiría escalar sin cambiar la lógica de negocio. Los dos runners ADK podrían ser corrutinas en el mismo event loop | Alto | Media |
| **Doble trigger con `asyncio.wait_for` + `asyncio.Queue`** — Reemplaza el polling manual por un event loop nativo | El trigger de volumen (max 10 logs) y tiempo (15s) se implementaría de forma más limpia y eficiente con `asyncio.Queue.get(timeout=15)` | Medio | Media |
| **Sesión compartida entre runners** — Es un antipatrón conocido cuando dos agentes modifican estado concurrentemente | Si el `SOC_Triage_Agent` y el `SOC_Feedback_Agent` comparten `InMemorySessionService`, pueden producirse race conditions al actualizar el historial de conversación. Solución simple: una sesión por agente, o usar `asyncio.Lock` alrededor del acceso a la sesión | Bajo | Alta |

---

### 🗄️ SQLite y persistencia

| Mejora | Impacto en Sentinel-IT | Esfuerzo | Prioridad |
|--------|----------------------|----------|-----------|
| **Activar WAL mode en `soc_alerts.db`** — Hasta 10x mejora de rendimiento en escrituras concurrentes según benchmarks 2026. Una sola línea de código: `PRAGMA journal_mode=WAL` | El `SOC_Triage_Agent` y el `SOC_Feedback_Agent` escriben a la misma base de datos simultáneamente (`register_alert` y `update_alert_status`). WAL permite que un writer no bloquee a lectores (el dashboard Flask), eliminando timeouts | Muy bajo | Alta |
| **Mantener SQLite (descartar DuckDB)** — DuckDB es OLAP, optimizado para queries analíticas sobre millones de filas, no para inserciones transaccionales frecuentes de un SOC | Para el volumen esperado de Sentinel-IT (decenas/cientos de alertas), SQLite con WAL es perfectamente adecuado. DuckDB introduciría complejidad innecesaria | — | — |
| **`PRAGMA synchronous = NORMAL`** — Junto con WAL, reduce los fsync y mejora la latencia de escritura sin sacrificar integridad en caso de crash del SO | Combinado con WAL, es la configuración recomendada para aplicaciones de alta disponibilidad en embedded databases | Muy bajo | Media |

---

### 📊 Dashboard Flask

| Mejora | Impacto en Sentinel-IT | Esfuerzo | Prioridad |
|--------|----------------------|----------|-----------|
| **Añadir SSE (Server-Sent Events) sin dependencias extra** — Flask soporta streaming responses nativamente con `Response(stream_with_context(...))` | El dashboard actual muestra alertas estáticas. Con SSE, el navegador recibe actualizaciones en tiempo real cuando el `SOC_Triage_Agent` registra una nueva alerta, sin necesidad de refrescar la página. Implementación documentada sin Redis ni dependencias adicionales | Medio | Alta |
| **Migrar de HTTP Basic Auth a Flask-JWT-Extended** — JWT v4.7.1 (2026) añade refresh tokens, revocación y custom claims | HTTP Basic Auth envía credenciales en cada request. JWT es más seguro (tokens de corta vida, 15min-1h) y permite invalidar sesiones. Especialmente relevante si el dashboard se expone en una red más amplia | Medio | Media |
| **Cabeceras de seguridad en Flask** — `X-Content-Type-Options`, `X-Frame-Options`, `Content-Security-Policy`, `Strict-Transport-Security` | Hardening básico del dashboard. Flask 3.x no las añade por defecto. Se implementan con un `@app.after_request` en 5 líneas | Muy bajo | Alta |
| **HTTPS en el dashboard** — Flask en modo debug no usa TLS | Si el dashboard es accesible fuera de localhost, configurar un certificado autofirmado o usar el proxy inverso de la PI-4 con TLS terminado en nginx | Bajo | Alta |

---

### 🤖 Ollama y modelos locales

| Mejora | Impacto en Sentinel-IT | Esfuerzo | Prioridad |
|--------|----------------------|----------|-----------|
| **Evaluar `qwen2.5:7b` o `llama3.2:3b` para análisis de logs** — Estudios 2026 muestran F1-score de 0.928 en detección de vulnerabilidades con estos modelos, frente a 0.555 de XGBoost | El modelo actual `gemma4:e2b` (variante E2B de Gemma 4, lanzado el 2/04/2026) es muy reciente. Para análisis de logs de seguridad específicamente, `qwen2.5:7b` tiene mejor rendimiento documentado pero requiere 8GB RAM. `llama3.2:3b` (~5 tokens/s en Pi 5) es un buen compromiso | Bajo | Media |
| **`gemma3:1b` como modelo de triage rápido** — El más eficiente en Pi 5 (8-12 tokens/s), consume menos RAM | Para un sistema de triage de dos niveles: `gemma3:1b` para clasificación rápida (urgente/normal) y el modelo principal para análisis detallado. Reduciría latencia para alertas críticas | Medio | Media |
| **Modo cuantización Q4** — Ollama usa Q4 por defecto en ARM64 | Verificar que el modelo está cargado con Q4 y no Q8. `ollama show gemma4:e2b` muestra la cuantización activa. Q4 reduce uso de RAM a la mitad con pérdida mínima de precisión | Muy bajo | Alta |
| **Overclocking moderado Pi 5** — Foros documentan mejora de ~15-20% en tokens/s pasando de 2.4GHz a 3.0GHz | En un sistema de producción como un TFG con supervisión, el overclocking es viable. Requiere cooling adecuado (heatsink + ventilador) | Bajo | Baja |

---

### 🐳 Docker y dependencias

| Mejora | Impacto en Sentinel-IT | Esfuerzo | Prioridad |
|--------|----------------------|----------|-----------|
| **Docker rootless mode** — Elimina la necesidad de root para ejecutar el daemon Docker | Si el coordinador se ve comprometido, el attacker no obtiene privilegios root en la PI-5. Soporte nativo en ARM64/Raspberry Pi OS 64-bit. Limitación: no soporta `--privileged` ni ports <1024 (el coordinador probablemente no los necesita) | Bajo | Alta |
| **Imágenes distroless o slim** — Reducen la superficie de ataque eliminando shell y utilidades innecesarias | Para el contenedor del coordinador, usar `python:3.12-slim-bookworm` (ARM64) en lugar de `python:3.12` reduce la imagen de ~900MB a ~130MB | Bajo | Media |
| **Pydantic v3** — Aún en planificación (sin fecha de release confirmada en 2026) | NO hay breaking changes inminentes. Pydantic v3 solo eliminará los helpers de migración v1→v2. El proyecto ya usa `pydantic>=2.12.5`, así que está al día. No requiere acción | — | — |
| **Cosign v3 para verificación de imágenes** — Best practice 2026 para supply chain security | Firmar y verificar las imágenes Docker del coordinador antes de desplegar. Útil si el TFG se despliega en un entorno con múltiples admins | Alto | Baja |
| **`--cap-drop ALL` + `--cap-add` selectivo** — Docker otorga capabilities por defecto que la mayoría de apps no necesitan | Añadir `cap_drop: [ALL]` y solo `cap_add: [NET_BIND_SERVICE]` si aplica en el `docker-compose.yml`. Mejora de seguridad con una línea | Muy bajo | Alta |

---

### 🔍 Técnicas SOC aplicables

| Mejora | Impacto en Sentinel-IT | Esfuerzo | Prioridad |
|--------|----------------------|----------|-----------|
| **Nueva tool: `check_ip_reputation(ip)`** con AbuseIPDB API | AbuseIPDB ofrece **1.000 consultas gratuitas/día**. El `SOC_Triage_Agent` podría llamarla antes de `block_ip()` para confirmar si la IP es conocida como maliciosa. Implementación: una llamada `requests.get` con la API key. Reduce falsos positivos | Bajo | Alta |
| **Nueva tool: `check_ip_reputation(ip)`** con AlienVault OTX (alternativa open) | OTX ofrece feeds de amenazas gratuitos y sin límite diario para consultas básicas de reputación. Complementa a AbuseIPDB | Bajo | Media |
| **Correlación temporal en el batching** — Detectar múltiples eventos del mismo IP en la misma ventana de tiempo | El `LogBatchQueue` ya agrupa logs por tiempo (15s). Añadir pre-procesado que agrupe por `source_ip` antes de enviar al agente permitiría al triage detectar patrones de brute force/port scan sin análisis IA costoso | Medio | Alta |
| **Reglas de correlación ligeras** — Un dict Python `{(ip, tipo_ataque): contador}` con ventana deslizante | Antes de invocar al modelo LLM, un filtro de reglas simples (ej: >5 SSH failures en 30s = brute force) reduciría el número de inferencias y la latencia | Medio | Media |

---

## 🖥️ Mejoras PI-4 (breve)

### CVEs urgentes
- **nginx-ui CVE-2026-33032 (CVSS 9.8)**: Si la PI-4 usa nginx-ui, actualizar a 2.3.4 inmediatamente. Explotación activa confirmada.
- **MariaDB CVE-2026-32710 (CVSS 8.6)**: Actualizar a versión 11.4.10+ o 11.8.5+.
- **nginx core**: Buffer overflows en módulos DAV y MP4 (severidad media). Si no se usan esos módulos, riesgo bajo.
- **vsftpd**: Sin CVEs nuevos en 2026. El riesgo histórico mayor es la versión 2.3.4 con backdoor (CVE-2011-2523); verificar que se usa una versión >=3.0.5.

### Hardening destacable
- **SSH**: Revisar que `PasswordAuthentication no` esté activo y usar solo claves Ed25519. Configurar `MaxAuthTries 3` y `LoginGraceTime 30s`.
- **Honeypot**: Considerar sustituir el honeypot web actual por **T-Pot** (stack Docker con 20+ honeypots + Kibana integrado) o **Heralding** (Python, ligero, captura credenciales de FTP/SSH/HTTP). Ambos generan logs en formato JSON, más fáciles de procesar con el pipeline MQTT.

---

## 💡 Top 3 mejoras de la semana

1. **Activar WAL mode en SQLite** (`PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;`): Es la mejora de mayor impacto con el menor esfuerzo de todo el informe. Una sola conexión SQLite al inicio del coordinador activa el modo, elimina los bloqueos entre el agente de triage y el de feedback, y reduce la latencia del dashboard Flask. Cambio de 2 líneas de código.

2. **Añadir la tool `check_ip_reputation()` con AbuseIPDB**: AbuseIPDB tiene API gratuita (1.000 consultas/día), documentación clara, y la integración son ~15 líneas de Python. Permite al `SOC_Triage_Agent` validar si una IP atacante es conocida globalmente antes de bloquearla, reduciendo falsos positivos y añadiendo inteligencia de amenazas real al TFG con coste cero.

3. **Cabeceras de seguridad + SSE en el dashboard Flask**: Las cabeceras de seguridad son 5 líneas en un `@app.after_request` y eliminan vulnerabilidades básicas de clickjacking y XSS. SSE convierte el dashboard en tiempo real (alertas aparecen sin refrescar), lo que mejora significativamente la demostración del TFG ante el tribunal.

---

## 🔗 Fuentes consultadas

- [AWS IoT Greengrass v2.17 release notes](https://docs.aws.amazon.com/greengrass/v2/developerguide/greengrass-release-2026-04-16.html)
- [AWS IoT Core MQTT 5 features](https://aws.amazon.com/blogs/iot/introducing-new-mqttv5-features-for-aws-iot-core-to-help-build-flexible-architecture-patterns/)
- [awsiotsdk en PyPI](https://pypi.org/project/awsiotsdk/)
- [Python asyncio vs threading benchmark 2026](https://docs.bswen.com/blog/2026-04-14-asyncio-vs-threading-vs-multiprocessing/)
- [SQLite WAL mode 10x performance](https://dev.to/lumin-playstar/sqlite-wal-mode-10x-performance-for-python-apps-4ic)
- [SQLite WAL setup 2026](https://oneuptime.com/blog/post/2026-03-02-how-to-set-up-sqlite-with-wal-mode-on-ubuntu/view)
- [DuckDB vs SQLite comparison 2026](https://www.analyticsvidhya.com/blog/2026/01/duckdb-vs-sqlite/)
- [Flask JWT authentication 2026](https://oneuptime.com/blog/post/2026-02-02-flask-jwt-authentication/view)
- [Flask SSE sin dependencias](https://maxhalford.github.io/blog/flask-sse-no-deps/)
- [Gemma 4 en Raspberry Pi](https://dev.to/alanwest/gemma-4-runs-on-a-raspberry-pi-i-tested-it-56c5)
- [LLMs performance en Raspberry Pi 5](https://www.stratosphereips.org/blog/2025/6/5/how-well-do-llms-perform-on-a-raspberry-pi-5)
- [Small LLMs para ciberseguridad 2026](https://www.siliconflow.com/articles/en/best-open-source-LLM-for-Cybersecurity-Threat-Analysis)
- [Docker rootless mode](https://docs.docker.com/engine/security/rootless/)
- [Docker security best practices 2026](https://www.techsaas.cloud/blog/docker-container-security-best-practices-2026/)
- [CVE-2026-33032 nginx-ui (activamente explotado)](https://thehackernews.com/2026/04/critical-nginx-ui-vulnerability-cve.html)
- [CVE-2026-27944 nginx-ui backup leak](https://securityaffairs.com/189123/security/critical-nginx-ui-flaw-cve-2026-27944-exposes-server-backups.html)
- [MariaDB CVEs 2026](https://stack.watch/product/mariadb/mariadb/)
- [AbuseIPDB API gratuita](https://dev.to/0012303/abuseipdb-has-a-free-api-check-if-any-ip-address-is-malicious-in-one-request-16ac)
- [Mejores Threat Intelligence APIs 2026](https://ismalicious.com/posts/best-threat-intelligence-api-comparison-2026)
- [SOC automation Python 2026](https://medium.com/@ahmedsobhialii/demystifying-siem-how-i-built-a-real-time-ai-detection-pipeline-in-pure-python-24ee10974587)
- [Honeypots open source 2026](https://anantis.io/best-honeypot-solutions-in-2026-including-open-source/)

---
*Informe generado automáticamente el 2026-04-23. Google ADK y sus agentes se analizan en un informe separado.*
