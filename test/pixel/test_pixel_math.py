# -*- coding: utf-8 -*-
"""PixelMathMethod / Effect 單元測試

驗證 slave/lib/PixelMathMethod.py 與 slave/pixel/effects/effects.py：
  1. _wave01_q12 / _sin_q12：值域 + 對 math.sin 的逼近誤差（math.sin 僅測試對照用）
  2. 六種波形段 type：keep / math_now / square_wave_now / pulse_wave / pulse / starter
  3. pattern_value_at：決定性、值域 0-4095、循環（t 與 t+total 同值）
  4. Effect：frame 長度/值域、spacing/step/offset/speed/reverse、restart/seek 決定性
  5. effects.json 載入 → make() → dump()

用法:
  PC(CPython):  python test\\pixel\\test_pixel_math.py
  裝置(REPL):   import test_pixel_math; test_pixel_math.run()
"""
import sys

IS_MICROPYTHON = (getattr(sys, "implementation", None)
                  and sys.implementation.name == "micropython")

if not IS_MICROPYTHON:
    import os
    _HERE = os.path.dirname(os.path.abspath(__file__))
    _ROOT = os.path.dirname(os.path.dirname(_HERE))      # repo 根
    _SLAVE = os.path.join(_ROOT, "slave")
    if _SLAVE not in sys.path:
        sys.path.insert(0, _SLAVE)

from lib.PixelMathMethod import mt, _wave01_q12, _sin_q12
from pixel.effects import effects

_PASS = []
_FAIL = []


def _check(name, cond, detail=""):
    if cond:
        _PASS.append(name)
        print("  \u2705 PASS - {}".format(name))
    else:
        _FAIL.append(name)
        print("  \u274c FAIL - {} {}".format(name, detail))


# ── 1. 波形核心 ──────────────────────────────────────
def _test_wave():
    print("-- 波形核心 --")
    mn, mx = 1 << 30, -1
    for p in range(0, 65536, 7):
        v = _wave01_q12(p)
        mn = min(mn, v)
        mx = max(mx, v)
    _check("_wave01_q12 值域 0-4095", mn >= 0 and mx <= 4095, "mn={} mx={}".format(mn, mx))

    if not IS_MICROPYTHON:
        import math
        max_err = 0.0
        for p in range(0, 65536, 64):
            ideal = (math.sin(2 * math.pi * p / 65536.0) + 1.0) / 2.0 * 4095.0
            err = abs(ideal - _wave01_q12(p))
            max_err = max(max_err, err)
        _check("_wave01_q12 逼近誤差 < 60", max_err < 60, "max_err={:.2f}".format(max_err))

    # 關鍵相位：0 → mid(~2048)、16384 → peak(~4095)、49152 → trough(~0)
    _check("_wave01_q12(0) ≈ 2048 (mid)",
           1984 <= _wave01_q12(0) <= 2112, "v={}".format(_wave01_q12(0)))
    _check("_wave01_q12(16384) ≈ 4095 (peak)", _wave01_q12(16384) > 4032,
           "v={}".format(_wave01_q12(16384)))
    _check("_wave01_q12(49152) ≈ 0 (trough)", _wave01_q12(49152) < 64,
           "v={}".format(_wave01_q12(49152)))

    smn, smx = 1 << 30, -(1 << 30)
    for p in range(0, 65536, 7):
        v = _sin_q12(p)
        smn = min(smn, v)
        smx = max(smx, v)
    _check("_sin_q12 值域 -4096..4096", smn >= -4096 and smx <= 4096,
           "mn={} mx={}".format(smn, smx))


# ── 2. 六種波形段 type ──────────────────────────────
def _values_of(program):
    """掃完整個 pattern 的每一幀，回傳 (值集合, 值列表)。"""
    total = program[-1]["end_Time"]
    vals = [mt.pattern_value_at(program, t) for t in range(total)]
    return set(vals), vals


def _test_segments():
    print("-- 波形段 type --")
    # keep：恆定
    s, _ = _values_of([{"type": "keep", "l_max": 1000, "l_lim": 0, "end_Time": 10}])
    _check("keep 恆定 l_max", s == {1000}, "s={}".format(sorted(s)))

    # math_now：值域落在 [l_lim, l_max]，且有變化
    s, v = _values_of([{"type": "math_now", "F": 2, "l_max": 4095, "l_lim": 100,
                        "phi": 0, "end_Time": 100}])
    _check("math_now 值域 [l_lim, l_max]",
           min(v) >= 100 and max(v) <= 4095 and len(s) > 1,
           "min={} max={} n={}".format(min(v), max(v), len(s)))

    # square_wave_now：只有 {l_lim, l_max}（F 要夠高讓相位覆蓋完整週期）
    s, _ = _values_of([{"type": "square_wave_now", "F": 25, "l_max": 3000, "l_lim": 100,
                        "phi": 0, "end_Time": 100}])
    _check("square_wave_now 只有 {l_lim, l_max}", s == {100, 3000},
           "s={}".format(sorted(s)))

    # pulse_wave：只有 {l_lim, l_max}
    s, _ = _values_of([{"type": "pulse_wave", "F": 25, "l_max": 3000, "l_lim": 50,
                        "phi": 0, "pulse": 2047, "end_Time": 100}])
    _check("pulse_wave 只有 {l_lim, l_max}", s == {50, 3000}, "s={}".format(sorted(s)))

    # pulse：只有 {l_lim, l_max}
    s, _ = _values_of([{"type": "pulse", "F": 4, "l_max": 3000, "l_lim": 50,
                        "phi": 0, "pulse": 1, "end_Time": 100}])
    _check("pulse 只有 {l_lim, l_max}", s == {50, 3000}, "s={}".format(sorted(s)))

    # starter：恆 0
    s, _ = _values_of([{"type": "starter", "l_max": 100, "l_lim": 0, "end_Time": 10}])
    _check("starter 恆 0", s == {0}, "s={}".format(sorted(s)))


# ── 3. pattern_value_at ──────────────────────────────
def _test_pattern():
    print("-- pattern_value_at --")
    prog = effects.eyes.DEFAULT_PROGRAM
    total = prog[-1]["end_Time"]

    # 決定性
    a = mt.pattern_value_at(prog, 123)
    b = mt.pattern_value_at(prog, 123)
    _check("決定性（同 t 同值）", a == b)

    # 循環：t 與 t+total 同值
    c = mt.pattern_value_at(prog, 123 + total)
    _check("循環（t 與 t+total 同值）", a == c, "{} vs {}".format(a, c))

    # 值域
    mn = min(mt.pattern_value_at(prog, t) for t in range(0, total, 3))
    mx = max(mt.pattern_value_at(prog, t) for t in range(0, total, 3))
    _check("值域 0-4095", mn >= 0 and mx <= 4095, "mn={} mx={}".format(mn, mx))


# ── 4. Effect ────────────────────────────────────────
def _test_effect():
    print("-- Effect --")
    # 直接建構（pixel_n=8，math_now 波形 + spacing）
    params = {
        "pixel_n": 8,
        "program": [{"type": "math_now", "F": 2, "l_max": 4095, "l_lim": 0,
                     "phi": 0, "end_Time": 100}],
        "step": 1, "spacing": 3, "offset": 0, "speed": 1, "reverse": False,
    }
    e = effects.breathing("breathing", params)
    buf = e.frame(0)
    _check("frame 長度 == pixel_n", len(buf) == 8, "len={}".format(len(buf)))
    _check("frame 值域 0-4095", all(0 <= v <= 4095 for v in buf))
    _check("spacing 產生空間分布", len(set(buf)) > 1,
           "values={}".format(list(buf)[:8]))

    # speed：speed=2 → frame(0) == frame(1)（同輸出重複）
    params2 = dict(params, speed=2, spacing=0)
    e2 = effects.breathing("breathing", params2)
    _check("speed=2 重複輸出", list(e2.frame(0)) == list(e2.frame(1)))

    # reverse：反轉
    params3 = dict(params, reverse=True)
    e3 = effects.breathing("breathing", params3)
    fwd = list(effects.breathing("breathing", params).frame(5))
    rev = list(e3.frame(5))
    _check("reverse 反轉輸出", rev == fwd[::-1], "fwd={} rev={}".format(fwd[:4], rev[:4]))

    # restart / seek 決定性
    ey = effects.eyes("eyes", {"pixel_n": 8,
                               "program": effects.eyes.DEFAULT_PROGRAM,
                               "step": 1, "spacing": 10, "offset": 0,
                               "speed": 1, "reverse": False})
    f0 = list(next(ey))
    f1 = list(next(ey))
    ey.seek(0)
    _check("seek(0) 重現 frame0", list(next(ey)) == f0)
    ey.restart()
    _check("restart 重現 frame0", list(next(ey)) == f0)
    _check("frame0 != frame1（eyes 有變化）", f0 != f1)


# ── 5. effects.json 載入 ─────────────────────────────
def _test_json():
    print("-- effects.json 載入 --")
    if IS_MICROPYTHON:
        path = "/pixel/effects/effects.json"
    else:
        import os
        _HERE = os.path.dirname(os.path.abspath(__file__))
        _ROOT = os.path.dirname(os.path.dirname(_HERE))
        path = os.path.join(_ROOT, "slave", "pixel", "effects", "effects.json")

    try:
        import json
        with open(path) as f:
            data = json.load(f)
        effects.load_json(data.get("effects", []))
    except Exception as ex:
        _check("讀取 effects.json", False, str(ex))
        return

    d = effects.dump()
    _check("effects.json 載入 breathing+eyes", d.get("breathing") == 1 and d.get("eyes") == 2,
           "dump={}".format(d))

    eff = effects.make("eyes")
    _check("make('eyes') pixel_n=64", eff.pixel_n == 64, "pixel_n={}".format(eff.pixel_n))
    _check("make('eyes') spacing=10", eff.spacing == 10, "spacing={}".format(eff.spacing))
    buf = eff.frame(0)
    _check("eyes frame0 值域 + 空間分布",
           len(buf) == 64 and all(0 <= v <= 4095 for v in buf) and len(set(buf)) > 1)


def run():
    print("=== PixelMathMethod / Effect 單元測試 ===")
    del _PASS[:]
    del _FAIL[:]
    _test_wave()
    _test_segments()
    _test_pattern()
    _test_effect()
    _test_json()
    print("\n結果: {} pass / {} fail".format(len(_PASS), len(_FAIL)))
    if _FAIL:
        print("FAIL 項目:")
        for n in _FAIL:
            print("  - {}".format(n))
    return not _FAIL


if __name__ == "__main__":
    ok = run()
    # 裝置上不呼叫 sys.exit（MicroPython 未捕捉的 SystemExit 會 soft reboot）
    if not IS_MICROPYTHON:
        import sys as _sys
        _sys.exit(0 if ok else 1)
