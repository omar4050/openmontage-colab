"""Artifact validators for images, audio, and video.

These attempt lightweight checks without adding heavy new dependencies. They
try layered strategies: stdlib (imghdr, wave), Pillow if available, and
ffprobe when ffmpeg is installed.
"""
from pathlib import Path
import imghdr
import os
import subprocess
import json


def is_valid_image(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return {"valid": False, "reason": "missing"}
    if p.stat().st_size == 0:
        return {"valid": False, "reason": "zero_size"}

    # try PIL for more thorough checks
    try:
        from PIL import Image
        with Image.open(p) as im:
            im.verify()
            return {"valid": True, "width": im.width, "height": im.height, "format": im.format}
    except Exception:
        pass

    # fallback: use imghdr
    kind = imghdr.what(p)
    if kind:
        return {"valid": True, "format": kind}

    return {"valid": False, "reason": "unknown_or_corrupt_image"}


def is_valid_audio(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return {"valid": False, "reason": "missing"}
    if p.stat().st_size == 0:
        return {"valid": False, "reason": "zero_size"}

    # try WAV via stdlib wave
    try:
        import wave
        with wave.open(str(p), "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            duration = frames / float(rate) if rate else None
            return {"valid": True, "format": "wav", "duration_s": duration}
    except Exception:
        pass

    # try ffprobe for many audio formats
    try:
        cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration,format_name", "-print_format", "json", str(p)]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
        if res.returncode == 0 and res.stdout:
            info = json.loads(res.stdout)
            fmt = info.get("format", {})
            duration = float(fmt.get("duration", 0.0)) if fmt.get("duration") else None
            return {"valid": True, "format": fmt.get("format_name"), "duration_s": duration}
    except Exception:
        pass

    return {"valid": False, "reason": "unsupported_or_corrupt_audio"}


def is_valid_video(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return {"valid": False, "reason": "missing"}
    if p.stat().st_size == 0:
        return {"valid": False, "reason": "zero_size"}

    # try ffprobe to check streams and duration
    try:
        cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-show_streams", "-print_format", "json", str(p)]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if res.returncode == 0 and res.stdout:
            info = json.loads(res.stdout)
            fmt = info.get("format", {})
            streams = info.get("streams", [])
            duration = float(fmt.get("duration", 0.0)) if fmt.get("duration") else None
            has_video = any(s.get("codec_type") == "video" for s in streams)
            has_audio = any(s.get("codec_type") == "audio" for s in streams)
            if has_video:
                return {"valid": True, "duration_s": duration, "has_audio": has_audio}
    except Exception:
        pass

    # try moviepy if available
    try:
        from moviepy.editor import VideoFileClip
        clip = VideoFileClip(str(p))
        dur = clip.duration
        clip.reader.close()
        if hasattr(clip, "audio") and clip.audio:
            clip.audio.reader.close_proc()
        return {"valid": True, "duration_s": dur}
    except Exception:
        pass

    return {"valid": False, "reason": "unsupported_or_corrupt_video"}
