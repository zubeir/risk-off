@echo off
setlocal enabledelayedexpansion

set ROOT=%~dp0
set VENV=%ROOT%.venv
set PY=%VENV%\Scripts\python.exe

set PORT=8000
if not "%~1"=="" set PORT=%~1

for /f "tokens=5" %%p in ('netstat -ano ^| findstr /R /C:":%PORT% .*LISTENING"') do (
  echo Stopping PID %%p on port %PORT%
  taskkill /PID %%p /F >nul 2>nul
)

if not exist "%PY%" (
  python -m venv "%VENV%"
)

"%PY%" -m pip install --upgrade pip
"%PY%" -m pip install -r "%ROOT%requirements.txt"

"%PY%" -m uvicorn app.main:app --host 127.0.0.1 --port %PORT%
