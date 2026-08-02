"""Lightweight runtime health checks used by the orchestrator.

This module intentionally keeps the checks simple and safe to run in CI/Colab:
- Avoids forcing heavy imports unless available (torch).
- Returns a machine-readable report suitable for the preflight step.
"""
import shutil
import subprocess
import json
import os
from typing import Dict, Any


def _which(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def _run_cmd(cmd):
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        return out.decode("utf-8", errors="replace")
    except Exception:
        return None


def check_environment() -> Dict[str, Any]:
    """Return a dictionary describing key environment availability."""
    report: Dict[str, Any] = {}
    report["ffmpeg"] = {"available": _which("ffmpeg")}
    report["ffprobe"] = {"available": _which("ffprobe")}
    report["node"] = {"available": _which("node")}
    report["disk_free_gb"] = round(shutil.disk_usage(".").free / (1024 ** 3), 2)
    # Torch / GPU info (best-effort)
    try:
        import torch
        cuda = torch.cuda.is_available()
        gpus = torch.cuda.device_count() if cuda else 0
        gpu_names = []
        for i in range(gpus):
            try:
                gpu_names.append(torch.cuda.get_device_name(i))
            except Exception:
                gpu_names.append("unknown")
        report["torch"] = {"available": True, "cuda": cuda, "gpu_count": gpus, "gpu_names": gpu_names}
    except Exception:
        report["torch"] = {"available": False, "cuda": False, "gpu_count": 0}
    # Basic runtime info
    report["python_version"] = {"version": os.sys.version.split()[0]}
    return report


def check_capabilities(registry) -> Dict[str, Any]:
    """
    Best-effort capability readiness from a registry-like object.
    The registry is expected to provide either:
      - registry.capability_catalog() OR
      - registry.capabilities() / registry.provider_menu_summary()
    This function never raises if registry is missing fields — it returns a conservative readiness map.
    """
    result: Dict[str, Any] = {}
    try:
        if hasattr(registry, "capability_catalog"):
            caps = registry.capability_catalog()
        elif hasattr(registry, "capabilities"):
            caps = registry.capabilities()
        elif hasattr(registry, "provider_menu_summary"):
            caps = registry.provider_menu_summary().get("capabilities", {})
        else:
            caps = {}
    except Exception:
        caps = {}

    env = check_environment()
    for cap_name, cap_info in (caps.items() if isinstance(caps, dict) else []):
        # Default: if any configured provider exists, mark as configured
        configured = cap_info.get("configured", None) if isinstance(cap_info, dict) else None
        if configured is None:
            # try to infer from provider list
            providers = cap_info.get("providers") if isinstance(cap_info, dict) else None
            configured = bool(providers)
        result[cap_name] = {"configured": configured, "reason": "inferred"}
    # For safety, include a few canonical capabilities if absent
    for canonical in ("video_generation", "image_generation", "tts", "music_generation", "editing"):
        result.setdefault(canonical, {"configured": False, "reason": "missing_from_registry"})
    return {"environment": env, "capabilities": result}
