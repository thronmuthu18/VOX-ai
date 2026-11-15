@echo off
title CHAMP Setup Installer
echo ======================================================
echo                 CHAMP SETUP INSTALLER
echo ======================================================
echo.

cd /d "%~dp0"

echo [1/4] Checking Python installation...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH.
    pause
    exit /b 1
)

echo [2/4] Installing / Upgrading pip dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo [3/4] Installing Playwright Chromium browser...
python -m playwright install chromium

echo [4/4] Running system diagnostics...
python diagnostics.py

echo.
echo ======================================================
echo SETUP COMPLETE! Run 'run_champ.bat' to start CHAMP.
echo ======================================================
pause
