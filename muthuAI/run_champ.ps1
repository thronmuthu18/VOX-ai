# CHAMP AI Personal Assistant — PowerShell Launcher

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "                CHAMP STARTING UP...                 " -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $PSScriptRoot

# Check Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ ERROR: Python is not installed or not in PATH." -ForegroundColor Red
    Write-Host "Please install Python 3.10+ and add it to PATH."
    Read-Host "Press Enter to exit"
    exit 1
}

# Run diagnostics
Write-Host "Running system diagnostics check..." -ForegroundColor Yellow
python diagnostics.py
Write-Host ""

# Launch CHAMP
Write-Host "Launching CHAMP Personal Assistant..." -ForegroundColor Green
python launcher.py
Write-Host ""
