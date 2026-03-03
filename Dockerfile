FROM python:3.13-slim

WORKDIR /app

# Copiar dependencias e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el proyecto
COPY . .

# Hugging Face Spaces expone el puerto 7860
ENV PORT=7860
ENV GRPC_HOST=localhost
ENV GRPC_PORT=50051

EXPOSE 7860

# Iniciar gRPC + Flask via gunicorn
CMD ["gunicorn", "wsgi:app", "--bind", "0.0.0.0:7860", "--workers", "1", "--threads", "4", "--timeout", "120"]
