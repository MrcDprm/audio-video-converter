"""Dosya bilgisi: ffprobe ile süre, çözünürlük ve codec'ler okunur.

ffprobe'un çıktısı dosyanın içeriğinden gelir; körü körüne güvenilmez, sadece beklenen
türdeki alanlar alınır.
"""
import json
import math
import subprocess

from app_info import NO_WINDOW

PROBE_TIMEOUT_SECONDS = 30


class ProbeError(Exception):
    """Dosya okunamadı. code, i18n'deki mesajın anahtarıdır."""

    def __init__(self, code):
        super().__init__(code)
        self.code = code


def _positive_number(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and number > 0 else None


def _positive_int(value):
    return value if isinstance(value, int) and not isinstance(value, bool) and value > 0 else None


def _text(value):
    return value if isinstance(value, str) and value else None


def parse_probe(data):
    """ffprobe'un JSON çıktısından gereken bilgileri seçer."""
    if not isinstance(data, dict):
        raise ProbeError("not_media")
    streams = data.get("streams") if isinstance(data.get("streams"), list) else []
    file_format = data.get("format") if isinstance(data.get("format"), dict) else {}

    video = audio = None
    for stream in streams:
        if not isinstance(stream, dict):
            continue
        disposition = stream.get("disposition") if isinstance(stream.get("disposition"), dict) else {}
        # MP3'lerdeki albüm kapağı da "video" görünür; gerçek görüntü sayılmaz
        if stream.get("codec_type") == "video" and video is None and not disposition.get("attached_pic"):
            video = stream
        elif stream.get("codec_type") == "audio" and audio is None:
            audio = stream

    duration = _positive_number(file_format.get("duration"))
    if duration is None or (video is None and audio is None):
        raise ProbeError("not_media")  # resim, metin ya da boş dosya
    return {
        "duration": duration,
        "video_codec": _text(video.get("codec_name")) if video else None,
        "width": _positive_int(video.get("width")) if video else None,
        "height": _positive_int(video.get("height")) if video else None,
        "audio_codec": _text(audio.get("codec_name")) if audio else None,
        "channels": _positive_int(audio.get("channels")) if audio else None,
    }


def probe(ffprobe, path):
    command = [ffprobe, "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)]
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=PROBE_TIMEOUT_SECONDS, creationflags=NO_WINDOW,
        )
    except subprocess.TimeoutExpired:
        raise ProbeError("not_media") from None
    except OSError:
        raise ProbeError("ffmpeg_missing") from None
    if result.returncode != 0:
        raise ProbeError("not_media")
    try:
        data = json.loads(result.stdout)
    except ValueError:
        raise ProbeError("not_media") from None
    return parse_probe(data)