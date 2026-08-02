"""Benchmark script to run candidate models in mock or real mode and write a markdown report."""
import time
from pathlib import Path
import json
from src.registry import load_registry
from src.selector import ModelSelector
from src.adapters.adapter_loader import get_component
import datetime
import traceback

OUT = Path("outputs") / "benchmarks"
OUT.mkdir(parents=True, exist_ok=True)


def measure(func, *a, **kw):
    t0 = time.perf_counter()
    res = func(*a, **kw)
    t1 = time.perf_counter()
    return res, t1 - t0


def run_benchmark(mock=True):
    reg = load_registry().data
    sel = ModelSelector(reg)
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    run_dir = OUT / f"benchmark_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "timestamp": timestamp,
        "mock": bool(mock),
        "results": [],
    }

    # For each role, attempt to load adapter and run a minimal workload
    for role in reg.keys():
        pick = sel.pick(role, profile=("mock" if mock else "balanced"))
        entry = {"role": role, "choice": pick, "duration_s": None, "memory": None, "result": None}

        if mock:
            def work():
                time.sleep(0.05)
                return {"status": "ok", "note": "mock run"}
            res, dur = measure(work)
            entry["duration_s"] = dur
            entry["result"] = res
        else:
            try:
                comp = get_component(role, profile="balanced")
                if comp is None:
                    entry["result"] = {"status": "no_adapter", "note": "no adapter available on this machine"}
                else:
                    # run small sample for each role
                    def task():
                        if role == "transcriber":
                            return comp.run("tests/sample_audio_short.wav")
                        if role == "planner":
                            return comp.run("This is a short subtitle. Make scenes.")
                        if role in ("tts", "tts_generator"):
                            return comp.run("Hello world", output=str(run_dir / "tts_test.wav"))
                        if role == "image_generation":
                            return comp.run("A sunset over mountains", count=1)
                        if role == "video_generation":
                            return comp.run({"prompt": "short motion"})
                        # generic
                        return {"status": "no_task_defined"}

                    res, dur = measure(task)
                    entry["duration_s"] = dur
                    entry["result"] = res
            except Exception as e:
                entry["result"] = {"status": "error", "error": str(e), "trace": traceback.format_exc()}
                entry["duration_s"] = 0.0

        report["results"].append(entry)

    # write JSON and markdown summary
    (run_dir / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    md = [f"# Benchmark {timestamp}\n", f"Mock mode: {mock}\n\n"]
    for r in report["results"]:
        # defensive formatting when fields may be missing
        choice = r.get('choice', {})
        choice_name = choice.get('choice') if isinstance(choice, dict) else str(choice)
        source = choice.get('source') if isinstance(choice, dict) else None
        duration = r.get('duration_s') or 0.0
        note = (r.get('result') or {}).get('note', '') if isinstance(r.get('result'), dict) else str(r.get('result'))
        md.append(f"- **{r['role']}** -> {choice_name} ({source}) — {duration:.3f}s — {note}\n")
    (run_dir / "summary.md").write_text("\n".join(md), encoding="utf-8")
    print(f"Benchmark written to {run_dir}")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--mock", action="store_true", help="Run in fast mock mode")
    args = p.parse_args()
    run_benchmark(mock=args.mock)
