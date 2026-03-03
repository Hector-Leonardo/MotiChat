"""
wsgi.py — Punto de entrada para produccion (Render + gunicorn).

Lanza el servidor gRPC en background y expone la app Flask
como aplicacion WSGI.

Comando de inicio (Render):
    gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 1 --threads 4
"""

import time
import config
from server.main import start_grpc_background
from web.main import create_app
from web.routes import grpc_client

# 1. Iniciar gRPC internamente
print("[Render] Iniciando servidor gRPC interno...")
_grpc_server = start_grpc_background()
time.sleep(1)

# 2. Conectar el cliente gRPC del modulo web
grpc_client.grpc_host = config.GRPC_HOST
grpc_client.grpc_port = config.GRPC_PORT
grpc_client.connect()
print(f"[Render] Cliente gRPC conectado a {config.GRPC_HOST}:{config.GRPC_PORT}")

# 3. Crear la app Flask (gunicorn busca esta variable)
app = create_app()
print(f"[Render] App lista — puerto {config.FLASK_PORT}")
