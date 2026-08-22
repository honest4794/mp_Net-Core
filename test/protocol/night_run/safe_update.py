# -*- coding: utf-8 -*-
"""safe_update.py — Master 端「安全檔案更新」流程（基於 master_agent.Link）

流程（對應用戶需求）：
  1. stage()       新檔先傳到 slave 的暫存路徑 /sd/_XD_<name>（不碰正式檔）
  2. verify_stage() 下載回暫存檔驗 sha256 == 本地
  3. apply()       把暫存檔「交換」到正式路徑（slave 兩段式 commit 自動留 .bak）
  4. confirm()     確認 → 刪 .bak（正式生效）
  5. undo()        回滾 → .bak 蓋回（恢復舊檔）
  6. cleanup()     刪除

用法（Master 板 REPL，需先 import master_agent 建 link）：
    import master_agent as ma
    print(ma.init_link(115200))
    import safe_update
    safe_update.stage('/sd/new.bin')      # 把 Master 本地 /sd/new.bin 傳到 slave 暫存
    safe_update.apply('/sd/new.bin', '/sd/final.bin')   # 交換到正式路徑
    safe_update.confirm('/sd/final.bin')   # 確認
    safe_update.undo('/sd/final.bin')      # 回滾
"""

import time
import uhashlib

import master_agent as ma

CHUNK = 4096
STAGE_PREFIX = "/sd/_XD_"


def _L():
    return ma._link


def _sha256_data(data):
    return uhashlib.sha256(data).digest()


def _read_local(path):
    with open(path, 'rb') as f:
        return f.read()


def stage(local_path, slave_id=None):
    """把 Master 本地 local_path 傳到 slave 的暫存路徑 /sd/_XD_<basename>。
    回 (ok, 訊息)。"""
    L = _L()
    name = local_path.strip('/').split('/')[-1]
    remote = STAGE_PREFIX + name
    data = _read_local(local_path)
    sha = _sha256_data(data)
    addr = ma.ADDR_BROADCAST if slave_id is None else slave_id

    # 清掉舊暫存
    L.send(0x2009, {"path": remote}, addr=addr)
    time.sleep_ms(150)
    L.recv_until([0x2006, 0x2010], 800)
    L._drain()

    # BEGIN（無回覆，靠後續 chunk 的 ACK 確認是否生效；若 chunk 回 err_not_active 就重發 BEGIN）
    L.send(0x2001, {"file_id": 1, "total_size": len(data), "chunk_size": CHUNK,
                    "sha256": sha, "path": remote}, addr=addr)
    time.sleep_ms(250)

    # CHUNK loop（重試遮蓋偶發掉包；BEGIN 若丟失，靠 err_not_active 自我修復）
    off = 0
    begin_retries = 0
    while off < len(data):
        chunk = data[off:off + CHUNK]
        r = L.send_wait(0x2002, {"file_id": 1, "offset": off, "data": chunk},
                        want_cmds=(0x2004, 0x2010), addr=addr,
                        timeout_ms=2000, retries=10)
        if r is None:
            return (False, "chunk fail @%d" % off)
        if r[0] == 0x2010:
            # err_not_active → BEGIN 沒生效（丟了），重發 BEGIN 再重試此 chunk
            if r[1].get('err_not_active') == 1 and begin_retries < 5:
                begin_retries += 1
                L.send(0x2001, {"file_id": 1, "total_size": len(data),
                                "chunk_size": CHUNK, "sha256": sha, "path": remote}, addr=addr)
                time.sleep_ms(300)
                continue
            return (False, "ERR: %s" % r[1])
        off += len(chunk)
        time.sleep_ms(20)

    # END
    r = L.send_wait(0x2003, {"file_id": 1}, want_cmds=(0x2006, 0x2010),
                    addr=addr, timeout_ms=3000, retries=10)
    if r is None:
        return (False, "no END rsp")
    if r[0] == 0x2010:
        return (False, "END ERR: %s" % r[1])
    ok = r[1].get('sha256') == sha
    return (ok, "staged %d bytes -> %s (sha %s)" % (len(data), remote, "OK" if ok else "BAD"))


def verify_stage(local_path, slave_id=None):
    """下載 slave 暫存檔，跟本地 sha 比對。回 (ok, 訊息)。"""
    L = _L()
    name = local_path.strip('/').split('/')[-1]
    remote = STAGE_PREFIX + name
    addr = ma.ADDR_BROADCAST if slave_id is None else slave_id
    local_sha = _sha256_data(_read_local(local_path))

    # 下載驗證
    dl = bytearray()
    pos = 0
    while True:
        L.send(0x2007, {"path": remote, "offset": pos, "length": CHUNK}, addr=addr)
        r = L.recv_until([0x2002, 0x2010], 3000)
        if r is None:
            return (False, "read fail @%d" % pos)
        cdata = bytes(r[1].get('data', b'')) if r[0] == 0x2002 else b''
        if not cdata:
            break
        dl.extend(cdata)
        pos += len(cdata)
        time.sleep_ms(20)
    ok = _sha256_data(dl) == local_sha
    return (ok, "verify %d bytes sha %s" % (len(dl), "OK" if ok else "BAD"))


def apply(local_path, final_path, slave_id=None):
    """把本地 local_path 直接上傳覆蓋 slave 的 final_path。
    slave 的 FILE_END 兩段式 commit 會自動把舊 final_path 留成 .bak（備份）。
    回 (ok, 訊息)。"""
    L = _L()
    addr = ma.ADDR_BROADCAST if slave_id is None else slave_id
    data = _read_local(local_path)
    sha = _sha256_data(data)

    # 上傳覆蓋（FILE_BEGIN 對已存在的 final_path 會走「覆蓋」路徑，END 後留 .bak）
    L.send(0x2001, {"file_id": 2, "total_size": len(data), "chunk_size": CHUNK,
                    "sha256": sha, "path": final_path}, addr=addr)
    time.sleep_ms(250)

    off = 0
    begin_retries = 0
    while off < len(data):
        chunk = data[off:off + CHUNK]
        r = L.send_wait(0x2002, {"file_id": 2, "offset": off, "data": chunk},
                        want_cmds=(0x2004, 0x2010), addr=addr,
                        timeout_ms=2000, retries=10)
        if r is None:
            return (False, "chunk fail @%d" % off)
        if r[0] == 0x2010:
            if r[1].get('err_not_active') == 1 and begin_retries < 5:
                begin_retries += 1
                L.send(0x2001, {"file_id": 2, "total_size": len(data),
                                "chunk_size": CHUNK, "sha256": sha, "path": final_path}, addr=addr)
                time.sleep_ms(300)
                continue
            return (False, "ERR: %s" % r[1])
        off += len(chunk)
        time.sleep_ms(20)

    r = L.send_wait(0x2003, {"file_id": 2}, want_cmds=(0x2006, 0x2010),
                    addr=addr, timeout_ms=3000, retries=10)
    if r is None:
        return (False, "no END rsp")
    if r[0] == 0x2010:
        return (False, "END ERR: %s" % r[1])
    ok = r[1].get('sha256') == sha
    pending = r[1].get('pending', 0)
    return (ok, "applied %d bytes -> %s (sha=%s pending=%d)" % (
        len(data), final_path, "OK" if ok else "BAD", pending))


def promote(src_path, dst_path, slave_id=None):
    """FILE_PROMOTE (0x2011)：把 slave /sd 的 src 交換到根目錄 dst（自動 .bak 備份）。
    回 (ok, 訊息)。"""
    L = _L()
    addr = ma.ADDR_BROADCAST if slave_id is None else slave_id
    L.send(0x2011, {"src": src_path, "dst": dst_path}, addr=addr)
    r = L.recv_until([0x2006, 0x2010], 4000)
    if r is None:
        return (False, "no PROMOTE rsp")
    if r[0] == 0x2010:
        return (False, "PROMOTE ERR: %s" % r[1])
    d = r[1]
    return (True, "promoted %s -> %s (exists=%d size=%d)" % (
        src_path, dst_path, d.get('exists'), d.get('size')))


def confirm(final_path, slave_id=None):
    """確認：刪 .bak，正式生效。回 (ok, 訊息)。"""
    L = _L()
    addr = ma.ADDR_BROADCAST if slave_id is None else slave_id
    L.send(0x2008, {"path": final_path}, addr=addr)
    r = L.recv_until([0x2006], 2500)
    if r is None:
        return (False, "no CONFIRM rsp")
    return (True, "confirmed %s (pending=%d)" % (final_path, r[1].get('pending', 0)))


def undo(final_path, slave_id=None):
    """回滾：.bak 蓋回，恢復舊檔。回 (ok, 訊息)。"""
    L = _L()
    addr = ma.ADDR_BROADCAST if slave_id is None else slave_id
    L.send(0x200A, {"path": final_path}, addr=addr)
    r = L.recv_until([0x2006], 2500)
    if r is None:
        return (False, "no UNDO rsp")
    return (True, "undone %s (pending=%d)" % (final_path, r[1].get('pending', 0)))


def cleanup(path, slave_id=None):
    """刪除 slave 檔案。回 (ok, 訊息)。"""
    L = _L()
    addr = ma.ADDR_BROADCAST if slave_id is None else slave_id
    L.send(0x2009, {"path": path}, addr=addr)
    r = L.recv_until([0x2006], 2500)
    if r is None:
        return (False, "no DELETE rsp")
    return (True, "deleted %s" % path)
