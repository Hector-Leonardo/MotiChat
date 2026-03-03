@echo off
REM ============================================================
REM generate_proto.bat - Genera codigo Python desde chat.proto
REM ============================================================
REM Ejecutar desde la carpeta raiz del proyecto:
REM   scripts\generate_proto.bat
REM ============================================================

REM Ir a la raiz del proyecto (un nivel arriba de scripts/)
cd /d "%~dp0.."

echo ============================================================
echo   Generando codigo gRPC desde chat.proto...
echo ============================================================

REM Crear carpeta generated si no existe
if not exist "server\generated" mkdir "server\generated"

REM Generar codigo Python desde el archivo .proto
python -m grpc_tools.protoc ^
    -I./server ^
    --python_out=./server/generated ^
    --grpc_python_out=./server/generated ^
    ./server/chat.proto

REM Crear archivo __init__.py en generated (necesario para importar)
echo. > server\generated\__init__.py

REM Fix: el codigo generado usa "import chat_pb2" absoluto,
REM pero al usarlo como paquete (server.generated) falla.
REM Se agrega un fallback con try/except.
powershell -Command "(Get-Content 'server\generated\chat_pb2_grpc.py') -replace '^import chat_pb2 as chat__pb2$', 'try:`n    import chat_pb2 as chat__pb2`nexcept ImportError:`n    from server.generated import chat_pb2 as chat__pb2' | Set-Content 'server\generated\chat_pb2_grpc.py'"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================
    echo   Codigo generado exitosamente!
    echo   Archivos en: server/generated/
    echo ============================================================
) else (
    echo.
    echo ============================================================
    echo   ERROR al generar el codigo.
    echo   Asegurate de tener instalado grpcio-tools:
    echo     pip install grpcio-tools
    echo ============================================================
)

pause
