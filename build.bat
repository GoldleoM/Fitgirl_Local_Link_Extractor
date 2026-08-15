@echo off
setlocal enabledelayedexpansion
title FitGirl FastLink Extractor - Standalone EXE Builder
color 0B

echo ======================================================================
echo           FitGirl Link Extractor - Standalone EXE Builder
echo ======================================================================
echo.

:: 1. Check Python
echo [1/4] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] Python is NOT installed or NOT found in PATH.
    echo Please install Python 3.10+ from python.org and add it to PATH.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo [OK] Found %%i
echo.

:: 2. Install / Verify Requirements & PyInstaller
echo [2/4] Verifying required build dependencies (CustomTkinter, DrissionPage, PyInstaller)...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] Failed to install build dependencies.
    pause
    exit /b 1
)
echo [OK] Build dependencies verified.
echo.

:: 3. Build Standalone Executable with PyInstaller
echo [3/4] Building standalone executable with PyInstaller...
echo Packing app into a single file executable... Please wait, this takes ~30-60 seconds...
echo.

python -m PyInstaller ^
    --onefile ^
    --noconsole ^
    --name "FitGirl_Link_Extractor" ^
    --collect-all customtkinter ^
    --collect-all DrissionPage ^
    --collect-all darkdetect ^
    --collect-all bs4 ^
    --clean ^
    --noconfirm ^
    app.py

if %errorlevel% neq 0 (
    color 0C
    echo.
    echo [ERROR] PyInstaller build failed! Please check the output above.
    pause
    exit /b 1
)

:: 4. Copy to root directory for convenient access
echo.
echo [4/4] Finalizing build...
if exist "dist\FitGirl_Link_Extractor.exe" (
    copy /y "dist\FitGirl_Link_Extractor.exe" "FitGirl_Link_Extractor.exe" >nul
    certutil -hashfile "FitGirl_Link_Extractor.exe" SHA256 | findstr /r "^[0-9A-F][0-9A-F]" > "FitGirl_Link_Extractor.exe.sha256"
    color 0A
    echo ======================================================================
    echo [SUCCESS] Standalone executable created successfully!
    echo ======================================================================
    echo.
    echo Executable location:
    echo   -^> .\FitGirl_Link_Extractor.exe
    echo   -^> .\dist\FitGirl_Link_Extractor.exe
    echo   -^> .\FitGirl_Link_Extractor.exe.sha256
    echo.
    echo You can now send 'FitGirl_Link_Extractor.exe' to ANY Windows device.
    echo No Python installation or setup scripts needed on their machine!
    echo.
) else (
    color 0C
    echo [ERROR] Executable was not found in dist folder.
    pause
    exit /b 1
)

pause
endlocal
