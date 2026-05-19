"""
Firma de comandos PI-5 -> PI-4 con Ed25519.

Cada payload publicado al sensor lleva cuatro campos adicionales:

    iat   (issued at, unix seconds)
    exp   (expires at, unix seconds; ventana de 60 s por defecto)
    nonce (uuid4, anti-replay)
    sig   (base64 de la firma Ed25519 sobre el JSON canonico sin `sig`)

El JSON canonico se construye con sort_keys=True y separators=(",", ":")
para garantizar que ambos extremos serialicen exactamente los mismos bytes.

PI-4 carga unicamente la clave publica y verifica firma + ventana de tiempo
+ nonce no visto antes. Comprometer PI-4 no permite forjar comandos.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import time
import uuid
from typing import Optional

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

logger = logging.getLogger("CoordinatorSOC")

# Campos que se inyectan al payload. NO incluir aqui 'sig' (se firma sobre
# el resto y se anade despues).
_SIGNED_FIELDS = ("iat", "exp", "nonce")

# Ventana de validez por defecto. Si el reloj de PI-4 se desfasa mas que
# esto, los comandos se rechazaran -> mantener NTP activo en ambos lados.
DEFAULT_TTL_SECONDS = 60

_private_key: Optional[Ed25519PrivateKey] = None
_private_key_path: Optional[str] = None


class SigningNotInitializedError(RuntimeError):
    """Se intento firmar antes de cargar la clave privada."""


def load_private_key(path: str) -> None:
    """
    Carga la clave privada Ed25519 desde un PEM en disco. Idempotente:
    llamar varias veces con la misma ruta es seguro.
    """
    global _private_key, _private_key_path
    abs_path = os.path.abspath(path)
    if _private_key is not None and _private_key_path == abs_path:
        return

    with open(abs_path, "rb") as f:
        key = serialization.load_pem_private_key(f.read(), password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise TypeError(
            f"La clave en {abs_path} no es Ed25519 (es {type(key).__name__})."
        )
    _private_key = key
    _private_key_path = abs_path
    logger.info(f"[SIGN] Clave privada Ed25519 cargada desde {abs_path}")


def sign_payload(payload: dict, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> dict:
    """
    Devuelve un nuevo dict con iat/exp/nonce/sig anadidos.

    No muta el dict original. Lanza SigningNotInitializedError si nadie ha
    llamado a load_private_key() antes.
    """
    if _private_key is None:
        raise SigningNotInitializedError(
            "load_private_key() no se ha llamado todavia."
        )

    now = int(time.time())
    signed = dict(payload)
    signed["iat"] = now
    signed["exp"] = now + ttl_seconds
    signed["nonce"] = str(uuid.uuid4())

    message = _canonical_bytes(signed)
    signature = _private_key.sign(message)
    signed["sig"] = base64.b64encode(signature).decode("ascii")
    return signed


def _canonical_bytes(payload: dict) -> bytes:
    """
    Serializa el payload de forma deterministica para que PI-5 y PI-4
    obtengan exactamente los mismos bytes a firmar/verificar. El campo
    'sig' se excluye porque se calcula a partir del resto.
    """
    to_sign = {k: v for k, v in payload.items() if k != "sig"}
    return json.dumps(to_sign, sort_keys=True, separators=(",", ":")).encode("utf-8")
