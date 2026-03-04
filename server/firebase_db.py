
import firebase_admin
from firebase_admin import credentials, firestore


def init_firebase(credentials_path: str = None, credentials_dict: dict = None):

    try:
        import os
        if not credentials_path or not os.path.isfile(credentials_path):
            print(f"[Firebase] Archivo de credenciales no encontrado: {credentials_path}", flush=True)
            return None
        cred = credentials.Certificate(credentials_path)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("[Firebase] Inicialización exitosa", flush=True)
        return db
    except Exception as e:
        print(f"[Firebase] Error al inicializar Firebase: {e}", flush=True)
        return None


def guardar_mensaje(db, user: str, message: str, timestamp: str):
    if db is None:
        return
    try:
        db.collection("messages").add({
            "user": user,
            "message": message,
            "timestamp": timestamp,
        })
    except Exception as e:
        pass


def cargar_historial(db, limite: int = 50):
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
        return historial
    except Exception as e:
        return []


def eliminar_todos(db):
    if db is None:
        return 0
    docs = db.collection("messages").stream()
    count = 0
    for doc in docs:
        doc.reference.delete()
        count += 1
    return count
