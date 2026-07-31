#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.audio.kokoro_tts import KokoroTTS

voice_text = Path('production_output/scripts/quick_test_voiceover.txt').read_text(encoding='utf-8')

tts = KokoroTTS()
res = tts.execute({
    'text': voice_text,
    'voice': 'en',
    'speed': 1.0,
    'output_path': str(Path('production_output/audio/quick_test_kokoro.wav'))
})
print('Success:', res.success)
print('Error:', res.error)
print('Data:', res.data)
