# Phase 4: Voice & Audio Generation

**Status:** ✅ IMPLEMENTED  
**Date:** 2026-07-27  
**Components:** TTS Providers, Music Selection, Audio Mixing

---

## Overview

Phase 4 automates the complete audio pipeline for video production:

1. **Narration Generation (TTS)** — Convert scripts to speech
2. **Music Selection** — Choose or generate background music
3. **Audio Mixing** — Combine narration + music with ducking and normalization

The entire phase is **zero-cost** when using open-source providers (Kokoro, Piper, music library).

---

## Architecture

```
orchestrate.py (Phase 4)
    ↓
├─ 4a: Narration (TTS)
│   ├─ Kokoro TTS (primary, open-source, free, offline)
│   └─ Piper TTS (fallback, open-source, free, offline)
│
├─ 4b: Music Selection
│   ├─ User's music_library/ folder (free)
│   └─ Google Music API (Lyria 3 Pro, ~$0.01-0.05/track)
│
└─ 4c: Audio Mixing
    └─ AudioMixer (FFmpeg-based, speech ducking, normalization)
```

---

## TTS Providers

### Kokoro TTS (Primary Choice)

**Why:** Open-source, fast, natural-sounding, offline, completely free.

```python
from tools.audio.kokoro_tts import KokoroTTS

tool = KokoroTTS()
result = tool.execute({
    "text": "Your narration text here",
    "voice": "en",              # Language code
    "speed": 1.0,               # 0.5-2.0 range
    "output_path": "narration.wav"
})
```

**Setup:**
```bash
pip install kokoro-onnx
# or
pip install git+https://github.com/remixer-dec/kokoro-onnx.git
```

**Supported Languages:**
- af (Afrikaans)
- am (Amharic)
- en (English)
- es (Spanish)
- fr (French)
- ja (Japanese)
- ko (Korean)
- pt (Portuguese)
- tr (Turkish)
- zh (Chinese)

**Cost:** $0.00 (local, open-source)

---

### Piper TTS (Fallback)

**Why:** Proven offline TTS, multiple voice models, zero API cost.

```python
from tools.audio.piper_tts import PiperTTS

tool = PiperTTS()
result = tool.execute({
    "text": "Your narration text here",
    "output_path": "narration.wav"
})
```

**Setup:**
```bash
pip install piper-tts
piper --download-dir ~/.piper/models --model en_US-lessac-medium
```

**Cost:** $0.00 (local)

---

### Google TTS (Cloud Alternative)

**When to Use:** If you prefer Google's voices (700+ options).

```python
from tools.audio.google_tts import GoogleTTS

tool = GoogleTTS()
result = tool.execute({
    "text": "Your narration text",
    "voice_name": "en-US-Neural2-C",
    "output_path": "narration.wav"
})
```

**Cost:** ~$0.016/1M characters (~$0.001 per 60s video)  
**Setup:** `GOOGLE_API_KEY` in .env

---

### OpenAI TTS

**When to Use:** For premium, natural-sounding voices.

```python
from tools.audio.openai_tts import OpenAITTS

tool = OpenAITTS()
result = tool.execute({
    "text": "Your narration text",
    "voice": "alloy",  # alloy, echo, fable, onyx, nova, shimmer
    "output_path": "narration.wav"
})
```

**Cost:** ~$0.015 per 1M characters  
**Setup:** `OPENAI_API_KEY` in .env

---

### ElevenLabs TTS

**When to Use:** For highly expressive, cloneable voices.

```python
from tools.audio.elevenlabs_tts import ElevenLabsTTS

tool = ElevenLabsTTS()
result = tool.execute({
    "text": "Your narration text",
    "voice_id": "21m00Tcm4TlvDq8ikWAM",  # Pre-defined voice
    "model_id": "eleven_multilingual_v2",
    "output_path": "narration.wav"
})
```

**Cost:** Free tier (10k characters/month) or $11+/month  
**Setup:** `ELEVENLABS_API_KEY` in .env

---

## Music Selection

### User's Music Library (Priority 1)

Create a `music_library/` folder in the project root and drop your royalty-free tracks:

```
music_library/
├── ambient_track.mp3
├── cinematic_epic.m4a
└── upbeat_corporate.wav
```

```python
from tools.audio.music_library import MusicLibrary

tool = MusicLibrary()
result = tool.execute({"operation": "list"})

# Returns available tracks with duration, file format, etc.
```

**Cost:** $0.00 (your own files)  
**Sources:** YouTube Audio Library, Jamendo, Freesound, Pixabay Music

---

### Google Music (Lyria 3 Pro)

Generate music via Google's AI:

```python
from tools.audio.google_music import GoogleMusic

tool = GoogleMusic()
result = tool.execute({
    "prompt": "Upbeat electronic background music, 60-90 BPM, energetic",
    "duration_seconds": 600,
    "output_path": "background_music.mp3"
})
```

**Cost:** ~$0.03-0.05 per track (depends on duration)  
**Setup:** `GOOGLE_API_KEY` in .env  
**Max Duration:** 184 seconds

---

### Suno Music

Generate full songs with lyrics:

```python
from tools.audio.suno_music import SunoMusic

tool = SunoMusic()
result = tool.execute({
    "prompt": "Epic orchestral cinematic score for space documentary",
    "duration_seconds": 600,
    "output_path": "epic_score.mp3"
})
```

**Cost:** Free tier (25 credits/month) or $10/month  
**Setup:** `SUNO_API_KEY` in .env

---

### Pixabay Music

Free royalty-free music search:

```python
from tools.audio.pixabay_music import PixabayMusic

tool = PixabayMusic()
result = tool.execute({
    "query": "upbeat corporate",
    "duration_seconds": 600,
    "output_path": "pixabay_music.mp3"
})
```

**Cost:** $0.00 (free API)  
**Setup:** `PIXABAY_API_KEY` in .env

---

## Audio Mixing

The `AudioMixer` combines narration + music with professional mixing:

```python
from tools.audio.audio_mixer import AudioMixer

mixer = AudioMixer()

# Simple duck: lower music when speech is present
result = mixer.execute({
    "operation": "full_mix",
    "primary_audio": "narration.wav",        # Speech (stays full volume)
    "secondary_audio": "background_music.mp3",  # Music (gets ducked)
    "output_path": "final_audio.wav"
})
```

**Features:**
- **Speech Ducking:** Music volume drops 3-6dB when narration is present
- **Normalization:** Ensures consistent loudness levels
- **Crossfades:** Smooth transitions between segments
- **Loudness Targeting:** Matches YouTube/broadcast standards

---

## Phase 4 in the Orchestrator

### Basic Usage

```bash
# Run full production including Phase 4 audio
python orchestrate.py --title "My Video" --topic "AI in 2024"

# Skip audio generation
python orchestrate.py --title "My Video" --topic "AI in 2024" --skip-audio

# Skip research and script, just do audio
python orchestrate.py --title "My Video" --topic "AI in 2024" \
  --skip-research --skip-script --skip-assets
```

### Batch Mode

```bash
python orchestrate.py --batch videos.json
```

**videos.json:**
```json
{
  "videos": [
    {
      "title": "AI in 2024",
      "topic": "Latest AI trends and developments",
      "type": "educational",
      "duration": 600
    },
    {
      "title": "How to Learn Python",
      "topic": "Python programming for beginners",
      "type": "tutorial",
      "duration": 900
    }
  ]
}
```

### Output Structure

```
production_output/
├── audio/
│   ├── My_Video_narration_kokoro.wav      # Generated narration
│   ├── My_Video_music.mp3                 # Background music
│   └── My_Video_final_mix.wav             # Final mixed audio
├── scripts/
│   ├── My_Video_script.json
│   └── My_Video_voiceover.txt
├── assets/
│   └── ...
└── manifests/
    └── My_Video_asset_manifest.json
```

---

## Cost Breakdown

### Fully Open-Source Path (Zero Cost)

| Step | Provider | Cost |
|------|----------|------|
| Narration | Kokoro TTS | $0.00 |
| Music | User's library | $0.00 |
| Mixing | AudioMixer (FFmpeg) | $0.00 |
| **Total per video** | | **$0.00** |

### Production Path (Minimal Cost)

| Step | Provider | Cost |
|------|----------|------|
| Narration | Piper TTS | $0.00 |
| Music | Google Music | $0.03 |
| Mixing | AudioMixer | $0.00 |
| **Total per video** | | **$0.03** |

### Premium Path (All APIs)

| Step | Provider | Cost |
|------|----------|------|
| Narration | ElevenLabs | $0.01 |
| Music | Suno Music | $0.04 |
| Mixing | AudioMixer | $0.00 |
| **Total per video** | | **$0.05** |

---

## Troubleshooting

### Kokoro Not Found

**Problem:** `ModuleNotFoundError: No module named 'kokoro'`

**Solution:**
```bash
pip install kokoro-onnx
# or
pip install git+https://github.com/remixer-dec/kokoro-onnx.git
```

### Piper No Voice Models

**Problem:** `RuntimeError: No voice models found`

**Solution:**
```bash
# Download a voice model
piper --download-dir ~/.piper/models --model en_US-lessac-medium

# Or specify a model directory in execute()
piper_tool.execute({
    "text": "Hello",
    "model_dir": "/path/to/piper/models",
    "output_path": "out.wav"
})
```

### Google Music Not Generating

**Problem:** `API call failed` or `GOOGLE_API_KEY not set`

**Solution:**
1. Check `.env` file has `GOOGLE_API_KEY`
2. Verify key is valid at console.cloud.google.com
3. Enable Generative AI API in Google Cloud Console
4. Fallback to Pixabay: `pip install pixabay` (requires `PIXABAY_API_KEY`)

### Audio Mixing Fails

**Problem:** `ffmpeg not found` or mixing produces silence

**Solution:**
1. Install FFmpeg: `brew install ffmpeg` (macOS) or `apt install ffmpeg` (Linux)
2. Check input files exist: `ls -la audio/`
3. Check file formats: `ffmpeg -i narration.wav` (should show valid codec)

---

## Next Steps: Phase 5

Phase 5 will:
1. **Compose:** Convert script + assets + audio → video timeline
2. **Render:** Generate final MP4 using Remotion or HyperFrames
3. **Publish:** Upload to YouTube with metadata

---

## Testing

Run Phase 4 tests:

```bash
pytest tests/contracts/test_phase4_audio_generation.py -v
```

---

## Configuration Reference

### .env Variables

```bash
# TTS Providers
GOOGLE_API_KEY=...              # Google Texto → Habla (TTS) + Lyria (Music)
OPENAI_API_KEY=...              # OpenAI TTS
ELEVENLABS_API_KEY=...          # ElevenLabs TTS

# Music Providers
SUNO_API_KEY=...                # Suno Music Generation
PIXABAY_API_KEY=...             # Pixabay Stock Music
GOOGLE_API_KEY=...              # Google Music (Lyria)

# Local/Free (no keys needed)
# - Kokoro TTS
# - Piper TTS
# - Music Library (music_library/ folder)
```

---

## Summary

✅ **Phase 4 Complete**

- [x] Kokoro TTS (primary, open-source)
- [x] Piper TTS (fallback, open-source)
- [x] Google/OpenAI/ElevenLabs TTS (cloud options)
- [x] Music Library, Google Music, Suno, Pixabay (music sources)
- [x] Audio Mixer (FFmpeg-based mixing + ducking)
- [x] Orchestrator integration
- [x] Contract tests

**Next:** Phase 5 — Composition & Rendering
