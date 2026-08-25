# -*- coding: utf-8 -*-
"""PixelMathMethod 大批量測試：大規模正確性 + 性能 + 準確度

三大部分，全在大資料量上跑：
  §1 大規模準確度 — 全相位 65536 點波形 + 全 hue×s×v 密集網格色彩，統計誤差
  §2 大規模性能   — bulk 色彩轉換在不同像素數（64/256/1024/2000）的每像素耗時與擴展
  §3 大規模正確性 — bulk==單值、值域、雙向 round-trip（密集網格）

用法:
  PC(CPython):  python test\\pixel\\test_pixel_bulk.py
  裝置(REPL):   import test_pixel_bulk; test_pixel_bulk.run()
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

import math
from array import array as _array

from lib.sw.PixelMathMethod import (
    _wave01_q12, _sin_q12,
    hsv_to_rgb8, rgb_to_hsv8, hsv_to_rgb12, rgb_to_hsv12,
    hsv_to_rgb8_buf, rgb_to_hsv8_buf, hsv_to_rgb12_buf, rgb_to_hsv12_buf,
)

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


def _fmt(v):
    if v >= 1000:
        return "{:.1f} ms".format(v / 1000.0)
    return "{:.1f} us".format(v)


# ════════════════════════════════════════════════════════
# 基準（reference）：浮點 math.sin + 標準 HSV↔RGB
# ════════════════════════════════════════════════════════
def ref_wave01_q12(phase):
    return int((math.sin(2.0 * math.pi * (phase & 65535) / 65536.0) + 1.0) / 2.0 * 4095.0)


def ref_sin_q12(phase):
    return int(math.sin(2.0 * math.pi * (phase & 65535) / 65536.0) * 4096.0)


def _ref_hsv_to_rgb(h, s, v, scale):
    h = h % 360
    sf, vf = s / scale, v / scale
    c = vf * sf
    x = c * (1.0 - abs((h / 60.0) % 2.0 - 1.0))
    m = vf - c
    if h < 60:
        rf, gf, bf = c, x, 0.0
    elif h < 120:
        rf, gf, bf = x, c, 0.0
    elif h < 180:
        rf, gf, bf = 0.0, c, x
    elif h < 240:
        rf, gf, bf = 0.0, x, c
    elif h < 300:
        rf, gf, bf = x, 0.0, c
    else:
        rf, gf, bf = c, 0.0, x
    return (int(round((rf + m) * scale)),
            int(round((gf + m) * scale)),
            int(round((bf + m) * scale)))


def _ref_rgb_to_hsv(r, g, b, scale):
    rf, gf, bf = r / scale, g / scale, b / scale
    mx = max(rf, gf, bf)
    mn = min(rf, gf, bf)
    delta = mx - mn
    v = mx
    if delta == 0.0:
        return 0, 0, int(round(v * scale))
    s = delta / mx
    if mx == rf:
        h = (gf - bf) / delta
    elif mx == gf:
        h = (bf - rf) / delta + 2.0
    else:
        h = (rf - gf) / delta + 4.0
    return int(round((h * 60.0) % 360.0)), int(round(s * scale)), int(round(v * scale))


def _hue_dist(a, b):
    d = abs(int(a) - int(b)) % 360
    return d if d <= 180 else 360 - d


# ════════════════════════════════════════════════════════
# §1 大規模準確度
# ════════════════════════════════════════════════════════
def _acc_wave():
    print("-- §1a 波形：全相位 65536 點 vs math.sin --")
    for fn, ref, name in ((_wave01_q12, ref_wave01_q12, "_wave01_q12"),
                          (_sin_q12, ref_sin_q12, "_sin_q12")):
        max_e = 0.0
        sum_e = 0.0
        sum_e2 = 0.0
        for p in range(65536):
            e = abs(fn(p) - ref(p))
            max_e = max(max_e, e)
            sum_e += e
            sum_e2 += e * e
        mean = sum_e / 65536
        rmse = math.sqrt(sum_e2 / 65536)
        print("  {}: 65536 點 max={:.2f} mean={:.4f} rmse={:.4f}".format(name, max_e, mean, rmse))


def _acc_color():
    print("-- §1b 色彩：密集網格 hue×s×v --")
    # 8-bit：hue 0-359, s 0..255 step 8 (33), v 0..255 step 8 (33) → 360*33*33 = 392040 點
    # 12-bit：hue 0-359, s 0..4095 step 128 (33), v 0..4095 step 128 (33) → 392040 點
    for scale, tag in ((255, "8-bit"), (4095, "12-bit")):
        if scale == 255:
            opt_h2r, ref_h2r = hsv_to_rgb8, lambda h, s, v: _ref_hsv_to_rgb(h, s, v, 255)
            opt_r2h, ref_r2h = rgb_to_hsv8, lambda r, g, b: _ref_rgb_to_hsv(r, g, b, 255)
            step = 8
        else:
            opt_h2r, ref_h2r = hsv_to_rgb12, lambda h, s, v: _ref_hsv_to_rgb(h, s, v, 4095)
            opt_r2h, ref_r2h = rgb_to_hsv12, lambda r, g, b: _ref_rgb_to_hsv(r, g, b, 4095)
            step = 128

        sv = list(range(0, scale + 1, step))
        n = 0
        max_e = 0.0
        sum_e = 0.0
        sum_e2 = 0.0
        for h in range(360):
            for s in sv:
                for v in sv:
                    o = opt_h2r(h, s, v)
                    r = ref_h2r(h, s, v)
                    e = max(abs(oi - ri) for oi, ri in zip(o, r))
                    max_e = max(max_e, e)
                    sum_e += e
                    sum_e2 += e * e
                    n += 1
        print("  hsv→rgb {}: {} 點 RGB誤差 max={:.2f} mean={:.4f} rmse={:.4f}".format(
            tag, n, max_e, sum_e / n, math.sqrt(sum_e2 / n)))

        # rgb→hsv：用 ref_h2r 生成 RGB，再反解，比 hue 角 + s/v
        n = 0
        h_max = 0.0
        h_sum = 0.0
        s_max = 0.0
        v_max = 0.0
        for h in range(360):
            for s in sv:
                for v in sv:
                    r, g, b = ref_h2r(h, s, v)
                    oh, os_, ov = opt_r2h(r, g, b)
                    rh, rs, rv = ref_r2h(r, g, b)
                    dh = _hue_dist(oh, rh)
                    h_max = max(h_max, dh)
                    h_sum += dh
                    s_max = max(s_max, abs(os_ - rs))
                    v_max = max(v_max, abs(ov - rv))
                    n += 1
        print("  rgb→hsv {}: {} 點 hue角 max={:.1f}° mean={:.4f}° | s誤差max={} v誤差max={}".format(
            tag, n, h_max, h_sum / n, s_max, v_max))


# ════════════════════════════════════════════════════════
# §2 大規模性能（bulk，不同像素數）
# ════════════════════════════════════════════════════════
def _perf_bulk():
    print("-- §2 bulk 性能：不同像素數的每像素耗時 --")
    sizes = (64, 256, 1024, 2000)
    loops = {64: 500, 256: 200, 1024: 50, 2000: 20}

    for name, fn in (("hsv→rgb 8", hsv_to_rgb8_buf),
                     ("rgb→hsv 8", rgb_to_hsv8_buf),
                     ("hsv→rgb 12", hsv_to_rgb12_buf),
                     ("rgb→hsv 12", rgb_to_hsv12_buf)):
        line = "  {:>12}:".format(name)
        for n in sizes:
            h_buf = _array('H', [i % 360 for i in range(n)])
            s_buf = _array('H', [255] * n)
            v_buf = _array('H', [255 - (i * 7) % 200 for i in range(n)])
            rgb8 = bytearray(n * 3)
            h_o = _array('H', [0] * n)
            s_o = _array('H', [0] * n)
            v_o = _array('H', [0] * n)
            out12 = _array('H', [0] * (n * 3))
            rgb12 = _array('H', [(i * 37) & 4095 for i in range(n * 3)])

            if fn is hsv_to_rgb8_buf:
                args = (h_buf, s_buf, v_buf, rgb8, n)
            elif fn is rgb_to_hsv8_buf:
                args = (rgb8, h_o, s_o, v_o, n)
            elif fn is hsv_to_rgb12_buf:
                args = (h_buf, s_buf, v_buf, out12, n)
            else:
                args = (rgb12, h_o, s_o, v_o, n)

            t0 = _ticks()
            for _ in range(loops[n]):
                fn(*args)
            dt = _diff(t0, _ticks())
            per_px = dt / (loops[n] * n)
            line += "  {}px: {:.2f}us/px".format(n, per_px)
        print(line)


# ════════════════════════════════════════════════════════
# §3 大規模正確性
# ════════════════════════════════════════════════════════
def _corr():
    print("-- §3 大規模正確性 --")
    # 3a. bulk == 單值（大 buffer）
    n = 512
    h_buf = _array('H', [(i * 53) % 360 for i in range(n)])
    s_buf = _array('H', [(i * 31) % 256 for i in range(n)])
    v_buf = _array('H', [(i * 17) % 256 for i in range(n)])
    out8 = bytearray(n * 3)
    hsv_to_rgb8_buf(h_buf, s_buf, v_buf, out8, n)
    ok = True
    for i in range(n):
        r, g, b = hsv_to_rgb8(h_buf[i], s_buf[i], v_buf[i])
        if (out8[i*3], out8[i*3+1], out8[i*3+2]) != (r, g, b):
            ok = False
            break
    print("  bulk==單值 (hsv→rgb8, {} px): {}".format(n, "\u2705" if ok else "\u274c"))

    # 3b. 值域（全相位 + 密集網格都落在範圍內）
    ok = all(0 <= _wave01_q12(p) <= 4095 for p in range(0, 65536, 13))
    ok = ok and all(-4096 <= _sin_q12(p) <= 4096 for p in range(0, 65536, 13))
    print("  波形值域 (0-4095 / ±4096): {}".format("\u2705" if ok else "\u274c"))

    # 3c. 雙向 round-trip（密集網格，8-bit）：驗證 RGB 還原度
    # 直接比 hue 角在低飽和度會誤報（delta 小時 ±1LSB 量化誤差放大 hue），
    # 故改比「hsv→rgb→hsv→rgb」兩次 RGB 是否一致（資訊保真）。
    ok = True
    worst = 0
    for h in range(0, 360, 5):
        for s in range(0, 256, 16):
            for v in range(0, 256, 16):
                r, g, b = hsv_to_rgb8(h, s, v)
                h2, s2, v2 = rgb_to_hsv8(r, g, b)
                r2, g2, b2 = hsv_to_rgb8(h2, s2, v2)
                e = max(abs(r2 - r), abs(g2 - g), abs(b2 - b))
                worst = max(worst, e)
                if e > 4:   # 兩次整數轉換的累積上界 ≈ 4 LSB（單次 ≤2 LSB）
                    ok = False
                    break
            if not ok:
                break
        if not ok:
            break
    print("  雙向 round-trip 8-bit（RGB 還原）: {} (worst={} LSB)".format(
        "\u2705" if ok else "\u274c", worst))


def run():
    print("=== PixelMathMethod 大批量測試（正確性 + 性能 + 準確度）===")
    _acc_wave()
    _acc_color()
    _perf_bulk()
    _corr()
    print("--- 完成 ---")


if __name__ == "__main__":
    run()
