"""Colab-friendly runner: installs checks are run manually in notebook; this script runs a GPU-aware pipeline run.

Usage:
  python scripts/colab_run.py --project colab-run --benchmark
"""
import argparse
import json
from pathlib import Path
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default="colab-run")
    parser.add_argument("--benchmark", action="store_true")
    args = parser.parse_args()

    # Ensure src is importable
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from src.registry import load_registry
    from scripts.model_cache import health_check
    from src.pipeline import Pipeline

    print("Loading registry...")
    reg = load_registry().data
    print("Roles:", list(reg.keys()))

    print("Running preflight health check...")
    results = health_check()
    available = sum(1 for r in results.values() if r.get("available"))
    print(f"Adapters available: {available}/{len(results)}")

    print("Running pipeline with real adapters (mock=False). This may use GPU and download models.")
    start = time.perf_counter()
    p = Pipeline(mock=False)
    summary = p.run(args.project)
    duration = time.perf_counter() - start
    print(f"Pipeline finished in {duration:.2f}s")

    out = Path(args.project) / "artifacts" / "run_summary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        json.dump(summary, f, indent=2)
    print("Wrote run summary to:", out)

    if args.benchmark:
        print("Running benchmark (mock=False). This may take long depending on models.")
        try:
            from scripts.benchmark import run_benchmark
            # run_benchmark accepts mock flag; outputs written under outputs/benchmarks/
            run_benchmark(mock=False)
        except Exception as e:
            print("Benchmark failed:", e)


if __name__ == '__main__':
    main()
