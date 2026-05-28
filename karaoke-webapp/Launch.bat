@echo off
title Karaoke Maker
color 0E

set PYTHON=%~dp0venv\Scripts\python.exe

echo.
echo  =========================================
echo   Karaoke Maker
echo  =========================================
echo.

:: Kill anything currently on port 8000
echo  [1/2] Clearing port 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000 " 2^>nul') do (
    taskkill /f /pid %%a >nul 2>&1
)
echo         Done.
echo.

:: Run from batch file's directory (handles Z: drive correctly)
cd /d "%~dp0"

echo  [2/2] Starting server...
echo.
echo  Open: http://localhost:8000
echo.
echo  Press Ctrl+C to stop.
echo  =========================================
echo.

:: Open browser after a 3s delay (gives uvicorn time to boot)
start "" cmd /c "timeout /t 3 /nobreak >nul && start http://localhost:8000"

"%PYTHON%" -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
if %errorlevel% neq 0 (
    echo.
    echo  ERROR: Server failed to start. See message above.
    pause
)
