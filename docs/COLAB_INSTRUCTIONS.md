Google Colab GPU setup instructions for OpenMontage

Overview
--------
This guide prepares a Colab notebook environment to run OpenMontage with GPU-accelerated models where available. It installs system dependencies, GPU builds of PyTorch, and key ML/media packages, then runs a GPU-aware pipeline and optional benchmark.

Open in Colab
--------------
1. Open a new Colab notebook: https://colab.research.google.com/
2. Set Runtime > Change runtime type > GPU (e.g., NVIDIA T4, A100 if available)

Notebook cells
--------------
Copy each block into a separate code cell in Colab and run in order.

Cell 1 — system packages
```bash
# Install system dependencies
!apt-get update -qq
!apt-get install -y -qq ffmpeg libsndfile1 git-lfs
```

Cell 2 — clone repo
```python
# Provide the GitHub repository URL when prompted, or set REPO_URL below.
# Example: https://github.com/<your-github-username>/OpenMontage.git
REPO_URL = input("Enter the GitHub repo URL (or press Enter to use a default placeholder): ")
if not REPO_URL:
    REPO_URL = "https://github.com/<your-github-username>/OpenMontage.git"  # replace when you push

# Clone the repo into /content/openmontage if not already present
import os
if not os.path.exists('/content/openmontage'):
    !git clone {REPO_URL} /content/openmontage
%cd /content/openmontage
```

Cell 3 — Python & CUDA packages
```bash
# Upgrade pip
!python -m pip install -q --upgrade pip

# Install CUDA-compatible PyTorch for Colab (adjust if colab has newer CUDA)
!python -m pip install -q torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# ML/media packages
!python -m pip install -q faster-whisper diffusers transformers accelerate safetensors ffmpeg-python moviepy librosa scipy huggingface_hub
```

Cell 4 — optional: xformers / bitsandbytes (for faster diffusion/quant)
```bash
# Optional - may speed up diffusion but can be tricky to install
# !python -m pip install -q xformers bitsandbytes
```

Cell 5 — run a preflight and pipeline
```bash
# Run health check and a pipeline run (may download models)
!python scripts/colab_run.py --project colab-run --benchmark
```

Output & artifacts
------------------
- Artifacts will be written to `projects/<project>/` (e.g., `projects/colab-run/`)
- Benchmarks (if run) will be in `outputs/benchmarks/`.
- Final video: `projects/<project>/renders/final.mp4`

Troubleshooting
---------------
- If a model is missing or an adapter fails, the pipeline will fallback to mock implementations. Check `FINALIZATION_REPORT.json` and the console logs.
- For GPU memory errors, try smaller models or switch to CPU-only variants by editing `configs/models.yaml`.

Notes
-----
- This repo uses a model registry (`configs/models.yaml`) as the single source of truth.
- Some adapters (Qwen3, Wan, CosyVoice) rely on external SDKs not available by default and will use fallbacks.
- Use Colab Pro for more VRAM and faster runs.

"