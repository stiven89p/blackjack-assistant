@echo off
cd /d "%~dp0"
echo Iniciando Blackjack Assistant...
echo Abre tu navegador en: http://localhost:8000
echo.
echo Presiona CTRL+C para detener el servidor.
echo.
.\venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
pause
