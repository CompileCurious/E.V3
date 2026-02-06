@echo off
REM E.V3 Kernel Launcher (Mock/Development Version)
REM
REM Starts the E.V3 kernel with IPC server for shell communication
REM This launcher handles Python path setup and executes the kernel
REM
REM For production: Build C++ kernel with CMake and run the executable
REM For development: Use this batch file with Python mock kernel

setlocal enabledelayedexpansion

REM Get script directory  
set SCRIPT_DIR=%~dp0
set REPO_ROOT=%SCRIPT_DIR%..\..

REM Setup Python path
set PYTHONPATH=%REPO_ROOT%;!PYTHONPATH!

REM Try to find Python
for /f "tokens=*" %%i in ('where python 2^>nul') do set PYTHON=%%i
if not defined PYTHON (
    for /f "tokens=*" %%i in ('where python3 2^>nul') do set PYTHON=%%i
)

if not defined PYTHON (
    echo.
    echo ERROR: Python not found. 
    echo Please install Python 3.10+ or add it to your PATH
    echo.
    pause
    exit /b 1
)

REM Display startup info
echo.
echo ======================================
echo  E.V3 Kernel - Mock Implementation
echo ======================================
echo.
echo Python:        !PYTHON!
echo Repo Root:     %REPO_ROOT%
echo IPC Pipe:      \\.\pipe\E.V3.v2
echo Config:        config/config.yaml
echo Logs:          logs/ev3.log
echo.

REM Create logs directory if needed
if not exist "%REPO_ROOT%\logs" mkdir "%REPO_ROOT%\logs"

REM Change to repo root for config paths
cd /d "%REPO_ROOT%"

REM Launch mock kernel
echo Launching mock kernel...
echo.
!PYTHON! "%SCRIPT_DIR%ev3_kernel.py" -c config/config.yaml

if errorlevel 1 (
    echo.
    echo ERROR: Kernel failed to start (exit code: !ERRORLEVEL!)
    echo Check logs/ev3.log for details
    pause
)

endlocal

