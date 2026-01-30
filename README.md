# E.V3 - Privacy-Focused Desktop Companion

> **⚠️ ALPHA STATUS**: E.V3 is currently in active development. Core features are functional, but many exciting features are still in progress. Expect frequent updates and improvements!

A privacy-first desktop companion with a 3D animated character, built on a **microkernel architecture** with isolated capability modules.

![E.V3 Screenshot](assets/ev3_screenshot.png)
<<<<<<< HEAD
*E.V3 with custom VRM character rendering and chat interface*
=======

*E.V3 with VRM character rendering and chat interface*
>>>>>>> dd0919794416a89076beabaf7fd33ad3bbe63115

## ✨ Features

- **Privacy First**: No data scraping, no raw logs sent, all processing local by default
- **Microkernel Architecture**: Modular design with permission boundaries and event-based communication
- **Native Windows Kernel**: Runs in background, monitors system events
- **Interactive Shell**: System tray control with Show/Hide, Stop Kernel, Exit menu
- **Fully Customizable Character**: Bring your own VRM/GLTF/GLB model - no default character included
- **Dual LLM Modes**: 
  - **Fast Mode**: Phi-3-mini (2.3GB) for quick responses
  - **Deep Thinking Mode**: Mistral 7B for complex reasoning
- **Local Text-to-Speech**: Hot-swappable voicepacks, neural TTS and sample-based audio
- **Optional External LLM**: GPT mini API only when explicitly requested
- **Event Monitoring**: Windows Defender, Firewall, System notifications
- **Calendar Integration**: Surface reminders from your calendar
- **Transparent UI**: Frameless window with proper transparency and click-through support
- **System Tray Control**: Full control via system tray icon
- **Native IPC**: Fast communication between kernel and shell via named pipes
- **Module Configuration UI**: File picker interface for easy model selection

## 🚧 Roadmap (Coming Soon)

- **Voice Commands**: Wake word detection and natural voice interaction
- **Advanced Animations**: Full bone rigging, lip sync, and emotional expressions
- **Plugin System**: Third-party module support with sandboxing
- **Multi-Monitor**: Character can move between screens
- **Smart Context**: Learn from your usage patterns (all local)
- **Enhanced TTS**: Real-time voice cloning and emotion modulation
- **Mobile Companion**: Sync with phone for notifications
- **Custom Gestures**: Teach your character custom animations
- **Screen Awareness**: Character reacts to what's on screen
- **And much more...**

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

## 📚 Quick Links

- **[FIRST_TIME_SETUP.md](FIRST_TIME_SETUP.md)** - 🚀 **START HERE!** Complete first-time setup guide
- **[USAGE_GUIDE.md](USAGE_GUIDE.md)** - How to use E.V3 daily
- **[models/MODEL_SETUP.md](models/MODEL_SETUP.md)** - Detailed LLM and character model setup
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical architecture and design
- **[docs/SPEECH_SYSTEM.md](docs/SPEECH_SYSTEM.md)** - TTS and voice system setup
- **[BUILD_GUIDE.md](BUILD_GUIDE.md)** - Building standalone executables
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Contributing and development workflow

## Requirements

- Python 3.13+ (Python 3.10+ supported)
- Windows 10/11
- **llama-cpp-python** for local LLM inference
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

# Install LLM support
pip install llama-cpp-python
```

### Model Setup

#### 1. LLM Models (Required for AI features)

E.V3 supports **dual LLM modes** for different use cases. **Models are NOT included** - you download them separately for privacy and flexibility.

**Fast Mode (Phi-3-mini)**:
```bash
# Download Phi-3 (2.3GB quantized model)
python tools/download_phi3.py
```
- Quick responses (150 tokens max)
- Lower temperature (0.7) for consistency
- Ideal for greetings, simple queries, system responses

**Deep Thinking Mode (Mistral 7B)**:
- Download from HuggingFace: https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF
- Longer responses (512 tokens max)
- Higher temperature (0.8) for creativity
- Best for complex reasoning, detailed explanations

Both models should be placed in `models/llm/` directory. Configure via:
- **UI Method**: System tray → Modules → Select LLM Models (file pickers)
- **Manual Method**: Edit `config/config.yaml` to set `fast_model` and `deep_model` paths

**Privacy Note**: LLM models are stored locally only and NOT tracked in git. Your models stay on your machine.

#### 2. 3D Character Model (Required - Fully Customizable!)

**E.V3 does NOT include a default character** - you bring your own! This ensures full creative freedom and privacy.

**Supported Formats**:
- **VRM** (.vrm) - VRoid Studio models (recommended)
- **GLTF/GLB** (.gltf, .glb) - Blender or other 3D tools
- **FBX/OBJ** - Additional format support

**Where to Get Models**:
- **VRoid Studio**: Create your own at https://vroid.com/en/studio
- **VRoid Hub**: Download pre-made at https://hub.vroid.com/
- **Ready Player Me**: https://readyplayer.me/
- **Sketchfab**: https://sketchfab.com/
- **Blender**: Create custom characters

**Setup**:
1. Place your character file in `models/character/`
2. Configure via:
   - **UI Method**: System tray → Modules → Select Character Model
   - **Manual Method**: Edit `config/config.yaml`

```yaml
ui:
  model:
    model_path: "models/character/YOUR_CUSTOM_MODEL.vrm"
    scale: 0.6              # Adjust size (0.5-1.0 recommended)
    position: [0, -1.2, 0]  # [x, y, z] - negative Y moves down
```

**Privacy Note**: Character models are stored locally only and NOT tracked in git. Your character is yours alone!

#### 3. Voice/Speech Model (Optional)

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
- **Stop Kernel**: Right-click → "Stop Kernel"
- **Exit**: Right-click → "Exit"
- **Modules**: Right-click → "Modules" to configure LLM modes and models

### Module Configuration UI
Access via system tray → Modules:
- **LLM Mode**: Switch between Fast (Phi-3) and Deep Thinking (Mistral)
- **Model Selection**: Use file pickers to select custom .gguf or .vrm/.glb models
- **Save Changes**: Type 'Y' in commit field and press Enter to save to config
- **Discard Changes**: Type 'N' or close window to discard

### Chat with E.V3
Interact with the AI companion:
- **Summon Chat**: Press **Win+C** (default) to show character and open chat window
- **Type Message**: Enter your message in the chat window
- **LLM Modes**: 
  - Fast mode responds quickly with concise answers
  - Deep mode provides detailed, thoughtful responses
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
  mode: "fast"  # "fast" for Phi-3, "deep" for Mistral
  local:
    enabled: true
    fast_model: "Phi-3-mini-4k-instruct-q4.gguf"
    deep_model: "mistral-7b-instruct-v0.2.Q4_K_M.gguf"
    fast_max_tokens: 150
    fast_temperature: 0.7
    deep_max_tokens: 512
    deep_temperature: 0.8
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
    model_path: "models/character/E.V3.vrm"
    scale: 0.6
    position: [0, -1.2, 0]  # [x, y, z] positioning
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
- **All AI processing happens on your machine by default**
- **No analytics, telemetry, or tracking**
- **Models are NOT included in repo** - you download and control them
- **Character models are yours alone** - stored locally, never shared
- Event data is anonymized (no usernames, paths, IPs)
- Configuration and state stored locally only

### Modular & Customizable
- **Bring your own character** - full creative freedom
- **Choose your LLM models** - optimize for your hardware
- **Hot-swappable components** - change models without restart
- **No vendor lock-in** - all open standards (VRM, GLTF, GGUF)

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
- **Install llama-cpp-python first**: `pip install llama-cpp-python`
- Check if model files exist in `models/llm/`
- Verify GPU drivers (if using GPU acceleration)
- Try CPU-only mode: set `use_gpu: false` in config
- Ensure kernel is running before starting shell

### UI not appearing
- Check if kernel is running first (`start_kernel.bat`)
- Look for shell in system tray (may be in hidden icons)
- Check UI logs for errors
- Verify model file exists at configured path

### VRM model not rendering
- **No default model included** - ensure you've added your own character to `models/character/`
- Ensure model path is correct in config
- Check logs for texture loading errors
- Verify model scale and position settings
- Try adjusting `scale` (0.5-1.0) and `position` Y value (-2.0 to 0)
- Test with different VRM/GLB models to isolate issues

### Missing models
- **Models are NOT included in the repository**
- Download LLM models separately (see Model Setup section)
- Add your own character model (see Character Model section)
- Models are stored locally only for privacy

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
- ✅ Use your own models and characters (they're yours!)

You **cannot**:
- ❌ Use it for commercial purposes without permission
- ❌ Profit from modifications or derivatives

See [LICENSE.txt](LICENSE.txt) for full terms.

For commercial licensing inquiries, please contact the project maintainers.

---

## 🎨 About Customization

E.V3 is designed to be **fully modular and customizable**:

- **Your Character, Your Way**: No default character model means total creative freedom
- **Your Models, Your Privacy**: All LLM models stay on your machine, never shared
- **Open Standards**: VRM, GLTF, GGUF - industry standard formats
- **Hot-Swappable**: Change characters and models on the fly via UI
- **Community Driven**: Share tips and tricks (not your actual models!)

**This is Alpha software** - we're actively developing new features and welcome feedback! Check the Roadmap section for what's coming next.

