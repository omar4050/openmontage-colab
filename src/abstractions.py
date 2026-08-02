"""Abstract interfaces for pipeline components."""
from abc import ABC, abstractmethod
from typing import Any, Dict


class Component(ABC):
    def __init__(self, model_name: str, config: Dict[str, Any] | None = None):
        self.model_name = model_name
        self.config = config or {}

    @abstractmethod
    def run(self, *args, **kwargs) -> Any:
        raise NotImplementedError


class Planner(Component):
    def run(self, subtitles: str, **kwargs) -> Dict[str, Any]:
        """Produce a structured scene plan from subtitles/text."""
        raise NotImplementedError


class Transcriber(Component):
    def run(self, audio_path: str, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError


class VoiceGenerator(Component):
    def run(self, text: str, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError


class ImageGenerator(Component):
    def run(self, prompt: str, count: int = 1, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError


class VideoGenerator(Component):
    def run(self, prompts: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        raise NotImplementedError


class Editor(Component):
    def run(self, project_path: str, assets: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        raise NotImplementedError


class Enhancer(Component):
    def run(self, asset_path: str, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError


class MusicGenerator(Component):
    def run(self, prompt: str, duration: int = 30, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError
