# Quick Reference — YouTube Video Production System

## 🎬 One-Command Video Production

```bash
# Generate script for a video idea
python orchestrate.py --title "Your Title" --topic "Your Topic"

# Batch produce 3 videos
python orchestrate.py --batch batch.json

# Skip research (faster, if you already have research data)
python orchestrate.py --title "..." --topic "..." --skip-research
```

## 📁 Output Locations

```
production_output/
├── scripts/         ← Your generated scripts (JSON + TXT)
├── cache/           ← Cached research data (don't delete!)
├── assets/          ← (Future) Downloaded B-roll, images
├── compositions/    ← (Future) OpenMontage YAML files
├── renders/         ← (Future) Final MP4 videos
└── metadata/        ← (Future) YouTube titles, descriptions
```

## 🔑 APIs & Their Status

| API | Key Status | Used For | Cost |
|-----|-----------|----------|------|
| Gemini | ✓ In .env | Research + Scripting | $0/video |
| Groq | ✓ In .env | Fallback scripting | $0/video |
| TMDB | ✓ In .env | Movie research | $0/video |
| Pexels | ✓ In .env | Stock footage (next phase) | $0/video |
| Pixabay | ✓ In .env | Stock images (next phase) | $0/video |

## 📊 Script Output Example

The system generates scripts like this:

```json
{
  "title": "Your Video Title",
  "segments": [
    {
      "type": "hook",
      "voiceover": "First 3 seconds of narration...",
      "suggested_broll": ["scene description"],
      "retention_cue": "Why viewers keep watching"
    },
    // ... more segments
  ],
  "retention_score": 82.5  // 0-100
}
```

Each segment has:
- **voiceover** - Exact text for narrator
- **suggested_broll** - Scene/visual descriptions
- **duration_seconds** - How long to show this segment
- **retention_cue** - Hook to keep viewers watching
- **visual_notes** - On-screen graphics, text, effects

## 🏃 Typical Workflow

```
1. Create video topic
   ↓
2. Run orchestrator
   python orchestrate.py --title "..." --topic "..."
   ↓
3. Get script files
   - script_*.json (full metadata)
   - *_voiceover.txt (for text-to-speech)
   ↓
4. (Future) Generate voice
   - Convert voiceover text → MP3
   ↓
5. (Future) Collect assets
   - Download B-roll from Pexels/Pixabay
   - Select music from YouTube library
   ↓
6. (Future) Compose video
   - Create OpenMontage YAML
   - Place assets + timing
   ↓
7. (Future) Render & publish
   - Render to MP4
   - Auto-generate YouTube metadata
   - Upload (with manual review)
```

## 💰 Cost Per Video

| Phase | Cost | Status |
|-------|------|--------|
| Research | $0.001 | ✓ Working |
| Scripting | $0.001 | ✓ Working |
| Voice (future) | $0.016 or $0 | Planned |
| Assets | $0.000 | Planned |
| Music | $0.000 | Planned |
| Rendering | $0.000 | Planned |
| Publishing | $0.000 | Planned |
| **TOTAL** | **$0.002** | Achievable |

**For 3 videos/week:** ~$0.006/week (~$0.02/month) ✓

## 🛠️ Common Tasks

### Generate a single script
```bash
python orchestrate.py \
  --title "Oppenheimer: Filmmaking Analysis" \
  --topic "How Nolan revolutionized cinema" \
  --type analysis
```

### Generate 5 scripts in parallel
```bash
# Create batch.json with 5 videos
python orchestrate.py --batch batch.json
```

### Test without API calls
```bash
# Skip research, use mock data
python orchestrate.py --title "Test" --topic "Test" --skip-research
```

### Review a generated script
```bash
# Open the JSON file
cat production_output/scripts/[filename].json

# Or just the voiceover text
cat production_output/scripts/[filename]_voiceover.txt
```

## 🔍 Troubleshooting

| Problem | Solution |
|---------|----------|
| "GEMINI_API_KEY not configured" | Check `.env` file has your key |
| "Gemini rate-limited" | Groq fallback activates automatically |
| "Groq model not found" | Groq deprecates models; update `tools/script_generator.py` |
| "TMDB API error" | Check your TMDB key in `.env` |
| "Production output not created" | Directory auto-creates; check permissions |

## 📈 Next Features (Roadmap)

- [x] Research engine
- [x] Script generator
- [ ] Asset collector (Pexels/Pixabay download)
- [ ] Voice generation (Google Cloud TTS)
- [ ] Music selector (YouTube Audio Library)
- [ ] Caption generator (Whisper)
- [ ] Composition builder (OpenMontage YAML)
- [ ] Rendering orchestrator (HyperFrames)
- [ ] YouTube publisher (Auto-upload)

## 🎯 Success Metrics

Your system is working when:

1. ✓ `orchestrate.py` runs without errors
2. ✓ Script files appear in `production_output/scripts/`
3. ✓ JSON includes all segments with voiceover text
4. ✓ Retention score is 70+ (out of 100)
5. ✓ Word count is 1000-1500 for ~10 min video
6. ✓ B-roll suggestions are specific and actionable

## 📞 Quick Links

- **Setup Guide:** `PRODUCTION_SETUP.md`
- **Full Summary:** `IMPLEMENTATION_SUMMARY.md`
- **Tool Details:** See docstrings in `tools/*.py`
- **Example Script:** `production_output/scripts/Oppenheimer_sample_script.json`

## 🚀 Right Now You Can:

```bash
# 1. Generate scripts in bulk
python orchestrate.py --batch my_videos.json

# 2. Review generated scripts
ls production_output/scripts/

# 3. Extract voiceover for narration
cat production_output/scripts/*_voiceover.txt

# 4. Check retention scores
grep retention_score production_output/scripts/*.json
```

---

**Your $0-marginal-cost YouTube production system is ready. Let's build!** 🎬

