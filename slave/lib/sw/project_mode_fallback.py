"""Project Slave Master-liveness policy（10 秒失聯進入本機 Dev Mode）。"""

import time

from lib.sys.sys_bus import bus


def _ticks_ms():
    try:
        return time.ticks_ms()
    except AttributeError:
        return int(time.monotonic() * 1000)


def _ticks_diff(now, then):
    try:
        return time.ticks_diff(now, then)
    except AttributeError:
        return now - then


def arm_master_watch(now=None):
    """由 App 啟動時建立等待 Master 的共同起點。"""
    if now is None:
        now = _ticks_ms()
    bus.shared["master_watch_started_ms"] = int(now)
    bus.shared["master_seen_seq"] = 0
    bus.shared.pop("master_last_seen_ms", None)


def note_master_seen(now=None):
    """有效且通過本機 address filter 的 frame 才算 Master 在線。"""
    if now is None:
        now = _ticks_ms()
    bus.shared["master_last_seen_ms"] = int(now)
    bus.shared["master_seen_seq"] = int(
        bus.shared.get("master_seen_seq", 0) or 0) + 1


class ProjectModeFallback:
    """純狀態 policy；回傳 ``enter``／``leave`` edge，唔直接控制硬件。"""

    def __init__(self, timeout_ms=10000, ticks_diff=None):
        self.timeout_ms = max(1, int(timeout_ms))
        self._ticks_diff = ticks_diff or _ticks_diff
        self._started_at = 0
        self._last_master_at = None
        self.active = False

    def start(self, now):
        self._started_at = int(now)
        self._last_master_at = None
        self.active = False

    def note_master(self, now):
        self._last_master_at = int(now)
        if self.active:
            self.active = False
            return "leave"
        return None

    def poll(self, now):
        if self.active:
            return None
        baseline = (self._last_master_at if self._last_master_at is not None
                    else self._started_at)
        if self._ticks_diff(int(now), baseline) >= self.timeout_ms:
            self.active = True
            return "enter"
        return None
