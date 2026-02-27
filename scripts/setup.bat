@echo off
echo Setting up Space Black for Windows...

:: 1. Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found. Please install Python 3.10+ and add it to PATH.
    pause
    exit /b
)

:: 2. Create venv
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
) else (
    echo Virtual environment found.
)

:: 3. Install
echo Installing dependencies...
call .venv\Scripts\activate
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo ❌ Installation failed.
    pause
    exit /b
)

echo.
echo Setup Complete!
echo.
echo To start, run:
echo    ghost start
pause
