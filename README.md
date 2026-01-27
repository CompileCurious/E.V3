# E.V3 - Privacy-Focused Desktop Companion

A privacy-first desktop companion with a 3D animated character consisting of a background daemon and interactive shell.

## Features

- **Privacy First**: No data scraping, no raw logs sent, all processing local by default
- **Native Windows Daemon**: Runs in background, monitors system events
- **Interactive Shell**: System tray control with Show/Hide, Stop Daemon, Exit menu
- **3D Animated Character**: VRoid/Blender models with bone animations and blendshapes
- **Local LLM**: Mistral 7B quantized for personality and event interpretation
- **Optional External LLM**: GPT mini API only when explicitly requested
- **Event Monitoring**: Windows Defender, Firewall, System notifications
- **Calendar Integration**: Surface reminders from your calendar
- **Transparent UI**: Frameless window with proper transparency support
- **System Tray Control**: Full control via system tray icon
- **Native IPC**: Fast communication between daemon and shell

## Architecture

```
┌─────────────────────────────────────┐
│   E.V3 Daemon (Background Service)  │
│  ┌──────────────────────────────┐   │
│  │   State Machine               │   │
│  │   (idle/scanning/alert/       │   │
│  │    reminder)                  │   │
│  └──────────────────────────────┘   │
│  ┌──────────────────────────────┐   │
│  │   Event Listeners             │   │
│  │   - Windows Defender          │   │
│  │   - Firewall                  │   │
│  │   - System Notifications      │   │
│  └──────────────────────────────┘   │
│  ┌──────────────────────────────┐   │
│  │   LLM Integration             │   │
│  │   - Local: Mistral 7B         │   │
│  │   - External: GPT mini        │   │
│  └──────────────────────────────┘   │
│  ┌──────────────────────────────┐   │
│  │   Calendar Integration        │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
              │
              │ Native IPC
              │ (Named Pipes)
              ▼
┌─────────────────────────────────────┐
│   E.V3 Shell (3D UI with Tray)      │
│  ┌──────────────────────────────┐   │
│  │   System Tray Icon            │   │
│  │   - Show/Hide Shell           │   │
│  │   - Stop Daemon               │   │
│  │   - Exit                      │   │
│  └──────────────────────────────┘   │
│  ┌──────────────────────────────┐   │
│  │   Transparent Window          │   │
│  │   Bottom-right, Moveable      │   │
│  └──────────────────────────────┘   │
│  ┌──────────────────────────────┐   │
│  │   3D Model Renderer           │   │
│  │   - Bone animations           │   │
│  │   - Blendshapes               │   │
│  │   - Glow effects              │   │
│  └──────────────────────────────┘   │
│  ┌──────────────────────────────┐   │
│  │   Animation Controller        │   │
│  │   - Idle breathing            │   │
│  │   - Eye blinking              │   │
│  │   - Alert poses               │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
```

## Project Structure

```
E.V3/
├── service/              # Background service
│   ├── core/            # Core service logic
│   ├── events/          # Event listeners
│   ├── llm/             # LLM integration
│   ├── calendar/        # Calendar integration
│   └── state/           # State machine
├── ui/                  # 3D UI layer
│   ├── renderer/        # OpenGL 3D renderer
│   ├── window/          # Transparent window
│   └── animations/      # Animation system
├── ipc/                 # Native IPC communication
├── models/              # 3D character models
├── config/              # Configuration
└── tests/               # Tests
```

## Requirements

- Python 3.10+
- Windows 10/11
- CUDA-capable GPU (optional, for faster local LLM)
- 8GB+ RAM (16GB recommended for local LLM)

## Installation

### For Users (Executable)
1. Download the latest release (EV3_Setup_vX.X.X.exe)
2. Run the installer
3. Choose to install as Windows service (recommended)
4. Launch E.V3 from Start Menu

### For Developers (Python)
```bash
# Run setup
setup.bat

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Quick Start (Recommended)
```batch
# Start both Daemon and Shell
start_ev3.bat
```

The Shell will appear in your system tray. Right-click the icon for options.

### Separate Launch
```batch
# Start Daemon (background service)
start_daemon.bat

# Start Shell (UI with system tray)
start_shell.bat
```

### Python Direct
```bash
# Run daemon
python main_service.py

# Run shell (in separate terminal)
python main_ui.py
```

### System Tray Control
Once the Shell is running:
- **Find Icon**: Check Windows system tray (bottom-right, may be in hidden icons)
- **Show/Hide**: Double-click icon or use "Show/Hide Shell" menu
- **Stop Daemon**: Right-click → "Stop Daemon"
- **Exit**: Right-click → "Exit"

### Executable Version (when built)
```bash
# Run daemon
dist/EV3Daemon.exe

# Run shell
dist/EV3Shell.exe
```

## Building Executables

To create standalone .exe files:

```bash
# Quick build
build.bat

# Or manually
pip install pyinstaller
python build_exe.py
```

See [BUILD_GUIDE.md](BUILD_GUIDE.md) for detailed instructions.

## Privacy Controls

All privacy settings in `config/privacy.yaml`:
- Local LLM only by default
- External API only on "find out" trigger
- No telemetry, no analytics
- All data processed locally

## Model Setup

Place your VRoid or Blender exported model (with armature) in `models/` directory:
- Supported formats: .vrm, .glb, .gltf
- Should include bone structure for animations
- Optional: blendshapes for facial expressions

## License

**Polyform Noncommercial License 1.0.0**

E.V3 is free and open source for noncommercial use. You can:
- ✅ Use it personally for any noncommercial purpose
- ✅ Study and modify the code
- ✅ Share it with others
- ✅ Create derivatives for noncommercial purposes

You **cannot**:
- ❌ Use it for commercial purposes without permission
- ❌ Profit from modifications or derivatives

See [LICENSE.txt](LICENSE.txt) for full terms.

For commercial licensing inquiries, please contact the project maintainers.

