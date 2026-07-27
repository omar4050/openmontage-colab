# OpenMontage Production System Setup

This guide walks you through setting up the **$0-marginal-cost YouTube video production system**.

## Overview

Your production system consists of:

1. **Research Engine** (`tools/research_engine.py`) — Automated research via Gemini, TMDB, TVMaze, Internet Archive
2. **Script Generator** (`tools/script_generator.py`) — Retention-optimized script generation via Gemini
3. **Orchestrator** (`orchestrate.py`) — Coordinates the full pipeline
4. **Configuration** (`tools/production_config.py`) — Centralized API keys and production parameters

This setup is designed to:
- Run research + scripting completely for ~$0.002 per video (free tier Gemini API)
- Cache everything to avoid re-fetching
- Scale to 3+ videos per week with minimal human intervention
- Remain fully open-source and vendor-neutral

---

## Installation

### 1. Install Dependencies

```bash
# Create/activate virtual environment
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install OpenMontage core
make install

# Install production tools
pip install python-dotenv google-genai aiohttp
```

### 2. Configure API Keys

Copy the example `.env` file and add your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```
# REQUIRED (free tier):
GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE

# OPTIONAL (free tier):
TMDB_API_KEY=YOUR_TMDB_KEY_HERE
PEXELS_API_KEY=YOUR_PEXELS_KEY_HERE
PIXABAY_API_KEY=YOUR_PIXABAY_KEY_HERE
YOUTUBE_API_KEY=YOUR_YOUTUBE_API_KEY_HERE
```

#### Getting Free API Keys

**Gemini API (Required)**
- Go to https://aistudio.google.com/apikey
- Click "Create API key"
- Copy the key to `.env` as `GEMINI_API_KEY`
- Free tier: 60 requests/minute = unlimited for your use case

**TMDB API (Recommended for movie analysis)**
- Register at https://www.themoviedb.org/settings/api
- Copy your API key to `.env` as `TMDB_API_KEY`
- Free tier: 40 requests/10s

**Pexels & Pixabay APIs (For stock media)**
- Pexels: https://www.pexels.com/api/ (click "Generate API Key")
- Pixabay: https://pixabay.com/api/docs/ (register, get key)
- Both free tier: 100-200 requests/day

**YouTube API (For future publishing automation)**
- Go to https://console.cloud.google.com/
- Create a new project
- Enable YouTube Data API v3
- Create OAuth 2.0 credentials (Desktop application)
- Save the JSON file locally and reference it in `.env`

---

## Quick Start: Produce Your First Video

### Option A: Single Video (Recommended for first test)

```bash
# Activate virtual environment first
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate  # Windows

# Produce a single video from topic to script
python orchestrate.py \
  --title "Oppenheimer: How One Film Changed Cinema" \
  --topic "Christopher Nolan's Oppenheimer - filmmaking analysis" \
  --type educational \
  --duration 600
```

This will:
1. Research the topic (using Gemini + TMDB)
2. Generate a retention-optimized script
3. Output to `production_output/scripts/`
4. Show you the retention score and word count

**Expected output:**
```
✓ Script generated: 1200 words, 480s, retention score 78.5/100
Outputs:
  research: production_output/cache/research_20240115_143022.json
  script_json: production_output/scripts/Oppenheimer_20240115_143022.json
  script_voiceover: production_output/scripts/Oppenheimer_voiceover_20240115_143022.txt
```

### Option B: Batch Production

Create a `batch.json` file:

```json
{
  "videos": [
    {
      "title": "Oppenheimer: How Nolan Changed Cinema",
      "topic": "Christopher Nolan's Oppenheimer - filmmaking analysis",
      "type": "analysis",
      "duration": 600
    },
    {
      "title": "AI in 2024: The Year Everything Changed",
      "topic": "AI developments and breakthroughs in 2024",
      "type": "educational",
      "duration": 600
    }
  ]
}
```

Then run:

```bash
python orchestrate.py --batch batch.json
```

---

## System Components Deep Dive

### 1. Research Engine (`tools/research_engine.py`)

**What it does:**
- Researches topics using Gemini
- Fetches movie data from TMDB
- Finds public domain content on Internet Archive
- Caches results to avoid re-fetching

**Cost:** $0.001 per video (Gemini free tier)

**Methods:**
```python
# General research
result = await engine.research_general_topic(
    "AI in healthcare",
    focus_areas=["current trends", "regulations"]
)

# Movie research
movie_data = await engine.research_tmdb_movie("Oppenheimer")

# Public domain content
pd_content = await engine.research_public_domain("WWII", media_type="movies")

# Batch research (all at once)
results = await engine.batch_research({
    "topic_1": {"type": "general"},
    "movie_title": {"type": "tmdb_movie"},
    "pd_search": {"type": "public_domain"}
})
```

### 2. Script Generator (`tools/script_generator.py`)

**What it does:**
- Converts research into professional scripts
- Optimizes for viewer retention (hooks, pacing, pattern interrupts)
- Marks B-roll requirements
- Estimates timing and word count
- Scores retention potential (0-100)

**Cost:** $0.001 per video (Gemini free tier)

**Key features:**
- **Hook optimization:** First 3 seconds are critical
- **Pattern interrupts:** Scene changes every 15-30 seconds
- **Curiosity gaps:** Questions answered within 10 seconds
- **B-roll markers:** Specific visual suggestions at each segment
- **Retention score:** Predicted viewer engagement (0-100)

**Output format:**
```json
{
  "title": "Video title",
  "segments": [
    {
      "type": "hook",
      "voiceover": "First 3 seconds - grab attention...",
      "duration_seconds": 3,
      "suggested_broll": ["opening sequence"],
      "visual_notes": "Eye-catching opener",
      "retention_cue": "What keeps viewers watching"
    },
    // more segments...
  ],
  "call_to_action": "Subscribe for more...",
  "retention_score": 78.5
}
```

### 3. Orchestrator (`orchestrate.py`)

**What it does:**
- Coordinates research → script pipeline
- Handles parallelization
- Tracks costs
- Exports outputs for next phases

**Usage:**
```bash
# Single video
python orchestrate.py --title "..." --topic "..."

# Batch
python orchestrate.py --batch videos.json

# Skip phases (useful for testing)
python orchestrate.py --title "..." --skip-research  # Only generate script from existing research
python orchestrate.py --title "..." --skip-script    # Only do research
```

### 4. Production Config (`tools/production_config.py`)

**What it does:**
- Centralized API credential management
- Production parameters (duration, resolution, budget)
- Output directory structure
- Cost tracking settings

**Key configuration:**
```python
from tools.production_config import config, credentials

# Check what's configured
print(credentials.validate())
# Output: {'gemini': True, 'tmdb': True, 'youtube': False, ...}

# Access settings
print(config.TARGET_VIDEO_LENGTH_SECONDS)  # 600
print(config.MONTHLY_BUDGET_USD)  # 0.0
print(config.AUTO_PUBLISH)  # False (always require manual approval)
```

---

## Output Structure

```
production_output/
├── cache/
│   ├── research/
│   │   ├── abc123.json           # Cached research (keyed by topic hash)
│   │   └── research_20240115.json # Batch research export
│   └── ...
├── scripts/
│   ├── VideoTitle_20240115.json  # Full script with segments
│   ├── VideoTitle_voiceover.txt  # Just the voiceover text (for TTS)
│   └── ...
├── storyboards/                   # (Future: scene-by-scene breakdown)
├── assets/                        # (Future: downloaded B-roll, images, music)
├── compositions/                  # (Future: OpenMontage YAML files)
├── renders/                       # (Future: final MP4 files)
└── metadata/                      # (Future: YouTube titles, descriptions, etc.)
```

---

## Cost Breakdown

| Phase | Tool | Cost/Video | Notes |
|-------|------|-----------|-------|
| Research | Gemini free tier | $0.001 | 60 req/min = unlimited for you |
| Scripting | Gemini free tier | $0.001 | Included in research allowance |
| B-roll metadata | Pexels/Pixabay APIs | $0.000 | Free tier unlimited |
| Voice (future) | Google Cloud TTS | $0.016 | Or use free Piper locally |
| Music (future) | YouTube Audio Library | $0.000 | 8,000+ tracks, fully licensed |
| Rendering (future) | Local CPU | $0.000 | 2-4x realtime on modern CPU |
| Publishing (future) | YouTube API | $0.000 | Free tier |
| **Total** | | **$0.002** | ~$0 at scale |

---

## Next Phases (Coming Soon)

### Phase 2: Asset Collection
- Automatically fetch B-roll from Pixabay/Pexels
- Organize by scene/type
- Generate asset manifest for editing

### Phase 3: Voice & Audio
- Generate voiceovers via Google Cloud TTS (local Piper as free alternative)
- Select music from YouTube Audio Library
- Add sound effects

### Phase 4: Composition
- Convert script → OpenMontage YAML composition
- Auto-place B-roll and music
- Generate captions via Whisper

### Phase 5: Rendering & Publishing
- Render via HyperFrames (local, deterministic)
- Generate YouTube metadata (title, description, tags, chapters)
- Auto-upload (with human review gate)

---

## Troubleshooting

### "GEMINI_API_KEY not configured"
- Check `.env` file exists and has `GEMINI_API_KEY=...`
- Verify key is valid at https://aistudio.google.com/apikey
- Restart orchestrator after editing `.env`

### "JSON parse error"
- Gemini response may have formatting issues
- Check internet connection
- Try running again (API may have rate-limited temporarily)

### "Cannot import tools"
- Ensure you're in the `.venv` virtual environment
- Run `pip install -r requirements.txt` again

### "Research taking too long"
- Gemini free tier is rate-limited to 60 req/min
- For batch research, use `PARALLEL_RESEARCH_WORKERS` setting (default: 4)
- Results are cached, so re-running won't re-fetch

---

## Performance Tips

### To speed up research:
```bash
# Only generate script (skip research if you already have research data)
python orchestrate.py --title "..." --skip-research
```

### To cache better:
- Research results are automatically cached by topic
- Re-running with same topic uses cache (instant)
- Clear cache with: `rm production_output/cache/research/*`

### To batch multiple videos:
- Create `batch.json` with all videos
- Run once: `python orchestrate.py --batch batch.json`
- All research and scripts run in parallel

---

## What's Next?

1. **Run your first video** (see Quick Start above)
2. **Review the outputs** — Check retention score, script quality
3. **Set up next phase** — Asset collection (coming soon)
4. **Iterate on topics** — Find what works best

Once you're comfortable with research + scripting, we'll add:
- TTS voice generation
- B-roll asset collection  
- Automatic composition
- Rendering
- Publishing

---

## Architecture Diagram

```
User Request (topic + title)
          ↓
    Orchestrator
          ↓
   ┌──────────┴──────────┐
   ↓                     ↓
Research Engine    Script Generator
   ↓                     ↓
TMDB/Gemini/IA    Gemini (retention opt)
   ↓                     ↓
Cache (JSON)          Cache (JSON)
   ↓                     ↓
┌──────────────────────────────┐
│ Production Output            │
│ - research_*.json            │
│ - script_*.json              │
│ - voiceover_*.txt            │
└──────────────────────────────┘
         ↓
    (Next phases)
    Asset Collector
    Voice Generator
    Composer
    Renderer
    Publisher
```

---

## Questions?

- Review tool docstrings: `python -c "import tools.research_engine; help(tools.research_engine.ResearchEngine)"`
- Check logs: All operations logged to console
- Inspect outputs: JSON files in `production_output/` are human-readable

---

**Ready to build?** Run your first video:

```bash
python orchestrate.py --title "Your video title" --topic "Your topic"
```

