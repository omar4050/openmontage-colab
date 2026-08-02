"""Quick test of transcription adapter with test audio."""
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.gen_test_audio import generate_sine_wave_audio
from src.adapters.transcriber_faster_whisper import FasterWhisperTranscriber

# Generate test audio
audio_file = generate_sine_wave_audio("tests/sample_audio.wav", duration=3.0)
print(f"Generated test audio: {audio_file}")

# Try to transcribe
trans = FasterWhisperTranscriber("faster-whisper")
print(f"Transcriber available: {trans.available}, backend: {trans._backend}")

if trans.available:
    try:
        result = trans.run(audio_file)
        print(f"Transcription result: {result}")
    except Exception as e:
        print(f"Transcription failed: {e}")
else:
    print("Transcriber not available on this machine")
