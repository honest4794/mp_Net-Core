"""
UART Display 接收測試 (MicroPython ESP32)

用法: exec(open("esp_rx.py").read())

接線: GPIO5=RX, GPIO6=TX
"""

from machine import UART, Pin
import time

# 5-byte 幀: [0xB4] [mode] [brightness] [time] [0xFF]
_SOF = 0xB4
_EOF = 0xFF
_SPECIAL = 0x80

uart = UART(2, baudrate=115200, tx=Pin(6), rx=Pin(5), timeout=0)
buf = bytearray()
n = 0

print("[RX] UART1 tx=6 rx=5 baud=115200")
print("等待幀...  Ctrl+C 停止")
print()

try:
    while True:
        if uart.any():
            chunk = uart.read()
#             print(chunk)
            if chunk:
                buf.extend(chunk)

        i = 0
        while i + 4 < len(buf):
            if buf[i] == _SOF and buf[i + 4] == _EOF:
                mode = buf[i + 1]
                bri = buf[i + 2] & 0x1F
                t = buf[i + 3]
                n += 1
                special = "(SPECIAL)" if (mode & _SPECIAL) else ""
                print("[%d] %smode=%d bri=%d time=%d  RAW=0x%02X" %
                      (n, special, mode & 0x3F, bri, t, mode))
                i += 5
            else:
                i += 1

        if i > 0:
            buf = buf[i:]

        time.sleep_ms(10)

except KeyboardInterrupt:
    print("\n[RX] stop (%d frames)" % n)
finally:
    uart.deinit()
