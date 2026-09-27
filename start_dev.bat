@echo off
title FD-LMS Local Development Server
cd /d "%~dp0"

echo =========================================================
echo       FD-LMS: Starting Local Development Server
echo =========================================================
echo Database: Local PostgreSQL 16 (Port 5433 - Offline Isolated Dev)
echo.

if exist "venv\Scripts\python.exe" (
    echo [OK] Using virtual environment: venv
    venv\Scripts\python.exe run.py
) else (
    echo [INFO] Virtual environment not found, attempting global python...
    python run.py
)

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Server exited with an error.
    pause
)
