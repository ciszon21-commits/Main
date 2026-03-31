@echo off
setlocal enabledelayedexpansion

title SiteANA Launcher

set "NODE_DIR=e:\00.DEVE\01.VibeCoding\TOOL\node-v24.14.1-win-x64\node-v24.14.1-win-x64"

echo ============================================================
echo  SiteANA Launcher - Checking environment...
echo ============================================================
echo.

echo [1/4] Checking Node.js...
if not exist "%NODE_DIR%\node.exe" (
    echo [ERROR] Node.js not found at:
    echo %NODE_DIR%
    goto FAIL
)
echo OK.

echo [2/4] Checking Python venv...
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Python venv not found. Please run setup first.
    goto FAIL
)
echo OK.

echo [3/4] Checking project folders...
if not exist "siteana\apps\backend" (
    echo [ERROR] Cannot find siteana\apps\backend
    goto FAIL
)
if not exist "siteana\apps\frontend" (
    echo [ERROR] Cannot find siteana\apps\frontend
    goto FAIL
)
echo OK.

echo [4/4] Checking Docker (optional)...
docker --version >nul 2>&1
if %errorlevel% equ 0 (
    echo OK - Docker running.
) else (
    echo WARN - Docker not running. Using Mock Mode.
)

echo.
echo ============================================================
echo  All checks passed. Starting services...
echo ============================================================
echo.

set "PATH=%NODE_DIR%;%PATH%"

echo Starting Backend (port 8000)...
start "SiteANA-Backend" cmd /k "venv\Scripts\activate.bat && cd siteana\apps\backend && uvicorn app.main:app --reload --port 8000"

echo Starting Frontend (port 5173)...
start "SiteANA-Frontend" cmd /k "set PATH=%NODE_DIR%;%%PATH%% && cd siteana\apps\frontend && npm run dev"

echo.
echo Done! Open your browser:
echo - Frontend: http://localhost:5173
echo - API Docs: http://127.0.0.1:8000/docs
echo.
echo Press any key to close this window...
pause >nul
exit

:FAIL
echo.
echo ============================================================
echo  [FAILED] Please fix the error above and try again.
echo ============================================================
echo.
pause
exit
