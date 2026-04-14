@echo off
echo Closing processes using port 8000...

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do (
    echo Killing process PID: %%a
    taskkill /F /PID %%a >nul 2>&1
)

echo Done. Starting backend server...
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
