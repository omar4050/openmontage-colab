"""Simple modular pipeline runner with mock mode for OpenMontage.

NOTE: This module is a local smoke-test / mock runner. Production runs MUST go
through the orchestrator preflight and pipeline manifest flow (see lib/orchestrator.py
and AGENT_GUIDE.md Rule Zero).
"""
from pathlib import Path
from .registry import load_registry
from .selector import ModelSelector
from .mock import (
    MockPlanner,
    MockTranscriber,
    MockVoice,
    MockImageGen,
    MockVideoGen,
    MockEditor,
    MockEnhancer,
    MockMusic,
)
import json
import logging
import time
from typing import Dict, Any

log = logging.getLogger(__name__)

PROJECTS_ROOT = Path("projects")


class Pipeline:
    def __init__(self, mock: bool = True):
        self.registry = load_registry().data
        self.selector = ModelSelector(self.registry)
        self.mock = mock

        # Try to load real adapters via adapter_loader. Fall back to mocks when unavailable.
        from .adapters.adapter_loader import get_component

        # helper to choose adapter or mock
        def _get(role: str, mock_cls):
            if self.mock:
                return mock_cls("mock")
            comp = get_component(role, profile=("mock" if self.mock else "balanced"))
            if comp is None:
                return mock_cls("mock")
            return comp

        self.planner = _get("planner", MockPlanner)
        self.transcriber = _get("transcriber", MockTranscriber)
        self.voice = _get("tts", MockVoice)
        self.image = _get("image_generation", MockImageGen)
        self.video = _get("video_generation", MockVideoGen)
        self.editor = _get("montage", MockEditor)
        self.enhancer = _get("enhancement", MockEnhancer)
        self.music = _get("music", MockMusic)

    def run(self, title: str = "sample-project") -> Dict[str, Any]:
        project = PROJECTS_ROOT / title
        project.mkdir(parents=True, exist_ok=True)
        artifacts = project / "artifacts"
        artifacts.mkdir(parents=True, exist_ok=True)

        start = time.perf_counter()
        log.info("Running planner (mock)...")
        plan = self.planner.run("[mock subtitles]")
        (artifacts / "scene_plan.json").write_text(json.dumps(plan, indent=2))

        log.info("Generating voice (mock)...")
        voice = self.voice.run("This is a mocked narration.", output=str(project / "assets" / "audio" / "voice.wav"))

        log.info("Generating images (mock)...")
        imgs = self.image.run("A cinematic still", count=2)

        log.info("Generating video clips (mock)...")
        clip = self.video.run({"prompt": "motion clip"})

        log.info("Composing (mock)...")
        final = self.editor.run(str(project), assets={"voice": voice, "images": imgs, "clip": clip})

        duration = time.perf_counter() - start
        summary = {
            "project": title,
            "plan": plan,
            "voice": voice,
            "images": imgs,
            "clip": clip,
            "final": final,
            "duration_s": duration,
        }
        (artifacts / "run_summary.json").write_text(json.dumps(summary, indent=2))
        return summary


def create_sample_run(output_dir: str = "projects/sample-project") -> Dict[str, Any]:
    p = Pipeline(mock=True)
    return p.run("sample-project")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    s = create_sample_run()
    print("Created sample run:", s.get("final"))
