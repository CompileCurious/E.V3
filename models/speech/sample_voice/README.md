# Sample Voice Pack

This is a sample-based voicepack using pre-recorded audio files.

## Structure

```
sample_voice/
├── config.json
└── samples/
    ├── greetings/
    │   ├── hello.wav
    │   ├── hi.wav
    │   ├── good_morning.wav
    │   ├── good_afternoon.wav
    │   └── good_evening.wav
    ├── farewells/
    │   ├── goodbye.wav
    │   └── see_you_later.wav
    └── responses/
        ├── thanks.wav
        ├── thank_you.wav
        ├── yes.wav
        ├── no.wav
        └── okay.wav
```

## Creating Audio Samples

1. **Record with Audacity** (free): https://www.audacityteam.org/
   - Record at 22050 Hz sample rate
   - Export as WAV (16-bit PCM)

2. **Use Text-to-Speech**:
   - Generate audio online
   - Download as WAV files
   - Place in appropriate folders

3. **Voice Actor Recordings**:
   - Hire voice actors
   - Record professional lines
   - Process and organize

## Adding Emotion Variants

For emotion support, record multiple versions:
- `hello.wav` - Normal version
- `hello_happy.wav` - Happy version
- `hello_sad.wav` - Sad version

Configure in `emotion_map` with `sample_suffix`.

## File Format

- **Recommended**: WAV, 22050 Hz, 16-bit, mono
- **Supported**: WAV, MP3, OGG, FLAC
- Keep files small (< 5 MB each)

## Fallback Behavior

When a phrase isn't found in the mapping:
- Falls back to `text_only` mode (displays text without audio)
- Consider using a hybrid voicepack with neural TTS for fallback
