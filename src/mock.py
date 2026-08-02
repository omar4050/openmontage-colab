"""Mock implementations for fast local development and testing."""
from .abstractions import (
    Planner,
    Transcriber,
    VoiceGenerator,
    ImageGenerator,
    VideoGenerator,
    Editor,
    Enhancer,
    MusicGenerator,
)
from typing import Dict, Any
import time
import json
from pathlib import Path


class MockPlanner(Planner):
    def __init__(self, model_name: str = "mock-planner"):
        super().__init__(model_name)
    
    def run(self, subtitles: str, **kwargs) -> Dict[str, Any]:
        time.sleep(0.1)
        plan = {
            "title": "Sample Plan",
            "scenes": [
                {"id": "scene-1", "duration": 5, "description": "Opening shot"},
                {"id": "scene-2", "duration": 8, "description": "Middle"},
            ],
        }
        return plan


class MockTranscriber(Transcriber):
    def __init__(self, model_name: str = "mock-transcriber"):
        super().__init__(model_name)
    
    def run(self, audio_path: str, **kwargs) -> Dict[str, Any]:
        time.sleep(0.05)
        return {"transcript": "This is a mocked transcript.", "segments": []}


class MockVoice(VoiceGenerator):
    def __init__(self, model_name: str = "mock-voice"):
        super().__init__(model_name)
    
    def run(self, text: str, **kwargs) -> Dict[str, Any]:
        out = Path(kwargs.get("output", "projects/sample-project/assets/audio/voice_mock.wav"))
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("MOCK_AUDIO")
        return {"path": str(out)}


class MockImageGen(ImageGenerator):
    def __init__(self, model_name: str = "mock-image"):
        super().__init__(model_name)
    
    def run(self, prompt: str, count: int = 1, **kwargs) -> Dict[str, Any]:
        out_dir = Path("projects/sample-project/assets/images")
        out_dir.mkdir(parents=True, exist_ok=True)
        paths = []
        for i in range(count):
            p = out_dir / f"mock_img_{i+1}.png"
            p.write_text("MOCK_IMAGE")
            paths.append(str(p))
        return {"paths": paths}


class MockVideoGen(VideoGenerator):
    def __init__(self, model_name: str = "mock-video"):
        super().__init__(model_name)
    
    def run(self, prompts: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        out_dir = Path("projects/sample-project/assets/video")
        out_dir.mkdir(parents=True, exist_ok=True)
        p = out_dir / "mock_clip.mp4"
        p.write_text("MOCK_VIDEO")
        return {"path": str(p)}


class MockEditor(Editor):
    def __init__(self, model_name: str = "mock-editor"):
        super().__init__(model_name)
    
    def run(self, project_path: str, assets: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        project = Path(project_path)
        project.mkdir(parents=True, exist_ok=True)
        final = project / "renders" / "final.mp4"
        final.parent.mkdir(parents=True, exist_ok=True)
        final.write_text("MOCK_FINAL_VIDEO")
        return {"final": str(final)}


class MockEnhancer(Enhancer):
    def __init__(self, model_name: str = "mock-enhancer"):
        super().__init__(model_name)
    
    def run(self, asset_path: str, **kwargs) -> Dict[str, Any]:
        # touch a new file to represent enhanced output
        p = Path(asset_path)
        out = p.parent / (p.stem + "_enhanced" + p.suffix)
        out.write_text("MOCK_ENHANCED")
        return {"path": str(out)}


class MockMusic(MusicGenerator):
    def __init__(self, model_name: str = "mock-music"):
        super().__init__(model_name)
    
    def run(self, prompt: str, duration: int = 30, **kwargs) -> Dict[str, Any]:
        out = Path("projects/sample-project/assets/music/bg_mock.mp3")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("MOCK_MUSIC")
        return {"path": str(out)}


# Aliases for compatibility
MockVoiceGenerator = MockVoice
MockImageGenerator = MockImageGen
MockVideoGenerator = MockVideoGen
MockMusicGenerator = MockMusic
