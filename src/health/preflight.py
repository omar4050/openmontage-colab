"""Model & capability preflight health checker.

Scans configs/models.yaml, attempts to load mapped adapters, and reports
configured vs available vs initializable. Writes a JSON report to
`health_report.json` and prints a human-friendly summary.

Usage: python -m src.health.preflight --profile local-first
"""
import argparse
import json
import logging
from pathlib import Path
from src.registry import load_registry
from src.adapters import adapter_loader

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def check_model_entry(model_id: str, adapter_map: dict, adapters_conf: dict):
    result = {"model_id": model_id, "configured": True, "adapter_found": False, "initializable": False, "available": False, "notes": []}
    mapping = adapter_map.get(model_id)
    if not mapping:
        result["notes"].append("no_adapter_mapping")
        return result
    module_name, class_name = mapping
    full_module = f"src.adapters.{module_name}"
    try:
        mod = __import__(full_module, fromlist=[class_name])
        cls = getattr(mod, class_name)
        result["adapter_found"] = True
        # pass adapter-specific config from registry if present
        conf = adapters_conf.get(model_id, {})
        # Try multiple safe instantiation patterns to handle adapter constructor differences
        inst = None
        inst_errors = []
        attempts = [
            (lambda: cls(model_id, config=conf or {})),
            (lambda: cls(model_id)),
            (lambda: cls(conf or {})),
            (lambda: cls()),
        ]
        for attempt in attempts:
            try:
                inst = attempt()
                break
            except TypeError as te:
                inst_errors.append(str(te))
                continue
            except Exception as e:
                inst_errors.append(str(e))
                continue
        if inst is None:
            result["notes"].append("adapter_instantiation_failed: " + " | ".join(inst_errors))
        else:
            result["initializable"] = True
            result["available"] = getattr(inst, "available", False)
            if not result["available"]:
                result["notes"].append("adapter_initialization_succeeded_but_unavailable")
    except Exception as e:
        result["notes"].append(f"import_failed: {e}")
    return result


def run_preflight(profile: str = "local-first"):
    reg = load_registry().data
    adapters_conf = reg.get("adapters", {})
    model_map = {}
    # build flat list of models across capabilities
    for cap, entry in reg.items():
        if cap in ("adapters", "policy", "profiles", "health"):
            continue
        models = []
        if isinstance(entry, dict) and "models" in entry:
            models = entry.get("models", [])
        else:
            # backward-compat: entry could be shorthand with default_choice
            continue
        for m in models:
            model_map[m["id"]] = m

    report = {"profile": profile, "models": {}}
    for mid in sorted(model_map.keys()):
        report["models"][mid] = check_model_entry(mid, adapter_loader.MODEL_TO_ADAPTER, adapters_conf)

    out = Path("health_report.json")
    out.write_text(json.dumps(report, indent=2))
    # print concise summary
    for mid, r in report["models"].items():
        status = "OK" if r["available"] else ("INIT_OK" if r["initializable"] else "MISSING")
        log.info("%s: %s (%s)", mid, status, ",".join(r.get("notes", []))[:200])
    log.info("Wrote health report to %s", out)
    return report


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--profile", default="local-first")
    args = p.parse_args()
    run_preflight(args.profile)
