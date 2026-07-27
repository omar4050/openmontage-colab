# OpenMontage Quick Launch Guide

## 🚀 Quick Start (30 seconds)

```bash
cd "C:\Users\hp\Desktop\New Folder\OpenMontage-main"
python orchestrate.py --title "Your Title" --topic "Your Topic"
```

That's it! The orchestrator will:
1. Research the topic
2. Generate a script
3. Find images/videos
4. Create narration + music
5. Compose and render video

**Output**: `production_output/composition/final_video.mp4`

---

## 📋 Common Examples

### Educational Video (Default)
```bash
python orchestrate.py \
    --title "Machine Learning Basics" \
    --topic "machine learning" \
    --type educational
```
**Result**: Stock-component educational video with text cards, charts, stats

### Product Launch (Branded)
```bash
python orchestrate.py \
    --title "Our New AI Assistant" \
    --topic "product launch" \
    --type marketing \
    --composition-runtime hyperframes \
    --composition-mode atelier
```
**Result**: Unique branded video (requires hand-authored composition code)

### Quick Test (No Research)
```bash
python orchestrate.py \
    --title "Quick Test" \
    --topic "test" \
    --skip-research \
    --skip-assets
```
**Result**: Fast test run (skips slow phases)

### Batch Production
```bash
python orchestrate.py --batch videos.json
```

**videos.json** format:
```json
{
  "videos": [
    {"title": "Video 1", "topic": "AI", "type": "educational"},
    {"title": "Video 2", "topic": "ML", "type": "educational"}
  ]
}
```

---

## ⚙️ All CLI Options

```bash
# Video details (required in single mode)
--title "Video Title"              # Title of the video
--topic "Main Topic"               # Main topic to research
--type educational                 # Type: educational, marketing, entertainment, explainer

# Duration (in milliseconds)
--duration 60000                   # Default: 60 seconds (1 minute)
--duration 300000                  # 5 minutes
--duration 600000                  # 10 minutes

# Skip phases (for faster testing)
--skip-research                    # Skip Phase 1: Research
--skip-script                      # Skip Phase 2: Script generation
--skip-assets                      # Skip Phase 3: Asset collection
--skip-audio                       # Skip Phase 4: Audio generation
--skip-composition                 # Skip Phase 5: Composition & rendering

# Composition runtime (HARD RULE: both shown)
--composition-runtime remotion     # React-based (default, fastest)
--composition-runtime hyperframes  # HTML/GSAP (good for branded)

# Authoring mode
--composition-mode templated       # Stock components (default, fast)
--composition-mode atelier         # Hand-authored (more creative, slower)

# Batch mode
--batch videos.json                # Process multiple videos from JSON

# Output directory (optional)
--output-dir C:/output/            # Custom output directory
```

---

## 📁 Output Structure

After running, check `production_output/`:

```
production_output/
├── research/
│   └── research_export.json              # Phase 1 research data
│
├── scripts/
│   ├── *_script.json                     # Phase 2 full script
│   └── *_voiceover.txt                   # Phase 2 narration text
│
├── assets/
│   ├── manifests/
│   │   └── *_asset_manifest.json         # Phase 3 asset listing
│   ├── images/                           # Downloaded images
│   └── videos/                           # Downloaded video clips
│
├── audio/
│   ├── narration_kokoro.wav              # Phase 4a TTS narration
│   ├── music.mp3                         # Phase 4b background music
│   └── final_mix.wav                     # Phase 4c mixed audio
│
└── composition/
    ├── composition_remotion_templated.json   # Phase 5a composition spec
    └── final_video.mp4                      # ← FINAL VIDEO (Phase 5b)
```

---

## 🎬 Phase Breakdown

### Phase 1: Research (10-30 seconds)
- Gathers facts about your topic
- Uses Gemini API + web search
- **Cost**: $0.01-0.05
- **Can skip with**: `--skip-research`

### Phase 2: Script (10-20 seconds)
- Creates narrative structure
- Adds hooks, calls-to-action
- Splits into segments
- **Cost**: $0.01-0.05
- **Can skip with**: `--skip-script`

### Phase 3: Assets (20-60 seconds)
- Finds images from Pexels/Pixabay (free)
- Finds videos from multiple sources
- Maps assets to script segments
- **Cost**: $0-0.50 (if using paid stock)
- **Can skip with**: `--skip-assets`

### Phase 4: Audio (10-60 seconds)
- **4a**: Generates narration via Kokoro TTS (free, offline)
- **4b**: Selects background music (library or Pixabay)
- **4c**: Mixes narration + music with ducking
- **Cost**: $0 (all free providers)
- **Can skip with**: `--skip-audio`

### Phase 5: Composition (60-300 seconds)
- **5a**: Builds scene timeline from script
- **5b**: Renders to MP4 via Remotion or HyperFrames
- **Cost**: $0 (local rendering)
- **Can skip with**: `--skip-composition`

---

## 🔧 Troubleshooting

### "Missing required APIs"
**Error**: `❌ Missing required APIs: [gemini]`

**Fix**: Add API key to `.env` file:
```bash
GEMINI_API_KEY=your_key_here
```

Get a free Gemini API key: https://makersuite.google.com/app/apikey

---

### "Module not found"
**Error**: `ModuleNotFoundError: No module named 'kokoro'`

**Fix**: Install Kokoro TTS
```bash
pip install kokoro-onnx
```

Or use fallback: `--skip-audio` and it will skip narration generation

---

### "Node.js not found" (at rendering)
**Error**: `Remotion not found. Install with: npm install remotion`

**Fix**: Install Node.js and Remotion
```bash
# Install Node.js from https://nodejs.org/ (LTS)
npm install remotion
```

Or skip rendering for now: `--skip-composition`

---

### Video is taking too long
**Slow phases**:
- Phase 1 (Research) — API calls are slow
- Phase 3 (Assets) — Downloads are slow
- Phase 5 (Composition) — Rendering takes time

**Fast test**:
```bash
python orchestrate.py --title "Test" --topic "test" \
    --skip-research --skip-assets --duration 30000
```

---

## 💰 Cost Tracking

**Zero-cost path** (all open-source):
- Gemini (free tier)
- Pexels/Pixabay (free media)
- Kokoro TTS (free, offline)
- Remotion (free, open-source)
- **Total**: $0/video

**Minimal-cost path** ($0.03-0.05/video):
- Add Google Music generation
- Everything else stays free

**Premium path** ($0.50-2.00/video):
- OpenAI/ElevenLabs for TTS
- iStock for premium images
- Suno for music generation

---

## 📊 Real Example Output

Running:
```bash
python orchestrate.py --title "AI Trends 2024" --topic "AI trends"
```

Expected output:
```
✓ APIs configured: gemini, grok, tmdb, pixabay, pexels
🚀 STARTING PRODUCTION: AI Trends 2024
==============================================================

📚 PHASE 1: RESEARCH
----------------------------------------------------------------------
✓ Research complete. Cost: $0.0234

✍️  PHASE 2: SCRIPT GENERATION
----------------------------------------------------------------------
✓ Script generated:
  Duration: 72.3s (1.2m)
  Words: 245
  Retention score: 87.5/100
  Cost: $0.0156

🎬 PHASE 3: ASSET COLLECTION
----------------------------------------------------------------------
✓ Assets collected:
  Total assets: 18
  By segment: 5
  Cost: $0.0000

🎤 PHASE 4: VOICE & AUDIO GENERATION
----------------------------------------------------------------------
📢 Generating narration via TTS...
  Trying Kokoro TTS (open-source, free)...
✓ Narration generated with Kokoro: narration_kokoro.wav
🎵 Selecting background music...
✓ Using music from library: ambient_bg.mp3
🔊 Mixing narration + music...
✓ Audio mix complete: final_mix.wav
✓ Phase 4 complete. Cost: $0.0000

🎬 PHASE 5: COMPOSITION & RENDERING
----------------------------------------------------------------------
📐 Composing with remotion (templated mode)...
✓ Composition created:
  Runtime: remotion
  Mode: templated
  Scenes: 5
🎥 Rendering to MP4...
✓ Video rendered:
  Path: final_video.mp4
  Runtime: remotion

======================================================================
✓ PRODUCTION PHASE COMPLETE
======================================================================
Elapsed time: 187.4s
Total cost: $0.0390

Outputs:
  research: production_output/research/research_export.json
  script_json: production_output/scripts/script.json
  script_voiceover: production_output/scripts/voiceover.txt
  asset_manifest: production_output/manifests/manifest.json
  narration: production_output/audio/narration_kokoro.wav
  music: production_output/audio/music.mp3
  final_audio: production_output/audio/final_mix.wav
  composition: production_output/composition/composition_remotion_templated.json
  video: production_output/composition/final_video.mp4

👉 Final video: production_output/composition/final_video.mp4
```

---

## 📖 Next Steps After Video is Made

1. **Watch the video**
   ```bash
   # Open in default media player
   start production_output/composition/final_video.mp4
   ```

2. **Upload to YouTube** (Phase 6 - coming soon)
   ```bash
   python orchestrate.py ... --publish-youtube
   ```

3. **Fine-tune composition** (Atelier mode)
   ```bash
   python orchestrate.py ... \
       --composition-runtime hyperframes \
       --composition-mode atelier
   ```

4. **Batch produce** (multiple videos)
   ```bash
   python orchestrate.py --batch videos.json
   ```

---

## 📞 Support

- **Docs**: `PHASE_5_COMPOSITION_GUIDE.md` (composition details)
- **Build Summary**: `PHASE_5_BUILD_SUMMARY.md` (technical details)
- **Issues**: Check `.env` configuration and API keys first
