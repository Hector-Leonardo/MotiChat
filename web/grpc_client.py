"""
web/grpc_client.py — Cliente gRPC que actúa como puente HTTP ↔ gRPC.

Mantiene una conexión de streaming bidireccional y un buffer
indexado de mensajes. Cada pestaña del navegador rastrea su
propia posición con el parámetro `since`.
"""

import grpc
import threading
import time
from datetime import datetime

from server.generated import chat_pb2, chat_pb2_grpc


class GrpcChatClient:

    def __init__(self, host: str = "localhost", port: int = 50051):
        self.grpc_host = host
        self.grpc_port = port
        self.messages: list[dict] = []
        self.lock = threading.Lock()
        self.connected = False
        self.channel = None
        self.stub = None
        self._outgoing: list = []
        self._stop = threading.Event()

    # ── Conexión ─────────────────────────────────────────────
    def connect(self):
        try:
            self.channel = grpc.insecure_channel(
                f"{self.grpc_host}:{self.grpc_port}"
            )
            self.stub = chat_pb2_grpc.ChatServiceStub(self.channel)
            self.connected = True
            threading.Thread(target=self._stream_loop, daemon=True).start()
            print(f"[Web] Conectado al gRPC en {self.grpc_host}:{self.grpc_port}")
        except Exception as e:
            print(f"[Web] Error al conectar con gRPC: {e}")
            self.connected = False

    # ── Generador de salida ──────────────────────────────────
    def _generate_outgoing(self):
        while not self._stop.is_set():
            while self._outgoing:
                yield self._outgoing.pop(0)
            time.sleep(0.1)

    # ── Loop de streaming ────────────────────────────────────
    def _stream_loop(self):
        try:
            responses = self.stub.ChatStream(self._generate_outgoing())
            for response in responses:
                with self.lock:
                    idx = len(self.messages)
                    self.messages.append({
                        "id": idx,
                        "user": response.user,
                        "message": response.message,
                        "timestamp": response.timestamp,
                    })
        except grpc.RpcError as e:
            print(f"[Web] Conexion gRPC perdida: {e.code()}")
            self.connected = False
        except Exception as e:
            print(f"[Web] Error en stream: {e}")
            self.connected = False

    # ── Enviar mensaje ───────────────────────────────────────
    def send_message(self, user: str, message: str) -> dict:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._outgoing.append(
            chat_pb2.ChatMessage(user=user, message=message, timestamp=timestamp)
        )
        return {"status": "ok", "timestamp": timestamp}

    # ── Obtener mensajes nuevos ──────────────────────────────
    def get_messages_since(self, since_id: int = -1) -> list[dict]:
        with self.lock:
            if since_id < 0:
                return list(self.messages)
            return [m for m in self.messages if m["id"] > since_id]

    # ── Desconectar ──────────────────────────────────────────
    def disconnect(self):
        self._stop.set()
        if self.channel:
            self.channel.close()
        self.connected = False
