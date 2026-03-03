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
│   ├── clear_db.py                 # Limpia todos los mensajes de Firestore
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

---

## Instalacion

### 1. Requisitos Previos

- **Python 3.8+** ([python.org](https://python.org))
- Conexion a Internet (para Firebase)

### 2. Instalar Dependencias

```bash
cd chat-grpc-firebase
pip install -r requirements.txt
```

### 3. Configurar Variables de Entorno

```bash
copy .env.example .env
```

Edita `.env` con tus credenciales reales de Firebase.

### 4. Configurar Firebase

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

> **Nunca commitees** `firebase_config.json` ni `.env`. Ya estan en `.gitignore`.

### 5. Generar Codigo gRPC

```bash
scripts\generate_proto.bat
```

---

## Ejecucion

Necesitas **2 terminales** desde la raiz del proyecto:

### Terminal 1 — Servidor gRPC

```bash
python -m server.main
```

### Terminal 2 — Servidor Web (Flask)

```bash
python -m web.main
```

Abre **http://localhost:5000** en tu navegador.

---

## Arquitectura

```
┌─────────────┐     HTTP/JSON      ┌──────────────┐     gRPC Stream     ┌──────────────┐
│  Navegador  │ ──────────────────> │  Flask        │ ──────────────────> │  gRPC Server │
│  (Frontend) │ <────────────────── │  (web/)       │ <────────────────── │  (server/)   │
└─────────────┘  POST /api/send    └──────────────┘  Bidirectional      └──────┬───────┘
                 GET /api/messages                                              │
                                                                         Firebase Admin
                                                                              │
                                                                     ┌──────────────┐
                                                                     │   Firebase    │
                                                                     │ Auth + Store  │
                                                                     └──────────────┘
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

# Limpiar todos los mensajes de Firestore
python -m scripts.clear_db
```

---

## Solucion de Problemas

| Error | Causa | Solucion |
|---|---|---|
| `ModuleNotFoundError: chat_pb2` | Codigo gRPC no generado | Ejecutar `scripts\generate_proto.bat` |
| `ModuleNotFoundError: grpc` | Dependencias no instaladas | `pip install -r requirements.txt` |
| `firebase_admin.exceptions` | Credenciales invalidas | Verificar `firebase_config.json` |
| `Connection refused` | gRPC server no iniciado | Iniciar `python -m server.main` primero |
| `Address already in use` | Puerto ocupado | `netstat -ano \| findstr 50051` -> `taskkill /PID <PID> /F` |

---

## Licencia

Proyecto educativo de codigo abierto. Usalo libremente.
