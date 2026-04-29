# Arquitectura del SOC Autónomo basado en IA Distribuida

Este proyecto (Trabajo de Fin de Grado) consiste en un Centro de Operaciones de Seguridad (SOC) distribuido, diseñado para ejecutarse en una red de dispositivos de bajo consumo (Raspberry Pi). En lugar de reglas estáticas tradicionales, utiliza Agentes de Inteligencia Artificial (Google Gemini + ADK) para procesar logs, decidir si un comportamiento es malicioso y ejecutar medidas de mitigación en tiempo real.

## 1. Topología de Red y Roles

El sistema adopta un modelo de **Coordinación Centralizada con Ejecutores Remotos**.

### A. Nodo Cerebro / Coordinador (Raspberry Pi 5)
Actúa como el centro neurálgico del SOC.
- **Sin captura local:** No lee sus propios logs de sistema, se limita a procesar telemetría.
- **Motor de IA (Agente ADK):** Utiliza un analista de Nivel 1 instanciado bajo el Google Agent Development Kit, que razona los veredictos.
- **Herramientas (Tools):** Dispone de la capacidad algorítmica de enviar órdenes de vuelta (ej. `bloquear_ip`) a otros dispositivos.
- **Interfaz (Dashboard):** Levanta un servidor Flask interno en el puerto 5000 para ofrecer telemetría a un administrador humano.

### B. Nodos Sensores / Ejecutores (Raspberry Pi 4)
Actúan como las terminaciones nerviosas. 
- **Captura:** Monitorean sus logs host (como `auth.log` de OpenSSH).
- **Ejecución:** Cuentan con capacidad de ejecutar bloqueos inmediatos a nivel de firewall (`sudo iptables`) cuando el Cerebro se lo instruye.

### C. Capa de Mensajería y Transporte (MQTT Segura)
Todo el ecosistema se intercomunica a través de **AWS IoT Core**.
- Implementa autenticación mutua (mTLS) garantizando que ningún dispositivo no autorizado inyecte logs o escuche órdenes defensivas.
- Todo viaja por los topics MQTT genéricos configurados en el proyecto.

## 2. Nueva Estructura Modular Profesional (GitOps)

El entorno del Coordinador (`pi5-dani`) está fuertemente estructurado bajo estándares de microservicios:

```text
/pi5-dani/
 ├── Dockerfile                  (Construcción agnóstica del motor)
 ├── requirements.txt            (Dependencias siempre instaladas en >Latest)
 ├── start_services.sh           (Entrada de ejecución concurrente)
 ├── config.yml                  (Ajustes y constantes unificadas)
 │
 ├── src/                        (CÓDIGO FUENTE AISLADO)
 │    ├── main_coordinator.py    (Script inyector)
 │    ├── dashboard_soc.py       (Web de control y reversiones)
 │    ├── base_datos.py          (Esquema automático de SQLite)
 │    ├── aws_connector.py       (Cliente asíncrono AWS IoT)
 │    ├── agents/                (Contiene el 'Prompt' analítico del soc_agent)
 │    ├── tools/                 (Modificadores físicos: iptables, sqlite_logs)
 │    └── templates/             (HTML Rendering del dashboard)
 │
 └── tests/                      (PRUEBAS AISLADAS)
      ├── test_adk.py            (Mock testing off-line sin gastar tokens)
      └── ...
```

La política de código estipula que TODO este directorio sea hermético. No contiene cachés ni credenciales; todo el contenido es **programación pura lista para GitHub**.
