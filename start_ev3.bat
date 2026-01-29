

@echo off
REM E.V3 Complete Launcher - Starts both Kernel and Shell
title E.V3 Launcher

echo ============================================
echo E.V3 - Privacy-Focused Desktop Companion
echo ============================================
echo.

echo Starting Kernel...
REM Use portable Python 3.13 for Kernel (has llama-cpp-python), .venv for Shell
start "E.V3 Kernel" /MIN .python313_portable\python.exe main_service.py
timeout /t 2 /nobreak > nul

echo Starting Shell...
start "E.V3 Shell" /MIN .venv\Scripts\pythonw.exe main_ui.py
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
