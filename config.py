

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")



GRPC_HOST = os.getenv("GRPC_HOST", "localhost")
GRPC_PORT = int(os.getenv("GRPC_PORT", "50051"))

FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"

_default_cred = BASE_DIR / "server" / "firebase_config.json"
FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", str(_default_cred))

if not os.path.isabs(FIREBASE_CREDENTIALS_PATH):
    FIREBASE_CREDENTIALS_PATH = str((BASE_DIR / FIREBASE_CREDENTIALS_PATH).resolve())

if not os.path.isfile(FIREBASE_CREDENTIALS_PATH):
    print(f"[Config] Advertencia: no se encontró el archivo de credenciales: "
          f"{FIREBASE_CREDENTIALS_PATH}", flush=True)
else:
    print(f"[Config] FIREBASE_CREDENTIALS_PATH={FIREBASE_CREDENTIALS_PATH}", flush=True)


FIREBASE_WEB = {
    "apiKey":            os.getenv("FIREBASE_API_KEY", ""),
    "authDomain":        os.getenv("FIREBASE_AUTH_DOMAIN", ""),
    "projectId":         os.getenv("FIREBASE_PROJECT_ID", ""),
    "storageBucket":     os.getenv("FIREBASE_STORAGE_BUCKET", ""),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID", ""),
    "appId":             os.getenv("FIREBASE_APP_ID", ""),
}
