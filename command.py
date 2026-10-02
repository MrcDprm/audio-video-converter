"""ffmpeg komutunu oluşturur: hangi akış kopyalanacak (hızlı mod), hangisi yeniden kodlanacak,
kalite ve çözünürlük. Sadece argüman listesi döndürür, çalıştırmaz; bu yüzden test edilir.
"""
from pathlib import Path

from presets import FORMATS, LOSSLESS_AUDIO, QUALITIES, RESOLUTIONS

MP3_MAX_CHANNELS = 2


class CommandError(ValueError):
    """Bu dosya bu formata dönüştürülemez. code, i18n'deki mesajın anahtarıdır."""

    def __init__(self, code):
        super().__init__(code)
        self.code = code


def output_path(source, format_key, folder=None):
    """Çıktı dosyasının yolu. Var olan dosyanın (ve kaynağın) üzerine yazılmaz: "video (1).mp4"."""
    source = Path(source)
    folder = Path(folder) if folder else source.parent
    extension = FORMATS[format_key]["extension"]
    candidate = folder / f"{source.stem}{extension}"
    number = 1
    while candidate.exists() or candidate.resolve() == source.resolve():
        candidate = folder / f"{source.stem} ({number}){extension}"
        number += 1
    return candidate


def needs_scaling(info, resolution):
    max_height = RESOLUTIONS[resolution]
    return bool(max_height and info["height"] and info["height"] > max_height)


def video_arguments(info, output, quality, resolution, fast):
    if fast and info["video_codec"] in output["copy_video"] and not needs_scaling(info, resolution):
        arguments = ["-c:v", "copy"]
        if info["video_codec"] == "hevc" and output["extension"] in (".mp4", ".mov"):
            arguments += ["-tag:v", "hvc1"]  # Apple cihazları H.265'i bu etiketle tanır
        return arguments
    settings = QUALITIES[quality]
    if output["video_codec"] == "libvpx-vp9":
        arguments = ["-c:v", "libvpx-vp9", "-crf", str(settings["vp9_crf"]), "-b:v", "0",
                     "-deadline", "good", "-cpu-used", "4", "-row-mt", "1"]
    else:
        arguments = ["-c:v", "libx264", "-preset", "medium", "-crf", str(settings["crf"])]
    if needs_scaling(info, resolution):
        arguments += ["-vf", f"scale=-2:{RESOLUTIONS[resolution]}"]  # -2: genişlik orantılı ve çift sayı
    return arguments + ["-pix_fmt", "yuv420p"]  # her oynatıcının açabildiği renk biçimi


def audio_arguments(info, output, quality, fast):
    if fast and info["audio_codec"] in output["copy_audio"]:
        return ["-c:a", "copy"]
    arguments = ["-c:a", output["audio_codec"]]
    if output["audio_codec"] not in LOSSLESS_AUDIO:
        arguments += ["-b:a", QUALITIES[quality]["audio_bitrate"]]
    if output["audio_codec"] == "libmp3lame" and (info["channels"] or 0) > MP3_MAX_CHANNELS:
        arguments += ["-ac", str(MP3_MAX_CHANNELS)]  # MP3 en fazla stereo olabilir
    return arguments


def build_command(ffmpeg, source, target, info, format_key, quality="medium", resolution="original", fast=True):
    output = FORMATS[format_key]
    if output["kind"] == "video" and not info["video_codec"]:
        raise CommandError("no_video")
    if not info["audio_codec"] and output["kind"] == "audio":
        raise CommandError("no_audio")

    # Yollar her zaman tam yol verilir: "-" ile başlayan bir dosya adı seçenek sanılmasın
    command = [ffmpeg, "-hide_banner", "-nostdin", "-loglevel", "error", "-i", str(Path(source).resolve())]
    if output["kind"] == "video":
        command += ["-map", "0:v:0"] + video_arguments(info, output, quality, resolution, fast)
    if info["audio_codec"]:
        command += ["-map", "0:a:0"] + audio_arguments(info, output, quality, fast)
    if output["extension"] in (".mp4", ".mov", ".m4a"):
        command += ["-movflags", "+faststart"]  # internette ve oynatıcılarda hemen açılsın
    return command + ["-progress", "pipe:1", "-nostats", "-y", str(Path(target).resolve())]