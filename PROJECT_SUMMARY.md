# E.V3 Project Summary

## Overview
E.V3 is a privacy-focused desktop companion application for Windows that combines system monitoring, AI assistance, and a 3D animated character interface.

## Architecture

### Two-Part System

**1. Background Service** (`main_service.py`)
- Runs as native Windows service or standalone process
- Monitors Windows Defender, Firewall, and system events
- Integrates with calendar (Outlook/Google)
- Runs local LLM (Mistral 7B) for AI processing
- Optionally calls external LLM (GPT mini) on user request
- Implements state machine (idle/scanning/alert/reminder)
- Communicates with UI via native Windows named pipes

**2. UI Layer** (`main_ui.py`)
- PySide6-based transparent window
- OpenGL 3D renderer for character model
- Supports VRM (VRoid), GLB, GLTF formats
- Bone animations and blendshapes
- Always-on-top, frameless, click-through
- Anchored bottom-right above taskbar
- Real-time animations (breathing, blinking, poses)

## Key Features

### Privacy-First Design
- All data processing local by default
- No telemetry, no analytics, no data collection
- Events anonymized before processing
- External AI only on explicit "find out" trigger
- Credentials stored locally only
- Read-only calendar access

### System Monitoring
- **Windows Defender**: Malware detection, protection status
- **Firewall**: Rule changes, security updates
- **System Events**: Important notifications

### AI Integration
- **Local**: Mistral 7B quantized (Q4_K_M recommended)
  - Event interpretation
  - Natural conversation
  - Context-aware responses
  - ~4GB RAM usage
- **External**: GPT-4 mini (optional)
  - Only on "find out" trigger
  - Anonymized context
  - Single-shot queries

### 3D Animation System
- Idle breathing animation
- Automatic eye blinking (random intervals)
- State-based poses (alert, reminder, scanning)
- Blendshape support for expressions
- Glow effects for different states
- Bone animation system

### Calendar Integration
- Microsoft 365/Outlook support
- Google Calendar support
- Configurable reminder advance time
- Non-intrusive notifications

## Technical Stack

### Core Technologies
- **Python 3.10+**
- **PySide6**: Qt6 for GUI
- **PyOpenGL**: 3D rendering
- **llama-cpp-python**: Local LLM inference
- **pywin32**: Windows API integration
- **WMI**: Windows Management Instrumentation

### Communication
- **IPC**: Native Windows named pipes
- **Format**: JSON messages
- **Bidirectional**: Service ↔ UI

### File Formats
- **Config**: YAML
- **Models**: VRM, GLB, GLTF
- **LLM**: GGUF (quantized)

## Project Structure

```
E.V3/
├── service/              # Background service
│   ├── core/            # Main service logic
│   │   └── service.py   # EV3Service class
│   ├── state/           # State machine
│   │   └── state_machine.py
│   ├── events/          # Event listeners
│   │   └── event_listeners.py
│   ├── llm/             # LLM integration
│   │   └── llm_manager.py
│   └── calendar/        # Calendar integration
│       └── calendar_manager.py
├── ui/                  # UI layer
│   ├── window/          # Main window
│   │   └── companion_window.py
│   ├── renderer/        # 3D rendering
│   │   ├── opengl_renderer.py
│   │   └── model_loader.py
│   └── animations/      # Animation system
│       └── animation_controller.py
├── ipc/                 # IPC communication
│   └── native_pipe.py   # Named pipe implementation
├── models/              # 3D models and LLM
│   ├── character/       # VRM/GLB character models
│   └── llm/             # Quantized LLM files
├── config/              # Configuration
│   ├── config.yaml      # Main configuration
│   └── credentials/     # API credentials
├── tests/               # Tests
│   └── test_components.py
├── main_service.py      # Service entry point
├── main_ui.py           # UI entry point
├── install_service.py   # Windows service installer
├── start.py             # Quick start script
└── setup.bat            # Setup script
```

## State Machine

```
┌──────┐     start_scan      ┌──────────┐
│ IDLE │ ──────────────────> │ SCANNING │
│      │ <────────────────── │          │
└──────┘     finish_scan     └──────────┘
   │ ▲                            │
   │ │                            │
   │ │ dismiss_alert    trigger_alert
   │ │                            │
   ▼ │                            ▼
┌───────┐                    ┌───────┐
│ ALERT │                    │ ALERT │
└───────┘                    └───────┘
   │ ▲
   │ │
   │ │ dismiss_reminder
   │ │
   ▼ │
┌──────────┐
│ REMINDER │
└──────────┘
```

## Privacy Controls

### Configuration Levels

1. **Paranoid** (Maximum Privacy):
   ```yaml
   privacy:
     local_only: true
     allow_external_on_request: false
     no_telemetry: true
   ```

2. **Balanced** (Recommended):
   ```yaml
   privacy:
     local_only: true
     allow_external_on_request: true  # On "find out"
     no_telemetry: true
   ```

3. **Custom**: Configure per feature

### Data Flow

```
System Event
    │
    ▼
Anonymize ──> Local Processing ──> State Change
    │              │                     │
    │              ▼                     ▼
    │         Local LLM            UI Update
    │              │
    └──> "find out" trigger?
              │
              ▼ (if yes)
         External LLM
         (anonymized)
```

## Performance Characteristics

### Resource Usage (Typical)

- **CPU**: 2-5% idle, 10-30% during AI inference
- **RAM**: 
  - Base: ~200MB
  - With Q4_K_M model: ~4.5GB
  - With Q2_K model: ~2.7GB
- **GPU**: Optional, speeds up AI inference significantly
- **Disk**: ~5-10GB (including AI model)

### Optimization Tips

1. Use GPU acceleration (CUDA)
2. Choose appropriate model quantization
3. Adjust animation FPS
4. Disable unused event monitoring
5. Use simpler 3D character model

## Security Considerations

### Implemented
- ✅ Local data processing
- ✅ Event anonymization
- ✅ No telemetry
- ✅ Credential encryption (system keyring)
- ✅ Read-only calendar access
- ✅ Sandboxed LLM execution

### User Responsibilities
- Secure API keys
- Review event filters
- Monitor log files
- Keep dependencies updated
- Run with minimal privileges

## Extensibility

### Add New Event Listener
```python
class CustomEventListener(WindowsEventListener):
    def __init__(self):
        super().__init__("CustomLog", [event_ids])
```

### Add New Animation
```python
def _apply_custom_pose(self):
    # Modify bones, blendshapes
    pass
```

### Add New State
```python
# In state_machine.py
states = [..., "custom_state"]
# Add transitions
```

## Future Enhancements

### Potential Features
- Voice input/output
- Custom gesture library
- Plugin system
- Multiple character support
- Network monitoring (privacy-safe)
- Task automation
- Cross-platform support (Linux, macOS)

### Community Contributions
The project is designed to be extensible:
- Modular architecture
- Clear separation of concerns
- Well-documented code
- Comprehensive configuration

## Known Limitations

1. **Windows Only**: Native Windows APIs used
2. **GLTF/VRM Support**: Basic implementation, complex features limited
3. **AI Model Size**: Large models require significant RAM
4. **Calendar OAuth**: Requires manual setup
5. **Real-time Events**: Small delay in event processing

## Installation Requirements

### Minimum
- Windows 10/11
- Python 3.10+
- 4GB RAM
- 5GB disk space

### Recommended
- Windows 11
- Python 3.11+
- 16GB RAM
- CUDA-capable GPU
- 10GB disk space

## License
Private project - see license file for details.

## Credits
- **LLM**: Mistral AI (Mistral 7B)
- **3D Support**: VRoid Studio, Blender community
- **UI Framework**: Qt Project (PySide6)
- **OpenGL**: Khronos Group

## Version History

### v0.1.0 (Initial Release)
- Core service implementation
- 3D UI with OpenGL
- State machine
- Event monitoring
- LLM integration
- Calendar support
- IPC communication
- Privacy controls
