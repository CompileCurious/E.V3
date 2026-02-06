@echo off
REM E.V3 System Launcher - Starts Kernel + UI

setlocal
cd /d "%~dp0"

REM Check if already running
tasklist /FI "IMAGENAME eq EV3Kernel.py" 2>NUL | find /I /N "EV3Kernel.py">NUL
if "%ERRORLEVEL%"=="0" (
    echo E.V3 Kernel is already running
    goto shell
)

REM Start Kernel in background
echo Starting E.V3 Kernel...
start "" python "kernel_cpp\bin\EV3Kernel.py"
timeout /t 2 /nobreak

:shell
REM Start Shell
echo Starting E.V3 Shell...
start "" "dist\Shell\Shell.exe"

endlocal
