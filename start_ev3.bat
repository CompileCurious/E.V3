

@echo off
REM E.V3 Complete Launcher - Starts both Kernel and Shell
title E.V3 Launcher

echo ============================================
echo E.V3 - Privacy-Focused Desktop Companion
echo ============================================
echo.

echo Starting Kernel...
start "E.V3 Kernel" /MIN python main_service.py
timeout /t 2 /nobreak > nul

echo Starting Shell...
start "E.V3 Shell" python main_ui.py
timeout /t 1 /nobreak > nul

echo.
echo E.V3 is starting!
echo - Kernel: Background service  
echo - Shell: Minimized to system tray
echo.
echo Note: The mutex ensures only one instance of each component runs.
echo Check system tray for the E.V3 icon (may be in hidden icons area)
echo.
timeout /t 3
