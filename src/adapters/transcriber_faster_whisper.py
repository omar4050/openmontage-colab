"""Adapter wrapper for faster-whisper (best-effort local availability).
Falls back to unavailable when package not present.
"""
from typing import Dict, Any
from src.abstractions import Transcriber


class FasterWhisperTranscriber(Transcriber):
    def __init__(self, model_name: str, config: Dict[str, Any] = None):
        super().__init__(model_name, config)
        self.available = False
        self._backend = None
        self._model = None
        self._model_path = None
        self.config = config or {}
        model_spec = self.config.get("model", "small")

        # If model_spec looks like a huggingface repo id, try to download it into models/
        try:
            from scripts.model_helpers import check_model_available, download_hf_repo  # type: ignore
        except Exception:
            check_model_available = None
            download_hf_repo = None

        # Resolve model path or id
        if isinstance(model_spec, str) and "/" in model_spec:
            # treat as HF repo
            repo = model_spec
            local_dir = Path("models") / repo.replace("/", "__")
            if not local_dir.exists():
                if check_model_available:
                    ok = check_model_available(repo)
                    if not ok and download_hf_repo:
                        try:
                            download_hf_repo(repo, local_dir)
                        except Exception:
                            pass
            if local_dir.exists():
                self._model_path = str(local_dir)
            else:
                # fallback to using the hub id directly
                self._model_path = repo
        else:
            self._model_path = model_spec

        # Try faster-whisper first
        try:
            from faster_whisper import WhisperModel  # type: ignore
            import torch
            device = "cuda" if torch and getattr(torch, "cuda", None) and torch.cuda.is_available() else "cpu"
            compute_type = self.config.get("compute_type")
            # initialize model with optional compute_type
            if compute_type and device == "cuda":
                self._model = WhisperModel(self._model_path, device=device, compute_type=compute_type)
            else:
                self._model = WhisperModel(self._model_path, device=device)
            self._backend = "faster_whisper"
            self.available = True
        except Exception:
            # Try the OpenAI/whisper package as fallback
            try:
                import whisper  # type: ignore
                self._backend = "whisper"
                self._model = whisper
                self.available = True
            except Exception:
                self.available = False

    def run(self, audio_path: str, **kwargs) -> Dict[str, Any]:
        """Transcribe audio_path and return dict {transcript, segments, info?}.

        kwargs may include model override, beam_size, language, and temperature.
        """
        if not self.available:
            raise RuntimeError("No local transcription backend available (faster-whisper or whisper)")

        beam_size = int(kwargs.get("beam_size", 5))

        if self._backend == "faster_whisper":
            model = self._model
            segments_out = []
            try:
                segs, info = model.transcribe(audio_path, beam_size=beam_size)
                for s in segs:
                    segments_out.append({"start": float(s.start), "end": float(s.end), "text": str(s.text)})
                transcript = "".join([s["text"] for s in segments_out])
                return {"transcript": transcript, "segments": segments_out, "info": getattr(info, "__dict__", str(info))}
            except Exception as e:
                raise RuntimeError(f"faster-whisper transcription failed: {e}")

        if self._backend == "whisper":
            whisper = self._model
            try:
                model_name = kwargs.get("model", self._model_path or "small")
                m = whisper.load_model(model_name)
                res = m.transcribe(audio_path)
                return {"transcript": res.get("text", ""), "segments": res.get("segments", [])}
            except Exception as e:
                raise RuntimeError(f"whisper transcription failed: {e}")
