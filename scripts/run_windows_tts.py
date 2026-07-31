#!/usr/bin/env python3
import pyttsx3
from pathlib import Path

text = Path('production_output/scripts/quick_test_voiceover.txt').read_text(encoding='utf-8')
engine = pyttsx3.init()
# Use a slower rate for clarity
rate = engine.getProperty('rate')
engine.setProperty('rate', int(rate * 0.9))
# Select a voice if available (0 is usually a male voice)
voices = engine.getProperty('voices')
if voices:
    engine.setProperty('voice', voices[0].id)

out_path = Path('production_output/audio/quick_test_tts.wav')
engine.save_to_file(text, str(out_path))
engine.runAndWait()
print('Wrote TTS to', out_path)
