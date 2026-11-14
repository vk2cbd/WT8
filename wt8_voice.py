"""Nonblocking offline voice annunciator for WT8 antenna state changes.

Requires espeak-ng (preferred) or espeak on Ubuntu. No speech command ever
blocks the GUI or antenna motion. The worker is daemonised and bounded.
"""
import queue
import shutil
import subprocess
import threading


class VoiceAnnunciator:
    def __init__(self):
        self.engine = shutil.which("espeak-ng") or shutil.which("espeak")
        self.muted = True  # Safe default: no unexpected announcements at startup.
        self.volume = 70
        self._lock = threading.Lock()
        self._queue = queue.Queue(maxsize=12)
        self._closed = False
        self._process = None
        self._thread = threading.Thread(target=self._run, daemon=True, name="WT8Voice")
        self._thread.start()

    def set_muted(self, muted):
        with self._lock:
            self.muted = bool(muted)
            if self.muted:
                self._clear_queue()
                if self._process is not None:
                    self._process.terminate()

    def set_volume(self, volume):
        with self._lock:
            self.volume = max(0, min(100, int(volume)))

    def say(self, message, force=False):
        if not self.engine:
            return False
        with self._lock:
            if self._closed or (self.muted and not force):
                return False
            try:
                self._queue.put_nowait((str(message), bool(force)))
                return True
            except queue.Full:
                return False

    def _clear_queue(self):
        while True:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break

    def _run(self):
        while True:
            item = self._queue.get()
            if item is None:
                break
            message, force = item
            with self._lock:
                if self._closed or (self.muted and not force):
                    continue
                volume = self.volume
                try:
                    self._process = subprocess.Popen(
                        [self.engine, "-v", "en+f3", "-a", str(round(volume * 2)), message],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    )
                except OSError:
                    self._process = None
            process = self._process
            if process is not None:
                process.wait()
            with self._lock:
                if self._process is process:
                    self._process = None

    def close(self):
        with self._lock:
            self._closed = True
            self._clear_queue()
            if self._process is not None:
                self._process.terminate()
        try:
            self._queue.put_nowait(None)
        except queue.Full:
            pass
