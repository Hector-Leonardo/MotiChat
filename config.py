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

def _rebuild_pem(raw_pem: str) -> str:
    """
    Reconstruye una clave PEM desde cero.

    1. Quita headers/footers y TODO el whitespace.
    2. Obtiene el base64 puro.
    3. Lo re-formatea en lineas de 64 caracteres.
    4. Re-agrega headers/footers correctos.

    Esto garantiza un PEM valido sin importar como
    Render haya corrompido los saltos de linea.
    """
    import re
    import base64

    # Normalizar cualquier variante de newline
    pk = raw_pem
    pk = pk.replace("\\\\n", "\n")
    pk = pk.replace("\\n", "\n")
    pk = pk.replace("\r\n", "\n")
    pk = pk.replace("\r", "\n")

    # Extraer solo el contenido base64 (quitar headers, footers, espacios)
    pk = re.sub(r"-----\s*BEGIN[^-]*-----", "", pk)
    pk = re.sub(r"-----\s*END[^-]*-----", "", pk)
    pk = re.sub(r"\s+", "", pk)  # quitar TODOS los espacios/newlines

    if not pk:
        print("[Config] ADVERTENCIA: private_key quedo vacia tras limpieza")
        return raw_pem

    # Validar que es base64 valido
    try:
        decoded = base64.b64decode(pk)
        print(f"[Config] PEM base64 decodificado OK: {len(decoded)} bytes")
    except Exception as e:
        print(f"[Config] ADVERTENCIA: base64 no valido: {e}")
        # Intentar devolver la clave original con newlines normalizados
        return raw_pem.replace("\\n", "\n")

    # Re-codificar en base64 limpio (por si acaso)
    pk_clean = base64.b64encode(decoded).decode("ascii")

    # Formatear en lineas de 64 caracteres (estandar PEM RFC 7468)
    lines = [pk_clean[i:i+64] for i in range(0, len(pk_clean), 64)]

    # Reconstruir PEM completo
    rebuilt = "-----BEGIN PRIVATE KEY-----\n"
    rebuilt += "\n".join(lines)
    rebuilt += "\n-----END PRIVATE KEY-----\n"

    print(f"[Config] PEM reconstruida: {len(rebuilt)} chars, "
          f"{len(lines)} lineas de base64")
    return rebuilt


def _fix_private_key(raw_json: str) -> str:
    """
    Repara la private_key PEM que puede llegar corrupta desde env vars.
    Reconstruye el PEM completamente desde el base64 puro.
    """
    try:
        cred = json.loads(raw_json)
    except json.JSONDecodeError:
        # Si falla el parse, posiblemente hay newlines reales rompiendo el JSON.
        raw_json = raw_json.replace("\r\n", "\\n").replace("\r", "\\n").replace("\n", "\\n")
        try:
            cred = json.loads(raw_json)
        except json.JSONDecodeError:
            print("[Config] ERROR: FIREBASE_CREDENTIALS_JSON no es JSON valido")
            return raw_json

    if "private_key" in cred:
        original = cred["private_key"]
        print(f"[Config] private_key original: {len(original)} chars")
        cred["private_key"] = _rebuild_pem(original)

    return json.dumps(cred)


# Estrategia de credenciales (en orden de prioridad):
#   1. FIREBASE_CREDENTIALS_BASE64  — JSON codificado en Base64 (mejor opcion)
#   2. FIREBASE_CREDENTIALS_JSON    — JSON como string (problemas con \n)
#   3. Archivo local firebase_config.json
import base64 as _b64

_cred_b64 = os.getenv("FIREBASE_CREDENTIALS_BASE64", "")
_cred_json = os.getenv("FIREBASE_CREDENTIALS_JSON", "")

if _cred_b64:
    # --- OPCION 1: Base64 (recomendado para Render) ---
    try:
        _cred_json = _b64.b64decode(_cred_b64).decode("utf-8")
        print(f"[Config] Credenciales decodificadas de Base64: {len(_cred_json)} chars")
    except Exception as e:
        print(f"[Config] ERROR decodificando Base64: {e}")
        _cred_json = ""

if _cred_json:
    # Si viene de Base64 ya esta limpio; si viene del env var plano, reparar
    if not _cred_b64:
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
