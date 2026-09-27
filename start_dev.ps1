# FD-LMS Local Development Server Launcher (PowerShell)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "      FD-LMS: Starting Local Development Server" -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "Database: Supabase Cloud (Single source of truth)`n" -ForegroundColor Yellow

$PythonExe = Join-Path $ScriptDir "venv\Scripts\python.exe"
if (Test-Path $PythonExe) {
    Write-Host "[OK] Using virtual environment: venv" -ForegroundColor Green
    & $PythonExe run.py
} else {
    Write-Host "[INFO] Virtual environment not found, attempting global python..." -ForegroundColor Yellow
    python run.py
}
