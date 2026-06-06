import time

from lib.task import Task
from lib.sys_bus import bus
from lib.log_service import get_log
from lib.dp_buffer_service import HDR_OUT, ensure_dp_buffer_service


def _try_heap_caps(size):
    """嘗試從 heap_caps 分配 DMA 或 PSRAM 緩衝"""
    try:
        import heap_caps
        buf = heap_caps.malloc(size, heap_caps.CAP_DMA)
        if buf is not None:
            return buf, "DMA"
        buf = heap_caps.malloc(size, heap_caps.CAP_SPIRAM)
        if buf is not None:
            return buf, "PSRAM"
    except Exception:
        pass
    return None, None


class DpBufferTask(Task):
    def on_start(self):
        super().on_start()
        self._svc = ensure_dp_buffer_service(bus)
        self._disabled = False
        self._copy_buf = None
        self._buf_tag = ""

        pf = str(self._svc.get("pixel_format") or "")
        if pf.startswith("RGB888"):
            tm = bus.get_service("task_manager")
            if tm:
                tm.set_affinity("dp_buffer", (0, 0))
            self._disabled = True
            return

        max_fb = int(self._svc.get("max_frame_bytes", 0) or 0)
        if max_fb > 0:
            buf, tag = _try_heap_caps(HDR_OUT + max_fb)
            if buf is not None:
                self._copy_buf = buf
                self._buf_tag = tag
        get_log().info("🔄 [DpBuffer] buf={} tag={}".format(
            max_fb, self._buf_tag or "gc"))

    def loop(self):
        if not self.running:
            return

        self._svc = bus.get_service("dp_buffer") or self._svc
        if not self._svc or not self._svc.get("enable", True):
            return
        pf = str(self._svc.get("pixel_format") or "")
        if pf.startswith("RGB888"):
            if not self._disabled:
                tm = bus.get_service("task_manager")
                if tm:
                    tm.set_affinity("dp_buffer", (0, 0))
                self._disabled = True
            return

        jpeg_out = self._svc.get("jpeg_out")
        if jpeg_out is None:
            return

        out_hub = self._svc.get("out_hub")
        if out_hub is None:
            return

        # 用 heap_caps buffer 或備用 bytearray
        fb_size = int(self._svc.get("max_frame_bytes", 0) or 0)
        need_size = HDR_OUT + fb_size
        if self._copy_buf is not None:
            buf = self._copy_buf
            if len(buf) < need_size:
                buf = bytearray(need_size)
        else:
            buf = bytearray(need_size)

        if not jpeg_out.read_into(buf):
            return

        wv = out_hub.get_write_view()
        if wv is None:
            return
        if int(len(wv)) < len(buf):
            self._svc["last_err"] = "out buffer too small"
            self._svc["last_ms"] = time.ticks_ms()
            return

        copy_len = min(len(buf), int(len(wv)))
        out_hub.bounce_into(wv, buf, copy_len)
        out_hub.commit()

        self._svc["frames"] = int(self._svc.get("frames", 0) or 0) + 1
        self._svc["last_done"] = {"ms": time.ticks_ms()}
        self._svc["last_err"] = ""
        self._svc["last_ms"] = time.ticks_ms()

        self.success += 1

    def on_stop(self):
        super().on_stop()
        if self._copy_buf is not None:
            try:
                import heap_caps
                heap_caps.free(self._copy_buf)
                self._copy_buf = None
            except Exception:
                pass
