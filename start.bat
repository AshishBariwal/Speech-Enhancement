@echo off
echo ===================================================
echo  Starting DeepFilterNet Speech Enhancement System
echo ===================================================
echo.

set "PROJECT_ROOT=%~dp0"

echo [1/2] Launching Backend Server (FastAPI on Port 8000)...
start "DeepFilterNet Backend" cmd /k "cd /d "%PROJECT_ROOT%backend" && python -m uvicorn server:app --reload --port 8000"

echo [2/2] Launching Frontend App (React on Port 3000)...
start "DeepFilterNet Frontend" cmd /k "cd /d "%PROJECT_ROOT%frontend" && npm start"

echo.
echo ===================================================
echo  Both servers launched in new terminal windows!
echo  - Frontend UI: http://localhost:3000
echo  - Backend API: http://localhost:8000
echo ===================================================
echo.
pause
