# -*- coding: utf-8 -*-
"""RS485 對端板 — 長期監聽 + 自動 echo + 週期 beacon（自包含，上傳即跑）

這塊板是被動端：收到一整幀（CRC 通過）就原樣回送；
另外每 BEACON_MS 主動發一幀 beacon（seq=0xFFFF，payload=目前 baud），
讓主測板能確認「對端有活著、線路通、baud 對」。

完全自包含：不 import 任何專案模組（driver/lib），
只要把本檔上傳就能跑（檔尾已直接 run()）。

部署：
  1. 把本檔改名 main.py 丟到裝置根目錄 → 開機自動跑。
  2. 或 REPL：exec(open("rs485_echo_auto.py").read())

腳位（以程式碼為準）：
  GPIO8 = TX  → 收發器 DI      (MCU 送出)
  GPIO9 = RX  ← 收發器 RO      (MCU 收到)
  GPIO7 = EN  → 收發器 DE+RE   (active-high：1=發送, 0=接收)
波特率：會自動輪流在 BAUDS 裡的每個 baud 停留 DWELL_MS。
"""

import struct
import time

try:
    import ubinascii as binascii
except ImportError:
    import binascii

from machine import UART, Pin

MAGIC = b"RS48"
_HDR = 12                     # 4 magic + 2 seq + 2 plen + 4 crc

BAUDS = (9600, 115200)        # 輪流測試的波特率
DWELL_MS = 15000              # 每個 baud 停留多久
BEACON_MS = 2000              # 每隔多久發一次 beacon
TX, RX, EN = 8, 9, 7          # DI, RO, DE+RE
UART_ID = 1


# ── 自包含 RS485 方向控制（與 driver._Rs485Uart 同一套時序） ──
class _RS485:
    def __init__(self, uart, en_pin, baudrate):
        self.io = uart
        self.en = en_pin
        self.baud = int(baudrate)
        self.en.value(0)

    def _wait_sent(self, nbytes):
        if hasattr(self.io, "txdone"):
            try:
                while not self.io.txdone():
                    time.sleep_ms(0)
                return
            except Exception:
                pass
        time.sleep_ms(max(1, (nbytes + 4) * 10 * 1000 // self.baud + 2))

    def write(self, data):
        self.en.value(1)
        try:
            n = self.io.write(data)
            self._wait_sent(len(data) if (n is None or n <= 0) else n)
            return n
        finally:
            self.en.value(0)

    def readinto(self, buf):
        return self.io.readinto(buf)


def _ticks_ms():
    if hasattr(time, "ticks_ms"):
        return time.ticks_ms()
    return int(time.time() * 1000)


def _ticks_diff(a, b):
    if hasattr(time, "ticks_diff"):
        return time.ticks_diff(a, b)
    return a - b


def _build(seq, payload):
    hdr = struct.pack("<4sHH", MAGIC, seq & 0xFFFF, len(payload))
    crc = binascii.crc32(hdr[4:] + payload) & 0xFFFFFFFF
    return hdr + payload + struct.pack("<I", crc)


def _beacon(baud):
    return _build(0xFFFF, struct.pack("<I", baud & 0xFFFFFFFF))


def _crc_ok(frame):
    if len(frame) < _HDR:
        return False
    plen = frame[6] | (frame[7] << 8)
    if len(frame) != _HDR + plen:
        return False
    got = frame[-4] | (frame[-3] << 8) | (frame[-2] << 16) | (frame[-1] << 24)
    return got == (binascii.crc32(frame[4:-4]) & 0xFFFFFFFF)


class _Framer:
    def __init__(self):
        self.buf = bytearray()

    def feed(self, data):
        self.buf.extend(data)

    def next(self):
        while True:
            i = self.buf.find(MAGIC)
            if i < 0:
                if len(self.buf) > 3:
                    self.buf = self.buf[-3:]
                return None
            if i > 0:
                del self.buf[:i]
            if len(self.buf) < 8:
                return None
            plen = self.buf[6] | (self.buf[7] << 8)
            total = _HDR + plen
            if len(self.buf) < total:
                return None
            f = bytes(self.buf[:total])
            del self.buf[:total]
            return f


def _drain(uart):
    tmp = bytearray(256)
    for _ in range(32):
        try:
            if uart.any():
                uart.readinto(tmp)
            else:
                break
        except Exception:
            break


def run(bauds=BAUDS, dwell_ms=DWELL_MS, beacon_ms=BEACON_MS,
        tx=TX, rx=RX, en=EN, uart_id=UART_ID):
    uart = UART(int(uart_id), baudrate=int(bauds[0]), tx=Pin(int(tx)), rx=Pin(int(rx)))
    rs = _RS485(uart, Pin(int(en), Pin.OUT, value=0), bauds[0])
    buf = bytearray(256)

    print("RS485 ECHO ready  (tx={} rx={} en={})".format(tx, rx, en))
    print("baud sweep: {}  dwell={}s  beacon every {}s".format(
        list(bauds), dwell_ms // 1000, beacon_ms // 1000))

    while True:
        for baud in bauds:
            baud = int(baud)
            try:
                uart.init(baudrate=baud)
            except Exception:
                pass
            rs.baud = baud
            _drain(uart)
            framer = _Framer()
            print("ECHO switch baud={}".format(baud))

            t_phase = _ticks_ms()
            t_beacon = 0
            rx = bad = echoed = 0
            while _ticks_diff(_ticks_ms(), t_phase) < int(dwell_ms):
                n = 0
                try:
                    n = rs.readinto(buf)
                except Exception:
                    n = 0
                if n and n > 0:
                    framer.feed(buf[:n])

                f = framer.next()
                while f is not None:
                    if _crc_ok(f):
                        rx += 1
                        rs.write(f)          # echo（DE 自動切換 + 等送完）
                        echoed += 1
                    else:
                        bad += 1
                    f = framer.next()

                if _ticks_diff(_ticks_ms(), t_beacon) >= int(beacon_ms):
                    rs.write(_beacon(baud))
                    t_beacon = _ticks_ms()

                time.sleep_ms(1)

            print("ECHO baud={} done  rx={} echoed={} bad={}".format(baud, rx, echoed, bad))


run()
