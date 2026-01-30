# Hybrid Voice Pack

This voicepack combines the best of both worlds:
- **Pre-recorded samples** for common phrases and catchphrases
- **Neural TTS** for everything else

## Setup

1. Download Piper TTS model files:
   - `en_US-lessac-medium.onnx`
   - `en_US-lessac-medium.onnx.json`
   - From: https://github.com/rhasspy/piper/releases

2. Create sample folders and record/add audio files:
   ```
   samples/
   ├── greetings/
   ├── farewells/
   └── catchphrases/
   ```

## How It Works

1. **Sample lookup first**: E.V3 checks if there's a pre-recorded sample
2. **TTS fallback**: If no sample exists, generates speech with neural TTS
3. **Emotion variants**: Tries emotion-specific samples (e.g., `hello_happy.wav`)

## Benefits

- **Instant playback** for common phrases
- **Natural voice** for your character's signature lines
- **Unlimited flexibility** for dynamic content
- **Consistent quality** across all speech

## Recommended Samples

Record these common phrases for best experience:
- Greetings: "hello", "good morning", "good afternoon", "good evening"
- Farewells: "goodbye", "see you later", "take care"
- Responses: "yes", "no", "okay", "sure", "understood"
- Character catchphrases: Custom lines that define your character

## Tips

- Keep samples short (1-3 seconds)
- Match the TTS voice quality and style
- Record emotion variants for key phrases
- Use samples for personality, TTS for flexibility
