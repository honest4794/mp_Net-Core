# -*- coding: utf-8 -*-
"""rs485_probe.py — RS485 漸進式測試（板端 agent，MicroPython，自包含）

三步漸進、每一階段都有明確 PASS / FAIL / CHECK 與人工確認點，
取代舊的散落測試腳本（circuit_bus_* / bench_tx / rs485_de_scan / ...）：

  Stage 1  GPIO 確認      run(1)
            1) UART 能否用指定腳位建立
            2) EN 腳跳動      → 電錶/示波器看 GPIO 電壓跟著跳
            3) TX 送 0x55 方波 → 示波器看 A/B 差動線有無方波
            4) RX 總線安靜檢查 → 3 秒收到多少 byte + 內容判讀
            5) （選）TTL 迴路自測（LOOPBACK=1，收發器需先斷開）
  Stage 2  通訊確認        run(2)          本板當 reflector（對端：PC 跑 host peer --stage 2）
                          run(2, mode="ping") 本板當發送端（對端：PC host 或另一塊板 run(9)）
  Stage 3  系統路徑        run(3)          真實 driver.uart_drv._Rs485Uart + 真實 5-byte 顯示幀
                                           （對端：PC host peer --stage 3，或另一塊板 run(9)）
  對端模式                run(9)          另一塊板模擬「PC/顯示器」：反射 probe 幀 + 回顯示 ack

部署：板 A 上傳本檔跑 run(1)→run(2)→run(3)；對端用「PC USB-RS485 轉接器
      + rs485_probe_host.py」或「另一塊板跑 run(9)」。
      板上若有開機自動跑的 main.py，請先 Ctrl+C 停掉任務，避免佔用 UART1。

接線（預設值，全部可被 run() 參數覆蓋）：
  TX=9 → 收發器 DI、RX=8 ← 收發器 RO、EN=7 → DE+RE（active-high）
  匯流排 A-A、B-B，兩端 GND 共地。
  注意：repo 的 ports/ESP32-S3-RS485/config.json 目前寫 tx=8/rx=9 ——
  Stage1/2 用哪組腳位由本檔常數決定；Stage3 讀板上 config.json（真實系統路徑）。
  若 Stage2 通、Stage3 不通，第一嫌疑就是 config.json 的 tx/rx 與實際接線相反。
"""

import time
from machine import UART, Pin

# ═══ 部署設定（與你的硬體一致；run() 可參數覆蓋）═══
TX, RX, EN = 9, 8, 7          # MCU TX→DI、MCU RX←RO、EN→DE+RE
BAUD = 9600
UART_ID = 1
EN_ACTIVE = 1                 # 1 = 拉高發送（active-high）；0 = 拉低發送（active-low）
SETTLE_MS = 1                 # DE 使能 settle（實測 0ms 不穩、1ms 穩定）
LOOPBACK = 0                  # Stage1 第 5 步 TTL 迴路自測（需先把收發器與 MCU 斷開再跳線）

# ═══ 幀格式 ═══
P_HEAD, P_TAIL, P_LEN = 0xAC, 0xFF, 10   # Stage2 probe 幀
D_SOF, D_EOF, D_LEN = 0xB4, 0xFF, 5      # Stage3 真實顯示幀（action_task_1 同款）

PING_COUNT = 20
PING_INTERVAL_MS = 300
ECHO_TIMEOUT_MS = 800


def _ticks_ms():
    return time.ticks_ms() if hasattr(time, "ticks_ms") else int(time.time() * 1000)


def _ticks_diff(a, b):
    return time.ticks_diff(a, b) if hasattr(time, "ticks_diff") else a - b


def _hex(data):
    return " ".join("{:02X}".format(b) for b in data)


# ── RS485 半雙工發送（與 driver.uart_drv._Rs485Uart 同一時序語意） ──
class _RS485:
    """DE 拉高 → settle → write → 等真正送完(txdone) → DE 放低回接收。"""

    def __init__(self, uart, en_pin, baud, settle_ms=SETTLE_MS, en_active=EN_ACTIVE):
        self.io = uart
        self.en = en_pin
        self.baud = int(baud)
        self.settle_ms = int(settle_ms)
        self.en_active = int(en_active)
        # 閒置必須是 TX enable 的反相。舊 probe 固定寫 0，令
        # en_active=0 的接收端一直保持發送，測反相極性時會自行霸住 bus。
        self.en.value(0 if self.en_active else 1)

    def _byte_ms(self):
        return max(1, (10 * 1000) // self.baud)

    def _wait_sent(self, nbytes):
        if hasattr(self.io, "txdone"):
            t0 = _ticks_ms()
            try:
                while not self.io.txdone():
                    if _ticks_diff(_ticks_ms(), t0) > 2000:
                        break                  # 防卡死（測試用保險，與 bench 版一致）
                    time.sleep_ms(0)
            except Exception:
                pass
        time.sleep_ms(self._byte_ms() + 1)

    def write(self, data):
        self.en.value(self.en_active)
        if self.settle_ms > 0:
            time.sleep_ms(self.settle_ms)
        try:
            n = self.io.write(data)
            self._wait_sent(len(data) if (n is None or n <= 0) else n)
            return n
        finally:
            self.en.value(0 if self.en_active else 1)


# ── Stage2 probe 幀 ──
def _build_probe(seq):
    f = bytearray(P_LEN)
    f[0] = P_HEAD
    f[1] = seq & 0xFF
    f[2] = (seq >> 8) & 0xFF
    f[3] = (seq >> 16) & 0xFF
    f[4] = (seq >> 24) & 0xFF
    f[5] = 0x11
    f[6] = 0x22
    f[7] = 0x33
    f[8] = 0x44
    f[9] = P_TAIL
    return bytes(f)


def _seq_of(f):
    return f[1] | (f[2] << 8) | (f[3] << 16) | (f[4] << 24)


def _echo_probe(f):
    """把收到的 probe 幀 seq+1 原樣回傳（證明是「新的回音」不是 loopback）。"""
    return _build_probe((_seq_of(f) + 1) & 0xFFFFFFFF)


# ── Stage3 真實顯示幀（與 action_task_1 的 [B4 mode bri time FF] 一致） ──
def _build_disp(mode, bri, t):
    return bytes([D_SOF, mode & 0xFF, bri & 0x1F, t & 0xFF, D_EOF])


# ── 收幀掃描器（跨 chunk 組幀 + 錯位自動重同步，9600 下 UART 會把一幀拆成多段） ──
def _read_probe(uart, timeout_ms):
    """讀到一幀 10B probe 幀回傳 bytes；逾時回 None。"""
    buf = bytearray()
    t0 = _ticks_ms()
    while _ticks_diff(_ticks_ms(), t0) < int(timeout_ms):
        try:
            if uart.any():
                chunk = uart.read(uart.any())
                if chunk:
                    buf.extend(chunk)
        except Exception:
            pass
        while True:
            idx = buf.find(b"\xAC")
            if idx < 0:
                if len(buf) > P_LEN - 1:
                    buf = buf[-(P_LEN - 1):]   # 只留最後 9B（防頭跨段）
                break
            if idx > 0:
                buf = buf[idx:]
            if len(buf) < P_LEN:
                break
            if buf[P_LEN - 1] == P_TAIL:
                f = bytes(buf[:P_LEN])
                buf = buf[P_LEN:]
                return f
            buf = buf[1:]                      # 尾不是 FF → 假頭，跳過再找
        time.sleep_ms(1)
    return None


def _read_disp(uart, timeout_ms):
    """讀到一幀 5B 顯示幀回傳 bytes；逾時回 None。"""
    buf = bytearray()
    t0 = _ticks_ms()
    while _ticks_diff(_ticks_ms(), t0) < int(timeout_ms):
        try:
            if uart.any():
                chunk = uart.read(uart.any())
                if chunk:
                    buf.extend(chunk)
        except Exception:
            pass
        while True:
            idx = buf.find(b"\xB4")
            if idx < 0:
                if len(buf) > D_LEN - 1:
                    buf = buf[-(D_LEN - 1):]
                break
            if idx > 0:
                buf = buf[idx:]
            if len(buf) < D_LEN:
                break
            if buf[D_LEN - 1] == D_EOF:
                f = bytes(buf[:D_LEN])
                buf = buf[D_LEN:]
                return f
            buf = buf[1:]
        time.sleep_ms(1)
    return None


def _drain(uart, ms=30):
    """讀掉 RX FIFO 殘留（發送後 ~30ms 內到達的通常是自己的回波/線路殘留）。"""
    t0 = _ticks_ms()
    while _ticks_diff(_ticks_ms(), t0) < int(ms):
        try:
            if uart.any():
                uart.read(uart.any())
        except Exception:
            pass
        time.sleep_ms(1)


# ═══════════════════ Stage 1 — GPIO 確認 ═══════════════════
def run_gpio(tx=TX, rx=RX, en=EN, baud=BAUD, uart_id=UART_ID,
             en_active=EN_ACTIVE, loopback=LOOPBACK, invert=0):
    print("=" * 60)
    print("STAGE 1 — GPIO 確認 (tx={} rx={} en={} baud={} en_active={})".format(
        tx, rx, en, baud, en_active))
    print("=" * 60)

    # 1/5 UART 建立
    try:
        uart = UART(int(uart_id), baudrate=int(baud),
                    tx=Pin(int(tx)), rx=Pin(int(rx)), invert=int(invert))
        print("[1/5][PASS] UART{} 建立成功 tx={} rx={} baud={}".format(
            uart_id, tx, rx, baud))
    except Exception as e:
        print("[1/5][FAIL] UART 建立失敗: {}".format(repr(e)))
        print("  → 腳位被佔用或與 config.json 衝突；先停掉系統任務再試")
        return

    # 2/5 EN 跳動（人工看電錶/示波器）
    en_pin = Pin(int(en), Pin.OUT, value=0)
    print("[2/5] EN(GPIO{}) 開始跳動 6 次（0.5s 高 / 0.5s 低）...".format(en))
    for i in range(6):
        en_pin.value(en_active)
        time.sleep_ms(500)
        en_pin.value(0 if en_active else 1)
        time.sleep_ms(500)
    en_pin.value(0 if en_active else 1)
    print("[2/5][CHECK] 請人工確認：電錶/示波器量 GPIO{} 是否跟著 0/3.3V 跳動".format(en))
    print("  （不會跳 → EN 腳錯、短路或腳位被其他外設佔用）")

    # 3/5 TX 方波輸出（人工看示波器）
    rs = _RS485(uart, en_pin, baud, en_active=en_active)
    print("[3/5] 送 8 串 0x55 x16（EN 自動拉高）...")
    for i in range(8):
        rs.write(b"\x55" * 16)
        time.sleep_ms(300)
    print("[3/5][CHECK] 請人工確認：示波器量 A/B 差動線（或收發器 A/B 腳）應有方波")
    print("  （完全沒波 → 查 DI 接線 / EN 極性 / 收發器供電；有波但雜 → 查 GND 共地）")

    # 4/5 RX 總線安靜檢查
    print("[4/5] EN 放低回接收，先清 FIFO 再監聽 3 秒...")
    left = 0
    try:
        left = uart.any()
        if left:
            uart.read(left)
    except Exception:
        left = 0
    print("  TX 結束後 FIFO 殘留 {} bytes（>0 且內容是剛送的 55 → 自己的回波，代表 RE 常開）".format(left))

    t0 = _ticks_ms()
    got = bytearray()
    while _ticks_diff(_ticks_ms(), t0) < 3000:
        try:
            if uart.any():
                chunk = uart.read(uart.any())
                if chunk:
                    got.extend(chunk)
        except Exception:
            pass
        time.sleep_ms(1)
    if len(got) == 0:
        print("[4/5][PASS] 3 秒內 0 byte → 總線安靜（偏壓/終端/GND 正常）")
    else:
        print("[4/5][WARN] 3 秒內收到 {} bytes: {}".format(len(got), _hex(got[:16])))
        print("  → 總線有雜訊/浮空：檢查 A/B 偏壓電阻、終端電阻、兩端 GND 共地、baud 是否一致")

    # 5/5（選）TTL 迴路自測
    if loopback:
        print("[5/5] TTL 迴路自測：請確認已把 MCU 的 TX/RX 直接短路（收發器斷開），")
        print("      否則結果無意義。發 16 幀自收比對...")
        ok = 0
        for i in range(16):
            f = _build_probe(i)
            try:
                uart.write(f)
            except Exception:
                break
            back = _read_probe(uart, 200)
            if back is not None and back == f:
                ok += 1
        if ok == 16:
            print("[5/5][PASS] 迴路自測 16/16 → UART 腳位/baud/收發路徑無誤")
        else:
            print("[5/5][FAIL] 迴路自測 {}/16 → 檢查跳線、TX/RX 腳位、baud".format(ok))
    else:
        print("[5/5][SKIP] 未啟用 TTL 迴路自測（LOOPBACK=1 才跑）")

    print("-" * 60)
    print("STAGE 1 結束。1/2/3 需人工看儀器確認；全部 OK 再跑 run(2)。")
    print("=" * 60)


# ═══════════════════ Stage 2 — 通訊確認 ═══════════════════
def run_link_reflect(rs, seconds=60):
    """本板當 reflector：收到 probe 幀 → seq+1 原樣回傳。對端跑 PC host peer --stage 2。"""
    print("=" * 60)
    print("STAGE 2 — REFLECT 模式（收到 probe 幀即 seq+1 回傳，{} 秒）".format(seconds))
    print("對端請執行：python -B rs485_probe_host.py peer --stage 2（或另一塊板 run(9)）")
    print("=" * 60)
    got = 0
    t0 = _ticks_ms()
    while _ticks_diff(_ticks_ms(), t0) < int(seconds) * 1000:
        f = _read_probe(rs.io, 100)
        if f is not None:
            got += 1
            rs.write(_echo_probe(f))
            print("RECV seq={} → ECHO seq={} (total={})".format(
                _seq_of(f), (_seq_of(f) + 1) & 0xFFFFFFFF, got))
            _drain(rs.io, 15)      # 吃掉自己 TX 的回波（RE 常開的收發器才有）
        time.sleep_ms(1)
    print("RESULT stage=2 mode=reflect frames={} (對端統計才是成敗依據)".format(got))


def run_link_ping(rs, count=PING_COUNT, interval_ms=PING_INTERVAL_MS):
    """本板當發送端：送 probe 幀、等 seq+1 回音。對端跑 PC host（reflect 模式）或另一塊板 run(9)。"""
    print("=" * 60)
    print("STAGE 2 — PING 模式（{} 幀、間隔 {}ms、回音逾時 {}ms）".format(
        count, interval_ms, ECHO_TIMEOUT_MS))
    print("=" * 60)
    ok = 0
    rtts = []
    for i in range(count):
        f = _build_probe(i)
        t0 = _ticks_ms()
        rs.write(f)
        back = _read_probe(rs.io, ECHO_TIMEOUT_MS)
        dt = _ticks_diff(_ticks_ms(), t0)
        if back is not None and _seq_of(back) == (i + 1) & 0xFFFFFFFF:
            ok += 1
            rtts.append(dt)
            print("[{:>2}] OK   rtt={}ms".format(i, dt))
        else:
            raw = _hex(back) if back is not None else "(無回應)"
            print("[{:>2}] LOST  got={}".format(i, raw))
        time.sleep_ms(max(0, interval_ms - dt))
    print("-" * 60)
    if rtts:
        print("RTT min/avg/max = {}/{}/{} ms".format(
            min(rtts), sum(rtts) // len(rtts), max(rtts)))
    if ok == count:
        print("RESULT stage=2 mode=ping PASS ({}/{})".format(ok, count))
    else:
        print("RESULT stage=2 mode=ping FAIL ({}/{})".format(ok, count))
        print("  全部 LOST → 查接線/EN 極性/GND；部分 LOST → settle_ms 或總線品質")


# ═══════════════════ Stage 3 — 我們系統的路徑 ═══════════════════
def _load_device_uart_cfg(uart_id):
    """讀板上 /config.json（真實系統同一個設定檔）的 UART 段；找不到回 None。"""
    try:
        import ujson
    except ImportError:
        try:
            import json as ujson
        except ImportError:
            return None
    root = None
    for path in ("/config.json", "config.json"):
        try:
            with open(path, "r") as f:
                root = ujson.load(f)
            break
        except Exception:
            root = None
    if not isinstance(root, dict):
        return None
    for item in (root.get("UART") or {}).get("list", []):
        if int(item.get("id", 1)) == int(uart_id):
            return item
    return None


def _import_real_driver():
    """匯入真實 driver.uart_drv（板上佈局 driver/，repo 佈局 slave/driver/）。"""
    for name in ("driver.uart_drv", "slave.driver.uart_drv"):
        try:
            mod = __import__(name, None, None, ["uart_drv"])
            return mod
        except Exception:
            pass
    return None


def run_system(tx=None, rx=None, en=None, baud=None, uart_id=None,
               en_active=None, settle_ms=None):
    """真實系統路徑：config.json + driver.uart_drv._Rs485Uart + 真實 5-byte 顯示幀。

    對端：PC host peer --stage 3（USB-RS485 模擬顯示器）或另一塊板 run(9)。
    未傳參數時一律用板上 config.json 的值（= 系統實際會用的值）；
    config.json 讀不到才退回本檔常數。
    """
    print("=" * 60)
    print("STAGE 3 — 我們系統的路徑（config.json + uart_drv._Rs485Uart + 5-byte 顯示幀）")
    print("=" * 60)

    cfg = _load_device_uart_cfg(uart_id if uart_id is not None else UART_ID)
    if cfg is not None:
        gpio = cfg.get("GPIO", {}) or {}
        tx = tx if tx is not None else gpio.get("tx")
        rx = rx if rx is not None else gpio.get("rx")
        en = en if en is not None else gpio.get("en", -1)
        baud = baud if baud is not None else cfg.get("baudrate", BAUD)
        settle_ms = settle_ms if settle_ms is not None else cfg.get("en_settle_ms", SETTLE_MS)
        print("[SYS][CFG] 已讀 /config.json → tx={} rx={} en={} baud={} settle_ms={}".format(
            tx, rx, en, baud, settle_ms))
    else:
        tx = tx if tx is not None else TX
        rx = rx if rx is not None else RX
        en = en if en is not None else EN
        baud = baud if baud is not None else BAUD
        settle_ms = settle_ms if settle_ms is not None else SETTLE_MS
        print("[SYS][CFG] 板上無 /config.json → 用腳本常數 tx={} rx={} en={} baud={}".format(
            tx, rx, en))
    en_active = en_active if en_active is not None else EN_ACTIVE
    uart_id = uart_id if uart_id is not None else UART_ID
    if en is None or int(en) < 0:
        print("[SYS][FAIL] config 沒給 en（DE 方向腳）→ 半雙工無法控方向，中止")
        return

    print("[SYS][注意] 上面 tx/rx 必須等於實體接線（TX→DI、RX←RO）。")
    print("          Stage2 通、Stage3 不通 → 第一嫌疑就是 config.json 的 tx/rx 寫反。")

    uart = UART(int(uart_id), baudrate=int(baud),
                tx=Pin(int(tx)), rx=Pin(int(rx)))
    en_pin = Pin(int(en), Pin.OUT, value=0)
    _drain(uart, 30)

    drv = _import_real_driver()
    if drv is not None:
        rs = drv._Rs485Uart(uart, en_pin, int(baud), settle_ms=int(settle_ms))
        print("[SYS][PASS] 使用真實 driver.uart_drv._Rs485Uart（含 listen-before-talk）")
    else:
        rs = _RS485(uart, en_pin, baud, settle_ms=settle_ms, en_active=en_active)
        print("[SYS][WARN] import driver.uart_drv 失敗 → 用內建同款時序（非生產路徑！）")

    # 真實 5-byte 顯示幀（[B4 mode bri time FF]）；對端顯示器收到會原樣 echo = ack
    frames = [(1, 5, 7), (2, 9, 8), (0x81, 3, 0)]
    ok = 0
    for (mode, bri, t) in frames:
        f = _build_disp(mode, bri, t)
        rs.write(f)
        print("[SYS] TX -> {} (mode={} bri={} time={})".format(_hex(f), mode, bri, t))
        ack = _read_disp(uart, 1000)
        if ack is not None:
            print("[SYS] RX <- {} (mode={} bri={} time={})".format(
                _hex(ack), ack[1], ack[2], ack[3]))
            if ack == f:
                ok += 1
                print("      ack 與送出幀逐 byte 一致 → OK")
            else:
                print("      ack 內容不同 → 對端解析或線路內容有誤")
        else:
            print("[SYS] RX <- (1 秒內無回覆)")
        time.sleep_ms(200)

    print("-" * 60)
    if ok == len(frames):
        print("RESULT stage=3 PASS ({}/{}) → 系統路徑可通訊".format(ok, len(frames)))
    else:
        print("RESULT stage=3 FAIL ({}/{})".format(ok, len(frames)))
        print("  檢查順序：1) config.json 的 tx/rx 與實體接線是否一致")
        print("            2) 對端是否在收/在回（PC host 畫面）")
        print("            3) EN 極性、GND、baud（對照 Stage1/2 的結論）")


# ═══════════════════ 對端模式（另一塊板模擬 PC/顯示器）═══════════════════
def _peer_scan(buf):
    """掃描緩衝開頭。一律回 (frame, 剩餘)：
    - frame 非 None       → 拿到一幀（probe 或 顯示幀）
    - (None, 較短 buf)    → 本次無幀但已丟掉垃圾/假頭（有進展，繼續掃）
    - (None, 同長度 buf)  → 無進展（等新資料）"""
    n = len(buf)
    if n < D_LEN:
        return None, buf
    if buf[0] == P_HEAD and n >= P_LEN and buf[P_LEN - 1] == P_TAIL:
        return bytes(buf[:P_LEN]), buf[P_LEN:]
    if buf[0] == D_SOF and buf[D_LEN - 1] == D_EOF:
        return bytes(buf[:D_LEN]), buf[D_LEN:]
    # 找下一個可能的頭（AC 或 B4）
    ia = buf.find(b"\xAC", 1)
    ib = buf.find(b"\xB4", 1)
    idxs = [i for i in (ia, ib) if i >= 0]
    if not idxs:
        keep = max(P_LEN, D_LEN) - 1
        if n > keep:
            return None, buf[-keep:]
        return None, buf
    return None, buf[min(idxs):]


def run_peer(tx=TX, rx=RX, en=EN, baud=BAUD, uart_id=UART_ID,
             en_active=EN_ACTIVE, settle_ms=SETTLE_MS, seconds=0, invert=0):
    """另一塊板當對端：反射 Stage2 probe 幀(seq+1)、模擬顯示器回 Stage3 ack(原樣 echo)。"""
    print("=" * 60)
    print("PEER 模式 — 模擬 PC/顯示器 (tx={} rx={} en={} baud={})".format(tx, rx, en, baud))
    print("對面那塊板請依序跑 run(2, mode='ping') → run(3)")
    print("=" * 60)
    uart = UART(int(uart_id), baudrate=int(baud), tx=Pin(int(tx)), rx=Pin(int(rx)),
                invert=int(invert))
    en_pin = Pin(int(en), Pin.OUT, value=(0 if en_active else 1))
    rs = _RS485(uart, en_pin, baud, settle_ms=settle_ms, en_active=en_active)
    _drain(uart, 30)

    buf = bytearray()
    got = 0
    t0 = _ticks_ms()
    while True:
        try:
            if uart.any():
                chunk = uart.read(uart.any())
                if chunk:
                    buf.extend(chunk)
        except Exception:
            pass
        while True:
            f, rest = _peer_scan(buf)
            if f is None:
                if len(rest) >= len(buf):
                    break              # 無進展 → 回去等新資料
                buf = rest             # 丟掉垃圾/假頭後繼續掃
                continue
            buf = rest
            if f[0] == P_HEAD and f[P_LEN - 1] == P_TAIL:
                echo = _echo_probe(f)
                rs.write(echo)
                got += 1
                print("PROBE seq={} → echo seq={} (total={})".format(
                    _seq_of(f), (_seq_of(f) + 1) & 0xFFFFFFFF, got))
                _drain(uart, 15)
            elif f[0] == D_SOF and f[D_LEN - 1] == D_EOF:
                rs.write(f)
                got += 1
                print("DISP mode={} bri={} time={} → ack 原樣回傳 (total={})".format(
                    f[1], f[2], f[3], got))
                _drain(uart, 15)
        if seconds and _ticks_diff(_ticks_ms(), t0) >= int(seconds) * 1000:
            break
        time.sleep_ms(1)
    print("RESULT peer frames={}".format(got))


# ═══════════════════ 入口 ═══════════════════
def run(stage=0, tx=None, rx=None, en=None, baud=None, uart_id=None,
        en_active=None, settle_ms=None, mode="reflect",
        count=PING_COUNT, interval_ms=PING_INTERVAL_MS, seconds=60, loopback=None,
        invert=0):
    """漸進式測試入口。stage: 1=GPIO 2=通訊 3=系統路徑 9=對端模式。

    只覆蓋你傳的參數；Stage3 沒傳的一律用板上 config.json（真實系統值），
    其餘 stage 沒傳的用本檔常數。
    """
    if stage == 3:
        # 不解析常數：讓 run_system 自己去讀 config.json（= 系統實際用的值）
        run_system(tx=tx, rx=rx, en=en, baud=baud, uart_id=uart_id,
                   en_active=en_active, settle_ms=settle_ms)
        return

    tx = TX if tx is None else int(tx)
    rx = RX if rx is None else int(rx)
    en = EN if en is None else int(en)
    baud = BAUD if baud is None else int(baud)
    uart_id = UART_ID if uart_id is None else int(uart_id)
    en_active = EN_ACTIVE if en_active is None else int(en_active)
    settle_ms = SETTLE_MS if settle_ms is None else int(settle_ms)
    loopback = LOOPBACK if loopback is None else int(loopback)
    invert = int(invert)

    if stage == 1:
        run_gpio(tx, rx, en, baud, uart_id, en_active, loopback, invert)
    elif stage == 2:
        uart = UART(uart_id, baudrate=baud, tx=Pin(tx), rx=Pin(rx), invert=invert)
        en_pin = Pin(en, Pin.OUT, value=(0 if en_active else 1))
        rs = _RS485(uart, en_pin, baud, settle_ms=settle_ms, en_active=en_active)
        _drain(uart, 30)
        if mode == "ping":
            run_link_ping(rs, count=count, interval_ms=interval_ms)
        else:
            run_link_reflect(rs, seconds=seconds)
    elif stage == 9:
        run_peer(tx, rx, en, baud, uart_id, en_active, settle_ms,
                 seconds=seconds, invert=invert)
    else:
        print(__doc__)
        print("\n用法（逐階段、每階段人工確認後再往下）：")
        print("  run(1)                  # Stage1 GPIO")
        print("  run(2)                  # Stage2 本板當 reflector")
        print("  run(2, mode='ping')     # Stage2 本板當發送端")
        print("  run(3)                  # Stage3 系統路徑")
        print("  run(9)                  # 對端模式（另一塊板）")
