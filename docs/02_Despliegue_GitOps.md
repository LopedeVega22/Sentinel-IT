# Guía de Despliegue Limpio (GitOps Maintance)

Este clúster de ciberseguridad ya NO usa despliegues clásicos por Systemd (como se hacía en su fase inicial experimental). Ahora funciona exclusivamente como un **Motor de Ejecución Dockerizado**.

El objetivo es no "ensuciar" las Raspberry Pis con código base. Las Pi solo ejecutan lo que GitHub ordene.

## Mantenimiento y Actualizaciones (Ciclo GitOps)

1. En tu portátil personal, abres el código fuente, desarrollas nuevas mejoras en la carpeta `src/`, y guardas los cambios con Git:
   `git commit -m "Nueva feature"` -> `git push`
2. En las Raspberry Pi (producción), **no tocas ni una coma de código**. Solo ejecutas su automatizador de descargas y él arranca la nueva versión empaquetada.

---

## Instrucciones Paso a Paso para la Raspberry Pi 5

Al clonar de cero la máquina o reinstalarla, el disco de la Pi 5 debe estar vacío excepto por las herramientas base.

### Paso 1: Configurar la Jaula de Secretos
Entra a la carpeta del TFG y ejecuta por primera y única vez:
```bash
$ ./setup_credenciales.sh
```
Esto creará una carpeta súper restrictiva en `./certificados/` y un archivo `../.env`.
- Pon dentro de la carpeta los ficheros `*.pem`, `*.key` y `root-CA.crt` que descargas de AWS IoT.
- Edita el `.env` con `nano .env` e introduce tu `GEMINI_API_KEY`.
*(Ojo: Gracias al `.gitignore` gigante que creamos, Git nunca subirá esto a tu repo público).*

### Paso 2: Vincular tu Repo Oficial
El script de arranque necesita saber de qué repositorio de la nube bajar el código.
Abre `arrancar_soc.sh` y edita la primera línea con tu URL final:
```bash
REPO_URL="https://github.com/tu_usuario/tu_tfg.git"
```

### Paso 3: Arrancar el Motor
Invoca al script de arranque en la raíz:
```bash
$ ./arrancar_soc.sh
```
**¿Qué pasa internamente?**
El script crea una carpeta invisible `.soc_engine_src`, baja el último `commit` siliciosamente desde tu GitHub, le inyecta "en caliente" las claves de la jaula segura, usa Docker-Compose para virtualizar e instalar paquetes (`python >=3.13`), y expone tu web en el puerto 5000. 

### Parar y Destruir
Si quieres apagar por completo el sistema y borrar la red interna de Docker:
```bash
$ cd .soc_engine_src
$ docker compose down
```
