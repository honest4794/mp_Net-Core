# -*- coding: utf-8 -*-
"""RS485 一發一收 (ping-pong echo) 性能 + 可靠性測試

驗證對象：slave/driver/uart_drv.py 的 _Rs485Uart（DE 方向腳自動切換）。
  write() 內等送完(txdone)再放低 DE 的時序，直接反映在「無故障」統計上：
  - DE 太早放低 → 尾 byte 截斷 → CRC 錯 → corrupt++
  - DE 太晚放低 → echo 延遲增加 → RTT 上升
  - 任何 lost/corrupt → 都是傳輸層或方向切換故障的信號。

═══ 接線（兩塊板，RS485 匯流排）═══
  每塊板都要一顆 RS485 收發器（如 MAX485）：
    板 A：GPIO8→DI、GPIO9→RO、GPIO7→DE+RE
    板 B：GPIO8→DI、GPIO9→RO、GPIO7→DE+RE
  匯流排：A 的 A 接 B 的 A，A 的 B 接 B 的 B；兩板 GND 共地。
  兩端各接一顆 120Ω 終端電阻（距離遠時）。
  注意：DI/RO 是「各自」的腳位，A 的 DI 接 A 收發器 DI，別跟 B 交叉——
  匯流排只接 A/B 兩條差動線，TX/RX 是單端內部線，不跨板。

═══ 執行（兩塊板角色不同）═══
  對端板（被動 echo，先跑）：
      exec(open("test/protocol/rs485_echo_test.py").read())
      run_echo()                       # 或 run_echo(tx=8, rx=9, en=7, baudrate=9600)
  主測板（主動發送 + 統計）：
      exec(open("test/protocol/rs485_echo_test.py").read())
      run_master()                     # 或 run_master(tx=8, rx=9, en=7, baudrate=9600)

  預設腳位/波特率對齊 ports/ESP32-S3-RS485/config.json（tx=8, rx=9, en=7, 9600）。

═══ 測試內容 ═══
  run_master 對多個 payload 檔位（16/64/256/1024）各跑 N 幀 ping-pong，
  輸出：RTT(avg/min/max)、有效吞吐、lost/corrupt 數、最終 PASS/FAIL。
"""

import struct
import time

try:
    import ubinascii as binascii
except ImportError:
    import binascii

from machine import UART, Pin
from driver.uart_drv import _Rs485Uart

MAGIC = b"RS48"
_HDR = 12                     # 4 magic + 2 seq + 2 plen + 4 crc


def _ticks_us():
    if hasattr(time, "ticks_us"):
        return time.ticks_us()
    return int(time.time() * 1_000_000)


def _ticks_diff(a, b):
    if hasattr(time, "ticks_diff"):
        return time.ticks_diff(a, b)
    return a - b


def _sleep_ms(ms):
    if hasattr(time, "sleep_ms"):
        time.sleep_ms(ms)
    else:
        time.sleep(ms / 1000.0)


def _open_rs485(uart_id=1, baudrate=9600, tx=8, rx=9, en=7):
    uart = UART(int(uart_id), baudrate=int(baudrate), tx=Pin(int(tx)), rx=Pin(int(rx)))
    return _Rs485Uart(uart, Pin(int(en), Pin.OUT, value=0), baudrate)


def _payload(seq, plen):
    return bytes([(i * 131 + seq) & 0xFF for i in range(plen)])


def _build(seq, plen):
    """frame = magic(4) + seq(2) + plen(2) + payload + crc32(seq..payload)(4)"""
    hdr = struct.pack("<4sHH", MAGIC, seq & 0xFFFF, plen)
    payload = _payload(seq, plen)
    crc = binascii.crc32(hdr[4:] + payload) & 0xFFFFFFFF
    return hdr + payload + struct.pack("<I", crc)


def _crc_ok(frame):
    if len(frame) < _HDR:
        return False
    plen = frame[6] | (frame[7] << 8)
    if len(frame) != _HDR + plen:
        return False
    # crc 固定在最尾 4 byte；覆蓋範圍 = seq..payload（即 frame[4:-4]）
    crc_got = frame[-4] | (frame[-3] << 8) | (frame[-2] << 16) | (frame[-1] << 24)
    crc_calc = binascii.crc32(frame[4:-4]) & 0xFFFFFFFF
    return crc_got == crc_calc


class _Framer:
    """累積 byte 流、依 MAGIC + length 切出完整幀（非阻塞，碎片/黏包都安全）。"""

    def __init__(self):
        self.buf = bytearray()

    def feed(self, data):
        self.buf.extend(data)

    def next(self):
        """回傳下一幀完整 bytes（含 crc），或 None（還沒齊）。"""
        while True:
            i = self.buf.find(MAGIC)
            if i < 0:
                # 保留尾部 3 byte，防 MAGIC 跨段
                if len(self.buf) > 3:
                    self.buf = self.buf[-3:]
                return None
            if i > 0:
                del self.buf[:i]           # 丟掉前面的雜訊/錯位
            if len(self.buf) < 8:
                return None
            plen = self.buf[6] | (self.buf[7] << 8)
            total = _HDR + plen
            if len(self.buf) < total:
                return None
            frame = bytes(self.buf[:total])
            del self.buf[:total]
            return frame


def _drain_uart(uart):
    """清掉開機後 RX FIFO 殘留雜訊。"""
    tmp = bytearray(256)
    for _ in range(32):
        try:
            if uart.any():
                uart.readinto(tmp)
            else:
                break
        except Exception:
            break


# ═══════════════════════════════════════════════════════════════
#  對端：被動 echo
# ═══════════════════════════════════════════════════════════════

def run_echo(uart_id=1, baudrate=9600, tx=8, rx=9, en=7, duration=0):
    """被動 echo：收到整幀就原樣回送。duration>0 表示跑 N 秒後自動停。"""
    uart = _open_rs485(uart_id, baudrate, tx, rx, en)
    _drain_uart(uart)
    framer = _Framer()
    print("RS485 ECHO on UART{} baud={} tx={} rx={} en={}".format(uart_id, baudrate, tx, rx, en))

    t0 = _ticks_us()
    echoed = 0
    while True:
        if duration and _ticks_diff(_ticks_us(), t0) >= int(duration) * 1_000_000:
            break
        n = 0
        try:
            n = uart.readinto(_buf)
        except Exception:
            try:
                raw = uart.read(256)
                if raw:
                    _buf[:len(raw)] = raw
                    n = len(raw)
            except Exception:
                n = 0
        if n and n > 0:
            framer.feed(_buf[:n])
        while True:
            f = framer.next()
            if f is None:
                break
            if _crc_ok(f):
                uart.write(f)          # DE 自動切換 + 等送完
                echoed += 1
        _sleep_ms(1)
    print("RS485 ECHO done, echoed={}".format(echoed))


_buf = bytearray(256)


# ═══════════════════════════════════════════════════════════════
#  主測：主動發送 + 統計
# ═══════════════════════════════════════════════════════════════

def _wait_echo(uart, framer, want_seq, timeout_ms):
    """等一幀 echo 回來並通過 CRC，回傳 (seq, payload) 或 None。"""
    start = _ticks_us()
    deadline = start + int(timeout_ms) * 1000
    while _ticks_diff(_ticks_us(), start) < int(timeout_ms) * 1000:
        n = 0
        try:
            if uart.any():
                n = uart.readinto(_buf)
        except Exception:
            pass
        if n and n > 0:
            framer.feed(_buf[:n])
        f = framer.next()
        while f is not None:
            if _crc_ok(f):
                seq = f[4] | (f[5] << 8)
                plen = f[6] | (f[7] << 8)
                return seq, bytes(f[8:8 + plen])
            f = framer.next()
        _sleep_ms(0)
    return None


def run_master(uart_id=1, baudrate=9600, tx=8, rx=9, en=7,
               sizes=(16, 64, 256, 1024), frames=200, timeout_ms=500):
    """主動發送：對每個 payload 檔位跑 frames 幀 ping-pong，量 RTT/吞吐/錯誤。"""
    uart = _open_rs485(uart_id, baudrate, tx, rx, en)
    _drain_uart(uart)
    framer = _Framer()

    print("=" * 60)
    print("RS485 ping-pong echo 測試 (master)")
    print("UART{} baud={} tx={} rx={} en={}".format(uart_id, baudrate, tx, rx, en))
    print("=" * 60)

    all_ok = True
    for size in sizes:
        lost = 0
        corrupt = 0
        rtts = []
        for seq in range(frames):
            frame = _build(seq, size)
            t0 = _ticks_us()
            uart.write(frame)                     # 走 _Rs485Uart：DE 自動切換
            r = _wait_echo(uart, framer, seq, timeout_ms)
            t1 = _ticks_us()
            rtt_us = _ticks_diff(t1, t0)
            if r is None:
                lost += 1
                continue
            rseq, rpayload = r
            if rseq != seq or rpayload != _payload(seq, size):
                corrupt += 1
                continue
            rtts.append(rtt_us)

        n = len(rtts)
        if n:
            avg_us = sum(rtts) // n
            mn_us = min(rtts)
            mx_us = max(rtts)
            # 有效吞吐 = 單向 payload bits / 平均 RTT
            thr_bps = (size * 8 * 1_000_000) // avg_us if avg_us else 0
        else:
            avg_us = mn_us = mx_us = 0
            thr_bps = 0

        ok = (lost == 0 and corrupt == 0 and n == frames)
        all_ok = all_ok and ok
        print("-" * 60)
        print("payload {:>5}B  frames={}  lost={}  corrupt={}".format(size, frames, lost, corrupt))
        print("  RTT avg={:.2f}ms min={:.2f}ms max={:.2f}ms".format(
            avg_us / 1000, mn_us / 1000, mx_us / 1000))
        print("  有效吞吐 ~{} bit/s  ({:.1f} KB/s)".format(thr_bps, thr_bps / 8192))
        print("  結果: {}".format("PASS" if ok else "FAIL"))
        _sleep_ms(20)

    print("=" * 60)
    if all_ok:
        print("✅ 全部通過 — 傳輸無故障（DE 切換 + txdone 時序正確）")
    else:
        print("❌ 有失敗 — lost/corrupt 非零，請檢查接線/終端電阻/DE 腳")
    print("=" * 60)
    return all_ok


if __name__ == "__main__":
    # 預設跑 echo（對端先跑）；要跑主測改呼叫 run_master()
    run_echo()
