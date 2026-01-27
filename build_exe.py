"""
Build script for creating E.V3 executables
Creates standalone .exe files for both service and UI
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

print("=" * 60)
print("E.V3 Build Script")
print("Creating standalone executables")
print("=" * 60)
print()

# Check if PyInstaller is installed
try:
    import PyInstaller
    print("✓ PyInstaller found")
except ImportError:
    print("✗ PyInstaller not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    print("✓ PyInstaller installed")

print()

# Clean previous builds
print("[1/5] Cleaning previous builds...")
for folder in ["build", "dist"]:
    if os.path.exists(folder):
        shutil.rmtree(folder)
        print(f"  Removed {folder}/")
print("  ✓ Clean")
print()

# Build service executable
print("[2/5] Building service executable...")
service_cmd = [
    sys.executable, "-m", "PyInstaller",
    "--name=EV3Service",
    "--onefile",
    "--noconsole",
    "--icon=assets/icon.ico" if os.path.exists("assets/icon.ico") else "",
    "--add-data=config;config",
    "--hidden-import=win32timezone",
    "--hidden-import=pywintypes",
    "--hidden-import=win32api",
    "--hidden-import=win32event",
    "--hidden-import=win32service",
    "--hidden-import=servicemanager",
    "main_service.py"
]
service_cmd = [arg for arg in service_cmd if arg]  # Remove empty strings

try:
    subprocess.check_call(service_cmd)
    print("  ✓ Service executable built")
except subprocess.CalledProcessError as e:
    print(f"  ✗ Failed to build service: {e}")
    sys.exit(1)
print()

# Build UI executable
print("[3/5] Building UI executable...")
ui_cmd = [
    sys.executable, "-m", "PyInstaller",
    "--name=EV3Companion",
    "--onefile",
    "--windowed",
    "--icon=assets/icon.ico" if os.path.exists("assets/icon.ico") else "",
    "--add-data=config;config",
    "--hidden-import=PySide6.QtCore",
    "--hidden-import=PySide6.QtGui",
    "--hidden-import=PySide6.QtWidgets",
    "--hidden-import=PySide6.QtOpenGL",
    "--hidden-import=PySide6.QtOpenGLWidgets",
    "--hidden-import=OpenGL",
    "--hidden-import=OpenGL.GL",
    "--hidden-import=OpenGL.GLU",
    "main_ui.py"
]
ui_cmd = [arg for arg in ui_cmd if arg]

try:
    subprocess.check_call(ui_cmd)
    print("  ✓ UI executable built")
except subprocess.CalledProcessError as e:
    print(f"  ✗ Failed to build UI: {e}")
    sys.exit(1)
print()

# Create distribution package
print("[4/5] Creating distribution package...")
dist_folder = Path("dist/EV3_Package")
dist_folder.mkdir(exist_ok=True)

# Copy executables
shutil.copy("dist/EV3Service.exe", dist_folder / "EV3Service.exe")
shutil.copy("dist/EV3Companion.exe", dist_folder / "EV3Companion.exe")
print("  ✓ Executables copied")

# Copy configuration
shutil.copytree("config", dist_folder / "config", dirs_exist_ok=True)
print("  ✓ Configuration copied")

# Copy models folder structure
(dist_folder / "models" / "llm").mkdir(parents=True, exist_ok=True)
(dist_folder / "models" / "character").mkdir(parents=True, exist_ok=True)
shutil.copy("models/MODEL_SETUP.md", dist_folder / "models/MODEL_SETUP.md")
print("  ✓ Model folders created")

# Copy documentation
for doc in ["README.md", "QUICKSTART.md", "USAGE_GUIDE.md", "CHANGELOG.md"]:
    if os.path.exists(doc):
        shutil.copy(doc, dist_folder / doc)
print("  ✓ Documentation copied")

# Copy .env.example
shutil.copy(".env.example", dist_folder / ".env.example")
print("  ✓ Environment template copied")

# Create logs folder
(dist_folder / "logs").mkdir(exist_ok=True)
print("  ✓ Logs folder created")

print()

# Create launchers
print("[5/5] Creating launcher scripts...")

# Windows launcher
launcher_bat = dist_folder / "Start_EV3.bat"
with open(launcher_bat, "w") as f:
    f.write("""@echo off
title E.V3 Companion
echo ================================================
echo E.V3 Privacy-Focused Desktop Companion
echo ================================================
echo.
echo Starting service...
start "EV3 Service" /MIN EV3Service.exe
timeout /t 2 /nobreak >NUL
echo Starting UI...
start "EV3 UI" EV3Companion.exe
echo.
echo ================================================
echo E.V3 is now running!
echo ================================================
echo.
echo Your companion should appear in the bottom-right corner.
echo Close this window - the service will continue running.
echo.
pause
""")
print("  ✓ Start_EV3.bat created")

# Service installer wrapper
installer_bat = dist_folder / "Install_Service.bat"
with open(installer_bat, "w") as f:
    f.write("""@echo off
title E.V3 Service Installer
echo ================================================
echo E.V3 Windows Service Installer
echo ================================================
echo.
echo This will install E.V3 as a Windows service.
echo The service will auto-start with Windows.
echo.
echo Administrative privileges required.
echo.
pause

echo.
echo Installing service...
EV3Service.exe install
if errorlevel 1 (
    echo.
    echo Failed to install service.
    echo Make sure you run this as Administrator.
    pause
    exit /b 1
)

echo.
echo Starting service...
net start EV3CompanionService

echo.
echo ================================================
echo Service installed and started successfully!
echo ================================================
echo.
echo The service will now start automatically with Windows.
echo Run EV3Companion.exe to show the UI.
echo.
pause
""")
print("  ✓ Install_Service.bat created")

# Uninstaller
uninstaller_bat = dist_folder / "Uninstall_Service.bat"
with open(uninstaller_bat, "w") as f:
    f.write("""@echo off
title E.V3 Service Uninstaller
echo ================================================
echo E.V3 Windows Service Uninstaller
echo ================================================
echo.
pause

echo Stopping service...
net stop EV3CompanionService 2>NUL

echo Uninstalling service...
EV3Service.exe remove

echo.
echo ================================================
echo Service uninstalled
echo ================================================
echo.
pause
""")
print("  ✓ Uninstall_Service.bat created")

# Create README for distribution
readme_dist = dist_folder / "START_HERE.txt"
with open(readme_dist, "w") as f:
    f.write("""================================================
E.V3 Privacy-Focused Desktop Companion
================================================

QUICK START:
1. Double-click: Start_EV3.bat
2. Your companion will appear in the bottom-right corner

FIRST TIME SETUP:
1. (Optional) Download AI model:
   - See models/MODEL_SETUP.md
   - Place in models/llm/

2. (Optional) Add 3D character:
   - Place .vrm or .glb file in models/character/
   - Edit config/config.yaml to set path

3. (Optional) Configure calendar:
   - Copy .env.example to .env
   - Add your API credentials

RUNNING OPTIONS:

Option 1: Standalone Mode
- Run: Start_EV3.bat
- Service and UI run together
- Close when done

Option 2: Windows Service (Recommended)
- Run: Install_Service.bat (as Administrator)
- Service runs in background
- Run: EV3Companion.exe to show UI
- To uninstall: Uninstall_Service.bat

MANUAL START:
- Service: EV3Service.exe
- UI: EV3Companion.exe

FEATURES:
✓ Privacy-first design
✓ Local AI processing (with model)
✓ System event monitoring
✓ Calendar reminders
✓ 3D animated character

DOCUMENTATION:
- QUICKSTART.md - Quick setup guide
- README.md - Full documentation
- USAGE_GUIDE.md - User manual

PRIVACY:
All data stays on your computer by default.
No telemetry, no data collection.

SUPPORT:
Check logs/ folder for troubleshooting.

Enjoy E.V3!
""")
print("  ✓ START_HERE.txt created")

print()
print("=" * 60)
print("✓ Build Complete!")
print("=" * 60)
print()
print(f"Distribution package created in: {dist_folder.absolute()}")
print()
print("Contents:")
print("  - EV3Service.exe       (Background service)")
print("  - EV3Companion.exe     (UI application)")
print("  - Start_EV3.bat        (Quick launcher)")
print("  - Install_Service.bat  (Service installer)")
print("  - Uninstall_Service.bat (Service uninstaller)")
print("  - config/              (Configuration files)")
print("  - models/              (Model folders)")
print("  - Documentation files")
print()
print("To distribute:")
print(f"  Zip the folder: {dist_folder.name}")
print("  Share with users")
print()
print("To test:")
print(f"  cd {dist_folder}")
print("  Start_EV3.bat")
print()
