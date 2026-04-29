# Módulo 5.1: Despliegue de Servicios (Daemons) Systemd

Para elevar el nivel del proyecto a un entorno de producción (*Enterprise*), los scripts de Python ya no se ejecutarán manualmente. Se han convertido en servicios de sistema (*daemons*) gestionados por `systemd` en Linux.

## Beneficios para el TFG

1. **Arranque Automático:** Si alguna placa se reinicia (ej. corte de luz temporal), el SOC vuelve a levantarse completamente solo en segundos.
2. **Autorrecuperación:** Si por algún casual la API de Gemini falla y el script crashea, Linux lo reiniciará automáticamente.
3. **Trazabilidad:** Podemos leer los logs del sistema de forma limpia invocando `journalctl`.

---

## Automatización de la Instalación (Fase 5.4)

> ⚠️ **Importante:** Como parte de la evolución Enterprise, ya **no es necesario** lanzar comandos línea a línea. Simplemente utiliza nuestro script autodiagnóstico en cada nodo:
> `sudo ./setup.sh`
> Este script se encargará él solo de todo lo descrito a continuación, instalando librerías, comprobando rutas, reemplazando la ruta completa en tu servicio predeterminado y recargando los demonios.

## Instrucciones Manuales de Instalación en las Raspberries Reales (Bajo el capó)

### 1. Pi 4 (Nodo Sensor)

El archivo responsable es `soc-sensor.service`.

**Ejecutar en la terminal de la Pi 4:**

```bash
# 1. Copiar el archivo al directorio de servicios de sistema (requiere sudo)
sudo cp /home/pi/TFG/pi4-felix/soc-sensor.service /etc/systemd/system/

# 2. Recargar los demonios para que Linux detecte el nuevo archivo
sudo systemctl daemon-reload

# 3. Activar el servicio para que arranque en cada inicio del sistema
sudo systemctl enable soc-sensor.service

# 4. Iniciar el servicio ahora mismo
sudo systemctl start soc-sensor.service

# 5. Comprobar que está "Activo (Running)"
sudo systemctl status soc-sensor.service
```

*Para leer los logs del recolector en vivo: `sudo journalctl -u soc-sensor.service -f`*

---

### 2. Pi 5 (Coordinador IA y Dashboard)

Tenemos dos servicios: uno para el Agente (`soc-coordinator.service`) y otro para el Panel de Control Web (`soc-dashboard.service`).

**Ejecutar en la terminal de la Pi 5:**

```bash
# 1. Copiar ambos archivos
sudo cp /home/pi/TFG/pi5-dani/soc-coordinator.service /etc/systemd/system/
sudo cp /home/pi/TFG/pi5-dani/soc-dashboard.service /etc/systemd/system/

# 2. Recargar demonios
sudo systemctl daemon-reload

# 3. Activar que arranquen al encender la Pi 5
sudo systemctl enable soc-coordinator.service
sudo systemctl enable soc-dashboard.service

# 4. Iniciarlos
sudo systemctl start soc-coordinator.service
sudo systemctl start soc-dashboard.service

# 5. Comprobar estados
sudo systemctl status soc-coordinator.service
sudo systemctl status soc-dashboard.service
```

*Para ver cómo piensa el agente de Gemini en tiempo real (logs): `sudo journalctl -u soc-coordinator.service -f`*
