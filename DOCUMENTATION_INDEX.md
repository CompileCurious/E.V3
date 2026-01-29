# E.V3 Documentation Index

## 📚 Quick Navigation

### 🚀 Getting Started
1. **[QUICKSTART.md](QUICKSTART.md)** - 5-minute setup guide
   - Installation steps
   - Basic usage
   - First-time configuration

2. **[README.md](README.md)** - Project overview
   - Features
   - Architecture
   - Requirements

### 📖 User Documentation
3. **[USAGE_GUIDE.md](USAGE_GUIDE.md)** - Complete user guide
   - Detailed features
   - Customization options
   - Troubleshooting

4. **[models/MODEL_SETUP.md](models/MODEL_SETUP.md)** - Model setup
   - LLM download instructions
   - 3D character setup
   - Model resources

### 🔧 Technical Documentation
5. **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Technical overview
   - Architecture details
   - Component descriptions
   - Performance characteristics

6. **[DIAGRAMS.md](DIAGRAMS.md)** - System diagrams
   - Component architecture
   - Data flow
   - State machine
   - IPC protocol

7. **[DEVELOPMENT.md](DEVELOPMENT.md)** - Developer guide
   - Development setup
   - Code style
   - Testing
   - Contributing

### 📝 Reference
8. **[CHANGELOG.md](CHANGELOG.md)** - Version history
   - Feature additions
   - Bug fixes
   - Known issues

9. **[config/config.yaml](config/config.yaml)** - Configuration reference
   - All settings explained
   - Default values
   - Privacy controls

## 🎯 Common Tasks

### First Time Setup
```bash
# 1. Run setup
setup.bat

# 2. (Optional) Download AI model
# See models/MODEL_SETUP.md

# 3. (Optional) Add character model
# See models/MODEL_SETUP.md

# 4. Launch E.V3
python start.py
```
**Reference**: [QUICKSTART.md](QUICKSTART.md)

### Customizing Appearance
```yaml
# Edit config/config.yaml
ui:
  window:
    width: 400
    height: 600
    offset_x: 20
  model:
    scale: 1.0
    rotation: [0, 0, 0]
```
**Reference**: [USAGE_GUIDE.md](USAGE_GUIDE.md#customization)

### Privacy Configuration
```yaml
# Edit config/config.yaml
privacy:
  local_only: true              # No external calls
  allow_external_on_request: true  # "find out" trigger
  no_telemetry: true
```
**Reference**: [USAGE_GUIDE.md](USAGE_GUIDE.md#privacy-controls)

### Installing as Service
```bash
# Requires administrator
python install_service.py install
python install_service.py start
```
**Reference**: [USAGE_GUIDE.md](USAGE_GUIDE.md#advanced-usage)

### Debugging Issues
1. Check logs: `logs/ev3.log`, `logs/ev3_ui.log`
2. Run tests: `python tests/test_components.py`
3. Verify installation: `verify_install.bat`

**Reference**: [USAGE_GUIDE.md](USAGE_GUIDE.md#troubleshooting)

## 🔍 Find Information By Topic

### Privacy & Security
- Privacy architecture: [DIAGRAMS.md](DIAGRAMS.md#privacy-architecture)
- Privacy controls: [USAGE_GUIDE.md](USAGE_GUIDE.md#privacy-controls)
- Security considerations: [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md#security-considerations)
- Data anonymization: [DEVELOPMENT.md](DEVELOPMENT.md#security-considerations)

### AI / LLM
- LLM setup: [models/MODEL_SETUP.md](models/MODEL_SETUP.md)
- Local vs external: [USAGE_GUIDE.md](USAGE_GUIDE.md#features)
- AI configuration: [config/config.yaml](config/config.yaml)
- LLM architecture: [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md#ai-integration)

### 3D Character
- Model setup: [models/MODEL_SETUP.md](models/MODEL_SETUP.md)
- Animation system: [DIAGRAMS.md](DIAGRAMS.md#animation-system)
- Supported formats: [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md#file-formats)
- Customization: [USAGE_GUIDE.md](USAGE_GUIDE.md#customization)

### System Monitoring
- Event types: [USAGE_GUIDE.md](USAGE_GUIDE.md#features)
- Configuration: [config/config.yaml](config/config.yaml)
- Event flow: [DIAGRAMS.md](DIAGRAMS.md#data-flow-diagram)

### Calendar Integration
- Setup guide: [USAGE_GUIDE.md](USAGE_GUIDE.md#customization)
- Supported providers: [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md#calendar-integration)
- Configuration: [config/config.yaml](config/config.yaml)

### Windows Service
- Installation: [install_service.py](install_service.py)
- Management: [USAGE_GUIDE.md](USAGE_GUIDE.md#advanced-usage)
- Troubleshooting: [USAGE_GUIDE.md](USAGE_GUIDE.md#troubleshooting)

### Development
- Setup: [DEVELOPMENT.md](DEVELOPMENT.md)
- Architecture: [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)
- Code style: [DEVELOPMENT.md](DEVELOPMENT.md#code-style)
- Testing: [DEVELOPMENT.md](DEVELOPMENT.md#testing)

## 📂 File Reference

### Python Files
- `main_service.py` - Service entry point
- `main_ui.py` - UI entry point
- `start.py` - Quick start script
- `install_service.py` - Service installer
- `service/Modules/service.py` - Main service class
- `ui/window/companion_window.py` - Main window
- `ui/renderer/opengl_renderer.py` - 3D renderer
- `ui/animations/animation_controller.py` - Animations
- `ipc/native_pipe.py` - IPC implementation

### Configuration Files
- `config/config.yaml` - Main configuration
- `.env` - Environment variables
- `requirements.txt` - Python dependencies

### Batch Files
- `setup.bat` - First-time setup
- `run.bat` - One-click launcher
- `verify_install.bat` - Installation check

### Documentation
- `README.md` - Project overview
- `QUICKSTART.md` - Quick start guide
- `USAGE_GUIDE.md` - User manual
- `DEVELOPMENT.md` - Developer docs
- `PROJECT_SUMMARY.md` - Technical summary
- `DIAGRAMS.md` - Visual diagrams
- `CHANGELOG.md` - Version history
- `models/MODEL_SETUP.md` - Model setup

## 🆘 Getting Help

### For Users
1. Start with [QUICKSTART.md](QUICKSTART.md)
2. Check [USAGE_GUIDE.md](USAGE_GUIDE.md) troubleshooting
3. Review logs in `logs/` directory
4. Run `verify_install.bat`

### For Developers
1. Read [DEVELOPMENT.md](DEVELOPMENT.md)
2. Study [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)
3. Review [DIAGRAMS.md](DIAGRAMS.md)
4. Check code comments

### Common Issues
- **Installation problems**: [QUICKSTART.md](QUICKSTART.md)
- **Configuration errors**: [config/config.yaml](config/config.yaml)
- **Model loading**: [models/MODEL_SETUP.md](models/MODEL_SETUP.md)
- **Service issues**: [USAGE_GUIDE.md](USAGE_GUIDE.md#troubleshooting)

## 🎓 Learning Path

### Beginner
1. [QUICKSTART.md](QUICKSTART.md) - Get it running
2. [README.md](README.md) - Understand what it does
3. [USAGE_GUIDE.md](USAGE_GUIDE.md) - Learn features

### Intermediate
1. [models/MODEL_SETUP.md](models/MODEL_SETUP.md) - Add custom models
2. [config/config.yaml](config/config.yaml) - Customize settings
3. [USAGE_GUIDE.md](USAGE_GUIDE.md#advanced-usage) - Advanced features

### Advanced
1. [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Technical deep dive
2. [DIAGRAMS.md](DIAGRAMS.md) - System architecture
3. [DEVELOPMENT.md](DEVELOPMENT.md) - Modify and extend

## 📊 Documentation Statistics

- **Total Documents**: 10 major files
- **Word Count**: ~25,000+ words
- **Code Files**: 20+ Python modules
- **Configuration**: Fully documented
- **Examples**: Included throughout

## 🔄 Keep Updated

This documentation is maintained alongside the code. When updating E.V3:
1. Check [CHANGELOG.md](CHANGELOG.md) for changes
2. Review updated [config/config.yaml](config/config.yaml)
3. Read release notes

---

**Quick Links:**
- [GitHub Repository](#) (add your repo link)
- [Issue Tracker](#) (add your issue tracker)
- [Discussions](#) (add your discussions)

**Version:** 0.1.0  
**Last Updated:** 2026-01-27
