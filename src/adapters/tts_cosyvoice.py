"""CosyVoice TTS adapter placeholder.
"""
from typing import Dict, Any
from src.abstractions import VoiceGenerator


class CosyVoiceTTS(VoiceGenerator):
    def __init__(self, model_name: str, config: Dict[str, Any] = None):
        super().__init__(model_name, config)
        self.available = False
        self._backend = None
        try:
            import cosyvoice  # hypothetical package
            self._backend = "cosyvoice"
            self.available = True
        except Exception:
            try:
                import pyttsx3
                self._backend = "pyttsx3"
                self.available = True
            except Exception:
                self.available = False

    def run(self, text: str, **kwargs) -> Dict[str, Any]:
        if not self.available:
            raise RuntimeError("No TTS backend available locally (cosyvoice or pyttsx3)")
        output = kwargs.get("output") or kwargs.get("path") or "projects/sample-project/assets/audio/voice.wav"
        if self._backend == "cosyvoice":
            try:
                import cosyvoice
                # This is a placeholder: actual SDK usage will vary
                cosy = cosyvoice.Client()
                cosy.synthesize(text, output)
                return {"path": output}
            except Exception as e:
                raise RuntimeError(f"cosyvoice TTS failed: {e}")

        if self._backend == "pyttsx3":
            try:
                import pyttsx3
                engine = pyttsx3.init()
                # ensure parent dir exists
                from pathlib import Path
                p = Path(output)
                p.parent.mkdir(parents=True, exist_ok=True)
                engine.save_to_file(text, str(p))
                engine.runAndWait()
                return {"path": str(p)}
            except Exception as e:
                raise RuntimeError(f"pyttsx3 TTS failed: {e}")
