"""Wan 2.2 video generator adapter with MoviePy fallback.

Attempts to use a native `wan` package if present. If not, uses MoviePy
to assemble a short clip from provided images or generates a color clip as a lightweight local fallback.
"""
from typing import Dict, Any
from src.abstractions import VideoGenerator
from pathlib import Path
import logging

log = logging.getLogger(__name__)


class WanVideoGenerator(VideoGenerator):
    def __init__(self, model_name: str, config: Dict[str, Any] = None):
        super().__init__(model_name, config)
        self.available = False
        self._backend = None
        try:
            import wan  # hypothetical wan python package
            self._backend = "wan"
            self.available = True
        except Exception:
            try:
                from moviepy.editor import ImageSequenceClip, ColorClip  # type: ignore
                self._backend = "moviepy"
                self.available = True
            except Exception as e:
                log.debug("No wan or moviepy available: %s", e)
                self.available = False

    def run(self, prompts: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        out_dir = Path(kwargs.get("output_dir", "projects/sample-project/assets/video"))
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / (kwargs.get("filename", "wan_fallback.mp4"))

        if not self.available:
            raise RuntimeError("No video backend available locally")

        if self._backend == "wan":
            # Placeholder for actual WAN SDK usage
            try:
                wan = __import__("wan")
                # user must implement real call; here we raise to indicate non-implemented
                raise NotImplementedError("WAN SDK call not implemented in adapter; integrate your local WAN client here.")
            except Exception as e:
                raise RuntimeError(f"wan backend failed: {e}")

        if self._backend == "moviepy":
            try:
                from moviepy.editor import ImageSequenceClip, ColorClip
                images = prompts.get("images") or []
                duration = float(prompts.get("duration", 5.0))
                fps = int(prompts.get("fps", 24))
                if images:
                    clip = ImageSequenceClip(images, fps=fps)
                    clip = clip.set_duration(duration)
                    clip.write_videofile(str(out_path), fps=fps, audio=False, logger=None)
                else:
                    # create a solid color clip as a placeholder
                    clip = ColorClip(size=(1280, 720), color=(20, 20, 40), duration=duration)
                    clip.write_videofile(str(out_path), fps=fps, audio=False, logger=None)
                return {"path": str(out_path)}
            except Exception as e:
                raise RuntimeError(f"moviepy fallback failed: {e}")

        raise RuntimeError("Unsupported video backend")
