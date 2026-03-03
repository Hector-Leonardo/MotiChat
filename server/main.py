"""
server/main.py — Punto de entrada del servidor gRPC.

Uso directo (desarrollo):
    python -m server.main

Uso embebido (produccion):
    from server.main import start_grpc_background
    grpc_server = start_grpc_background()
"""

import grpc
from concurrent import futures

import config
from server.firebase_db import init_firebase
from server.service import ChatServiceServicer
from server.generated import chat_pb2_grpc


def start_grpc_background():
    """Inicia el gRPC server en background y retorna la instancia
    (sin bloquear; ideal para lanzarlo junto con Flask/gunicorn)."""
    db = init_firebase(
        credentials_path=config.FIREBASE_CREDENTIALS_PATH,
        credentials_dict=config.FIREBASE_CREDENTIALS_DICT,
    )
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=20))
    chat_pb2_grpc.add_ChatServiceServicer_to_server(
        ChatServiceServicer(db), server
    )
    server.add_insecure_port(f"[::]:{config.GRPC_PORT}")
    server.start()
    print(f"[gRPC] Servidor iniciado en puerto {config.GRPC_PORT}")
    return server


def iniciar_servidor():
    server = start_grpc_background()
    print("=" * 55)
    print(f"  Servidor gRPC iniciado en puerto {config.GRPC_PORT}")
    print("  Esperando conexiones...")
    print("=" * 55)
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\n[Server] Servidor detenido")
        server.stop(0)


if __name__ == "__main__":
    iniciar_servidor()
