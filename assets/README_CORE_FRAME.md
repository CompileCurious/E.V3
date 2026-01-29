# Modules Frame Vector Image

Place your vector robot frame image here as `core_frame.eps` or `core_frame.svg`

## Supported Formats
- **EPS** (Encapsulated PostScript) - Preferred
- **SVG** (Scalable Vector Graphics) - Alternative

## Expected Specifications
- Dimensions: 500x550px recommended (will be scaled to fit)
- Transparent background recommended
- Clear definition of body parts (skull, throat, chest, etc.)

## Component Positions

The clickable regions are positioned based on the following body parts:

- **Skull** (210, 50, 80x80) - Brain/LLM selection
- **Throat** (230, 140, 40x50) - Voice/TTS selection  
- **Left Ear** (160, 70, 30x40) - Speech-to-Text selection
- **Right Eye** (340, 70, 30x40) - Computer Vision selection
- **Heart** (215, 210, 70x60) - Personality/Character selection
- **Chest** (200, 280, 100x80) - Modules Settings

## Placeholder

Until you upload `core_frame.eps` or `core_frame.svg`, the system will display a simple geometric robot frame as a placeholder.

## To Add Your Custom Frame:
1. Create or download a robot frame vector image
2. Save it as `assets/core_frame.eps` (or `core_frame.svg`)
3. If using EPS, ensure Pillow is installed: `pip install pillow`
4. Restart the application
5. The Modules window will automatically use your custom image

## Notes
- EPS files require the Pillow library for rendering
- The system will try EPS first, then fall back to SVG
- If neither is found, a geometric placeholder is displayed
