"""Generate a simple test audio file (sine wave with spoken text simulation)."""
import struct
import math
from pathlib import Path

def generate_sine_wave_audio(filename: str, duration: float = 3.0, frequency: float = 440.0, sample_rate: int = 16000):
    """Generate a simple sine wave WAV file (test fixture)."""
    out = Path(filename)
    out.parent.mkdir(parents=True, exist_ok=True)
    
    num_samples = int(sample_rate * duration)
    
    # Create WAV header (minimal valid WAV)
    channels = 1
    bytes_per_sample = 2
    byte_rate = sample_rate * channels * bytes_per_sample
    block_align = channels * bytes_per_sample
    
    wav_header = bytearray()
    wav_header.extend(b'RIFF')
    wav_header.extend(struct.pack('<I', 36 + num_samples * bytes_per_sample))
    wav_header.extend(b'WAVE')
    wav_header.extend(b'fmt ')
    wav_header.extend(struct.pack('<I', 16))  # subchunk1 size
    wav_header.extend(struct.pack('<H', 1))   # audio format (PCM)
    wav_header.extend(struct.pack('<H', channels))
    wav_header.extend(struct.pack('<I', sample_rate))
    wav_header.extend(struct.pack('<I', byte_rate))
    wav_header.extend(struct.pack('<H', block_align))
    wav_header.extend(struct.pack('<H', 16))  # bits per sample
    wav_header.extend(b'data')
    wav_header.extend(struct.pack('<I', num_samples * bytes_per_sample))
    
    # Generate audio data (sine wave)
    audio_data = bytearray()
    max_amplitude = 32767
    for i in range(num_samples):
        t = i / sample_rate
        # vary frequency slightly for a more natural sound
        freq = frequency + 10 * math.sin(2 * math.pi * 0.5 * t)
        sample = int(max_amplitude * 0.3 * math.sin(2 * math.pi * freq * t))
        audio_data.extend(struct.pack('<h', sample))
    
    with open(out, 'wb') as f:
        f.write(wav_header)
        f.write(audio_data)
    
    return str(out)

if __name__ == '__main__':
    path = generate_sine_wave_audio('tests/sample_audio.wav', duration=5.0, frequency=440.0)
    print(f"Generated test audio: {path}")
