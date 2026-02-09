@echo off
REM E.V3 System Launcher - Starts Kernel + UI

setlocal
cd /d "%~dp0"

REM Check if already running
tasklist /FI "IMAGENAME eq EV3Kernel.exe" 2>NUL | find /I /N "EV3Kernel.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo E.V3 Kernel is already running
    goto shell
)

REM Start C++ Kernel in background
echo Starting E.V3 C++ Kernel...
if exist "kernel_cpp\build\Release\EV3Kernel.exe" (
    start "" "kernel_cpp\build\Release\EV3Kernel.exe"
) else (
    echo ERROR: C++ Kernel not found. Please build it first:
    echo   cd kernel_cpp ^&^& mkdir build ^&^& cd build
    echo   cmake .. -G "Visual Studio 17 2022" -A x64 -DCMAKE_BUILD_TYPE=Release
    echo   cmake --build . --config Release
    exit /b 1
)
timeout /t 2 /nobreak

:shell
REM Start Shell
echo Starting E.V3 Shell...
start "" "dist\Shell\Shell.exe"

endlocal
