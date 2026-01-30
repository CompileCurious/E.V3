# E.V3 Speech Models

This directory contains voicepacks for E.V3's text-to-speech system.

## Quick Start

1. **Choose a voicepack type:**
   - **Neural TTS** (Recommended): Download Piper TTS model
   - **Samples**: Record your own audio clips
   - **Hybrid**: Combine both approaches

2. **Set up your voicepack:**
   - See example configs in subfolders
   - Each voicepack needs a `config.json` file

3. **Activate in config:**
   ```yaml
   # In config/config.yaml
   speech:
     active_voicepack: "piper_english"
   ```

4. **Hot-swap anytime:**
   - Drop new voicepack folders here
   - They're automatically detected!

## Directory Structure

```
models/speech/
├── voicepack_schema.json       # JSON schema for config validation
├── piper_english/              # Example: Neural TTS voicepack
│   ├── config.json
│   ├── README.md
│   └── [model files here]
├── sample_voice/               # Example: Sample-based voicepack
│   ├── config.json
│   ├── README.md
│   └── samples/
└── hybrid_voice/               # Example: Hybrid voicepack
    ├── config.json
    ├── README.md
    ├── [model files here]
    └── samples/
```

## Available Voicepacks

### piper_english (Neural TTS)
High-quality English voice using Piper TTS. Requires downloading model files.

**Setup:** See [piper_english/README.md](piper_english/README.md)

### sample_voice (Sample-Based)
Pre-recorded audio clips for common phrases. Add your own WAV files.

**Setup:** See [sample_voice/README.md](sample_voice/README.md)

### hybrid_voice (Hybrid)
Best of both: samples for catchphrases, TTS for flexibility.

**Setup:** See [hybrid_voice/README.md](hybrid_voice/README.md)

## Creating Your Own Voicepack

### Minimal Setup

1. Create a folder: `models/speech/my_voice/`

2. Add `config.json`:
   ```json
   {
     "name": "My Voice",
     "version": "1.0.0",
     "type": "neural",
     "neural": {
       "engine": "piper",
       "model_path": "my_model.onnx",
       "config_path": "my_model.onnx.json"
     }
   }
   ```

3. Add your model files

4. Done! E.V3 will detect it automatically.

## Voicepack Features

### Emotion Support
Automatically adjust voice for different emotions:
- happy, sad, angry, calm, excited, neutral

### Audio Filters
- Equalizer (EQ)
- Compressor
- Reverb

### Fallback Behavior
What to do when speech fails:
- silent, text_only, beep, retry

### Animation Sync
Generates phoneme data for lip-sync animations.

## Testing

Test your voicepack:
```bash
python tools/test_speech.py
```

List available voicepacks:
```bash
python tools/test_speech.py --list
```

## Resources

- **Full Documentation:** [docs/SPEECH_SYSTEM.md](../docs/SPEECH_SYSTEM.md)
- **Model Setup Guide:** [MODEL_SETUP.md](MODEL_SETUP.md)
- **Config Schema:** [voicepack_schema.json](voicepack_schema.json)

## TTS Engines

### Piper (Recommended)
- Fast and lightweight
- High quality
- Download: https://github.com/rhasspy/piper/releases

### Coqui TTS
- Very high quality
- Voice cloning
- Install: `pip install TTS`

### eSpeak (Fallback)
- No model files needed
- Basic quality
- Built-in

## Tips

- **Neural TTS:** Use Q4 quantized models for speed
- **Samples:** Record at 22050 Hz, 16-bit, mono WAV
- **Hybrid:** Pre-record common phrases, use TTS for flexibility
- **Testing:** Run `test_speech.py` to verify setup
- **Performance:** Samples = instant, Neural = 50-500ms

## Support

- Check logs: `logs/ev3_ui.log`
- Validate config: Use JSON schema validation
- Test voicepack: `python tools/test_speech.py`

## License

Voicepacks and models may have their own licenses. Check individual model sources for licensing information.
