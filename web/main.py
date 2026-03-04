
import time
from flask import Flask
from flask_cors import CORS
import config
from web.routes import register_routes, grpc_client

def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)
    register_routes(app)
    return app

def main():
    grpc_client.grpc_host = config.GRPC_HOST
    grpc_client.grpc_port = config.GRPC_PORT
    grpc_client.connect()
    time.sleep(1)
    app = create_app()
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=config.FLASK_DEBUG)


if __name__ == "__main__":
    main()
