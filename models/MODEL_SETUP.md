# E.V3 Model Setup Guide

## Downloading the Local LLM Model

E.V3 uses Mistral 7B Instruct for local AI processing. This ensures privacy by keeping all AI processing on your machine.

### Download Mistral 7B Quantized Model

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

## 3D Character Model Setup

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

## Testing Without Models

E.V3 includes a simple built-in character for testing. If no model is found, it will automatically use a basic geometric character.

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
