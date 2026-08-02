"""Smoke test script that verifies core imports, config load, mock pipeline run, and artifact creation."""
from src.registry import load_registry
from src.pipeline import create_sample_run
from pathlib import Path
import sys


def run_all():
    # 1. Load registry
    reg = load_registry().data
    print("Registry roles:", list(reg.keys()))

    # 2. Run a mock pipeline
    summary = create_sample_run()
    final = summary.get("final")
    if not final:
        print("Smoke test failed: no final artifact in summary")
        return 2
    # check files exist
    import os
    final_path = final.get("final") if isinstance(final, dict) else final
    if not final_path:
        # try standard location
        final_path = "projects/sample-project/renders/final.mp4"
    if not Path(final_path).exists():
        print("Smoke test failed: final artifact missing at", final_path)
        return 3
    print("Smoke test passed. Created:", final_path)
    return 0


if __name__ == "__main__":
    sys.exit(run_all())
