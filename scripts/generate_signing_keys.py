"""
Genera un par Ed25519 para firmar comandos PI-5 -> PI-4.

Salida:
  PI-5/certificados/sentinel_pi5_signing.key  (privada, gitignored)
  PI-4/Agente de monitorizacion/sentinel_pi5_signing.pub  (publica, commiteable)

Uso:
  python scripts/generate_signing_keys.py
  python scripts/generate_signing_keys.py --force   (sobreescribe si existen)

Rotacion:
  Borrar ambos ficheros y volver a ejecutar. Recordar reiniciar tanto el
  coordinador (PI-5) como el agente (PI-4) tras rotar.
"""

import argparse
import os
import sys

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PRIV_PATH = os.path.join(REPO_ROOT, "PI-5", "certificados", "sentinel_pi5_signing.key")
PUB_PATH = os.path.join(
    REPO_ROOT, "PI-4", "Agente de monitorizacion", "sentinel_pi5_signing.pub"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true",
                        help="Sobreescribe claves existentes (rotacion)")
    args = parser.parse_args()

    for path in (PRIV_PATH, PUB_PATH):
        if os.path.exists(path) and not args.force:
            print(f"[ERROR] Ya existe {path}. Usa --force para rotar.", file=sys.stderr)
            return 1

    os.makedirs(os.path.dirname(PRIV_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(PUB_PATH), exist_ok=True)

    private_key = Ed25519PrivateKey.generate()
    priv_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    with open(PRIV_PATH, "wb") as f:
        f.write(priv_pem)
    try:
        os.chmod(PRIV_PATH, 0o600)
    except OSError:
        pass

    with open(PUB_PATH, "wb") as f:
        f.write(pub_pem)

    print(f"[OK] Privada -> {PRIV_PATH}")
    print(f"[OK] Publica -> {PUB_PATH}")
    print()
    print("Distribucion:")
    print("  * La privada queda en PI-5 (gitignored). NO la subas a git.")
    print("  * La publica vive con el agente de PI-4. Es segura para commit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
