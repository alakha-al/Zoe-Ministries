@echo off
title Zoe Lead Generator — Setup ^& Run
color 0A
echo.
echo  ============================================
echo   Zoe Lead Generator — Windows Setup ^& Run
echo  ============================================
echo.

:: ── Check Python ─────────────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python is not installed or not on PATH.
    echo.
    echo  Please download and install Python from:
    echo    https://www.python.org/downloads/
    echo.
    echo  IMPORTANT: During install, tick "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo  [OK] %PYVER% found
echo.

:: ── Move to script directory ──────────────────────────────────────────────────
cd /d "%~dp0"
echo  [INFO] Working directory: %CD%
echo.

:: ── Install dependencies ──────────────────────────────────────────────────────
echo  [INFO] Installing required packages...
echo.
pip install flask requests beautifulsoup4 lxml openpyxl apscheduler python-dotenv --quiet
if errorlevel 1 (
    echo  [ERROR] pip install failed. Check your internet connection.
    pause
    exit /b 1
)
echo  [OK] All packages installed.
echo.

:: ── Start Flask ───────────────────────────────────────────────────────────────
echo  ============================================
echo   Starting Flask server...
echo   Open your browser at: http://localhost:5000
echo.
echo   Press Ctrl+C to stop the server.
echo  ============================================
echo.

python app.py

pause
