# E.V3 Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2026-01-27

### Added
- Initial release of E.V3 Privacy-Focused Desktop Companion
- Background service with Windows event monitoring
- Transparent 3D UI with OpenGL rendering
- State machine implementation (idle, scanning, alert, reminder)
- Local LLM integration (Mistral 7B support)
- External LLM integration (GPT mini, opt-in only)
- Native Windows IPC using named pipes
- Calendar integration (Outlook and Google Calendar)
- 3D model loading (VRM, GLB, GLTF formats)
- Animation system (breathing, blinking, state-based poses)
- Blendshape/morph target support
- Privacy controls and anonymization
- Windows service installer
- Comprehensive documentation
- Setup and verification scripts

### Features

#### Privacy
- All processing local by default
- Event anonymization
- No telemetry or data collection
- External API only on explicit user trigger
- Local-only mode enforcement option

#### System Monitoring
- Windows Defender event monitoring
- Firewall change detection
- System notification integration
- Configurable event filters

#### AI Integration
- Local Mistral 7B for personality and interpretation
- GPU acceleration support (CUDA)
- Quantized model support (Q2_K to Q8_0)
- External GPT mini with "find out" trigger
- Context-aware responses
- Event interpretation

#### 3D Character
- VRoid Studio model support (.vrm)
- Blender model support (.glb, .gltf)
- Skeletal animation system
- Blendshape facial expressions
- Real-time bone manipulation
- Idle breathing animation
- Automatic eye blinking
- State-based poses
- Glow effects

#### UI
- Transparent frameless window
- Always-on-top positioning
- Bottom-right anchoring (above taskbar)
- Click-through when idle
- Interactive when alert/reminder
- Draggable window
- Message overlay system
- State-based visual effects

#### Calendar
- Microsoft 365/Outlook integration
- Google Calendar integration
- OAuth2 authentication
- Configurable reminder timing
- Non-intrusive notifications

#### Technical
- Native Windows named pipe IPC
- Bidirectional service-UI communication
- JSON message protocol
- Robust error handling
- Comprehensive logging
- Configuration via YAML
- Environment variable support

### Installation
- Automated setup script (setup.bat)
- Dependency installation
- Directory structure creation
- Configuration file generation
- Virtual environment setup

### Documentation
- README.md - Project overview and architecture
- QUICKSTART.md - 5-minute setup guide
- USAGE_GUIDE.md - Comprehensive user guide
- MODEL_SETUP.md - 3D model and LLM setup
- PROJECT_SUMMARY.md - Technical summary
- DEVELOPMENT.md - Developer documentation
- CHANGELOG.md - Version history

### Scripts
- setup.bat - First-time setup
- run.bat - One-click launcher
- start.py - Cross-platform starter
- verify_install.bat - Installation verification
- install_service.py - Windows service installer
- test_components.py - Component tests

### Configuration
- config/config.yaml - Main configuration
- .env.example - Environment template
- Comprehensive default settings
- Privacy-first defaults
- Extensible configuration system

### Known Limitations
- Windows-only (native APIs used)
- Basic GLTF/VRM support (complex features limited)
- Large LLM models require significant RAM
- Manual calendar OAuth setup required
- Small delay in real-time event processing

### Future Enhancements
- Voice input/output
- Custom gesture library
- Plugin system
- Multiple character support
- Network monitoring (privacy-safe)
- Task automation
- Cross-platform support (Linux, macOS)
- Advanced 3D rendering features
- Shader-based effects
- More animation presets

---

## Version Numbering

E.V3 follows [Semantic Versioning](https://semver.org/):
- MAJOR version: Incompatible API changes
- MINOR version: New functionality (backward compatible)
- PATCH version: Bug fixes (backward compatible)

## Release Notes Format

### Added
New features and capabilities

### Changed
Changes to existing functionality

### Deprecated
Soon-to-be-removed features

### Removed
Removed features

### Fixed
Bug fixes

### Security
Security improvements and fixes
