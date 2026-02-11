@echo off

if "%1"=="onboard" (
    echo Starting One-Time Setup...
    call scripts\setup.bat
) else if "%1"=="start" (
    echo Launching Space Black...
    call scripts\run.bat
) else (
    echo Usage: spaceblack [command]
    echo.
    echo Commands:
    echo   onboard  -^> Run this ONCE when you first install the app.
    echo   start    -^> Run this EVERY TIME you want to use the app.
    echo.
)
