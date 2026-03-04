@echo off
REM Script para lanzar ngrok y mostrar la URL pública automáticamente

REM Iniciar ngrok en background
start ngrok.exe http 5000

REM Esperar unos segundos para que ngrok arranque
timeout /t 3 > nul

REM Obtener la URL pública desde la API local de ngrok
for /f "tokens=2 delims=:" %%a in ('curl -s http://127.0.0.1:4040/api/tunnels ^| findstr /i "public_url"') do (
    set url=%%a
    set url=!url:~2,-2!
    echo Tu URL pública de ngrok es: !url!
)
pause
