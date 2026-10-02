"""Gerçek ffmpeg ile uçtan uca testler. ffmpeg yüklü değilse atlanır.

Test dosyaları ffmpeg'in kendi deneme kaynaklarıyla (renkli görüntü + sinüs sesi) geçici klasörde üretilir.
"""
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path

from app_info import NO_WINDOW, find_tool
from command import build_command, output_path
from probe import ProbeError, probe
from runner import Conversion

FFMPEG, FFPROBE = find_tool("ffmpeg"), find_tool("ffprobe")


def make_sample(path, seconds, video=True):
    inputs = ["-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}"]
    if video:
        inputs = ["-f", "lavfi", "-i", f"testsrc2=size=1280x720:rate=30:duration={seconds}"] + inputs
    subprocess.run([FFMPEG, "-v", "error", "-y", *inputs, "-c:v", "libx264", "-preset", "ultrafast", "-shortest",
                    str(path)], check=True, creationflags=NO_WINDOW)


@unittest.skipUnless(FFMPEG and FFPROBE, "ffmpeg is not installed")
class TestRunner(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.folder = Path(cls.temp.name)
        cls.video = cls.folder / "örnek video.mkv"  # Türkçe karakter ve boşluk bilerek
        cls.long_video = cls.folder / "uzun.mkv"
        cls.audio = cls.folder / "şarkı.mp3"
        make_sample(cls.video, 3)
        make_sample(cls.long_video, 30)
        make_sample(cls.audio, 3, video=False)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def convert(self, source, format_key, **options):
        info = probe(FFPROBE, source)
        target = output_path(source, format_key)
        updates = []
        command = build_command(FFMPEG, source, target, info, format_key, **options)
        result = Conversion(command, target, info["duration"], lambda *args: updates.append(args)).run()
        return result, target, updates

    def test_probe(self):
        info = probe(FFPROBE, self.video)
        self.assertEqual((info["video_codec"], info["width"], info["height"]), ("h264", 1280, 720))
        self.assertAlmostEqual(info["duration"], 3, delta=0.2)
        self.assertIsNone(probe(FFPROBE, self.audio)["video_codec"])

    def test_probe_rejects_non_media(self):
        text_file = self.folder / "not-a-video.mp4"
        text_file.write_text("hello", encoding="utf-8")
        for path in (text_file, self.folder / "missing.mp4"):
            with self.subTest(path=path.name):
                with self.assertRaises(ProbeError):
                    probe(FFPROBE, path)

    def test_video_conversions(self):
        for format_key, options in (("mp4", {}), ("webm", {"resolution": "480p", "quality": "low"})):
            with self.subTest(format_key=format_key):
                result, target, updates = self.convert(self.video, format_key, **options)
                self.assertEqual(result, "done")
                self.assertTrue(updates)
                self.assertEqual(updates[-1][0], 100)
                info = probe(FFPROBE, target)
                expected_height = 480 if options.get("resolution") == "480p" else 720
                self.assertEqual(info["height"], expected_height)

    def test_audio_conversions(self):
        for format_key, codec in (("mp3", "mp3"), ("m4a", "aac"), ("wav", "pcm_s16le"), ("flac", "flac"),
                                  ("ogg", "opus")):
            with self.subTest(format_key=format_key):
                result, target, _ = self.convert(self.video, format_key, fast=False)
                self.assertEqual(result, "done")
                self.assertEqual(probe(FFPROBE, target)["audio_codec"], codec)

    def test_cancel_removes_partial_file(self):
        info = probe(FFPROBE, self.long_video)
        target = output_path(self.long_video, "mkv")
        command = build_command(FFMPEG, self.long_video, target, info, "mkv", quality="high", fast=False)
        conversion = Conversion(command, target, info["duration"])
        threading.Timer(0.5, conversion.cancel).start()
        self.assertEqual(conversion.run(), "cancelled")
        self.assertFalse(target.exists())

    def test_missing_ffmpeg(self):
        target = self.folder / "never.mp4"
        conversion = Conversion([str(self.folder / "no-ffmpeg.exe"), "-i", "x"], target, 1)
        self.assertEqual(conversion.run(), "ffmpeg_missing")


if __name__ == "__main__":
    unittest.main()
