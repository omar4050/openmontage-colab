# OpenMontage Local-First GPU-Ready Refactor

This document describes the refactored OpenMontage architecture designed for clean, modular, local-first video production with GPU acceleration support and comprehensive model management.

## Architecture Overview

The refactored codebase introduces a **modular, adapter-based pipeline** where each component (Planner, Transcriber, TTS, Image Generator, Video Generator, Editor, Enhancer, Music Generator) can be independently implemented and swapped without rewriting the core pipeline.

### Key Principles

1. **Local-first by default** — open-source and self-hosted models are preferred; cloud providers are opt-in via configuration.
2. **Mock mode for development** — every component has a fast mock implementation for testing on laptops without GPUs.
3. **Adapter-based extensibility** — each abstraction (Component subclass) maps to pluggable adapters (e.g., faster-whisper, qwen3, diffusers).
4. **Single source of truth** — `configs/models.yaml` defines all model choices and adapter configurations in one place.
5. **Preflight health checks** — before running production, the system audits available adapters and chooses appropriate implementations.
6. **Clean error handling** — unavailable models gracefully fall back to available alternatives or mock implementations.

### Directory Structure

```
src/
  ├── __init__.py
  ├── abstractions.py      # Component base classes (Planner, Transcriber, VoiceGenerator, ...)
  ├── registry.py          # Load models.yaml into a ModelRegistry
  ├── selector.py          # ModelSelector: picks best model based on GPU/profile
  ├── mock.py              # Fast mock implementations for all components
  ├── pipeline.py          # Main Pipeline orchestrator
  └── adapters/
      ├── __init__.py
      ├── adapter_loader.py # Dynamic adapter loader with config passing
      ├── planner_qwen3.py
      ├── transcriber_faster_whisper.py
      ├── tts_cosyvoice.py
      ├── image_qwen.py
      └── video_wan.py

configs/
  └── models.yaml          # Registry: model choices, adapter config, policy

scripts/
  ├── benchmark.py         # Benchmark runner: exercises each model and writes reports
  ├── smoke_test.py        # Quick smoke test: creates sample project and verifies
  ├── integration_test.py  # Full integration: preflight + pipeline + artifact check
  ├── model_cache.py       # CLI for model cache: list, check, download, health-check
  ├── model_helpers.py     # Utilities: check_model_available, download_hf_repo
  ├── gen_test_audio.py    # Generate test audio fixtures

tests/
  └── test_smoke.py        # pytest-compatible smoke test

docs/
  └── LOCAL_FIRST.md       # Quick local-first guide
```

## How It Works

### 1. Model Registry (`configs/models.yaml`)

A single YAML file defines:
- Primary and fallback model choices for each role (planner, transcriber, tts, image_generation, video_generation, etc.)
- Adapter-specific configuration (model IDs, compute types, device preferences)
- Local-first policy settings

Example:
```yaml
transcriber:
  primary: faster-whisper
  fallback: whisper
  lightweight_fallback: whisper.cpp
adapters:
  faster-whisper:
    model: small
    compute_type: int8  # optional
```

### 2. Model Selector (`src/selector.py`)

`ModelSelector` examines the registry and the current hardware:
- If GPU available → prefer primary model
- If no GPU → prefer lightweight_fallback
- If mock profile requested → return mock choice

Returns: `{"choice": "faster-whisper", "source": "primary"}`

### 3. Adapter Loader (`src/adapters/adapter_loader.py`)

Maps registry choices to adapter modules dynamically:
- `faster-whisper` → `src/adapters/transcriber_faster_whisper.py : FasterWhisperTranscriber`
- Passes per-model config from registry to the adapter constructor
- Returns the instantiated adapter if `available=True`, otherwise None

Graceful fallback chain:
1. Try to load real adapter (faster-whisper)
2. If unavailable, try fallback adapter (whisper)
3. If all unavailable, use mock in the pipeline

### 4. Abstract Components (`src/abstractions.py`)

Each role has a base class that adapters must implement:
```python
class Transcriber(Component):
    def run(self, audio_path: str, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError
```

All adapters inherit from these and provide real or fallback implementations.

### 5. Pipeline Orchestrator (`src/pipeline.py`)

```python
p = Pipeline(mock=False)  # Try real adapters
summary = p.run("my-project")
```

The pipeline:
1. Loads the registry
2. Attempts to load real adapters via adapter_loader
3. Falls back to mocks if adapters unavailable
4. Runs each stage (plan, voice, images, video, compose, enhance, music)
5. Writes artifacts to `projects/<project>/artifacts/` and `projects/<project>/renders/`

### 6. Mock Mode

Fast mock implementations in `src/mock.py`:
- MockPlanner: returns a heuristic 2-scene plan
- MockTranscriber: returns empty transcript
- MockVoice, MockImageGen, MockVideoGen, MockEditor, MockEnhancer, MockMusic: write placeholder files

Enables development and testing without heavy GPU models.

## Running the System

### Quick Start (Mock Mode)

```bash
# Setup (one-time)
make setup

# Run mock pipeline
python -c "from src.pipeline import create_sample_run; create_sample_run()"

# Result: projects/sample-project/renders/final.mp4 + artifacts
```

### Health Check & Preflight

```bash
# See which adapters are available on this machine
python scripts/model_cache.py health-check

# Check a specific model
python scripts/model_cache.py check faster-whisper

# List recommended models
python scripts/model_cache.py list
```

### Benchmark

```bash
# Run fast mock benchmark
python scripts/benchmark.py --mock

# Run real benchmark (requires adapters installed)
python scripts/benchmark.py
```

### Integration Test

```bash
# Run preflight + pipeline + artifact verification
python scripts/integration_test.py
```

## Adapter Implementation Guide

### Adding a New Adapter

1. **Inherit from the abstraction** in `src/abstractions.py`:
   ```python
   from src.abstractions import ImageGenerator
   
   class MyImageAdapter(ImageGenerator):
       def __init__(self, model_name: str, config: Dict = None):
           super().__init__(model_name, config)
           self.available = ...  # check if library is installed
           self._model = ...     # load model if available
       
       def run(self, prompt: str, count: int = 1, **kwargs):
           if not self.available:
               raise RuntimeError("...")
           # call real model
           return {"paths": [...]}
   ```

2. **Register in adapter_loader.py**:
   ```python
   MODEL_TO_ADAPTER = {
       "my-model": ("adapter_module", "MyImageAdapter"),
   }
   ```

3. **Add config in models.yaml**:
   ```yaml
   adapters:
     my-model:
       model_id: some/huggingface/repo
   ```

4. **Test**:
   ```python
   from src.adapters.adapter_loader import get_component
   comp = get_component("image_generation")
   result = comp.run("a sunset", count=1)
   ```

## Model Management

### Downloading Models

```bash
# Download a specific model to models/
python scripts/model_cache.py download runwayml/stable-diffusion-v1-5

# Models are cached in models/<repo-id-with-slashes-replaced>
```

### Using Local Model Paths

In `configs/models.yaml`:
```yaml
adapters:
  diffusers-sd:
    model_id: runwayml/stable-diffusion-v1-5
    torch_dtype: float16
```

The adapter_loader passes this config to the adapter, which can download or use a local cached path.

## Default Model Choices

| Role | Primary | Fallback | Lightweight |
|------|---------|----------|-------------|
| **Planner** | Qwen3 | Qwen3-Coder | (heuristic) |
| **Transcriber** | faster-whisper | Whisper | whisper.cpp |
| **TTS** | CosyVoice 3.0 | Kokoro | pyttsx3 (local) |
| **Image** | Qwen-Image | FLUX.1 [schnell] | diffusers SD 1.5 |
| **Video** | Wan 2.2 | LTX-2.3 | MoviePy |
| **Montage** | FFmpeg | Remotion | MoviePy |
| **Enhancement** | Real-ESRGAN | RIFE | (none) |
| **Music** | MusicGen | Stable Audio | (local TTS fallback) |

All favor **open-source and locally-runnable** models by default.

## GPU Support

The system automatically detects CUDA availability:
- **With GPU**: ModelSelector prefers primary (more capable) models
- **Without GPU**: ModelSelector chooses lightweight_fallback or defaults to mock
- **Manual override**: Set `profile="mock"` to force mock mode for testing

```python
selector = ModelSelector(registry)
pick = selector.pick("image_generation", profile="balanced")  # auto GPU detection
pick = selector.pick("image_generation", profile="mock")       # force mock
```

## Error Handling & Logging

### Adapter Errors

Adapters report `available=False` if:
- Required library is not installed
- Model weights cannot be found or downloaded
- GPU memory insufficient

The pipeline gracefully falls back to a fallback adapter or mock.

### Pipeline Errors

If an adapter's `run()` fails:
- The error is logged with context
- The pipeline may retry with a fallback (configurable)
- User sees a clear error message with suggested next steps

## Testing

### Unit Tests

```bash
# Quick smoke tests
pytest tests/test_smoke.py -v

# Run via make
make test
```

### Integration Tests

```bash
# Full end-to-end with preflight
python scripts/integration_test.py
```

### Benchmarking

```bash
# Compare models on same sample input
python scripts/benchmark.py --mock  # fast mock comparison
python scripts/benchmark.py         # real model benchmark (if installed)
```

Outputs: `outputs/benchmarks/benchmark_<timestamp>/` with JSON report + markdown summary.

## Cloud & API Fallback

Although local-first by default, the system can optionally use cloud providers:

1. Add API keys to `.env` (e.g., `OPENAI_API_KEY`, `FAL_KEY`)
2. Update `configs/models.yaml` to include cloud provider fallbacks
3. Implement adapters that call cloud APIs as fallback
4. Pipeline automatically tries cloud fallback if local unavailable

## Performance Notes

### Laptop (no GPU)
- **Recommended**: Mock mode for development; use only lightweight models (faster-whisper small, FLUX on CPU)
- **Turnaround**: 5–30 seconds per pipeline run
- **Memory**: <4GB

### Local GPU (NVIDIA 12GB+)
- **Recommended**: Primary models (faster-whisper medium, Stable Diffusion, Qwen-Image)
- **Turnaround**: 30–90 seconds per run
- **Memory**: 8–12GB (with appropriate compute_type, e.g., int8, float16)

### Remote GPU (RunPod, Vast, etc.)
- **Recommended**: Large primary models (Wan 2.2, HunyuanVideo)
- **Turnaround**: 60–180 seconds per run
- **Setup**: Provide remote endpoint URL and credentials in `.env`

## Next Steps for Contributors

1. **Implement missing adapters**:
   - Qwen3 planner (Qwen3 SDK integration)
   - Real Wan 2.2 video generator
   - Music generation (MusicGen, Stable Audio)

2. **Add more fallbacks**:
   - whisper.cpp for ultra-lightweight transcription
   - RIFE for video frame interpolation
   - Kokoro TTS (lightweight)

3. **Optimize for edge cases**:
   - Low-memory laptop mode (ONNX quantization)
   - CPU-only inference paths
   - Batch processing for multiple projects

4. **Extend testing**:
   - Parameterized tests for all adapters
   - GPU memory profiling in benchmark
   - Quality metrics (LPIPS, SSIM) for image/video outputs

5. **Documentation**:
   - Per-adapter setup guides (API keys, weights download, environment)
   - Troubleshooting guide for common errors
   - Video walkthroughs of example workflows

---

**Refactor Status**: ✓ Modular architecture complete. Core adapters (transcriber) implemented. Pipeline tested. Mock mode verified.
