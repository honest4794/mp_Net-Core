"""
UART Display 發送 (MicroPython) — 改頂部參數，exec 即送

用法: exec(open("esp_tx.py").read())
接線: 測試 RX(5) ← 目標 TX(18) ,  測試 TX(6) → 目標 RX(8)
"""

from machine import UART, Pin
import time

# ═══ 修改這裡 ═══
MODE      = 1      # 模式 (0-63, 0=standby)
BRIGHTNESS = 10     # 亮度 (0-31)
TIME      = 0       # time (0-255)
SPECIAL   = 0   # 特殊模式 (bit7)

_SOF = 0xB4
_EOF = 0xFF
_SPECIAL = 0x80

uart = UART(2, baudrate=115200, tx=Pin(6), rx=Pin(5), timeout=0)

mode_byte = MODE | (_SPECIAL if SPECIAL else 0)
frame = bytes([_SOF, mode_byte, BRIGHTNESS & 0x1F, TIME & 0xFF, _EOF])

print("[TX] mode=%d%s bri=%d time=%d" %
      (MODE, " *" if SPECIAL else "", BRIGHTNESS, TIME))
print("  -> %s" % " ".join("%02X" % b for b in frame))

uart.write(frame)

time.sleep_ms(100)
uart.deinit()
print("[TX] done")
