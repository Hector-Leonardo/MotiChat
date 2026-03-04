@echo off
REM Script para descargar e instalar ngrok en Windows

REM Cambia a la carpeta del proyecto
cd /d %~dp0

REM Descargar ngrok (última versión estable)
set NGROK_ZIP=ngrok-stable-windows-amd64.zip
curl -L -o %NGROK_ZIP% https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-stable-windows-amd64.zip

REM Extraer el ejecutable
tar -xf %NGROK_ZIP%

REM Eliminar el zip
del %NGROK_ZIP%

REM Mensaje final
echo ngrok instalado. Ejecuta "ngrok.exe http 5000" para exponer Flask.
pause
