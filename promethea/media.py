"""Audio and video conversion using the separately bundled FFmpeg executable."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

from .convert import atomic_save
from .util import UserError, sibling

AUDIO_TARGETS = ("MP3", "WAV", "OGG", "OPUS", "M4A", "FLAC")
VIDEO_TARGETS = ("MP3", "WAV", "GIF", "MP4")


def ffmpeg_path() -> str:
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    candidate = root / "vendor" / "ffmpeg" / "bin" / ("ffmpeg.exe" if sys.platform == "win32" else "ffmpeg")
    if candidate.is_file():
        return str(candidate)
    fallback = shutil.which("ffmpeg")
    if fallback:
        return fallback
    # Finder and launchd apps often have a minimal PATH without Homebrew.
    if sys.platform == "darwin":
        for path in (Path("/opt/homebrew/bin/ffmpeg"), Path("/usr/local/bin/ffmpeg")):
            if path.is_file() and os.access(path, os.X_OK):
                return str(path)
        raise UserError("FFmpeg is missing. Install it with Homebrew to use audio and video conversion.")
    raise UserError("FFmpeg is missing. Reinstall PROMETHEA Drop to use audio and video conversion.")


@lru_cache(maxsize=4)
def _encoders(executable: str) -> frozenset[str]:
    try:
        result = subprocess.run([executable, "-hide_banner", "-encoders"],
                                capture_output=True, text=True, check=True,
                                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
    except (OSError, subprocess.SubprocessError):
        return frozenset()
    return frozenset(parts[1] for line in result.stdout.splitlines()
                     if len(parts := line.split()) >= 2 and len(parts[0]) == 6)


def targets(cat: str, ext: str) -> list[str]:
    available = AUDIO_TARGETS if cat == "audio" else VIDEO_TARGETS if cat == "video" else ()
    current = ext.lstrip(".").upper()
    return [target for target in available if target != current]


def convert(src: str | Path, cat: str, target: str) -> list[Path]:
    src, target = Path(src), target.upper()
    if target not in targets(cat, src.suffix):
        raise UserError("This media conversion is not supported")
    out = sibling(src, ext="." + target.lower())
    command = [ffmpeg_path(), "-hide_banner", "-nostdin", "-loglevel", "error", "-i", str(src)]
    available = _encoders(command[0])
    if target in AUDIO_TARGETS:
        command += ["-map", "0:a:0", "-vn", "-map_metadata", "0"]
        codecs = {"MP3": ["-c:a", "libmp3lame", "-q:a", "3", "-f", "mp3"],
                  "WAV": ["-c:a", "pcm_s16le", "-f", "wav"],
                  "OGG": ["-c:a", "libvorbis", "-q:a", "5", "-f", "ogg"],
                  "OPUS": ["-c:a", "libopus", "-b:a", "128k", "-f", "opus"],
                  "M4A": ["-c:a", "aac", "-b:a", "192k", "-f", "ipod"],
                  "FLAC": ["-c:a", "flac", "-f", "flac"]}
        if target == "OGG" and "libvorbis" not in available and "vorbis" in available:
            codecs["OGG"] = ["-c:a", "vorbis", "-strict", "experimental", "-ac", "2", "-q:a", "5", "-f", "ogg"]
        command += codecs[target]
    elif target == "GIF":
        command += ["-map", "0:v:0", "-an", "-vf", "fps=15,scale='min(720,iw)':-2:flags=lanczos", "-f", "gif"]
    else:
        video_encoder = next((name for name in ("libopenh264", "libx264", "h264_videotoolbox")
                              if name in available), "libopenh264")
        command += ["-map", "0:v:0", "-map", "0:a:0?", "-c:v", video_encoder, "-b:v", "4M",
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-f", "mp4"]

    def write(tmp):
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        try:
            result = subprocess.run(command + ["-y", str(tmp)], capture_output=True, creationflags=flags)
        except OSError as exc:
            raise UserError(f"Could not start FFmpeg: {exc}") from exc
        if result.returncode:
            error = result.stderr.decode("utf-8", "replace").strip()
            if "matches no streams" in error or "Stream map" in error:
                raise UserError("The file does not contain the required audio or video track")
            raise UserError("Could not convert this media file. Check that the file and its codecs are supported.")
    atomic_save(write, out)
    return [out]
