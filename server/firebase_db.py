"""
server/firebase_db.py — Inicialización de Firebase y operaciones de Firestore.
"""

import firebase_admin
from firebase_admin import credentials, firestore


def init_firebase(credentials_path: str = None, credentials_dict: dict = None):
    """
    Inicializa Firebase Admin SDK y retorna el cliente de Firestore.
    Acepta un path a archivo JSON o un diccionario de credenciales.
    Retorna None si falla (el servidor funcionará sin persistencia).
    """
    try:
        if credentials_dict:
            print(f"[Firebase] Cargando credenciales desde dict (project: {credentials_dict.get('project_id', '?')})", flush=True)
            pk = credentials_dict.get('private_key', '')
            print(f"[Firebase] PEM: {len(pk)} chars, empieza con '{pk[:30]}...', termina con '...{pk[-30:]}'", flush=True)
            cred = credentials.Certificate(credentials_dict)
        else:
            print(f"[Firebase] Cargando credenciales de archivo: {credentials_path}", flush=True)
            cred = credentials.Certificate(credentials_path)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("[Firebase] Cliente Firestore creado OK", flush=True)

        # Test de conectividad (no bloqueante - en background)
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
