"""Çıktı formatları, kalite ve çözünürlük seçenekleri.

Kullanıcı codec adı değil format seçer. Her formatın hangi codec'lerle kodlandığı ve hangi kaynak
codec'lerin yeniden kodlanmadan kopyalanabileceği (hızlı mod) burada tanımlıdır.
"""


def output_format(label, kind, extension, video_codec, audio_codec, copy_video=(), copy_audio=()):
    return {
        "label": label,
        "kind": kind,  # "video" ya da "audio"
        "extension": extension,
        "video_codec": video_codec,
        "audio_codec": audio_codec,
        "copy_video": set(copy_video),  # bu codec'lerdeki görüntü kopyalanabilir
        "copy_audio": set(copy_audio),
    }


FORMATS = {
    "mp4": output_format("MP4 (H.264)", "video", ".mp4", "libx264", "aac", ("h264", "hevc"), ("aac", "mp3")),
    "mkv": output_format(
        "MKV (H.264)", "video", ".mkv", "libx264", "aac",
        ("h264", "hevc", "vp9", "av1"), ("aac", "mp3", "opus", "vorbis", "flac", "ac3", "eac3"),
    ),
    "webm": output_format("WebM (VP9)", "video", ".webm", "libvpx-vp9", "libopus", ("vp8", "vp9", "av1"), ("opus", "vorbis")),
    "mov": output_format("MOV (H.264)", "video", ".mov", "libx264", "aac", ("h264", "hevc"), ("aac",)),
    "mp3": output_format("MP3", "audio", ".mp3", None, "libmp3lame", copy_audio=("mp3",)),
    "m4a": output_format("M4A (AAC)", "audio", ".m4a", None, "aac", copy_audio=("aac",)),
    "wav": output_format("WAV", "audio", ".wav", None, "pcm_s16le", copy_audio=("pcm_s16le",)),
    "flac": output_format("FLAC", "audio", ".flac", None, "flac", copy_audio=("flac",)),
    "ogg": output_format("OGG (Opus)", "audio", ".ogg", None, "libopus", copy_audio=("opus", "vorbis")),
}

# crf: H.264 kalite ayarı (düşük sayı = daha iyi kalite, daha büyük dosya); vp9_crf aynısının VP9 karşılığı
QUALITIES = {
    "low": {"crf": 28, "vp9_crf": 40, "audio_bitrate": "128k"},
    "medium": {"crf": 23, "vp9_crf": 33, "audio_bitrate": "192k"},
    "high": {"crf": 18, "vp9_crf": 24, "audio_bitrate": "320k"},
}

RESOLUTIONS = {"original": None, "1080p": 1080, "720p": 720, "480p": 480}

LOSSLESS_AUDIO = {"pcm_s16le", "flac"}  # bit hızı ayarı olmayan codec'ler

# Dosya seçme penceresindeki filtre; asıl kontrolü ffprobe yapar
INPUT_EXTENSIONS = (
    ".mp4", ".mkv", ".mov", ".avi", ".webm", ".wmv", ".flv", ".m4v", ".mpg", ".mpeg", ".ts", ".3gp",
    ".mp3", ".m4a", ".aac", ".wav", ".flac", ".ogg", ".opus", ".wma",
)