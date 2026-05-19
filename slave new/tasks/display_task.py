import time

from lib.task import Task
from lib.sys_bus import bus
from lib.dp_buffer_service import HDR_OUT, ensure_dp_buffer_service, unpack_out_header_into
from lib.buffer_hub import DmaBounceBuf

_SPI_TX_BUF_SIZE = 32 * 1024


class DisplayTask(Task):
    log_schema = ["fps_window", "fps_total", "disp_src_fill"]

    def on_start(self):
        super().on_start()
        self._buf = ensure_dp_buffer_service(bus)
        self._lcd = None
        self._out_hdr = [0] * 9
        self._last_x = -1
        self._last_y = -1
        self._last_w = -1
        self._last_h = -1
        self._last_write_ms = 0

        self._spi_tx = DmaBounceBuf(_SPI_TX_BUF_SIZE)
        self._spi_pool = None
        self._spi_pool_buf = None
        self._spi_pool_free = None
        self._spi_inflight = []

        self._fps_window_t0 = 0
        self._fps_window_count = 0
        self._fps_start_ms = 0
        self._fps_total_frames = 0

    def _resolve_lcd(self):
        if self._lcd is not None:
            return self._lcd
        lcd = bus.get_service("lcd")
        if lcd is None:
            lcd = bus.get_service("tft")
        self._lcd = lcd
        return lcd

    def _tick_fps(self):
        self._fps_window_count += 1
        self._fps_total_frames += 1

        now = time.ticks_ms()
        if self._fps_start_ms == 0 and self._fps_total_frames > 0:
            self._fps_start_ms = now

        if self._fps_window_t0 == 0:
            self._fps_window_t0 = now
            return

        dt = time.ticks_diff(now, self._fps_window_t0)
        interval = int(self.fcache_get("fps_stats_interval", 1000, ttl_ms=3000) or 1000)
        if dt < interval:
            return

        fps_window = self._fps_window_count
        self._lw_ex(0, fps_window)

        if self._fps_start_ms > 0:
            total_elapsed = time.ticks_diff(now, self._fps_start_ms)
            if total_elapsed > 0:
                fps_cumulative = self._fps_total_frames * 1000 // total_elapsed
                self._lw_ex(1, fps_cumulative)
            else:
                self._lw_ex(1, 0)
        else:
            self._lw_ex(1, 0)

        self._fps_window_t0 = now
        self._fps_window_count = 0

    def loop(self):
        if not self.running:
            return

        pace_ms = 0
        try:
            sys_cfg = bus.shared.get("System") if hasattr(bus, "shared") else None
            if isinstance(sys_cfg, dict):
                pace_ms = int(sys_cfg.get("pace_ms", 0) or 0)
        except Exception:
            pace_ms = 0
        if pace_ms > 0 and self._last_write_ms:
            now = time.ticks_ms()
            if time.ticks_diff(now, self._last_write_ms) < pace_ms:
                return

        lcd = self._resolve_lcd()
        if lcd is None:
            return
        spi = getattr(lcd, "spi", None)
        use_spi_queue = spi is not None and hasattr(spi, "pending") and hasattr(spi, "is_busy") and hasattr(spi, "wait_all")
        if use_spi_queue and self._spi_pool is None:
            depth = int(self.fcache_get("spi_queue_depth", 4, ttl_ms=3000) or 4)
            if depth < 2:
                depth = 2
            if depth > 8:
                depth = 8
            self._spi_pool = [DmaBounceBuf(_SPI_TX_BUF_SIZE) for _ in range(depth)]
            self._spi_pool_buf = []
            self._spi_pool_free = [True] * depth
            for b in self._spi_pool:
                mv = b.get()
                if mv is None:
                    mv = bytearray(_SPI_TX_BUF_SIZE)
                self._spi_pool_buf.append(mv)

        if (not use_spi_queue) and bus.shared.get("spi_busy"):
            return

        self._buf = bus.get_service("dp_buffer") or self._buf
        if not self._buf or not self._buf.get("enable", True):
            return

        use_jpeg_out = bool(self._buf.get("bypass_copy")) or str(self._buf.get("pixel_format") or "").startswith("RGB888")
#         hub = self._buf.get("jpeg_out") if use_jpeg_out else self._buf.get("out_hub")
        hub = self._buf.get("jpeg_out")
        if hub is None:
            return
        try:
            self._lw_ex(2, int(hub.get_fill_level() or 0) + 1)
        except Exception:
            pass

        rv = hub.get_read_view()
        if rv is None:
            return

        try:
            unpack_out_header_into(rv, self._out_hdr)
            payload_len = int(self._out_hdr[0])
            if payload_len <= 0:
                return
            x = int(self._out_hdr[3])
            y = int(self._out_hdr[4])
            w = int(self._out_hdr[5])
            h = int(self._out_hdr[6])
            payload = rv[HDR_OUT : HDR_OUT + payload_len]

            try:
                if use_spi_queue:
                    try:
                        pending = int(spi.pending() or 0)
                    except Exception:
                        pending = 0
                    done = len(self._spi_inflight) - pending
                    if done > 0:
                        for _ in range(done):
                            idx = self._spi_inflight.pop(0)
                            if self._spi_pool_free is not None:
                                self._spi_pool_free[idx] = True

                if x != self._last_x or y != self._last_y or w != self._last_w or h != self._last_h:
                    if use_spi_queue:
                        try:
                            spi.wait_all()
                        except Exception:
                            pass
                        self._spi_inflight = []
                        if self._spi_pool_free is not None:
                            for i in range(len(self._spi_pool_free)):
                                self._spi_pool_free[i] = True
                    try:
                        lcd.set_window(x, y, x + w - 1, y + h - 1)
                    except Exception:
                        try:
                            lcd.set_window(x, y)
                        except Exception:
                            pass
                    self._last_x = x
                    self._last_y = y
                    self._last_w = w
                    self._last_h = h

                if use_spi_queue and self._spi_pool_free is not None:
                    pending = 0
                    try:
                        pending = int(spi.pending() or 0)
                    except Exception:
                        pending = 0
                    if pending >= len(self._spi_pool_free):
                        return
                    if payload_len > _SPI_TX_BUF_SIZE:
                        try:
                            spi.wait_all()
                        except Exception:
                            pass
                        lcd.write_data(payload)
                        try:
                            spi.wait_all()
                        except Exception:
                            pass
                        return
                    idx = -1
                    for i, free in enumerate(self._spi_pool_free):
                        if free:
                            idx = i
                            break
                    if idx < 0:
                        return
                    buf = self._spi_pool_buf[idx]
                    buf[:payload_len] = payload[:payload_len]
                    tid = lcd.write_data(memoryview(buf)[:payload_len])
                    self._spi_pool_free[idx] = False
                    self._spi_inflight.append(idx)
                    if isinstance(tid, int):
                        pass
                else:
                    tx_payload = self._spi_tx.prep_for_spi(payload, payload_len)
                    lcd.write_data(tx_payload)
            finally:
                pass

            self._last_write_ms = time.ticks_ms()

            self._buf["last_ms"] = time.ticks_ms()
            self._buf["last_err"] = ""
            self.success += 1
            self._tick_fps()
        except Exception as e:
            try:
                bus.shared["spi_busy"] = False
            except Exception:
                pass
            try:
                self._buf["last_err"] = str(e)
                self._buf["last_ms"] = time.ticks_ms()
            except Exception:
                pass
            self._lcd = None
        finally:
            try:
                hub.release_read()
            except Exception:
                pass

    def on_stop(self):
        super().on_stop()
        self._spi_tx.close()
        if self._spi_pool:
            for b in self._spi_pool:
                try:
                    b.close()
                except Exception:
                    pass
        self._spi_pool = None
        self._spi_pool_buf = None
        self._spi_pool_free = None
        self._spi_inflight = []
