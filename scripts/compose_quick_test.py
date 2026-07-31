#!/usr/bin/env python3
"""Compose and attempt render for Quick Test using CompositionDirector."""
import sys
import json
from pathlib import Path
# Ensure repository root is on sys.path so `tools` can be imported when running scripts
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.composition_director import CompositionDirector

script_path = Path("production_output/scripts/quick_test_script.json")
audio_path = Path("production_output/audio/quick_test_narration.wav")
output_dir = Path("production_output/composition")
output_dir.mkdir(parents=True, exist_ok=True)

director = CompositionDirector()

print("Composing...")
compose_result = director.execute({
    "operation": "compose",
    "runtime": "remotion",
    "mode": "templated",
    "script_path": str(script_path),
    "asset_manifest_path": "",
    "audio_path": str(audio_path),
    "output_dir": str(output_dir),
    "duration_seconds": 15,
    "resolution": "1920x1080",
    "frame_rate": 30
})

print("Compose result:", compose_result.success)
if compose_result.success:
    comp_file = compose_result.data.get("composition_file")
    print("Composition file:", comp_file)
    print("Attempting render (may require Node.js/remotion)...")
    render_result = director.execute({
        "operation": "render",
        "composition_file": comp_file,
        "output_path": str(output_dir / "quick_test_final.mp4")
    })
    print("Render result:", render_result.success)
    if render_result.success:
        print("Video queued/created:", render_result.data.get("output_path"))
    else:
        print("Render error:", render_result.error)
else:
    print("Compose failed:", compose_result.error)

print("Done")
