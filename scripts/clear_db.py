"""
clear_db.py — Limpia TODOS los mensajes de Firestore.

Ejecutar desde la raiz del proyecto:
    python -m scripts.clear_db
"""

import sys
from pathlib import Path

# Agregar raiz del proyecto al path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import FIREBASE_CREDENTIALS_PATH
from server.firebase_db import init_firebase, eliminar_todos


def main():
    db = init_firebase(FIREBASE_CREDENTIALS_PATH)
    if db is None:
        print("[clear_db] No se pudo conectar a Firestore")
        sys.exit(1)

    print("[clear_db] Eliminando todos los mensajes...")
    count = eliminar_todos(db)
    print(f"[clear_db] Eliminados {count} mensajes")


if __name__ == "__main__":
    main()
