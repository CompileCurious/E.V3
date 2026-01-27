@echo off
REM E.V3 Complete Launcher - Executable Version
REM Starts both Daemon.exe and Shell.exe from dist folder
title E.V3 Launcher

echo ============================================
echo E.V3 - Privacy-Focused Desktop Companion
echo ============================================
echo.

if not exist "dist\Daemon.exe" (
    echo ERROR: Daemon.exe not found in dist folder!
    echo Please build executables first: python build_exe.py
    echo.
    echo Using Python version instead...
    echo.
    start_ev3.bat
    exit /b
)

if not exist "dist\Shell.exe" (
    echo WARNING: Shell.exe not found in dist folder!
    echo Using Python version for Shell...
    echo.
)

cd dist

echo Starting Daemon...
start "E.V3 Daemon" /MIN Daemon.exe
timeout /t 2 /nobreak > nul

if exist "Shell.exe" (
    echo Starting Shell...
    start "E.V3 Shell" Shell.exe
) else (
    echo Starting Shell ^(Python^)...
    cd ..
    start "E.V3 Shell" python main_ui.py
    cd dist
)

cd ..

echo.
echo E.V3 is now running!
echo - Daemon: Background service
echo - Shell: UI with system tray icon
echo.
echo To control: Right-click the system tray icon
echo.
pause
