
"""
wsgi.py — Punto de entrada para producción (gunicorn o local).

Lanza el servidor gRPC en background y expone la app Flask
como aplicación WSGI.

Comando de inicio sugerido:
    gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 1 --threads 4

La app Flask se crea INMEDIATAMENTE para que gunicorn
pueda bindear el puerto rápido. La inicialización de Firebase/gRPC
ocurre en un hilo en background.
"""

import sys
import threading
import time
import config
from server.main import start_grpc_background
from web.main import create_app
from web.routes import grpc_client


def _init_services():
    """Inicializa gRPC + Firebase en background."""
    try:
        print("[Init] Iniciando servidor gRPC interno...", flush=True)
        _grpc_server = start_grpc_background()
        time.sleep(0.5)

        grpc_client.grpc_host = config.GRPC_HOST
        grpc_client.grpc_port = config.GRPC_PORT
        grpc_client.connect()
        print(f"[Init] Cliente gRPC conectado a "
              f"{config.GRPC_HOST}:{config.GRPC_PORT}", flush=True)
    except Exception as e:
        print(f"[Init] ERROR en inicializacion: {e}", flush=True)


# 1. Crear la app Flask PRIMERO (gunicorn bindea el puerto de inmediato)
app = create_app()
print(f"[Init] App Flask creada — puerto {config.FLASK_PORT}", flush=True)

# 2. Iniciar gRPC/Firebase en background (no bloquea el binding)
threading.Thread(target=_init_services, daemon=True, name="init-services").start()

print("[Init] Inicializacion de servicios lanzada en background", flush=True)

# Permitir ejecutar wsgi.py directamente en desarrollo
if __name__ == "__main__":
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=config.FLASK_DEBUG)
