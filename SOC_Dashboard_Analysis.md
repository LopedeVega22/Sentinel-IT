# Análisis Completo del Dashboard SOC (Sentinel-IT)

## 1. Introducción
Este documento detalla un análisis profundo del código fuente asociado al Dashboard SOC del proyecto Sentinel-IT, abarcando los archivos `dashboard_soc.py` (backend) e `index.html` (frontend). Se ha evaluado la funcionalidad real del código, identificando tanto las características que operan correctamente como aquellas que no tienen un uso real. Finalmente, se proponen mejoras a nivel funcional y de diseño UI/UX.

---

## 2. Funcionalidades Activas y Útiles
Los siguientes componentes tienen una implementación completa y aportan valor directo al sistema:
- **Live Threat Feed (Tabla de Eventos):** Se nutre correctamente desde la base de datos y presenta los últimos incidentes.
- **Sistema HITL (Human-in-the-Loop):** El flujo para aprobar o rechazar comandos mitigadores desde el Dashboard está completo; el endpoint `/api/mitigate/approve` se comunica vía MQTT de forma funcional.
- **Refresco Dinámico (AJAX):** El mecanismo que solicita `/api/data` cada 5 segundos y manipula el DOM es excelente para evitar recargas de la página y mantener la estética de la aplicación.
- **Métricas de BD (KPIs):** Las consultas de total de logs, logs críticos y bloqueos en `get_db_stats()` son eficaces y se representan de forma óptima.
- **Topología de Red Dinámica:** El uso de ECharts en `get_topology_data()` construye un grafo relacional de los atacantes y el nodo central PI-5 de una manera muy inteligente.

---

## 3. Elementos Inactivos, Desaprovechados o Datos Falsos
Se han encontrado bastantes fragmentos de código, variables y elementos de UI que no tienen un propósito final o están "hardcodeados" con datos falsos que pueden desorientar al usuario.

### 3.1. Funciones de Backend no conectadas al Frontend
1. **Ruta `/revert/<int:log_id>` (Botón fantasma):**
   - **Estado:** Existe la lógica completa en el backend para revertir una acción (envía `iptables -D` por MQTT y cambia el estado en DB a `[REVERTIDO]`). Sin embargo, **no existe ningún botón en `index.html`** que active esto.
   - **Solución:** Añadir un botón rojo de "REVERTIR" en la columna *Acción* para los logs cuyo `action` contenga la palabra "bloquear" o "bloqueo".
2. **Variable `unique_vectors`:**
   - **Estado:** La función `get_unique_vectors()` se ejecuta, se calcula y se envía a la vista, pero **jamás se renderiza** en `index.html`.
   - **Solución:** Agregar esta estadística en el panel "Distribución de Vectores" (por ejemplo: *"Se han detectado X vectores únicos en total"*).
3. **Variable `last_seen`:**
   - **Estado:** `get_db_stats()` devuelve el timestamp del último ataque, pero se desperdicia en la plantilla.
   - **Solución:** Colocarlo en la barra superior (Topbar) indicando "Último evento: {last_seen}" para mayor percepción de la actividad en vivo.

### 3.2. Mockups UI sin funcionalidad (Elementos Estáticos)
1. **Barra de Búsqueda (Topbar):**
   - **Estado:** El input `"Buscar IP, hash, dominio..."` es 100% inactivo.
   - **Solución:** Ocultarlo o implementar un script en JS que filtre las filas de la tabla ocultando aquellas que no coincidan con el texto ingresado.
2. **Filtros Temporales (LIVE, 1H, 24H):**
   - **Estado:** Son puramente visuales, no alteran las consultas a SQLite.
   - **Solución:** Modificarlos para enviar un parámetro (`?time=1h`) en el endpoint `/api/data` o quitarlos del diseño.
3. **Menú de Navegación Lateral (Sidebar):**
   - **Estado:** Los botones "Threats" y "Blocked IPs" tienen `href="#"`.
   - **Solución:** Utilizarlos como atajos para filtrar la tabla principal, o simplemente dejarlos y marcarlos visualmente como "próximamente".

### 3.3. Fallbacks de Datos Inseguros (Fake Data)
1. **Fallback de `psutil` en `get_sys_info()`:**
   - **Estado:** Si `psutil` falla, devuelve *18% CPU*, *42% RAM* y un *Uptime falso*. Esto es un anti-patrón en ciberseguridad, ya que reporta falsos positivos sobre la salud del nodo.
   - **Solución:** Enviar valores nulos, `"N/A"` o `"Error"` en el bloque `except` para alertar de que el daemon de métricas ha fallado.
2. **Fallback de ECharts Radar:**
   - **Estado:** Si no hay logs en la base de datos para los vectores, inyecta `Brute Force 45, SQL Injection 30, etc.` en el JS.
   - **Solución:** Si la tabla está limpia, debe inyectarse una matriz vacía para indicar paz, en lugar de falsos ataques.
3. **Indicador "IA AGENT ACTIVE":**
   - **Estado:** La animación verde del sonar siempre corre en bucle asumiendo éxito.
   - **Solución:** Debería apagarse o volverse roja si la conexión MQTT falla o si no hay pings recientes del agente.

---

## 4. Propuestas de Mejora de Diseño y Espacio
1. **Aprovechamiento del Raw Log Viewer:**
   - El clic actual sobre un log largo (clase `log-preview collapsed`) simplemente empuja todo hacia abajo y puede descuadrar la tabla. **Recomendación:** Convertirlo en un enlace que abra un modal exclusivo con fondo oscuro, usando `<pre><code>` para mantener el JSON limpio y coloreado.
2. **Uso de Toasts en lugar de `alert()`:**
   - El sistema HITL usa `alert("Error: ...")` en fallos de red (JS de `submitMitigation`). Esto rompe por completo la atmósfera *Cyber-Glassmorphism*. **Recomendación:** Usar notificaciones "Toast" integradas en el CSS que floten desde abajo.
3. **Gestión de Identidad:**
   - Actualmente, el Dashboard está protegido por `HTTPBasicAuth`, pero muestra de forma estática "SOC Admin" y carece de opciones en la cabecera. Sería un buen toque visual pasar el nombre de usuario autenticado o incluir un dropdown simbólico.
4. **Espacios en Blanco en la Topología:**
   - Cuando no hay eventos, aparece solo un "PI-5 Coordinator" y un falso "PI-4 (Demo)". El área visual se queda muy vacía. Se puede acompañar el panel con estadísticas textuales si el grafo tiene menos de 2 nodos.
