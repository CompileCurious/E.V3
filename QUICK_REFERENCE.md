# E.V3 Quick Reference

## Terminology
- **Kernel**: Background service that monitors system events
- **Shell**: Interactive UI with 3D character and system tray icon

## Quick Start
```batch
start_ev3.bat
```
This starts both Kernel and Shell.

## System Tray Icon
**Location**: Windows taskbar, bottom-right (may be in hidden icons area)

**Menu Options:**
- **Show/Hide Shell**: Toggle window visibility
- **Stop Kernel**: Stop background service
- **Exit**: Close Shell application

**Shortcuts:**
- Double-click icon: Show/Hide window
- Right-click icon: Open menu

## Window Controls
- **Move**: Click and drag window
- **Close**: Hides to tray (doesn't exit)
- **Exit**: Use system tray menu

## Files
-- `start_ev3.bat` - Launch both Kernel and Shell
-- `start_kernel.bat` - Launch Kernel only
- `start_shell.bat` - Launch Shell only
-- `main_service.py` - Kernel Python script
- `main_ui.py` - Shell Python script
**Shell can't connect to Kernel:**
- Start Kernel first with `start_kernel.bat`
## Executables (when built)
-- `dist/EV3Kernel.exe` - Background service
- `dist/EV3Shell.exe` - UI application
- `dist/EV3Service.exe` - Old name (same as Daemon)

## Transparency Note
The window should be transparent with only the 3D character visible.
If you see a white box, check:
1. GPU supports OpenGL 2.1+
2. Graphics drivers are up to date
3. Windows Desktop Composition is enabled (default on Win10/11)

## Logs
Located in `logs/ev3.log` (or `dist/logs/ev3.log` for executables)

## Configuration
Edit `config/config.yaml` for settings:
- Window position and size
- Rendering options (FPS, lighting, etc.)
- IPC pipe name
- State machine timings

## Troubleshooting

**No system tray icon:**
- Check Shell is running
- Look in hidden icons (click ^ arrow in taskbar)
- Check Windows notification settings

**Shell can't connect to Kernel:**
- Start Kernel first with `start_kernel.bat`
- Check `logs/ev3.log` for errors
- Verify no firewall blocking

**White box instead of transparent:**
- Update graphics drivers
- Try running as administrator
- Check OpenGL support with `python -c "from OpenGL.GL import *; print(glGetString(GL_VERSION))"`

- **Kernel won't start:**
- Check if already running (only one instance allowed)
- Look in Task Manager for existing python/EV3 processes
- Check logs in `logs/ev3.log`

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/

# Build executables
python build_exe.py

# Clean build artifacts
rmdir /s /q build dist
```

## Key Dependencies
- PySide6 - Qt for GUI
- PyOpenGL - 3D rendering
- pywin32 - Windows API access
- loguru - Logging
- transitions - State machine
- PyYAML - Configuration
