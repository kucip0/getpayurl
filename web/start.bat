@echo off
echo Starting GetPayurl Web Application...
echo.

:: Start backend
echo Starting backend server...
start "Backend" cmd /k "cd backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

:: Wait for backend to start
timeout /t 3 /nobreak >nul

:: Start frontend
echo Starting frontend dev server...
start "Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo API Docs: http://localhost:8000/docs
echo.
echo Press any key to stop all servers...
pause >nul

:: Kill both processes
taskkill /FI "WINDOWTITLE eq Backend*" /T /F
taskkill /FI "WINDOWTITLE eq Frontend*" /T /F

echo Servers stopped.
