# tools/selftest_file.py
#
# 檔案更新流程的 loopback 自測 (on-device, USB REPL 手動執行)。
#
# 原理:
#   發起端把 NC4 幀直接送進 app.handle_stream() (與 BusDecodeTask 相同的解碼器入口),
#   handler 的 ctx["send"] 被接到 Loopback.send(), 把回應幀快照進 inbox;
#   發起端再從 inbox 讀回應, 用獨立 StreamParser 解碼。
#   因此「請求 → 解碼 → handler → 回應 → 解碼」整條路徑都是真的, 只是傳輸層換成記憶體迴路。
#
# 注意:
#   - 只在 MicroPython 裝置上跑 (用到 ujson/ubinascii)。
#   - Proto.pack() 回傳共享 buffer, Loopback.send() 內必須 bytes() 快照, 否則會被下一個 pack 覆蓋。
#   - 所有回應幀都是廣播 (addr=0xFFFF), handle_stream 的 addr 過濾會放行。
#
# 用法 (USB REPL):
#   >>> import sys; sys.path.insert(0, "/")
#   >>> exec(open("/tools/selftest_file.py").read())   # 或直接貼上執行
#   >>> run_all()

import os
import hashlib
import ubinascii

from lib.sys.proto import Proto
from lib.sys.schema_codec import SchemaCodec
from lib.sys.fs_manager import fs
# 註: handler 由 App.__init__() 內部的 register_all() 完成, 這裡不重複。


class Loopback:
    def __init__(self, app):
        self.app = app
        self.parser = app.create_parser()   # 請求路徑的解碼器
        self.rp = app.create_parser()       # 回應路徑的解碼器
        self.inbox = []

    def send(self, data):
        """handler 的 ctx['send'] 接這裡: 快照回應幀 (共享 buffer 陷阱)。"""
        self.inbox.append(bytes(data))

    def tx(self, cmd, fields):
        """發起端: encode + pack + 直接送進解碼器 (同步跑完 handler)。"""
        d = self.app.store.get(cmd)
        payload = SchemaCodec.encode(d, fields)
        self.app.handle_stream(self.parser, Proto.pack(cmd, payload), "LOOP", self.send)

    def recv(self):
        """讀下一筆回應幀, 回傳 (cmd_int, fields_dict) 或 None。"""
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


# ── 工具 ──────────────────────────────────────────────

def make_data(n, seed=1):
    b = bytearray(n)
    x = seed
    for i in range(n):
        x = (x * 1103515245 + 12345) & 0x7FFFFFFF
        b[i] = x & 0xFF
    return bytes(b)


def sha_digest(data):
    return hashlib.sha256(data).digest()


def sha_hex(data):
    return ubinascii.hexlify(sha_digest(data)).decode()


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


PASS = []
FAIL = []


def check(cond, msg, extra=""):
    if cond:
        PASS.append(msg)
        print("  ✅", msg)
    else:
        FAIL.append(msg)
        print("  ❌", msg, extra)


# ── 上傳一個檔案 (完整 chunk 迴圈 + END) ──────────────

def do_upload(lb, path, data, file_id=1, chunk_size=4096):
    total = len(data)
    lb.tx(0x2001, {
        "file_id": file_id,
        "total_size": total,
        "chunk_size": chunk_size,
        "sha256": sha_digest(data),
        "path": path,
    })
    for off in range(0, total, chunk_size):
        lb.tx(0x2002, {
            "file_id": file_id,
            "offset": off,
            "data": data[off:off + chunk_size],
        })
        cmd, f = lb.recv()
        if cmd != 0x2004 or f.get("offset") != off:
            return False
    lb.tx(0x2003, {"file_id": file_id})
    return lb.recv()


# ── 場景 ──────────────────────────────────────────────

def scenario_new_upload_download_delete(lb, path):
    print("\n== 場景 A: 全新上傳 + 查詢 + 下載 + 刪除 ==")
    reset_path(path)
    data = make_data(20000, seed=1)

    # 前置查詢
    lb.tx(0x2005, {"path": path})
    cmd, f = lb.recv()
    check(cmd == 0x2006 and f.get("exists") == 0, "A.前置查詢 exists=0", f)

    # 上傳
    cmd, f = do_upload(lb, path, data)
    ok = (cmd == 0x2006 and f.get("exists") == 1
          and f.get("sha256") == sha_digest(data)
          and f.get("size") == len(data)
          and f.get("pending") == 0)
    check(ok, "A.上傳完成 sha/size 正確、pending=0", f)

    # 下載片段
    lb.tx(0x2007, {"path": path, "offset": 1000, "length": 4096})
    cmd, f = lb.recv()
    got = bytes(f.get("data", b"")) if f else b""
    check(cmd == 0x2002 and f.get("file_id") == 0
          and got == data[1000:1000 + 4096], "A.下載片段內容正確", f)

    # 刪除
    lb.tx(0x2009, {"path": path})
    cmd, f = lb.recv()
    check(cmd == 0x2006 and f.get("exists") == 0, "A.刪除後 exists=0", f)


def scenario_overwrite_confirm_undo(lb, path):
    print("\n== 場景 B: 同名覆蓋 + 兩段式 commit (confirm/undo) ==")
    reset_path(path)
    v1 = make_data(8000, seed=11)
    v2 = make_data(8000, seed=22)
    v3 = make_data(8000, seed=33)

    cmd, f = do_upload(lb, path, v1)
    check(cmd == 0x2006 and f.get("pending") == 0, "B.首傳 v1 pending=0", f)

    # 覆蓋 v2 → 應 pending=1
    cmd, f = do_upload(lb, path, v2)
    check(cmd == 0x2006 and f.get("pending") == 1
          and f.get("sha256") == sha_digest(v2), "B.覆蓋 v2 後 pending=1", f)

    # CONFIRM → pending=0, 保留 v2
    lb.tx(0x2008, {"path": path})
    cmd, f = lb.recv()
    check(cmd == 0x2006 and f.get("pending") == 0
          and f.get("sha256") == sha_digest(v2), "B.CONFIRM 後 pending=0 且保留 v2", f)

    # 覆蓋 v3 → UNDO → 回到 v2
    cmd, f = do_upload(lb, path, v3)
    check(cmd == 0x2006 and f.get("pending") == 1, "B.覆蓋 v3 後 pending=1", f)
    lb.tx(0x200A, {"path": path})
    cmd, f = lb.recv()
    check(cmd == 0x2006 and f.get("pending") == 0
          and f.get("sha256") == sha_digest(v2), "B.UNDO 後回到 v2", f)


def scenario_sha_mismatch(lb, path):
    print("\n== 場景 C: sha 不符 → 拒絕落地 ==")
    reset_path(path)
    data = make_data(5000, seed=5)
    wrong = sha_digest(b"wrong")

    lb.tx(0x2001, {"file_id": 1, "total_size": len(data),
                   "chunk_size": 4096, "sha256": wrong, "path": path})
    lb.tx(0x2002, {"file_id": 1, "offset": 0, "data": data})
    lb.recv()  # ACK
    lb.tx(0x2003, {"file_id": 1})
    cmd, f = lb.recv()
    check(cmd == 0x2010 and f.get("err_sha_mismatch") == 1, "C.回 err_sha_mismatch", f)

    # 確認沒落地、無 pending
    lb.tx(0x2005, {"path": path})
    cmd, f = lb.recv()
    check(cmd == 0x2006 and f.get("exists") == 0 and f.get("pending") == 0,
          "C.檔案未落地且無 pending", f)


def scenario_resume(lb, path):
    print("\n== 場景 D: 斷點續傳 ==")
    reset_path(path)
    data = make_data(10000, seed=7)
    chunk = 4096

    # 傳 2 塊後中斷 (不 END)
    lb.tx(0x2001, {"file_id": 1, "total_size": len(data),
                   "chunk_size": chunk, "sha256": sha_digest(data), "path": path})
    for off in (0, chunk):
        lb.tx(0x2002, {"file_id": 1, "offset": off, "data": data[off:off + chunk]})
        lb.recv()  # ACK

    # partial 查詢 → written == 2*chunk
    lb.tx(0x200E, {"path": path})
    cmd, f = lb.recv()
    check(cmd == 0x200F and f.get("partial") == 1
          and f.get("written") == 2 * chunk, "D.中斷後 partial written=8192", f)

    # 重新 BEGIN (同 path+size+sha) → 應自動續傳
    lb.tx(0x2001, {"file_id": 2, "total_size": len(data),
                   "chunk_size": chunk, "sha256": sha_digest(data), "path": path})
    for off in range(2 * chunk, len(data), chunk):
        lb.tx(0x2002, {"file_id": 2, "offset": off, "data": data[off:off + chunk]})
        lb.recv()  # ACK
    lb.tx(0x2003, {"file_id": 2})
    cmd, f = lb.recv()
    check(cmd == 0x2006 and f.get("sha256") == sha_digest(data)
          and f.get("size") == len(data), "D.續傳完成 sha/size 正確", f)

    # partial 應已清空
    lb.tx(0x200E, {"path": path})
    cmd, f = lb.recv()
    check(cmd == 0x200F and f.get("partial") == 0, "D.完成後 partial=0", f)


def scenario_move(lb, path):
    print("\n== 場景 E: 通用改名 (FILE_MOVE) ==")
    reset_path(path)
    dst = path + ".renamed"
    data = make_data(3000, seed=9)

    cmd, f = do_upload(lb, path, data)
    check(cmd == 0x2006, "E.上傳準備完成", f)

    lb.tx(0x200D, {"src": path, "dst": dst})
    # FILE_MOVE 成功不回覆; 用 query 驗證
    lb.tx(0x2005, {"path": path})
    cmd, f = lb.recv()
    check(cmd == 0x2006 and f.get("exists") == 0, "E.原路徑不存在", f)
    lb.tx(0x2005, {"path": dst})
    cmd, f = lb.recv()
    check(cmd == 0x2006 and f.get("exists") == 1
          and f.get("sha256") == sha_digest(data), "E.新路徑存在且 sha 正確", f)

    reset_path(dst)


# ── 入口 ──────────────────────────────────────────────

def run_all():
    from app import App
    app = App()
    lb = Loopback(app)
    path = "/sd/_selftest.bin"

    del PASS[:]
    del FAIL[:]

    scenario_new_upload_download_delete(lb, path)
    scenario_overwrite_confirm_undo(lb, path)
    scenario_sha_mismatch(lb, path)
    scenario_resume(lb, path)
    scenario_move(lb, path)

    print("\n" + "=" * 40)
    print(f"結果: {len(PASS)} 通過, {len(FAIL)} 失敗")
    if FAIL:
        print("失敗項:")
        for m in FAIL:
            print("  -", m)
    else:
        print("🎉 全部通過")
    return len(FAIL) == 0


if __name__ == "__main__":
    run_all()
