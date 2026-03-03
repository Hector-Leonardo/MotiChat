"""
wsgi.py — Punto de entrada para produccion (Render + gunicorn).

Lanza el servidor gRPC en background y expone la app Flask
como aplicacion WSGI.

Comando de inicio (Render):
    gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 1 --threads 4

IMPORTANTE: La app Flask se crea INMEDIATAMENTE para que gunicorn
pueda bindear el puerto rapido y Render no muestre "No open HTTP ports".
La inicializacion de Firebase/gRPC ocurre en un hilo en background.
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
        print("[Render] Iniciando servidor gRPC interno...", flush=True)
        _grpc_server = start_grpc_background()
        time.sleep(0.5)

        grpc_client.grpc_host = config.GRPC_HOST
        grpc_client.grpc_port = config.GRPC_PORT
        grpc_client.connect()
        print(f"[Render] Cliente gRPC conectado a "
              f"{config.GRPC_HOST}:{config.GRPC_PORT}", flush=True)
    except Exception as e:
        print(f"[Render] ERROR en inicializacion: {e}", flush=True)


# 1. Crear la app Flask PRIMERO (gunicorn bindea el puerto de inmediato)
app = create_app()
print(f"[Render] App Flask creada — puerto {config.FLASK_PORT}", flush=True)

# 2. Iniciar gRPC/Firebase en background (no bloquea el binding)
threading.Thread(target=_init_services, daemon=True, name="init-services").start()
print("[Render] Inicializacion de servicios lanzada en background", flush=True)
