@echo off

:: ghost.bat - CLI Wrapper for Space Black (Windows)
:: Usage: ghost start | ghost daemon | ghost help

if "%1"=="start" (
    :: Auto-setup on first run
    if not exist ".venv" (
        echo 🔧 First run detected. Setting up Space Black...
        call scripts\setup.bat
        if %errorlevel% neq 0 (
            echo ❌ Setup failed.
            pause
            exit /b
        )
    )
    echo 🚀 Launching Ghost...
    call scripts\run.bat
) else if "%1"=="daemon" (
    if not exist ".venv" (
        echo 🔧 First run detected. Setting up Space Black...
        call scripts\setup.bat
    )
    echo 👻 Starting Ghost Daemon...
    call .venv\Scripts\activate
    python main.py daemon
) else (
    echo Ghost — The AI Agent on Space Black
    echo.
    echo Usage: ghost ^<command^>
    echo.
    echo Commands:
    echo   start   Launch the Ghost agent (auto-setup on first run^)
    echo   daemon  Start the background daemon service
    echo   help    Show this help message
    echo.
)
