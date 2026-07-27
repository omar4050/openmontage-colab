"""Kokoro TTS - Open source, lightweight, high-quality text-to-speech.

Kokoro is a fast, open-source TTS model that produces natural-sounding speech.
It runs locally for free and supports multiple languages.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Any

from tools.base_tool import (
    BaseTool,
    Determinism,
    ExecutionMode,
    ResourceProfile,
    ToolResult,
    ToolRuntime,
    ToolStability,
    ToolStatus,
    ToolTier,
)


class KokoroTTS(BaseTool):
    name = "kokoro_tts"
    version = "0.1.0"
    tier = ToolTier.VOICE
    capability = "tts"
    provider = "kokoro"
    stability = ToolStability.BETA
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.DETERMINISTIC
    runtime = ToolRuntime.LOCAL

    dependencies = ["cmd:python"]
    install_instructions = (
        "Install Kokoro TTS:\n"
        "  pip install kokoro-onnx\n"
        "Or from source:\n"
        "  pip install git+https://github.com/remixer-dec/kokoro-onnx.git"
    )
    fallback_tools = ["piper_tts"]
    agent_skills = ["text-to-speech"]

    capabilities = [
        "text_to_speech",
        "offline_generation",
    ]
    supports = {
        "offline": True,
        "free": True,
        "fast": True,
        "multiple_voices": True,
        "natural_sounding": True,
    }
    best_for = [
        "offline TTS without API keys",
        "real-time or batch narration",
        "high-quality open-source speech",
        "low-latency generation",
    ]
    not_good_for = [
        "highly specialized accents",
        "extreme customization",
    ]

    input_schema = {
        "type": "object",
        "required": ["text"],
        "properties": {
            "text": {
                "type": "string",
                "description": "Text to convert to speech",
            },
            "voice": {
                "type": "string",
                "enum": ["af", "am", "en", "es", "fr", "ja", "ko", "pt", "tr", "zh"],
                "default": "en",
                "description": "Voice language code (af=Afrikaans, am=Amharic, en=English, etc.)",
            },
            "speed": {
                "type": "number",
                "minimum": 0.5,
                "maximum": 2.0,
                "default": 1.0,
                "description": "Speech speed multiplier",
            },
            "output_path": {
                "type": "string",
                "default": "kokoro_output.wav",
                "description": "Path where the WAV file should be written",
            },
        },
    }

    def execute(self, input_data: dict[str, Any]) -> ToolResult:
        """Generate speech using Kokoro TTS."""
        try:
            text = input_data.get("text", "")
            voice = input_data.get("voice", "en")
            speed = input_data.get("speed", 1.0)
            output_path = Path(input_data.get("output_path", "kokoro_output.wav"))

            if not text:
                return ToolResult(
                    success=False,
                    error="text parameter is required",
                    data={},
                )

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Try to use Kokoro via Python API
            try:
                import kokoro
            except ImportError:
                return ToolResult(
                    success=False,
                    error="Kokoro TTS not installed. Install with: pip install kokoro-onnx",
                    data={},
                    status=ToolStatus.UNAVAILABLE,
                )

            # Initialize Kokoro engine
            try:
                from kokoro import generate
                
                # Generate audio
                audio, sr = generate(
                    text,
                    voice=voice,
                    speed=speed,
                )

                # Save to file
                import soundfile as sf
                
                sf.write(str(output_path), audio, sr)

                return ToolResult(
                    success=True,
                    data={
                        "audio_path": str(output_path),
                        "format": "wav",
                        "sample_rate": sr,
                        "duration_seconds": len(audio) / sr,
                        "cost_usd": 0.0,  # Open source, free
                        "voice": voice,
                        "speed": speed,
                    },
                    status=ToolStatus.COMPLETED,
                )

            except Exception as e:
                return ToolResult(
                    success=False,
                    error=f"Kokoro generation failed: {str(e)}",
                    data={},
                )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Unexpected error in Kokoro TTS: {str(e)}",
                data={},
            )

    def probe(self) -> dict[str, Any]:
        """Check if Kokoro is available."""
        try:
            import kokoro
            
            return {
                "available": True,
                "version": getattr(kokoro, "__version__", "unknown"),
                "voices": ["af", "am", "en", "es", "fr", "ja", "ko", "pt", "tr", "zh"],
            }
        except ImportError:
            return {
                "available": False,
                "install_command": "pip install kokoro-onnx",
            }
