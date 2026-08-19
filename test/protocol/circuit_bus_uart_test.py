# -*- coding: utf-8 -*-
"""CircuitBus 真實 UART 收發驗證（loopback + 對端 echo 兩種模式）

目的：驗證最近三項生產改動在「真實 UART」路徑下正確：
  1. circuit_bus 接收 buffer 硬編碼 RX_BUF_SIZE=4096（不再讀 config Buffer.size）
  2. bus_decode 消費 rx_hub 改用 view 模式（get_read_view/release_read）
  3. StreamParser.feed/compact 改用 memoryview slice 賦值（memmove）

覆蓋用例：單幀 / 黏包 / 半包 / 大幀(接近 8K) / CRC 壞幀 / 連續高速收發 / cache_hub read_into。

═══ 接線 ═══
  Loopback 模式（單機，預設）：用杜邦線把 UART 的 TX 與 RX 短接。
    config 現況 tx=39 / rx=41 → 短接 GPIO39 ↔ GPIO41。
  對端 echo 模式（雙機）：A 機跑 run_master()，B 機跑 run_peer_echo()，
    兩機 GND 共地、A.tx↔B.rx、A.rx↔B.tx（交叉）。

═══ 重要前提 ═══
  測試會自己開 machine.UART，所以執行前「全 app 不能同時持有這條 UART」。
  最乾淨做法：先把 config 的 UART.enable 設成 0（boot 不開 UART、circuit/action
  任務不綁線），在 REPL 執行：
      exec(open("test/protocol/circuit_bus_uart_test.py").read())
      run_loopback()          # 單機 loopback
  （若要雙機，見檔尾 run_master / run_peer_echo 的說明。）
"""

import struct
import time
import gc

try:
    import ubinascii as binascii
except ImportError:
    import binascii

from lib.proto import Proto, StreamParser, MAX_PAYLOAD, RX_BUF_SIZE, HDR_LEN, CRC_LEN
from lib.circuit_bus import CircuitBus

IS_MICROPYTHON = (getattr(__import__("sys"), "implementation", None)
                  and __import__("sys").implementation.name == "micropython")

# 測試用 cmd（不與任何 schema 衝突）
_CMD = 0x18F1
_HUB_OFF = 2
# 115200 8N1 ≈ 86.8µs/byte；loopback 下 RX FIFO 只有 ~128B，寫入期間必須
# 邊寫邊讀，否則 8K 幀阻塞寫入 ~700ms 時 FIFO 溢位。64B 一段 ≈ 5.6ms，留 2x 餘量。
_SEND_CHUNK = 64


# ═══════════════════════════════════════════════════════════════
#  基礎工具
# ═══════════════════════════════════════════════════════════════

def _ticks_ms():
    if hasattr(time, "ticks_ms"):
        return time.ticks_ms()
    return int(time.time() * 1000)


def _ticks_diff(a, b):
    if hasattr(time, "ticks_diff"):
        return time.ticks_diff(a, b)
    return a - b


def _sleep_ms(ms):
    if hasattr(time, "sleep_ms"):
        time.sleep_ms(ms)
    else:
        time.sleep(ms / 1000.0)


def _uart_open(uart_id=1, baudrate=115200, tx=39, rx=41):
    if not IS_MICROPYTHON:
        raise RuntimeError("UART 測試需在 MicroPython 裝置上執行")
    import machine
    try:
        return machine.UART(
            int(uart_id), baudrate=int(baudrate),
            bits=8, parity=None, stop=1,
            tx=machine.Pin(int(tx)), rx=machine.Pin(int(rx)),
            timeout=0, timeout_char=0,
        )
    except TypeError:
        return machine.UART(
            int(uart_id), baudrate=int(baudrate),
            bits=8, parity=None, stop=1,
            tx=int(tx), rx=int(rx),
            timeout=0, timeout_char=0,
        )


def _make_payload(seq, size):
    """payload = u16 seq + 確定性 data。size 是 data 長度（不含 seq 2B）。"""
    data = bytes([(i * 131 + seq) & 0xFF for i in range(size)])
    return struct.pack("<H", seq & 0xFFFF) + data


def _frame(seq, size):
    return bytes(Proto.pack(_CMD, _make_payload(seq, size)))


def _seq_of(payload):
    return payload[0] | (payload[1] << 8)


# ═══════════════════════════════════════════════════════════════
#  Harness：把 UART 包成 CircuitBus，走「poll → rx_hub view → parser.feed」
#  這條與 BusDecodeTask 完全一致的消費路徑（正是要驗證的新代碼路徑）。
# ═══════════════════════════════════════════════════════════════

class Harness:
    def __init__(self, uart, baudrate=115200):
        from lib.buffer_hub import AtomicStreamHub
        self.uart = uart
        self.baudrate = int(baudrate)
        self.hub = AtomicStreamHub(RX_BUF_SIZE + _HUB_OFF, num_buffers=4, try_dma=False)
        self.cb = CircuitBus(uart, label="LOOP", rx_hub=self.hub)
        self.parser = StreamParser()
        self._got = []          # 累積已解出的 (seq, payload)
        self._drain_uart()

    def _drain_uart(self):
        """清掉開機後 RX FIFO 裡可能殘留的垃圾。"""
        tmp = bytearray(512)
        for _ in range(32):
            n = self._readinto(tmp)
            if n is None or n <= 0:
                break

    def _readinto(self, buf):
        try:
            n = self.uart.readinto(buf)
            return 0 if n is None else n
        except Exception:
            try:
                raw = self.uart.read(len(buf))
                if not raw:
                    return 0
                buf[:len(raw)] = raw
                return len(raw)
            except Exception:
                return 0

    def poll_decode(self):
        """一次 poll（UART→rx_hub）+ 把 rx_hub 全部 slot 餵進 parser。
        完全對齊 tasks/bus_decode.py 的 view 消費迴圈。"""
        self.cb.poll()
        while True:
            view = self.hub.get_read_view()
            if view is None:
                break
            try:
                ln = view[0] | (view[1] << 8)
                if ln > 0:
                    self.parser.feed(view[_HUB_OFF:_HUB_OFF + ln])
            finally:
                self.hub.release_read()
        for _v, _a, cmd, payload in self.parser.pop():
            if cmd == _CMD:
                self._got.append((_seq_of(payload), bytes(payload)))

    def send_interleaved(self, data):
        """分小段寫入 + 每段之後立刻 poll，避免 loopback 時 RX FIFO 溢位。
        資料仍是一個連續位元組流（黏包），parser 靠 SOF/length 自行切幀。"""
        mv = memoryview(data)
        off = 0
        ln = len(mv)
        while off < ln:
            n = min(_SEND_CHUNK, ln - off)
            self.cb.write(mv[off:off + n])
            off += n
            # 等這一段在線上排空（~n bytes 傳輸時間）+ 餘量，再讀 RX
            self._sleep_ms(max(1, int(n * 10 * 1000 / self.baudrate) + 3))
            self.poll_decode()

    def collect(self, want, timeout_ms=5000):
        """繼續 poll 直到解出 want 幀或逾時。回傳累積的 (seq, payload) 清單。"""
        start = _ticks_ms()
        while len(self._got) < want and _ticks_diff(_ticks_ms(), start) < int(timeout_ms):
            self.poll_decode()
            self._sleep_ms(1)
        return self._got

    def reset(self):
        self._got = []
        self.parser = StreamParser()


# ═══════════════════════════════════════════════════════════════
#  測試用例
# ═══════════════════════════════════════════════════════════════

def test_single_frame(h):
    f = _frame(0, 1024)
    h.send_interleaved(f)
    got = h.collect(1)
    assert len(got) == 1, "應解出 1 幀, 實際 {}".format(len(got))
    seq, payload = got[0]
    assert seq == 0 and len(payload) == 1024 + 2
    assert payload[2:] == _make_payload(0, 1024)[2:], "單幀 payload 內容不符"


def test_sticky_packets(h):
    # 三幀黏成一串連續位元組流，一次 send_interleaved 送出
    stream = _frame(0, 1024) + _frame(1, 1024) + _frame(2, 1024)
    h.send_interleaved(stream)
    got = h.collect(3)
    assert len(got) == 3, "黏包應解出 3 幀, 實際 {}".format(len(got))
    for i, (seq, payload) in enumerate(got):
        assert seq == i, "黏包 seq 錯序: got {} want {}".format(seq, i)
        assert len(payload) == 1024 + 2


def test_half_packet(h):
    f = _frame(0, 2048)
    half = len(f) // 2
    # 前半：不該解出任何幀
    h.send_interleaved(f[:half])
    assert len(h._got) == 0, "半包不該提前解出, 卻解出 {} 幀".format(len(h._got))
    # 後半：補齊後應解出 1 幀
    h.send_interleaved(f[half:])
    got = h.collect(1)
    assert len(got) == 1 and got[0][0] == 0
    assert len(got[0][1]) == 2048 + 2, "半包重組後長度不符"


def test_large_frame(h):
    # 接近 MAX_PAYLOAD：payload = 8190（u16 seq + 8188 data），
    # 整幀 = 8203 bytes > RX_BUF_SIZE(4096)，會跨多次 poll 分 chunk 到達。
    payload = _make_payload(0, MAX_PAYLOAD - 2)
    assert len(payload) == MAX_PAYLOAD
    f = bytes(Proto.pack(_CMD, payload))
    assert len(f) == HDR_LEN + MAX_PAYLOAD + CRC_LEN
    h.send_interleaved(f)
    got = h.collect(1, timeout_ms=8000)
    assert len(got) == 1, "大幀應解出 1 幀, 實際 {}".format(len(got))
    seq, p = got[0]
    assert seq == 0 and len(p) == MAX_PAYLOAD
    assert p[2:] == payload[2:], "大幀 payload 內容不符（跨 chunk 重組出錯）"


def test_crc_corrupt(h):
    good1 = _frame(0, 1024)
    bad = bytearray(_frame(1, 1024))
    # 破壞 payload 中間一個 byte → CRC 必錯
    k = HDR_LEN + 500
    bad[k] ^= 0xFF
    good2 = _frame(2, 1024)
    h.send_interleaved(bytes(good1) + bytes(bad) + bytes(good2))
    got = h.collect(2, timeout_ms=6000)
    seqs = [s for s, _ in got]
    assert 0 in seqs, "好幀 seq0 丟失"
    assert 1 not in seqs, "CRC 壞幀被誤解出"
    assert 2 in seqs, "壞幀之後的 resync 失敗"
    assert len(got) == 2, "應只解出 2 幀好幀, 實際 {}".format(len(got))


def test_continuous_stress(h):
    N = 200
    payload_size = 1024
    total = 0
    t0 = _ticks_ms()
    for s in range(N):
        h.send_interleaved(_frame(s, payload_size))
        total += payload_size + 2 + HDR_LEN + CRC_LEN
    got = h.collect(N, timeout_ms=20000)
    dt = _ticks_diff(_ticks_ms(), t0)
    assert len(got) == N, "連續收發應解出 {} 幀, 實際 {}".format(N, len(got))
    for i, (seq, p) in enumerate(got):
        assert seq == i, "連續收發 seq 錯序: got {} want {}".format(seq, i)
        assert len(p) == payload_size + 2
    kbps = int(total * 8 / max(dt, 1))  # kbit/s
    print("    throughput ~{} kbit/s ({} frames, {} ms)".format(kbps, N, dt))


def test_cache_readinto(h):
    # 驗證 _commit 的 cache_hub 鏡像 + read_into（action_task_1 顯示面板路徑）。
    # 用 40B 小幀、單次 write + 單次 poll，避免分段。
    payload = _make_payload(7, 25)
    f = bytes(Proto.pack(_CMD, payload))
    # 首次 read_into 惰性建立 cache_hub（回 0）
    buf = bytearray(512)
    h.cb.read_into(buf)
    h.cb.write(f)
    h._sleep_ms(30)
    h.cb.poll()
    n = h.cb.read_into(buf)
    assert n == len(f), "read_into 長度錯: {} != {}".format(n, len(f))
    assert bytes(buf[:n]) == f, "cache_hub 鏡像內容不符"


# ═══════════════════════════════════════════════════════════════
#  Loopback 主流程
# ═══════════════════════════════════════════════════════════════

def run_loopback(uart_id=1, baudrate=115200, tx=39, rx=41):
    print("=" * 56)
    print("CircuitBus 真實 UART loopback 驗證")
    print("UART{} baud={} tx={} rx={}  (請確認 TX↔RX 已短接)".format(
        uart_id, baudrate, tx, rx))
    print("=" * 56)

    uart = _uart_open(uart_id, baudrate, tx=tx, rx=rx)
    h = Harness(uart, baudrate=baudrate)

    cases = [
        ("單幀 (1KB)", lambda: test_single_frame(h)),
        ("黏包 (3×1KB)", lambda: test_sticky_packets(h)),
        ("半包 (2KB 分兩段)", lambda: test_half_packet(h)),
        ("大幀 (接近 8K, 8203B)", lambda: test_large_frame(h)),
        ("CRC 壞幀丟棄 + resync", lambda: test_crc_corrupt(h)),
        ("連續高速收發 (200×1KB)", lambda: test_continuous_stress(h)),
        ("cache_hub read_into 路徑", lambda: test_cache_readinto(h)),
    ]

    passed = 0
    failed = 0
    for name, fn in cases:
        h.reset()
        gc.collect()
        try:
            fn()
            print("  [PASS] {}".format(name))
            passed += 1
        except Exception as e:
            print("  [FAIL] {}  → {}".format(name, e))
            failed += 1

    print("-" * 56)
    print("結果: {} 通過, {} 失敗".format(passed, failed))
    if failed == 0:
        print("✅ 全部通過 — view 消費 + feed slice 賦值在真實 UART 下正確")
    else:
        print("❌ 有失敗 — 請回報上方 [FAIL] 用例")
    print("=" * 56)
    return failed == 0


# ═══════════════════════════════════════════════════════════════
#  對端 echo 模式（雙機驗證，可選）
# ═══════════════════════════════════════════════════════════════

def run_peer_echo(uart_id=1, baudrate=115200, tx=39, rx=41, seconds=20):
    """第二台裝置跑這個：把收到的每一筆位元組原樣回送（echo）。
    與另一台 run_master() 對接，用兩台獨立時鐘驗證收發（非 loopback）。"""
    uart = _uart_open(uart_id, baudrate, tx=tx, rx=rx)
    print("PEER echo on UART{} baud={}, echo {}s".format(uart_id, baudrate, seconds))
    buf = bytearray(512)
    start = _ticks_ms()
    while _ticks_diff(_ticks_ms(), start) < int(seconds) * 1000:
        n = 0
        try:
            n = uart.readinto(buf)
        except Exception:
            try:
                raw = uart.read(len(buf))
                if raw:
                    buf[:len(raw)] = raw
                    n = len(raw)
            except Exception:
                n = 0
        if n and n > 0:
            uart.write(buf[:n])
        else:
            _sleep_ms(1)
    print("PEER echo done")


def run_master(uart_id=1, baudrate=115200, tx=39, rx=41, frames=200, payload_size=1024):
    """第一台裝置跑這個：發出測試幀並自我驗證（對端需跑 run_peer_echo）。
    因為是跨機 echo，驗證內容等同 loopback 各用例，但用兩台獨立時鐘。"""
    print("=" * 56)
    print("CircuitBus 雙機 echo 驗證 (本機=master)")
    print("UART{} baud={} tx={} rx={}  (對端需 run_peer_echo)".format(
        uart_id, baudrate, tx, rx))
    print("=" * 56)
    uart = _uart_open(uart_id, baudrate, tx=tx, rx=rx)
    h = Harness(uart, baudrate=baudrate)

    t0 = _ticks_ms()
    total = 0
    for s in range(frames):
        f = _frame(s, payload_size)
        h.send_interleaved(f)
        total += len(f)
    got = h.collect(frames, timeout_ms=30000)
    dt = _ticks_diff(_ticks_ms(), t0)

    ok = len(got) == frames
    if ok:
        for i, (seq, p) in enumerate(got):
            if seq != i or len(p) != payload_size + 2:
                ok = False
                break
    print("結果: 收到 {} / {} 幀, 順序{}".format(
        len(got), frames, "正確" if ok else "錯"))
    if dt > 0:
        print("throughput ~{} kbit/s".format(int(total * 8 / dt)))
    print("✅ PASS" if ok else "❌ FAIL")
    return ok


if __name__ == "__main__":
    run_loopback()
