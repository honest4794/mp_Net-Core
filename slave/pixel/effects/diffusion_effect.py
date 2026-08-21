"""
diffusion_effect.py — 舊專案 main.py 直接進入的「擴散」燈效移植

舊 main.py (temp/1) 最後一行：
    ledC.run_Pattern(diffusion_init, run_time=300*64, debug=1)

diffusion_init 由三組引擎合成（RGB_IO GPIO14 共 64 顆，H=0/S=0 → 灰階亮度波）：
  group A: only_rgb_io[8] + only_rgb_io[16] → stepping_wave_next(2, eyes_start1, step=40)
  group B: only_rgb_io[:8]                   → stepping_engine_list_next(8, p, [(5,1),(3,1),(2,1),(1,5)])
  group C: only_rgb_io[24:24+8]              → overlay(16, p, [(5,1),(3,1),(2,1),(1,5)], overlay=5, gap=10)

本類別把三引擎合成進單一 Effect：frame(t) 直接算 64 顆亮度，
輸出 array('H') 192 個值（R,G,B 依序，灰階 R=G=B），
由 PixelTask 用 write:"rgb" scatter 到 matrix.full（64 顆）。

波形段語義對齊舊 is_math_pattern_next(stop=True)：
  keep    : 恆定 l_lim + (l_max - l_lim)
  math_now: A=(l_max-l_lim)/2 的正弦 + A，再加 l_lim（0..l_max）
  phi     : 0-4095 對應 0-360°

stepping_engine 精確模擬（舊程式語義）：
  每個 pulse (hold, rep)：寫亮點 → 前進一格 → yield hold 幀；重複 rep 次。
  所以亮點「慢走（hold 大）→ 快走（hold 小）」交錯循環。
"""

import math
from array import array as _array

_PI2 = 6.283185307179586


def _build_wave(pattern):
    """pattern → 單輪波形 list[int]（舊 stop=True 的語義）。"""
    out = []
    run_time = 0
    for seg in pattern:
        run_fs = seg["end_Time"] - run_time
        run_time = seg["end_Time"]
        l_max = seg["l_max"]
        l_lim = seg["l_lim"]
        l_range = l_max - l_lim
        kind = seg["type"]
        if kind == "keep":
            out.extend([l_lim + l_range] * run_fs)
        elif kind == "math_now":
            A = l_range / 2.0
            F = seg["F"]
            phi = seg["phi"] / 4095.0 * 360.0
            ph0 = math.radians(phi)
            for i in range(run_fs):
                t = i / run_fs
                y = A * math.sin(_PI2 * F * t + ph0) + A
                out.append(int(y) + l_lim)
        else:
            raise ValueError("diffusion 不支援波形段 type={!r}".format(kind))
    return out


class _StepEngine:
    """stepping_engine_list_next 單引擎（舊語義精確模擬）。

    狀態跨幀：pulse_i（pulse_list 索引）、stepping（亮點位置）、
    hold_left（本 repeat 輪剩餘 yield 幀）、repeat_left（剩餘 repeat 輪）、
    val（當前亮度）、hist_i（波表游標）。
    """

    def __init__(self, led_no, hist, pulse_list):
        self.led_no = led_no
        self.hist = hist
        self.pulses = list(pulse_list)
        self.pos = 0
        self.pulse_i = 0
        self.hold_left = 0
        self.repeat_left = 0
        self.hold = 0
        self.val = 0
        self.hist_i = 0

    def step(self):
        """推進一幀 → 本幀亮點位置（舊 tempbuf 中 val 的位置）。"""
        if self.hold_left == 0 and self.repeat_left == 0:
            # 開始新 pulse：取波值
            self.hold, rep = self.pulses[self.pulse_i]
            self.pulse_i = (self.pulse_i + 1) % len(self.pulses)
            self.val = self.hist[self.hist_i % len(self.hist)]
            self.hist_i += 1
            self.repeat_left = rep
        lit = self.pos
        self.pos = (self.pos + 1) % self.led_no
        self.hold_left += 1
        if self.hold_left >= self.hold:
            self.hold_left = 0
            self.repeat_left -= 1
        return lit


# ── 波表 module 級快取：import 時（主線程）算好，thread 內零計算 ──
# PixelTask 在 Core 1（_thread）實例化 effect；math.sin 在 thread 內執行
# 有崩潰風險（ESP32 MicroPython 浮點 + thread 堆疊）。故波表在 import
# 時一次性算好（主線程），之後 __init__ 只做 index 讀取。
_WAVE_CACHE = {}


def _get_wave(key, pattern):
    """取波表；已算過直接回傳（避免 thread 內重算）。"""
    if key not in _WAVE_CACHE:
        _WAVE_CACHE[key] = _build_wave(pattern)
    return _WAVE_CACHE[key]


class diffusion:
    """舊專案「擴散」燈效：三引擎合成 64 顆 RGB（灰階）。

    不繼承 Effect（有自己的合成邏輯），但實作同一套接口：
    __next__ / restart / seek / release，供 PixelTask 播放端使用。
    """

    EYES_START1 = [
        {"type": "math_now", "F": 10, "l_max": 500, "l_lim": 0, "phi": 3071, "end_Time": 300},
    ]
    P_WAVE = [
        {"type": "keep", "F": 1, "l_max": 110, "l_lim": 0, "phi": 0, "end_Time": 16},
    ]
    PULSE_LIST = [(5, 1), (3, 1), (2, 1), (1, 5)]

    def __init__(self, name, params=None):
        self.name = name
        params = params or {}
        self.pixel_n = int(params.get("pixel_n", params.get("num_leds", 64)))
        self._t = 0
        # RGB 通道流：R,G,B 依序（灰階 R=G=B）
        self._buf = _array('H', [0] * (self.pixel_n * 3))

        # 波表：module 快取（import 時主線程已算好，thread 內零計算）
        self._wave_eyes = _get_wave("eyes", self.EYES_START1)
        self._wave_p = _get_wave("p", self.P_WAVE)

        # group B 引擎（8 顆）
        self._engB = _StepEngine(8, self._wave_p, self.PULSE_LIST)
        # group C 引擎 ×5（16 顆），各自 delay = i*10 幀
        self._engC = []
        for i in range(5):
            e = _StepEngine(16, self._wave_p, self.PULSE_LIST)
            e.delay = i * 10
            self._engC.append(e)
        self._ov_step = 0

    def _clear(self):
        for i in range(len(self._buf)):
            self._buf[i] = 0

    def _set_px(self, idx, val):
        if 0 <= idx < self.pixel_n:
            o = idx * 3
            self._buf[o] = val
            self._buf[o + 1] = val
            self._buf[o + 2] = val

    def frame(self, t):
        self._clear()
        n = self.pixel_n

        # group A: 位置 8、16，stepping_wave(2, eyes_start1, step=40)
        wl = len(self._wave_eyes)
        step_ct = t % wl
        self._set_px(8, self._wave_eyes[(step_ct * 40 + 0) % wl])
        self._set_px(16, self._wave_eyes[(step_ct * 40 + 1) % wl])

        # group B: 引擎每幀推進，亮點寫入（位置 0-7）
        litB = self._engB.step()
        self._set_px(litB, 110)

        # group C: 5 引擎錯開（overlay）。舊專案 led_no=16 但 GPIO 只映射
        # 前 8 格（only_rgb_io[24:32]）：亮點在 0-7 顯示、8-15 隱藏區不顯示。
        for e in self._engC:
            if self._ov_step >= e.delay:
                litC = e.step()
                if litC < 8:
                    self._set_px(24 + litC, 110)
        self._ov_step += 1

        return self._buf

    def restart(self):
        self._t = 0
        self._engB = _StepEngine(8, self._wave_p, self.PULSE_LIST)
        self._engC = []
        for i in range(5):
            e = _StepEngine(16, self._wave_p, self.PULSE_LIST)
            e.delay = i * 10
            self._engC.append(e)
        self._ov_step = 0

    def seek(self, t):
        self.restart()
        self._t = int(t)

    def __next__(self):
        b = self.frame(self._t)
        self._t += 1
        return b

    def release(self):
        pass
