# -*- coding: utf-8 -*-
"""PixelMathMethod / Effect 效能基準測試

量測：
  1. _wave01_q12 單值吞吐（viper 多項式逼近，裝置上為 viper；PC 為純 Python 對照）
  2. pattern_value_at 單值吞吐（走 pattern 分派）
  3. Effect.frame 完整幀吞吐（64 pixel、eyes 波形，含空間分布迴圈）
  4. 對照：math.sin 全幀（僅供參考，正式路徑不用浮點）

判讀：看「每幀時間」與「每值時間」，對照 40 FPS 目標（一幀預算 = 25000us @40fps）。
裝置上 viper 逼近應遠快於 math.sin；PC 上純 Python 版只當邏輯對照、不具裝置代表性。

用法:
  PC(CPython):  python test\\pixel\\bench_pixel_math.py
  裝置(REPL):   import bench_pixel_math; bench_pixel_math.run()
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
        return int((b - a) * 1_000_000)   # 秒 → 微秒


from lib.sw.PixelMathMethod import mt, _wave01_q12
from pixel.effects import effects

# eyes 的 program（畫波範例；單一真源在 effects.json，此處複製一份當測試固定輸入）
EYES_PROGRAM = [
    {"type": "keep",     "F": 1, "l_max": 0,    "l_lim": 0,   "phi": 0,    "end_Time": 60},
    {"type": "math_now", "F": 5, "l_max": 100,  "l_lim": 20,  "phi": 3071, "end_Time": 100},
    {"type": "math_now", "F": 5, "l_max": 1023, "l_lim": 100, "phi": 3071, "end_Time": 200},
    {"type": "math_now", "F": 5, "l_max": 1023, "l_lim": 200, "phi": 1023, "end_Time": 320},
]

def _fmt(v, unit="us"):
    if v >= 1000:
        return "{:.1f} ms".format(v / 1000.0)
    if v >= 1:
        return "{:.1f} {}".format(v, unit)
    return "{:.2f} {}".format(v, unit)


def run():
    print("=== PixelMathMethod / Effect 效能 ===")

    # 1. _wave01_q12 單值吞吐
    N = 20000
    t0 = _ticks()
    acc = 0
    for i in range(N):
        acc += _wave01_q12((i * 7919) & 65535)
    dt = _diff(t0, _ticks())
    print("[_wave01_q12] {} 值 / {} → {}/值 (acc={})".format(
        N, _fmt(dt), _fmt(dt / N), acc))

    # 2. value_at（預編譯後）單值吞吐
    comp = mt.compile(EYES_PROGRAM)
    N2 = 20000
    total = comp[-1][1]
    t0 = _ticks()
    acc = 0
    for i in range(N2):
        acc += mt.value_at(comp, i % total)
    dt = _diff(t0, _ticks())
    print("[value_at 預編譯] {} 值 / {} → {}/值 (acc={})".format(
        N2, _fmt(dt), _fmt(dt / N2), acc))

    # 3. Effect.frame 完整幀（64 pixel、eyes）—— 畫波效果用內建 Effect
    eff = effects.Effect("eyes", {"pixel_n": 64, "program": EYES_PROGRAM,
                                  "step": 1, "spacing": 10, "offset": 0,
                                  "speed": 1, "reverse": False})
    FRAMES = 2000
    t0 = _ticks()
    for _ in range(FRAMES):
        eff.frame(_)
    dt = _diff(t0, _ticks())
    per_frame = dt / FRAMES
    print("[Effect.frame] {} 幀 (64px) / {} → {}/幀".format(
        FRAMES, _fmt(dt), _fmt(per_frame)))
    if per_frame > 0:
        print("            理論上限 ≈ {:.0f} FPS  (40 FPS 預算 = 25000us/幀)".format(
            1_000_000 / per_frame))

    # 4. 對照：math.sin 全幀（僅 PC 參考，正式路徑不用浮點）
    if not IS_MICROPYTHON:
        import math
        t0 = _ticks()
        acc = 0
        for i in range(N):
            acc += int((math.sin(2 * math.pi * ((i * 7919) & 65535) / 65536.0) + 1) / 2 * 4095)
        dt = _diff(t0, _ticks())
        print("[math.sin 對照] {} 值 / {} → {}/值 (僅參考，非正式路徑)".format(
            N, _fmt(dt), _fmt(dt / N)))

    print("--- 完成（裝置上 viper 才是代表性數據；PC 為純 Python 對照）---")


if __name__ == "__main__":
    run()
