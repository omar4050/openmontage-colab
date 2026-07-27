# Phase 5: Composition & Rendering

**Status**: ✅ MVP Complete (Phase 4 integration point)

Converts script + assets + audio into rendered video. Orchestrates composition engine (Remotion or HyperFrames) and rendering to MP4.

## Overview

Phase 5 takes the outputs from Phases 1-4 and creates the final video:

```
Script + Assets + Audio → Composition Timeline → Rendered MP4
                            (Remotion or HyperFrames)
```

### Two Composition Runtimes (HARD RULE)

Per AGENT_GUIDE.md, **both runtimes must be presented to user before choice is locked**:

#### **Remotion** (React-based)
- **Best for**: Explainers, educational content, batch production, quick turnaround
- **Strengths**:
  - Stock components (text cards, stat cards, bar charts, comparisons)
  - Spring physics animations
  - Word-level caption burn-in
  - Avatar support (TalkingHead)
  - Proven for commercial production
  - Fast batch rendering
- **Weaknesses**:
  - Limited visual novelty when using templated components
  - Requires Node.js
  - Longer render times for complex scenes
- **Cost**: Free (open-source)
- **Install**: `npm install remotion`

#### **HyperFrames** (HTML/CSS/GSAP)
- **Best for**: Branded content, typography-heavy videos, website demos, launch reels
- **Strengths**:
  - Registry-block driven scene system
  - Kinetic typography effects
  - Website-to-video capability
  - Product promo templates
  - Launch reel templates
  - SVG character rigs
  - Faster local rendering
- **Weaknesses**:
  - Newer (less battle-tested in production)
  - Requires Node.js ≥ 22
  - Registry blocks require initial setup
- **Cost**: Free (open-source)
- **Install**: `npm install hyperframes`

### Two Authoring Modes

#### **Templated Mode** (Default)
- **What it is**: Assemble stock scene-types (text_card, stat_card, bar_chart, etc.) into composition
- **Speed**: Fast assembly (5-15 min)
- **Reliability**: Proven, consistent output
- **Best for**: Internal clips, quick drafts, batch production, localization variants
- **Visual distinctiveness**: Low (many videos share same look)

#### **Atelier Mode** (Hand-Authored)
- **What it is**: Bespoke composition from scratch, no component reuse
- **Speed**: Slower (1-2 hours per video)
- **Creativity**: Full control, unique visual language per video
- **Best for**: Hero work, marketing launches, brand pieces, single-deliverable explainers
- **Visual distinctiveness**: High (every video has unique motion/design)
- **Note**: Default to atelier for work that must impress; use templated for batch/internal only

## Architecture

### CompositionDirector Tool

Located in `tools/composition_director.py`. Handles both composition creation and rendering.

```python
from tools.composition_director import CompositionDirector

director = CompositionDirector()

# Show both runtimes (HARD RULE - user chooses)
options = director.execute({"operation": "preset_options"})

# Create composition timeline
compose_result = director.execute({
    "operation": "compose",
    "runtime": "remotion",  # or "hyperframes"
    "mode": "templated",    # or "atelier"
    "script_path": "script.json",
    "asset_manifest_path": "assets.json",
    "audio_path": "audio_mix.wav",
    "output_dir": "output/",
    "duration_seconds": 60
})

# Render to MP4
render_result = director.execute({
    "operation": "render",
    "composition_file": compose_result.data["composition_file"],
    "output_path": "final_video.mp4"
})
```

### Orchestrator Integration

Phase 5 is integrated into `orchestrate.py`:

```bash
# Single video with Remotion + templated (default)
python orchestrate.py --title "My Video" --topic "AI" \
    --composition-runtime remotion --composition-mode templated

# Or with HyperFrames + atelier for hero work
python orchestrate.py --title "Brand Launch" --topic "Product" \
    --composition-runtime hyperframes --composition-mode atelier

# Skip Phase 5 (just get through Phase 4)
python orchestrate.py --title "Test" --topic "Test" --skip-composition
```

## Scene Planning

Phase 5 builds a scene plan from script segments:

```json
{
  "scenes": [
    {
      "id": "scene_0",
      "type": "text_card",
      "duration": 5.0,
      "start_time": 0.0,
      "text": "Segment narration",
      "assets": ["asset1.jpg", "asset2.jpg"],
      "transitions": "fade"
    },
    {
      "id": "scene_1",
      "type": "bar_chart",
      "duration": 5.0,
      "start_time": 5.0,
      "text": "Next narration",
      "assets": [],
      "transitions": "slide_left"
    }
  ]
}
```

### Stock Scene Types (Templated Mode)

Available in Remotion:
- `text_card` — Title/text with background
- `stat_card` — Large number + label (e.g., "85% faster")
- `bar_chart` — Animated bar chart
- `comparison_card` — Side-by-side comparison
- `video_clip` — Embedded video segment
- `image_with_caption` — Photo + text overlay
- `callout` — Highlighted point with icon
- `transition_slide` — Scene transition (fade, slide, zoom)

## Rendering

### Remotion Rendering Path

```bash
npx remotion render <composition-spec> output.mp4 \
    --resolution 1920x1080 \
    --fps 30 \
    --concurrency 4
```

Outputs: MP4 with H.264 codec, AAC audio, YouTube-compatible format

### HyperFrames Rendering Path

```bash
npx hyperframes render <composition-spec> output.mp4 \
    --resolution 1920x1080 \
    --fps 30
```

Outputs: MP4 with VP9 or H.264, Opus or AAC audio

## Cost Breakdown

**Phase 5 is zero-cost** (all open-source, local rendering):

| Path | Cost | Notes |
|------|------|-------|
| Remotion + templated | $0 | Free, open-source React components |
| HyperFrames + templated | $0 | Free, open-source HTML/CSS/GSAP |
| Atelier mode (either runtime) | $0 | Hand-authored, no external APIs |

Rendering is local (on user's machine), not cloud-based.

## Configuration

### Environment Variables (`.env`)

```bash
# Optional: Render platform (local, AWS Lambda, etc.)
RENDER_PLATFORM=local

# Optional: Rendering concurrency (for Remotion)
RENDER_CONCURRENCY=4

# Optional: Output format
OUTPUT_CODEC=h264  # h264, vp9, av1
OUTPUT_BITRATE=5000k
```

### Composition Config

In code:

```python
composition_config = {
    "runtime": "remotion",
    "mode": "templated",
    "resolution": "1920x1080",  # 1920x1080, 1280x720, 3840x2160
    "frame_rate": 30,  # 24, 30, 60
    "duration_seconds": 60,
    "apply_subtitles": True,
    "subtitle_style": "white_outline",
    "apply_color_grading": False
}
```

## Audio-Video Synchronization

Phase 5 receives audio from Phase 4 and synchronizes:

1. **Narration timing**: Divides audio into segments matching script segments
2. **Scene cuts**: Places scene cuts where narration pauses/changes
3. **Music ducking**: Respects audio mix (Phase 4 already ducked music during narration)
4. **Subtitle sync**: Burns subtitles with frame-accurate timing

## Troubleshooting

### "Remotion not found"

**Cause**: Node.js and Remotion not installed

**Fix**:
```bash
# Install Node.js (if needed)
# https://nodejs.org/ (LTS recommended)

# Install Remotion
npm install remotion
npx remotion --version
```

### "HyperFrames not found"

**Cause**: Node.js ≥ 22 and HyperFrames not installed

**Fix**:
```bash
node --version  # Must be >= 22
npm install hyperframes
npx hyperframes info
```

### "Composition file not found"

**Cause**: Phase 5 expecting composition JSON from Phase 5a but file missing

**Fix**:
```bash
# Check orchestrate logs for Phase 5 output
python orchestrate.py --title "Test" --topic "Test" 2>&1 | grep "composition"

# Verify script and assets exist before Phase 5
ls production_output/scripts/
ls production_output/manifests/
```

### "Rendering is slow"

**Cause**: Using defaults or large resolution

**Solutions**:
```bash
# For testing: use lower resolution
python orchestrate.py ... --composition-resolution 1280x720

# For production: use rendering concurrency (Remotion only)
RENDER_CONCURRENCY=8 python orchestrate.py ...

# Consider using HyperFrames (faster local rendering than Remotion)
python orchestrate.py ... --composition-runtime hyperframes
```

### Audio out of sync with video

**Cause**: Scene timing doesn't match narration duration

**Fix**:
- Verify audio duration matches script
- Check Phase 4 output: `production_output/audio/final_mix.wav`
- Re-run Phase 5 with explicit `--duration` matching audio length

## Metrics & Performance

### Composition Generation Speed
- Templated: 1-3 seconds (scene plan only)
- Atelier: Depends on hand-authoring time (no auto measurement)

### Rendering Speed (Local)
- Remotion: 2-5 minutes for 60s video (1080p, 30fps)
- HyperFrames: 1-2 minutes for 60s video (1080p, 30fps)
- HyperFrames is 2-3x faster due to direct HTML/CSS rendering vs React compilation

### Output Quality
- Resolution: Up to 4K (3840x2160) with both runtimes
- Frame rate: 24fps (cinema), 30fps (standard), 60fps (smooth motion)
- Bitrate: 5000-8000 kbps (YouTube-compatible)
- Audio: 192 kbps AAC (or Opus for HyperFrames)

## Examples

### Example 1: Educational Video (Remotion + Templated)

```bash
python orchestrate.py \
    --title "Machine Learning Basics" \
    --topic "ML" \
    --type educational \
    --composition-runtime remotion \
    --composition-mode templated
```

Produces: Stock-component-based explainer with text cards, stat cards, charts

### Example 2: Product Launch (HyperFrames + Atelier)

```bash
python orchestrate.py \
    --title "Our New AI Assistant" \
    --topic "Product Launch" \
    --type marketing \
    --composition-runtime hyperframes \
    --composition-mode atelier
```

Produces: Custom-designed launch video with unique motion and branding

### Example 3: Test Run (Skip Rendering)

```bash
python orchestrate.py \
    --title "Test" \
    --topic "Quick test" \
    --skip-composition
```

Produces: Outputs through Phase 4, skips rendering

## Next Steps

After Phase 5:

1. **Subtitles (Phase 5b)**: Burn word-level captions from Phase 4 audio timing
2. **Color grading (Phase 5c)**: Apply LUTs, curves, grades for brand consistency
3. **Publishing (Phase 6)**: Upload to YouTube, generate metadata, track views
4. **Analytics**: Track completion rate, engagement, CTR

## Decision Log

### Runtime Selection Rule (HARD RULE per AGENT_GUIDE.md)

When a user asks to build Phase 5:

1. **Always show both runtimes first** (preset_options)
2. **Let user choose** (or suggest based on use case)
3. **Lock choice** and proceed with chosen runtime
4. Never silently pick one without asking

### Authoring Mode Recommendation

- **Default to templated** for: Batch videos, internal content, quick turnaround
- **Recommend atelier** for: Marketing, launches, brand pieces, hero work
- **Require explicit approval** before starting atelier (more tokens, more time)

## Testing

Run Phase 5 contract tests:

```bash
pytest tests/contracts/test_phase5_composition_rendering.py -v
```

Tests verify:
- Both runtimes are presented (HARD RULE check)
- Composition creation works
- Scene planning is correct
- Rendering is queued (actual render requires Node.js + npm)
- Error handling is robust

## References

- **Remotion Docs**: https://remotion.dev/docs
- **HyperFrames Docs**: https://github.com/tweag/hyperframes
- **AGENT_GUIDE.md**: Composition runtime rules and authoring modes
- **QUICK_REFERENCE.md**: Runtime/mode decision matrix
