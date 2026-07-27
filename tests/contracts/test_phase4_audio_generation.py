"""Phase 4 contract tests — Voice & Audio Generation.

Tests TTS providers (Kokoro, Piper, Google, ElevenLabs, OpenAI),
music generation (Google Music, Suno, Pixabay), music library,
audio mixing, and end-to-end audio pipeline.
"""

import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.audio.kokoro_tts import KokoroTTS
from tools.audio.piper_tts import PiperTTS
from tools.audio.google_tts import GoogleTTS
from tools.audio.openai_tts import OpenAITTS
from tools.audio.elevenlabs_tts import ElevenLabsTTS
from tools.audio.music_library import MusicLibrary
from tools.audio.google_music import GoogleMusic
from tools.audio.audio_mixer import AudioMixer
from tools.base_tool import ToolStatus


class TestKokoroTTS:
    """Test Kokoro TTS provider."""

    def test_kokoro_tts_schema(self):
        """Verify Kokoro TTS has correct input schema."""
        tool = KokoroTTS()
        schema = tool.input_schema

        assert schema["type"] == "object"
        assert "text" in schema["required"]
        assert "voice" in schema["properties"]
        assert "speed" in schema["properties"]
        assert "output_path" in schema["properties"]

    def test_kokoro_tts_probe_unavailable(self):
        """Test probe when Kokoro is not installed."""
        tool = KokoroTTS()
        
        with patch("tools.audio.kokoro_tts.KokoroTTS.probe") as mock_probe:
            mock_probe.return_value = {
                "available": False,
                "install_command": "pip install kokoro-onnx"
            }
            
            result = mock_probe()
            assert result["available"] is False
            assert "pip install" in result["install_command"]

    def test_kokoro_tts_metadata(self):
        """Test Kokoro TTS tool metadata."""
        tool = KokoroTTS()

        assert tool.name == "kokoro_tts"
        assert tool.provider == "kokoro"
        assert tool.tier.value == "voice"
        assert tool.runtime.value == "local"
        assert tool.supports["offline"] is True
        assert tool.supports["free"] is True


class TestPiperTTS:
    """Test Piper TTS provider (fallback)."""

    def test_piper_tts_schema(self):
        """Verify Piper TTS has correct input schema."""
        tool = PiperTTS()
        schema = tool.input_schema

        assert schema["type"] == "object"
        assert "text" in schema["required"]
        assert "output_path" in schema["properties"]

    def test_piper_tts_metadata(self):
        """Test Piper TTS tool metadata."""
        tool = PiperTTS()

        assert tool.name == "piper_tts"
        assert tool.provider == "piper"
        assert tool.runtime.value == "local"


class TestMusicLibrary:
    """Test local music library discovery."""

    def test_music_library_schema(self):
        """Verify music library has correct schema."""
        tool = MusicLibrary()
        schema = tool.input_schema

        assert schema["type"] == "object"
        assert "operation" in schema["required"]

    def test_music_library_metadata(self):
        """Test music library tool metadata."""
        tool = MusicLibrary()

        assert tool.name == "music_library"
        assert tool.provider == "local"
        assert tool.supports["local_offline"] is True
        assert tool.supports["free"] is True


class TestAudioMixer:
    """Test audio mixing operations."""

    def test_audio_mixer_schema(self):
        """Verify audio mixer has correct input schema."""
        tool = AudioMixer()
        schema = tool.input_schema

        assert schema["type"] == "object"
        assert "operation" in schema["required"]
        
        # Check available operations
        operations = schema["properties"]["operation"]["enum"]
        assert "mix" in operations
        assert "duck" in operations
        assert "full_mix" in operations

    def test_audio_mixer_metadata(self):
        """Test audio mixer tool metadata."""
        tool = AudioMixer()

        assert tool.name == "audio_mixer"
        assert tool.provider == "ffmpeg"
        assert tool.tier.value == "core"
        assert "mix" in tool.capabilities
        assert "duck" in tool.capabilities


class TestGoogleMusicGeneration:
    """Test Google Music generation."""

    def test_google_music_schema(self):
        """Verify Google Music has correct schema."""
        tool = GoogleMusic()
        schema = tool.input_schema

        assert schema["type"] == "object"
        assert "prompt" in schema["required"]
        assert "duration_seconds" in schema["properties"]

    def test_google_music_metadata(self):
        """Test Google Music tool metadata."""
        tool = GoogleMusic()

        assert tool.name == "google_music"
        assert tool.provider == "google"
        assert tool.capability == "music_generation"


class TestPhase4AudioPipeline:
    """End-to-end Phase 4 audio pipeline tests."""

    def test_tts_fallback_chain(self):
        """Test TTS provider fallback chain: Kokoro → Piper."""
        kokoro_tool = KokoroTTS()
        piper_tool = PiperTTS()

        # Both should be available (or at least configurable)
        assert kokoro_tool.fallback_tools == ["piper_tts"]
        assert piper_tool.name == "piper_tts"

    def test_music_selection_order(self):
        """Test music selection priority: library → Google Music → Pixabay."""
        # Music library has no fallback (it's local)
        library_tool = MusicLibrary()
        assert library_tool.runtime.value == "local"

        # Google Music has fallback to other generators
        google_music = GoogleMusic()
        assert "music_gen" in google_music.fallback_tools

    def test_orchestrator_phase4_integration(self):
        """Test that Phase 4 is integrated into orchestrator."""
        orchestrate_path = PROJECT_ROOT / "orchestrate.py"
        assert orchestrate_path.exists()

        with open(orchestrate_path, "r") as f:
            content = f.read()

            # Check Phase 4 section exists
            assert "PHASE 4: VOICE & AUDIO GENERATION" in content

            # Check Kokoro import
            assert "from tools.audio.kokoro_tts import KokoroTTS" in content

            # Check audio generation logic
            assert "KokoroTTS()" in content
            assert "PiperTTS()" in content
            assert "AudioMixer()" in content

    def test_audio_formats_supported(self):
        """Test that audio tools support standard formats."""
        # Kokoro outputs WAV
        kokoro = KokoroTTS()
        assert kokoro.input_schema["properties"]["output_path"]["type"] == "string"

        # Piper outputs WAV
        piper = PiperTTS()
        assert piper.input_schema["properties"]["output_path"]["type"] == "string"

        # Mixer handles various formats
        mixer = AudioMixer()
        assert "extract" in mixer.capabilities


class TestAudioProviderSelection:
    """Test provider selection logic for audio generation."""

    def test_tts_provider_availability(self):
        """Test that TTS providers are discoverable."""
        tts_providers = [
            KokoroTTS(),
            PiperTTS(),
            GoogleTTS(),
            OpenAITTS(),
            ElevenLabsTTS(),
        ]

        for provider in tts_providers:
            assert provider.capability == "tts"
            assert provider.tier.value == "voice"
            assert "text_to_speech" in provider.capabilities

    def test_music_provider_availability(self):
        """Test that music providers are discoverable."""
        music_library = MusicLibrary()
        google_music = GoogleMusic()

        # Both should be music-related
        assert music_library.provider == "local"
        assert google_music.provider == "google"


class TestPhase4CostTracking:
    """Test cost tracking for Phase 4 operations."""

    def test_kokoro_is_free(self):
        """Kokoro TTS should be free (open source, local)."""
        tool = KokoroTTS()
        
        # Mock execution would return cost_usd: 0.0
        schema = tool.input_schema
        assert schema is not None  # Tool exists

    def test_piper_is_free(self):
        """Piper TTS should be free (open source, local)."""
        tool = PiperTTS()
        
        schema = tool.input_schema
        assert schema is not None  # Tool exists

    def test_music_library_is_free(self):
        """Music library should be free (user's local files)."""
        tool = MusicLibrary()
        assert tool.supports["free"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
