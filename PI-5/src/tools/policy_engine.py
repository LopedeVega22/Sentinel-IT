"""
Policy Engine — Sentinel-IT (PI-5)

Sustituye la blacklist por substring de iot_tools.py por una clasificacion de
comandos en cuatro niveles de riesgo (SAFE_READ / LOW / HIGH / CRITICAL).

Filosofia:
    * Lectura pura se ejecuta sin friccion (incluso `sudo cat /var/log/...`).
    * Escritura acotada pasa por HITL con etiqueta de nivel.
    * Solo lo destructivo no reversible exige doble confirmacion explicita
      desde el dashboard (CRITICAL).
    * Lo desconocido NO se deniega automaticamente: cae a LOW y llega al
      humano. Esto es deliberado para no entorpecer al agente IA.

Capas adicionales:
    * record_dispatch + verify_feedback  -> deteccion de comandos que llegan
      por feedback sin haberse emitido nunca desde PI-5 (round-trip).
    * audit(...)  -> escritura inmutable en la tabla `audit_log`.
"""

from __future__ import annotations

import logging
import os
import re
import shlex
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional

import yaml

logger = logging.getLogger("CoordinatorSOC")

# ---------------------------------------------------------------------------
# Configuracion (ruta a la BD)
# ---------------------------------------------------------------------------
_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
_CONFIG_PATH = os.path.join(_BASE_DIR, 'config.yml')
try:
    with open(_CONFIG_PATH, "r") as _f:
        _config = yaml.safe_load(_f)
    DB_PATH = os.path.join(_BASE_DIR, _config['database']['db_path'])
except Exception:
    DB_PATH = os.path.join(_BASE_DIR, "soc_data.db")


# ---------------------------------------------------------------------------
# Niveles
# ---------------------------------------------------------------------------
class RiskLevel(IntEnum):
    SAFE_READ = 0
    LOW = 1
    HIGH = 2
    CRITICAL = 3

    def label(self) -> str:
        return self.name


@dataclass
class Classification:
    level: RiskLevel
    parsed_verb: str
    reasons: list = field(default_factory=list)
    is_executable_via_interpreter: bool = False

    def to_dict(self) -> dict:
        return {
            "level": self.level.label(),
            "verb": self.parsed_verb,
            "reasons": list(self.reasons),
            "interpreter": self.is_executable_via_interpreter,
        }


@dataclass
class Decision:
    allow_direct: bool          # True solo para SAFE_READ
    classification: Classification

    @property
    def level(self) -> RiskLevel:
        return self.classification.level


# ---------------------------------------------------------------------------
# Catalogos de verbos (heuristica, no whitelist cerrada)
# ---------------------------------------------------------------------------
_READ_VERBS = {
    "cat", "ls", "ll", "grep", "egrep", "fgrep", "ss", "netstat", "ps",
    "journalctl", "tail", "head", "less", "more", "id", "whoami", "uname",
    "df", "du", "free", "uptime", "who", "w", "last", "stat", "file", "wc",
    "hostname", "dig", "host", "nslookup", "ping", "traceroute", "tracepath",
    "awk", "cut", "sort", "uniq", "tr", "env", "printenv", "true", "echo",
    "date", "lsblk", "lsof", "lspci", "lsusb", "iostat", "vmstat", "mpstat",
    "tcpdump",  # solo lectura aunque sea sudo
}

_BOUNDED_WRITE_VERBS = {
    "iptables", "ip6tables", "ufw",
}

_BROAD_WRITE_VERBS = {
    "systemctl", "service", "kill", "pkill", "mount", "umount",
    "chmod", "chown", "useradd", "usermod", "passwd", "iptables-restore",
    "ip", "tc", "sysctl", "modprobe", "rmmod",
}

_DESTRUCTIVE_VERBS = {
    "rm", "dd", "mkfs", "shutdown", "reboot", "halt", "poweroff",
    "userdel", "fdisk", "parted", "wipefs", "shred", "init",
}

_INTERPRETER_VERBS = {"bash", "sh", "zsh", "dash", "ash", "php", "python",
                     "python3", "perl", "ruby", "node", "lua", "eval", "exec"}
_INTERPRETER_EXEC_FLAGS = {"-c", "-e", "-r", "--command", "-x"}  # ejecucion en linea

_SHELL_METACHARS = (";", "&&", "||", "`", "$(", ">", "|")  # presencia cruda en str
# (las pipes legitimas dentro de un solo verbo de lectura son frecuentes y se
#  tratan especial en la deteccion)

_SENSITIVE_WILDCARD_PATHS = ("/etc/", "/boot/", "/sys/", "/proc/", "/var/lib/",
                            "/dev/sd", "/dev/nvme", "/dev/disk", "/root/")

_IP_REGEX = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")


# ---------------------------------------------------------------------------
# Clasificador
# ---------------------------------------------------------------------------
def classify(cmd: str) -> Classification:
    """
    Devuelve una Classification con el nivel inferido del comando.

    No lanza excepciones: cualquier fallo de parseo se traduce a HIGH con la
    razon documentada. La idea es que el humano siempre pueda decidir.
    """
    raw = (cmd or "").strip()
    if not raw:
        return Classification(
            level=RiskLevel.HIGH,
            parsed_verb="",
            reasons=["comando vacio: tratado como HIGH para forzar revision"],
        )

    reasons: list = []

    # --- 1) Tokenizacion con shlex (modo POSIX) ---
    try:
        tokens = shlex.split(raw, posix=True)
    except ValueError as exc:
        # Comillas mal cerradas, escapes raros... Mejor llega al humano.
        return Classification(
            level=RiskLevel.HIGH,
            parsed_verb=raw.split()[0] if raw else "",
            reasons=[f"shlex no pudo parsear: {exc}"],
        )

    if not tokens:
        return Classification(
            level=RiskLevel.HIGH,
            parsed_verb="",
            reasons=["sin tokens tras parseo"],
        )

    # --- 2) Saltar sudo y env ---
    sudo_present = False
    while tokens and tokens[0] in ("sudo", "env"):
        if tokens[0] == "sudo":
            sudo_present = True
        tokens.pop(0)
    if not tokens:
        return Classification(
            level=RiskLevel.HIGH,
            parsed_verb="sudo" if sudo_present else "",
            reasons=["sudo/env aislado, sin verbo siguiente"],
        )

    verb_full = tokens[0]
    verb = os.path.basename(verb_full)  # admite /usr/bin/php o php
    args = tokens[1:]

    # --- 3) Nivel base por verbo ---
    if verb in _READ_VERBS:
        level = RiskLevel.SAFE_READ
        reasons.append(f"verbo de lectura: {verb}")
    elif verb in _DESTRUCTIVE_VERBS:
        level = RiskLevel.CRITICAL
        reasons.append(f"verbo destructivo: {verb}")
    elif verb in _BROAD_WRITE_VERBS:
        level = RiskLevel.HIGH
        reasons.append(f"verbo de escritura amplia: {verb}")
    elif verb in _BOUNDED_WRITE_VERBS:
        level, sub_reasons = _classify_bounded_write(verb, args)
        reasons.extend(sub_reasons)
    elif verb in _INTERPRETER_VERBS:
        level = RiskLevel.LOW
        reasons.append(f"interprete: {verb}")
    else:
        # Desconocido: NUNCA DENY automatico. Cae a LOW. (Respuesta a L63
        # del doc futuras_mejoras.md.)
        level = RiskLevel.LOW
        reasons.append(f"verbo desconocido '{verb}': tratado como LOW")

    if sudo_present:
        reasons.append("ejecucion con sudo")

    # --- 4) Modificadores (escalan nivel) ---
    is_interp = False
    if verb in _INTERPRETER_VERBS:
        # interprete con flag de ejecucion -c / -e / -r -> +2
        if any(a in _INTERPRETER_EXEC_FLAGS for a in args):
            is_interp = True
            level = _bump(level, 2)
            reasons.append("interprete con ejecucion en linea (-c/-e/-r): +2")

    # Metacaracteres en la cadena original (no en tokens, porque shlex los
    # consume). Un `|` o `>` cruzando un solo comando ya es senal de algo
    # mas complejo que conviene escalar.
    extra = _detect_shell_metachars(raw)
    if extra:
        level = _bump(level, 1)
        reasons.append(f"metacaracteres de shell detectados: {', '.join(extra)}")

    # Wildcards en paths sensibles
    if _hits_sensitive_wildcard(args):
        level = _bump(level, 1)
        reasons.append("wildcard sobre path sensible (/etc, /boot, /dev/sd...): +1")

    # Heuristica especifica: `find ... -delete` o `find ... -exec` con verbo destructivo
    if verb == "find":
        if "-delete" in args:
            level = max(level, RiskLevel.HIGH)
            reasons.append("find con -delete")
        if "-exec" in args:
            level = max(level, RiskLevel.HIGH)
            reasons.append("find con -exec")
    # `sed -i` muta archivos
    if verb == "sed" and any(a == "-i" or a.startswith("-i") for a in args):
        level = max(level, RiskLevel.HIGH)
        reasons.append("sed con -i (modificacion in-place)")

    # Verbo destructivo en cualquier posicion del comando (cubre encadenamientos
    # tipo `ls /tmp; rm /tmp/foo` o `cmd && shutdown`).
    extra_destructive = _scan_destructive_anywhere(raw, primary=verb)
    if extra_destructive:
        level = RiskLevel.CRITICAL
        reasons.append(
            f"verbo destructivo encadenado: {', '.join(extra_destructive)}"
        )

    return Classification(
        level=level,
        parsed_verb=verb,
        reasons=reasons,
        is_executable_via_interpreter=is_interp,
    )


def _classify_bounded_write(verb: str, args: list) -> tuple[RiskLevel, list]:
    """
    Casos especiales de iptables/ip6tables/ufw:
        -L / -S / --list / --check   -> SAFE_READ
        -F / --flush sin tabla       -> CRITICAL
        -A / -I / -D INPUT -s <IP>   -> LOW
        cualquier otra cosa          -> HIGH
    """
    reasons: list = []
    if not args:
        reasons.append(f"{verb} sin argumentos: HIGH por defecto")
        return RiskLevel.HIGH, reasons

    flat = " ".join(args)
    # Solo-lectura
    read_flags = ("-L", "-S", "--list", "--check", "-V", "--version")
    if any(a in read_flags for a in args):
        reasons.append(f"{verb} en modo lectura ({flat})")
        return RiskLevel.SAFE_READ, reasons

    # Flush global (peligroso)
    if "-F" in args or "--flush" in args:
        # Si va seguido de un nombre de cadena especifica (INPUT/FORWARD/OUTPUT)
        idx = args.index("-F" if "-F" in args else "--flush")
        target = args[idx + 1] if idx + 1 < len(args) else ""
        if target in ("INPUT", "OUTPUT", "FORWARD"):
            reasons.append(f"{verb} flush de cadena especifica: HIGH")
            return RiskLevel.HIGH, reasons
        reasons.append(f"{verb} flush sin cadena: CRITICAL")
        return RiskLevel.CRITICAL, reasons

    # Append/insert/delete contra una IP
    if any(f in args for f in ("-A", "-I", "-D", "--append", "--insert", "--delete")):
        # Comprobamos que haya una IP en los args (parametro -s <ip>)
        has_ip = any(_IP_REGEX.match(a) for a in args)
        if has_ip:
            reasons.append(f"{verb} regla contra IP concreta: LOW")
            return RiskLevel.LOW, reasons
        reasons.append(f"{verb} regla sin IP concreta: HIGH")
        return RiskLevel.HIGH, reasons

    reasons.append(f"{verb} con flags no clasificados ({flat}): HIGH")
    return RiskLevel.HIGH, reasons


def _detect_shell_metachars(raw: str) -> list:
    """
    Devuelve la lista de metacaracteres relevantes encontrados.

    Las pipes solas (`|`) entre dos lecturas son tan comunes (`ps aux | grep`)
    que no las cuento como senal de escalada salvo que aparezcan junto a otro
    metacaracter. La heuristica es conservadora: ante la duda, escala y deja
    decidir al humano.
    """
    hits = []
    # Quitar contenido entre comillas simples/dobles para no leer metacaracteres
    # que el shell trataria como literales.
    sanitized = re.sub(r"'[^']*'", "''", raw)
    sanitized = re.sub(r'"[^"]*"', '""', sanitized)
    for token in (";", "&&", "||", "`", "$("):
        if token in sanitized:
            hits.append(token)
    # `>` y `>>` solo si redirigen fuera de /tmp o /var/log/sentinel
    redirect = re.search(r">>?\s*(\S+)", sanitized)
    if redirect:
        target = redirect.group(1)
        if not (target.startswith("/tmp/") or target.startswith("/var/log/")):
            hits.append(f"> {target}")
    return hits


def _scan_destructive_anywhere(raw: str, primary: str) -> list:
    """
    Devuelve los verbos destructivos encontrados como palabra completa en el
    comando bruto, excluyendo el verbo principal (que ya se ha contado).

    Cubre encadenamientos del tipo `ls /tmp; rm foo` o `whoami && shutdown`
    que shlex no separa en clauses independientes.
    """
    hits = []
    # Recorrer cada palabra del comando, ignorando contenido entre comillas
    # (no es metodo perfecto pero suficiente para detectar palabras sueltas).
    sanitized = re.sub(r"'[^']*'", "", raw)
    sanitized = re.sub(r'"[^"]*"', "", sanitized)
    for match in re.finditer(r"\b([a-zA-Z_][a-zA-Z0-9_-]*)\b", sanitized):
        word = match.group(1)
        if word == primary:
            continue
        if word in _DESTRUCTIVE_VERBS:
            hits.append(word)
    return hits


def _hits_sensitive_wildcard(args: list) -> bool:
    for a in args:
        if "*" in a or "?" in a:
            for path in _SENSITIVE_WILDCARD_PATHS:
                if path in a:
                    return True
    return False


def _bump(level: RiskLevel, steps: int) -> RiskLevel:
    new = min(int(level) + steps, int(RiskLevel.CRITICAL))
    return RiskLevel(new)


# ---------------------------------------------------------------------------
# Decision
# ---------------------------------------------------------------------------
def decide(cmd: str) -> Decision:
    """
    Solo SAFE_READ permite ejecucion directa. Todo lo demas exige HITL.
    """
    cl = classify(cmd)
    return Decision(allow_direct=(cl.level == RiskLevel.SAFE_READ), classification=cl)


# ---------------------------------------------------------------------------
# Cache de comandos emitidos (round-trip)
# ---------------------------------------------------------------------------
_DISPATCH_TTL_SECONDS = 300  # 5 minutos
_dispatch_lock = threading.Lock()
_dispatch_cache: list = []  # lista de dicts: cmd, device, log_id, ts


def record_dispatch(cmd: str, device: str, log_id: Optional[int] = None) -> None:
    """
    Registra un comando publicado a un dispositivo para verificar despues
    contra el feedback que devuelve PI-4.
    """
    now = time.time()
    with _dispatch_lock:
        _dispatch_cache.append({
            "cmd": _normalize_for_match(cmd),
            "raw": cmd,
            "device": device,
            "log_id": log_id,
            "ts": now,
        })
        # Limpiar entradas viejas
        _dispatch_cache[:] = [
            e for e in _dispatch_cache if now - e["ts"] < _DISPATCH_TTL_SECONDS
        ]


def verify_feedback(executed_cmd: str, device: str) -> str:
    """
    Devuelve 'MATCH' si el comando ejecutado por PI-4 coincide con alguno
    emitido recientemente para ese dispositivo; 'ANOMALY' en otro caso.
    """
    return "MATCH" if match_feedback(executed_cmd, device) else "ANOMALY"


def match_feedback(executed_cmd: str, device: str) -> Optional[dict]:
    """
    Variante de verify_feedback que devuelve la entrada de dispatch completa
    (incluyendo log_id) para correlacionar respuestas de PI-4 con la fila
    original de logs. Devuelve None si no hay match.

    Si hay varios despachos del mismo comando, devuelve el mas reciente
    (es el unico viable, dado que PI-4 no incluye un identificador en su
    respuesta y la cache es FIFO).
    """
    norm = _normalize_for_match(executed_cmd)
    now = time.time()
    best = None
    with _dispatch_lock:
        for entry in _dispatch_cache:
            if entry["device"] != device:
                continue
            if now - entry["ts"] >= _DISPATCH_TTL_SECONDS:
                continue
            if entry["cmd"] != norm:
                continue
            if best is None or entry["ts"] > best["ts"]:
                best = entry
    return dict(best) if best else None


def _normalize_for_match(cmd: str) -> str:
    """
    Normaliza espacios en blanco para comparar comandos sin sufrir por
    espacios extras. No toca el contenido semantico.
    """
    return " ".join((cmd or "").split())


# ---------------------------------------------------------------------------
# Audit log (append-only) — inmutabilidad asegurada por triggers en BD
# ---------------------------------------------------------------------------
def audit(
    event_type: str,
    device: str,
    command: str,
    classification: Optional[Classification] = None,
    decision_reason: str = "",
    related_log_id: Optional[int] = None,
) -> None:
    """
    Inserta una entrada en audit_log. Si la tabla no existe (BD vieja) se
    ignora silenciosamente para no romper el flujo principal.
    """
    cls_label = classification.level.label() if classification else ""
    reasons = ""
    if classification:
        joined = "; ".join(classification.reasons) if classification.reasons else ""
        if decision_reason:
            reasons = f"{decision_reason} | {joined}" if joined else decision_reason
        else:
            reasons = joined
    else:
        reasons = decision_reason

    for attempt in range(3):
        conn = None
        try:
            conn = sqlite3.connect(DB_PATH, timeout=10.0, check_same_thread=False)
            conn.execute('PRAGMA journal_mode=WAL;')
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO audit_log
                    (event_type, device, command, classification, decision_reason, related_log_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (event_type, device, command, cls_label, reasons, related_log_id),
            )
            conn.commit()
            return
        except sqlite3.OperationalError as e:
            msg = str(e).lower()
            if "no such table" in msg:
                logger.warning("[POLICY] audit_log no existe; saltando entrada.")
                return
            if "locked" in msg and attempt < 2:
                time.sleep(1)
                continue
            logger.error(f"[POLICY] No se pudo escribir audit_log: {e}")
            return
        except Exception as e:
            logger.error(f"[POLICY] Error inesperado escribiendo audit_log: {e}")
            return
        finally:
            if conn:
                conn.close()
