# Character Models

This directory is for your **fully customizable 3D character models**. E.V3 does not include a default character - you bring your own!

## Supported Formats

- **VRM** (.vrm) - VRoid Studio models (recommended for anime-style characters)
- **GLTF/GLB** (.gltf, .glb) - Standard 3D formats from Blender or other tools
- **FBX** (.fbx) - Autodesk FBX format
- **OBJ** (.obj) - Wavefront OBJ format

## Getting Character Models

### VRoid Studio (Recommended)
1. Download VRoid Studio: https://vroid.com/en/studio
2. Create your own character or download from VRoid Hub: https://hub.vroid.com/
3. Export as .vrm file
4. Place in this directory

### Blender
1. Create or download a character model
2. Export as .glb or .gltf
3. Place in this directory

### Other Sources
- Ready Player Me: https://readyplayer.me/
- Sketchfab: https://sketchfab.com/
- CGTrader: https://www.cgtrader.com/

## Configuration

After adding your character model:

1. **Via UI**: Right-click system tray → Modules → Select Character Model (file picker)
2. **Via Config**: Edit `config/config.yaml`:

```yaml
ui:
  model:
    model_path: "models/character/YOUR_MODEL.vrm"
    scale: 0.6              # Adjust size (0.5-1.0)
    position: [0, -1.2, 0]  # [x, y, z] - adjust Y to position vertically
```

## Privacy Note

**Character models are NOT tracked in git** - they are stored locally only. This ensures:
- Your custom character stays private
- Repository stays lightweight
- Full creative freedom without file size limits
- Easy swapping between different characters

## Example E.V3.vrm

If you have an `E.V3.vrm` file here, it's your local customization. The project does not ship with a default character model - it's completely up to you!
