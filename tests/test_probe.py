import unittest

from i18n import media_summary
from probe import ProbeError, parse_probe


def ffprobe_output(streams, duration="20.5"):
    return {"streams": streams, "format": {"duration": duration}}


VIDEO_STREAM = {"codec_type": "video", "codec_name": "h264", "width": 1920, "height": 1080}
AUDIO_STREAM = {"codec_type": "audio", "codec_name": "aac", "channels": 2}


class TestParseProbe(unittest.TestCase):
    def test_video_file(self):
        info = parse_probe(ffprobe_output([VIDEO_STREAM, AUDIO_STREAM]))
        self.assertEqual(info, {
            "duration": 20.5, "video_codec": "h264", "width": 1920, "height": 1080,
            "audio_codec": "aac", "channels": 2,
        })
        self.assertEqual(media_summary(info), "1920×1080 · H.264 · AAC · 0:20")

    def test_album_cover_is_not_video(self):
        cover = {**VIDEO_STREAM, "codec_name": "mjpeg", "disposition": {"attached_pic": 1}}
        info = parse_probe(ffprobe_output([{**AUDIO_STREAM, "codec_name": "mp3"}, cover]))
        self.assertIsNone(info["video_codec"])
        self.assertEqual(media_summary(info), "MP3 · 0:20")

    def test_first_stream_of_each_kind_is_used(self):
        second = {**AUDIO_STREAM, "codec_name": "ac3", "channels": 6}
        info = parse_probe(ffprobe_output([VIDEO_STREAM, AUDIO_STREAM, second]))
        self.assertEqual(info["audio_codec"], "aac")

    def test_unexpected_values_are_ignored(self):
        odd_video = {"codec_type": "video", "codec_name": 5, "width": "wide", "height": True}
        odd_audio = {"codec_type": "audio", "codec_name": "", "channels": -2}
        info = parse_probe(ffprobe_output([odd_video, odd_audio, "junk", None]))
        self.assertEqual(
            (info["video_codec"], info["width"], info["height"], info["audio_codec"], info["channels"]),
            (None, None, None, None, None),
        )

    def test_not_media(self):
        cases = [
            None,
            [],
            {"streams": "x", "format": []},
            ffprobe_output([]),
            ffprobe_output([VIDEO_STREAM], duration=None),
            ffprobe_output([VIDEO_STREAM], duration="N/A"),
            ffprobe_output([VIDEO_STREAM], duration="0"),
            ffprobe_output([VIDEO_STREAM], duration="inf"),
            ffprobe_output([{"codec_type": "subtitle"}]),
        ]
        for data in cases:
            with self.subTest(data=data):
                with self.assertRaises(ProbeError) as context:
                    parse_probe(data)
                self.assertEqual(context.exception.code, "not_media")


if __name__ == "__main__":
    unittest.main()
