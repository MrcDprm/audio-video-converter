import tempfile
import unittest
from pathlib import Path
from unittest import mock

import storage
from settings import SETTINGS_FILE, clean_settings, default_settings, load_settings, save_settings


class TestSettings(unittest.TestCase):
    """Testler gerçek kullanıcı klasörüne değil geçici bir klasöre yazar."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        patcher = mock.patch.object(storage, "DATA_DIR", Path(self.temp.name))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.temp.cleanup)

    def test_defaults(self):
        self.assertEqual(load_settings(), default_settings())

    def test_save_and_load(self):
        settings = {"lang": "en", "theme": "light", "format": "mp3", "quality": "high",
                    "resolution": "720p", "fast": False, "output_dir": "C:\\Videos"}
        save_settings(settings)
        self.assertEqual(load_settings(), settings)

    def test_invalid_values_fall_back(self):
        data = {"lang": "de", "theme": 1, "format": "exe", "quality": "max", "resolution": "4k",
                "fast": "yes", "output_dir": "x" * 1000, "extra": True}
        self.assertEqual(clean_settings(data), default_settings())

    def test_broken_file(self):
        (Path(self.temp.name) / SETTINGS_FILE).write_text("{not json", encoding="utf-8")
        self.assertEqual(load_settings(), default_settings())


if __name__ == "__main__":
    unittest.main()
