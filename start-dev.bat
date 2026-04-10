@echo off
REM Start Command Center Dashboard and Backend
REM This script opens two PowerShell windows and starts both services

echo Starting Steganography Command Center...
echo.

REM Start Backend in new PowerShell window
echo Starting Backend Server on port 5000...
start /d "%cd%" powershell -NoExit -Command "cd '%cd%' ; python -m uvicorn app:app --host 127.0.0.1 --port 5000 --reload"

REM Wait a moment for backend to start
timeout /t 3 /nobreak

REM Start Frontend in new PowerShell window
echo Starting Frontend Server on port 3000...
start /d "%cd%\Frontend" powershell -NoExit -Command "cd '%cd%\Frontend' ; npm run dev"

echo.
echo ============================================
echo Backend: http://localhost:5000
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:5000/docs
echo ============================================
echo.
echo Both servers are starting in separate windows.
echo Close each window to stop the respective server.
