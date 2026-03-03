"""
web/main.py — Punto de entrada del servidor Flask.

Uso:
    python -m web.main
"""

import time
from flask import Flask
from flask_cors import CORS

import config
from web.routes import register_routes, grpc_client


def create_app() -> Flask:
    """Factory de la aplicación Flask."""
    app = Flask(__name__)
    CORS(app)
    register_routes(app)
    return app


def main():
    print("=" * 55)
    print("  Servidor Web del Chat")
    print("=" * 55)

    # Conectar al servidor gRPC
    grpc_client.grpc_host = config.GRPC_HOST
    grpc_client.grpc_port = config.GRPC_PORT
    print(f"[Web] Conectando al gRPC en {config.GRPC_HOST}:{config.GRPC_PORT}...")
    grpc_client.connect()
    time.sleep(1)

    # Iniciar Flask
    app = create_app()
    print(f"[Web] Flask en http://{config.FLASK_HOST}:{config.FLASK_PORT}")
    print("=" * 55)
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=config.FLASK_DEBUG)


if __name__ == "__main__":
    main()
