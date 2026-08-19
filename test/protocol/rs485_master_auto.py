# -*- coding: utf-8 -*-
"""RS485 主測板 — 自動收發 + 性能/可靠性統計（自包含，上傳即跑）

這塊板是主動端：輪流在每個 baud 跑「發一幀 → 等 echo → 比對 → 統計」，
每測完一個 baud 印一份報告。同時偵測對端的 beacon（seq=0xFFFF），
確認「對端有活著、線路通、baud 對」。

完全自包含：不 import 任何專案模組（driver/lib），
只要把本檔上傳就能跑（檔尾已直接 run()）。對端板先跑 rs485_echo_auto.py。

部署：
  1. 把本檔改名 main.py 丟到裝置根目錄 → 開機自動跑。
  2. 或 REPL：exec(open("rs485_master_auto.py").read())

TEST_MS 刻意 > 對端 DWELL_MS，這樣兩塊板即使不同時開機，
也能保證每個 baud 都有重疊時段，自動對到。

腳位（以程式碼為準）：
  GPIO8 = TX  → 收發器 DI      (MCU 送出)
  GPIO9 = RX  ← 收發器 RO      (MCU 收到)
  GPIO7 = EN  → 收發器 DE+RE   (active-high：1=發送, 0=接收)
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
TEST_MS = 20000               # 每個 baud 測多久（> 對端 DWELL_MS 以保證重疊）
PLEN = 64                     # 測試 payload 大小
TIMEOUT_MS = 300              # 單幀等 echo 上限
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


def _ticks_us():
    if hasattr(time, "ticks_us"):
        return time.ticks_us()
    return int(time.time() * 1_000_000)


def _ticks_diff(a, b):
    if hasattr(time, "ticks_diff"):
        return time.ticks_diff(a, b)
    return a - b


def _payload(seq, plen):
    return bytes([(i * 131 + seq) & 0xFF for i in range(plen)])


def _build(seq, payload):
    hdr = struct.pack("<4sHH", MAGIC, seq & 0xFFFF, len(payload))
    crc = binascii.crc32(hdr[4:] + payload) & 0xFFFFFFFF
    return hdr + payload + struct.pack("<I", crc)


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


def run(bauds=BAUDS, test_ms=TEST_MS, plen=PLEN, timeout_ms=TIMEOUT_MS,
        tx=TX, rx=RX, en=EN, uart_id=UART_ID):
    uart = UART(int(uart_id), baudrate=int(bauds[0]), tx=Pin(int(tx)), rx=Pin(int(rx)))
    rs = _RS485(uart, Pin(int(en), Pin.OUT, value=0), bauds[0])
    buf = bytearray(256)

    print("RS485 MASTER ready  (tx={} rx={} en={})".format(tx, rx, en))
    print("baud sweep: {}  test {}s each, payload {}B".format(
        list(bauds), test_ms // 1000, plen))

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

            seq = 0
            sent = lost = corrupt = beacons = 0
            rtt_sum = rtt_n = 0
            rtt_min = rtt_max = 0
            t_phase = _ticks_ms()
            print("--- test baud={} ({}s) ---".format(baud, test_ms // 1000))

            while _ticks_diff(_ticks_ms(), t_phase) < int(test_ms):
                frame = _build(seq, _payload(seq, plen))
                t0 = _ticks_us()
                rs.write(frame)                # DE 自動切換 + 等送完
                got_us = None

                while _ticks_diff(_ticks_us(), t0) < int(timeout_ms) * 1000:
                    n = 0
                    try:
                        n = rs.readinto(buf)
                    except Exception:
                        pass
                    if n and n > 0:
                        framer.feed(buf[:n])
                    while True:
                        fr = framer.next()
                        if fr is None:
                            break
                        if not _crc_ok(fr):
                            corrupt += 1
                            continue
                        s = fr[4] | (fr[5] << 8)
                        if s == 0xFFFF:            # beacon：對端在線
                            beacons += 1
                            continue
                        if s == seq:
                            pl = fr[6] | (fr[7] << 8)
                            if bytes(fr[8:8 + pl]) == _payload(seq, plen):
                                got_us = _ticks_diff(_ticks_us(), t0)
                                break
                    if got_us is not None:
                        break
                    time.sleep_ms(0)

                sent += 1
                if got_us is None:
                    lost += 1
                else:
                    rtt_n += 1
                    rtt_sum += got_us
                    if rtt_min == 0 or got_us < rtt_min:
                        rtt_min = got_us
                    if got_us > rtt_max:
                        rtt_max = got_us
                seq = (seq + 1) & 0xFFFF

            # 每個 baud 的報告
            if rtt_n:
                avg_us = rtt_sum // rtt_n
                thr_bps = (plen * 8 * 1_000_000) // avg_us if avg_us else 0
            else:
                avg_us = 0
                thr_bps = 0
            print("baud={}  sent={} ok={} lost={} corrupt={} beacons={}".format(
                baud, sent, rtt_n, lost, corrupt, beacons))
            print("    RTT avg={:.2f}ms min={:.2f}ms max={:.2f}ms  ~{} bit/s ({:.1f} KB/s)".format(
                avg_us / 1000, rtt_min / 1000, rtt_max / 1000, thr_bps, thr_bps / 8192))
            if beacons == 0:
                print("    ⚠️ 沒收到 beacon → 對端沒跑 / 線路不通 / baud 錯")
            if rtt_n == 0:
                print("    ❌ 此 baud 零往返")


run()
