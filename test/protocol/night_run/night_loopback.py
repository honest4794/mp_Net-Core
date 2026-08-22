# -*- coding: utf-8 -*-
"""night_loopback — 1201 單板 loopback 綜合測試（不用第二塊板）

透過 app.handle_stream 記憶體迴路（與 selftest_file 相同機制），驗證：
  T1: FILE 全新上傳 256KB 大檔 + 分片下載 + 完整 sha 比對
  T2: 錯誤路徑（無 session CHUNK / file_id 不符 / MOVE 跨卷 / 下載不存在）
  T3: SPEED 提速狀態機（QUERY→SET→COMMIT→REVERT + 非法 bus_type/bus_id）
  T4: FILE_READ 下載不存在檔案（回空 data）

用法: exec(open("night_loopback.py").read()); run_night()
"""

import os
import hashlib
import ubinascii

from lib.sys.proto import Proto
from lib.sys.schema_codec import SchemaCodec
from lib.sys.fs_manager import fs
from lib.sys import bus_speed


class Loopback:
    def __init__(self, app):
        self.app = app
        self.parser = app.create_parser()
        self.rp = app.create_parser()
        self.inbox = []

    def send(self, data):
        self.inbox.append(bytes(data))

    def tx(self, cmd, fields):
        d = self.app.store.get(cmd)
        payload = SchemaCodec.encode(d, fields)
        self.app.handle_stream(self.parser, Proto.pack(cmd, payload), "LOOP", self.send)

    def recv(self):
        if not self.inbox:
            return None
        data = self.inbox.pop(0)
        self.rp.feed(data)
        r = self.rp.pop_frame()
        if r is None:
            return None
        _ver, _addr, cmd, payload = r
        d = self.app.store.get(cmd)
        fields = SchemaCodec.decode(d, payload, self.app.store) if d else {}
        return cmd, fields


PASS = []
FAIL = []


def check(cond, msg, extra=""):
    if cond:
        PASS.append(msg)
        print("  \u2705", msg)
    else:
        FAIL.append(msg)
        print("  \u274c", msg, extra)


def make_data(n, seed=1):
    b = bytearray(n)
    x = seed
    for i in range(n):
        x = (x * 1103515245 + 12345) & 0x7FFFFFFF
        b[i] = x & 0xFF
    return bytes(b)


def sha_digest(data):
    return hashlib.sha256(data).digest()


def reset_path(path):
    for p in (path, path + ".tmp", path + ".bak"):
        try:
            os.remove(p)
        except Exception:
            pass
    fs.delta["partial"].pop(path, None)
    fs.delta["pending"].pop(path, None)
    fs._save_delta()
    fs.remove_manifest_entry(path)


def do_upload(lb, path, data, file_id=1, chunk_size=4096):
    total = len(data)
    lb.tx(0x2001, {
        "file_id": file_id, "total_size": total, "chunk_size": chunk_size,
        "sha256": sha_digest(data), "path": path,
    })
    for off in range(0, total, chunk_size):
        lb.tx(0x2002, {"file_id": file_id, "offset": off, "data": data[off:off + chunk_size]})
        cmd, f = lb.recv()
        if cmd != 0x2004 or f.get("offset") != off:
            return (cmd, f)
    lb.tx(0x2003, {"file_id": file_id})
    return lb.recv()


def t_big_file(lb):
    print("\n== T1: 256KB 大檔上傳 + 分片下載 + sha ==")
    path = "/sd/_night_big.bin"
    reset_path(path)
    data = make_data(262144, seed=42)   # 256KB
    print("  data: %d bytes sha=%s" % (len(data), ubinascii.hexlify(sha_digest(data)).decode()[:16]))

    cmd, f = do_upload(lb, path, data, file_id=10)
    ok = (cmd == 0x2006 and f.get("exists") == 1
          and f.get("sha256") == sha_digest(data) and f.get("size") == len(data))
    check(ok, "T1.大檔上傳 sha/size 正確", f)

    # 下載分片驗證 (offset 0, 中間, 尾段)
    ok_all = True
    for off in (0, 100000, len(data) - 4096):
        lb.tx(0x2007, {"path": path, "offset": off, "length": 4096})
        cmd, f = lb.recv()
        got = bytes(f.get("data", b"")) if f else b""
        exp = data[off:off + 4096]
        if not (cmd == 0x2002 and got == exp):
            ok_all = False
            print("    download mismatch @%d got %d exp %d" % (off, len(got), len(exp)))
    check(ok_all, "T1.分片下載內容正確", "")

    reset_path(path)
    check(True, "T1.清理完成", "")


def t_error_paths(lb):
    print("\n== T2: 錯誤路徑 ==")
    path = "/sd/_night_err.bin"
    reset_path(path)
    data = make_data(4096, seed=7)

    # 1) 無 session 就 CHUNK → err_not_active
    lb.tx(0x2002, {"file_id": 99, "offset": 0, "data": b"\x01\x02"})
    cmd, f = lb.recv()
    check(cmd == 0x2010 and f.get("err_not_active") == 1, "T2.無 session CHUNK → err_not_active", f)

    # 2) BEGIN 後 file_id 不符 → err_id_mismatch
    lb.tx(0x2001, {"file_id": 1, "total_size": len(data), "chunk_size": 4096,
                   "sha256": sha_digest(data), "path": path})
    lb.tx(0x2002, {"file_id": 2, "offset": 0, "data": data})   # id 不符
    cmd, f = lb.recv()
    check(cmd == 0x2010 and f.get("err_id_mismatch") == 1, "T2.file_id 不符 → err_id_mismatch", f)
    # 清 session
    lb.tx(0x2003, {"file_id": 1})
    lb.recv()

    # 3) MOVE 跨卷 → err_write_fail
    src = "/sd/_night_move_src.bin"
    dst = "/ram/_night_move_dst.bin"
    reset_path(src)
    cmd, f = do_upload(lb, src, make_data(2000, seed=9))
    check(cmd == 0x2006, "T2.move src 上傳完成", f)
    lb.tx(0x200D, {"src": src, "dst": dst})
    cmd, f = lb.recv()
    check(cmd == 0x2010 and f.get("err_write_fail") == 1, "T2.MOVE 跨卷 → err_write_fail", f)
    reset_path(src)

    # 4) 下載不存在檔案 → 空 data (EOF 表示)
    lb.tx(0x2007, {"path": "/sd/_nonexist.bin", "offset": 0, "length": 4096})
    cmd, f = lb.recv()
    got = bytes(f.get("data", b"")) if f else b""
    check(cmd == 0x2002 and len(got) == 0, "T2.下載不存在檔案 → 空 data", f)

    # 5) DELETE 不存在 → 正常回 RSP (exists=0)
    lb.tx(0x2009, {"path": "/sd/_nonexist.bin"})
    cmd, f = lb.recv()
    check(cmd == 0x2006 and f.get("exists") == 0, "T2.DELETE 不存在 → exists=0", f)


def t_speed_state(lb):
    print("\n== T3: SPEED 提速狀態機 ==")
    bus_type, bus_id = 7, 0

    # 1) QUERY 初始 IDLE
    lb.tx(0x1407, {"bus_type": bus_type, "bus_id": bus_id})
    cmd, f = lb.recv()
    check(cmd == 0x1408 and f.get("state") == 0, "T3.QUERY 初始 state=0", f)

    # 2) SET (UART, id=0) → 切速 + SYNCING + ACK ok=1
    lb.tx(0x1403, {"bus_type": bus_type, "bus_id": bus_id, "speed": 921600, "timeout_ms": 3000})
    cmd, f = lb.recv()
    check(cmd == 0x1404 and f.get("ok") == 1, "T3.SET → ACK ok=1", f)
    check(f.get("target_speed") == 921600, "T3.ACK target_speed=921600", f)
    st = bus_speed._get_state()
    check(st.get("state") == bus_speed.STATE_SYNCING, "T3.狀態=SYNCING", st)

    # 3) QUERY 確認 SYNCING + remain
    lb.tx(0x1407, {"bus_type": bus_type, "bus_id": bus_id})
    cmd, f = lb.recv()
    check(cmd == 0x1408 and f.get("state") == 1, "T3.QUERY state=1 (SYNCING)", f)
    check(f.get("remain_ms", 0) > 0, "T3.remain_ms 計時中", f)

    # 4) COMMIT → COMMITTED (COMMIT 無回覆)
    lb.tx(0x1405, {"bus_type": bus_type, "bus_id": bus_id})
    lb.tx(0x1407, {"bus_type": bus_type, "bus_id": bus_id})
    cmd, f = lb.recv()
    check(cmd == 0x1408 and f.get("state") == 2, "T3.COMMIT 後 state=2 (COMMITTED)", f)

    # 5) REVERT → IDLE (REVERT 無回覆)
    lb.tx(0x1406, {"bus_type": bus_type, "bus_id": bus_id})
    lb.tx(0x1407, {"bus_type": bus_type, "bus_id": bus_id})
    cmd, f = lb.recv()
    check(cmd == 0x1408 and f.get("state") == 0, "T3.REVERT 後 state=0 (IDLE)", f)

    # 6) 非法 bus_type (SPI=2) → ACK ok=0
    lb.tx(0x1403, {"bus_type": 2, "bus_id": 0, "speed": 921600, "timeout_ms": 1000})
    cmd, f = lb.recv()
    check(cmd == 0x1404 and f.get("ok") == 0, "T3.SET SPI → ok=0 (not supported)", f)

    # 7) 非法 bus_id (超界) → ACK ok=0
    lb.tx(0x1403, {"bus_type": 7, "bus_id": 9, "speed": 921600, "timeout_ms": 1000})
    cmd, f = lb.recv()
    check(cmd == 0x1404 and f.get("ok") == 0, "T3.SET bus_id=9 → ok=0", f)


def t_read_missing(lb):
    print("\n== T4: 額外下載邊界 ==")
    # 讀取 length=0 → 空 data
    lb.tx(0x2007, {"path": "/sd/_night_big.bin", "offset": 0, "length": 0})
    cmd, f = lb.recv()
    got = bytes(f.get("data", b"")) if f else b""
    check(cmd == 0x2002 and len(got) == 0, "T4.READ length=0 → 空 data", f)


def run_night():
    from app import App
    app = App()
    lb = Loopback(app)

    del PASS[:]
    del FAIL[:]

    t_big_file(lb)
    t_error_paths(lb)
    t_speed_state(lb)
    t_read_missing(lb)
    t_speed_auto_revert(lb)

    print("\n" + "=" * 40)
    print("night_loopback 結果: %d 通過, %d 失敗" % (len(PASS), len(FAIL)))
    if FAIL:
        for m in FAIL:
            print("  -", m)
    else:
        print("\U0001F389 全部通過")
    return len(FAIL) == 0


if __name__ == "__main__":
    run_night()


def t_speed_auto_revert(lb):
    print("\n== T5: SPEED 不 COMMIT → timeout 自動回滾 ==")
    bus_type, bus_id = 7, 0
    # 確保 IDLE
    lb.tx(0x1407, {"bus_type": bus_type, "bus_id": bus_id})
    lb.recv()

    # SET 但 timeout 很短 (1500ms)，不 COMMIT
    lb.tx(0x1403, {"bus_type": bus_type, "bus_id": bus_id, "speed": 921600, "timeout_ms": 1500})
    cmd, f = lb.recv()
    check(cmd == 0x1404 and f.get("ok") == 1, "T5.SET ok=1", f)

    # 立即查：SYNCING
    lb.tx(0x1407, {"bus_type": bus_type, "bus_id": bus_id})
    cmd, f = lb.recv()
    check(f.get("state") == 1, "T5.立即查 state=1 (SYNCING)", f)

    # 等超過 timeout (1500ms + margin)
    import time
    time.sleep_ms(2000)

    # 不 COMMIT，模擬 CircuitTask.loop 呼叫 poll → 應自動回滾到 IDLE
    bus_speed.bus_speed_poll()
    lb.tx(0x1407, {"bus_type": bus_type, "bus_id": bus_id})
    cmd, f = lb.recv()
    check(cmd == 0x1408 and f.get("state") == 0, "T5.timeout 後 poll 觸發自動回滾 state=0 (IDLE)", f)
    st = bus_speed._get_state()
    check(st.get("state") == bus_speed.STATE_IDLE, "T5.內部狀態 IDLE", st)
