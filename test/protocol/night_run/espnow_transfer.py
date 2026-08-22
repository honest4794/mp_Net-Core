# -*- coding: utf-8 -*-
"""espnow_transfer.py — ESP-NOW 板間傳檔測試

角色（兩塊板各跑一份）：
  SENDER   本檔跑在發送板：讀本地檔案 → 用 NowBus 走 NC4 FILE 協議(0x20xx)傳給對板
  RECEIVER 對板跑正常 slave firmware（NowBus 已是 bus source，FILE handler 已註冊），
           收到後寫 /sd，零改動。

用法（發送板 REPL）：
    import espnow_transfer
    espnow_transfer.send_file('/sd/_fw.bin', mac=None)   # mac=None → 廣播

限制：ESP-NOW 單包 ≤250B，NC4 幀 = 9B header + payload + 4B CRC → FILE_CHUNK data ≤231B。
      大檔會很慢；僅驗證「無線傳輸可行」的鏈路能力。
"""

import os
import time
import uhashlib
import ubinascii

from lib.sys.now_bus import NowBus
from lib.sys.proto import Proto, StreamParser, ADDR_BROADCAST
from lib.sys.schema_loader import SchemaStore
from lib.sys.schema_codec import SchemaCodec

CHANNEL = 6
CHUNK = 200          # FILE_CHUNK data 每包 200B（含 header/CRC 後 <250B）

_store = SchemaStore('/schema')
_store.finalize()
_cc = SchemaCodec(_store)


class ESPLink:
    def __init__(self, channel=CHANNEL):
        self.now = NowBus('ESP-TX')
        self.now.init(channel=channel)
        self.parser = StreamParser()
        self.inbox = []

    def send_frame(self, cmd, args, mac=None):
        d = _store.get(cmd)
        payload = _cc.encode(d, args)
        frame = Proto.pack(cmd, payload, addr=ADDR_BROADCAST)
        if mac is None:
            return self.now.broadcast(frame)
        return self.now.send(mac, frame)

    def poll_inbox(self, timeout_ms=2000):
        """收回應：NowBus.poll 把對板回應寫進 rx_hub，這裡讀出來解碼。"""
        t0 = time.ticks_ms()
        mv = bytearray(300)
        while time.ticks_diff(time.ticks_ms(), t0) < timeout_ms:
            self.now.poll()
            # 從 rx_hub 讀
            hub = self.now.rx_hub
            if hub is not None:
                view = hub.get_read_view()
                if view is not None:
                    n = view[0] | (view[1] << 8)
                    self.parser.feed(memoryview(view)[2:2 + n])
                    hub.commit()
                    r = self.parser.pop_frame()
                    if r is not None:
                        _v, _a, cmd, payload = r
                        d = _store.get(cmd)
                        vals = _cc.decode(d, bytes(payload), _store) if d else {}
                        return cmd, vals
            time.sleep_ms(2)
        return None


def send_file(path, mac=None, file_id=1):
    """把本機 path 用 ESP-NOW 傳給對板（走 FILE 協議，每 chunk 200B，等 ACK）。"""
    if not path.startswith('/'):
        path = '/' + path
    data = open(path, 'rb').read()
    total = len(data)
    sha = uhashlib.sha256(data).digest()
    remote = '/sd' + path   # 對板寫到 /sd 下

    L = ESPLink()
    if not L.now.connected:
        return "ESP-NOW init failed"

    # BEGIN
    L.send_frame(0x2001, {"file_id": file_id, "total_size": total, "chunk_size": CHUNK,
                          "sha256": sha, "path": remote}, mac)
    time.sleep_ms(300)

    # CHUNK loop（等 ACK）
    off = 0
    n = 0
    while off < total:
        chunk = data[off:off + CHUNK]
        L.send_frame(0x2002, {"file_id": file_id, "offset": off, "data": chunk}, mac)
        r = L.poll_inbox(3000)
        if r is None or r[0] != 0x2004:
            return "chunk fail @%d (rsp=%r)" % (off, r)
        off += len(chunk)
        n += 1
        time.sleep_ms(10)

    # END
    L.send_frame(0x2003, {"file_id": file_id}, mac)
    r = L.poll_inbox(5000)
    if r is None or r[0] not in (0x2006, 0x2010):
        return "no END rsp"
    if r[0] == 0x2010:
        return "END ERR: %r" % r[1]
    ok = r[1].get('sha256') == sha
    return "ESP-NOW 傳輸 %dB 完成 (%d chunks) sha=%s" % (total, n, "OK" if ok else "BAD")
