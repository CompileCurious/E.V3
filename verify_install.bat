@echo off
REM Quick test script to verify E.V3 installation

echo ================================================
echo E.V3 Installation Verification
echo ================================================
echo.

REM Check Python
echo [1/5] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo   X Python not found
    echo   Please install Python 3.10 or higher
    goto :error
) else (
    python --version
    echo   OK
)
echo.

REM Check virtual environment
echo [2/5] Checking virtual environment...
if exist "venv\Scripts\python.exe" (
    echo   OK - Virtual environment exists
) else (
    echo   ! Virtual environment not found
    echo   Run setup.bat first
    goto :error
)
echo.

REM Check dependencies
echo [3/5] Checking key dependencies...
call venv\Scripts\activate.bat
python -c "import PySide6; print('  OK - PySide6')" 2>nul || echo   ! PySide6 not installed
python -c "import OpenGL; print('  OK - PyOpenGL')" 2>nul || echo   ! PyOpenGL not installed
python -c "import yaml; print('  OK - PyYAML')" 2>nul || echo   ! PyYAML not installed
python -c "import win32pipe; print('  OK - pywin32')" 2>nul || echo   ! pywin32 not installed
echo.

REM Check configuration
echo [4/5] Checking configuration...
if exist "config\config.yaml" (
    echo   OK - config.yaml exists
) else (
    echo   X config.yaml not found
    goto :error
)

if exist ".env" (
    echo   OK - .env exists
) else (
    echo   ! .env not found (optional)
    echo   Copy .env.example to .env if needed
)
echo.

REM Check directories
echo [5/5] Checking directories...
if exist "models\llm" (
    echo   OK - models/llm/
) else (
    echo   X models/llm/ not found
    goto :error
)

if exist "models\character" (
    echo   OK - models/character/
) else (
    echo   X models/character/ not found
    goto :error
)

if exist "logs" (
    echo   OK - logs/
) else (
    mkdir logs
    echo   OK - logs/ (created)
)
echo.

REM Check LLM model (optional)
if exist "models\llm\*.gguf" (
    echo   OK - LLM model found
) else (
    echo   ! No LLM model found (optional)
    echo   See models/MODEL_SETUP.md to download
)
echo.

REM Check 3D model (optional)
if exist "models\character\*.vrm" (
    echo   OK - VRM character model found
) else if exist "models\character\*.glb" (
    echo   OK - GLB character model found
) else (
    echo   ! No character model found (will use default)
    echo   See models/MODEL_SETUP.md for custom models
)
echo.

REM Run component tests
echo Running component tests...
echo.
python tests\test_components.py
if errorlevel 1 (
    echo.
    echo   ! Some tests failed
    echo   Check errors above
    goto :error
)
echo.

echo ================================================
echo Installation verified successfully!
echo ================================================
echo.
echo You can now run E.V3:
echo   python start.py
echo.
echo Or separately:
echo   python main_service.py  (in terminal 1)
echo   python main_ui.py       (in terminal 2)
echo.
goto :end

:error
echo.
echo ================================================
echo Installation has issues
echo ================================================
echo.
echo Please run setup.bat first:
echo   setup.bat
echo.
pause
exit /b 1

:end
pause
