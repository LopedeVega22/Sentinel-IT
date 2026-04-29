# Sentinel IT – Plataforma de Seguridad Distribuida

## Descripción

Sentinel IT es un proyecto desarrollado como **TFG del ciclo ASIR** que implementa una plataforma de **monitorización, detección y respuesta automática ante incidentes de seguridad** utilizando dos **Raspberry Pi** conectadas mediante **AWS IoT Core** con comunicación **MQTT cifrada con TLS**.

El sistema simula un entorno real donde un servidor expone varios servicios a usuarios externos mientras otro nodo analiza la actividad y responde automáticamente ante posibles amenazas.

---

## Arquitectura

<img width="765" height="509" alt="image" src="https://github.com/user-attachments/assets/7f6b5126-daee-42f7-b55f-f545c1c53793" />


El sistema está compuesto por dos nodos:

### Raspberry Pi 4 – Nodo protegido
Servidor accesible por los usuarios que ejecuta varios servicios:

- Servidor web (Apache / Nginx)
- FTP (vsftpd)
- SSH
- Base de datos MariaDB
- DNS local (dnsmasq)
- Proxy inverso
- Web honeypot para pruebas de seguridad

Este nodo genera logs y envía eventos de seguridad al sistema de análisis.

### Raspberry Pi 5 – Nodo coordinador
Encargado de analizar los eventos recibidos y ejecutar respuestas automáticas:

- Agente de seguridad basado en **ADK**
- Recepción de eventos mediante **AWS IoT Core**
- Clasificación de incidentes
- Generación de informes
- Gestión de copias de seguridad

---

## Funcionamiento

1. Los usuarios acceden a los servicios del servidor.
2. Los servicios generan logs de actividad.
3. Se detectan eventos relevantes de seguridad.
4. Los eventos se envían mediante AWS IoT Core.
5. El nodo coordinador analiza la amenaza y ejecuta acciones si es necesario.

---

## Tecnologías utilizadas

**Hardware**

- Raspberry Pi 4
- Raspberry Pi 5

**Software**

- Raspberry Pi OS
- Python
- PHP
- MariaDB
- Apache / Nginx
- vsftpd
- dnsmasq

**Cloud**

- AWS IoT Core
- MQTT
- TLS

---

## Autores

Daniel Alarcón Perea  
Félix Tejedor Zapatero  

TFG – Administración de Sistemas Informáticos en Red  
Salesianos de Atocha
