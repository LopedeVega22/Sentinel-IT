import os
import json
from dotenv import load_dotenv, find_dotenv
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from tools.db_tools import register_alert
from tools.iot_tools import execute_diagnostic_command, request_mitigation_approval

# Búsqueda robusta del .env (para docker-compose y directorios relativos)
env_path = find_dotenv(usecwd=True)
load_dotenv(env_path)

# Evaluamos tipo de IA pedida por el script shell (en local es Ollama, en api es la API de GCP)
ai_mode = os.environ.get("AI_MODE", "local").strip().lower()
ai_model_name = os.environ.get("AI_MODEL", "ollama/gemma4:e2b").strip()

print(f"\n[INIT] -----------------------------------------------------------------")
print(f"[INIT] Cargando entorno de triage_agent.py")
print(f"[INIT] .env detectado en: {env_path}")
print(f"[INIT] => AI_MODE configurado a: '{ai_mode}'")
print(f"[INIT] => AI_MODEL configurado a: '{ai_model_name}'")
print(f"[INIT] -----------------------------------------------------------------\n")

if ai_mode == "local":
    # Redirigimos la URL base para que ollama lo intercepte desde ADK/LiteLLM
    os.environ["OLLAMA_API_BASE"] = "http://local-ai-engine:11434"
    model_config = LiteLlm(model=ai_model_name)
else:
    # Usamos modelo remoto normal, tal y como decida el usuario para Vertex/Gemini APIs
    model_config = ai_model_name

# Cargar catálogo de comandos recomendados
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
REC_PATH = os.path.join(BASE_DIR, 'recommendations.json')
try:
    with open(REC_PATH, 'r') as f:
        recommendations_data = json.load(f)
    recs_list = []
    for item in recommendations_data.get("recomendaciones_mitigacion", []):
        cmd = item.get("comando", "").replace("{", "<").replace("}", ">")
        recs_list.append(f"- Ataque: {item.get('ataque', '')}\n  Comando: {cmd}\n  Explicacion: {item.get('explicacion', '')}")
    recommendations_str = "\n\n".join(recs_list)
except Exception as e:
    print(f"[WARNING] No se pudo cargar recommendations.json: {e}")
    recommendations_str = "No hay recomendaciones cargadas."

# Configuracion del Agente SOC bajo el framework ADK
triage_agent = LlmAgent(
    name="SOC_Triage_Agent",
    model=model_config, 
    description="Level 1 Analyst (Triage) specialized in parsing both raw IoT logs and structured JSON telemetry. Evaluate security events, extract source IPs, decide if it's benign or an attack, and apply mitigations securely via Human-in-the-Loop.",
    instruction=f"""You are an advanced 'Level 1 SOC Triage Agent' responsible for analyzing security logs and mitigating threats.

### IOT ENVIRONMENT & RECOMMENDATIONS
Below is the knowledge base of recommended mitigation commands for the PI-4. You can use these exact commands, modify them (e.g. replacing <IP> or flags), or invent entirely new Bash commands based on the context.

{recommendations_str}

### FORENSIC CHAIN-OF-THOUGHT (HOW TO THINK):
Logs will arrive as plain text (SSH) or structured JSON (Web events, telemetry). The logs are delivered in near real-time, meaning the threat is active NOW.
1. **Who & Where**: Extract the source IP or attacking entity, and the target device (e.g., from "sensor").
2. **What & How**: Is it benign or malicious?
3. **Decide Action**: Formulate a response based on severity.

### MITIGATION PROTOCOLS & ZERO TRUST (HITL):

1. **[BENIGN TRAFFIC OR STANDARD TELEMETRY]**:
   - Normal occurrences, expected activity, or routine summary telemetry.
   - **Action**: DO NOTHING. Simply state the traffic is benign. **DO NOT** use `register_alert`.

2. **[SUSPICIOUS OR CONFIRMED ATTACK]**:
   - Clear malicious intent, unauthorized access attempts, active exploits (SQLi, XSS, Brute force).
   - **Action**: 
     - 1. **Mandatory**: Use `register_alert` to document the threat EXACTLY ONCE. CRITICAL: For the `raw_log` parameter, you MUST pass the COMPLETE, EXACT original log text you received as input. Never truncate, summarize, or leave it empty — the dashboard displays this verbatim.
     - 2. **Diagnosis (Optional)**: If you need to check the firewall or process list, use `execute_diagnostic_command` (Read-only commands or allowed sudo like `sudo iptables -L`).
     - 3. **Mitigation**: Use `request_mitigation_approval` to propose a destructive/mutating Bash command (like `sudo iptables -A...` or `kill -9...`). Explain your reasoning clearly in the rationale. DO NOT try to use diagnostic commands for destructive actions.

### CRITICAL EXECUTION RULES:
- Once you call `request_mitigation_approval`, your action is placed in quarantine for a human admin to review. YOU MUST STOP tool execution immediately after.
- Finish your turn by replying with a regular TEXT message summarizing the threat and the mitigation you proposed.
- DO NOT hallucinate tools. Use ONLY the tools provided.""",
    tools=[register_alert, execute_diagnostic_command, request_mitigation_approval]
)
