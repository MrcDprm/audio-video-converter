"""Bir dönüştürmeyi ffmpeg süreciyle çalıştırır, ilerlemeyi bildirir ve iptal edilebilir.

Arayüzden bağımsızdır: run() bitene kadar bekler, bu yüzden arayüz onu ayrı bir iş parçacığında çağırır.
"""
import collections
import subprocess
import threading
import time
from pathlib import Path

from app_info import NO_WINDOW
from progress import ProgressParser, remaining_seconds

# ffmpeg'in hata çıktısındaki ifadeler → kullanıcıya gösterilecek mesajın anahtarı
ERROR_PATTERNS = (
    ("No space left on device", "disk_full"),
    ("Permission denied", "permission"),
    ("Invalid data found", "not_media"),
)


def classify_error(stderr_lines):
    text = "\n".join(stderr_lines)
    for pattern, code in ERROR_PATTERNS:
        if pattern in text:
            return code
    return "failed"


class Conversion:
    def __init__(self, command, target, duration, on_progress=None):
        self.command = command
        self.target = Path(target)
        self.duration = duration
        self.on_progress = on_progress  # (yüzde, kalan saniye ya da None)
        self.process = None
        self.cancelled = False
        self.stderr = collections.deque(maxlen=20)  # sadece son satırlar tutulur

    def _read_stderr(self):
        for line in self.process.stderr:
            self.stderr.append(line.rstrip())

    def run(self):
        """Dönüştürür; "done", "cancelled" ya da bir hata anahtarı döner."""
        try:
            self.process = subprocess.Popen(
                self.command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, encoding="utf-8", errors="replace", creationflags=NO_WINDOW,
            )
        except OSError:
            return "ffmpeg_missing"
        if self.cancelled:  # iptal, süreç tam başlarken basıldıysa
            self.process.terminate()
        # Hata çıktısı ayrıca okunmazsa tampon dolar ve ffmpeg takılı kalır
        reader = threading.Thread(target=self._read_stderr, daemon=True)
        reader.start()

        parser = ProgressParser(self.duration)
        started = time.monotonic()
        for line in self.process.stdout:
            if parser.feed(line) and self.on_progress:
                percent = parser.percent
                self.on_progress(percent, remaining_seconds(percent, time.monotonic() - started))
        self.process.wait()
        reader.join(timeout=2)

        if self.cancelled:
            self._remove_partial_output()
            return "cancelled"
        if self.process.returncode != 0:
            self._remove_partial_output()
            return classify_error(self.stderr)
        return "done"

    def cancel(self):
        self.cancelled = True
        if self.process and self.process.poll() is None:
            self.process.terminate()

    def _remove_partial_output(self):
        try:
            self.target.unlink(missing_ok=True)
        except OSError:
            pass