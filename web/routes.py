
from flask import render_template, request, jsonify
import config
from web.grpc_client import GrpcChatClient
grpc_client = GrpcChatClient()

def register_routes(app):
    @app.route("/")
    def index():
        return render_template("index.html", firebase_config=config.FIREBASE_WEB)

    @app.route("/api/send", methods=["POST"])
    def send_message():
        data = request.get_json()
        if not data or "user" not in data or "message" not in data:
            return jsonify({"error": "Faltan campos 'user' y 'message'"}), 400
        if not grpc_client.connected:
            return jsonify({"error": "No conectado al servidor gRPC"}), 503
        result = grpc_client.send_message(data["user"], data["message"])
        return jsonify(result)

    @app.route("/api/messages", methods=["GET"])
    def get_messages():
        if not grpc_client.connected:
            return jsonify({"error": "No conectado al servidor gRPC", "messages": []}), 503
        since_id = request.args.get("since", -1, type=int)
        return jsonify({"messages": grpc_client.get_messages_since(since_id)})

    @app.route("/api/status", methods=["GET"])
    def get_status():
        return jsonify({
            "grpc_connected": grpc_client.connected,
            "server": f"{grpc_client.grpc_host}:{grpc_client.grpc_port}",
        })
