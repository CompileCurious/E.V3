@echo off
REM E.V3 One-Click Launcher

echo ================================================
echo E.V3 Desktop Companion
echo ================================================
echo.

REM Check if already set up
if not exist "venv\Scripts\python.exe" (
    echo First-time setup required...
    echo.
    call setup.bat
    if errorlevel 1 (
        echo Setup failed. Please check errors above.
        pause
        exit /b 1
    )
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if service is already running
tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq E.V3*" 2>NUL | find /I /N "python.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo E.V3 service is already running.
    echo Starting UI only...
    echo.
    start "E.V3 UI" python main_ui.py
) else (
    echo Starting E.V3...
    echo.
    
    REM Start service in background
    start "E.V3 Service" /MIN python main_service.py
    
    REM Wait a moment for service to initialize
    timeout /t 2 /nobreak >NUL
    
    REM Start UI
    start "E.V3 UI" python main_ui.py
)

echo.
echo ================================================
echo E.V3 is now running!
echo ================================================
echo.
echo Your companion should appear in the bottom-right corner.
echo.
echo To stop E.V3:
echo - Close the UI window
echo - Or run: taskkill /FI "WINDOWTITLE eq E.V3*"
echo.
