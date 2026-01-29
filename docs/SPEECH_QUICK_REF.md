# E.V3 Speech System - Quick Reference

## Message Protocol

### Kernel sends to Shell:

```python
{
    "type": "speak",
    "text": "Good afternoon. How may I assist you today?",
    "emotion": "calm",     # Optional: happy, sad, angry, calm, excited, neutral
    "blocking": False      # Optional: wait for speech to complete
}
```

## Voicepack Types

| Type | Use Case | Speed | Flexibility |
|------|----------|-------|-------------|
| **neural** | TTS generation | 50-500ms | Unlimited text |
| **samples** | Pre-recorded | Instant | Fixed phrases |
| **hybrid** | Best of both | Varies | Full flexibility |

## Directory Structure

```
models/speech/
├── voicepack_schema.json        # Schema definition
├── your_voicepack/              # Your voicepack folder
│   ├── config.json              # Required
│   ├── model.onnx               # Neural TTS model (if neural)
│   └── samples/                 # Audio files (if samples)
│       └── hello.wav
```

## Minimal Config Examples

### Neural (Piper):
```json
{
  "name": "My Voice",
  "version": "1.0.0",
  "type": "neural",
  "neural": {
    "engine": "piper",
    "model_path": "model.onnx",
    "config_path": "model.onnx.json"
  }
}
```

### Samples:
```json
{
  "name": "Sample Voice",
  "version": "1.0.0",
  "type": "samples",
  "samples": {
    "folder": "samples",
    "mapping": {
      "hello": "greetings/hello.wav"
    }
  }
}
```

### Hybrid:
```json
{
  "name": "Hybrid Voice",
  "version": "1.0.0",
  "type": "hybrid",
  "neural": {
    "engine": "piper",
    "model_path": "model.onnx",
    "config_path": "model.onnx.json"
  },
  "samples": {
    "folder": "samples",
    "mapping": {
      "hello": "greetings/hello.wav"
    }
  }
}
```

## Configuration (config.yaml)

```yaml
speech:
  active_voicepack: "piper_english"
  scan_on_startup: true
  auto_reload: true
  reload_check_interval: 10
```

## Emotion Parameters

```json
{
  "emotion_map": {
    "happy": {
      "pitch": 1.2,    // Higher pitch
      "speed": 1.1,    // Faster speech
      "energy": 1.3    // More expressive
    },
    "sad": {
      "pitch": 0.9,    // Lower pitch
      "speed": 0.85,   // Slower speech
      "energy": 0.7    // Less expressive
    },
    "calm": {
      "pitch": 1.0,
      "speed": 0.9,
      "energy": 0.9
    }
  }
}
```

## Audio Filters

```json
{
  "filters": {
    "eq": {
      "enabled": true,
      "low": 1.0,      // Bass
      "mid": 0.0,      // Mids
      "high": -0.5     // Treble
    },
    "compressor": {
      "enabled": true,
      "threshold": -20.0,
      "ratio": 3.0
    },
    "reverb": {
      "enabled": false,
      "room_size": 0.3,
      "damping": 0.5
    }
  }
}
```

## Testing

### List voicepacks:
```bash
python tools/test_speech.py --list
```

### Test speech:
```bash
python tools/test_speech.py
```

### From Python:
```python
from ui.speech import SpeechManager

sm = SpeechManager(config)
result = sm.speak("Hello world!", "happy")
# Returns: {'duration': 1.5, 'phonemes': [...]}
```

## Installation

```bash
# Required for audio playback
pip install pygame

# Optional TTS engines
pip install piper-tts      # Recommended
pip install TTS            # Coqui TTS (larger, higher quality)
```

## Quick Setup

1. **Download Piper voice:**
   - https://github.com/rhasspy/piper/releases
   - Get `.onnx` and `.onnx.json` files

2. **Place in folder:**
   ```
   models/speech/piper_english/
   ├── config.json
   ├── model.onnx
   └── model.onnx.json
   ```

3. **Configure:**
   ```yaml
   speech:
     active_voicepack: "piper_english"
   ```

4. **Test:**
   ```bash
   python tools/test_speech.py
   ```

## Common Tasks

### Switch voicepack:
Edit `config/config.yaml`:
```yaml
speech:
  active_voicepack: "new_voicepack"
```

### Add emotion:
Edit voicepack `config.json`:
```json
{
  "emotion_map": {
    "custom_emotion": {
      "pitch": 1.1,
      "speed": 1.0,
      "energy": 1.2
    }
  }
}
```

### Use pre-recorded sample:
1. Record/get WAV file
2. Place in `samples/` folder
3. Add to mapping:
```json
{
  "samples": {
    "mapping": {
      "your text": "path/to/file.wav"
    }
  }
}
```

## Files Reference

| File | Purpose |
|------|---------|
| `models/speech/voicepack_schema.json` | Schema definition |
| `models/speech/README.md` | Quick start guide |
| `models/MODEL_SETUP.md` | Setup instructions |
| `docs/SPEECH_SYSTEM.md` | Complete documentation |
| `SPEECH_IMPLEMENTATION.md` | Implementation details |
| `ui/speech/speech_manager.py` | Main speech engine |
| `ui/speech/voicepack_loader.py` | Voicepack scanner |
| `tools/test_speech.py` | Test script |

## Troubleshooting

### No audio:
```bash
pip install pygame
```

### Model not loading:
- Check file paths in `config.json`
- Verify model files exist
- Check logs: `logs/ev3_ui.log`

### Wrong emotion:
- Check `emotion_map` in config
- Verify emotion name matches
- Try different parameter values

### Voicepack not found:
- Ensure folder is in `models/speech/`
- Verify `config.json` exists
- Check `active_voicepack` name matches folder

## Resources

- **Piper TTS:** https://github.com/rhasspy/piper
- **Coqui TTS:** https://github.com/coqui-ai/TTS
- **Schema:** `models/speech/voicepack_schema.json`
- **Examples:** `models/speech/*/config.json`
