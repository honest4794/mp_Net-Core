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
        self._fb = None          # 全幀 framebuffer
        self._fb_size = 0
        self._bpp = 2            # bytes per pixel (RGB565)
        self._w = 0
        self._h = 0
        self._pending_tid = None # DMA trans_id
        self._source = None      # 統一媒體來源（folder/jpk/bin）
        self._total_frames = 0
        self._frame = 0

        # 統計
        self._fps_count = 0
        self._fps_t0 = 0
        self._frame_t0 = 0
        self._last_frame_ms = 0    # pace_ms 節奏控制

    def on_start(self):
        super().on_start()

        # ── LCD ──
        self.lcd = bus.get_service("lcd") or bus.get_service("tft")
        if self.lcd is None:
            get_log().error("❌ [JpegPlayer] LCD not found")
            return
        self._bus = getattr(self.lcd, "_bus", None)
        if self._bus is None:
            get_log().error("❌ [JpegPlayer] bus adapter not found")
            return

        sys_cfg = bus.shared.get("System", {})
        self._w = int(sys_cfg.get("player_width", bus.shared.get("tft_width", 240)))
        self._h = int(sys_cfg.get("player_height", bus.shared.get("tft_height", 320)))

        # ── Framebuffer（PSRAM 優先）──
        self._bpp = int(bus.shared.get("System", {}).get("player_bpp", 2))
        self._fb_size = self._w * self._h * self._bpp
        fb = self._alloc_fb(self._fb_size)
        if fb is None:
            get_log().error("❌ [JpegPlayer] framebuffer alloc failed")
            return
        self._fb = fb
        get_log().info("🖼 [JpegPlayer] {}x{} fb={} KB".format(
            self._w, self._h, self._fb_size // 1024))

        # ── Decoder ──
        try:
            import jpeg
            fmt = str(sys_cfg.get("player_pixel_format", "RGB565_LE"))
            self._decoder = jpeg.Decoder(
                pixel_format=fmt,
                rotation=0,
                block=True,
                return_bytes=False,
            )
        except Exception as e:
            get_log().error("❌ [JpegPlayer] Decoder init: {}".format(e))
            return

        # ── 播放控制（保留 boot 預設的 pace_ms）──
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

    # ── 來源管理（統一 media_source）──────────────────

    def _apply_source_req(self, req):
        """處理來源切換請求，建立統一 MediaSource（folder/jpk/bin 自動判斷）"""
        source = str(req.get("source", "") or "").strip()
        if not source:
            return
        # 關閉舊來源
        if self._source is not None:
            try:
                self._source.close()
            except Exception:
                pass
            self._source = None
        try:
            from lib import media_source
            loop = bool(bus.shared.get("jpeg_loop", True))
            # bin 模式參數（可由請求覆寫，預設用 player 尺寸）
            self._source = media_source.open_source(
                source,
                decoder=self._decoder,
                bpp=self._bpp,
                loop=loop,
                frame_size=req.get("frame_size"),
                width=int(req.get("width", self._w) or self._w),
                height=int(req.get("height", self._h) or self._h),
                max_jpeg=req.get("max_jpeg"),
            )
            self._total_frames = int(self._source.count)
            bus.shared["jpeg_player"]["total"] = self._total_frames
            bus.shared["jpeg_player"]["source"] = source
            # 起始幀（seek）：bin 隨機存取，其他來源忽略
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

    def _fill_next_frame(self):
        """把下一幀填入 fb（jpeg 整幀解碼 / bin 直接拷貝）。成功回 True。"""
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

    # ── DMA 寫入 ──────────────────────────────────────

    def _dma_fire(self, mv):
        """async DMA：分段送整幀 pixel data，回傳最後的 trans_id"""
        bus_obj = self._bus
        off, rem = 0, len(mv)
        last_tid = None
        while rem > 0:
            n = min(rem, _SEND_CHUNK)
            tid = bus_obj.write_data_async(mv[off:off + n])
            if tid is not None:
                last_tid = tid
            off += n
            rem -= n
        return last_tid

    # ── 主迴圈 ────────────────────────────────────────

    def loop(self):
        if not self.running:
            return
        if self.lcd is None or self._bus is None or self._decoder is None:
            return

        # ── 來源切換 ──
        req = bus.shared.pop("jpeg_source_req", None)
        if req is not None:
            self._apply_source_req(req)

        if self._source is None:
            return

        # ── pace_ms 節奏控制 ──
        pace_ms = int(bus.shared.get("jpeg_player", {}).get("pace_ms", 0) or 0)
        if pace_ms > 0 and self._last_frame_ms:
            now = time.ticks_ms()
            if time.ticks_diff(now, self._last_frame_ms) < pace_ms:
                return

        # ── 播放控制（幀邊界生效）──
        player = bus.shared.get("jpeg_player", {})
        if not player.get("playing", True):
            return
        if player.get("paused", False):
            return

        # ── 取下一幀填入 fb（jpeg 整幀解碼 / bin 直接拷貝）──
        if not self._fill_next_frame():
            bus.shared["jpeg_player"]["playing"] = False
            return

        # ── 整幀寫入 LCD ──
        self.lcd.set_window(0, 0, self._w - 1, self._h - 1)
        mv = memoryview(self._fb)[:self._fb_size]

        if self._pending_tid is not None:
            self._bus.wait(self._pending_tid)
        self._pending_tid = self._dma_fire(mv)
        if self._pending_tid is not None:
            self._bus.wait(self._pending_tid)
            self._pending_tid = None
        self._bus.flush()

        # ── 統計 ──
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
