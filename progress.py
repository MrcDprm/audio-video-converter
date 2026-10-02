"""ffmpeg'in "-progress" çıktısını okur. Çıktı "out_time_us=1500000" gibi satırlardan oluşur ve
her blok "progress=continue" (ya da sonda "progress=end") satırıyla biter.
"""


class ProgressParser:
    def __init__(self, duration):
        self.duration = duration  # saniye
        self.position = 0.0
        self.finished = False

    def feed(self, line):
        """Bir satır işler; bir blok bittiyse (ekran güncellenmeli) True döner."""
        key, _, value = line.strip().partition("=")
        if key == "out_time_us":
            try:
                self.position = max(0.0, int(value) / 1_000_000)
            except ValueError:  # başta "N/A" gelebilir
                pass
        elif key == "progress":
            self.finished = value == "end"
            return True
        return False

    @property
    def percent(self):
        if self.finished:
            return 100.0
        if not self.duration:
            return 0.0
        return min(99.9, self.position / self.duration * 100)


def remaining_seconds(percent, elapsed):
    """Şimdiye kadarki hıza göre kalan süre; ilk anlarda tahmin yapılmaz."""
    if percent < 1 or elapsed < 1:
        return None
    return elapsed * (100 - percent) / percent


def format_duration(seconds):
    """3725 → "1:02:05", 65 → "1:05"."""
    seconds = max(0, round(seconds))
    hours, rest = divmod(seconds, 3600)
    minutes, seconds = divmod(rest, 60)
    return f"{hours}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes}:{seconds:02d}"