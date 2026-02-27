@echo off

:: ghost.bat - CLI Wrapper for Space Black (Windows)
:: Usage: ghost start | ghost update | ghost daemon | ghost --help

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
) else if "%1"=="update" (
    echo 🔄 Updating Space Black...
    git pull --ff-only
    if exist ".venv" (
        echo 📦 Updating dependencies...
        call .venv\Scripts\activate
        pip install -r requirements.txt --quiet
    )
    echo ✅ Update complete! Run 'ghost start' to launch.
) else if "%1"=="daemon" (
    if not exist ".venv" (
        echo 🔧 First run detected. Setting up Space Black...
        call scripts\setup.bat
    )
    echo 👻 Starting Ghost Daemon...
    call .venv\Scripts\activate
    python main.py daemon
) else if "%1"=="--version" (
    echo Space Black v1.0.0
) else if "%1"=="-v" (
    echo Space Black v1.0.0
) else (
    echo.
    echo   Ghost — The AI Agent on Space Black
    echo   Version: 1.0.0
    echo.
    echo   Usage: ghost ^<command^>
    echo.
    echo   Commands:
    echo     start       Launch the Ghost agent TUI (auto-setup on first run^)
    echo     update      Pull latest code and update dependencies
    echo     daemon      Run Ghost as a background service
    echo     help        Show this help message
    echo.
    echo   Options:
    echo     --help      Show this help message
    echo     --version   Show version number
    echo.
    echo   Examples:
    echo     ghost start           Launch the interactive TUI
    echo     ghost update          Update to the latest version
    echo     ghost daemon          Start the background daemon
    echo.
    echo   Docs:   https://spaceblack.info/docs
    echo   GitHub: https://github.com/udaysagarm/SpaceBlack
    echo.
)
