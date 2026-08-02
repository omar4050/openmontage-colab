Local-first, GPU-ready notes

This repo snapshot includes a compact, local-first modular pipeline skeleton intended for quick local development and benchmarking.

Key files added by the refactor:

- configs/models.yaml — single source of truth for model choices (primary/fallback/mock)
- src/registry.py — loads the model registry
- src/selector.py — lightweight model selector (GPU-aware)
- src/abstractions.py — component interfaces (Planner, Transcriber, ...)
- src/mock.py — fast mock implementations for development
- src/pipeline.py — a simple orchestrator that runs the pipeline in mock mode
- scripts/benchmark.py — runs quick benchmarks across registry entries (mock by default)
- scripts/smoke_test.py — fast smoke test that creates a sample project and artifacts
- tests/test_smoke.py — pytest-compatible smoke test for CI

Quick start (local-first):

- Setup virtualenv & deps (cross-platform):
  - make setup

- Run smoke test:
  - python scripts/smoke_test.py
  - or make test (runs pytest tests/)

- Run benchmark (fast mock):
  - python scripts/benchmark.py --mock

Mock mode:
- All components support mock implementations. Use mock for development on laptops without GPUs.

GPU mode:
- The selector will prefer primary models when torch.cuda is available. Real model integrations should be plugged into the abstractions and registered in configs/models.yaml.

License note:
- This refactor prefers local and open-source models by default. Cloud providers may be enabled via .env and per-run decisions.
