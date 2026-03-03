"""
config.py — Configuracion centralizada del proyecto.

Carga las variables de entorno desde .env y expone
constantes tipadas para todos los modulos.

Soporta despliegue en Render:
  - PORT (asignado por Render)
  - FIREBASE_CREDENTIALS_JSON (credenciales como JSON string)
"""

import os
import json
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# Raiz del proyecto
BASE_DIR = Path(__file__).resolve().parent

# Cargar .env una sola vez (solo existe en desarrollo local)
load_dotenv(BASE_DIR / ".env")

# Detectar si estamos en Render
IS_RENDER = os.getenv("RENDER", "") == "true"

# -- gRPC (interno) -----------------------------------------------------------
GRPC_HOST = os.getenv("GRPC_HOST", "localhost")
GRPC_PORT = int(os.getenv("GRPC_PORT", "50051"))

# -- Flask ---------------------------------------------------------------------
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
# Render asigna el puerto via la variable PORT
FLASK_PORT = int(os.getenv("PORT", os.getenv("FLASK_PORT", "5000")))
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"

# -- Firebase Admin SDK --------------------------------------------------------
# En produccion (Render) las credenciales se pasan como JSON en la variable
# FIREBASE_CREDENTIALS_JSON. En desarrollo se sigue usando el archivo local.

def _fix_private_key(raw_json: str) -> str:
    """
    Repara la private_key PEM que puede llegar corrupta desde env vars.
    Render maneja los \\n de formas impredecibles:
      - A veces quedan como literal \\n (2 chars: backslash + n)
      - A veces se convierten en saltos de linea reales
      - A veces quedan como \\\\n (doble escape)
    """
    try:
        cred = json.loads(raw_json)
    except json.JSONDecodeError:
        # Si falla el parse, posiblemente hay newlines reales rompiendo el JSON.
        # Intentar reparar reemplazando newlines reales dentro del string
        raw_json = raw_json.replace("\r\n", "\\n").replace("\r", "\\n").replace("\n", "\\n")
        try:
            cred = json.loads(raw_json)
        except json.JSONDecodeError:
            print("[Config] ERROR: FIREBASE_CREDENTIALS_JSON no es JSON valido")
            return raw_json

    if "private_key" in cred:
        pk = cred["private_key"]
        # Paso 1: normalizar todos los tipos de newline a \n real
        pk = pk.replace("\\\\n", "\n")  # doble escape → newline real
        pk = pk.replace("\\n", "\n")    # escape simple → newline real
        pk = pk.replace("\r\n", "\n")   # CRLF → LF
        pk = pk.replace("\r", "\n")     # CR → LF

        # Paso 2: asegurar que empiece y termine correctamente
        if not pk.startswith("-----BEGIN"):
            pk = pk.strip()
        if not pk.endswith("\n"):
            pk += "\n"

        cred["private_key"] = pk
        print(f"[Config] Private key reparada: {len(pk)} chars, "
              f"empieza con '{pk[:30]}...'")

    return json.dumps(cred)


_cred_json = os.getenv("FIREBASE_CREDENTIALS_JSON", "")
if _cred_json:
    _cred_json = _fix_private_key(_cred_json)

    # Escribir JSON temporal para que firebase_admin lo consuma
    _tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, dir=tempfile.gettempdir()
    )
    _tmp.write(_cred_json)
    _tmp.close()
    FIREBASE_CREDENTIALS_PATH = _tmp.name
    print(f"[Config] Credenciales escritas en {FIREBASE_CREDENTIALS_PATH}")
else:
    _default_cred = str(BASE_DIR / "server" / "firebase_config.json")
    FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", _default_cred)
    if not os.path.isabs(FIREBASE_CREDENTIALS_PATH):
        FIREBASE_CREDENTIALS_PATH = str(BASE_DIR / FIREBASE_CREDENTIALS_PATH)

# -- Firebase Web (frontend) ---------------------------------------------------
FIREBASE_WEB = {
    "apiKey":            os.getenv("FIREBASE_API_KEY", ""),
    "authDomain":        os.getenv("FIREBASE_AUTH_DOMAIN", ""),
    "projectId":         os.getenv("FIREBASE_PROJECT_ID", ""),
    "storageBucket":     os.getenv("FIREBASE_STORAGE_BUCKET", ""),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID", ""),
    "appId":             os.getenv("FIREBASE_APP_ID", ""),
}
