# E.V3 - Quick Start Guide

Welcome to E.V3, your privacy-focused desktop companion!

## 🚀 Quick Setup (5 minutes)

### Step 1: Install Dependencies
```bash
setup.bat
```

### Step 2: Run E.V3
```bash
python start.py
```

That's it! E.V3 will appear in the bottom-right corner of your screen.

## 📦 What You Get Out of the Box

- ✅ **Basic functionality** - System monitoring, notifications
- ✅ **3D animated character** - Simple geometric character (placeholder)
- ✅ **Privacy protection** - All processing local by default
- ⚠️ **Limited AI** - No LLM until you download the model (optional)

## 🎨 Optional Enhancements

### Add AI Personality (Recommended)

1. **Download Mistral 7B** (~4.4 GB):
   - Visit: https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF
   - Download: `mistral-7b-instruct-v0.2.Q4_K_M.gguf`
   - Place in: `models/llm/`

2. **Benefits**:
   - Natural conversation
   - Event interpretation
   - Context-aware responses

### Add Custom 3D Character (Optional)

1. **Get a character**:
   - Create in VRoid Studio (free)
   - Download from VRoid Hub
   - Use Blender model

2. **Setup**:
   - Place .vrm or .glb file in `models/character/`
   - Edit `config/config.yaml`:
     ```yaml
     ui:
       model:
         model_path: "models/character/your-file.vrm"
     ```

3. **See**: `models/MODEL_SETUP.md` for details

### Add Calendar Integration (Optional)

**For Outlook/Microsoft 365**:
1. Get credentials from Azure Portal
2. Edit `.env`:
   ```
   OUTLOOK_CLIENT_ID=your_id
   OUTLOOK_CLIENT_SECRET=your_secret
   ```

**For Google Calendar**:
1. Get credentials from Google Cloud Console
2. Edit `.env`:
   ```
   GOOGLE_CALENDAR_CREDENTIALS=path/to/credentials.json
   ```

## 🎯 Using E.V3

### Basic Interaction

- **Idle State**: Character breathes, blinks, click-through enabled
- **Alert State**: Important event detected, window becomes interactive
- **Reminder State**: Calendar event coming up
- **Double-click**: Dismiss alert/reminder

### Privacy Features

- ✅ All data stays on your computer
- ✅ No telemetry, no analytics
- ✅ Events are anonymized
- ✅ External AI only when you say "find out"

### Customization

Edit `config/config.yaml` to customize:
- Window position and size
- Animation settings
- Monitoring preferences
- AI behavior
- Privacy controls

## 🔧 Troubleshooting

### Character not showing?
```bash
# Check logs
type logs\ev3_ui.log

# Try simple test
python tests\test_components.py
```

### Service not starting?
```bash
# Check logs
type logs\ev3.log

# Run with debug output
python main_service.py
```

### High CPU usage?
- Download smaller AI model (Q2_K instead of Q4_K_M)
- Lower FPS in config: `rendering: { fps: 30 }`
- Disable unused features in config

## 📚 Documentation

- **Full Guide**: See `../USAGE_GUIDE.md`
- **Model Setup**: See `../../models/MODEL_SETUP.md`
- **Architecture**: See `../../README.md`

## 🛡️ Privacy Commitment

E.V3 is designed with privacy as the #1 priority:

1. **Local First**: All processing happens on your machine
2. **No Telemetry**: Zero data collection or analytics
3. **Transparent**: Open source, you can verify everything
4. **User Control**: You decide what data leaves your machine
5. **Opt-in External**: External AI only when explicitly requested

## 🎮 Try These Features

1. **System Monitoring**: E.V3 will notify you of security events
2. **Chat** (with AI model): Ask about system events
3. **Calendar**: Get reminders 15 minutes before events
4. **Animations**: Watch character react to different states
5. **Customization**: Change appearance and behavior

## 🚀 Advanced Usage

### Install as Windows Service
```bash
# Requires administrator
python install_service.py install
python install_service.py start

# Then just run UI
python main_ui.py
```

### Multiple Configurations
```bash
python main_service.py --config myconfig.yaml
python main_ui.py --config myconfig.yaml
```

## 💡 Tips

1. **Performance**: Use GPU acceleration if available (CUDA)
2. **Privacy**: Keep `local_only: true` in config
3. **Appearance**: Adjust `opacity` for better visibility
4. **Monitoring**: Enable only events you care about
5. **Updates**: Check for new AI models periodically

## 🆘 Getting Help

1. **Check logs** in `logs/` directory
2. **Run tests**: `python tests/test_components.py`
3. **Review config**: Ensure `config/config.yaml` is correct
4. **Read docs**: See `USAGE_GUIDE.md` for detailed info

## 🎉 Enjoy E.V3!

Your privacy-focused companion is ready. It will:
- Monitor your system quietly
- Alert you to important events
- Remind you of calendar items
- Chat with you (if AI model installed)
- Look cool while doing it! 😊

**Remember**: Everything stays private and local by default!
