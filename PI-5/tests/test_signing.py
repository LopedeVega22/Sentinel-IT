"""
Tests del modulo de firma PI-5/src/tools/signing.py y del verificador
PI-4/Agente de monitorizacion/signing.py.

Verifican el contrato end-to-end:
  * Round-trip sign/verify funciona.
  * Modificar el payload tras firmarlo invalida la firma.
  * Un comando expirado se rechaza.
  * Reenviar el mismo nonce dos veces se rechaza.
  * Cargar una clave que no es Ed25519 falla con mensaje claro.
"""

import importlib.util
import os
import sys
import time

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.rsa import generate_private_key

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PI5_TOOLS_DIR = os.path.join(REPO_ROOT, "PI-5", "src", "tools")
PI4_AGENT_DIR = os.path.join(REPO_ROOT, "PI-4", "Agente de monitorizacion")


def _load_module(name: str, path: str):
    """Carga un .py por ruta absoluta; util porque PI-5 y PI-4 tienen un
    fichero `signing.py` cada uno y no queremos colisiones de nombre."""
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def pi5_signing():
    return _load_module("pi5_signing", os.path.join(PI5_TOOLS_DIR, "signing.py"))


@pytest.fixture
def pi4_signing():
    mod = _load_module("pi4_signing", os.path.join(PI4_AGENT_DIR, "signing.py"))
    # Cada test estrena su propia cache de nonces para aislamiento.
    mod._seen_nonces.clear()
    return mod


@pytest.fixture
def keypair(tmp_path):
    """Genera un par Ed25519 y lo escribe en tmp_path como PEM."""
    priv = Ed25519PrivateKey.generate()
    priv_path = tmp_path / "test.key"
    pub_path = tmp_path / "test.pub"
    priv_path.write_bytes(priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ))
    pub_path.write_bytes(priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ))
    return str(priv_path), str(pub_path)


def test_sign_and_verify_roundtrip(pi5_signing, pi4_signing, keypair):
    priv_path, pub_path = keypair
    pi5_signing.load_private_key(priv_path)
    pi4_signing.load_public_key(pub_path)

    payload = {"accion": "ejecutar_comando", "comando": "ls /tmp", "motivo": "test"}
    signed = pi5_signing.sign_payload(payload)

    assert {"iat", "exp", "nonce", "sig"}.issubset(signed.keys())
    ok, motivo = pi4_signing.verify_payload(signed)
    assert ok, f"verificacion deberia pasar: {motivo}"


def test_tampered_command_is_rejected(pi5_signing, pi4_signing, keypair):
    priv_path, pub_path = keypair
    pi5_signing.load_private_key(priv_path)
    pi4_signing.load_public_key(pub_path)

    signed = pi5_signing.sign_payload({"accion": "ejecutar_comando", "comando": "ls /tmp"})
    signed["comando"] = "rm -rf /"  # Atacante muta el comando tras firmarlo

    ok, motivo = pi4_signing.verify_payload(signed)
    assert not ok
    assert "firma" in motivo.lower()


def test_expired_command_is_rejected(pi5_signing, pi4_signing, keypair, monkeypatch):
    priv_path, pub_path = keypair
    pi5_signing.load_private_key(priv_path)
    pi4_signing.load_public_key(pub_path)

    # Forzamos un TTL negativo: el payload nace expirado.
    signed = pi5_signing.sign_payload({"comando": "ls"}, ttl_seconds=-3600)
    # Sin nonce cache pollution previa.
    pi4_signing._seen_nonces.clear()

    ok, motivo = pi4_signing.verify_payload(signed)
    assert not ok
    assert "expirado" in motivo.lower()


def test_replay_same_nonce_is_rejected(pi5_signing, pi4_signing, keypair):
    priv_path, pub_path = keypair
    pi5_signing.load_private_key(priv_path)
    pi4_signing.load_public_key(pub_path)

    signed = pi5_signing.sign_payload({"comando": "ls"})

    ok1, _ = pi4_signing.verify_payload(signed)
    ok2, motivo2 = pi4_signing.verify_payload(signed)
    assert ok1 is True
    assert ok2 is False
    assert "nonce" in motivo2.lower()


def test_missing_signature_is_rejected(pi5_signing, pi4_signing, keypair):
    _, pub_path = keypair
    pi4_signing.load_public_key(pub_path)
    ok, motivo = pi4_signing.verify_payload({"comando": "ls"})
    assert not ok
    assert "sig" in motivo.lower()


def test_non_ed25519_key_raises(pi5_signing, tmp_path):
    rsa = generate_private_key(public_exponent=65537, key_size=2048)
    bad = tmp_path / "rsa.key"
    bad.write_bytes(rsa.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ))
    with pytest.raises(TypeError):
        pi5_signing.load_private_key(str(bad))


def test_sign_without_loaded_key_raises(pi5_signing):
    # Limpiamos cualquier estado previo de otros tests.
    pi5_signing._private_key = None
    pi5_signing._private_key_path = None
    with pytest.raises(pi5_signing.SigningNotInitializedError):
        pi5_signing.sign_payload({"comando": "ls"})
