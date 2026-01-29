# E.V3 - Privacy-Focused Desktop Companion

A privacy-first desktop companion with a 3D animated character, built on a **microkernel architecture** with isolated capability modules.

## Features

- **Privacy First**: No data scraping, no raw logs sent, all processing local by default
- **Microkernel Architecture**: Modular design with permission boundaries and event-based communication
-- **Native Windows Kernel**: Runs in background, monitors system events
-- **Interactive Shell**: System tray control with Show/Hide, Stop Kernel, Exit menu
- **3D Animated Character**: VRoid/Blender models with bone animations and blendshapes- **Local Text-to-Speech**: Hot-swappable voicepacks, neural TTS and sample-based audio- **Local LLM**: Mistral 7B quantized for personality and event interpretation
- **Optional External LLM**: GPT mini API only when explicitly requested
- **Event Monitoring**: Windows Defender, Firewall, System notifications
- **Calendar Integration**: Surface reminders from your calendar
- **Transparent UI**: Frameless window with proper transparency support
- **System Tray Control**: Full control via system tray icon
-- **Native IPC**: Fast communication between kernel and shell via named pipes

## Architecture

**Microkernel Design** - Minimal core + isolated capability modules:

```
┌─────────────────────────────────────────────────────────────┐
│                     E.V3 MICROKERNEL                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Minimal Event Loop Core                             │   │
│  │  - Event bus for module communication                │   │
│  │  - Permission checker (scoped storage)               │   │
│  │  - Module registry (lifecycle management)            │   │
│  │  - Kernel API (emit/subscribe events, config access) │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Kernel API (Permission-Checked Boundary)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  CAPABILITY MODULES                         │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   State     │  │   Events    │  │    LLM      │        │
│  │   Module    │  │   Module    │  │   Module    │        │
│  │ (idle/      │  │ (Defender/  │  │ (Mistral/   │        │
│  │  alert/     │  │  Firewall)  │  │  GPT mini)  │        │
│  │  reminder)  │  │             │  │             │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐                          │
│  │  Calendar   │  │    IPC      │                          │
│  │   Module    │  │   Module    │                          │
│  │ (Reminders) │  │ (Named Pipe)│                          │
│  └─────────────┘  └─────────────┘                          │
│                                                             │
│  All modules: Explicit permissions, lifecycle, events      │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Native IPC (Named Pipes)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│   E.V3 Shell (3D UI with System Tray)                       │
│  - Transparent window with 3D character                     │
│  - System tray control (Show/Hide/Stop/Exit)                │
│  - Animation system (breathing, blinking, expressions)      │
└─────────────────────────────────────────────────────────────┘
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed module documentation.

## Project Structure

```
E.V3/
├── kernel/              # Microkernel core
│   ├── kernel.py       # Event bus, permissions, registry
│   └── module.py       # Module interface, KernelAPI
│
├── modules/             # Capability modules
│   ├── state_module.py    # State machine
│   ├── event_module.py    # System event monitoring
│   ├── llm_module.py      # LLM processing
│   ├── calendar_module.py # Calendar integration
│   └── ipc_module.py      # Inter-process communication
│
├── service/             # Legacy implementations (used by modules)
│   ├── state/          # State machine implementation
│   ├── events/         # Event listeners
│   ├── llm/            # LLM providers
│   └── calendar/       # Calendar providers
│
├── ui/                  # 3D UI shell (separate process)
│   ├── renderer/       # OpenGL 3D renderer
│   ├── window/         # Transparent window
│   └── animations/     # Animation system
│
├── ipc/                 # IPC implementation (named pipes)
├── models/              # LLM and 3D character models
├── config/              # Configuration
├── main_service.py      # Kernel entrypoint
└── main_ui.py           # Shell entrypoint
```

## Requirements

- Python 3.10+
- Windows 10/11
- CUDA-capable GPU (optional, for faster local LLM)
- 8GB+ RAM (16GB recommended for local LLM)

## Installation

### Quick Setup
```bash
# Clone repository
git clone https://github.com/yourusername/E.V3.git
cd E.V3

# Run setup
setup.bat

# Install dependencies
pip install -r requirements.txt
```

### Model Setup

1. **LLM Model** (Required for AI features):
   - Download Mistral 7B quantized model from HuggingFace
   - See [models/MODEL_SETUP.md](models/MODEL_SETUP.md) for instructions
   - Place in `models/llm/` directory

2. **3D Character Model** (Optional):
   - Use built-in test character, OR
   - Add your own VRoid (.vrm) or Blender (.glb/.gltf) model
   - Place in `models/character/` directory
   - Update `config/config.yaml` with model path

3. **Voice/Speech Model** (Optional):
   - Download Piper TTS voice from: https://github.com/rhasspy/piper/releases
   - Place model files in `models/speech/piper_english/`
   - See [models/MODEL_SETUP.md](models/MODEL_SETUP.md) for details

## Usage

### Quick Start (Recommended)
```batch
# Start both kernel and shell together
start_ev3.bat
```

The shell will appear in your system tray. Right-click the tray icon for options.

### Separate Launch
```batch
# Start kernel (background service)
start_kernel.bat

# Start shell (UI with system tray) - in separate terminal
start_shell.bat
```

### Python Direct
```bash
# Run kernel
python main_service.py

# Run shell (in separate terminal)
python main_ui.py
```

### System Tray Control
Once the shell is running:
- **Find Icon**: Check Windows system tray (bottom-right, may be in hidden icons)
- **Show/Hide**: Double-click icon or use "Show/Hide Shell" menu
-- **Stop Kernel**: Right-click → "Stop Kernel"
- **Exit**: Right-click → "Exit"

### Chat with E.V3
Interact with the AI companion:
- **Summon Chat**: Press **Win+C** (default) to show character and open chat window
- **Type Message**: Enter your message in the chat window
- **External LLM**: Include "find out" in your message to use GPT mini instead of local LLM
- **Close Chat**: Click the X button to close chat window independently
- **Configure Hotkey**: Right-click tray icon → Shell → Summon Hotkey → Enable/Disable

The chat window:
- Floats next to the 3D character
- Shows conversation history (last 10 messages)
- Can be closed without hiding the character
- Press Enter or click Send to submit messages

## Configuration

Edit `config/config.yaml` to customize:

### Privacy Settings
```yaml
privacy:
  local_only: true              # Use only local LLM
  allow_external_on_request: true  # Allow GPT mini on "find out" trigger
  no_telemetry: true            # No analytics/telemetry
  anonymize_events: true        # Strip personal data from events
```

### Module Toggles
```yaml
events:
  windows_defender:
    enabled: true
  firewall:
    enabled: true

calendar:
  enabled: true
  provider: "outlook"  # or "google"

llm:
  local:
    enabled: true
  external:
    enabled: false  # Only on "find out" trigger
```

### UI Settings
```yaml
ui:
  window:
    position: "bottom_right"
    width: 400
    height: 600
    opacity: 0.95
  model:
    model_path: "models/character/your-model.vrm"
    scale: 1.0
  hotkey:
    enabled: true
    combination: "win+c"  # Windows key + C to summon
```

See config file for full options.

## Microkernel Architecture

E.V3 uses a **microkernel architecture** for:
- **Modularity**: Add/remove capabilities without core changes
- **Security**: Permission boundaries between modules
- **Reliability**: Module failures don't crash kernel
- **Testability**: Test modules in isolation

### Module Lifecycle

Each module follows the lifecycle:
1. **Load** - Initialize with configuration
2. **Enable** - Start active operations
3. **Disable** - Pause operations
4. **Shutdown** - Release resources

### Permission Model

Modules must declare permissions:
- `IPC_SEND` / `IPC_RECEIVE`
- `EVENT_EMIT` / `EVENT_SUBSCRIBE`
- `STORAGE_READ` / `STORAGE_WRITE`
- `SYSTEM_EVENTS` / `SECURITY_EVENTS`
- `CALENDAR_READ`
- `LLM_LOCAL` / `LLM_EXTERNAL`

### Event Bus

Modules communicate via central event bus:
- State changes: `state.changed`
- System events: `system.defender`, `system.firewall`
- IPC messages: `ipc.user_message`, `ipc.send_message`
- State transitions: `state.transition.alert`, `state.transition.reminder`

See [ARCHITECTURE.md](ARCHITECTURE.md) for details.

## Building Executables

To create standalone .exe files:

```bash
# Quick build
build.bat

# Or manually
pip install pyinstaller
python build_exe.py
```

Executables will be in `dist/`:
- `EV3Kernel.exe` - Background kernel
- `EV3Shell.exe` - UI shell

See [BUILD_GUIDE.md](BUILD_GUIDE.md) for detailed instructions.

## Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Microkernel design, modules, event flows
- **[models/MODEL_SETUP.md](models/MODEL_SETUP.md)** - LLM, 3D models, and speech setup
- **[docs/SPEECH_SYSTEM.md](docs/SPEECH_SYSTEM.md)** - Complete speech/TTS documentation
- **[SPEECH_IMPLEMENTATION.md](SPEECH_IMPLEMENTATION.md)** - Speech system implementation summary
- **[BUILD_GUIDE.md](BUILD_GUIDE.md)** - Building executables
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Development workflow
- **[USAGE_GUIDE.md](USAGE_GUIDE.md)** - User guide

## Privacy & Security

### Local-First Design
- All AI processing happens on your machine by default
- No analytics, telemetry, or tracking
- Event data is anonymized (no usernames, paths, IPs)
- Configuration and state stored locally only

### Permission Model
- Each module declares required permissions
- Kernel enforces permission boundaries at runtime
- Scoped storage - modules can't access each other's data
- Event-based communication prevents direct coupling

### External API Usage
- External LLM (GPT mini) only enabled when explicitly requested
- Trigger phrase: "find out"
- All external calls logged
- Can be completely disabled in config

## Development

### Adding a New Module

1. Create module class inheriting from `Module`:
```python
from kernel.module import Module, Permission, KernelAPI

class MyModule(Module):
    def __init__(self, kernel_api: KernelAPI):
        super().__init__("my_module", kernel_api)
    
    def get_required_permissions(self) -> Set[Permission]:
        return {Permission.EVENT_EMIT}
    
    def get_dependencies(self) -> Set[str]:
        return {"state"}  # depends on state module
    
    def load(self, config: Dict[str, Any]) -> bool:
        # Initialize resources
        return True
    
    def enable(self) -> bool:
        # Start operations
        return True
    
    def disable(self) -> bool:
        # Pause operations
        return True
    
    def shutdown(self) -> bool:
        # Cleanup
        return True
    
    def handle_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        # Process events
        pass
```

2. Register in [main_service.py](main_service.py):
```python
my_module = MyModule(kernel_api)
kernel.register_module(my_module)
```

3. Add configuration to `config/config.yaml`

### Testing

```bash
# Run tests
python -m pytest tests/

# Test specific component
python tests/test_components.py
```

## Troubleshooting

### Kernel won't start
- Check logs in `logs/ev3.log`
- Ensure no other instance is running
- Verify config file syntax

### LLM not responding
- Check if model file exists in `models/llm/`
- Verify GPU drivers (if using GPU acceleration)
- Try CPU-only mode: set `use_gpu: false` in config

### UI not appearing
-- Check if kernel is running first
- Look for shell in system tray (may be in hidden icons)
- Check UI logs for errors

### Module failures
- Check `logs/ev3.log` for module-specific errors
- Verify module dependencies are enabled
- Check module permissions in config

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

