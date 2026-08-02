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
        profile: one of 'fast','quality','balanced'
        Returns a dict with keys: choice, source (primary|fallback|mock)
        """
        info = self.registry.get(role) or {}
        if not info:
            log.warning("No registry entry for role=%s", role)
            return {"choice": "mock", "source": "mock"}

        # local-first: pick primary if local GPU available or profile favors quality
        has_gpu = self._has_gpu()
        gpu_mem = self._gpu_memory_gb()

        # If mock requested via special profile
        if profile == "mock":
            return {"choice": info.get("mock", "mock"), "source": "mock"}

        primary = info.get("primary")
        fallback = info.get("fallback")

        if has_gpu:
            # prefer primary when GPU present
            return {"choice": primary or fallback or "mock", "source": "primary"}

        # No GPU: prefer lightweight fallback if present
        lw = info.get("lightweight_fallback") or info.get("small_fallback")
        if lw:
            return {"choice": lw, "source": "fallback"}

        # default fallback to primary if nothing else
        return {"choice": primary or fallback or "mock", "source": "primary"}
