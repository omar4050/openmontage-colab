Local-first Model Stack (OpenMontage)

Overview

This repository now ships a local-first model registry (configs/models.yaml) and:

- adapter loader: src/adapters/adapter_loader.py
- model selector: src/selector.py (profiles: local-first, balanced, quality-first)
- preflight health check: python -m src.health.preflight --profile local-first
- artifact validators: src/validators.py

Default stacks

Planner: qwen3 (default), gemma3-27b-it (premium), deepseek-r1-distill (lightweight)
Transcription: faster-whisper (large-v3), distil-whisper (distil-large-v3.5), seamless-m4t-v2
TTS: kokoro-82m, moss-tts, parler-tts
Image generation: flux.2-klein-4b, qwen-image, flux.2-dev
Video generation: wan2.2-ti2v-5b, ltx-video, hunyuanvideo-1.5
Music: stable-audio-open-small, musicgen, stable-audio-3-medium
Montage & post: ffmpeg, moviepy, remotion; enhancers: real-esrgan, rife

Running the health check

1. python -m src.health.preflight --profile local-first
2. Report written to health_report.json in repo root. The preflight reports:
   - configured
   - adapter found
   - initializable
   - available

Switching profiles

Edit configs/models.yaml `profiles` section and set `policy.profiles_default` or pass --profile to the health check and the selector will use profile preferences.

Validating outputs

Use src/validators.py functions:
- is_valid_image(path)
- is_valid_audio(path)
- is_valid_video(path)

These functions try layered checks (Pillow/ffprobe/moviepy) and return a dict {valid: bool, reason: ...}.

Next steps

- Add adapter implementations for premium models and any missing mappings.
- Add small sample assets for runtime-executable verification (optional).
- Wire preflight output into the UI/pipeline preflight step to present available capabilities to users.
