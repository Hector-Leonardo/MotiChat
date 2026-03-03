"""
server/service.py — Implementación del servicio gRPC ChatService.
"""

import threading
import time
from datetime import datetime

from server.generated import chat_pb2, chat_pb2_grpc
from server import firebase_db


class ChatServiceServicer(chat_pb2_grpc.ChatServiceServicer):
    """
    Streaming bidireccional: cada cliente se conecta, recibe historial
    y luego intercambia mensajes en tiempo real con todos los demás.
    """

    def __init__(self, db):
        self.db = db
        self.clients: list[list] = []
        self.lock = threading.Lock()

    # ── Broadcast ────────────────────────────────────────────
    def _broadcast(self, mensaje):
        """Envía un mensaje a todas las colas de clientes conectados."""
        with self.lock:
            desconectados = []
            for i, cola in enumerate(self.clients):
                try:
                    cola.append(mensaje)
                except Exception:
                    desconectados.append(i)
            for i in reversed(desconectados):
                self.clients.pop(i)

    # ── RPC principal ────────────────────────────────────────
    def ChatStream(self, request_iterator, context):
        cola_cliente: list = []
        with self.lock:
            self.clients.append(cola_cliente)
            total = len(self.clients)
        print(f"[Server] Cliente conectado. Total: {total}")

        # Enviar historial
        historial = firebase_db.cargar_historial(self.db)
        for item in historial:
            yield chat_pb2.ChatMessage(
                user=item["user"],
                message=item["message"],
                timestamp=item["timestamp"],
            )

        activo = [True]

        def recibir():
            try:
                for mensaje in request_iterator:
                    if not activo[0]:
                        break
                    if not mensaje.timestamp:
                        mensaje = chat_pb2.ChatMessage(
                            user=mensaje.user,
                            message=mensaje.message,
                            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        )
                    print(f"[Chat] {mensaje.user}: {mensaje.message}")
                    firebase_db.guardar_mensaje(
                        self.db, mensaje.user, mensaje.message, mensaje.timestamp
                    )
                    self._broadcast(mensaje)
            except Exception:
                pass
            finally:
                activo[0] = False

        hilo = threading.Thread(target=recibir, daemon=True)
        hilo.start()

        try:
            while activo[0] or len(cola_cliente) > 0:
                while len(cola_cliente) > 0:
                    yield cola_cliente.pop(0)
                time.sleep(0.1)
        except (GeneratorExit, Exception):
            pass
        finally:
            activo[0] = False
            with self.lock:
                if cola_cliente in self.clients:
                    self.clients.remove(cola_cliente)
                total = len(self.clients)
            print(f"[Server] Cliente desconectado. Total: {total}")
