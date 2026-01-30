# E.V3 Model Setup Guide

> **Important**: E.V3 does NOT include LLM or character models. All models are downloaded/added separately for privacy and modularity. Models are stored locally only and NOT tracked in git.

## 🤖 Downloading Local LLM Models

E.V3 supports dual LLM modes for different use cases. Both models are **required** for full functionality.

### Fast Mode: Phi-3-mini (Recommended for Quick Responses)

**Automated Download**:
```bash
python tools/download_phi3.py
```

**Manual Download**:
1. Visit: https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf
2. Download: `Phi-3-mini-4k-instruct-q4.gguf` (~2.3 GB)
3. Place in: `models/llm/`

### Deep Thinking Mode: Mistral 7B (For Complex Reasoning)

1. Visit: https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF

2. Download the quantized model (recommended: Q4_K_M for balance of size and quality):
   - File: `mistral-7b-instruct-v0.2.Q4_K_M.gguf`
   - Size: ~4.4 GB

3. Place the file in: `models/llm/`

### Alternative Quantizations

- **Q2_K** (~2.5 GB) - Smallest, lower quality
- **Q4_K_M** (~4.4 GB) - **Recommended** - Good balance
- **Q5_K_M** (~5.2 GB) - Higher quality
- **Q8_0** (~7.7 GB) - Highest quality, largest size

**Privacy Note**: Models stay on your machine and are never tracked in version control.

## 🎨 3D Character Model Setup

**E.V3 does NOT include a default character** - you bring your own! This ensures full creative freedom and privacy.

E.V3 supports VRoid Studio models (.vrm) and standard 3D formats (.glb, .gltf).

### Option 1: VRoid Studio (Recommended for Anime-style Characters)

1. Download VRoid Studio: https://vroid.com/en/studio

2. Create or download a character:
   - Create your own in VRoid Studio
   - Download from VRoid Hub: https://hub.vroid.com/

3. Export as .vrm file:
   - File > Export > VRM

4. Place the .vrm file in: `models/character/`

5. Update `config/config.yaml`:
   ```yaml
   ui:
     model:
       model_path: "models/character/your-character.vrm"
   ```

### Option 2: Blender

1. Create or download a character model in Blender

2. Ensure the model has:
   - **Armature** (bone structure) for animations
   - **Blendshapes/Shape Keys** for facial expressions (optional but recommended)
   - UV-mapped textures

3. Export as GLB or GLTF:
   - File > Export > glTF 2.0 (.glb/.gltf)
   - Check: Include > Mesh, Armature, Shape Keys
   - Check: Transform > +Y Up

4. Place the file in: `models/character/`

5. Update `config/config.yaml`:
   ```yaml
   ui:
     model:
       model_path: "models/character/your-character.glb"
   ```

### Recommended Blendshapes/Shape Keys

For best animation support, include these shape keys:

**Eyes:**
- `eye_blink_left`
- `eye_blink_right`
- `eye_wide`
- `eye_happy`
- `eye_sad`

**Mouth:**
- `mouth_smile`
- `mouth_frown`
- `mouth_o`

**Brows:**
- `brow_angry`
- `brow_surprised`

**Body:**
- Ensure armature has bones named: `spine`, `chest`, `head`, `neck`

## Free Model Resources

### VRoid Models
- VRoid Hub: https://hub.vroid.com/
- Booth.pm: https://booth.pm/ (search "VRM")

### Generic 3D Models
- Sketchfab: https://sketchfab.com/ (filter: Downloadable, GLTF/GLB)
- Mixamo: https://www.mixamo.com/ (free rigged characters)

## Speech/Voice Setup

E.V3 supports local text-to-speech with hot-swappable voicepacks. No cloud APIs required.

### Voicepack Types

**Neural TTS:**
- Lightweight TTS models (Piper, Coqui TTS, etc.)
- Real-time generation
- Flexible and natural-sounding

**Sample-Based:**
- Pre-recorded audio clips
- Instant playback
- Best for specific phrases or character catchphrases

**Hybrid:**
- Combines both approaches
- Uses samples when available, TTS for everything else

### Setting Up Voicepacks

1. Create a folder in `models/speech/`:
   ```
   models/speech/my_voicepack/
   ```

2. Add a `config.json` file (see schema below)

3. Add your TTS model files OR audio samples

4. Voicepack is automatically detected and hot-swappable!

### Quick Start: Piper TTS (Recommended)

1. Download a Piper voice from: https://github.com/rhasspy/piper/releases
   - Choose a language and voice
   - Download both `.onnx` model and `.json` config

2. Create voicepack structure:
   ```
   models/speech/piper_english/
   ├── config.json
   ├── en_US-lessac-medium.onnx
   └── en_US-lessac-medium.onnx.json
   ```

3. Create `config.json`:
   ```json
   {
     "name": "Piper English",
     "version": "1.0.0",
     "type": "neural",
     "neural": {
       "engine": "piper",
       "model_path": "en_US-lessac-medium.onnx",
       "config_path": "en_US-lessac-medium.onnx.json",
       "sample_rate": 22050
     },
     "parameters": {
       "pitch": 1.0,
       "speed": 1.0,
       "volume": 1.0
     },
     "emotion_map": {
       "happy": { "pitch": 1.2, "speed": 1.1 },
       "sad": { "pitch": 0.9, "speed": 0.85 },
       "calm": { "pitch": 1.0, "speed": 0.9 }
     }
   }
   ```

### Creating a Sample-Based Voicepack

1. Record or collect audio files (WAV format recommended)

2. Organize in a folder structure:
   ```
   models/speech/sample_voice/
   ├── config.json
   └── samples/
       ├── greetings/
       │   ├── hello.wav
       │   ├── good_morning.wav
       │   └── good_evening.wav
       ├── farewells/
       │   └── goodbye.wav
       └── emotions/
           ├── happy_laugh.wav
           └── sad_sigh.wav
   ```

3. Create `config.json`:
   ```json
   {
     "name": "Sample Voice",
     "version": "1.0.0",
     "type": "samples",
     "samples": {
       "folder": "samples",
       "format": "wav",
       "mapping": {
         "hello": "greetings/hello.wav",
         "good morning": "greetings/good_morning.wav",
         "good evening": "greetings/good_evening.wav",
         "goodbye": "farewells/goodbye.wav"
       }
     },
     "parameters": {
       "volume": 1.0
     },
     "fallback": {
       "behavior": "text_only"
     }
   }
   ```

### Voicepack Config Schema

Full schema available at: `models/speech/voicepack_schema.json`

**Required Fields:**
- `name` - Display name
- `version` - Semantic version (e.g., "1.0.0")
- `type` - "neural", "samples", or "hybrid"
- `neural` - TTS model config (if type is neural/hybrid)
  - `engine` - "piper", "coqui", "espeak", "custom"
  - `model_path` - Path to model file
- `samples` - Sample config (if type is samples/hybrid)
  - `folder` - Folder containing audio files
  - `mapping` - Text-to-file mapping (optional)

**Optional Fields:**
- `parameters` - pitch, speed, volume, energy
- `emotion_map` - Adjust parameters per emotion
- `filters` - reverb, eq, compressor
- `fallback` - Behavior when generation fails
- `animation_sync` - Lip-sync settings
- `metadata` - language, gender, age, tags

### Selecting Active Voicepack

In `config/config.yaml`:
```yaml
speech:
  active_voicepack: "piper_english"  # Name of folder in models/speech/
  scan_on_startup: true
  auto_reload: true  # Hot-swap support
```

### Free TTS Resources

**Piper TTS Models:**
- https://github.com/rhasspy/piper/releases
- High quality, fast, lightweight
- Many languages available

**Coqui TTS Models:**
- https://github.com/coqui-ai/TTS
- Install: `pip install TTS`
- Download models via CLI

**Sample Sources:**
- Record your own with Audacity (free)
- Generate with online TTS, then download
- Voice actor recordings

### Advanced: Audio Filters

Apply post-processing to generated speech:

```json
{
  "filters": {
    "reverb": {
      "enabled": true,
      "room_size": 0.3,
      "damping": 0.5
    },
    "eq": {
      "enabled": true,
      "low": 2.0,
      "mid": 0.0,
      "high": -1.0
    },
    "compressor": {
      "enabled": true,
      "threshold": -20.0,
      "ratio": 4.0
    }
  }
}
```

### Emotion Mapping

Automatically adjust voice parameters based on emotion:

```json
{
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
    },
    "angry": {
      "pitch": 0.95,
      "speed": 1.15,
      "energy": 1.5
    },
    "calm": {
      "pitch": 1.0,
      "speed": 0.9,
      "energy": 0.9
    },
    "excited": {
      "pitch": 1.3,
      "speed": 1.2,
      "energy": 1.4
    }
  }
}
```

## Testing Without Models

E.V3 includes a simple built-in character for testing. If no model is found, it will automatically use a basic geometric character.

For speech, E.V3 will fall back to text-only display if no voicepacks are configured.

## Model Configuration

Edit `config/config.yaml` to adjust model settings:

```yaml
ui:
  model:
    model_path: "models/character/character.vrm"
    scale: 1.0  # Adjust size
    rotation: [0, 0, 0]  # Rotation in degrees [X, Y, Z]
    position: [0, 0, 0]  # Position offset [X, Y, Z]
```

## Troubleshooting

### Model not loading
- Check file path in config.yaml
- Ensure file format is supported (.vrm, .glb, .gltf)
- Check console logs for errors

### Model too large/small
- Adjust `scale` in config.yaml
- Try values between 0.5 and 2.0

### Model upside down or rotated wrong
- Adjust `rotation` in config.yaml
- Common fix: `rotation: [0, 180, 0]`

### Animations not working
- Ensure model has armature/bones
- Check bone naming conventions
- VRM models have standardized bone names
