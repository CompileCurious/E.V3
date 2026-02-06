@echo off
setlocal enabledelayedexpansion

set LLVM_PATH=C:\LLVM
set CXX=%LLVM_PATH%\bin\clang++.exe
set CC=%LLVM_PATH%\bin\clang.exe

cd /d C:\Users\Administrator\Documents\GitHub\E.V3\kernel_cpp

echo Compiling E.V3 Kernel with Clang...
echo Output: build\Release\EV3Kernel.exe

if exist build\Release rmdir /s /q build\Release
mkdir build\Release

REM Compile source files
echo Compiling source files...
%CXX% -std=c++20 -O3 ^
  -I include ^
  -I . ^
  src\event_bus.cpp ^
  src\main.cpp ^
  src\python_bindings.cpp ^
  -o build\Release\EV3Kernel.exe ^
  -pthread

if errorlevel 1 (
    echo Compilation failed!
    exit /b 1
)

echo Build completed successfully!
echo Output: C:\Users\Administrator\Documents\GitHub\E.V3\kernel_cpp\build\Release\EV3Kernel.exe

REM Verify the output
if exist build\Release\EV3Kernel.exe (
    echo Executable created successfully
    dir build\Release\EV3Kernel.exe
) else (
    echo ERROR: Executable not created!
)
