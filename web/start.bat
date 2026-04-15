@echo off
chcp 65001 >nul 2>&1
echo ============================================
echo   GetPayurl Web - Development Environment
echo ============================================
echo.

:: Check virtual environment
if not exist "backend\venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo.
    echo Please run the following commands:
    echo   cd backend
    echo   python -m venv venv
    echo   venv\Scripts\activate
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

:: Start backend
echo [1/2] Starting backend server...
start "GetPayurl Backend" cmd /k "cd backend && venv\Scripts\activate && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

:: Wait for backend to start
timeout /t 3 /nobreak >nul

:: Start frontend
echo [2/2] Starting frontend dev server...
start "GetPayurl Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ============================================
echo   Startup Complete!
echo ============================================
echo.
echo   Frontend: http://localhost:5173
echo   Backend:  http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo.
echo   TIP: Closing this window will NOT stop servers
echo   Please close Backend and Frontend windows manually
echo.
pause
