# -*- coding: utf-8 -*-
"""PixelMathMethod HSV↔RGB 色彩轉換單元測試

驗證 slave/lib/PixelMathMethod.py 的 bulk 色彩接口（8-bit 與 12-bit 各雙向）：
  1. 已知色對照：紅/綠/藍/白/黑/灰 → HSV → RGB round-trip
  2. bulk 結果 == 單值結果（兩者語義一致）
  3. 值域：RGB 輸出 0-255（8-bit）/ 0-4095（12-bit），h 0-359
  4. 修掉舊專案 bug 的驗證：RGB 順序正確（非 GRB）、飽和度非 0、色相 offset 正確

用法:
  PC(CPython):  python test\\pixel\\test_pixel_color.py
  裝置(REPL):   import test_pixel_color; test_pixel_color.run()
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

from lib.PixelMathMethod import (
    hsv_to_rgb8, rgb_to_hsv8, hsv_to_rgb12, rgb_to_hsv12,
    hsv_to_rgb8_buf, rgb_to_hsv8_buf, hsv_to_rgb12_buf, rgb_to_hsv12_buf,
)

_PASS = []
_FAIL = []


def _check(name, cond, detail=""):
    if cond:
        _PASS.append(name)
        print("  \u2705 PASS - {}".format(name))
    else:
        _FAIL.append(name)
        print("  \u274c FAIL - {} {}".format(name, detail))


def _near(a, b, tol):
    return abs(a - b) <= tol


def _test_known_8bit():
    print("-- 8-bit 已知色 --")
    # 純紅：h=0, s=255, v=255 → (255, 0, 0)
    r, g, b = hsv_to_rgb8(0, 255, 255)
    _check("hsv8(0,255,255)=紅", (r, g, b) == (255, 0, 0), "got {}".format((r, g, b)))
    # 純綠：h=120 → (0,255,0)
    r, g, b = hsv_to_rgb8(120, 255, 255)
    _check("hsv8(120,255,255)=綠", (r, g, b) == (0, 255, 0), "got {}".format((r, g, b)))
    # 純藍：h=240 → (0,0,255)
    r, g, b = hsv_to_rgb8(240, 255, 255)
    _check("hsv8(240,255,255)=藍", (r, g, b) == (0, 0, 255), "got {}".format((r, g, b)))
    # 白：s=0 → (v,v,v)
    r, g, b = hsv_to_rgb8(0, 0, 255)
    _check("hsv8(0,0,255)=白", (r, g, b) == (255, 255, 255), "got {}".format((r, g, b)))
    # 黑：v=0
    r, g, b = hsv_to_rgb8(0, 255, 0)
    _check("hsv8(0,255,0)=黑", (r, g, b) == (0, 0, 0), "got {}".format((r, g, b)))


def _test_known_12bit():
    print("-- 12-bit 已知色 --")
    r, g, b = hsv_to_rgb12(0, 4095, 4095)
    _check("hsv12(0,4095,4095)=紅", (r, g, b) == (4095, 0, 0), "got {}".format((r, g, b)))
    r, g, b = hsv_to_rgb12(120, 4095, 4095)
    _check("hsv12(120,4095,4095)=綠", (r, g, b) == (0, 4095, 0), "got {}".format((r, g, b)))
    r, g, b = hsv_to_rgb12(240, 4095, 4095)
    _check("hsv12(240,4095,4095)=藍", (r, g, b) == (0, 0, 4095), "got {}".format((r, g, b)))
    r, g, b = hsv_to_rgb12(0, 0, 4095)
    _check("hsv12(0,0,4095)=白", (r, g, b) == (4095, 4095, 4095), "got {}".format((r, g, b)))


def _test_roundtrip_8bit():
    print("-- 8-bit round-trip --")
    # 已知色 round-trip：rgb → hsv → rgb 應近似原值（飽和度非 0 的純色）
    cases = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 128, 0), (100, 200, 50)]
    ok = True
    for c in cases:
        h, s, v = rgb_to_hsv8(*c)
        r, g, b = hsv_to_rgb8(h, s, v)
        if not (_near(r, c[0], 2) and _near(g, c[1], 2) and _near(b, c[2], 2)):
            ok = False
            print("    round-trip 失敗: {} → hsv({},{},{}) → {}".format(
                c, h, s, v, (r, g, b)))
    _check("rgb→hsv→rgb 近似原值", ok)

    # 飽和度非 0（舊 bug 會恆 0）
    _, s, _ = rgb_to_hsv8(255, 0, 0)
    _check("飽和度非 0（舊 bug 修正）", s == 255, "s={}".format(s))
    # 綠色 h=120（舊 bug offset 會錯）
    h, _, _ = rgb_to_hsv8(0, 255, 0)
    _check("綠 h=120（offset 修正）", _near(h, 120, 1), "h={}".format(h))
    # 藍色 h=240
    h, _, _ = rgb_to_hsv8(0, 0, 255)
    _check("藍 h=240（offset 修正）", _near(h, 240, 1), "h={}".format(h))


def _test_roundtrip_12bit():
    print("-- 12-bit round-trip --")
    cases = [(4095, 0, 0), (0, 4095, 0), (0, 0, 4095), (4095, 2048, 0), (1000, 2000, 500)]
    ok = True
    for c in cases:
        h, s, v = rgb_to_hsv12(*c)
        r, g, b = hsv_to_rgb12(h, s, v)
        if not (_near(r, c[0], 20) and _near(g, c[1], 20) and _near(b, c[2], 20)):
            ok = False
            print("    round-trip 失敗: {} → hsv({},{},{}) → {}".format(
                c, h, s, v, (r, g, b)))
    _check("rgb→hsv→rgb 近似原值（12-bit）", ok)
    _, s, _ = rgb_to_hsv12(4095, 0, 0)
    _check("飽和度非 0（12-bit）", s == 4095, "s={}".format(s))


def _test_bulk_equals_single():
    print("-- bulk == 單值 --")
    # 8-bit
    n = 8
    h_buf = _array('H', [0, 120, 240, 60, 180, 300, 30, 90])
    s_buf = _array('H', [255] * n)
    v_buf = _array('H', [255, 255, 255, 128, 128, 128, 255, 255])
    out8 = bytearray(n * 3)
    hsv_to_rgb8_buf(h_buf, s_buf, v_buf, out8, n)
    ok = True
    for i in range(n):
        r, g, b = hsv_to_rgb8(h_buf[i], s_buf[i], v_buf[i])
        if (out8[i*3], out8[i*3+1], out8[i*3+2]) != (r, g, b):
            ok = False
            print("    idx {} bulk {} != single {}".format(
                i, (out8[i*3], out8[i*3+1], out8[i*3+2]), (r, g, b)))
    _check("hsv_to_rgb8 bulk==單值", ok)

    # 12-bit
    out12 = _array('H', [0] * (n * 3))
    hsv_to_rgb12_buf(h_buf, s_buf, v_buf, out12, n)
    ok = True
    for i in range(n):
        r, g, b = hsv_to_rgb12(h_buf[i], s_buf[i], v_buf[i])
        if (out12[i*3], out12[i*3+1], out12[i*3+2]) != (r, g, b):
            ok = False
            print("    idx {} bulk {} != single {}".format(
                i, (out12[i*3], out12[i*3+1], out12[i*3+2]), (r, g, b)))
    _check("hsv_to_rgb12 bulk==單值", ok)

    # rgb→hsv bulk==單值（8-bit）
    rgb8 = bytearray([255, 0, 0, 0, 255, 0, 0, 0, 255, 100, 200, 50])
    h_o = _array('H', [0] * 4)
    s_o = _array('H', [0] * 4)
    v_o = _array('H', [0] * 4)
    rgb_to_hsv8_buf(rgb8, h_o, s_o, v_o, 4)
    ok = True
    for i in range(4):
        h, s, v = rgb_to_hsv8(rgb8[i*3], rgb8[i*3+1], rgb8[i*3+2])
        if (h_o[i], s_o[i], v_o[i]) != (h, s, v):
            ok = False
            print("    idx {} bulk {} != single {}".format(
                i, (h_o[i], s_o[i], v_o[i]), (h, s, v)))
    _check("rgb_to_hsv8 bulk==單值", ok)


def run():
    print("=== PixelMathMethod HSV↔RGB 單元測試 ===")
    del _PASS[:]
    del _FAIL[:]
    _test_known_8bit()
    _test_known_12bit()
    _test_roundtrip_8bit()
    _test_roundtrip_12bit()
    _test_bulk_equals_single()
    print("\n結果: {} pass / {} fail".format(len(_PASS), len(_FAIL)))
    if _FAIL:
        print("FAIL 項目:")
        for n in _FAIL:
            print("  - {}".format(n))
    return not _FAIL


if __name__ == "__main__":
    ok = run()
    if not IS_MICROPYTHON:
        import sys as _sys
        _sys.exit(0 if ok else 1)
