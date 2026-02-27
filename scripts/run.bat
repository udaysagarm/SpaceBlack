@echo off
if not exist ".venv" (
    echo 🔧 Virtual environment not found. Running setup...
    call scripts\setup.bat
    if %errorlevel% neq 0 (
        pause
        exit /b
    )
)

call .venv\Scripts\activate
python main.py
pause
