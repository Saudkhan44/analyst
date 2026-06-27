@echo off
REM Startup script for AI Analytics Dashboard backend (Windows)

setlocal enabledelayedexpansion

echo.
echo =========================================
echo AI Analytics Dashboard Backend Startup
echo =========================================
echo.

REM Check Python version
echo Checking Python version...
python --version
if errorlevel 1 (
    echo Error: Python not found or not in PATH
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install dependencies
    pause
    exit /b 1
)
echo Dependencies installed

REM Check if .env file exists
if not exist ".env" (
    echo Creating .env file...
    copy .env.example .env
    echo Please edit .env with your configuration
    pause
    exit /b 1
)

REM Start the application
echo.
echo Starting FastAPI application...
echo API documentation available at: http://localhost:8000/docs
echo Press Ctrl+C to stop
echo.

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause
