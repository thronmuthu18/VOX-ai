@echo off
title CHAMP AI Personal Assistant
echo ======================================================
echo                 CHAMP STARTING UP...
echo ======================================================
echo.

cd /d "%~dp0"

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.10+ and add it to PATH.
    pause
    exit /b 1
)

echo Running system diagnostics check...
python diagnostics.py
echo.

echo Launching CHAMP Personal Assistant...
python launcher.py
echo.
pause
