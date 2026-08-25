# -*- coding: utf-8 -*-
"""PixelMathMethod bulk 吞吐量基準 — 每秒 RGB 轉換次數

核心：驗證「for loop 在 viper 裡面」的極限。測的是整條 buffer 一次處理（bulk），
不是 Python 迴圈逐 pixel call viper。理想結果：每秒數十萬次 RGB 轉換。

四個方向 × 兩套位深：
  hsv→rgb 8 / rgb→hsv 8 / hsv→rgb 12 / rgb→hsv 12

輸出：每秒轉換次數（px/s），與 50fps × 2000 px = 100k px/s 需求對照。

用法:
  PC(CPython):  python test\\pixel\\bench_pixel_throughput.py
  裝置(REPL):   import bench_pixel_throughput; bench_pixel_throughput.run()
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

from array import array as _array

from lib.sw.PixelMathMethod import (
    hsv_to_rgb8_buf, rgb_to_hsv8_buf, hsv_to_rgb12_buf, rgb_to_hsv12_buf,
)

if IS_MICROPYTHON:
    import time
    def _ticks():
        return time.ticks_us()
    def _diff(a, b):
        return time.ticks_diff(b, a)
    _SEC = 1_000_000
else:
    import time as _time
    def _ticks():
        return _time.perf_counter()
    def _diff(a, b):
        return int((b - a) * 1_000_000)
    _SEC = 1_000_000


def _fmt_rate(px_per_sec):
    if px_per_sec >= 1_000_000:
        return "{:.2f} M px/s".format(px_per_sec / 1_000_000)
    if px_per_sec >= 1_000:
        return "{:.0f} k px/s".format(px_per_sec / 1_000)
    return "{:.0f} px/s".format(px_per_sec)


def run():
    print("=== bulk 吞吐量：每秒 RGB 轉換次數（loop 在 viper 內）===")
    if IS_MICROPYTHON:
        print("（viper 路徑，代表性數據）")
    else:
        print("（PC 純 Python 對照，非代表性；裝置 viper 才是極限）")

    n = 2000                        # 對齊目標 pixel 數
    # 目標：50 FPS × 2000 px = 100k px/s
    print("需求對照：50 FPS × 2000 px = 100 k px/s（每方向都應遠超）\n")

    # 準備 buffer（一次，測試前）
    h_buf = _array('H', [i % 360 for i in range(n)])
    s_buf = _array('H', [255] * n)
    v_buf = _array('H', [255 - (i * 7) % 200 for i in range(n)])
    rgb8 = bytearray(n * 3)
    h_o = _array('H', [0] * n)
    s_o = _array('H', [0] * n)
    v_o = _array('H', [0] * n)
    out12 = _array('H', [0] * (n * 3))
    rgb12 = _array('H', [(i * 37) & 4095 for i in range(n * 3)])

    cases = (
        ("hsv→rgb 8", hsv_to_rgb8_buf, (h_buf, s_buf, v_buf, rgb8, n)),
        ("rgb→hsv 8", rgb_to_hsv8_buf, (rgb8, h_o, s_o, v_o, n)),
        ("hsv→rgb 12", hsv_to_rgb12_buf, (h_buf, s_buf, v_buf, out12, n)),
        ("rgb→hsv 12", rgb_to_hsv12_buf, (rgb12, h_o, s_o, v_o, n)),
    )

    # 每 case 測一個固定總轉換量，量大到計時穩定
    # 總轉換量 = n * loops；loops 依位深調整讓單 case 在 ~1 秒內
    loops = 200
    for name, fn, args in cases:
        # warmup
        for _ in range(20):
            fn(*args)
        t0 = _ticks()
        for _ in range(loops):
            fn(*args)
        dt = _diff(t0, _ticks())
        total_px = n * loops
        px_per_sec = total_px * _SEC // dt if dt > 0 else 0
        per_px = dt / total_px
        print("  {:>12}: {} px / {:.0f} ms → {}   ({:.2f} µs/px)".format(
            name, total_px, dt / 1000.0, _fmt_rate(px_per_sec), per_px))

    print("\n--- 完成 ---")


if __name__ == "__main__":
    run()
