#!/usr/bin/env bash
# ============================================================
# build.sh — Script de build para Render
# ============================================================
set -o errexit

echo "=== Instalando dependencias ==="
pip install -r requirements.txt

echo "=== Generando codigo gRPC desde proto ==="
python -m grpc_tools.protoc \
    -I server/generated/protos \
    --python_out=server/generated \
    --grpc_python_out=server/generated \
    server/generated/protos/chat.proto 2>/dev/null || echo "(proto ya generado, continuando)"

echo "=== Build completado ==="
