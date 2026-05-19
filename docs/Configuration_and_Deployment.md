---
title: "Configuración y Despliegue - Sentinel-IT (PI-5)"
author: "Daniel Alarcon"
date: "2026-05-17"
tags: ["deployment", "docker", "config", "env", "ollama", "gemini", "aws"]
---

# Configuración y Despliegue

## 1. Propósito

Este documento describe **cómo se monta y se levanta** el coordinador SOC en una Raspberry Pi 5: requisitos, configuración (YAML + variables de entorno + certificados), orquestación con Docker Compose, perfiles de IA (local vs Gemini API) y el script utilitario `soc_manager.sh`.

No describe la arquitectura del coordinador — eso vive en [System_Overview.md](System_Overview.md) y los docs por subsistema.

## 2. Requisitos del host

| Componente | Versión mínima | Notas |
|------------|----------------|-------|
| Raspberry Pi 5 | 4 GB RAM | Suficiente con perfil API; si usas Ollama local conviene 8 GB |
| Sistema operativo | Raspberry Pi OS 64-bit (Debian 12 base) | Ubuntu Server 26.04 también vale |
| Docker | 24.x+ | El script `soc_manager.sh` lo instala vía `get.docker.com` si falta |
| docker-compose-plugin | v2 | Idem, instalado por el script |
| Git | Cualquiera | Solo para clonar el repo |
| Conexión a Internet | — | Necesaria para AWS IoT (mTLS + endpoint) y, si aplica, Gemini API |

El coordinador está pensado para **una sola instancia** por proyecto. Levantar dos PI-5 a la vez con el mismo `client_id` los hace pelearse por la conexión MQTT (la Policy de AWS solo autoriza un `Pi5-dani`).

## 3. Configuración

Hay tres archivos de configuración. **Ninguno se sube a Git** (ver `.gitignore`):

### 3.1 `PI-5/config.yml` — Configuración aplicacional

```yaml
aws:
  endpoint: "aj4wsdnimoej8-ats.iot.eu-north-1.amazonaws.com"
  client_id: "Pi5-dani"
  cert_path: "./certificados/Pi5-dani.cert.pem"
  key_path:  "./certificados/Pi5-dani.private.key"
  root_ca:   "./certificados/root-CA.crt"

mqtt:
  topic_subscribe_telemetria: "seguridad/+/telemetria"
  topic_subscribe_eventos:    "seguridad/+/evento"
  topic_subscribe_respuestas: "seguridad/+/respuesta"
  topic_publish_comando:      "seguridad/{device}/comando"

database:
  db_path: "data/soc_data.db"

web:
  host: "0.0.0.0"
  port: 5000

agent:
  model_name: "gemini-3.1-flash"   # solo se usa si AI_MODE != local

logging:
  file_path: "/tmp/coordinator_soc.log"
  level: "INFO"
  max_bytes: 5242880    # 5 MB
  backup_count: 3

retention:
  max_days: 30          # purga filas 'Solo Registro' más antiguas
  purge_on_insert: true # ejecuta la purga antes de cada register_alert

batch:
  max_size: 10          # flush al alcanzar 10 logs en la cola
  flush_interval: 15    # flush si pasan 15 s desde el último flush
```

Cada sección la consume:

| Sección | Consumidor | Detalle en |
|---------|------------|-----------|
| `aws.*` | `main_coordinator.py`, `dashboard_soc.py`, `aws_connector.py` | [funcionamiento_mqtt.md](funcionamiento_mqtt.md) |
| `mqtt.*` | `main_coordinator.py`, `iot_tools.py`, `dashboard_soc.py` | [funcionamiento_mqtt.md](funcionamiento_mqtt.md) |
| `database.db_path` | `database.py`, `db_tools.py`, `iot_tools.py`, `dashboard_soc.py`, `policy_engine.py` | [Database_Schema.md](Database_Schema.md) |
| `web.*` | `dashboard_soc.py` | [Dashboard_Architecture.md](Dashboard_Architecture.md) |
| `agent.model_name` | `triage_agent.py`, `feedback_agent.py` | [Agent_Architecture.md](Agent_Architecture.md) |
| `logging.*` | `main_coordinator.py` | — |
| `retention.*` | `db_tools.rotate_old_logs` | [Database_Schema.md](Database_Schema.md) |
| `batch.*` | `main_coordinator.LogBatchQueue` | [Agent_Architecture.md](Agent_Architecture.md) |

### 3.2 `PI-5/.env` — Secretos y modo de IA

```ini
# Credenciales del dashboard (HTTP Basic Auth)
DASHBOARD_USER=admin
DASHBOARD_PASSWORD=cambiame_en_produccion
# Alternativa más segura: usar el hash precomputado y NO setear DASHBOARD_PASSWORD
# DASHBOARD_PASSWORD_HASH=pbkdf2:sha256:600000$...

# Modo del agente IA
AI_MODE=api                            # api → Vertex/Gemini directo
                                       # local → Ollama vía LiteLLM (necesita perfil docker)
AI_MODEL=gemini-3.1-flash              # solo si AI_MODE=api
# AI_MODEL=ollama/gemma4:2b            # si AI_MODE=local

# Credenciales Gemini (solo si AI_MODE=api)
GEMINI_API_KEY=...
```

El docker-compose monta este archivo como volumen read-only en `/app/.env`. Las claves se cargan al arrancar con `python-dotenv`.

### 3.3 `PI-5/certificados/*` — Identidad mTLS

Tres archivos obligatorios:

```
PI-5/certificados/
├── root-CA.crt              ← Raíz de AWS IoT (igual para todos los dispositivos)
├── Pi5-dani.cert.pem        ← Certificado del coordinador
└── Pi5-dani.private.key     ← Clave privada
```

Estos certificados los genera AWS IoT al crear el "Thing" desde la consola. La Policy IAM asociada autoriza al `client_id` `Pi5-dani` a conectar y a operar sobre `seguridad/*`. Los certificados se montan como `:ro` en el contenedor para que la clave privada no sea editable desde dentro.

> **No subir nunca a Git.** El `.gitignore` del repo excluye `**/certificados/*.{pem,key,crt}` y `**/.env`.

## 4. Despliegue con `soc_manager.sh`

Script bash interactivo en `PI-5/soc_manager.sh`. Se ejecuta con `sudo`:

```bash
cd ~/Sentinel-IT/PI-5
sudo ./soc_manager.sh
```

Menú principal:

1. **Iniciar SOC (Producción / Cloud)** → `docker compose up -d --build` (perfil sin Ollama).
2. **Iniciar SOC (Local / IA Privada)** → `docker compose --profile local-ai up -d --build` (con Ollama).
3. **Estado y Logs** → muestra `docker ps` y `tail` de los logs.
4. **Reiniciar** → `docker compose restart`.
5. **Parar** → `docker compose down`.
6. **Purgar completo** → `docker compose down -v` (¡borra el volumen de SQLite!).
7. **Actualizar repo** → `git pull` + rebuild.

Internamente:

- Comprueba que `docker`, `docker compose` y `git` están instalados; los instala si no.
- Verifica que los certificados existen en `./certificados/` antes de levantar.
- Avisa si `.env` no tiene `GEMINI_API_KEY` cuando `AI_MODE=api`.

El script es el camino recomendado para no memorizar los flags de Docker Compose.

## 5. Despliegue manual con Docker Compose

Sin el script:

```bash
cd PI-5

# Perfil cloud (Gemini API, sin Ollama)
docker compose up -d --build

# Perfil local (con Ollama)
docker compose --profile local-ai up -d --build
```

### 5.1 Estructura de `docker-compose.yml`

```yaml
services:
  soc-coordinator-pi5:
    build: { context: ., dockerfile: Dockerfile }
    ports: [ "5000:5000" ]
    volumes:
      - soc_data_volume:/app/data            # SQLite persistente
      - ./coordinator_soc.log:/app/coordinator_soc.log
      - ./dashboard_soc.log:/app/dashboard_soc.log
      - ./certificados:/app/certificados:ro  # mTLS (solo lectura)
      - ./.env:/app/.env:ro                  # Secretos (solo lectura)
    environment:
      - TZ=Europe/Madrid
      - GEMINI_API_KEY=${GEMINI_API_KEY}

  local-ai-engine:                           # Solo bajo --profile local-ai
    image: ollama/ollama:latest
    profiles: [ local-ai ]
    ports: [ "11434:11434" ]
    volumes:
      - ollama_data_volume:/root/.ollama

volumes:
  soc_data_volume:   { name: "soc_pi5_database_persistent" }
  ollama_data_volume:{ name: "soc_pi5_ollama_persistent" }
```

### 5.2 Dockerfile

```dockerfile
FROM python:3.14-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/src
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /app/data && python3 src/database.py
EXPOSE 5000
COPY scripts/start_services.sh .
RUN chmod +x start_services.sh
CMD ["./start_services.sh"]
```

### 5.3 `scripts/start_services.sh`

```bash
#!/bin/bash
# Inicializa esquema en runtime (el volume oculta el .db del build)
mkdir -p /app/data
python src/database.py

# Lanza dashboard en background y coordinator en primer plano
python src/dashboard_soc.py &
python src/main_coordinator.py
```

Dos procesos en un único contenedor: dashboard Flask en background y coordinator MQTT en primer plano (PID 1). Si el coordinator cae, el contenedor termina y `restart: unless-stopped` lo vuelve a levantar.

> **Decisión deliberada de simplicidad.** Producción más estricta separaría cada proceso en su propio contenedor. Para el MVP con un único host y monitorización ligera, un contenedor es suficiente.

## 6. Perfiles de IA

Dos formas de alimentar a los agentes:

### 6.1 Gemini API (default, recomendado)

```ini
AI_MODE=api
AI_MODEL=gemini-3.1-flash
GEMINI_API_KEY=AIza...
```

- Latencia ~1-3 s por inferencia.
- Coste por token. Modelos Gemini 3.1 son baratos pero medibles.
- Calidad alta, requiere conexión a Internet.

### 6.2 Ollama local (perfil `local-ai`)

```ini
AI_MODE=local
AI_MODEL=ollama/gemma4:2b     # ó cualquier modelo descargado en Ollama
```

```bash
docker compose --profile local-ai up -d --build
# Esto levanta el segundo servicio `local-ai-engine` con Ollama en :11434

# Descargar el modelo después de levantar:
docker exec -it local-ai-engine ollama pull gemma4:2b
```

- Sin coste por token.
- Latencia mayor (depende del hardware; en una Pi 5 con 8 GB RAM y un Gemma 4 2B se va a varias decenas de segundos).
- Sin conexión a Internet (excepto para descargar el modelo la primera vez).
- Calidad inferior a Gemini 3.1 Flash para razonamiento estructurado con tools — usar con prudencia.

Ambos perfiles son intercambiables sin tocar código: solo se cambian `AI_MODE` y `AI_MODEL` en `.env` y se reinicia el contenedor.

## 7. Logs y observabilidad

| Fichero | Contenido | Rotación |
|---------|-----------|----------|
| `coordinator_soc.log` | Eventos MQTT, batches, decisiones del Policy Engine, errores del coordinator | 5 MB × 3 archivos |
| `dashboard_soc.log` | Peticiones Flask, errores HITL/revert, conexiones MQTT del dashboard | 5 MB × 3 archivos |
| Stdout/stderr del contenedor | Mismo contenido + warnings de Python | Lo gestiona Docker |

Lectura rápida desde el host:

```bash
tail -f PI-5/coordinator_soc.log
tail -f PI-5/dashboard_soc.log
docker logs -f soc-coordinator-pi5
```

## 8. Firma de comandos (Ed25519)

Toda orden que el coordinador publica a un sensor lleva firma **Ed25519**. El sensor PI-4 verifica firma + ventana de validez + nonce antes de ejecutar; si algo falla, el comando se rechaza sin ejecución y se devuelve `status: "rejected_signature"` al coordinador. Esto sustituye al sistema anterior de detección reactiva `INTRUSION-COMMAND-INJECTION`.

### 8.1 Generación de claves

```bash
python scripts/generate_signing_keys.py
```

Produce dos archivos:

- `PI-5/certificados/sentinel_pi5_signing.key` — clave privada PEM, gitignored por `*.key`. **Nunca subir a git.**
- `PI-4/Agente de monitorizacion/sentinel_pi5_signing.pub` — clave pública PEM, commiteable en el repo de PI-4.

Para rotar:

```bash
python scripts/generate_signing_keys.py --force
# Copiar la nueva .pub a la PI-4 y reiniciar ambos servicios
```

### 8.2 Formato del payload firmado

```json
{
  "accion": "ejecutar_comando",
  "comando": "sudo iptables -A INPUT -s 192.168.1.50 -j DROP",
  "motivo": "Bloqueo de IP atacante",
  "iat": 1747645000,
  "exp": 1747645060,
  "nonce": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "sig": "<base64 Ed25519>"
}
```

- `iat` / `exp` — ventana de 60 s (configurable en `config.yml: signing.ttl_seconds`). Requiere NTP activo en ambos Pi.
- `nonce` — UUID4. PI-4 mantiene una cache LRU para rechazar reenvíos dentro de la ventana.
- `sig` — Ed25519 sobre el JSON canónico (`sort_keys=True`, `separators=(",", ":")`) sin el campo `sig`.

### 8.3 Configuración

`PI-5/config.yml`:

```yaml
signing:
  private_key_path: "./certificados/sentinel_pi5_signing.key"
  ttl_seconds: 60
```

`PI-4/Agente de monitorizacion/config.yml`:

```yaml
signing:
  public_key_path: "./sentinel_pi5_signing.pub"
```

### 8.4 Comportamiento de rechazo

Si `verify_payload()` falla en PI-4, el sensor publica en `comandos/<device>/out`:

```json
{"sensor": "...", "accion": "...", "comando": "...",
 "status": "rejected_signature", "output": "<motivo>"}
```

El feedback_agent lo procesa como cualquier otro feedback — no es ya un vector de ataque ruidoso, sino una respuesta legítima de "comando descartado por integridad".

## 9. Networking y firewall

Puertos que el coordinador necesita:

| Puerto | Protocolo | Dirección | Para qué |
|--------|-----------|-----------|----------|
| **5000/TCP** | HTTP | inbound LAN | Dashboard Flask |
| **8883/TCP** | MQTT/TLS | outbound a `*.iot.eu-north-1.amazonaws.com` | Tráfico mTLS con AWS IoT Core |
| **11434/TCP** | HTTP | localhost interno | Solo si perfil `local-ai` (Ollama) |
| **443/TCP** | HTTPS | outbound | Solo si `AI_MODE=api` (Gemini API endpoint) |

Si el dashboard se expone fuera de la LAN, **poner un reverse proxy con TLS por delante** (Nginx, Caddy). Flask con HTTP Basic en claro sobre Internet no es seguro. Esa pieza queda fuera del scope del MVP.

## 10. Variables de entorno (referencia)

| Variable | Quién la lee | Valor por defecto | Comentario |
|----------|--------------|-------------------|------------|
| `DASHBOARD_USER` | `dashboard_soc.py` | `admin` | Usuario para HTTP Basic |
| `DASHBOARD_PASSWORD` | `dashboard_soc.py` | (ninguno) | Si está, se hashea al arrancar |
| `DASHBOARD_PASSWORD_HASH` | `dashboard_soc.py` | (ninguno) | Hash pre-computado (preferido) |
| `AI_MODE` | `triage_agent.py`, `feedback_agent.py` | `api` | `local` para Ollama, `api` para Gemini |
| `AI_MODEL` | idem | `gemini-3.1-flash` | Nombre exacto del modelo |
| `GEMINI_API_KEY` | Vertex/Gemini SDK | — | Necesario si `AI_MODE=api` |
| `TZ` | Sistema | `Europe/Madrid` | Para timestamps en logs y BD |

## 11. Primera puesta en marcha (checklist)

```text
[ ] Clonar el repo:
       git clone https://github.com/LopedeVega22/Sentinel-IT.git
[ ] Cargar certificados en PI-5/certificados/:
       - root-CA.crt
       - Pi5-dani.cert.pem
       - Pi5-dani.private.key
[ ] Generar par de firma Ed25519:
       python scripts/generate_signing_keys.py
       (Copiar la .pub resultante al directorio del agente de PI-4)
[ ] Crear PI-5/.env con DASHBOARD_PASSWORD y (si AI_MODE=api) GEMINI_API_KEY.
[ ] Validar PI-5/config.yml: endpoint AWS correcto, db_path, batch sizing.
[ ] sudo ./PI-5/soc_manager.sh → opción 1 (cloud) o 2 (local-ai).
[ ] Abrir http://<ip-pi5>:5000  → autenticarse → confirmar que carga el dashboard.
[ ] Desde Pi-4 o test_local.py: publicar un log en seguridad/<dev>/evento.
[ ] Comprobar en el dashboard que aparece la nueva fila en 5-20 s.
```

## 12. Actualización en caliente

Cambios en código:

```bash
cd PI-5
git pull
docker compose up -d --build   # reconstruye y reinicia con el código nuevo
```

El volumen `soc_pi5_database_persistent` sobrevive al rebuild — la BD no se pierde. Las migraciones de esquema en `database.py` se ejecutan automáticamente al arrancar.

Cambios solo en `config.yml` o en `.env`:

```bash
docker compose restart soc-coordinator-pi5    # sin rebuild
```

## 13. Archivos involucrados

```
PI-5/
├── config.yml                  # Configuración aplicacional (versionada como template)
├── .env                        # Secretos (NO versionado)
├── certificados/               # mTLS de AWS IoT (NO versionado)
│   ├── root-CA.crt
│   ├── Pi5-dani.cert.pem
│   └── Pi5-dani.private.key
├── docker-compose.yml          # Servicios coordinator + (perfil) Ollama
├── Dockerfile                  # Python 3.14-slim + requirements
├── requirements.txt            # Dependencias Python
├── scripts/
│   └── start_services.sh       # Lanza dashboard + coordinator en el contenedor
├── soc_manager.sh              # CLI interactivo de gestión
└── Policy.json                 # Referencia local de la Policy IAM aplicada en AWS
```
