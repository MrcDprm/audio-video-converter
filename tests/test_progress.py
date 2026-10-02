import unittest

from progress import ProgressParser, format_duration, remaining_seconds
from runner import classify_error


class TestProgressParser(unittest.TestCase):
    def test_blocks(self):
        parser = ProgressParser(duration=20)
        self.assertFalse(parser.feed("frame=100\n"))
        self.assertFalse(parser.feed("out_time_us=5000000\n"))
        self.assertTrue(parser.feed("progress=continue\n"))
        self.assertEqual(parser.percent, 25)

    def test_not_available_values_are_skipped(self):
        parser = ProgressParser(duration=10)
        parser.feed("out_time_us=N/A")
        parser.feed("out_time_us=-30000")
        self.assertEqual(parser.percent, 0)

    def test_only_end_means_done(self):
        parser = ProgressParser(duration=10)
        parser.feed("out_time_us=10500000")
        parser.feed("progress=continue")
        self.assertEqual(parser.percent, 99.9)
        parser.feed("progress=end")
        self.assertEqual(parser.percent, 100)

    def test_unknown_duration(self):
        parser = ProgressParser(duration=None)
        parser.feed("out_time_us=5000000")
        self.assertEqual(parser.percent, 0)


class TestTime(unittest.TestCase):
    def test_remaining_seconds(self):
        self.assertEqual(remaining_seconds(25, 10), 30)
        self.assertIsNone(remaining_seconds(0.5, 10))
        self.assertIsNone(remaining_seconds(50, 0.2))

    def test_format_duration(self):
        cases = [(0, "0:00"), (5.4, "0:05"), (65, "1:05"), (3725, "1:02:05"), (-3, "0:00")]
        for seconds, expected in cases:
            with self.subTest(seconds=seconds):
                self.assertEqual(format_duration(seconds), expected)


class TestClassifyError(unittest.TestCase):
    def test_known_errors(self):
        cases = [
            (["av_interleaved_write_frame(): No space left on device"], "disk_full"),
            (["C:/out.mp4: Permission denied"], "permission"),
            (["in.mp4: Invalid data found when processing input"], "not_media"),
            (["Something else went wrong"], "failed"),
            ([], "failed"),
        ]
        for lines, code in cases:
            with self.subTest(lines=lines):
                self.assertEqual(classify_error(lines), code)


if __name__ == "__main__":
    unittest.main()
