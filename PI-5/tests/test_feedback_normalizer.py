"""
Tests del normalizador de feedback PI-4 -> formato canonico para el LLM.

El normalizador vive en PI-5/src/main_coordinator.py, pero main_coordinator
arranca clientes AWS al importarse, asi que aqui cargamos solo las dos
funciones puras (_normalize_pi4_feedback y _format_normalized_feedback)
inyectando un stub para los imports pesados antes de ejecutarlas.
"""

import importlib.util
import os
import sys
import types

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
COORDINATOR_PATH = os.path.join(REPO_ROOT, "PI-5", "src", "main_coordinator.py")


@pytest.fixture(scope="module")
def normalizer():
    """
    Cargamos main_coordinator.py como modulo pero stubeamos las dependencias
    de runtime (AWS IoT, ADK, agentes) — solo nos interesan dos funciones
    sincronas. Esto es mucho mas barato que montar la sesion ADK real.
    """
    # Stubs para que el import de main_coordinator no levante servicios.
    stubs = {
        "aws_connector": types.SimpleNamespace(AWSMqttClient=object),
        "agents.triage_agent.triage_agent": types.SimpleNamespace(triage_agent=object()),
        "agents.feedback_agent.feedback_agent": types.SimpleNamespace(feedback_agent=object()),
        "tools.iot_tools": types.SimpleNamespace(init_iot_tools=lambda *a, **kw: None),
    }
    # Stub minimo del SDK de google.adk para que las llamadas de modulo no
    # exploten: solo necesitamos que `Runner` exista y que crear sesion no
    # falle. InMemorySessionService devuelve un objeto con .id.
    class _DummySession:
        id = "test-session"

    class _DummySessionService:
        def create_session(self, app_name, user_id):
            async def coro():
                return _DummySession()
            return coro()

    class _DummyRunner:
        def __init__(self, *a, **kw):
            pass

    stubs["google.adk.runners"] = types.SimpleNamespace(Runner=_DummyRunner)
    stubs["google.adk.sessions"] = types.SimpleNamespace(InMemorySessionService=_DummySessionService)
    stubs["google.genai"] = types.SimpleNamespace(types=types.SimpleNamespace(
        Content=lambda **kw: None, Part=lambda **kw: None,
    ))

    saved = {k: sys.modules.get(k) for k in stubs}
    sys.modules.update(stubs)

    # Anadir src al path para que `from aws_connector import ...` resuelva
    # al stub (que toma precedencia gracias a sys.modules).
    src_dir = os.path.join(REPO_ROOT, "PI-5", "src")
    sys.path.insert(0, src_dir)

    # Hay que ejecutar main_coordinator desde su directorio porque abre
    # config.yml con ruta relativa.
    cwd_saved = os.getcwd()
    os.chdir(os.path.join(REPO_ROOT, "PI-5"))
    try:
        spec = importlib.util.spec_from_file_location("main_coordinator", COORDINATOR_PATH)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["main_coordinator"] = mod
        spec.loader.exec_module(mod)
    finally:
        os.chdir(cwd_saved)
        sys.path.remove(src_dir)
        # Restaurar stubs originales para no contaminar otros tests.
        for k, v in saved.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v

    return mod


def test_success_pi4_v3_shape(normalizer):
    data = {
        "sensor": "Pi4-Felix",
        "tipo": "RESULTADO_COMANDO",
        "comando": "ls /tmp",
        "resultado": {"exitcode": 0, "stdout": "file1\nfile2\n", "stderr": "", "timed_out": False},
    }
    norm = normalizer._normalize_pi4_feedback(data)
    assert norm == {
        "sensor": "Pi4-Felix",
        "command": "ls /tmp",
        "status": "success",
        "output": "file1\nfile2\n",
        "exitcode": 0,
    }


def test_error_with_stderr(normalizer):
    data = {
        "sensor": "Pi4-Felix",
        "comando": "cat /etc/shadow",
        "resultado": {"exitcode": 1, "stdout": "", "stderr": "Permission denied", "timed_out": False},
    }
    norm = normalizer._normalize_pi4_feedback(data)
    assert norm["status"] == "error"
    assert norm["output"] == "Permission denied"
    assert norm["exitcode"] == 1


def test_timeout_is_error(normalizer):
    data = {
        "sensor": "Pi4-Felix",
        "comando": "sleep 60",
        "resultado": {"exitcode": -1, "timed_out": True},
    }
    norm = normalizer._normalize_pi4_feedback(data)
    assert norm["status"] == "error"
    assert "timeout" in norm["output"].lower()


def test_rejected_signature_preserved(normalizer):
    data = {
        "sensor": "Pi4-Felix",
        "comando": "iptables -A INPUT ...",
        "status": "rejected_signature",
        "resultado": {"error": "firma Ed25519 invalida", "exitcode": -1},
    }
    norm = normalizer._normalize_pi4_feedback(data)
    assert norm["status"] == "rejected_signature"
    assert norm["output"] == "firma Ed25519 invalida"
    assert norm["exitcode"] == -1


def test_legacy_flat_shape(normalizer):
    """Simulador antiguo / agente_monitor.py legacy."""
    data = {
        "sensor": "Pi4-Felix",
        "comando": "ls",
        "status": "success",
        "output": "ok",
    }
    norm = normalizer._normalize_pi4_feedback(data)
    assert norm["status"] == "success"
    assert norm["output"] == "ok"
    assert norm["exitcode"] == 0


def test_unknown_shape_returns_none(normalizer):
    # Sin 'resultado' ni 'status', no podemos clasificar.
    norm = normalizer._normalize_pi4_feedback({"sensor": "X", "comando": "ls"})
    assert norm is None


def test_output_is_truncated(normalizer):
    huge = "A" * 5000
    data = {
        "sensor": "Pi4-Felix",
        "comando": "yes",
        "resultado": {"exitcode": 0, "stdout": huge, "stderr": "", "timed_out": False},
    }
    norm = normalizer._normalize_pi4_feedback(data)
    assert len(norm["output"]) < 5000
    assert "truncado" in norm["output"]


def test_format_normalized_feedback_layout(normalizer):
    norm = {
        "sensor": "Pi4-Felix", "command": "ls", "status": "success",
        "exitcode": 0, "output": "ok",
    }
    text = normalizer._format_normalized_feedback(norm)
    assert text.startswith("sensor: Pi4-Felix")
    assert "\nstatus: success\n" in text
    assert "\nexitcode: 0\n" in text
    assert text.endswith("output: ok")
