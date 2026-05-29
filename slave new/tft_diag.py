"""
TFT 螢幕逐步診斷測試

用法: exec(open("tft_diag.py").read())
"""

import time, gc
from lib.sys_bus import bus

lcd = bus.get_service("lcd")
if lcd is None:
    print("[err] LCD not found on bus")
    raise SystemExit(1)

w = bus.shared.get("tft_width", "?")
h = bus.shared.get("tft_height", "?")
print("[diag] LCD = {}x{}".format(w, h))
print("[diag] _bus._qspi =", getattr(lcd._bus, '_qspi', '?'))
print("[diag] _bus._dma  =", getattr(lcd._bus, '_dma', '?'))
print("[diag] _bus._dc   =", getattr(lcd._bus, '_dc', '?'))
print("[diag] _bus._cs   =", getattr(lcd._bus, '_cs', '?'))
print("[diag] _bus._rst  =", getattr(lcd._bus, '_rst', '?'))
print("[diag] free mem   =", gc.mem_free())

# ── Step 1: 小區塊 fill（100x100），確認 write_data 能送到 panel ──
SIZE = 100
bpp = getattr(lcd, 'bytes_per_pixel', 2)  # 2 or 3
buf_len = SIZE * SIZE * bpp
print("[diag] step1: fill 100x100 ({:.1f}KB)".format(buf_len / 1024))

# RGB565 red
r, g, b_val = 255, 0, 0
color565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b_val >> 3)
buf = bytearray(buf_len)
for i in range(0, len(buf), bpp):
    buf[i] = color565 >> 8
    if bpp >= 2:
        buf[i + 1] = color565 & 0xFF
    if bpp >= 3:
        buf[i + 2] = 0  # RGB888 extra byte

print("[diag] step1: buffer allocated, writing...")
try:
    lcd.set_window(0, 0, SIZE - 1, SIZE - 1)
    lcd.write_data(buf)
    print("[diag] step1: write OK. Seen red square top-left?")
except Exception as e:
    print("[diag] step1: ERROR —", e)

time.sleep_ms(2000)

# ── Step 2: 全螢幕 fill，但用較小的 chunk 分批送 ──
print("[diag] step2: full screen fill (green) via chunks")
gc.collect()
print("[diag] step2: mem after gc =", gc.mem_free())

g, b_val = 255, 0
color565 = ((0 & 0xF8) << 8) | ((g & 0xFC) << 3) | (b_val >> 3)

CHUNK_H = 20  # 一次送 20 行
row_len = w * bpp
chunk_buf = bytearray(row_len * CHUNK_H)
for i in range(0, len(chunk_buf), bpp):
    chunk_buf[i] = color565 >> 8
    if bpp >= 2:
        chunk_buf[i + 1] = color565 & 0xFF
    if bpp >= 3:
        chunk_buf[i + 2] = 0

lcd.set_window(0, 0, w - 1, h - 1)

for y in range(0, h, CHUNK_H):
    rows = min(CHUNK_H, h - y)
    chunk = memoryview(chunk_buf)[:rows * row_len]
    try:
        lcd.write_data(chunk)
    except Exception as e:
        print("[diag] step2: chunk y={} ERROR — {}".format(y, e))
        break
else:
    print("[diag] step2: full green screen sent. Seen?")

time.sleep_ms(2000)

# ── Step 3: 直接寫原始指令，測試 panel 有無回應 ──
print("[diag] step3: direct cmd 0x29 (display on) + blue")
b_val = 255
color565 = ((0 & 0xF8) << 8) | ((0 & 0xFC) << 3) | (b_val >> 3)
for i in range(0, len(chunk_buf), bpp):
    chunk_buf[i] = color565 >> 8
    if bpp >= 2:
        chunk_buf[i + 1] = color565 & 0xFF
    if bpp >= 3:
        chunk_buf[i + 2] = 0

try:
    lcd.write_cmd(0x29)  # display on (redundant but explicit)
    time.sleep_ms(50)
    lcd.set_window(0, 0, w - 1, h - 1)
    for y in range(0, h, CHUNK_H):
        rows = min(CHUNK_H, h - y)
        lcd.write_data(memoryview(chunk_buf)[:rows * row_len])
    print("[diag] step3: blue sent")
except Exception as e:
    print("[diag] step3: ERROR —", e)

print("[diag] === diag done ===")
