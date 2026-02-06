@echo off
setlocal enabledelayedexpansion

REM Set up the MSVC environment
set VS_PATH=C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools
call "%VS_PATH%\VC\Auxiliary\Build\vcvars64.bat" x86_amd64

REM Define paths
set CL_EXE=%VS_PATH%\VC\Tools\MSVC\14.44.35207\bin\Hostx64\x64\cl.exe
set LINK_EXE=%VS_PATH%\VC\Tools\MSVC\14.44.35207\bin\Hostx64\x64\link.exe
set INCDIR=%VS_PATH%\VC\Tools\MSVC\14.44.35207\include
set LIBDIR=%VS_PATH%\VC\Tools\MSVC\14.44.35207\lib\x64

cd /d C:\Users\Administrator\Documents\GitHub\E.V3\kernel_cpp

echo Compiling E.V3 Kernel with MSVC CL...

if exist build\Release rmdir /s /q build\Release
mkdir build\Release
cd build\Release

REM Compile object files
echo Compiling source files...

%CL_EXE% /std:c++latest /O2 /EHsc ^
  /I ..\..\include ^
  /I "%INCDIR%" ^
  /Fo. ^
  ..\..\src\event_bus.cpp ^
  ..\..\src\main.cpp ^
  ..\..\src\python_bindings.cpp

if errorlevel 1 (
    echo Compilation failed!
    cd ..\.
    exit /b 1
)

REM Link - no manifest
echo Linking...
%LINK_EXE% /OUT:EV3Kernel.exe /SUBSYSTEM:CONSOLE /NOLOGO ^
  event_bus.obj main.obj python_bindings.obj ^
  /LIBPATH:"%LIBDIR%" ^
  kernel32.lib user32.lib

if errorlevel 1 (
    echo Linking failed!
    cd ..\.
    exit /b 1
)

cd ..\.
echo Build completed successfully!
echo Output: C:\Users\Administrator\Documents\GitHub\E.V3\kernel_cpp\build\Release\EV3Kernel.exe

if exist build\Release\EV3Kernel.exe (
    echo Executable created:
    dir build\Release\EV3Kernel.exe
) else (
    echo ERROR: Executable not created!
)
