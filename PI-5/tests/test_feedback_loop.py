import asyncio
import os
import sys
import json
import sqlite3
import time
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from agents.triage_agent.triage_agent import triage_agent
from agents.feedback_agent.feedback_agent import feedback_agent
from tools.iot_tools import init_iot_tools

# Configuracion del entorno de prueba
load_dotenv()
os.environ["ADK_TEST_MODE"] = "true"

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'soc_data.db'))

class MockIotClient:
    """Cliente IoT simulado para interceptar comandos dirigidos a la Pi 4."""
    def __init__(self):
        self.commands_sent = []

    def publish(self, topic, payload):
        print(f"\n[MOCK MQTT] Interceptado en {topic}: {payload}")
        self.commands_sent.append(payload)

async def test_feedback_agent(session_service, runner_fb, session, device, status, output):
    print(f"\n--- INICIO DE PRUEBA FEEDBACK: {status.upper()} ---")
    mock_feedback = f"""
sensor: {device}
command: echo 'test'
status: {status}
output: {output}
"""
    from google.genai import types
    
    async for event in runner_fb.run_async(
        user_id="test_user",
        session_id=session.id,
        new_message=types.Content(role="user", parts=[types.Part.from_text(text=mock_feedback)])
    ):
        if event.content and event.content.parts:
            print(f"[FEEDBACK AGENTE]: {event.content.parts[0].text}")
            
        calls = event.get_function_calls()
        if calls:
            for call in calls:
                print(f"[FEEDBACK HERRAMIENTA - LLAMADA]: {call.name} con args: {call.args}")
        
        resps = event.get_function_responses()
        if resps:
            for resp in resps:
                print(f"[FEEDBACK HERRAMIENTA - RESPUESTA]: {resp}")
                
    print(f"--- FIN DE PRUEBA FEEDBACK: {status.upper()} ---")

async def run_test():
    print("==================================================================")
    print("   🛡️  TEST DE CICLO DE FEEDBACK (TRIAGE -> PI 4 -> FEEDBACK)  ")
    print("==================================================================")
    
    mock_iot = MockIotClient()
    init_iot_tools(mock_iot)
    
    session_service = InMemorySessionService()
    session_triage = await session_service.create_session(user_id="test_user", app_name="test_app_triage")
    runner_triage = Runner(agent=triage_agent, session_service=session_service, app_name="test_app_triage")
    
    session_fb = await session_service.create_session(user_id="test_user", app_name="test_app_fb")
    runner_fb = Runner(agent=feedback_agent, session_service=session_service, app_name="test_app_fb")
    
    from google.genai import types
    
    # 1. Provocar al agente Triage para que genere una respuesta inicial
    print("\n[PASO 1] Provocando al Triage Agent para que envíe un comando a la Pi 4...")
    log_ataque = """{
  "evento": "RCE_ATTACK",
  "prioridad": "ALTA",
  "sensor": "Pi4-Test",
  "timestamp": "2026-04-27 20:00:00",
  "ip": "10.0.0.55",
  "usuario": "www-data",
  "email_raw": "POST /api/exec HTTP/1.1",
  "patron": "Command Injection"
}"""
    user_input = f"Analiza este log:\nDispositivo Origen: Pi4-Test\nLog crudo: '{log_ataque}'\nDebes usar execute_remote_command para detener el servicio nginx."
    
    async for event in runner_triage.run_async(
        user_id="test_user",
        session_id=session_triage.id,
        new_message=types.Content(role="user", parts=[types.Part.from_text(text=user_input)])
    ):
        pass # Solo esperamos a que llame a la herramienta
        
    print("\n[PASO 2] Simulando que la Pi 4 ejecuta el comando y responde que TODO FUE BIEN (Válido)...")
    await test_feedback_agent(session_service, runner_fb, session_fb, "Pi4-Test", "success", "nginx.service successfully stopped.")
    
    print("\n[PASO 3] Simulando que la Pi 4 ejecuta otro comando y da ERROR (No válido), obligando a corregir...")
    await test_feedback_agent(session_service, runner_fb, session_fb, "Pi4-Test", "error", "Failed to stop nginx: Unit nginx.service not loaded.")
    
    print("\n[PASO 4] Comprobando la Base de Datos...")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, dispositivo, log_original, accion_tomada, estado_mitigacion FROM logs ORDER BY id DESC LIMIT 5")
        rows = cursor.fetchall()
        print("\n--- ÚLTIMOS 5 REGISTROS EN LA BASE DE DATOS ---")
        for row in rows:
            print(f"ID: {row[0]} | Dispositivo: {row[1]} | Accion: {row[3]} | Estado: {row[4]}")
        conn.close()
    except Exception as e:
        print(f"Error al leer la base de datos: {e}")

if __name__ == "__main__":
    asyncio.run(run_test())
