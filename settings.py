"""Kullanıcı ayarları: dil, tema, format, kalite, çözünürlük, hızlı mod ve kayıt klasörü.

Dosyadan okunan değerlere güvenilmez; bilinmeyen ya da bozuk değer yerine varsayılan kullanılır.
"""
from presets import FORMATS, QUALITIES, RESOLUTIONS
from storage import load_json, save_json

SETTINGS_FILE = "settings.json"
LANGUAGES = ("tr", "en")
THEMES = ("dark", "light")
MAX_PATH_LENGTH = 500


def default_settings():
    return {
        "lang": "tr", "theme": "dark", "format": "mp4", "quality": "medium",
        "resolution": "original", "fast": True, "output_dir": None,
    }


def clean_settings(data):
    settings = default_settings()
    if not isinstance(data, dict):
        return settings
    for key, allowed in (("lang", LANGUAGES), ("theme", THEMES), ("format", FORMATS),
                         ("quality", QUALITIES), ("resolution", RESOLUTIONS)):
        if data.get(key) in allowed:
            settings[key] = data[key]
    if isinstance(data.get("fast"), bool):
        settings["fast"] = data["fast"]
    output_dir = data.get("output_dir")
    if isinstance(output_dir, str) and 0 < len(output_dir) <= MAX_PATH_LENGTH:
        settings["output_dir"] = output_dir
    return settings


def load_settings():
    return clean_settings(load_json(SETTINGS_FILE, None))


def save_settings(settings):
    save_json(SETTINGS_FILE, settings)
