# tools/mock_ex_ic.py — 在另一顆 ESP32-C3 上跑的「外部 IC」模仿腳本(極簡)
#
# 純 UART:收到訊號幀 → 分類列印 → 原樣回覆。
#   收到 [0xB4, mode, bri, time, 0xFF] → 印出 mode/bri/time → 原樣回覆同一幀。
#
# 接線:ESP32-C3 GPIO0 → 馬達板 UART TX、GPIO1 → 馬達板 UART RX
#      (對不上就交換下面 TX/RX)
import machine
from machine import UART

TX = 0          # ESP32-C3 GPIO 腳
RX = 1
BAUD = 115200   # 對齊馬達板 config 的 UART baud

uart = UART(1, tx=TX, rx=RX, baudrate=BAUD)

buf = bytearray()
print('ok')
while True:
    chunk = uart.read()
    if not chunk:
        continue
    buf += chunk
    i = 0
    while i + 4 < len(buf):
        if buf[i] == 0xB4 and buf[i + 4] == 0xFF:
            mode, bri, tm = buf[i + 1], buf[i + 2], buf[i + 3]
            print("[RX] B4 {:02X} {:02X} {:02X} FF | mode={} bri={} time={}".format(
                mode, bri, tm, mode, bri, tm))
            uart.write(bytes(buf[i:i + 5]))   # 原樣回覆
            print("[TX] 回覆 B4 {:02X} {:02X} {:02X} FF".format(mode, bri, tm))
            buf = buf[i + 5:]                 # 移除已處理的幀(bytearray 不支援 del 切片)
            break
        i += 1
    if len(buf) > 256:
        buf = bytearray()
