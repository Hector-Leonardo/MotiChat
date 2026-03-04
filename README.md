# MotiChat — Chat web en tiempo real (Python + gRPC + Firebase)

Este proyecto es un chat web en tiempo real llamado **MotiChat**, construido con Python, gRPC y Firebase. Permite autenticación completa (registro, login, Google, verificación de email), chat en tiempo real usando streaming bidireccional gRPC, y almacenamiento de mensajes en Firebase Firestore. El frontend es una app web con Flask y una interfaz moderna tipo Telegram.

---

## ¿Qué hace este proyecto?

- Permite a los usuarios registrarse, iniciar sesión (email/contraseña o Google) y verificar su email.
- Los usuarios pueden chatear en tiempo real; todos los mensajes se transmiten a todos los clientes conectados.
- Los mensajes se almacenan en Firebase Firestore y se recupera el historial reciente al conectarse.
- El backend está dividido en dos partes: un servidor gRPC (maneja la lógica del chat y la persistencia) y un servidor Flask (sirve la web y actúa como puente HTTP-gRPC).
- El frontend es responsivo y moderno, con autenticación y chat en vivo.

---

## ¿Cómo ejecutarlo correctamente?

1. **Instala Python 3.8+** y asegúrate de tener conexión a internet.
2. **Clona el repositorio y entra a la carpeta:**
     ```bash
     cd chat-grpc-firebase
     ```
3. **Instala las dependencias:**
     ```bash
     pip install -r requirements.txt
     ```
4. **Configura las variables de entorno:**
     
     ### Configurar Firebase

     #### Firebase Admin SDK (servidor)

     1. Ve a [Firebase Console](https://console.firebase.google.com/) -> tu proyecto
     2. **Configuracion** -> **Cuentas de servicio** -> **Generar nueva clave privada**
     3. Renombra el archivo descargado a `firebase_config.json`
     4. Colocalo en `server/firebase_config.json`

     #### Firebase Auth (frontend)

     1. En Firebase Console -> **Authentication** -> **Metodo de acceso**
     2. Habilita **Correo electronico/contrasena** y **Google**
     3. Copia los valores de **Configuracion del SDK web** al archivo `.env`

     #### Firestore Database

     1. En Firebase Console -> **Firestore Database** -> **Crear base de datos**
     2. Selecciona **Modo de prueba** y tu ubicacion preferida
     
5. **Genera el código gRPC:**
     ```bash
     scripts\generate_proto.bat
     ```
6. **Inicia el servidor Flask en el puerto 5000:**
      - **Primero, inicia el servidor gRPC (backend) en una terminal:**
           ```bash
           python -m server.main
           ```
      - Luego, en otra terminal, inicia Flask:
           - En CMD:
                ```bash
                set FLASK_APP=web/main.py
                flask run --host=0.0.0.0 --port=5000
                ```
           - En PowerShell:
                ```bash
                $env:FLASK_APP="web/main.py"
                flask run --host=0.0.0.0 --port=5000
                ```
7. **En otra terminal, inicia ngrok para exponer el servidor:**
     ```bash
     ngrok http 5000
     ```
8. **Abre la URL pública que te da ngrok** para acceder a la app desde internet.

---

## Instrucciones adicionales y recomendaciones importantes

1. **Variables de entorno:**
     - Crea un archivo `.env` en la raíz del proyecto.
     - Llena los valores de Firebase (`FIREBASE_API_KEY`, `FIREBASE_AUTH_DOMAIN`, etc.) con los datos de tu proyecto en Firebase Console.
     - Verifica que la ruta de `FIREBASE_CREDENTIALS_PATH` apunte correctamente a `server/firebase_config.json`.

2. **Generar código gRPC:**
     - Antes de correr el servidor, ejecuta siempre `scripts\generate_proto.bat` para evitar errores de importación de `chat_pb2` o `chat_pb2_grpc`.
     - Si ves errores de `ModuleNotFoundError: grpc` o similares, ejecuta de nuevo `pip install -r requirements.txt`.

3. **Iniciar ambos servidores:**
     - El servidor gRPC (backend) debe estar corriendo antes de iniciar Flask.
       Ejemplo:
       ```bash
       python -m server.main
       ```
     - Luego, en otra terminal, inicia Flask como indica el README.

4. **Ngrok:**
     - Ngrok solo es necesario si quieres exponer la app a internet. Si solo pruebas localmente, puedes omitirlo.

5. **Dependencias:**
     - Usa Python 3.8 o superior, pero evita versiones incompatibles con los paquetes listados.
     - Si usas un entorno virtual, actívalo antes de instalar dependencias.

6. **Errores comunes:**
     - Si ves errores de credenciales, revisa que `server/firebase_config.json` exista y sea válido.
     - Si el puerto 50051 o 5000 está ocupado, cámbialo en el `.env` y en los comandos de inicio.


# Cómo correr el servidor y exponerlo con ngrok

1. Instala las dependencias:
     ```bash
     pip install -r requirements.txt
     ```

2. Inicia el servidor Flask en el puerto 5000:
     ```bash
     set FLASK_APP=web/main.py
     flask run --host=0.0.0.0 --port=5000
     ```
3. En otra terminal, inicia ngrok apuntando al puerto 5000:
     ```bash
     ngrok http 5000
     ```

4. Usa la URL pública que te da ngrok para acceder a tu app desde internet.

**Notas:**
- Asegúrate de que el servidor Flask esté corriendo antes de iniciar ngrok.
- Si cambias el puerto, también debes cambiarlo en el comando de ngrok.
# MotiChat — Python + gRPC + Firebase

Chat web en tiempo real con **autenticacion completa** (registro, login, Google, verificacion de email), construido con **Python**, **gRPC** (streaming bidireccional), **Firebase** (Auth + Firestore) y **Flask**.

---

## Estructura del Proyecto

```
chat-grpc-firebase/
│
├── config.py                       # Configuracion centralizada (.env)
│
├── server/                         # Paquete del servidor gRPC
│   ├── __init__.py
│   ├── main.py                     # Punto de entrada del servidor gRPC
│   ├── service.py                  # Implementacion del servicio ChatService
│   ├── firebase_db.py              # Inicializacion de Firebase + operaciones Firestore
│   ├── chat.proto                  # Definicion del servicio gRPC
│   ├── firebase_config.json        # Credenciales de Firebase (no commitear)
│   └── generated/                  # Codigo generado automaticamente
│       ├── chat_pb2.py
│       ├── chat_pb2_grpc.py
│       └── __init__.py
│
├── web/                            # Paquete del servidor Flask
│   ├── __init__.py
│   ├── main.py                     # Punto de entrada de Flask (app factory)
│   ├── routes.py                   # Rutas / endpoints HTTP
│   ├── grpc_client.py              # Cliente gRPC (puente HTTP-gRPC)
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css           # Estilos del frontend
│   │   └── js/
│   │       └── app.js              # Logica del frontend (auth + chat)
│   └── templates/
│       └── index.html              # HTML (estructura solamente)
│
├── scripts/                        # Utilidades
│   └── generate_proto.bat          # Genera codigo Python desde chat.proto
│
├── .env                            # Variables de entorno (no commitear)
├── .env.example                    # Plantilla de variables de entorno
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Caracteristicas

- **Autenticacion completa**: Registro con email/contrasena, login y Google Sign-In
- **Verificacion de email**: Flujo completo con reenvio y cooldown
- **Chat en tiempo real**: Streaming bidireccional via gRPC
- **Persistencia**: Mensajes almacenados en Firebase Firestore
- **Historial**: Se cargan los ultimos 50 mensajes al conectarse
- **Broadcast**: Todos los clientes reciben todos los mensajes (sistema de buffer indexado)
- **UI profesional**: Diseno dark theme estilo Telegram, responsive
- **Codigo modular**: Separacion clara de responsabilidades por paquetes

```

**Flujo de un mensaje:**
1. El usuario se autentica (email/password o Google) en el frontend
2. JavaScript envia `POST /api/send` con el mensaje al servidor Flask
3. Flask reenvia el mensaje al servidor gRPC por streaming bidireccional
4. gRPC guarda el mensaje en Firestore y hace broadcast a todos los clientes
5. Flask almacena el mensaje en su buffer indexado
6. El navegador obtiene mensajes nuevos por polling (`GET /api/messages?since=N`)

---

## Modulos

| Modulo | Responsabilidad |
|---|---|
| `config.py` | Carga `.env`, expone constantes tipadas |
| `server/main.py` | Arranca el servidor gRPC |
| `server/service.py` | Implementacion de `ChatServiceServicer` (streaming bidireccional) |
| `server/firebase_db.py` | Init Firebase + CRUD de mensajes en Firestore |
| `web/main.py` | App factory de Flask, conecta al gRPC y arranca el servidor web |
| `web/routes.py` | Define endpoints HTTP (`/`, `/api/send`, `/api/messages`, `/api/status`) |
| `web/grpc_client.py` | Cliente gRPC con buffer indexado (puente HTTP-gRPC) |

---

## Variables de Entorno

| Variable | Descripcion | Default |
|---|---|---|
| `GRPC_HOST` | Host del servidor gRPC | `localhost` |
| `GRPC_PORT` | Puerto del servidor gRPC | `50051` |
| `FLASK_HOST` | Host del servidor Flask | `0.0.0.0` |
| `FLASK_PORT` | Puerto del servidor Flask | `5000` |
| `FLASK_DEBUG` | Modo debug de Flask | `false` |
| `FIREBASE_CREDENTIALS_PATH` | Ruta al JSON de credenciales | `server/firebase_config.json` |
| `FIREBASE_API_KEY` | API Key del proyecto Firebase | — |
| `FIREBASE_AUTH_DOMAIN` | Auth domain de Firebase | — |
| `FIREBASE_PROJECT_ID` | ID del proyecto Firebase | — |
| `FIREBASE_STORAGE_BUCKET` | Storage bucket de Firebase | — |
| `FIREBASE_MESSAGING_SENDER_ID` | Sender ID de Firebase Cloud Messaging | — |
| `FIREBASE_APP_ID` | App ID de Firebase | — |

---

## Scripts de Utilidad

```bash
# Generar codigo gRPC desde chat.proto
scripts\generate_proto.bat

```

| Error | Causa | Solucion |
|---|---|---|
| `ModuleNotFoundError: chat_pb2` | Codigo gRPC no generado | Ejecutar `scripts\generate_proto.bat` |
| `ModuleNotFoundError: grpc` | Dependencias no instaladas | `pip install -r requirements.txt` |
| `firebase_admin.exceptions` | Credenciales invalidas | Verificar `firebase_config.json` |
| `Connection refused` | gRPC server no iniciado | Iniciar `python -m server.main` primero |
| `Address already in use` | Puerto ocupado | `netstat -ano \| findstr 50051` -> `taskkill /PID <PID> /F` |

---
