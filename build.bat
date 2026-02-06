@echo off
REM Build script for E.V3 executables
REM This script builds the Shell UI executable using PyInstaller

setlocal enabledelayedexpansion

echo.
echo ======================================
echo  E.V3 Build System
echo ======================================
echo.

REM Get current directory
set REPO_ROOT=%cd%

echo [1/3] Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found
    exit /b 1
)

echo [2/3] Checking PyInstaller...
python -m pip show pyinstaller > nul 2>&1
if errorlevel 1 (
    echo ERROR: PyInstaller not installed
    echo Install with: pip install pyinstaller
    exit /b 1
)

echo [3/3] Building Shell.exe...
echo.
echo Building with PyInstaller... (this may take 2-5 minutes)
echo.

python -m PyInstaller Shell.spec --distpath build\shell_dist --workpath build\build_temp --noconfirm

if errorlevel 1 (
    echo.
    echo ERROR: Build failed
    exit /b 1
)

echo.
echo ======================================
echo  Build Complete!
echo ======================================
echo.
echo Output:
echo   - Shell.exe:    build\shell_dist\Shell\Shell.exe
echo   - Kernel mock:  kernel_cpp\bin\EV3Kernel.bat
echo.
echo To run:
echo   1. Start kernel:  kernel_cpp\bin\EV3Kernel.bat
echo   2. Start shell:   build\shell_dist\Shell\Shell.exe
echo.

endlocal
