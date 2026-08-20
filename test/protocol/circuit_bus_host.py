# -*- coding: utf-8 -*-
"""CircuitBus 主機（發送端）— 每秒送一幀 AC...FF 10B，收 echo 驗證並統計（自包含，上傳即跑）

協議（統一 10 位元組）：
  幀 = [0xAC] + 8B 內容 + [0xFF]
        ├ 0xAC = 頭
        ├ 8B   = u32 序號(LE, 遞增) + 4B 填充(11 22 33 44，可改隨機)
        └ 0xFF = 尾

流程：
  每 1 秒送一幀 → 等對端（circuit_bus_recv.py）echo 同一幀回來 →
  驗證頭/尾/序號/填充一致 → 收到的任何 byte 都「馬上列印」，
  並統計成功 / 失敗（失敗 = 收到不符 或 逾時沒等到）。

處理方式（中央緩衝、避免 GC）：
  - 發送幀用預分配 bytearray 直接改內容（不逐幀建 bytes）。
  - RX 每讀一次全收（uart.any()），丟中央緩衝排列、切割（head 指標，不用 del）。
  - 不逐幀 GC：rxbuf / 組幀緩衝 / 發送幀全部重用。

接線 / 部署：同 circuit_bus_recv.py（A-A、B-B、GND 共地）。
  本檔改名 main.py 丟根目錄 → 開機自動跑；或 REPL exec。
"""

import time
from machine import UART, Pin

BAUD = 9600                    # 與接收器一致
TX, RX, EN = 8, 9, 7           # DI, RO, DE+RE
UART_ID = 1
INTERVAL_MS = 1000             # 每秒送一幀
ECHO_TIMEOUT_MS = 600          # 等 echo 上限
FRAME_LEN = 10                 # 統一 10 位元組
HEAD = 0xAC
TAIL = 0xFF

BENCH_BAUDS = (9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600)
BENCH_MS = 10000              # 每個 baud 測多久（時間盒）
BENCH_TIMEOUT_MS = 300        # 單幀等 echo 上限（10B @9600 往返 ~15ms，300ms 很鬆）
BENCH_BATCH = 20              # 一批幾幀（半雙工：發一批 → 停 → 等整批回覆）
BATCH_GAP_MS = 0              # 依 baud 動態算：3×幀傳輸時間（min 10ms），發完一批停這個長度


# ── RS485 半雙工方向控制（與 driver._Rs485Uart 同一套時序） ──
class _RS485:
    def __init__(self, uart, en_pin, baudrate):
        self.io = uart
        self.en = en_pin
        self.baud = int(baudrate)
        self.en.value(0)                       # 閒置 = 接收

    def _wait_sent(self, nbytes):
        # 半雙工 ping-pong：DE 必須「剛好送完就切回接收」，才能接住對端 echo 開頭。
        # 實傳時間 = nbytes * 10bit / baud；sleep 多一點點就吃掉 echo 開頭。
        # 10B@9600 → 10.4ms。這裡只算到「資料離開發送端」的最小值。
        t = (nbytes * 10 * 1000) // self.baud
        time.sleep_ms(t if t >= 1 else 1)

    def write(self, data):
        self.en.value(1)
        time.sleep_ms(2)                       # 驅動器使能穩定
        try:
            n = self.io.write(data)
            self._wait_sent(len(data) if (n is None or n <= 0) else n)
            return n
        finally:
            self.en.value(0)                   # 送完才回接收

    def readinto(self, buf):
        return self.io.readinto(buf)


# ── 中央緩衝：RX byte 流 → 依 AC/FF 固定 10B 切割（head 指標，不用 del） ──
class _Assembler:
    def __init__(self, cap=64):
        self.buf = bytearray(cap)
        self.n = 0             # 有效 byte 數（存在 buf[0:n]）
        self.head = 0          # 第一個未消費 byte 的位置
        self.garbage = 0       # 重同步時丟掉的垃圾 byte 數

    def feed(self, data):
        ln = len(data)
        if ln <= 0:
            return
        if self.n + ln > len(self.buf):
            self._compact()
            if self.n + ln > len(self.buf):
                self.buf = bytearray(max(len(self.buf) * 2, self.n + ln))
        self.buf[self.n:self.n + ln] = data
        self.n += ln

    def _compact(self):
        if self.head <= 0:
            return
        m = self.n - self.head
        if m > 0:
            self.buf[:m] = self.buf[self.head:self.n]
        self.n = m
        self.head = 0

    def next(self):
        """回傳完整 10B 幀(bytes) 或 None。頭尾不齊/錯位自動重同步。"""
        while True:
            if self.n - self.head < 2:
                self._compact()
                return None
            idx = self.head
            while idx < self.n and self.buf[idx] != HEAD:
                idx += 1
            if idx >= self.n:
                self.head = max(self.n - 9, 0) if self.n >= 9 else 0
                self._compact()
                return None
            if idx > self.head:
                self.garbage += (idx - self.head)   # 前導垃圾 byte 數
                self.head = idx
            if self.n - self.head < FRAME_LEN:
                self._compact()
                return None
            if self.buf[self.head + FRAME_LEN - 1] == TAIL:
                f = bytes(self.buf[self.head:self.head + FRAME_LEN])
                self.head += FRAME_LEN
                self._compact()
                return f
            self.head += 1     # 尾不是 FF → 假頭，跳過再找
            self.garbage += 1


def _ticks_ms():
    return time.ticks_ms() if hasattr(time, "ticks_ms") else int(time.time() * 1000)


def _ticks_us():
    return time.ticks_us() if hasattr(time, "ticks_us") else int(time.time() * 1_000_000)


def _ticks_diff(a, b):
    return time.ticks_diff(a, b) if hasattr(time, "ticks_diff") else a - b


def _sleep_ms(ms):
    if hasattr(time, "sleep_ms"):
        time.sleep_ms(ms)
    else:
        time.sleep(ms / 1000.0)


def _hex(data):
    return " ".join("{:02X}".format(b) for b in data)


def _text(data):
    """把 byte 轉成可印文字，非可列印字元顯示為 '.'。
    MicroPython 的 bytes.decode 不支援 errors=replace，遇到 binary 會拋
    UnicodeError；這裡先逐 byte 過濾成可列印 ASCII，decode 永不失敗。"""
    out = bytearray(len(data))
    for i in range(len(data)):
        b = data[i]
        out[i] = b if (32 <= b < 127) else 46   # 46 = '.'
    return bytes(out).decode("utf-8")


def _drain(uart):
    tmp = bytearray(64)
    for _ in range(8):
        try:
            if uart.any():
                uart.readinto(tmp)
            else:
                break
        except Exception:
            break


def _verify(f, seq):
    """驗證 echo 幀：頭/尾/序號/填充 全部一致才回 (True, "")。"""
    if f[0] != HEAD:
        return False, "頭非AC"
    if f[FRAME_LEN - 1] != TAIL:
        return False, "尾非FF"
    got = f[1] | (f[2] << 8) | (f[3] << 16) | (f[4] << 24)
    if got != (seq & 0xFFFFFFFF):
        return False, "seq不符(got={})".format(got)
    if (f[5], f[6], f[7], f[8]) != (0x11, 0x22, 0x33, 0x44):
        return False, "填充不符"
    return True, ""


def run(baud=BAUD, interval_ms=INTERVAL_MS, tx=TX, rx=RX, en=EN, uart_id=UART_ID):
    uart = UART(int(uart_id), baudrate=int(baud), tx=Pin(int(tx)), rx=Pin(int(rx)))
    rs = _RS485(uart, Pin(int(en), Pin.OUT, value=0), baud)
    _drain(uart)

    asm = _Assembler()
    rxbuf = bytearray(FRAME_LEN * 4)
    rxmv = memoryview(rxbuf)   # 讀取緩衝（中央，重用）
    frame = bytearray(FRAME_LEN)   # 發送幀緩衝（中央，直接改內容）

    print("=" * 56)
    print("CIRCUIT_BUS 主機 (baud={} tx={} rx={} en={})".format(baud, tx, rx, en))
    print("每秒送一幀: AC + seq(u32) + 11 22 33 44 + FF，收 echo 驗證")
    print("=" * 56)

    seq = 0
    sent = ok = bad = 0
    while True:
        t_cycle = _ticks_ms()

        # 組幀：直接寫入預分配 frame（零分配）
        frame[0] = HEAD
        frame[1] = seq & 0xFF
        frame[2] = (seq >> 8) & 0xFF
        frame[3] = (seq >> 16) & 0xFF
        frame[4] = (seq >> 24) & 0xFF
        frame[5] = 0x11
        frame[6] = 0x22
        frame[7] = 0x33
        frame[8] = 0x44
        frame[9] = TAIL
        rs.write(frame)
        sent += 1
        print("TX -> seq={} hex={}".format(seq, _hex(frame)))
        _drain(uart)                # 清掉 DE 切換瞬間 RX 浮空採樣出的垃圾，別讓它混進 echo

        # 等 echo，收到的全部馬上印
        t0 = _ticks_ms()
        got_echo = False
        while _ticks_diff(_ticks_ms(), t0) < ECHO_TIMEOUT_MS:
            n = 0
            try:
                if uart.any():
                    n = rs.readinto(rxbuf)
            except Exception:
                n = 0
            if n and n > 0:
                print("RX raw [{}B] hex={} text={!r}".format(
                    n, _hex(rxmv[:n]), _text(rxmv[:n])))
                asm.feed(rxmv[:n])
                f = asm.next()
                while f is not None:
                    okf, why = _verify(f, seq)
                    if okf:
                        ok += 1
                        got_echo = True
                        print("  ✓ 成功: echo 回 seq={} 內容一致".format(seq))
                    else:
                        bad += 1
                        got_echo = True
                        print("  ✗ 收到不符 ({}): hex={}".format(why, _hex(f)))
                    f = asm.next()
            _sleep_ms(1)

        if not got_echo:
            bad += 1
            print("  ✗ 沒等到 echo（timeout {}ms）".format(ECHO_TIMEOUT_MS))

        if sent % 10 == 0:
            print("-- 統計 (累計): sent={} ok={} bad={}".format(sent, ok, bad))

        seq = (seq + 1) & 0xFFFFFFFF
        rem = int(interval_ms) - _ticks_diff(_ticks_ms(), t_cycle)
        if rem > 0:
            _sleep_ms(rem)


def bench_run(bauds=BENCH_BAUDS, bench_ms=BENCH_MS, timeout_ms=BENCH_TIMEOUT_MS,
              batch=BENCH_BATCH, tx=TX, rx=RX, en=EN, uart_id=UART_ID):
    """性能測試 — 速度邊界掃描（半雙工批次規則，對齊網絡測試精神）

    半雙工規則：發送一批 → 停止發送 → 接收整批回覆 → 統計。
    對端 circuit_bus_recv.py 的 run_auto_bench() 也是「收集一批 → 整批回覆」。
    每個 baud 在時間盒內盡量發批 → 驗證整批 echo 的 seq → 統計，
    時間盒結束印一份報告，掃完所有 baud 再整個循環。
    """
    uart = UART(int(uart_id), baudrate=int(bauds[0]), tx=Pin(int(tx)), rx=Pin(int(rx)))
    rs = _RS485(uart, Pin(int(en), Pin.OUT, value=0), bauds[0])

    print("=" * 62)
    print("CIRCUIT_BUS 速度邊界掃描 (bench, 半雙工批次)")
    print("tx={} rx={} en={}  10B 幀/批{}幀, {}s/baud".format(tx, rx, en, batch, bench_ms // 1000))
    print("baud sweep: {}".format(list(bauds)))
    print("=" * 62)

    while True:
        for baud in bauds:
            baud = int(baud)
            try:
                uart.init(baudrate=baud)
            except Exception:
                pass
            rs.baud = baud
            _drain(uart)
            # 發完一批後停多久：等對端收集完一批 + 開始回覆（3×幀傳輸時間）
            frame_tx_ms = (FRAME_LEN * 10 * 1000) // baud
            gap_ms = max(10, 3 * frame_tx_ms)

            asm = _Assembler()
            rxbuf = bytearray(FRAME_LEN * 4)
            rxmv = memoryview(rxbuf)
            frame = bytearray(FRAME_LEN)

            seq = 0
            sent = ok = lost = corrupt = garbage = 0
            rtt_sum = rtt_n = 0
            rtt_min = rtt_max = 0
            t_phase = _ticks_ms()
            print("--- test baud={} ({}s) gap={}ms ---".format(baud, bench_ms // 1000, gap_ms))

            while _ticks_diff(_ticks_ms(), t_phase) < int(bench_ms):
                # ── 發送一批（只切一次 DE，不逐幀切）──
                batch_seq = []
                for i in range(batch):
                    s = (seq + i) & 0xFFFFFFFF
                    frame[0] = HEAD
                    frame[1] = s & 0xFF
                    frame[2] = (s >> 8) & 0xFF
                    frame[3] = (s >> 16) & 0xFF
                    frame[4] = (s >> 24) & 0xFF
                    frame[5] = 0x11
                    frame[6] = 0x22
                    frame[7] = 0x33
                    frame[8] = 0x44
                    frame[9] = TAIL
                    rs.write(frame)
                    batch_seq.append(s)
                    sent += 1
                # 發完一整批 → 停止發送，DE 回到接收，等對端整批回覆
                _sleep_ms(gap_ms)

                # ── 接收模式：等整批 echo ──
                want = len(batch_seq)
                got_batch = 0
                t0 = _ticks_us()
                while got_batch < want and _ticks_diff(_ticks_us(), t0) < int(timeout_ms) * 1000:
                    n = 0
                    try:
                        if uart.any():
                            n = rs.readinto(rxbuf)
                    except Exception:
                        n = 0
                    if n and n > 0:
                        asm.feed(rxmv[:n])
                        f = asm.next()
                        while f is not None:
                            garbage += asm.garbage
                            okf, why = _verify(f, batch_seq[got_batch] if got_batch < want else 0)
                            if okf and got_batch < want:
                                rtt_us = _ticks_diff(_ticks_us(), t0)
                                ok += 1
                                rtt_n += 1
                                rtt_sum += rtt_us
                                if rtt_min == 0 or rtt_us < rtt_min:
                                    rtt_min = rtt_us
                                if rtt_us > rtt_max:
                                    rtt_max = rtt_us
                                got_batch += 1
                            else:
                                corrupt += 1
                                got_batch += 1
                            f = asm.next()
                    _sleep_ms(0)

                lost += (want - got_batch)
                seq = (seq + batch) & 0xFFFFFFFF

            # 每檔報告
            if rtt_n:
                avg_us = rtt_sum // rtt_n
                thr_bps = (FRAME_LEN * 8 * 1_000_000) // avg_us if avg_us else 0
            else:
                avg_us = rtt_min = rtt_max = 0
                thr_bps = 0
            print("baud={:>7}  sent={}  ok={}  lost={}  corrupt={}  garbage={}".format(
                baud, sent, ok, lost, corrupt, garbage))
            print("           RTT avg={:.2f}ms min={:.2f}ms max={:.2f}ms  ~{} bit/s ({:.1f} KB/s)".format(
                avg_us / 1000, rtt_min / 1000, rtt_max / 1000, thr_bps, thr_bps / 8192))
            if ok == 0:
                print("           ❌ 此 baud 零往返，超出邊界（或對端未對齊）")
            elif lost or corrupt:
                print("           ⚠️ 有錯誤，已接近/超過此 baud 的可靠邊界")
            time.sleep(0.2)


if __name__ == "__main__":
#     run()
    bench_run()
