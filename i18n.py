"""Arayüz metinleri (Türkçe / İngilizce) ve dosya bilgisinin kısa yazımı."""
from progress import format_duration

MESSAGES = {
    "tr": {
        "app_name": "Ses ve Video Dönüştürücü",
        "add_files": "＋  Dosya ekle",
        "remove": "Kaldır",
        "clear": "Listeyi temizle",
        "drop_hint": "Dosyaları buraya sürükle ya da “Dosya ekle”ye tıkla",
        "drop_hint_sub": "Video: MP4, MKV, MOV, AVI, WebM…   Ses: MP3, WAV, FLAC, M4A…",
        "col_file": "Dosya",
        "col_info": "Bilgi",
        "col_status": "Durum",
        "format": "Format",
        "quality": "Kalite",
        "quality_low": "Düşük (küçük dosya)",
        "quality_medium": "Orta",
        "quality_high": "Yüksek",
        "resolution": "Çözünürlük",
        "resolution_original": "Orijinal",
        "fast_mode": "Mümkünse yeniden kodlamadan kopyala (çok hızlı)",
        "output_folder": "Kayıt yeri",
        "same_folder": "Kaynak dosyanın klasörü",
        "change": "Değiştir…",
        "use_source": "Kaynakla aynı",
        "convert": "Dönüştür",
        "cancel": "Durdur",
        "open_folder": "Klasörü aç",
        "status_probing": "Okunuyor…",
        "status_ready": "Bekliyor",
        "status_converting": "%{percent}",
        "status_remaining": "%{percent} · {time} kaldı",
        "status_done": "✓ Tamamlandı",
        "status_cancelled": "Durduruldu",
        "error_not_media": "Ses ya da video dosyası değil",
        "error_ffmpeg_missing": "FFmpeg bulunamadı",
        "error_no_video": "Görüntü yok; bir ses formatı seç",
        "error_no_audio": "Bu dosyada ses yok",
        "error_disk_full": "Disk dolu",
        "error_permission": "Klasöre yazma izni yok",
        "error_output_missing": "Kayıt klasörü bulunamadı",
        "error_failed": "Dönüştürülemedi",
        "summary_running": "{current} / {total} dosya",
        "summary_done": "{count} dosya dönüştürüldü",
        "summary_failed": "{count} dosya dönüştürülemedi",
        "summary_stopped": "Durduruldu",
        "theme": "Tema",
        "language": "English",
        "about": "Hakkında",
        "version": "Sürüm {version}",
        "about_text": "Python ve Tkinter ile yazılmış ses ve video dönüştürücü. Dönüştürme işini FFmpeg yapar.",
        "ffmpeg_credit": "FFmpeg, FFmpeg geliştiricilerinin projesidir (GPL).",
        "view_on_github": "GitHub'da görüntüle",
        "ffmpeg_missing_text": "FFmpeg bulunamadı. Uygulamayı yeniden kurmayı dene.",
        "quit_text": "Dönüştürme sürüyor. Çıkarsan yarım kalan dosya silinir. Çıkılsın mı?",
        "select_files": "Dönüştürülecek dosyaları seç",
        "select_folder": "Kayıt klasörünü seç",
        "filter_media": "Ses ve video dosyaları",
        "filter_all": "Tüm dosyalar",
        "unexpected_error": "Beklenmeyen bir hata oluştu. Uygulama çalışmaya devam ediyor.",
    },
    "en": {
        "app_name": "Audio Video Converter",
        "add_files": "＋  Add files",
        "remove": "Remove",
        "clear": "Clear list",
        "drop_hint": "Drop files here or click “Add files”",
        "drop_hint_sub": "Video: MP4, MKV, MOV, AVI, WebM…   Audio: MP3, WAV, FLAC, M4A…",
        "col_file": "File",
        "col_info": "Info",
        "col_status": "Status",
        "format": "Format",
        "quality": "Quality",
        "quality_low": "Low (small file)",
        "quality_medium": "Medium",
        "quality_high": "High",
        "resolution": "Resolution",
        "resolution_original": "Original",
        "fast_mode": "Copy without re-encoding when possible (very fast)",
        "output_folder": "Save to",
        "same_folder": "Same folder as the source file",
        "change": "Change…",
        "use_source": "Same as source",
        "convert": "Convert",
        "cancel": "Stop",
        "open_folder": "Open folder",
        "status_probing": "Reading…",
        "status_ready": "Waiting",
        "status_converting": "{percent}%",
        "status_remaining": "{percent}% · {time} left",
        "status_done": "✓ Done",
        "status_cancelled": "Stopped",
        "error_not_media": "Not an audio or video file",
        "error_ffmpeg_missing": "FFmpeg not found",
        "error_no_video": "No video; choose an audio format",
        "error_no_audio": "This file has no audio",
        "error_disk_full": "Disk is full",
        "error_permission": "No permission to write to the folder",
        "error_output_missing": "Output folder not found",
        "error_failed": "Could not convert",
        "summary_running": "{current} of {total} files",
        "summary_done": "{count} files converted",
        "summary_failed": "{count} files failed",
        "summary_stopped": "Stopped",
        "theme": "Theme",
        "language": "Türkçe",
        "about": "About",
        "version": "Version {version}",
        "about_text": "An audio and video converter written in Python and Tkinter. The conversion is done by FFmpeg.",
        "ffmpeg_credit": "FFmpeg is a project of the FFmpeg developers (GPL).",
        "view_on_github": "View on GitHub",
        "ffmpeg_missing_text": "FFmpeg was not found. Try reinstalling the app.",
        "quit_text": "A conversion is running. If you quit, the unfinished file is deleted. Quit anyway?",
        "select_files": "Choose files to convert",
        "select_folder": "Choose the output folder",
        "filter_media": "Audio and video files",
        "filter_all": "All files",
        "unexpected_error": "An unexpected error occurred. The app keeps running.",
    },
}

CODEC_NAMES = {
    "h264": "H.264", "hevc": "H.265", "vp8": "VP8", "vp9": "VP9", "av1": "AV1", "mpeg4": "MPEG-4",
    "mpeg2video": "MPEG-2", "wmv2": "WMV", "aac": "AAC", "mp3": "MP3", "opus": "Opus", "vorbis": "Vorbis",
    "flac": "FLAC", "ac3": "AC-3", "eac3": "E-AC-3", "wmav2": "WMA", "pcm_s16le": "PCM", "pcm_s24le": "PCM",
}


def translate(lang, key, **params):
    text = MESSAGES.get(lang, MESSAGES["en"]).get(key) or MESSAGES["en"].get(key, key)
    return text.format(**params) if params else text


def codec_name(codec):
    return CODEC_NAMES.get(codec, codec.upper()[:12])


def media_summary(info):
    """"1920×1080 · H.264 · AAC · 2:35" ya da ses için "MP3 · 3:12"."""
    parts = []
    if info["video_codec"]:
        if info["width"] and info["height"]:
            parts.append(f"{info['width']}×{info['height']}")
        parts.append(codec_name(info["video_codec"]))
    if info["audio_codec"]:
        parts.append(codec_name(info["audio_codec"]))
    parts.append(format_duration(info["duration"]))
    return " · ".join(parts)
