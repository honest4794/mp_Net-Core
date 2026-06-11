# jpeg_player_task.py
# JPEG 播放器 — decode_into(blocks=1) + 立即 async DMA 寫 LCD
#
# Pipeline（單 framebuffer，不同 offset 平行）：
#   decode_into(block N) → 寫入 fb[block_N_區域]
#                               ‖ (平行)
#   DMA 正在讀取 fb[block_N-1_區域] 發送到 LCD
#
# 無中間 hub、無 bounce copy、零 GC 分配

import time
from lib.task import Task
from lib.sys_bus import bus
from lib.log_service import get_log

_SEND_CHUNK = 32 * 1024


class JpegPlayerTask(Task):
    log_schema = ["fps", "block", "frame"]

    def __init__(self, name, ctx):
        super().__init__(name, ctx)
        self.lcd = None
        self._bus = None
        self._decoder = None
        self._fb = None
        self._fb_size = 0
        self._bpp = 2
        self._w = 0
        self._h = 0
        self._pending_tid = None
        self._source = None
        self._total_frames = 0
        self._frame = 0

        self._fps_count = 0
        self._fps_t0 = 0
        self._frame_t0 = 0
        self._last_frame_ms = 0
        self._test_first = True    # 測試模式首幀標記
        self._test_chunk = None   # 測試模式 row buffer（w*bpp bytes，只分配一次）

    def on_start(self):
        super().on_start()

        self.lcd = bus.get_service("lcd") or bus.get_service("tft")
        if self.lcd is None:
            get_log().error("❌ [JpegPlayer] LCD not found")
            return
        self._bus = getattr(self.lcd, "_bus", None)
        if self._bus is None:
            get_log().error("❌ [JpegPlayer] bus adapter not found")
            return

        # 直接從 lcd 物件讀取真實解析度（最可靠）
        self._w = getattr(self.lcd, "width", 240)
        self._h = getattr(self.lcd, "height", 320)
        sys_cfg = bus.shared.get("System", {})
        self._bpp = int(sys_cfg.get("player_bpp", 2))
        self._fb_size = self._w * self._h * self._bpp

        fb = self._alloc_fb(self._fb_size)
        if fb is None:
            get_log().error("❌ [JpegPlayer] framebuffer alloc failed")
            return
        self._fb = fb
        get_log().info("🖼 [JpegPlayer] {}x{} fb={} KB".format(
            self._w, self._h, self._fb_size // 1024))

        try:
            import jpeg
            fmt = str(sys_cfg.get("player_pixel_format", "RGB565_BE"))
            self._decoder = jpeg.Decoder(
                pixel_format=fmt,
                rotation=0,
                block=True,
                return_bytes=False,
            )
        except Exception as e:
            get_log().info("⚠ [JpegPlayer] no jpeg module — test pattern only: {}".format(e))

        old = bus.shared.get("jpeg_player") or {}
        bus.shared["jpeg_player"] = {
            "playing": True,
            "paused": False,
            "frame": 0,
            "total": 0,
            "source": "",
            "fps": 0,
            "err": "",
            "pace_ms": int(old.get("pace_ms", 33)),
        }

    def _alloc_fb(self, size):
        try:
            import heap_caps
            buf = heap_caps.malloc(size, heap_caps.CAP_SPIRAM)
            if buf is not None:
                return buf
        except Exception:
            pass
        try:
            import heap_caps
            buf = heap_caps.malloc(size, heap_caps.CAP_DMA)
            if buf is not None:
                return buf
        except Exception:
            pass
        return bytearray(size)

    def _apply_source_req(self, req):
        source = str(req.get("source", "") or "").strip()
        if not source:
            return
        if self._source is not None:
            try:
                self._source.close()
            except Exception:
                pass
            self._source = None
        try:
            from lib import media_source
            loop = bool(bus.shared.get("jpeg_loop", True))
            self._source = media_source.open_source(
                source, decoder=self._decoder, bpp=self._bpp, loop=loop,
                frame_size=req.get("frame_size"),
                width=int(req.get("width", self._w) or self._w),
                height=int(req.get("height", self._h) or self._h),
                max_jpeg=req.get("max_jpeg"),
            )
            self._total_frames = int(self._source.count)
            bus.shared["jpeg_player"]["total"] = self._total_frames
            bus.shared["jpeg_player"]["source"] = source
            start = int(req.get("start_frame", 0) or 0)
            if start > 0 and hasattr(self._source, "read_frame_into"):
                try:
                    self._source.read_frame_into(self._fb, start)
                    self._frame = start
                    bus.shared["jpeg_player"]["frame"] = start
                except Exception:
                    pass
            kind = "bin" if self._source.is_raw else "jpeg"
            get_log().info("🎬 [JpegPlayer] {} source: {} ({} frames)".format(
                kind, source, self._total_frames))
        except Exception as e:
            bus.shared["jpeg_player"]["err"] = str(e)
            self._source = None

    def _test_pattern_direct(self, frame):
        """填 framebuffer → show_frame() 整幀 DMA（write_frame 內部 chunk + CS/DC）"""
        bands = [
            [0xF800, 0x07E0, 0x001F, 0x07FF, 0xF81F, 0xFFE0, 0xFFFF, 0x0000],
            [0xFFFF, 0x0000, 0xF800, 0x07E0, 0x001F, 0xFFE0, 0x07FF, 0xF81F],
            [0x0000, 0xFFFF, 0xF81F, 0x07FF, 0xFFE0, 0x001F, 0x07E0, 0xF800],
            [0x07E0, 0xF800, 0xFFE0, 0x001F, 0xFFFF, 0x07FF, 0x0000, 0xF81F],
        ]
        bars = bands[frame % len(bands)]
        n_bars = len(bars)
        bar_w = max(1, self._w // n_bars)
        bpp = self._bpp

        # 預建 row buffer（只分配一次）
        if self._test_chunk is None:
            self._test_chunk = bytearray(self._w * bpp)
        row_buf = self._test_chunk
        row_mv = memoryview(row_buf)

        for bar_i, color in enumerate(bars):
            x0 = bar_i * bar_w
            x1 = min(x0 + bar_w, self._w)
            hi = (color >> 8) & 0xFF
            lo = color & 0xFF
            for x in range(x0, x1):
                off = x * bpp
                row_buf[off] = hi
                row_buf[off + 1] = lo

        fb_mv = memoryview(self._fb)
        row_bytes = self._w * bpp
        for row in range(self._h):
            off = row * row_bytes
            fb_mv[off:off + row_bytes] = row_mv

        self.lcd.set_window(0, 0, self._w - 1, self._h - 1)
        self.lcd.show_frame(fb_mv[:self._fb_size])

    def _fill_next_frame(self):
        if self._source is None:
            return False
        try:
            idx, n = self._source.read_into(self._fb)
        except Exception as e:
            bus.shared["jpeg_player"]["err"] = str(e)
            return False
        if idx is None or not n:
            return False
        self._frame = int(idx)
        bus.shared["jpeg_player"]["frame"] = self._frame
        return True

    def _dma_fire(self, mv):
        """逐 chunk 寫入 + wait，確保每段 DMA 完成再送下一段"""
        bus_obj = self._bus
        off, rem = 0, len(mv)
        while rem > 0:
            n = min(rem, _SEND_CHUNK)
            tid = bus_obj.write_data_async(mv[off:off + n])
            if tid is not None:
                bus_obj.wait(tid)
            off += n
            rem -= n

    # ── 主迴圈 ────────────────────────────────────────

    def loop(self):
        if not self.running:
            return
        if self.lcd is None or self._bus is None:
            return

        # ── 測試模式：色條直出（繞過 media source + framebuffer，直接 chunk DMA）──
        if bus.shared.get("jpeg_test_pattern"):
            self._test_pattern_direct(self._fps_count)

            self._fps_count += 1
            now = time.ticks_ms()

            if self._test_first:
                self._test_first = False
                print("[JpegPlayer] test w={} h={} bpp={} fb={}B".format(
                    self._w, self._h, self._bpp, self._fb_size))
                self._fps_t0 = now
            else:
                dt = time.ticks_diff(now, self._fps_t0)
                if dt >= 1000:
                    fps = self._fps_count * 1000 // dt
                    print("[JpegPlayer] fps={} frame={}".format(fps, self._fps_count))
                    self._fps_t0 = now
                    self._fps_count = 0

            self._last_frame_ms = now
            return

        # ── 正常播放：需要 decoder + source ──
        if self._decoder is None:
            return

        req = bus.shared.pop("jpeg_source_req", None)
        if req is not None:
            self._apply_source_req(req)

        if self._source is None:
            return

        pace_ms = int(bus.shared.get("jpeg_player", {}).get("pace_ms", 0) or 0)
        if pace_ms > 0 and self._last_frame_ms:
            now = time.ticks_ms()
            if time.ticks_diff(now, self._last_frame_ms) < pace_ms:
                return

        player = bus.shared.get("jpeg_player", {})
        if not player.get("playing", True):
            return
        if player.get("paused", False):
            return

        if not self._fill_next_frame():
            bus.shared["jpeg_player"]["playing"] = False
            return

        self.lcd.set_window(0, 0, self._w - 1, self._h - 1)
        self.lcd.show_frame(memoryview(self._fb)[:self._fb_size])

        self._fps_count += 1
        now = time.ticks_ms()
        if self._fps_t0 == 0:
            self._fps_t0 = now
            self._frame_t0 = now
        else:
            dt = time.ticks_diff(now, self._fps_t0)
            if dt >= 1000:
                fps = self._fps_count * 1000 // dt
                bus.shared["jpeg_player"]["fps"] = fps
                if bus.shared.get("verbose_print"):
                    print("[JpegPlayer] fps={} frame={}".format(fps, self._frame))
                else:
                    self._lw_ex(0, self._fps_count)
                self._fps_t0 = now
                self._fps_count = 0

        self._last_frame_ms = time.ticks_ms()

    def on_stop(self):
        super().on_stop()
        if self._fb is not None:
            try:
                import heap_caps
                heap_caps.free(self._fb)
            except Exception:
                pass
            self._fb = None
        if self._source is not None:
            try:
                self._source.close()
            except Exception:
                pass
            self._source = None
