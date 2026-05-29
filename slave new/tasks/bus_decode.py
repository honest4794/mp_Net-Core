import time
from lib.task import Task
from lib.sys_bus import bus


class BusDecodeTask(Task):
    def __init__(self, name, ctx):
        super().__init__(name, ctx)
        self.app = ctx["app"]
        self._buses = []
        self._parsers = {}
        self._read_buf = None

    def on_start(self):
        super().on_start()
        self._buses = []
        self._parsers = {}
        self._src_ts = 0
        buf_cfg = bus.shared.get("Buffer") or {}
        self._max_slots = int(buf_cfg.get("decode_budget_slots", 32) or 0)
        if self._max_slots <= 0:
            self._max_slots = 1

    def _refresh_sources(self):
        sources = bus.get_service("bus_sources")
        if sources:
            self._buses = list(sources.list() or [])
            return
        self._buses = []
        ctrl = bus.get_service("net_bus_ctrl")
        discv = bus.get_service("net_bus_discovery")
        if ctrl:
            self._buses.append(ctrl)
        if discv:
            self._buses.append(discv)
        circuit_list = bus.get_service("circuit_bus_list")
        if circuit_list:
            for cb in circuit_list:
                self._buses.append(cb)

    def _ensure_read_buf(self, size):
        if self._read_buf is None or len(self._read_buf) < size:
            self._read_buf = bytearray(size)

    def loop(self):
        if not self.running:
            return

        now = time.ticks_ms()
        if time.ticks_diff(now, self._src_ts) > 100:
            self._src_ts = now
            self._refresh_sources()
        if not self._buses:
            return

        used = 0
        for b in self._buses:
            hub = getattr(b, "rx_hub", None)
            if hub is None:
                continue
            self._ensure_read_buf(hub.size)
            p = self._parsers.get(id(b))
            if p is None:
                p = self.app.create_parser()
                self._parsers[id(b)] = p
            ctx_extra = getattr(b, "_decode_ctx", None) or {}
            mv = memoryview(self._read_buf)
            while True:
                if used >= self._max_slots:
                    return
                if not hub.read_into(self._read_buf):
                    break
                ln = self._read_buf[0] | (self._read_buf[1] << 8)
                if ln <= 0:
                    continue
                data = mv[2:2 + ln]
                self.app.handle_stream(
                    p,
                    data,
                    transport_name=getattr(b, "label", "Bus"),
                    send_func=b.write,
                    **ctx_extra
                )
                self.success += 1
                used += 1

    def on_stop(self):
        super().on_stop()
        self._buses = []
        self._parsers = {}
