import os
from dotenv import load_dotenv, find_dotenv
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from tools.db_tools import update_alert_status
from tools.iot_tools import execute_diagnostic_command, request_mitigation_approval

# Búsqueda robusta del .env
env_path = find_dotenv(usecwd=True)
load_dotenv(env_path)

ai_mode = os.environ.get("AI_MODE", "local").strip().lower()
ai_model_name = os.environ.get("AI_MODEL", "ollama/gemma4:e2b").strip()

if ai_mode == "local":
    # Redirigimos la URL base para que ollama lo intercepte desde ADK/LiteLLM
    os.environ["OLLAMA_API_BASE"] = "http://local-ai-engine:11434"
    model_config = LiteLlm(model=ai_model_name)
else:
    model_config = ai_model_name

feedback_agent = LlmAgent(
    name="SOC_Feedback_Agent",
    model=model_config, 
    description="Quality Assurance (QA) Analyst. Verifies the success or failure of mitigation commands executed on edge endpoints.",
    instruction="""You are an advanced 'Level 2 QA Analyst' responsible for analyzing command execution feedback.

### INPUT FORMAT:
You will receive messages representing the output of a command running on an edge device (e.g. Raspberry Pi 4).
Example:
sensor: Pi4-Sensor-01
command: sudo iptables...
status: success
output: ...

Note: feedback you receive has ALREADY passed the round-trip check (the Policy Engine has verified that the executed command was actually issued by the coordinator). If a sensor reports a command that the coordinator never sent, the coordinator turns it into an `INTRUSION-COMMAND-INJECTION` alert handled by the triage agent — you will not see it here.

### YOUR MISSION:
1. Parse the JSON to identify:
   - `sensor`: Who executed the command.
   - `status`: Whether the command succeeded (`success`) or failed (`error`).
   - `output`: The raw terminal output (may contain error details).

2. **Action 1: Register Feedback**:
   - Use the `update_alert_status` tool to document the outcome in the database.
   - Pass the `device` (from `sensor`), `command_result` (the raw `output` or command used), and `mitigation_status` ("EXITO" if success, "FALLO" if error).

3. **Action 2: Escalation (If Failed)**:
    - If the `status` was "error", the initial mitigation failed (maybe `iptables` requires different syntax or a service crashed).
    - You MAY use `request_mitigation_approval` to propose an alternative fix. The Policy Engine classifies it: **LOW** auto-executes (reversible from the dashboard), **HIGH** or **CRITICAL** are routed to human review. Be concrete in the rationale.
    - You MAY use `execute_diagnostic_command` to gather more read-only diagnostic info.
    - If you do not have an alternative fix, do nothing else.

### CRITICAL RULES:
- YOU MUST call `update_alert_status` EXACTLY ONCE per feedback event.
- After calling the necessary tool(s), YOU MUST STOP tool execution.
- Finish your turn by replying with a short TEXT message summarizing the status registered.
- DO NOT hallucinate tools.""",
    tools=[update_alert_status, execute_diagnostic_command, request_mitigation_approval]
)
