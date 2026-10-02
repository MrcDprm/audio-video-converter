import tempfile
import unittest
from pathlib import Path

from command import CommandError, build_command, output_path
from presets import FORMATS

VIDEO = {"duration": 20.0, "video_codec": "h264", "width": 1920, "height": 1080, "audio_codec": "aac", "channels": 2}
AUDIO = {"duration": 15.0, "video_codec": None, "width": None, "height": None, "audio_codec": "mp3", "channels": 2}


def build(info, format_key, **options):
    return build_command("ffmpeg", "in.mkv", "out" + FORMATS[format_key]["extension"], info, format_key, **options)


def value_after(command, flag):
    return command[command.index(flag) + 1]


class TestBuildCommand(unittest.TestCase):
    def test_fast_mode_copies_compatible_streams(self):
        command = build(VIDEO, "mp4")
        self.assertEqual(value_after(command, "-c:v"), "copy")
        self.assertEqual(value_after(command, "-c:a"), "copy")

    def test_fast_mode_off_re_encodes(self):
        command = build(VIDEO, "mp4", fast=False, quality="high")
        self.assertEqual(value_after(command, "-c:v"), "libx264")
        self.assertEqual(value_after(command, "-crf"), "18")
        self.assertEqual(value_after(command, "-c:a"), "aac")
        self.assertEqual(value_after(command, "-b:a"), "320k")

    def test_incompatible_codec_is_re_encoded(self):
        command = build(VIDEO, "webm")
        self.assertEqual(value_after(command, "-c:v"), "libvpx-vp9")
        self.assertEqual(value_after(command, "-c:a"), "libopus")

    def test_scaling_disables_copy_and_keeps_aspect_ratio(self):
        command = build(VIDEO, "mp4", resolution="720p")
        self.assertEqual(value_after(command, "-c:v"), "libx264")
        self.assertEqual(value_after(command, "-vf"), "scale=-2:720")

    def test_video_is_never_upscaled(self):
        small = {**VIDEO, "height": 480, "width": 854}
        command = build(small, "mp4", resolution="720p")
        self.assertEqual(value_after(command, "-c:v"), "copy")
        self.assertNotIn("-vf", command)

    def test_hevc_copied_to_mp4_gets_apple_tag(self):
        command = build({**VIDEO, "video_codec": "hevc"}, "mp4")
        self.assertEqual(value_after(command, "-tag:v"), "hvc1")

    def test_audio_from_video_drops_the_picture(self):
        command = build(VIDEO, "mp3")
        self.assertNotIn("0:v:0", command)
        self.assertEqual(value_after(command, "-c:a"), "libmp3lame")

    def test_lossless_audio_has_no_bitrate(self):
        for format_key in ("wav", "flac"):
            with self.subTest(format_key=format_key):
                self.assertNotIn("-b:a", build(AUDIO, format_key))

    def test_surround_sound_is_mixed_down_for_mp3(self):
        command = build({**VIDEO, "audio_codec": "ac3", "channels": 6}, "mp3")
        self.assertEqual(value_after(command, "-ac"), "2")

    def test_video_without_audio(self):
        command = build({**VIDEO, "audio_codec": None, "channels": None}, "mp4")
        self.assertNotIn("0:a:0", command)

    def test_impossible_conversions(self):
        with self.assertRaises(CommandError) as context:
            build(AUDIO, "mp4")
        self.assertEqual(context.exception.code, "no_video")
        with self.assertRaises(CommandError) as context:
            build({**VIDEO, "audio_codec": None}, "mp3")
        self.assertEqual(context.exception.code, "no_audio")

    def test_safe_arguments(self):
        command = build_command("ffmpeg", "-y.mkv", "-out.mp4", VIDEO, "mp4")
        self.assertIn("-nostdin", command)
        # Tire ile başlayan dosya adları tam yola çevrilir; seçenek sanılmaz
        self.assertTrue(Path(value_after(command, "-i")).is_absolute())
        self.assertTrue(Path(command[-1]).is_absolute())
        self.assertEqual(value_after(command, "-progress"), "pipe:1")


class TestOutputPath(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def test_existing_files_are_not_overwritten(self):
        source = self.folder / "video.mkv"
        source.touch()
        self.assertEqual(output_path(source, "mp4").name, "video.mp4")
        (self.folder / "video.mp4").touch()
        (self.folder / "video (1).mp4").touch()
        self.assertEqual(output_path(source, "mp4").name, "video (2).mp4")

    def test_source_is_never_the_target(self):
        source = self.folder / "song.mp3"
        source.touch()
        self.assertEqual(output_path(source, "mp3").name, "song (1).mp3")

    def test_custom_folder(self):
        other = self.folder / "out"
        other.mkdir()
        target = output_path(self.folder / "clip.mov", "webm", other)
        self.assertEqual(target, other / "clip.webm")


if __name__ == "__main__":
    unittest.main()
