@echo off
setlocal enabledelayedexpansion

cd /d "C:\Users\Administrator\Documents\GitHub\E.V3\kernel_cpp"

echo Cleaning build directory...
if exist build rmdir /s /q build
mkdir build
cd build

echo Setting up Visual Studio environment...
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" x86_amd64

echo Configuring CMake...
python -m cmake .. -G "Visual Studio 17 2022" -DCMAKE_BUILD_TYPE=Release -DLLAMA_CUBLAS=ON

if errorlevel 1 (
    echo CMake configuration failed!
    exit /b 1
)

echo Building kernel...
python -m cmake --build . --config Release --parallel

if errorlevel 1 (
    echo Build failed!
    exit /b 1
)

echo Build completed successfully!
echo Output: "C:\Users\Administrator\Documents\GitHub\E.V3\kernel_cpp\build\Release\EV3Kernel.exe"
