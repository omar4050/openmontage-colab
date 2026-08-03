"""Generic adapter stubs for capabilities that currently lack a production adapter.

These classes are intentionally minimal: they subclass the project's abstraction
interfaces, accept model_name/config, set available=False, and implement run()
that raises or returns a clear unavailable result. This lets preflight detect
adapter presence and instantiation without pretending the model is usable.
"""
from typing import Any, Dict
from src.abstractions import (
    Planner,
    Transcriber,
    VoiceGenerator,
    ImageGenerator,
    VideoGenerator,
    MusicGenerator,
    Enhancer,
)


class PlannerStub(Planner):
    def __init__(self, model_name: str = "stub", config: Dict[str, Any] = None):
        super().__init__(model_name, config)
        self.available = False

    def run(self, subtitles: str, **kwargs) -> Dict[str, Any]:
        return {"status": "unavailable", "reason": "adapter_stub", "model": self.model_name}


class TranscriberStub(Transcriber):
    def __init__(self, model_name: str = "stub", config: Dict[str, Any] = None):
        super().__init__(model_name, config)
        self.available = False

    def run(self, audio_path: str, **kwargs) -> Dict[str, Any]:
        return {"status": "unavailable", "reason": "adapter_stub", "model": self.model_name}


class VoiceStub(VoiceGenerator):
    def __init__(self, model_name: str = "stub", config: Dict[str, Any] = None):
        super().__init__(model_name, config)
        self.available = False

    def run(self, text: str, **kwargs) -> Dict[str, Any]:
        return {"status": "unavailable", "reason": "adapter_stub", "model": self.model_name}


class ImageStub(ImageGenerator):
    def __init__(self, model_name: str = "stub", config: Dict[str, Any] = None):
        super().__init__(model_name, config)
        self.available = False

    def run(self, prompt: str, count: int = 1, **kwargs) -> Dict[str, Any]:
        return {"status": "unavailable", "reason": "adapter_stub", "model": self.model_name, "paths": []}


class VideoStub(VideoGenerator):
    def __init__(self, model_name: str = "stub", config: Dict[str, Any] = None):
        super().__init__(model_name, config)
        self.available = False

    def run(self, prompts: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        return {"status": "unavailable", "reason": "adapter_stub", "model": self.model_name}


class MusicStub(MusicGenerator):
    def __init__(self, model_name: str = "stub", config: Dict[str, Any] = None):
        super().__init__(model_name, config)
        self.available = False

    def run(self, prompt: str, duration: int = 30, **kwargs) -> Dict[str, Any]:
        return {"status": "unavailable", "reason": "adapter_stub", "model": self.model_name}


class EnhancerStub(Enhancer):
    def __init__(self, model_name: str = "stub", config: Dict[str, Any] = None):
        super().__init__(model_name, config)
        self.available = False

    def run(self, asset_path: str, **kwargs) -> Dict[str, Any]:
        return {"status": "unavailable", "reason": "adapter_stub", "model": self.model_name}
