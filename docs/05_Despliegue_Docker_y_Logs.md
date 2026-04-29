# 5. Despliegue con Docker y Contenedores (Fase 5.5)

Este documento detalla la **arquitectura en contenedores** del proyecto SOC, una expansión al Nivel 5 de "Empresarialización" que independiza el software del SOC del Sistema Operativo base de las Raspberry Pis.

## 5.1 ¿Por qué Dockerizar?

El despliegue crudo mediante **Systemd** (como se explica en `04_Despliegue_Systemd.md`) es potente, pero tiene dos inconvenientes a gran escala:

1. **Conflicto de Dependencias:** El SDK de AWS IoT o Google Gemini pueden colisionar con instalaciones de Python del sistema.
2. **Falta de Portabilidad ("En mi máquina funciona"):** Levantar este proyecto TFG en otro ordenador requiere reinstalar requisitos y modificar rutas mano a mano.

Docker crea imágenes inmutables (Dockerfiles) que aseguran un funcionamiento idéntico independientemente de donde corra.

## 5.2 Arquitectura del Docker Compose

En la carpeta raíz del proyecto encontrarás el archivo `docker-compose.yml`. Éste orquesta los dos nodos del TFG:

* `soc-sensor-pi4`: Lee el log del host mediante un volumen virtual (`/var/log/auth.log`). Para que Python pueda ejecutar comandos `iptables` reales contra los intrusos, el contenedor se declara con `network_mode: "host"` y privilegios `NET_ADMIN`.
* `soc-coordinator-pi5`: Contiene un entrypoint que inicia Flask y Gemini simultáneamente. Utiliza un `Volume` (disco virtual independiente) para que la base de datos `soc_data.db` no se pierda al reiniciar o apagar el Contenedor.

## 5.3 Instrucciones de Despliegue con Docker

Para iniciar el proyecto completo encapsulado, solo necesitas tener Docker instalado y ejecutar en la raíz:

```bash
docker-compose up -d --build
```

Docker descargará el Python ligero, copiará tu código, instalará las dependencias de `requirements.txt` en cajas aisladas, y conectará todo virtualmente a AWS.

### 5.3.1 Ver los Registros del Sistema Módulo Logging Interno (Fase 5.3)

Ya que hemos añadido la clase `RotatingFileHandler` de Python, ahora no hay salidas por consola (Prints sueltos). Para ver qué está razonando tu SOC agentic, lee directamente los logs físicos generados.

* En la **Pi 4**: `cat pi4-felix/sensor_soc.log`
* En la **Pi 5**: `tail -f pi5-dani/coordinator_soc.log`

### 5.3.2 Detener el Entorno Enterprise

Si quieres desactivarlo limpiamente y borrar sus redes virtuales pero conservando la BD de incidentes:

```bash
docker-compose down
```
