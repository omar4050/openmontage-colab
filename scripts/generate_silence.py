#!/usr/bin/env python3
"""Generate a silent WAV file for quick testing."""
import wave
import struct
from pathlib import Path

out_dir = Path("production_output/audio")
out_dir.mkdir(parents=True, exist_ok=True)

out_path = out_dir / "quick_test_narration.wav"

duration_seconds = 15
framerate = 22050
nframes = duration_seconds * framerate

with wave.open(str(out_path), 'w') as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(framerate)
    silence_frame = struct.pack('<h', 0)
    # Write in chunks for performance
    chunk_size = 1024
    frames_written = 0
    zeros = silence_frame * chunk_size
    while frames_written < nframes:
        to_write = min(chunk_size, nframes - frames_written)
        wf.writeframes(zeros[: to_write * 2])
        frames_written += to_write

print(f"Wrote silent narration to: {out_path}")
