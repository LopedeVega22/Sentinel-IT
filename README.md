# TFG: Arquitectura de Seguridad IoT distribuida en AWS

## Descripción General

Este repositorio/carpeta centraliza la documentación y el código para el Trabajo de Fin de Grado (TFG) basado en la comunicación segura mediante AWS IoT Core entre dos nodos con Raspberry Pi.

- **Casa 1 (Compañero):** Raspberry Pi 4 (Nodo Protegido). Ejecuta monitorización, auditoría, backups y servicios web (Nginx / SSH). Envía eventos.
- **AWS IoT Core:** Eje central de comunicación, encargado de validar y retransmitir los mensajes mediante protocolos seguros (MQTT/TLS).
- **Casa 2 (Tu Casa):** Raspberry Pi 5 (Nodo Coordinador). Ejecuta el Agente ADK, gestiona respuestas, genera informes, y aloja la Base de Datos y la API.

## Estructura del Proyecto

- `/docs`: Documentación detallada dividida por fases (Requisitos, Arquitectura, Pruebas, Despliegue).
- `/pi4-felix`: Scripts, configuración y agente de monitorización para la Raspberry Pi 4 (Nodo Sensor).
- `/pi5-dani`: Scripts de la API, Agente ADK, conexión a la Base de Datos y Dashboard Web para la Raspberry Pi 5 (Nodo Coordinador).
- `docker-compose.yml`: Orquestación Docker para desplegar ambos nodos.
- `simulador_ataque.py`: Script de simulación de ataque SSH de fuerza bruta para demostraciones.
