# E.V3 User Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [Running E.V3](#running-ev3)
3. [Features](#features)
4. [Privacy Controls](#privacy-controls)
5. [Customization](#customization)
6. [Troubleshooting](#troubleshooting)

## Getting Started

### Prerequisites
- Windows 10/11
- Python 3.10 or higher
- 8GB RAM (16GB recommended for local LLM)
- GPU with CUDA support (optional, for faster AI processing)

### Installation

1. **Run the setup script:**
   ```bash
   setup.bat
   ```

2. **Configure environment variables:**
   - Edit `.env` file
   - Add API keys (optional, only if using external services)

3. **Download AI model (optional but recommended):**
   - See `models/MODEL_SETUP.md` for instructions
   - Download Mistral 7B for local AI processing

4. **Add 3D character model (optional):**
   - Place VRM or GLB file in `models/character/`
   - Update path in `config/config.yaml`

## Running E.V3

### Quick Start (Recommended)
```bash
python start.py
```
This starts both the service and UI together.

### Manual Start

**Option 1: As separate processes**
```bash
# Terminal 1 - Start service
python main_service.py

# Terminal 2 - Start UI
python main_ui.py
```

**Option 2: As Windows Service (requires admin)**
```bash
# Install
python install_service.py install

# Start
python install_service.py start

# Then start UI
python main_ui.py
```

## Features

### 1. Privacy-First Design
- **Local AI Processing**: All AI runs on your machine by default
- **No Data Collection**: No telemetry, no analytics, no data sent externally
- **Anonymized Events**: System events are stripped of personal information
- **Optional External AI**: Only activated when you say "find out"

### 2. System Monitoring
E.V3 monitors system events to keep you informed:

**Windows Defender Events:**
- Malware detection
- Protection status changes
- Scan results

**Firewall Events:**
- Rule changes
- Security policy updates

**System Notifications:**
- Important system updates
- Security alerts

### 3. Calendar Integration
- Connects to Outlook or Google Calendar
- Shows reminders before events
- Non-intrusive notifications

### 4. Intelligent Assistant
- **Local AI**: Mistral 7B for event interpretation and chat
- **External AI**: GPT-4 mini (only when you say "find out")
- Natural language interaction
- Context-aware responses

### 5. 3D Animated Companion
- Transparent, always-on-top window
- Anchored to bottom-right corner
- Click-through when idle
- Real-time animations:
  - Idle breathing
  - Eye blinking
  - Alert poses
  - Expression changes
  - Glow effects

## Privacy Controls

### Configuration (`config/config.yaml`)

```yaml
privacy:
  # Only use local AI
  local_only: true
  
  # Allow external AI only on "find out" trigger
  allow_external_on_request: true
  
  # No telemetry
  no_telemetry: true
  
  # Anonymize all events
  anonymize_events: true
  
  # Keep all data local
  local_storage_only: true
```

### Force Local-Only Mode
Set in `.env`:
```
FORCE_LOCAL_ONLY=true
```

### What Data is Collected?
**None.** E.V3 never sends data externally unless:
1. You explicitly say "find out" to trigger external AI
2. Even then, only anonymized context is sent

### What's Stored Locally?
- Configuration files
- Log files (can be disabled)
- AI model files
- 3D character models

## Customization

### Appearance

**Window Position & Size** (`config/config.yaml`):
```yaml
ui:
  window:
    position: "bottom_right"
    offset_x: 20  # pixels from edge
    offset_y: 20
    width: 400
    height: 600
    opacity: 0.95
```

**3D Model**:
```yaml
ui:
  model:
    model_path: "models/character/your-character.vrm"
    scale: 1.0
    rotation: [0, 0, 0]
```

**Animations**:
```yaml
ui:
  animations:
    idle_breathing:
      enabled: true
      speed: 0.5
      intensity: 0.3
    eye_blinking:
      enabled: true
      interval_min: 2.0
      interval_max: 6.0
    glow:
      enabled: true
      color: [0.3, 0.6, 1.0]  # RGB
      intensity: 0.5
```

### Behavior

**Event Monitoring**:
```yaml
events:
  windows_defender:
    enabled: true
  firewall:
    enabled: true
  system_notifications:
    enabled: true
```

**AI Settings**:
```yaml
llm:
  local:
    enabled: true
    temperature: 0.7
    max_tokens: 256
  external:
    enabled: false
    trigger_phrase: "find out"
```

**Calendar**:
```yaml
calendar:
  enabled: true
  provider: "outlook"  # or "google"
  check_interval: 300  # seconds
  reminder_advance: 900  # 15 minutes
```

## Interacting with E.V3

### States

**Idle**: Normal state, breathing animation, click-through enabled

**Scanning**: Actively monitoring system events

**Alert**: Important event detected, interactive, glow effect

**Reminder**: Calendar reminder, interactive, gentle glow

### User Interactions

**Double-click**: Dismiss alert/reminder

**Drag**: Move window (when interactive)

**Type message**: Chat with AI (when chat interface is active)

**Say "find out"**: Enable external AI for current query

## Troubleshooting

### Service won't start
- Check logs in `logs/ev3.log`
- Ensure no other instance is running
- Run as administrator if installing as service

### UI window not showing
- Check if service is running
- Look for errors in `logs/ev3_ui.log`
- Verify display settings (multi-monitor setup)

### Model not loading
- Check file path in config
- Ensure model file exists
- See `models/MODEL_SETUP.md`

### AI not responding
- Check if local model is downloaded
- Verify model path in config
- Check available RAM (need 4-8GB free)

### Calendar not working
- Verify credentials in `.env`
- Check internet connection
- Re-authenticate if needed

### High CPU/Memory usage
- Try smaller AI model (Q2_K instead of Q4_K_M)
- Reduce animation FPS in config
- Disable unused features

## Advanced Usage

### Windows Service Management

```bash
# Install service
python install_service.py install

# Start service
python install_service.py start

# Stop service
python install_service.py stop

# Restart service
python install_service.py restart

# Uninstall service
python install_service.py uninstall
```

### Command Line Options

Service:
```bash
python main_service.py --config path/to/config.yaml
```

UI:
```bash
python main_ui.py --config path/to/config.yaml
```

### Logging Levels

Edit `config/config.yaml`:
```yaml
logging:
  level: "DEBUG"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  log_to_file: true
  sanitize_logs: true  # Remove sensitive data
```

## Performance Tips

1. **Use GPU acceleration**: Enable CUDA for faster AI
2. **Choose right model**: Q4_K_M is good balance
3. **Adjust animation FPS**: Lower FPS = less CPU
4. **Disable unused features**: Turn off unneeded monitoring
5. **Use simpler 3D model**: Lower poly count = better performance

## Security Best Practices

1. **Keep local-only mode**: Unless you specifically need external AI
2. **Use strong API keys**: If using external services
3. **Review logs**: Check what events are being captured
4. **Update regularly**: Keep dependencies up to date
5. **Limit permissions**: Run with minimal required privileges

## Getting Help

Check logs:
- Service: `logs/ev3.log`
- UI: `logs/ev3_ui.log`

Common issues are usually:
- Missing dependencies
- Incorrect configuration
- File permission issues
- Missing model files

## Updates and Maintenance

Keep your installation updated:

```bash
# Update dependencies
pip install -r requirements.txt --upgrade

# Check for model updates
# Visit HuggingFace for newer quantizations

# Backup configuration
copy config\config.yaml config\config.yaml.backup
```
