# -*- coding: utf-8 -*-
"""master_agent — 跑在 1201，透過 UART GPIO9/8 對 1401 slave 發 NC4 指令

角色：master（PC 端 mpremote exec 呼叫）
  init_link(baud)         建立 UART 連線
  send(cmd, args, addr)   組幀送出（廣播 0xFFFF）
  recv(timeout_ms)        收一幀回 (cmd, dict) 或 None
  set_baud(baud)          切自己的 UART baud

測試函式（回傳結果字串，方便 host 收集）：
  t_link()                 STATUS_GET 敲門
  t_speed()                完整提速流程（QUERY→SET→敲門→COMMIT→REVERT）
  t_file_upload()          全新上傳 + 驗 sha
  t_file_download()        分片下載 + 驗 sha
  t_file_backup()          覆蓋→CONFIRM / 覆蓋→UNDO（備份恢復）
  t_file_resume()          中斷→PARTIAL_QUERY→續傳
  t_file_error()           錯誤路徑（sha錯/id錯/無session/move跨卷）
  t_file_mgmt()            QUERY/DELETE/MOVE 管理操作
  t_speed_auto_revert()    SET 後不 COMMIT → 等 timeout 自動回滾
"""

import time
from machine import UART, Pin

from lib.sys.proto import Proto, StreamParser, ADDR_BROADCAST
from lib.sys.schema_loader import SchemaStore
from lib.sys.schema_codec import SchemaCodec

TX, RX = 9, 8
UART_ID = 1
DEF_BAUD = 115200
SPEED_BAUD = 460800

_store = SchemaStore('/schema')
_store.finalize()
_cc = SchemaCodec(_store)


class Link:
    def __init__(self, baud=DEF_BAUD):
        self.baud = baud
        self.uart = UART(UART_ID, baud, tx=TX, rx=RX, rxbuf=16384, txbuf=16384)
        self.parser = StreamParser()
        self._drain()

    def _drain(self):
        b = bytearray(256)
        for _ in range(12):
            try:
                if self.uart.any():
                    self.uart.readinto(b)
                else:
                    break
            except Exception:
                break

    def set_baud(self, baud):
        self.uart.init(baudrate=baud, tx=TX, rx=RX, rxbuf=16384, txbuf=16384)
        self.baud = baud
        self._drain()

    def send(self, cmd, args=None, addr=ADDR_BROADCAST):
        if args is None:
            args = {}
        d = _store.get(cmd)
        if d is None:
            print("!! no schema for 0x%04X" % cmd)
            return
        payload = _cc.encode(d, args)
        frame = Proto.pack(cmd, payload, addr=addr)
        self.uart.write(frame)
        self._wait_sent()
        return len(frame)

    def _wait_sent(self):
        """等 UART 把 txbuf 排空（FIFO 空 + 最後 1 byte 離開 shift register）。

        關鍵：microPython 的 uart.write() 是非阻塞的（只把資料塞進 txbuf 就返回）。
        4KB 幀在 115200 下要 ~356ms 才真正發完。若不等發完就 recv，
        會跟自己還沒發完的數據/對端回應混在一起。"""
        if hasattr(self.uart, "txdone"):
            try:
                t0 = time.ticks_ms()
                while not self.uart.txdone():
                    if time.ticks_diff(time.ticks_ms(), t0) > 2000:
                        break
                    time.sleep_ms(0)
            except Exception:
                pass
        time.sleep_ms(2)   # 最後 1 byte 離開 shift register 的 margin

    def recv(self, timeout_ms=2000):
        """收一幀，回 (cmd_id, payload_dict, payload_bytes) 或 None"""
        t0 = time.ticks_ms()
        mv = bytearray(512)
        while time.ticks_diff(time.ticks_ms(), t0) < timeout_ms:
            try:
                if self.uart.any():
                    n = self.uart.readinto(mv)
                    if n and n > 0:
                        self.parser.feed(mv[:n])
                        r = self.parser.pop_frame()
                        if r is not None:
                            ver, addr, cmd, payload_mv = r
                            pb = bytes(payload_mv)   # 立即快照（view 生命週期）
                            if cmd in _HAND_DEC:
                                vals = _HAND_DEC[cmd](pb)
                            else:
                                d = _store.get(cmd)
                                vals = _cc.decode(d, pb) if d else {"_name": "0x%04X" % cmd}
                            return cmd, vals, pb
            except Exception:
                pass
            time.sleep_ms(1)
        return None

    def recv_until(self, want_cmds, timeout_ms=3000):
        """持續收直到出現 want_cmds 任一，回 (cmd, dict) 或 None"""
        t0 = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), t0) < timeout_ms:
            r = self.recv(200)
            if r is not None and r[0] in want_cmds:
                return r
        return None

    def send_wait(self, cmd, args=None, want_cmds=None, addr=ADDR_BROADCAST,
                  timeout_ms=2000, retries=10):
        """發送 + 等回應 + 失敗重發（預設同一個包試 10 次）。

        對應「鏈路丟包」：master→slave 的請求幀偶發丟失（slave 收到都正確回應）。
        這裡在 UART 層做 ACK 停等重試：發出去沒等到回應就重發同一幀，遮蓋鏈路丟包。
        回 (cmd, dict) 或 None（重試次數用盡仍無回應）。

        注意：重試前不清空 RX 對緩衝（避免把「遲到的 ACK」也清掉），
        只在每次發送前 drain 掉「可能殘留的半幀」。"""
        if want_cmds is None:
            want_cmds = ()
        for attempt in range(retries):
            self.send(cmd, args, addr=addr)
            r = self.recv_until(want_cmds, timeout_ms)
            if r is not None:
                return r
            # 重發前小延遲 + 清掉 RX 殘留半幀（避免上一幀殘留干擾下一幀解析）
            time.sleep_ms(20)
            self._drain()
        return None


# ── 測試輔助 ──

def _sha256(data):
    import uhashlib
    h = uhashlib.sha256()
    if isinstance(data, (bytes, bytearray)):
        h.update(data)
    else:
        for c in data:
            h.update(c)
    return h.digest()


def _hex(b):
    import ubinascii
    return ubinascii.hexlify(b).decode()


def _mkdata(size, seed=0x5A):
    """可預測的測試資料（避開 0xFF 干擾？不，FILE 是長度框無此問題）"""
    return bytes([(seed + i * 7) & 0xFF for i in range(size)])


_link = None


def init_link(baud=DEF_BAUD):
    global _link
    _link = Link(baud)
    return "link ready @%d" % baud


# ── 提速原語（批次傳檔用，可重入）──

def speed_enter(target=SPEED_BAUD, timeout_ms=3000):
    """提速進入：SPEED_QUERY → SPEED_SET → 等 ACK(舊速) → 切速 → 敲門 → COMMIT。
    回 (ok, 訊息)。失敗時會嘗試還原回 DEF_BAUD。"""
    L = _link
    # 0. 確認 slave 狀態；非 IDLE 先 REVERT 回穩
    L.send(0x1407, {"bus_type": 7, "bus_id": 0})
    r = L.recv_until([0x1408], 2000)
    if r is not None and r[1].get("state") != 0:
        L.send(0x1406, {"bus_type": 7, "bus_id": 0})
        time.sleep_ms(300)
        L.set_baud(DEF_BAUD)
        time.sleep_ms(100)

    # 1. SPEED_SET（slave 舊速回 ACK 後才切速；master 收到 ACK 後切速）
    L.send(0x1403, {"bus_type": 7, "bus_id": 0, "speed": target, "timeout_ms": timeout_ms})
    ack = L.recv_until([0x1404], 1500)
    if ack is None:
        return (False, "SPEED_SET: no ACK")
    if not ack[1].get("ok"):
        return (False, "SPEED_SET: ok=0")

    # 2. 收到 ACK 後 master 同步切速
    L.set_baud(target)

    # 3. 敲門直到 timeout_ms 耗盡（確認新速雙向通）
    deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
    while time.ticks_diff(deadline, time.ticks_ms()) > 0:
        L.send(0x1407, {"bus_type": 7, "bus_id": 0})
        r = L.recv_until([0x1408], 800)
        if r is not None and r[1].get("state") in (1, 2):
            # 4. COMMIT 鎖定
            L.send(0x1405, {"bus_type": 7, "bus_id": 0})
            time.sleep_ms(120)
            return (True, "speed %d entered (state=%s)" % (target, r[1].get("state")))
        time.sleep_ms(150)

    # 敲門失敗：等 slave 自動回滾（SYNCING timeout），再切回舊速
    time.sleep_ms(timeout_ms + 300)
    L.set_baud(DEF_BAUD)
    return (False, "verify failed, auto-reverted")


def speed_revert():
    """還原：SPEED_REVERT + master 同步切回 DEF_BAUD。回 (ok, 訊息)。"""
    L = _link
    L.send(0x1406, {"bus_type": 7, "bus_id": 0})
    time.sleep_ms(150)
    L.set_baud(DEF_BAUD)
    time.sleep_ms(100)
    for _ in range(3):
        L.send(0x1407, {"bus_type": 7, "bus_id": 0})
        r = L.recv_until([0x1408], 1500)
        if r is not None:
            return (True, "reverted (state=%s cur=%s)" % (
                r[1].get("state"), r[1].get("cur_speed")))
    return (False, "revert: no status")


# ── 測試 1: link 敲門 ──

def t_link():
    L = _link
    L.send(0x1101, {"query_type": 0})
    r = L.recv_until([0x1102], 3000)
    if r is None:
        return "LINK FAIL: no STATUS_RSP"
    cmd, d, pb = r
    sj = d.get("status_json", "")
    return "LINK OK: status_json len=%d head=%r" % (len(sj), sj[:60])


# ── 測試 2: SPEED 提速完整流程 ──

def t_speed():
    L = _link
    out = []
    # Step 0: 預熱敲門（slave 剛 boot 完需要時間初始化模組；連續敲到有回應）
    warm_ok = False
    for i in range(5):
        L.send(0x1407, {"bus_type": 7, "bus_id": 0})
        r = L.recv_until([0x1408], 2000)
        if r is not None:
            warm_ok = True
            out.append("warmup %d ok" % i)
            break
        time.sleep_ms(300)
    if not warm_ok:
        return "SPEED FAIL: slave not responding (boot not ready)\n" + "\n".join(out)

    # Step 1: SPEED_QUERY 確認 IDLE
    st = r[1]
    out.append("query state=%s cur=%s" % (st.get("state"), st.get("cur_speed")))
    if st.get("state") != 0:
        # 非 IDLE：先 REVERT 回穩
        L.send(0x1406, {"bus_type": 7, "bus_id": 0})
        time.sleep_ms(300)
        L.set_baud(DEF_BAUD)

    # Step 1: SPEED_SET（slave 先回 ACK(舊速) 再切速；master 收到 ACK 後才切速）
    timeout_ms = 3000
    L.send(0x1403, {"bus_type": 7, "bus_id": 0, "speed": SPEED_BAUD, "timeout_ms": timeout_ms})
    # 用「舊速」等 ACK（slave 收到 SET 後先回 ACK，再 apply 切速）
    ack = L.recv_until([0x1404], 1500)
    if ack is None:
        out.append("SET FAIL: no ACK (old baud)")
        return "SPEED FAIL: no SPEED_ACK\n" + "\n".join(out)
    out.append("ACK ok=%s cur=%s target=%s" % (
        ack[1].get("ok"), ack[1].get("cur_speed"), ack[1].get("target_speed")))
    if not ack[1].get("ok"):
        return "SPEED FAIL: ACK ok=0\n" + "\n".join(out)

    # Step 2: 收到 ACK 後，兩邊一起切速（master 同步切到 target）
    L.set_baud(SPEED_BAUD)

    # Step 3: 用新速「不斷敲門」直到 timeout_ms 耗盡（確保新設定下能通訊）
    deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
    verify_ok = False
    attempts = 0
    while time.ticks_diff(deadline, time.ticks_ms()) > 0:
        L.send(0x1407, {"bus_type": 7, "bus_id": 0})
        r = L.recv_until([0x1408], 800)
        attempts += 1
        if r is not None and r[1].get("state") in (1, 2):
            verify_ok = True
            out.append("verify @%d OK after %d knock(s) state=%s" % (
                SPEED_BAUD, attempts, r[1].get("state")))
            break
        time.sleep_ms(200)

    if not verify_ok:
        # 敲門失敗：等 slave 自動回滾（SYNCING timeout），再切回舊速確認
        out.append("verify @%d FAIL (%d knocks)" % (SPEED_BAUD, attempts))
        time.sleep_ms(timeout_ms + 500)
        L.set_baud(DEF_BAUD)
        L.send(0x1407, {"bus_type": 7, "bus_id": 0})
        r2 = L.recv_until([0x1408], 2000)
        if r2 is None:
            return "SPEED FAIL: verify fail & no status after revert\n" + "\n".join(out)
        return "SPEED FAIL: verify @%d failed, auto-reverted state=%s cur=%s\n%s" % (
            SPEED_BAUD, r2[1].get("state"), r2[1].get("cur_speed"), "\n".join(out))

    # Step 4: SPEED_COMMIT 鎖定（slave 進入 COMMITTED，啟動 idle 超時）
    L.send(0x1405, {"bus_type": 7, "bus_id": 0})
    time.sleep_ms(150)
    L.send(0x1407, {"bus_type": 7, "bus_id": 0})
    r = L.recv_until([0x1408], 1500)
    if r is None:
        out.append("commit check FAIL")
    else:
        out.append("commit state=%s cur=%s" % (r[1].get("state"), r[1].get("cur_speed")))

    # Step 5: 在新速下做一次小檔案傳輸驗證（期間 keepalive 刷新 idle）
    tf = _test_file_small()
    out.append("file@%d: %s" % (SPEED_BAUD, tf))

    # Step 6: SPEED_REVERT 還原（slave 切回舊速；master 同步切回並重試驗證）
    L.send(0x1406, {"bus_type": 7, "bus_id": 0})
    time.sleep_ms(150)
    L.set_baud(DEF_BAUD)
    time.sleep_ms(100)
    r = None
    for _ in range(3):
        L.send(0x1407, {"bus_type": 7, "bus_id": 0})
        r = L.recv_until([0x1408], 1500)
        if r is not None:
            break
    if r is None:
        out.append("revert check FAIL (no status)")
    else:
        out.append("revert state=%s cur=%s target=%s" % (
            r[1].get("state"), r[1].get("cur_speed"), r[1].get("target_speed")))

    return "SPEED DONE\n" + "\n".join(out)


def _test_file_small():
    """新速下小檔上傳（10KB）驗 sha（chunk 用 send_wait 重試，遮蓋鏈路丟包）"""
    L = _link
    path = "/sd/_speed_probe.bin"
    data = _mkdata(10240)
    sha = _sha256(data)
    L.send(0x2009, {"path": path})
    time.sleep_ms(200)
    L.recv_until([0x2006, 0x2010], 1500)
    L._drain()
    L.send_wait(0x2001, {"file_id": 1, "total_size": len(data), "chunk_size": 4096,
                         "sha256": sha, "path": path}, want_cmds=(), timeout_ms=500, retries=1)
    time.sleep_ms(300)
    off = 0
    n = 0
    while off < len(data):
        chunk = data[off:off + 4096]
        r = L.send_wait(0x2002, {"file_id": 1, "offset": off, "data": chunk},
                        want_cmds=(0x2004, 0x2010), timeout_ms=3000, retries=3)
        if r is None:
            return "chunk fail @off=%d" % off
        if r[0] == 0x2010:
            return "ERR: %s" % r[1]
        off += len(chunk)
        n += 1
        time.sleep_ms(30)
    r = L.send_wait(0x2003, {"file_id": 1}, want_cmds=(0x2006, 0x2010),
                    timeout_ms=3000, retries=3)
    if r is None:
        return "no END rsp"
    if r[0] == 0x2010:
        return "END ERR: %s" % r[1]
    d = r[1]
    ok = d.get("sha256") == sha and d.get("size") == len(data)
    # 清理
    L.send(0x2009, {"path": path})
    time.sleep_ms(100)
    return "upload %dB sha=%s size=%s pending=%s" % (len(data), "OK" if ok else "BAD", d.get("size"), d.get("pending"))


# ── 測試 3: FILE 全新上傳 + 下載 ──

def t_file_upload():
    L = _link
    out = []
    path = "/sd/_night_up.bin"
    data = _mkdata(20480, 0x11)
    sha = _sha256(data)

    # 前置清場（DELETE 後要讀掉回應，避免殘留幀干擾後續）
    L.send(0x2009, {"path": path})
    time.sleep_ms(200)
    L.recv_until([0x2006, 0x2010], 2000)   # 讀掉 DELETE 的回應
    L._drain()

    # 0x2005 QUERY exists=0
    L.send(0x2005, {"path": path})
    r = L.recv_until([0x2006], 2000)
    if r is None:
        return "UP FAIL: no query rsp"
    out.append("pre exists=%s size=%s" % (r[1].get("exists"), r[1].get("size")))

    # BEGIN
    L.send(0x2001, {"file_id": 7, "total_size": len(data), "chunk_size": 4096,
                    "sha256": sha, "path": path})
    time.sleep_ms(300)                     # 讓 slave 建立 .tmp 檔（實測必要）
    # CHUNK ×5
    off = 0
    acks = 0
    while off < len(data):
        chunk = data[off:off + 4096]
        L.send(0x2002, {"file_id": 7, "offset": off, "data": chunk})
        r = L.recv_until([0x2004, 0x2010], 3000)
        if r is None:
            return "UP FAIL: no ACK @off=%d" % off
        if r[0] == 0x2010:
            return "UP ERR: %s" % r[1]
        if r[1].get("offset") != off:
            return "UP FAIL: ack offset=%s want=%d" % (r[1].get("offset"), off)
        acks += 1
        off += len(chunk)
        time.sleep_ms(30)                  # 每 chunk 間隔，讓 slave 寫檔
    out.append("chunks=%d acks=%d" % (5, acks))

    # END
    L.send(0x2003, {"file_id": 7})
    r = L.recv_until([0x2006, 0x2010], 3000)
    if r is None:
        return "UP FAIL: no END rsp"
    if r[0] == 0x2010:
        return "UP END ERR: %s" % r[1]
    d = r[1]
    out.append("end exists=%s size=%s pending=%s sha_ok=%s" % (
        d.get("exists"), d.get("size"), d.get("pending"),
        "OK" if d.get("sha256") == sha else "BAD"))

    # 下載驗證：分片 READ
    dl = bytearray()
    pos = 0
    while pos < len(data):
        L.send(0x2007, {"path": path, "offset": pos, "length": 4096})
        r = L.recv_until([0x2002, 0x2010], 3000)
        if r is None:
            return "DL FAIL: no chunk @%d" % pos
        if r[0] == 0x2010:
            return "DL ERR: %s" % r[1]
        cdata = r[1].get("data", b"")
        if not cdata:
            break
        dl.extend(cdata)
        pos += len(cdata)
    out.append("downloaded=%d sha_ok=%s" % (len(dl), "OK" if _sha256(dl) == sha else "BAD"))

    # 清理
    L.send(0x2009, {"path": path})
    time.sleep_ms(100)
    return "UPLOAD+DOWNLOAD DONE\n" + "\n".join(out)


# ── 測試 4: 備份/恢復（覆蓋→CONFIRM / 覆蓋→UNDO）──

def t_file_backup():
    L = _link
    out = []
    path = "/sd/_night_bak.bin"
    v1 = _mkdata(8192, 0x21)
    v2 = _mkdata(12288, 0x22)
    v3 = _mkdata(4096, 0x23)
    s1, s2, s3 = _sha256(v1), _sha256(v2), _sha256(v3)

    def _upload(ver, fid, data, sha):
        L.send(0x2001, {"file_id": fid, "total_size": len(data), "chunk_size": 4096,
                        "sha256": sha, "path": path})
        time.sleep_ms(80)
        off = 0
        while off < len(data):
            chunk = data[off:off + 4096]
            L.send(0x2002, {"file_id": fid, "offset": off, "data": chunk})
            r = L.recv_until([0x2004, 0x2010], 3000)
            if r is None:
                return "no ack@%d" % off
            if r[0] == 0x2010:
                return "err %s" % r[1]
            off += len(chunk)
        L.send(0x2003, {"file_id": fid})
        r = L.recv_until([0x2006, 0x2010], 3000)
        if r is None:
            return "no end rsp"
        return r

    # 清場
    L.send(0x2009, {"path": path})
    time.sleep_ms(100)
    L._drain()

    # v1 全新上傳
    r = _upload("v1", 1, v1, s1)
    if isinstance(r, str):
        return "BAK FAIL v1: " + r
    out.append("v1 upload pending=%s" % r[1].get("pending"))

    # v2 覆蓋 → pending=1，.bak 應存在
    r = _upload("v2", 2, v2, s2)
    if isinstance(r, str):
        return "BAK FAIL v2: " + r
    out.append("v2 upload pending=%s (expect 1)" % r[1].get("pending"))

    # QUERY 確認 pending + sha=v2
    L.send(0x2005, {"path": path})
    r = L.recv_until([0x2006], 2000)
    out.append("after-v2 sha_ok=%s pending=%s" % ("OK" if r[1].get("sha256") == s2 else "BAD", r[1].get("pending")))

    # 讀 .bak 內容確認是 v1
    bak = "/sd/_night_bak.bin.bak"
    L.send(0x2007, {"path": bak, "offset": 0, "length": 20000})
    r = L.recv_until([0x2002], 2000)
    bdata = r[1].get("data", b"") if r else b""
    out.append(".bak read %dB sha=%s (expect v1)" % (len(bdata), "OK" if _sha256(bdata) == s1 else "BAD"))

    # CONFIRM → pending=0，.bak 刪除
    L.send(0x2008, {"path": path})
    r = L.recv_until([0x2006], 2000)
    out.append("confirm pending=%s (expect 0)" % r[1].get("pending"))

    # v3 再覆蓋 → pending=1
    r = _upload("v3", 3, v3, s3)
    if isinstance(r, str):
        return "BAK FAIL v3: " + r
    out.append("v3 upload pending=%s (expect 1)" % r[1].get("pending"))

    # UNDO → 回 v2
    L.send(0x200A, {"path": path})
    r = L.recv_until([0x2006], 2000)
    out.append("undo sha_ok(v2)=%s pending=%s" % ("OK" if r[1].get("sha256") == s2 else "BAD", r[1].get("pending")))

    # 清理
    L.send(0x2009, {"path": path})
    time.sleep_ms(100)
    return "BACKUP/RESTORE DONE\n" + "\n".join(out)


# ── 測試 5: 斷點續傳 ──

def t_file_resume():
    L = _link
    out = []
    path = "/sd/_night_res.bin"
    data = _mkdata(16384, 0x33)
    sha = _sha256(data)

    L.send(0x2009, {"path": path})
    time.sleep_ms(100)
    L._drain()

    # BEGIN + 傳 2 塊 (8192B) 中斷（不 END）
    L.send(0x2001, {"file_id": 5, "total_size": len(data), "chunk_size": 4096,
                    "sha256": sha, "path": path})
    time.sleep_ms(80)
    off = 0
    for _ in range(2):
        chunk = data[off:off + 4096]
        L.send(0x2002, {"file_id": 5, "offset": off, "data": chunk})
        r = L.recv_until([0x2004], 3000)
        if r is None:
            return "RESUME FAIL: no ack@%d" % off
        off += len(chunk)
    out.append("interrupted at %d (2 chunks)" % off)

    # PARTIAL_QUERY
    L.send(0x200E, {"path": path})
    r = L.recv_until([0x200F], 2000)
    if r is None:
        return "RESUME FAIL: no partial rsp"
    out.append("partial=%s written=%s total=%s" % (r[1].get("partial"), r[1].get("written"), r[1].get("total_size")))

    # 重新 BEGIN 同身份 → 續傳
    L.send(0x2001, {"file_id": 6, "total_size": len(data), "chunk_size": 4096,
                    "sha256": sha, "path": path})
    time.sleep_ms(80)
    # 續傳起點 = written
    w = r[1].get("written")
    off = w if w is not None else 0
    while off < len(data):
        chunk = data[off:off + 4096]
        L.send(0x2002, {"file_id": 6, "offset": off, "data": chunk})
        r = L.recv_until([0x2004, 0x2010], 3000)
        if r is None:
            return "RESUME FAIL: no ack resume@%d" % off
        if r[0] == 0x2010:
            return "RESUME ERR: %s" % r[1]
        off += len(chunk)

    L.send(0x2003, {"file_id": 6})
    r = L.recv_until([0x2006, 0x2010], 3000)
    if r is None:
        return "RESUME FAIL: no end rsp"
    if r[0] == 0x2010:
        return "RESUME END ERR: %s" % r[1]
    out.append("end sha_ok=%s size=%s partial_rsp=%s" % (
        "OK" if r[1].get("sha256") == sha else "BAD", r[1].get("size"), r[1].get("pending")))

    L.send(0x2009, {"path": path})
    time.sleep_ms(100)
    return "RESUME DONE\n" + "\n".join(out)


# ── 測試 6: 錯誤路徑 ──

def t_file_error():
    L = _link
    out = []
    path = "/sd/_night_err.bin"
    data = _mkdata(4096, 0x44)
    good_sha = _sha256(data)
    bad_sha = _sha256(b"wrong data")

    L.send(0x2009, {"path": path})
    time.sleep_ms(100)
    L._drain()

    # 1) sha 錯誤 → END 回 err_sha_mismatch
    L.send(0x2001, {"file_id": 9, "total_size": len(data), "chunk_size": 4096,
                    "sha256": bad_sha, "path": path})
    time.sleep_ms(80)
    L.send(0x2002, {"file_id": 9, "offset": 0, "data": data})
    r = L.recv_until([0x2004, 0x2010], 3000)
    L.send(0x2003, {"file_id": 9})
    r = L.recv_until([0x2006, 0x2010], 3000)
    if r is None:
        out.append("sha-err: no rsp")
    elif r[0] == 0x2010:
        out.append("sha-err: err_sha_mismatch=%s" % r[1].get("err_sha_mismatch"))
    else:
        out.append("sha-err: NOT REJECTED?! pending=%s" % r[1].get("pending"))
    # 檔案不應落地
    L.send(0x2005, {"path": path})
    r = L.recv_until([0x2006], 2000)
    out.append("  after sha-err exists=%s (expect 0)" % r[1].get("exists"))

    # 2) file_id 不符 → err_id_mismatch
    L.send(0x2001, {"file_id": 1, "total_size": len(data), "chunk_size": 4096,
                    "sha256": good_sha, "path": path})
    time.sleep_ms(80)
    L.send(0x2002, {"file_id": 2, "offset": 0, "data": data})   # id 不符
    r = L.recv_until([0x2004, 0x2010], 3000)
    if r is None:
        out.append("id-err: no rsp")
    elif r[0] == 0x2010:
        out.append("id-err: err_id_mismatch=%s" % r[1].get("err_id_mismatch"))
    else:
        out.append("id-err: got ACK (not rejected)")
    # 清場（END 正常結束避免殘留）
    L.send(0x2003, {"file_id": 1})
    time.sleep_ms(100)

    # 3) 無 session 就 CHUNK → err_not_active
    L.send(0x2002, {"file_id": 99, "offset": 0, "data": b"\x01\x02"})
    r = L.recv_until([0x2004, 0x2010], 2000)
    if r is None:
        out.append("no-session: no rsp")
    elif r[0] == 0x2010:
        out.append("no-session: err_not_active=%s" % r[1].get("err_not_active"))
    else:
        out.append("no-session: got ACK")

    # 4) MOVE 跨卷 → err_write_fail（/sd → /ram）
    src = "/sd/_night_err_src.bin"
    dst = "/ram/_night_err_dst.bin"
    # 先建 src
    L.send(0x2001, {"file_id": 3, "total_size": len(data), "chunk_size": 4096,
                    "sha256": good_sha, "path": src})
    time.sleep_ms(80)
    L.send(0x2002, {"file_id": 3, "offset": 0, "data": data})
    r = L.recv_until([0x2004], 3000)
    L.send(0x2003, {"file_id": 3})
    r = L.recv_until([0x2006, 0x2010], 3000)
    # MOVE /sd→/ram
    L.send(0x200D, {"src": src, "dst": dst})
    r = L.recv_until([0x2010, 0x2006], 2000)
    if r is None:
        out.append("cross-move: no rsp")
    elif r[0] == 0x2010:
        out.append("cross-move: err_write_fail=%s (expect 1)" % r[1].get("err_write_fail"))
    else:
        out.append("cross-move: not rejected?!")
    # src 應還在
    L.send(0x2005, {"path": src})
    r = L.recv_until([0x2006], 2000)
    out.append("  src still exists=%s (expect 1)" % r[1].get("exists"))

    # 清理
    L.send(0x2009, {"path": src})
    time.sleep_ms(100)
    return "ERROR-PATH DONE\n" + "\n".join(out)


# ── 測試 7: 檔案管理（QUERY/DELETE/MOVE 同卷）──

def t_file_mgmt():
    L = _link
    out = []
    src = "/sd/_night_mgmt_a.bin"
    dst = "/sd/_night_mgmt_b.bin"
    data = _mkdata(2048, 0x55)
    sha = _sha256(data)

    for p in (src, dst):
        L.send(0x2009, {"path": p})
    time.sleep_ms(100)
    L._drain()

    # QUERY 不存在
    L.send(0x2005, {"path": src})
    r = L.recv_until([0x2006], 2000)
    out.append("query-none exists=%s (expect 0)" % r[1].get("exists"))

    # 上傳 src
    L.send(0x2001, {"file_id": 4, "total_size": len(data), "chunk_size": 4096,
                    "sha256": sha, "path": src})
    time.sleep_ms(80)
    L.send(0x2002, {"file_id": 4, "offset": 0, "data": data})
    r = L.recv_until([0x2004], 3000)
    L.send(0x2003, {"file_id": 4})
    r = L.recv_until([0x2006, 0x2010], 3000)
    out.append("upload src exists=%s" % r[1].get("exists"))

    # MOVE 同卷
    L.send(0x200D, {"src": src, "dst": dst})
    r = L.recv_until([0x2010, 0x2006], 2000)
    if r is None:
        out.append("move: no rsp")
    elif r[0] == 0x2010:
        out.append("move: ERR %s" % r[1])
    else:
        out.append("move: rsp")
    time.sleep_ms(100)

    # src 消失、dst 存在且 sha 正確
    L.send(0x2005, {"path": src})
    r = L.recv_until([0x2006], 2000)
    out.append("src exists=%s (expect 0)" % r[1].get("exists"))
    L.send(0x2005, {"path": dst})
    r = L.recv_until([0x2006], 2000)
    out.append("dst exists=%s sha_ok=%s" % (r[1].get("exists"), "OK" if r[1].get("sha256") == sha else "BAD"))

    # DELETE dst
    L.send(0x2009, {"path": dst})
    r = L.recv_until([0x2006], 2000)
    out.append("delete dst exists=%s (expect 0)" % r[1].get("exists"))

    return "MGMT DONE\n" + "\n".join(out)


# ── 測試 8: SPEED 不 COMMIT → 自動回滾 ──

def t_speed_auto_revert():
    L = _link
    out = []
    L.send(0x1407, {"bus_type": 7, "bus_id": 0})
    r = L.recv_until([0x1408], 2000)
    if r is None:
        return "AUTO-REVERT: no initial status"
    st = r[1]
    if st.get("state") != 0:
        L.send(0x1406, {"bus_type": 7, "bus_id": 0})
        time.sleep_ms(300)
    # SPEED_SET 不 COMMIT
    L.send(0x1403, {"bus_type": 7, "bus_id": 0, "speed": SPEED_BAUD, "timeout_ms": 1500})
    time.sleep_ms(50)
    L.set_baud(SPEED_BAUD)
    # 敲門確認已切
    L.send(0x1101, {"query_type": 0})
    r = L.recv_until([0x1102], 2000)
    out.append("after set, verify @%d: %s" % (SPEED_BAUD, "OK" if r else "FAIL"))
    # 等 timeout(1500ms) 自動回滾
    time.sleep_ms(2200)
    # 切回舊速確認 state=0 cur=115200
    L.set_baud(DEF_BAUD)
    L.send(0x1407, {"bus_type": 7, "bus_id": 0})
    r = L.recv_until([0x1408], 2000)
    if r is None:
        return "AUTO-REVERT: no status after revert"
    out.append("after timeout state=%s cur=%s (expect 0, 115200)" % (r[1].get("state"), r[1].get("cur_speed")))
    return "AUTO-REVERT DONE\n" + "\n".join(out)


# ── 手動 decode 輔助（SchemaCodec.decode 的 viper 路徑在此 firmware 壞，改用手動 unpack）──

def _dec_speed_status(pb):
    """SPEED_STATUS 0x1408: state:u8 bus_type:u8 bus_id:u8 cur:u32 target:u32 remain:u32"""
    import struct
    if len(pb) < 15:
        return {}
    v = struct.unpack('<BBBIII', pb[:15])
    return {'state': v[0], 'bus_type': v[1], 'bus_id': v[2],
            'cur_speed': v[3], 'target_speed': v[4], 'remain_ms': v[5]}


def _dec_speed_ack(pb):
    """SPEED_ACK 0x1404: ok:u8 bus_type:u8 bus_id:u8 cur:u32 target:u32"""
    import struct
    if len(pb) < 11:
        return {}
    v = struct.unpack('<BBBII', pb[:11])
    return {'ok': v[0], 'bus_type': v[1], 'bus_id': v[2],
            'cur_speed': v[3], 'target_speed': v[4]}


def _dec_file_query(pb):
    """FILE_QUERY_RSP 0x2006: exists:u8 sha256:32B size:u32 path:str_u16len free:u32 pending:u8"""
    import struct
    if len(pb) < 41:
        return {}
    exists = pb[0]
    sha = pb[1:33]
    size = struct.unpack('<I', pb[33:37])[0]
    # path: str_u16len
    plen = struct.unpack('<H', pb[37:39])[0]
    path = pb[39:39+plen].decode('utf-8', 'replace') if plen else ''
    off = 39 + plen
    free = struct.unpack('<I', pb[off:off+4])[0] if off+4 <= len(pb) else 0
    pending = pb[off+4] if off+4 < len(pb) else 0
    return {'exists': exists, 'sha256': sha, 'size': size, 'path': path, 'free': free, 'pending': pending}


def _dec_file_ack(pb):
    """FILE_ACK 0x2004: file_id:u16 offset:u32"""
    import struct
    if len(pb) < 6:
        return {}
    v = struct.unpack('<HI', pb[:6])
    return {'file_id': v[0], 'offset': v[1]}


def _dec_file_chunk(pb):
    """FILE_CHUNK 0x2002 (下載回應): file_id:u16 offset:u32 data:bytes_rest"""
    import struct
    if len(pb) < 6:
        return {}
    v = struct.unpack('<HI', pb[:6])
    return {'file_id': v[0], 'offset': v[1], 'data': pb[6:]}


def _dec_file_partial(pb):
    """FILE_PARTIAL_RSP 0x200F: partial:u8 written:u32 total_size:u32 sha256:32B path:str"""
    import struct
    if len(pb) < 41:
        return {}
    partial = pb[0]
    written = struct.unpack('<I', pb[1:5])[0]
    total = struct.unpack('<I', pb[5:9])[0]
    sha = pb[9:41]
    plen = struct.unpack('<H', pb[41:43])[0] if len(pb) >= 43 else 0
    path = pb[43:43+plen].decode('utf-8','replace') if plen else ''
    return {'partial': partial, 'written': written, 'total_size': total, 'sha256': sha, 'path': path}


def _dec_file_error(pb):
    """FILE_ERROR_RSP 0x2010: 7 err flags u8 + failed_offset:u32 + written_up_to:u32 + path:str"""
    import struct
    if len(pb) < 7:
        return {}
    flags = pb[0:7]
    names = ['err_no_space','err_write_fail','err_offset_mismatch','err_id_mismatch',
             'err_sha_mismatch','err_not_active','err_busy']
    out = {names[i]: flags[i] for i in range(7)}
    off = 7
    if off+4 <= len(pb):
        out['failed_offset'] = struct.unpack('<I', pb[off:off+4])[0]
        off += 4
    if off+4 <= len(pb):
        out['written_up_to'] = struct.unpack('<I', pb[off:off+4])[0]
        off += 4
    if off < len(pb):
        plen = struct.unpack('<H', pb[off:off+2])[0] if off+2 <= len(pb) else 0
        out['path'] = pb[off+2:off+2+plen].decode('utf-8','replace') if plen else ''
    return out


_HAND_DEC = {
    0x1408: _dec_speed_status,
    0x1404: _dec_speed_ack,
    0x2006: _dec_file_query,
    0x2004: _dec_file_ack,
    0x2002: _dec_file_chunk,
    0x200F: _dec_file_partial,
    0x2010: _dec_file_error,
}
