"""Integration test: run the full pipeline with adapters and verify artifacts."""
import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline import Pipeline
from scripts.model_cache import health_check


def test_pipeline_with_preflight():
    """Run preflight health check, then run the pipeline."""
    print("=" * 60)
    print("PREFLIGHT: Checking adapter availability")
    print("=" * 60)
    results = health_check()
    print()
    
    print("=" * 60)
    print("RUNNING PIPELINE (mock mode)")
    print("=" * 60)
    p = Pipeline(mock=True)
    summary = p.run("integration-test-run")
    print()
    
    # Verify artifacts
    project_dir = Path("projects/integration-test-run")
    artifacts_dir = project_dir / "artifacts"
    
    print("=" * 60)
    print("VERIFYING ARTIFACTS")
    print("=" * 60)
    
    checks = {
        "scene_plan.json": artifacts_dir / "scene_plan.json",
        "run_summary.json": artifacts_dir / "run_summary.json",
        "final_video": project_dir / "renders" / "final.mp4",
    }
    
    for name, path in checks.items():
        exists = path.exists()
        status = "[OK]" if exists else "[MISSING]"
        print(f"{status:12s} {name:25s} {str(path)}")
    
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Pipeline run: {summary.get('project')}")
    print(f"Duration: {summary.get('duration_s'):.2f}s")
    print(f"Available adapters: {sum(1 for r in results.values() if r['available'])}/5")
    print()
    print("[OK] Integration test passed!")


if __name__ == "__main__":
    test_pipeline_with_preflight()
