"""
config.py — Configuracion centralizada del proyecto.

Carga las variables de entorno desde .env y expone
constantes tipadas para todos los modulos.

Soporta despliegue en Render:
  - PORT (asignado por Render)
  - FIREBASE_CREDENTIALS_BASE64 (credenciales como JSON en Base64)
"""

import os
import sys
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
# Estrategia de credenciales (en orden de prioridad):
#   1. FIREBASE_CREDENTIALS_BASE64 — JSON completo codificado en Base64
#   2. Archivo local server/firebase_config.json
#
# La clave se escribe a un archivo temporal para usar el code-path
# mas probado de firebase_admin (Certificate con filepath).

import base64 as _b64

FIREBASE_CREDENTIALS_PATH = None

_cred_b64 = os.getenv("FIREBASE_CREDENTIALS_BASE64", "").strip()

if _cred_b64:
    # --- Base64 → JSON → archivo temporal ---
    try:
        _raw = _b64.b64decode(_cred_b64).decode("utf-8")
        # Validar que es JSON valido
        _parsed = json.loads(_raw)
        _project = _parsed.get("project_id", "?")
        _pk = _parsed.get("private_key", "")

        # Diagnostico de la clave
        _has_real_nl = "\n" in _pk
        _has_escaped = "\\n" in _pk
        print(f"[Config] Base64 decodificado OK: {len(_raw)} chars, "
              f"project={_project}", flush=True)
        print(f"[Config] private_key: {len(_pk)} chars, "
              f"real_newlines={_has_real_nl}, escaped_newlines={_has_escaped}",
              flush=True)

        # Si la clave tiene \\n literales (raro desde Base64, pero por si acaso)
        if _has_escaped and not _has_real_nl:
            _pk = _pk.replace("\\n", "\n")
            _parsed["private_key"] = _pk
            _raw = json.dumps(_parsed)
            print("[Config] Corregidos \\\\n → newlines reales", flush=True)

        # Escribir a archivo temporal (firebase_admin lo lee de forma nativa)
        _tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", prefix="fb_cred_",
            delete=False, encoding="utf-8"
        )
        _tmp.write(_raw)
        _tmp.flush()
        _tmp.close()
        FIREBASE_CREDENTIALS_PATH = _tmp.name
        print(f"[Config] Credenciales escritas en {_tmp.name}", flush=True)

    except Exception as e:
        print(f"[Config] ERROR procesando Base64: {e}", flush=True)
        import traceback
        traceback.print_exc()

if not FIREBASE_CREDENTIALS_PATH:
    # --- Archivo local (desarrollo) ---
    _default_cred = str(BASE_DIR / "server" / "firebase_config.json")
    FIREBASE_CREDENTIALS_PATH = os.getenv(
        "FIREBASE_CREDENTIALS_PATH", _default_cred
    )
    if not os.path.isabs(FIREBASE_CREDENTIALS_PATH):
        FIREBASE_CREDENTIALS_PATH = str(BASE_DIR / FIREBASE_CREDENTIALS_PATH)

# Variable legacy (ya no se usa, pero mantener por compatibilidad)
FIREBASE_CREDENTIALS_DICT = None

# -- Firebase Web (frontend) ---------------------------------------------------
FIREBASE_WEB = {
    "apiKey":            os.getenv("FIREBASE_API_KEY", ""),
    "authDomain":        os.getenv("FIREBASE_AUTH_DOMAIN", ""),
    "projectId":         os.getenv("FIREBASE_PROJECT_ID", ""),
    "storageBucket":     os.getenv("FIREBASE_STORAGE_BUCKET", ""),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID", ""),
    "appId":             os.getenv("FIREBASE_APP_ID", ""),
}
