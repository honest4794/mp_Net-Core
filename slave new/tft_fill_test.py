"""
TFT 螢幕填充測試 — 依序顯示多種顏色

用法:
  1. 先讓 boot.py 正常初始化硬體（含 TFT）
  2. 手動執行: exec(open("tft_fill_test.py").read())
"""

import time
from lib.sys_bus import bus

# ── 待測顏色列表 ──
# fill() 接受 (R, G, B) tuple，自動轉成 RGB565
COLORS = [
    ("紅",    (255, 0, 0)),
    ("綠",    (0, 255, 0)),
    ("藍",    (0, 0, 255)),
    ("黃",    (255, 255, 0)),
    ("青",    (0, 255, 255)),
    ("紫",    (255, 0, 255)),
    ("白",    (255, 255, 255)),
    ("灰",    (128, 128, 128)),
    ("黑",    (0, 0, 0)),
]

# ── 從 bus 取得已初始化的 LCD ──
lcd = bus.get_service("lcd")
if lcd is None:
    print("[err] LCD not found on bus — did boot.py run?")
    raise SystemExit(1)

w = bus.shared.get("tft_width", "?")
h = bus.shared.get("tft_height", "?")
print("[tft_fill_test] LCD = {}x{}".format(w, h))

# ── 依序填入顏色 ──
INTERVAL_MS = 1500

for name, rgb in COLORS:
    print("[tft_fill_test] {}  ({},{},{})".format(name, rgb[0], rgb[1], rgb[2]))
    lcd.fill(rgb)
    time.sleep_ms(INTERVAL_MS)

print("[tft_fill_test] done")
