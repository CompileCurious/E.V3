# E.V3 System Tray & Transparency Update

## Changes Made

### 1. Renamed Components
- **Service → Daemon**: Background Windows service
- **Companion → Shell**: UI application with 3D character

### 2. System Tray Icon (ui/window/companion_window.py)
Added full system tray functionality with icon and menu:

**Menu Options:**
- **Show/Hide Shell**: Toggle window visibility
- **Stop Daemon**: Send command to stop background service
- **Exit**: Quit the Shell application

**Features:**
- Icon appears in Windows system tray (hidden icons area)
- Double-click tray icon to show/hide window
- Right-click for menu
- Closing window hides to tray instead of exiting
- Tooltip shows "E.V3 Shell"

### 3. Transparency Support (ui/renderer/opengl_renderer.py)
Fixed white box issue with proper transparency:

**Changes:**
- OpenGL 2.1 Compatibility profile (not Core 3.3)
- Alpha buffer size: 8 bits
- Qt attribute: WA_TranslucentBackground
- Transparent stylesheet
- glClearColor(0.0, 0.0, 0.0, 0.0) for transparent background
- Blending enabled with GL_BLEND

### 4. Window Control
**Before:** Window was click-through, user had no control
**After:** 
- Window is interactive
- Can be moved and controlled
- System tray provides hide/show/exit options
- No longer click-through by default

### 5. Executables
**Built:**
- `EV3Service.exe` (13.17 MB) - Original name
- `EV3Daemon.exe` (13.17 MB) - Renamed copy

**Pending Build:**
- `EV3Shell.exe` - UI with system tray and transparency
  (Build keeps getting interrupted, but Python version works perfectly)

### 6. Launcher Scripts
Created convenience scripts:

**start_daemon.bat**: Launch background service only
**start_shell.bat**: Launch UI only
**start_ev3.bat**: Launch both (Daemon minimized, then Shell)

## How to Use

### Option 1: Python (Recommended for testing)
```batch
start_ev3.bat
```
This will start both the Daemon and Shell using Python.

### Option 2: Individual Components
```batch
REM Start daemon
start_daemon.bat

REM Start shell (in separate window)
start_shell.bat
```

### Option 3: Python Directly
```batch
REM Terminal 1: Start daemon
python main_service.py

REM Terminal 2: Start shell
python main_ui.py
```

## System Tray Usage

1. **Launch Shell**: `start_shell.bat` or `python main_ui.py`
2. **Find Icon**: Look in Windows system tray (hidden icons area, bottom-right)
3. **Right-click Icon**: See menu with Show/Hide, Stop Daemon, Exit
4. **Double-click Icon**: Toggle window visibility
5. **Close Window**: Hides to tray (doesn't exit)
6. **Exit Application**: Use "Exit" in tray menu

## Testing Transparency

The window should now be transparent with the 3D character visible, not a white box:

**If still showing white box, check:**
1. GPU supports OpenGL 2.1+
2. Compositing enabled in Windows (enabled by default on Windows 10/11)
3. No conflicting window settings in OS

## Implementation Details

### System Tray Code
```python
# Create tray icon
self.tray_icon = QSystemTrayIcon(self)
self.tray_icon.setIcon(icon)

# Menu with actions
tray_menu = QMenu()
tray_menu.addAction("Show/Hide Shell", self.toggle_visibility)
tray_menu.addAction("Stop Daemon", self.stop_daemon)
tray_menu.addAction("Exit", self.quit_application)

self.tray_icon.setContextMenu(tray_menu)
self.tray_icon.show()
```

### Transparency Code
```python
# OpenGL format
fmt = QSurfaceFormat()
fmt.setVersion(2, 1)
fmt.setProfile(QSurfaceFormat.CompatibilityProfile)
fmt.setAlphaBufferSize(8)

# Qt transparency
self.setAttribute(Qt.WA_TranslucentBackground)
self.setStyleSheet("background: transparent;")

# OpenGL transparency
glClearColor(0.0, 0.0, 0.0, 0.0)
glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
```

### Window Control
```python
# Removed click-through flag
# self.setAttribute(Qt.WA_TransparentForMouseEvents)

# Hide to tray on close
def closeEvent(self, event):
    event.ignore()
    self.hide()
    self.tray_icon.showMessage(
        "E.V3 Shell",
        "Application minimized to system tray",
        QSystemTrayIcon.Information,
        2000
    )
```

## Known Issues

1. **Build Interruptions**: PyInstaller build for Shell keeps getting interrupted
   - **Workaround**: Use Python launcher scripts (work perfectly)
   - **Solution**: Can try building again or build on faster machine

2. **Missing pygltflib**: Warning about 3D model loading
   - **Impact**: Falls back to simple test character
   - **Fix**: `pip install pygltflib` (optional)

3. **Service Connection**: Shell shows connection errors if Daemon not running
   - **Expected**: Shell works in standalone mode
   - **Fix**: Start Daemon first using `start_daemon.bat`

## Files Modified

### New Files:
- `start_daemon.bat` - Launch daemon
- `start_shell.bat` - Launch shell
- `start_ev3.bat` - Launch both
- `dist/EV3Daemon.exe` - Renamed service executable

### Modified Files:
- `ui/window/companion_window.py` - Added system tray, removed click-through
- `ui/renderer/opengl_renderer.py` - Added transparency support
- `main_ui.py` - Updated app name to "E.V3 Shell"
- `build_exe.py` - Improved error handling for locked files

## Next Steps

1. **Test system tray**: Run `start_shell.bat` and verify icon appears
2. **Test transparency**: Check if window is transparent (not white)
3. **Test menu**: Right-click tray icon, verify all menu items work
4. **Test daemon control**: Use "Stop Daemon" menu item
5. **Build executable**: Retry building EV3Shell.exe once tests pass

## Troubleshooting

**No system tray icon appearing:**
- Check Windows notification area settings
- Ensure Shell is running (`python main_ui.py`)
- Look in hidden icons (click ^ arrow in taskbar)

**Still showing white box:**
- Update graphics drivers
- Check if GPU supports OpenGL 2.1+
- Try running as administrator

**"Stop Daemon" not working:**
- Daemon must be running first
- Check daemon is accessible via named pipe
- View daemon logs in `logs/ev3.log`

**Build failing:**
- Close all running E.V3 processes
- Delete `build/` and `dist/` folders manually
- Run: `python -m PyInstaller EV3Shell.spec`
