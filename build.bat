@echo off
REM Build E.V3 executables

echo ================================================
echo E.V3 Executable Builder
echo ================================================
echo.

REM Check if virtual environment is activated
if not defined VIRTUAL_ENV (
    if exist "venv\Scripts\activate.bat" (
        echo Activating virtual environment...
        call venv\Scripts\activate.bat
    )
)

REM Run build script
python3 build_exe.py

if errorlevel 1 (
    echo.
    echo Build failed. Check errors above.
    pause
    exit /b 1
)

echo.
echo ================================================
echo Build successful!
echo ================================================
echo.
echo Executable package is in: dist\EV3_Package\
echo.
echo You can now:
echo 1. Test the executables: cd dist\EV3_Package ^&^& Start_EV3.bat
echo 2. Create a zip for distribution
echo 3. Create an installer (see create_installer.bat)
echo.
pause
