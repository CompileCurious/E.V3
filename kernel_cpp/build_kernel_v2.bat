@echo off
setlocal

cd /d "C:\Users\Administrator\Documents\GitHub\E.V3\kernel_cpp"

if exist build rmdir /s /q build
mkdir build
cd build

REM Set up Visual Studio environment
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"

REM Call cmake directly from Python path
"C:\Users\Administrator\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m cmake .. -G "Visual Studio 17 2022" -DCMAKE_BUILD_TYPE=Release -DLLAMA_CUBLAS=ON

if errorlevel 1 (
    echo CMake config failed
    exit /b 1
)

REM Build
"C:\Users\Administrator\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m cmake --build . --config Release --parallel

if errorlevel 1 (
    echo Build failed
    exit /b 1  
)

echo Build complete! Check for EV3Kernel.exe in Release folder
dir Release\*.exe
