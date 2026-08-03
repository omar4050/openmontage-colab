"""Model selector that picks primary/fallback/mock based on simple heuristics."""
from typing import Dict, Optional
import logging

try:
    import torch
except Exception:
    torch = None

try:
    import psutil
except Exception:
    psutil = None

log = logging.getLogger(__name__)


class ModelSelector:
    def __init__(self, registry: Dict[str, Dict]):
        self.registry = registry

    def _has_gpu(self) -> bool:
        if torch is None:
            return False
        try:
            return torch.cuda.is_available()
        except Exception:
            return False

    def _gpu_memory_gb(self) -> Optional[float]:
        # best-effort GPU memory estimate
        try:
            if torch is not None and torch.cuda.is_available():
                return torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
        except Exception:
            pass
        return None

    def pick(self, role: str, profile: str = "balanced") -> Dict[str, str]:
        """Pick a model entry for a given role.

        profile selects preference order defined in registry.profiles. Logic:
        - If registry defines a structured `models` list, use tier preferences from profiles
        - Respect local compatibility and GPU/memory constraints
        - Return dict {choice: model_id, source: tier}
        """
        info = self.registry.get(role) or {}
        if not info:
            log.warning("No registry entry for role=%s", role)
            return {"choice": "mock", "source": "mock"}

        # Support legacy shorthand (primary/fallback)
        if "models" not in info:
            # fallback to legacy behavior
            has_gpu = self._has_gpu()
            primary = info.get("primary")
            fallback = info.get("fallback")
            lw = info.get("lightweight_fallback") or info.get("small_fallback")
            if profile == "mock":
                return {"choice": info.get("mock", "mock"), "source": "mock"}
            if has_gpu:
                return {"choice": primary or fallback or "mock", "source": "primary"}
            if lw:
                return {"choice": lw, "source": "fallback"}
            return {"choice": primary or fallback or "mock", "source": "primary"}

        models = info.get("models", [])
        profiles = self.registry.get("profiles", {})
        profile_conf = profiles.get(profile) or profiles.get(self.registry.get("policy", {}).get("profiles_default", "local-first")) or {"prefer_tiers": ["default", "lightweight", "premium"], "allow_cloud": False}
        prefer_tiers = profile_conf.get("prefer_tiers", ["default", "lightweight", "premium"]) if isinstance(profile_conf, dict) else ["default", "lightweight", "premium"]

        has_gpu = self._has_gpu()
        gpu_mem = self._gpu_memory_gb() or 0

        # Try tiers in order
        for tier in prefer_tiers:
            candidates = [m for m in models if m.get("tier") == tier]
            for m in candidates:
                # Skip if model requires GPU but none available
                res = m.get("resources", {}) or {}
                requires_gpu = bool(res.get("gpu"))
                vram = float(res.get("vram_gb") or 0)
                local_ok = bool(m.get("local_compatible", False))
                if requires_gpu and not has_gpu:
                    continue
                if requires_gpu and vram and gpu_mem and vram > gpu_mem:
                    # not enough GPU memory
                    continue
                if not local_ok and self.registry.get("policy", {}).get("local_first", True):
                    # local-first policy disallows non-local models
                    continue
                # candidate acceptable
                return {"choice": m.get("id"), "source": tier}

        # If nothing matched, pick any production_ready model as a last resort
        for m in models:
            if m.get("production_ready"):
                return {"choice": m.get("id"), "source": m.get("tier")}

        # final fallback
        return {"choice": models[0].get("id") if models else "mock", "source": "fallback"}
