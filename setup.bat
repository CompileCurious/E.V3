@echo off
REM E.V3 Setup Script for Windows

echo ================================================
echo E.V3 Privacy-Focused Desktop Companion
echo Setup Script
echo ================================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.10 or higher from https://www.python.org/
    pause
    exit /b 1
)

echo [1/6] Python found
echo.

REM Create virtual environment
echo [2/6] Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo Virtual environment created
) else (
    echo Virtual environment already exists
)
echo.

REM Activate virtual environment
echo [3/6] Activating virtual environment...
call venv\Scripts\activate.bat
echo.

REM Upgrade pip
echo [4/6] Upgrading pip...
python -m pip install --upgrade pip
echo.

REM Install dependencies
echo [5/6] Installing dependencies...
pip install -r requirements.txt
echo.

REM Create necessary directories
echo [6/6] Creating directories...
if not exist "logs" mkdir logs
if not exist "models\llm" mkdir models\llm
if not exist "models\character" mkdir models\character
if not exist "config\credentials" mkdir config\credentials
echo.

REM Copy environment template
if not exist ".env" (
    copy .env.example .env
    echo Created .env file from template
    echo Please edit .env and add your API keys
)
echo.

echo ================================================
echo Setup Complete!
echo ================================================
echo.
echo Next steps:
echo.
echo 1. Edit .env file and add your API keys (optional)
echo 2. Download Mistral 7B model (optional, for local LLM):
echo    https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF
echo    Place the .gguf file in models/llm/
echo.
echo 3. Add your VRoid or Blender model (optional):
echo    Place .vrm or .glb file in models/character/
echo    Update model path in config/config.yaml
echo.
echo 4. Run the service:
echo    python main_service.py
echo.
echo 5. Run the UI (in another terminal):
echo    python main_ui.py
echo.
echo 6. To install as Windows service (requires admin):
echo    python install_service.py install
echo.
pause
