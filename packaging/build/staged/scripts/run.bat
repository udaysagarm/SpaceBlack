@echo off
if not exist ".venv" (
    echo ❌ Virtual environment not found. Please run setup.bat first.
    pause
    exit /b
)

call .venv\Scripts\activate
python main.py
pause
