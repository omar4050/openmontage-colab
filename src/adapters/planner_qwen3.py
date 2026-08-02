"""Minimal Qwen3 planner adapter (graceful if library missing).

This adapter is a placeholder that should be expanded to call the real Qwen3 SDK
or local runtime. For now it reports `available=False` unless a `qwen3` package
is importable.
"""
from typing import Dict, Any
from src.abstractions import Planner


class PlannerQwen3(Planner):
    def __init__(self, model_name: str, config: Dict[str, Any] = None):
        super().__init__(model_name, config)
        self.available = False
        try:
            import qwen3  # type: ignore
            self.available = True
            # store client if needed in future
            self._client = qwen3
        except Exception:
            # qwen3 not installed locally; keep available False to let loader fallback
            self.available = False

    def run(self, subtitles: str, **kwargs) -> Dict[str, Any]:
        if self.available:
            # Best-effort placeholder: applications should implement a prompt and call the real Qwen3 client here.
            try:
                # If qwen3 exposes a chat/completion API, call it. Keep minimal to avoid hard dependency.
                client = getattr(self, "_client", None)
                if client is not None and hasattr(client, "Completion"):
                    # this is a defensive, optional path — real usage requires adapting to the installed SDK
                    resp = client.Completion.create(prompt="Generate a scene plan from subtitles:\n" + subtitles)
                    return {"title": "Qwen3 plan", "scenes": resp}
            except Exception:
                pass

        # Fallback heuristic planner: split subtitles into short scenes by sentence
        import re
        sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", subtitles) if s.strip()]
        scenes = []
        for i, sent in enumerate(sents[:20]):
            scenes.append({"id": f"scene-{i+1}", "duration": max(3, min(12, len(sent.split()) // 2)), "description": sent})
        if not scenes:
            scenes = [{"id": "scene-1", "duration": 5, "description": subtitles or "Opening"}]
        return {"title": "Heuristic Plan", "scenes": scenes}
