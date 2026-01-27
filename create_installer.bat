@echo off
REM Create E.V3 Installer using Inno Setup

echo ================================================
echo E.V3 Installer Builder
echo ================================================
echo.

REM Check if Inno Setup is installed
set INNO_SETUP="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %INNO_SETUP% (
    echo Error: Inno Setup not found
    echo.
    echo Please install Inno Setup 6 from:
    echo https://jrsoftware.org/isinfo.php
    echo.
    pause
    exit /b 1
)

echo Inno Setup found
echo.

REM Check if executables are built
if not exist "dist\EV3_Package\EV3Service.exe" (
    echo Error: Executables not found
    echo.
    echo Please run build.bat first to create executables
    echo.
    pause
    exit /b 1
)

echo Building installer...
echo.

REM Create installer directory
if not exist "installer" mkdir installer

REM Build installer
%INNO_SETUP% installer.iss

if errorlevel 1 (
    echo.
    echo Installer build failed
    pause
    exit /b 1
)

echo.
echo ================================================
echo Installer created successfully!
echo ================================================
echo.
echo Installer location: installer\EV3_Setup_v0.1.0.exe
echo.
echo You can now distribute this installer to users.
echo.
pause
