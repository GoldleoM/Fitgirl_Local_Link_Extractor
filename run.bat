@echo off
setlocal
title FitGirl FastLink Extractor
cd /d "%~dp0"

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to PATH.
    echo Running installer...
    call setup.bat
    exit /b 1
)

:: Launch the GUI app (running with pythonw or python)
python app.py
if %errorlevel% neq 0 (
    echo.
    echo An error occurred while running the app.
    echo Trying to reinstall dependencies...
    python -m pip install -r requirements.txt
    python app.py
    pause
)
endlocal
