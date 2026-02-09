@echo off
setlocal

cd /d "%~dp0kernel_cpp\build"

echo Building C++ Kernel...
python -m cmake --build . --config Release --parallel 4

if errorlevel 1 (
    echo Build failed!
    pause
    exit /b 1
)

echo.
echo Build complete!
if exist "..\..\dist\Kernel\EV3Kernel.exe" (
    echo Output: dist\Kernel\EV3Kernel.exe
    dir "..\..\dist\Kernel\EV3Kernel.exe"
) else (
    echo WARNING: EV3Kernel.exe not found in expected location
)

pause
