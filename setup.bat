@echo off
setlocal enabledelayedexpansion
title FitGirl FastLink Extractor - Setup & Installer
color 0B

echo ======================================================================
echo           FitGirl FastLink Extractor - Automated Setup
echo ======================================================================
echo.

:: 1. Check if Python is installed
echo [1/3] Checking for Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo.
    echo [ERROR] Python is NOT installed or NOT found in your system PATH!
    echo.
    echo Please download and install Python from:
    echo   https://www.python.org/downloads/
    echo.
    echo IMPORTANT: Make sure to check the box:
    echo   [x] "Add python.exe to PATH" during installation!
    echo.
    echo After installing Python, run this installer again.
    echo ======================================================================
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYTHON_VER=%%i
echo [OK] Found %PYTHON_VER%
echo.

:: 2. Check and install dependencies
echo [2/3] Installing and verifying required packages from requirements.txt...
echo This may take a few moments...
echo.

python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    color 0C
    echo.
    echo [ERROR] Failed to install some requirements.
    echo Please check your internet connection or run 'pip install -r requirements.txt' manually.
    echo.
    pause
    exit /b 1
)

echo.
echo [OK] All dependencies successfully installed!
echo.

:: 3. Setup Complete
color 0A
echo ======================================================================
echo [3/3] Setup Completed Successfully!
echo ======================================================================
echo.
echo You can now run the application anytime using 'run.bat'.
echo.
set /p LAUNCH="Do you want to launch the GUI app right now? (Y/N): "
if /i "%LAUNCH%"=="Y" (
    echo Launching FitGirl FastLink Extractor...
    start "" python app.py
)

endlocal
