# tft_test_tool.py — TFT 螢幕測試工具集
# 透過 TFT library 統一接口操作，驗證 lib/TFT.py 正確性
#
# 用法:
#   import tft_test_tool
#   tft_test_tool.config(240, 320)    # 手動設解析度 (選填)
#   tft_test_tool.fill_colors()
#   tft_test_tool.fps_test_tft()
#   tft_test_tool.all()

import gc, time, math, random
from lib.sys_bus import bus

# ═══ 內部狀態 ═══
_lcd = None
_w = 240
_h = 320
_manual_w = 0
_manual_h = 0

def config(width=0, height=0):
    """設定螢幕解析度。不傳參則從 bus 讀取"""
    global _manual_w, _manual_h
    _manual_w = width
    _manual_h = height

def _setup():
    global _lcd, _w, _h
    if _lcd is None:
        _lcd = bus.get_service("lcd")
        if _lcd is None:
            raise RuntimeError("LCD not on bus — did boot.py run?")
    if _manual_w and _manual_h:
        _w = _manual_w
        _h = _manual_h
    else:
        _w = int(bus.shared.get("tft_width", 240))
        _h = int(bus.shared.get("tft_height", 320))

def _color(r, g, b):
    """RGB 888 → RGB565 大端"""
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

def _color_le(r, g, b):
    """RGB 888 → RGB565 小端"""
    c = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
    return (c >> 8) | (c << 8)

def _hsv(h, s=100, v=100):
    """HSV → RGB565"""
    h = float(h % 360) / 60.0
    s, v = s / 100.0, v / 100.0
    i = int(h); f = h - i
    p = v * (1 - s); q = v * (1 - s * f); t = v * (1 - s * (1 - f))
    r, g, b = [(v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q)][i]
    return ((int(r * 31) & 0x1F) << 11) | ((int(g * 63) & 0x3F) << 3) | (int(b * 31) & 0x1F)

def _write_solid(color565):
    """全螢幕填色 — 透過 TFT._bus 層零大分配寫入"""
    chunk = bytearray(8192)
    for i in range(4096):
        chunk[i * 2] = color565 >> 8
        chunk[i * 2 + 1] = color565 & 0xFF
    total = _w * _h
    mv = memoryview(chunk)
    written = 0
    while written < total:
        n = min(total - written, 4096)
        hn = _lcd._bus.write_data_async(mv[:n * 2])
        if hn is not None: _lcd._bus.wait(hn)
        written += n
    _lcd._bus.flush()

def _clear():
    _lcd.set_window(0, 0, _w - 1, _h - 1)
    _write_solid(0x0000)

# ══════════════════════════════════════════════════════════════
#  公開測試 API
# ══════════════════════════════════════════════════════════════

def fill_colors():
    """九色全螢幕填滿 — 透過 TFT 接口"""
    _setup()
    gc.collect()
    colors = [
        ("RED",    0xF800), ("GREEN",  0x07E0), ("BLUE",   0x001F),
        ("YELLOW", 0xFFE0), ("CYAN",   0x07FF), ("MAGENTA",0xF81F),
        ("WHITE",  0xFFFF), ("GRAY",   0x8410), ("BLACK",  0x0000),
    ]
    for name, c in colors:
        print("  %s (0x%04X) ..." % (name, c))
        _lcd.set_window(0, 0, _w - 1, _h - 1)
        _write_solid(c)
        time.sleep_ms(500)
    print("fill_colors done")

def color_bars():
    """八色垂直條 — 透過 TFT 接口"""
    _setup()
    bar_h = _h // 8
    for i, c in enumerate([0xF800, 0x07E0, 0x001F, 0xFFFF,
                           0xFFE0, 0x07FF, 0xF81F, 0x0000]):
        y0, y1 = i * bar_h, (i + 1) * bar_h - 1 if i < 7 else _h - 1
        pixels = _w * (y1 - y0 + 1)
        chunk = bytearray(4096 * 2)
        for j in range(4096):
            chunk[j * 2] = c >> 8
            chunk[j * 2 + 1] = c & 0xFF
        mv = memoryview(chunk)
        _lcd.set_window(0, y0, _w - 1, y1)
        remaining = pixels
        while remaining > 0:
            n = min(remaining, 4096)
            hn = _lcd._bus.write_data_async(mv[:n * 2])
            if hn is not None: _lcd._bus.wait(hn)
            remaining -= n
        _lcd._bus.flush()
    time.sleep_ms(1500)
    print("color_bars done")

def gradient():
    """RGB 水平漸變 — 透過 TFT 接口"""
    _setup()
    gc.collect()
    row = bytearray(_w * 2)
    for x in range(_w):
        r = int(x * 255 / _w)
        g = int((1 - abs(x - _w / 2) / (_w / 2)) * 255)
        b = int((_w - x) * 255 / _w)
        c = _color(r, g, b)
        row[x * 2] = c >> 8
        row[x * 2 + 1] = c & 0xFF

    BATCH = 40
    for y in range(0, _h, BATCH):
        h = min(BATCH, _h - y)
        buf = bytearray(_w * h * 2)
        for i in range(h):
            off = i * _w * 2
            buf[off:off + len(row)] = row
        _lcd.set_window(0, y, _w - 1, y + h - 1)
        hn = _lcd._bus.write_data_async(buf)
        if hn is not None: _lcd._bus.wait(hn)
        _lcd._bus.flush()
    time.sleep_ms(2000)
    print("gradient done")

def fps_test_tft(frames=100):
    """黑白交替 FPS — 透過 TFT.show_frame()"""
    _setup()
    gc.collect()
    total = _w * _h * 2
    full_w = memoryview(bytearray(b'\xff\xff' * (total // 2))[:total])
    full_b = memoryview(bytearray(total))
    _lcd.set_window(0, 0, _w - 1, _h - 1)
    t0 = time.ticks_us()
    for n in range(frames):
        _lcd.show_frame(full_w if n & 1 else full_b)
    elapsed = time.ticks_diff(time.ticks_us(), t0) / 1_000_000
    fps = frames / elapsed
    mbps = total * frames / elapsed / (1024 * 1024)
    print("FPS(TFT): %.0f  (%.1f ms/frame, %.1f MB/s)" % (fps, elapsed/frames*1000, mbps))

def fps_test_tft888(frames=100):
    """TFT 層 RGB888 FPS — 透過 show_frame() 24bpp 全幀"""
    _setup()
    gc.collect()
    total = _w * _h * 3
    full_w = memoryview(bytearray(b'\xff\xff\xff' * (total // 3))[:total])
    full_b = memoryview(bytearray(total))
    _set_rgb888()
    _lcd.set_window(0, 0, _w - 1, _h - 1)
    t0 = time.ticks_us()
    for n in range(frames):
        _lcd.show_frame(full_w if n & 1 else full_b)
    elapsed = time.ticks_diff(time.ticks_us(), t0) / 1_000_000
    fps = frames / elapsed
    mbps = total * frames / elapsed / (1024 * 1024)
    print("FPS(TFT888): %.0f  (%.1f ms/frame, %.1f MB/s)" % (fps, elapsed/frames*1000, mbps))
    _set_rgb565()

def _colmod(cmd_val):
    _lcd.write_cmd_data(0x3A, bytes([cmd_val]))

def _set_rgb888():
    _colmod(0x76)
    _lcd.bytes_per_pixel = 3

def _set_rgb565():
    _colmod(0x55)
    _lcd.bytes_per_pixel = 2

def all():
    """全部依序執行：FPS (565/888) + 圖形驗證"""
    fps_test_tft(50)
    _clear(); time.sleep_ms(300)
    fps_test_tft888(50)
    _clear(); time.sleep_ms(300)
    fill_colors()
    _clear(); time.sleep_ms(300)
    color_bars()
    _clear(); time.sleep_ms(300)
    gradient()
    _clear(); time.sleep_ms(300)
    print("=== all tests done ===")
