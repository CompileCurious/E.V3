

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

echo.
echo E.V3 is now running!
echo - Kernel: Background service  
echo - Shell: UI with system tray icon
echo.
echo To control: Right-click the system tray icon
echo.
pause
