@echo off
REM Setup Python 3.13 venv for llama-cpp-python
title E.V3 - Setup LLM Environment

echo ============================================
echo E.V3 - LLM Environment Setup
echo ============================================
echo.

REM Check if Python 3.13 is available
py -3.13 --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python 3.13 not found!
    echo.
    echo Please install Python 3.13 from:
    echo https://www.python.org/downloads/
    echo.
    echo Or use winget:
    echo   winget install Python.Python.3.13
    echo.
    pause
    exit /b 1
)

echo Python 3.13 found!
echo.

REM Create venv if it doesn't exist
if not exist ".venv_llama" (
    echo Creating Python 3.13 virtual environment...
    py -3.13 -m venv .venv_llama
    if %errorlevel% neq 0 (
        echo Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo Virtual environment created: .venv_llama
    echo.
)

REM Install llama-cpp-python
echo Installing llama-cpp-python...
echo This may take a few minutes...
echo.

.venv_llama\Scripts\pip.exe install --upgrade pip
.venv_llama\Scripts\pip.exe install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu

if %errorlevel% equ 0 (
    echo.
    echo ============================================
    echo SUCCESS! llama-cpp-python installed
    echo ============================================
    echo.
    echo The Kernel will now use: .venv_llama
    echo The Shell will use: .venv
    echo.
    echo Next: Run start_ev3.bat to launch E.V3
    echo.
) else (
    echo.
    echo ============================================
    echo FAILED to install llama-cpp-python
    echo ============================================
    echo.
    echo The pre-built wheel may not be available yet.
    echo You may need Visual Studio Build Tools.
    echo.
)

pause
