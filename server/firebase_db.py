"""
server/firebase_db.py — Inicialización de Firebase y operaciones de Firestore.
"""

import firebase_admin
from firebase_admin import credentials, firestore


def init_firebase(credentials_path: str = None, credentials_dict: dict = None):
    """
    Inicializa Firebase Admin SDK y retorna el cliente de Firestore.
    Usa siempre el path al archivo JSON (mas confiable).
    Retorna None si falla (el servidor funcionará sin persistencia).
    """
    try:
        print(f"[Firebase] Cargando credenciales de: {credentials_path}", flush=True)

        # Verificar que el archivo existe
        import os
        if not credentials_path or not os.path.isfile(credentials_path):
            print(f"[Firebase] ERROR: archivo no encontrado: {credentials_path}", flush=True)
            return None

        # Diagnostico: leer y validar el JSON antes de pasarlo a Firebase
        with open(credentials_path, 'r', encoding='utf-8') as f:
            raw = f.read()
        data = __import__('json').loads(raw)
        pk = data.get('private_key', '')
        print(f"[Firebase] JSON OK: project={data.get('project_id','?')}, "
              f"client_email={data.get('client_email','?')[:30]}...", flush=True)
          print(f"[Firebase] private_key: {len(pk)} chars, "
              f"starts={repr(pk[:27])}, ends={repr(pk[-27:])}", flush=True)
          _has_real_nl = "\n" in pk
          _has_escaped = "\\n" in pk
          print(f"[Firebase] private_key real_newlines={_has_real_nl}, "
              f"escaped_newlines={_has_escaped}", flush=True)

        cred = credentials.Certificate(credentials_path)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("[Firebase] Cliente Firestore creado OK", flush=True)

        # Test de conectividad (no bloqueante)
        import threading
        def _test_conn():
            try:
                db.collection("messages").limit(1).get()
                print("[Firebase] Conexion exitosa con Firestore", flush=True)
            except Exception as e:
                print(f"[Firebase] Test de conexion fallo: {e}", flush=True)
        threading.Thread(target=_test_conn, daemon=True).start()

        return db
    except Exception as e:
        print(f"[Firebase] ERROR al conectar: {e}", flush=True)
        print(f"[Firebase] Tipo de error: {type(e).__name__}", flush=True)
        print("[Firebase] El servidor funcionara SIN persistencia", flush=True)
        return None


def guardar_mensaje(db, user: str, message: str, timestamp: str):
    """Guarda un mensaje en la colección 'messages' de Firestore."""
    if db is None:
        return
    try:
        db.collection("messages").add({
            "user": user,
            "message": message,
            "timestamp": timestamp,
        })
    except Exception as e:
        print(f"[Firebase] Error al guardar mensaje: {e}")


def cargar_historial(db, limite: int = 50):
    """
    Retorna los últimos `limite` documentos de 'messages' ordenados por timestamp.
    Cada elemento es un dict con keys: user, message, timestamp.
    """
    if db is None:
        return []
    try:
        docs = (
            db.collection("messages")
            .order_by("timestamp")
            .limit(limite)
            .stream()
        )
        historial = []
        for doc in docs:
            data = doc.to_dict()
            historial.append({
                "user": data.get("user", ""),
                "message": data.get("message", ""),
                "timestamp": data.get("timestamp", ""),
            })
        print(f"[Firebase] Historial cargado: {len(historial)} mensajes")
        return historial
    except Exception as e:
        print(f"[Firebase] Error al cargar historial: {e}")
        return []


def eliminar_todos(db):
    """Elimina todos los documentos de la colección 'messages'."""
    if db is None:
        print("[Firebase] Sin conexion a Firestore")
        return 0
    docs = db.collection("messages").stream()
    count = 0
    for doc in docs:
        doc.reference.delete()
        count += 1
    return count
