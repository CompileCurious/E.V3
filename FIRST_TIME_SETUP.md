# First Time Setup Guide

> **Welcome to E.V3!** This guide will help you get started with your fully customizable desktop companion.

## ⚠️ Alpha Status

E.V3 is in active development. Core features work, but many exciting features are still coming. See the Roadmap in [README.md](README.md) for what's next!

## 📋 Prerequisites

Before you start, you need:
1. **Windows 10/11**
2. **Python 3.13** (or 3.10+)
3. **8GB+ RAM** (16GB recommended for LLMs)
4. **Internet connection** (for downloading models)
5. **~7GB free disk space** (for LLM models)

## 🚀 Quick Start

### Step 1: Install Dependencies

```bash
# From E.V3 directory
setup.bat

# Or manually:
pip install -r requirements.txt
pip install llama-cpp-python
```

### Step 2: Download LLM Models (Required)

E.V3 needs **both** models for full functionality:

**Fast Mode (Phi-3)**:
```bash
python tools/download_phi3.py
```

**Deep Thinking Mode (Mistral)**:
1. Go to: https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF
2. Download: `mistral-7b-instruct-v0.2.Q4_K_M.gguf` (~4.4GB)
3. Place in: `models/llm/`

### Step 3: Add Your Character (Required)

**E.V3 does NOT include a default character** - bring your own!

**Quick Options**:
- **VRoid Studio**: https://vroid.com/en/studio (create custom)
- **VRoid Hub**: https://hub.vroid.com/ (download pre-made)
- **Ready Player Me**: https://readyplayer.me/ (quick avatar)

**Steps**:
1. Get a VRM, GLB, or GLTF file
2. Place in: `models/character/`
3. Name it something memorable (e.g., `my-character.vrm`)

### Step 4: Launch E.V3

```bash
start_ev3.bat
```

This starts both the kernel (background service) and shell (UI).

### Step 5: Configure Your Character

1. Look for E.V3 icon in system tray (bottom-right)
2. Right-click → **Modules**
3. Select your character model using file picker
4. Adjust LLM mode (Fast or Deep)
5. Type 'Y' in commit field and press Enter
6. Restart E.V3 to see your character!

## 🎨 Customization

### Character Positioning

If your character is too big, too small, or positioned wrong:

1. Edit `config/config.yaml`:
```yaml
ui:
  model:
    model_path: "models/character/YOUR_MODEL.vrm"
    scale: 0.6              # Adjust: 0.5 (smaller) to 1.0 (larger)
    position: [0, -1.2, 0]  # Y value: negative = down, positive = up
```

2. Restart E.V3 to see changes

### LLM Modes

- **Fast Mode**: Quick responses, uses Phi-3 (2.3GB)
- **Deep Mode**: Detailed responses, uses Mistral (4.4GB)

Switch via system tray → Modules → LLM Mode dropdown

## 🔧 Troubleshooting

### "No character showing"
- Ensure you added a character model to `models/character/`
- Check `config/config.yaml` has correct `model_path`
- Verify model file format is supported (.vrm, .glb, .gltf)

### "LLM not responding"
- Install: `pip install llama-cpp-python`
- Verify both LLM models exist in `models/llm/`
- Check logs: `logs/ev3.log`

### "Kernel won't start"
- Check no other instance is running
- Look in Task Manager for `python` processes
- Check logs: `logs/ev3.log`

### "Character is white/has no textures"
- Some VRM models don't export textures properly
- Try a different VRM model
- Check logs for texture loading errors

## 📚 Next Steps

- Read [USAGE_GUIDE.md](USAGE_GUIDE.md) for detailed usage
- See [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
- Check [docs/SPEECH_SYSTEM.md](docs/SPEECH_SYSTEM.md) for TTS setup
- Join community discussions (coming soon!)

## 🎉 You're Ready!

Press **Win+C** (default hotkey) to summon your character and start chatting!

Remember: This is **Alpha software**. Things may break, features are incomplete, but we're actively developing. Your feedback helps make E.V3 better!

---

**Privacy Reminder**: All your models (LLM and character) stay on your machine. Nothing is uploaded or tracked. E.V3 is yours alone!
