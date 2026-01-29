# E.V3 Speech System Documentation

## Overview

E.V3's speech system provides **100% local text-to-speech** with zero cloud dependencies. The system is built around hot-swappable voicepacks that can contain neural TTS models, pre-recorded samples, or both.

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────┐
│                        KERNEL                           │
│  - Generates text responses                             │
│  - Sends IPC message: {"type":"speak", "text":"...",    │
│    "emotion":"calm"}                                    │
└────────────────────┬────────────────────────────────────┘
                     │ IPC
                     ▼
┌─────────────────────────────────────────────────────────┐
│                        SHELL                            │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │          SpeechManager                           │  │
│  │  - Receives speak commands                       │  │
│  │  - Selects active voicepack                      │  │
│  │  - Generates/loads audio                         │  │
│  │  - Applies filters & emotion modulation          │  │
│  │  - Plays audio                                   │  │
│  │  - Returns phoneme data for lip-sync             │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │       VoicepackLoader                            │  │
│  │  - Scans models/speech/ folder                   │  │
│  │  - Validates config.json files                   │  │
│  │  - Hot-swaps voicepacks                          │  │
│  │  - Watches for changes                           │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │      TTS Engines (Piper, Coqui, etc.)           │  │
│  │  - Load neural TTS models                        │  │
│  │  - Synthesize speech from text                   │  │
│  │  - Apply voice parameters                        │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Message Protocol

### Kernel → Shell: Speak Request

```json
{
  "type": "speak",
  "text": "Good afternoon. How may I assist you today?",
  "emotion": "calm",
  "blocking": false
}
```

**Fields:**
- `text` (required): Text to speak
- `emotion` (optional): Emotion tag - "neutral", "happy", "sad", "angry", "calm", "excited", etc.
- `blocking` (optional): Wait for speech to complete before returning

### Shell → Kernel: Speech Status (Future)

```json
{
  "type": "speech_complete",
  "duration": 3.2,
  "success": true
}
```

## Voicepack System

### Structure

```
models/speech/
├── voicepack_schema.json          # JSON schema definition
├── piper_english/                 # Neural TTS voicepack
│   ├── config.json
│   ├── README.md
│   ├── en_US-lessac-medium.onnx   # Model file
│   └── en_US-lessac-medium.onnx.json
├── sample_voice/                  # Sample-based voicepack
│   ├── config.json
│   ├── README.md
│   └── samples/
│       ├── greetings/
│       │   ├── hello.wav
│       │   └── good_morning.wav
│       └── farewells/
│           └── goodbye.wav
└── hybrid_voice/                  # Hybrid voicepack
    ├── config.json
    ├── README.md
    ├── en_US-lessac-medium.onnx   # TTS model
    ├── en_US-lessac-medium.onnx.json
    └── samples/                    # Pre-recorded catchphrases
        └── catchphrases/
            └── ready.wav
```

### Config Schema

Voicepacks are defined by a `config.json` file. Full schema: [models/speech/voicepack_schema.json](models/speech/voicepack_schema.json)

**Minimal Neural Config:**
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

**Minimal Sample Config:**
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

**Full Config Example:**
```json
{
  "name": "Advanced Voice",
  "version": "1.0.0",
  "author": "Your Name",
  "description": "High-quality voice with emotion support",
  "type": "hybrid",
  
  "neural": {
    "engine": "piper",
    "model_path": "model.onnx",
    "config_path": "model.onnx.json",
    "sample_rate": 22050
  },
  
  "samples": {
    "folder": "samples",
    "format": "wav",
    "mapping": {
      "hello": "greetings/hello.wav"
    }
  },
  
  "parameters": {
    "pitch": 1.0,
    "speed": 1.0,
    "volume": 0.9,
    "energy": 1.0
  },
  
  "emotion_map": {
    "happy": {
      "pitch": 1.2,
      "speed": 1.1,
      "energy": 1.3
    },
    "sad": {
      "pitch": 0.9,
      "speed": 0.85,
      "energy": 0.7
    }
  },
  
  "filters": {
    "eq": {
      "enabled": true,
      "low": 1.0,
      "mid": 0.0,
      "high": -0.5
    },
    "compressor": {
      "enabled": true,
      "threshold": -20.0,
      "ratio": 3.0
    }
  },
  
  "fallback": {
    "behavior": "text_only",
    "retry_count": 2
  },
  
  "animation_sync": {
    "enabled": true,
    "estimate_timing": true
  }
}
```

## Voice Parameters

### Base Parameters

- **pitch** (0.1 - 3.0, default 1.0): Voice pitch multiplier
  - < 1.0: Lower pitch
  - \> 1.0: Higher pitch
  
- **speed** (0.1 - 3.0, default 1.0): Speech rate multiplier
  - < 1.0: Slower
  - \> 1.0: Faster
  
- **volume** (0.0 - 1.0, default 1.0): Audio volume
  
- **energy** (0.1 - 2.0, default 1.0): Speech intensity/expressiveness

### Emotion Mapping

Emotions automatically adjust parameters:

```json
{
  "emotion_map": {
    "happy": {"pitch": 1.2, "speed": 1.1, "energy": 1.3},
    "sad": {"pitch": 0.9, "speed": 0.85, "energy": 0.7},
    "angry": {"pitch": 0.95, "speed": 1.15, "energy": 1.5},
    "calm": {"pitch": 1.0, "speed": 0.9, "energy": 0.9},
    "excited": {"pitch": 1.3, "speed": 1.2, "energy": 1.4}
  }
}
```

When kernel sends `"emotion": "happy"`, these multipliers are applied to base parameters.

## Audio Filters

### Equalizer (EQ)

Adjust frequency response:

```json
{
  "eq": {
    "enabled": true,
    "low": 2.0,      // Boost bass
    "mid": 0.0,      // Neutral mids
    "high": -1.0     // Reduce treble
  }
}
```

### Compressor

Dynamic range compression:

```json
{
  "compressor": {
    "enabled": true,
    "threshold": -20.0,  // dB threshold
    "ratio": 4.0         // Compression ratio
  }
}
```

### Reverb

Add spatial depth:

```json
{
  "reverb": {
    "enabled": true,
    "room_size": 0.3,    // 0.0 - 1.0
    "damping": 0.5       // 0.0 - 1.0
  }
}
```

## Fallback Behavior

When speech generation fails:

- **silent**: No output, no error
- **text_only**: Display text without audio
- **beep**: Play simple beep sound
- **retry**: Retry generation N times

```json
{
  "fallback": {
    "behavior": "text_only",
    "retry_count": 2,
    "backup_voicepack": "fallback_voice"
  }
}
```

## Hot-Swapping

Voicepacks can be changed without restarting E.V3:

### In config.yaml:

```yaml
speech:
  active_voicepack: "piper_english"
  auto_reload: true
  reload_check_interval: 10  # seconds
```

### Programmatic:

```python
# In main_ui.py
app.speech_manager.set_voicepack("new_voicepack")

# Rescan for new voicepacks
app.speech_manager.reload_voicepacks()
```

### User Action:

1. Drop new voicepack folder into `models/speech/`
2. Edit `config/config.yaml` to set `active_voicepack`
3. Voicepack loads automatically (if `auto_reload: true`)

## TTS Engines

### Piper (Recommended)

**Pros:**
- Fast, lightweight
- High quality
- Many languages
- Easy to use

**Setup:**
```bash
# Install
pip install piper-tts

# Download models
# Visit: https://github.com/rhasspy/piper/releases
```

**Config:**
```json
{
  "neural": {
    "engine": "piper",
    "model_path": "en_US-lessac-medium.onnx",
    "config_path": "en_US-lessac-medium.onnx.json"
  }
}
```

### Coqui TTS

**Pros:**
- Very high quality
- Voice cloning support
- Extensive customization

**Cons:**
- Larger models
- Slower generation
- More dependencies

**Setup:**
```bash
pip install TTS
```

**Config:**
```json
{
  "neural": {
    "engine": "coqui",
    "model_path": "tts_models/en/ljspeech/tacotron2-DDC"
  }
}
```

### eSpeak (Fallback)

**Pros:**
- Very lightweight
- No model files needed

**Cons:**
- Robotic sound
- Limited quality

**Config:**
```json
{
  "neural": {
    "engine": "espeak"
  }
}
```

## Animation Synchronization

Speech generates phoneme/timing data for lip-sync:

```python
result = speech_manager.speak("Hello world", "happy")
# Returns:
{
  "duration": 1.5,           # seconds
  "phonemes": [              # Phoneme timing data
    {"phoneme": "HH", "start": 0.0, "end": 0.1},
    {"phoneme": "AH", "start": 0.1, "end": 0.3},
    # ...
  ],
  "sample_rate": 22050
}
```

The shell can use this to drive character animations:

```python
def _handle_speak(self, data):
    result = self.speech_manager.speak(data['text'], data['emotion'])
    if result and hasattr(self.window, 'sync_speech_animation'):
        self.window.sync_speech_animation(result)
```

## Creating Custom Voicepacks

### 1. Neural TTS Voicepack

```bash
# Create folder
mkdir models/speech/my_voice

# Download TTS model
# Place .onnx and .json files in folder

# Create config.json
```

### 2. Sample-Based Voicepack

```bash
# Create structure
mkdir models/speech/my_samples
mkdir models/speech/my_samples/samples

# Record audio files (WAV, 22050 Hz recommended)
# Place in samples/ folder

# Create config.json with mappings
```

### 3. Hybrid Voicepack

Combine both approaches:
- Neural TTS for flexibility
- Samples for character catchphrases
- Samples for common greetings
- Neural TTS for everything else

## Performance Considerations

- **Neural TTS**: 50-500ms generation time (depends on model and hardware)
- **Samples**: Instant playback
- **Hybrid**: Best of both worlds

**Optimization Tips:**
- Use Q4 or Q5 quantized models for faster generation
- Enable GPU acceleration if available
- Pre-generate common phrases as samples
- Use smaller models for real-time interaction

## Troubleshooting

### No audio output

1. Check pygame installation: `pip install pygame`
2. Verify voicepack config is valid
3. Check logs for errors

### Model not loading

1. Ensure model files exist in voicepack folder
2. Verify `model_path` in config.json
3. Check TTS engine is installed

### Speech sounds wrong

1. Adjust `parameters` in config.json
2. Try different `emotion_map` values
3. Test different TTS models

### Voicepack not detected

1. Ensure folder is in `models/speech/`
2. Verify `config.json` exists and is valid
3. Check required fields are present
4. Run `reload_voicepacks()` or restart shell

## Future Enhancements

- [ ] Voice cloning support
- [ ] Real-time audio effects processing
- [ ] Advanced phoneme extraction for better lip-sync
- [ ] Multi-language support per voicepack
- [ ] Streaming TTS for long text
- [ ] Emotion detection from text
- [ ] Background music mixing
- [ ] Audio ducking (lower music during speech)

## References

- Piper TTS: https://github.com/rhasspy/piper
- Coqui TTS: https://github.com/coqui-ai/TTS
- Voicepack Schema: [models/speech/voicepack_schema.json](models/speech/voicepack_schema.json)
- Model Setup Guide: [models/MODEL_SETUP.md](models/MODEL_SETUP.md)
