"""WebMaster 設備連線管理。

每個 slave 透過 WS 連入 /ws/{slave_id}, 本模組持有該連線並提供:
  - send(cmd, args): 單向發送 (廣播/串流控制, 不等回應)
  - request(cmd, args, expect, timeout): 發送 + 等待指定回應命令 (含超時)
  - 心跳餵狗 / 離線偵測
  - 0x1102 狀態快取 + 0x1101 主動查詢

回應匹配採 per-device 的 asyncio.Future dict, 依「期待的回應命令 id」路由。
注意: NC4 的 Proto.pack 回傳共享 memoryview, 本模組一律立刻 bytes() 拷貝再 await 送出。
"""
import asyncio
import time
import logging

from protocol import protocol, StreamParser

log = logging.getLogger("webmaster.device")


class Device:
    def __init__(self, slave_id, ws, addr=None):
        self.slave_id = slave_id
        self.ws = ws
        self.addr = addr
        self.connected_at = time.time()
        self.last_seen = time.time()
        self.parser = StreamParser()
        self.status = {}           # 最近一次 0x1102 狀態 dict
        self._pending = {}         # expect_cmd_id -> asyncio.Future
        self._lock = asyncio.Lock()

    # ── 發送 ──────────────────────────────────────────────
    async def send(self, cmd_id, args):
        """單向發送 (不回傳回應)。立即 bytes() 拷貝, 避免共享 buffer 被下一次 pack 覆蓋。"""
        data = bytes(protocol.pack(cmd_id, args))
        await self.ws.send_bytes(data)

    async def request(self, cmd_id, args, expect, timeout=5.0):
        """發送 cmd_id, 等待 expect 回應命令; 回傳 (expect_cmd_id, args_dict) 或 None (超時)。"""
        fut = asyncio.get_event_loop().create_future()
        async with self._lock:
            self._pending[expect] = fut
            await self.send(cmd_id, args)
        try:
            return await asyncio.wait_for(fut, timeout)
        except asyncio.TimeoutError:
            return None
        finally:
            self._pending.pop(expect, None)

    # ── 收到一幀 ──────────────────────────────────────────
    async def feed_bytes(self, data: bytes):
        self.parser.feed(data)
        while True:
            r = self.parser.pop_frame()
            if r is None:
                break
            ver, addr, cmd, payload = r
            self.last_seen = time.time()
            await self._dispatch(cmd, bytes(payload))

    async def _dispatch(self, cmd, payload):
        args = protocol.unpack(cmd, payload)
        if args is None:
            return
        name = protocol.name(cmd)
        # 1. 狀態心跳 0x1102 → 快取
        if cmd == 0x1102:
            import json
            try:
                self.status = json.loads(args.get("status_json", "{}"))
            except Exception:
                self.status = args
        # 2. 滿足等待中的 future
        fut = self._pending.get(cmd)
        if fut is not None and not fut.done():
            fut.set_result((cmd, args))
        log.debug("[%s] rx 0x%04X %s", self.slave_id, cmd, name)

    # ── 狀態查詢 ──────────────────────────────────────────
    async def query_status(self, timeout=2.0):
        r = await self.request(0x1101, {"query_type": 0}, expect=0x1102, timeout=timeout)
        return self.status if r is not None else None


class DeviceManager:
    def __init__(self):
        self.devices = {}          # slave_id -> Device
        self.ui_clients = set()    # 瀏覽器 WS (WebSocket 物件)

    # ── 註冊/移除 ─────────────────────────────────────────
    def register(self, slave_id, ws, addr=None):
        dev = Device(slave_id, ws, addr)
        self.devices[slave_id] = dev
        log.info("slave 上線: %s", slave_id)
        return dev

    def unregister(self, slave_id):
        dev = self.devices.pop(slave_id, None)
        if dev:
            log.info("slave 離線: %s", slave_id)

    def get(self, slave_id):
        return self.devices.get(slave_id)

    def list_devices(self):
        now = time.time()
        return [
            {
                "slave_id": sid,
                "addr": d.addr,
                "online": True,
                "uptime_s": int(now - d.connected_at),
                "status": d.status,
            }
            for sid, d in sorted(self.devices.items())
        ]

    # ── 瀏覽器 UI 廣播 ────────────────────────────────────
    async def broadcast_ui(self, message: dict):
        import json
        dead = []
        for ws in list(self.ui_clients):
            try:
                await ws.send_text(json.dumps(message, ensure_ascii=False))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.ui_clients.discard(ws)

    # ── 心跳 / 離線偵測 (背景迴圈) ────────────────────────
    async def heartbeat_loop(self, interval=5.0, offline_after=30.0):
        while True:
            await asyncio.sleep(interval)
            now = time.time()
            for sid, d in list(self.devices.items()):
                if now - d.last_seen > offline_after:
                    log.warning("slave %s 心跳逾時, 標記離線", sid)
                    self.unregister(sid)
            await self.broadcast_ui({"type": "device_list", "data": self.list_devices()})


manager = DeviceManager()
