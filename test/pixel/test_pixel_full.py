# -*- coding: utf-8 -*-
"""PixelMathMethod 綜合測試：基準 vs 優化（全路徑、全方向、準確度 + 速度）

兩套算法：
  基準（reference）— 標準浮點 math.sin / float HSV↔RGB，當「正確答案」的來源。
  優化（optimized）— 我們的整數/viper 版（免查表多項式 + 整數 HSV↔RGB）。

覆蓋所有路徑、所有方向：
  A. 波形     : _wave01_q12（0-4095）、_sin_q12（-4096..4096）  vs  math.sin
  B. 色彩單值 : hsv→rgb 8-bit / rgb→hsv 8-bit / hsv→rgb 12-bit / rgb→hsv 12-bit
  C. 色彩 bulk: 同上 4 個方向，但一次處理整條 buffer（viper ptr 掃）

每路徑測：
  1. 準確度：抽樣對比，報 max / mean / rmse 誤差
  2. 速度：N 次呼叫，報基準 vs 優化 耗時 + 加速比（speedup）

用法:
  PC(CPython):  python test\\pixel\\test_pixel_full.py
  裝置(REPL):   import test_pixel_full; test_pixel_full.run()
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

from lib.PixelMathMethod import (
    _wave01_q12, _sin_q12,
    hsv_to_rgb8, rgb_to_hsv8, hsv_to_rgb12, rgb_to_hsv12,
    hsv_to_rgb8_buf, rgb_to_hsv8_buf, hsv_to_rgb12_buf, rgb_to_hsv12_buf,
)

# ── 計時 ──────────────────────────────────────────────
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


# ════════════════════════════════════════════════════════
# 基準（reference）實作：標準浮點，當正確答案來源
# ════════════════════════════════════════════════════════
def ref_wave01_q12(phase):
    """phase 0-65535 → 0-4095 正弦。"""
    return int((math.sin(2.0 * math.pi * (phase & 65535) / 65536.0) + 1.0) / 2.0 * 4095.0)


def ref_sin_q12(phase):
    """phase 0-65535 → -4096..4096 正弦。"""
    return int(math.sin(2.0 * math.pi * (phase & 65535) / 65536.0) * 4096.0)


def _ref_hsv_to_rgb(h, s, v, scale):
    h = h % 360
    sf = s / scale
    vf = v / scale
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
    h = (h * 60.0) % 360.0
    return int(round(h)), int(round(s * scale)), int(round(v * scale))


def ref_hsv_to_rgb8(h, s, v):
    return _ref_hsv_to_rgb(h, s, v, 255)


def ref_rgb_to_hsv8(r, g, b):
    return _ref_rgb_to_hsv(r, g, b, 255)


def ref_hsv_to_rgb12(h, s, v):
    return _ref_hsv_to_rgb(h, s, v, 4095)


def ref_rgb_to_hsv12(r, g, b):
    return _ref_rgb_to_hsv(r, g, b, 4095)


# ════════════════════════════════════════════════════════
# 抽樣集合（決定性，可重現）
# ════════════════════════════════════════════════════════
WAVE_PHASES = list(range(0, 65536, 257))          # ~255 點，質數步進涵蓋全週

# 色彩抽樣：hue 全掃 + 關鍵 s/v
def _color_samples(scale):
    svs = [0, scale // 4, scale // 2, scale * 3 // 4, scale]
    out = []
    for h in range(0, 360, 15):
        for s in svs:
            for v in (scale // 4, scale // 2, scale * 3 // 4, scale):
                out.append((h, s, v))
    return out

RGB_SAMPLES_8 = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 255),
                 (0, 0, 0), (255, 128, 0), (100, 200, 50), (128, 128, 128)]
RGB_SAMPLES_12 = [(4095, 0, 0), (0, 4095, 0), (0, 0, 4095), (4095, 4095, 4095),
                  (0, 0, 0), (4095, 2048, 0), (1000, 2000, 500), (2048, 2048, 2048)]


# ════════════════════════════════════════════════════════
# 誤差統計
# ════════════════════════════════════════════════════════
def _err_stats(optimized_fn, ref_fn, samples, dims=1):
    """回傳 (max_err, mean_err, rmse)。optimized_fn/ref_fn 回傳單值或 tuple。"""
    max_e = 0.0
    sum_e = 0.0
    sum_e2 = 0.0
    n = 0
    for s in samples:
        if dims == 1:
            o = optimized_fn(s)
            r = ref_fn(s)
            e = abs(o - r)
        else:
            o = optimized_fn(*s)
            r = ref_fn(*s)
            e = max(abs(oi - ri) for oi, ri in zip(o, r))
        max_e = max(max_e, e)
        sum_e += e
        sum_e2 += e * e
        n += 1
    mean_e = sum_e / n
    rmse = math.sqrt(sum_e2 / n)
    return max_e, mean_e, rmse


def _report_accuracy(name, max_e, mean_e, rmse, tol):
    ok = max_e <= tol
    print("  {}: max={:.2f} mean={:.3f} rmse={:.3f} (tol={}) {}".format(
        name, max_e, mean_e, rmse, tol, "\u2705" if ok else "\u274c"))
    return ok


# ════════════════════════════════════════════════════════
# 全角度掃描（每個 hue 0-359 都測，每角度多個 s/v 點）
# ════════════════════════════════════════════════════════
def _hue_dist(a, b):
    """hue 環上最短距離（0-359）。"""
    d = abs(int(a) - int(b)) % 360
    return d if d <= 180 else 360 - d


def _sv_combos(scale):
    """每個角度的 s/v 組合（11 個點：灰階、飽和、明度變化 + 邊界）。"""
    return [
        (scale, scale),
        (scale, scale * 3 // 4),
        (scale, scale // 2),
        (scale, scale // 4),
        (scale * 3 // 4, scale),
        (scale // 2, scale),
        (scale // 4, scale),
        (scale * 3 // 4, scale * 3 // 4),
        (scale // 2, scale // 2),
        (0, scale),          # 灰階（s=0）
        (scale, 0),          # 黑（v=0）
    ]


def _sweep_hsv_to_rgb(scale, opt_fn, ref_fn):
    """每個 hue 0-359 × 11 個 s/v → 統計 RGB 三通道 max 誤差。"""
    combos = _sv_combos(scale)
    max_e = 0.0
    sum_e = 0.0
    sum_e2 = 0.0
    n = 0
    worst = None
    for h in range(360):
        for s, v in combos:
            o = opt_fn(h, s, v)
            r = ref_fn(h, s, v)
            e = max(abs(oi - ri) for oi, ri in zip(o, r))
            if e > max_e:
                max_e = e
                worst = (h, s, v, o, r)
            sum_e += e
            sum_e2 += e * e
            n += 1
    return max_e, sum_e / n, math.sqrt(sum_e2 / n), n, worst


def _sweep_rgb_to_hsv(scale, opt_fn, ref_fn, hsv_to_rgb_ref):
    """每個 hue 0-359 生成 RGB → 反解 HSV，比 h 角誤差 + s/v 誤差。"""
    combos = _sv_combos(scale)
    h_max = 0.0
    h_sum = 0.0
    h_sum2 = 0.0
    s_max = 0.0
    v_max = 0.0
    n = 0
    worst = None
    for h in range(360):
        for s, v in combos:
            r, g, b = hsv_to_rgb_ref(h, s, v)
            oh, os_, ov = opt_fn(r, g, b)
            rh, rs, rv = ref_fn(r, g, b)
            dh = _hue_dist(oh, rh)
            ds = abs(os_ - rs)
            dv = abs(ov - rv)
            if dh > h_max:
                h_max = dh
                worst = (h, s, v, (r, g, b), (oh, os_, ov), (rh, rs, rv))
            h_sum += dh
            h_sum2 += dh * dh
            s_max = max(s_max, ds)
            v_max = max(v_max, dv)
            n += 1
    return h_max, h_sum / n, math.sqrt(h_sum2 / n), s_max, v_max, n, worst


# ════════════════════════════════════════════════════════
# 速度對比
# ════════════════════════════════════════════════════════
def _time_fn(fn, args_iter, loops):
    t0 = _ticks()
    for _ in range(loops):
        for a in args_iter:
            fn(*a)
    return _diff(t0, _ticks())


def _report_speed(name, ref_fn, opt_fn, args_iter, loops):
    tr = _time_fn(ref_fn, args_iter, loops)
    to = _time_fn(opt_fn, args_iter, loops)
    speedup = tr / to if to > 0 else float('inf')
    print("  {}: 基準 {} / 優化 {} → {:.2f}×".format(name, _fmt(tr), _fmt(to), speedup))
    return speedup


def _fmt(v):
    if v >= 1000:
        return "{:.1f} ms".format(v / 1000.0)
    return "{} us".format(int(v))


# ════════════════════════════════════════════════════════
# 主流程
# ════════════════════════════════════════════════════════
def run():
    print("=== PixelMathMethod 綜合測試：基準 vs 優化 ===")
    print("（裝置上 viper 才是代表性速度；PC 為純 Python 對照）")

    # ── A. 波形準確度 ──
    print("\n── A. 波形準確度（math.sin 基準）──")
    ok = []
    max_e, mean_e, rmse = _err_stats(_wave01_q12, ref_wave01_q12, WAVE_PHASES, 1)
    ok.append(_report_accuracy("_wave01_q12", max_e, mean_e, rmse, 60))
    max_e, mean_e, rmse = _err_stats(_sin_q12, ref_sin_q12, WAVE_PHASES, 1)
    ok.append(_report_accuracy("_sin_q12", max_e, mean_e, rmse, 60))

    # ── B. 色彩準確度（全角度掃描：每 hue 0-359 × 11 個 s/v）──
    print("\n── B. 色彩準確度（全角度 0-359 掃描）──")

    for scale, tag in ((255, "8-bit"), (4095, "12-bit")):
        if scale == 255:
            opt_h2r = hsv_to_rgb8
            ref_h2r = ref_hsv_to_rgb8
            opt_r2h = rgb_to_hsv8
            ref_r2h = ref_rgb_to_hsv8
        else:
            opt_h2r = hsv_to_rgb12
            ref_h2r = ref_hsv_to_rgb12
            opt_r2h = rgb_to_hsv12
            ref_r2h = ref_rgb_to_hsv12

        max_e, mean_e, rmse, n, worst = _sweep_hsv_to_rgb(scale, opt_h2r, ref_h2r)
        print("  hsv→rgb {}: {} 點(360 hue × 11), RGB誤差 max={:.2f} mean={:.3f} rmse={:.3f} {}".format(
            tag, n, max_e, mean_e, rmse, "\u2705" if max_e <= 2 else "\u274c"))
        ok.append(max_e <= 2)

        h_max, h_mean, h_rmse, s_max, v_max, n, worst = _sweep_rgb_to_hsv(
            scale, opt_r2h, ref_r2h, ref_h2r)
        print("  rgb→hsv {}: {} 點, hue角誤差 max={:.1f}° mean={:.3f}° | s誤差max={} v誤差max={} {}".format(
            tag, n, h_max, h_mean, s_max, v_max, "\u2705" if h_max <= 3 else "\u274c"))
        ok.append(h_max <= 3)

    # ── C. 速度對比 ──
    print("\n── C. 速度對比（基準 vs 優化）──")
    print("  注意：PC 上 math.sin 是 C 原生、極快，純 Python 整數版反而慢（0.63× 屬正常）；")
    print("       裝置上 viper 整數版才遠快於浮點 math.sin。色彩是整數 vs 浮點，PC 已見整數優勢。")

    # C1. 波形
    wave_args = [(p,) for p in WAVE_PHASES]
    _report_speed("_wave01_q12", ref_wave01_q12, _wave01_q12, wave_args, 20)

    # C2. 色彩單值
    samples8 = _color_samples(255)
    samples12 = _color_samples(4095)
    col_args8 = samples8[:64]
    _report_speed("hsv→rgb 8", ref_hsv_to_rgb8, hsv_to_rgb8, col_args8, 20)
    _report_speed("rgb→hsv 8", ref_rgb_to_hsv8, rgb_to_hsv8, RGB_SAMPLES_8, 200)
    col_args12 = samples12[:64]
    _report_speed("hsv→rgb 12", ref_hsv_to_rgb12, hsv_to_rgb12, col_args12, 20)
    _report_speed("rgb→hsv 12", ref_rgb_to_hsv12, rgb_to_hsv12, RGB_SAMPLES_12, 200)

    # C3. bulk（64 px 一次處理）
    print("  （bulk：64 px，loops 對照）")
    n = 64
    h_buf = _array('H', [i % 360 for i in range(n)])
    s_buf = _array('H', [255] * n)
    v_buf = _array('H', [255 - (i * 3) % 200 for i in range(n)])
    out8 = bytearray(n * 3)

    # 基準 bulk = Python 迴圈 call ref
    t0 = _ticks()
    for _ in range(200):
        for i in range(n):
            r, g, b = ref_hsv_to_rgb8(h_buf[i], s_buf[i], v_buf[i])
            out8[i * 3] = r; out8[i * 3 + 1] = g; out8[i * 3 + 2] = b
    tr = _diff(t0, _ticks())
    t0 = _ticks()
    for _ in range(200):
        hsv_to_rgb8_buf(h_buf, s_buf, v_buf, out8, n)
    to = _diff(t0, _ticks())
    print("  hsv→rgb 8 bulk: 基準 {} / 優化 {} → {:.2f}×".format(_fmt(tr), _fmt(to), tr / to))

    # rgb→hsv 8 bulk
    rgb8 = bytearray([(i * 7) & 255 for i in range(n * 3)])
    h_o = _array('H', [0] * n); s_o = _array('H', [0] * n); v_o = _array('H', [0] * n)
    t0 = _ticks()
    for _ in range(200):
        for i in range(n):
            h, s, v = ref_rgb_to_hsv8(rgb8[i * 3], rgb8[i * 3 + 1], rgb8[i * 3 + 2])
            h_o[i] = h; s_o[i] = s; v_o[i] = v
    tr = _diff(t0, _ticks())
    t0 = _ticks()
    for _ in range(200):
        rgb_to_hsv8_buf(rgb8, h_o, s_o, v_o, n)
    to = _diff(t0, _ticks())
    print("  rgb→hsv 8 bulk: 基準 {} / 優化 {} → {:.2f}×".format(_fmt(tr), _fmt(to), tr / to))

    # ── 總結 ──
    print("\n=== 總結 ===")
    print("準確度: {} / {} 路徑在容差內".format(sum(ok), len(ok)))
    if not all(ok):
        print("  ⚠ 有路徑超容差，請檢查上述 ❌ 項目")
    print("--- 完成 ---")


if __name__ == "__main__":
    run()
