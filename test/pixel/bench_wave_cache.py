# -*- coding: utf-8 -*-
"""波緩衝（wave cache）對照基準測試

驗證「啟動即算、off 即丟、重啟重算」策略是否划算：
  1. compile() 成本（一次性、極小）
  2. 一次性算整條波 array('H') 的成本（= 啟動效果的初始化成本）
  3. 現況：Effect.frame 每幀每 pixel 現算 value_at
  4. 提案：預算波緩衝後，frame 只做 index + 加法 + 取模（_fill_from_wave）
  5. 波緩衝記憶體佔用（gc.mem_free 前後差）
  6. 損益平衡：一次性成本 ÷ 每幀省下的時間 = 幾幀回本

核心事實：波長 = program[-1].end_Time（eyes=320 幀），與 pixel 數無關。
整條波只需算 total 次，之後每一幀每一 pixel 都是 index 讀取。

用法:
  PC(CPython):  python test\\pixel\\bench_wave_cache.py
  裝置(REPL):   import bench_wave_cache; bench_wave_cache.run()
"""
import sys

IS_MICROPYTHON = (getattr(sys, "implementation", None)
                  and sys.implementation.name == "micropython")

if not IS_MICROPYTHON:
    import os
    _HERE = os.path.dirname(os.path.abspath(__file__))
    _ROOT = os.path.dirname(os.path.dirname(_HERE))
    _SLAVE = os.path.join(_ROOT, "slave")
    if _SLAVE not in sys.path:
        sys.path.insert(0, _SLAVE)

if IS_MICROPYTHON:
    import time
    def _ticks():
        return time.ticks_us()
    def _diff(a, b):
        return time.ticks_diff(b, a)
else:
    import time as _time
    def _ticks():
        return _time.perf_counter()
    def _diff(a, b):
        return int((b - a) * 1_000_000)

import gc
from array import array as _array

from lib.sw.PixelMathMethod import mt
from pixel.effects import effects

# eyes 的 program（畫波範例；單一真源在 effects.json，此處複製一份當測試固定輸入）
EYES_PROGRAM = [
    {"type": "keep",     "F": 1, "l_max": 0,    "l_lim": 0,   "phi": 0,    "end_Time": 60},
    {"type": "math_now", "F": 5, "l_max": 100,  "l_lim": 20,  "phi": 3071, "end_Time": 100},
    {"type": "math_now", "F": 5, "l_max": 1023, "l_lim": 100, "phi": 3071, "end_Time": 200},
    {"type": "math_now", "F": 5, "l_max": 1023, "l_lim": 200, "phi": 1023, "end_Time": 320},
]


def _fmt(v):
    if v >= 1000:
        return "{:.1f} ms".format(v / 1000.0)
    if v >= 1:
        return "{:.1f} us".format(v)
    return "{:.2f} us".format(v)


def _fill_from_wave(wave, total, n, g0, spacing, reverse=False):
    """提案的 frame 迴圈（純 Python）：index + 加法 + 取模，不碰 sin。"""
    buf = _array('H', [0] * n)
    g = g0
    if reverse:
        for i in range(n):
            buf[n - 1 - i] = wave[g % total]
            g += spacing
    else:
        for i in range(n):
            buf[i] = wave[g % total]
            g += spacing
    return buf


def run():
    print("=== 波緩衝對照基準 ===")
    total = EYES_PROGRAM[-1]["end_Time"]
    n = 64                       # 當前矩陣 pixel 數
    spacing = 10
    print("波長 total={} 幀 | pixel_n={} | spacing={}".format(total, n, spacing))

    # 1. compile 成本
    t0 = _ticks()
    comp = mt.compile(EYES_PROGRAM)
    dt = _diff(t0, _ticks())
    print("[compile] {}".format(_fmt(dt)))

    # 2. 一次性算整條波（array('H')）
    gc.collect()
    mem_before = gc.mem_free() if IS_MICROPYTHON else 0
    t0 = _ticks()
    wave = _array('H', [mt.value_at(comp, x) for x in range(total)])
    dt = _diff(t0, _ticks())
    gc.collect()
    mem_after = gc.mem_free() if IS_MICROPYTHON else 0
    print("[一次性算波] {} 幀 / {} → 啟動初始化成本（算一次）".format(total, _fmt(dt)))
    if IS_MICROPYTHON:
        print("             波緩衝記憶體 = {} bytes".format(mem_before - mem_after))
    else:
        print("             波緩衝記憶體 ≈ {} bytes（array('H') × total；裝置上測）".format(total * 2))

    # 3. 現況：每幀現算 value_at（Effect.frame 的核心）
    FR = 1000
    t0 = _ticks()
    for t in range(FR):
        g0 = t * 1   # speed=1, step=1
        for i in range(n):
            mt.value_at(comp, g0 + i * spacing)
    dt = _diff(t0, _ticks())
    per_frame_now = dt / FR
    print("[現況 每幀現算] {} 幀 / {} → {}/幀".format(FR, _fmt(dt), _fmt(per_frame_now)))

    # 4. 提案：預算波後 index 讀取
    t0 = _ticks()
    for t in range(FR):
        _fill_from_wave(wave, total, n, t, spacing)
    dt = _diff(t0, _ticks())
    per_frame_cached = dt / FR
    print("[提案 波緩衝 index] {} 幀 / {} → {}/幀".format(FR, _fmt(dt), _fmt(per_frame_cached)))

    # 5. 損益平衡：一次性成本 ÷ 每幀省下時間
    t0 = _ticks()
    _array('H', [mt.value_at(comp, x) for x in range(total)])
    one_time_us = _diff(t0, _ticks())
    saved_per_frame = per_frame_now - per_frame_cached
    if saved_per_frame > 0:
        breakeven = one_time_us / saved_per_frame
        print("[損益平衡] 一次性 {} / 每幀省 {} → 約 {} 幀回本".format(
            _fmt(one_time_us), _fmt(saved_per_frame), int(breakeven)))
    else:
        print("[損益平衡] 每幀省時 ≤ 0，波緩衝無收益")

    print("--- 完成（裝置上 viper 才是代表性數據）---")


if __name__ == "__main__":
    run()
