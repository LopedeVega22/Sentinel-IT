import asyncio
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from agents.triage_agent.triage_agent import triage_agent
from tools.iot_tools import init_iot_tools

# Configuracion del entorno de prueba
load_dotenv()
os.environ["ADK_TEST_MODE"] = "true"

class MockIotClient:
    """Cliente IoT simulado para capturar publicaciones de herramientas."""
    def publish(self, topic, payload):
        print(f"\n[MOCK MQTT] Publicando en {topic}: {payload}")

async def run_test():
    print("Iniciando prueba local de ADK con triage_agent...")
    
    # Inyeccion de dependencia: cliente IoT simulado
    init_iot_tools(MockIotClient())
    
    # Simulacion de log de ataque para el agente
    log_ataque = """{
  "evento": "SQL_INJECTION",
  "prioridad": "CRITICA",
  "sensor": "Pi4-Felix",
  "timestamp": "2026-04-14 18:06:30",
  "ip": "192.168.1.134",
  "usuario": "Admin",
  "email_raw": "admin@cybergard.com' UNION SELECT 1, 'Admin', '202cb962ac59075b964b07152d234b70', 'admin' -- -",
  "patron": "UNION SELECT"
}"""
    user_input = f"Analiza este log:\nDispositivo Origen: Pi4-Felix\nLog crudo: '{log_ataque}'"
    
    # Configuracion del ciclo de ejecucion del agente ADK
    session_service = InMemorySessionService()
    session = await session_service.create_session(user_id="test_user", app_name="test_app")
    runner = Runner(agent=triage_agent, session_service=session_service, app_name="test_app")
    
    from google.genai import types
    
    print("\n--- INICIO DEL ANALISIS ---")
    async for event in runner.run_async(
        user_id="test_user",
        session_id=session.id,
        new_message=types.Content(role="user", parts=[types.Part.from_text(text=user_input)])
    ):
        if event.content and event.content.parts:
            print(f"[AGENTE]: {event.content.parts[0].text}")
            
        calls = event.get_function_calls()
        if calls:
            for call in calls:
                print(f"[HERRAMIENTA - LLAMADA]: {call.name} con args: {call.args}")
        
        resps = event.get_function_responses()
        if resps:
            for resp in resps:
                print(f"[HERRAMIENTA - RESPUESTA]: {resp}")
        
        if getattr(event, 'is_final', False) or (event.actions and event.actions.end_of_agent):
             print(f"\n[ANALISIS FINALIZADO]")
            
    print("--- FIN DEL ANALISIS ---")

if __name__ == "__main__":
    asyncio.run(run_test())
