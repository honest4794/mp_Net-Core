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
        self._block_h = 0
        self._block_size = 0
        self._total_blocks = 0
        self._current_block = 0
        self._img_data = None    # 當前幀的 JPEG raw data
        self._pending_data = None# 下一幀已讀取但未載入（pause 時暫存）
        self._pending_tid = None # 前一個 block 的 DMA trans_id
        self._pack = None        # PackSource
        self._paths = []         # 檔案列表（folder 模式）
        self._idx = 0
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
        self._bpp = 2  # RGB565
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

        # ── 播放控制 ──
        bus.shared["jpeg_player"] = {
            "playing": True,
            "paused": False,
            "frame": 0,
            "total": 0,
            "source": "",
            "err": "",
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

    # ── 來源管理 ──────────────────────────────────────

    def _load_source_pack(self, path):
        """載入 pack 檔做為播放來源"""
        try:
            from lib.pack_source import PackSource
            self._pack = PackSource(path, loop=True)
            self._paths = []
            self._total_frames = int(self._pack.count)
            bus.shared["jpeg_player"]["total"] = self._total_frames
            bus.shared["jpeg_player"]["source"] = path
            get_log().info("📦 [JpegPlayer] Pack: {} ({} frames)".format(path, self._total_frames))
            return True
        except Exception as e:
            bus.shared["jpeg_player"]["err"] = str(e)
            return False

    def _load_source_folder(self, folder):
        """載入 JPEG 檔案資料夾做為播放來源"""
        try:
            from lib.media_source import list_jpegs
            pths = list_jpegs(folder)
            if not pths:
                bus.shared["jpeg_player"]["err"] = "no jpegs"
                return False
            self._pack = None
            self._paths = pths
            self._total_frames = len(pths)
            bus.shared["jpeg_player"]["total"] = self._total_frames
            bus.shared["jpeg_player"]["source"] = folder
            get_log().info("📁 [JpegPlayer] Folder: {} ({} files)".format(folder, self._total_frames))
            return True
        except Exception as e:
            bus.shared["jpeg_player"]["err"] = str(e)
            return False

    def _apply_source_req(self, req):
        """處理 mp4_source_req 來源切換請求"""
        source = str(req.get("source", "") or "").strip()
        if not source:
            return
        if source.endswith(".jpk") or source.endswith(".pack"):
            self._load_source_pack(source)
        else:
            self._load_source_folder(source)

    def _read_next_frame(self):
        """讀取下一幀的 JPEG raw data"""
        if self._pack is not None:
            frame_idx, n, _dt = self._pack.read_next_into(self._read_buf, self._max_jpeg)
            if frame_idx is None:
                return None
            self._frame = int(frame_idx or 0)
            return self._read_buf[:n]

        if self._paths:
            if self._idx >= len(self._paths):
                if not bus.shared.get("jpeg_loop", True):
                    return None
                self._idx = 0
            path = self._paths[self._idx]
            try:
                with open(path, "rb") as f:
                    data = f.read()
                self._frame = self._idx
                self._idx += 1
                return data
            except Exception:
                self._idx += 1
                return None

        return None

    def _alloc_read_buf(self, size):
        self._max_jpeg = int(size or 65536)
        try:
            import heap_caps
            buf = heap_caps.malloc(self._max_jpeg, heap_caps.CAP_SPIRAM)
            if buf is not None:
                self._read_buf = buf
                return
        except Exception:
            pass
        self._read_buf = bytearray(self._max_jpeg)

    def _load_first_frame(self):
        """載入第一幀，初始化解碼資訊"""
        self._alloc_read_buf(65536)
        data = self._read_next_frame()
        if data is None:
            return False
        return self._load_frame(data)

    def _load_frame(self, data):
        """載入一幀 JPEG data 到解碼器"""
        try:
            info = self._decoder.get_img_info(data)
            w, h = info[0], info[1]
            if len(info) >= 4:
                self._total_blocks = int(info[2])
                self._block_h = int(info[3])
            else:
                self._total_blocks = 1
                self._block_h = h
            self._block_size = w * self._block_h * self._bpp
            self._img_data = data
            self._current_block = 0
            self._pending_tid = None
            bus.shared["jpeg_player"]["frame"] = self._frame
            return True
        except Exception as e:
            bus.shared["jpeg_player"]["err"] = str(e)
            return False

    # ── DMA 寫入 ──────────────────────────────────────

    def _dma_fire(self, chunk):
        """async DMA：fire 一個 block 的 pixel data，回傳最後的 trans_id"""
        bus_obj = self._bus
        mv = memoryview(chunk) if isinstance(chunk, (bytearray, bytes)) else chunk
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
            self._load_first_frame()

        # ── pace_ms 節奏控制 ──
        pace_ms = int(bus.shared.get("jpeg_player", {}).get("pace_ms", 0) or 0)
        if pace_ms > 0 and self._last_frame_ms:
            now = time.ticks_ms()
            if time.ticks_diff(now, self._last_frame_ms) < pace_ms:
                return

        # ── 播放控制（只在幀邊界生效）──
        player = bus.shared.get("jpeg_player", {})
        if not player.get("playing", True):
            return

        # 初次載入或從暫停恢復
        if self._img_data is None:
            if self._pending_data is not None:
                # 暫停時讀好的下一幀，直接載入
                if self._load_frame(self._pending_data):
                    self._pending_data = None
                else:
                    return
            else:
                if not self._load_first_frame():
                    return

        # ── Decode 一個 block ──
        try:
            done = self._decoder.decode_into(self._img_data, self._fb, blocks=1)
        except Exception as e:
            bus.shared["jpeg_player"]["err"] = str(e)
            # 嘗試換下一幀
            self._img_data = None
            return

        # ── 寫入 LCD ──
        y0 = self._current_block * self._block_h

        # 先設 window（LCD 命令，阻塞但資料量極小）
        self.lcd.set_window(0, y0, self._w - 1, y0 + self._block_h - 1)

        # 準備 chunk
        block_start = y0 * self._w * self._bpp
        block_len = self._block_h * self._w * self._bpp
        chunk = memoryview(self._fb)[block_start:block_start + block_len]

        # 等上一 block 的 DMA 完成（防止覆蓋）
        if self._pending_tid is not None:
            self._bus.wait(self._pending_tid)

        # Fire DMA
        self._pending_tid = self._dma_fire(chunk)

        self._current_block += 1

        # ── 整幀完成（幀邊界，在此檢查暫停/停止）──
        if done or self._current_block >= self._total_blocks:
            # 等最後的 DMA
            if self._pending_tid is not None:
                self._bus.wait(self._pending_tid)
                self._pending_tid = None
            self._bus.flush()

            # 統計
            self._fps_count += 1
            now = time.ticks_ms()
            if self._fps_t0 == 0:
                self._fps_t0 = now
                self._frame_t0 = now
            else:
                dt = time.ticks_diff(now, self._fps_t0)
                if dt >= 1000:
                    self._lw_ex(0, self._fps_count)
                    self._fps_t0 = now
                    self._fps_count = 0

            self._last_frame_ms = time.ticks_ms()

            # 先在幀邊界檢查暫停（不跳過幀）
            player = bus.shared.get("jpeg_player", {})
            if player.get("paused", False):
                # 停在當前幀，讀取下一幀但不載入
                data = self._read_next_frame()
                if data is not None:
                    self._pending_data = data
                self._img_data = None
                return

            # 載入下一幀
            data = self._read_next_frame()
            if data is None:
                bus.shared["jpeg_player"]["playing"] = False
                self._img_data = None
                bus.shared["jpeg_player"]["frame"] = self._frame
            else:
                self._load_frame(data)

    def on_stop(self):
        super().on_stop()
        if self._fb is not None:
            try:
                import heap_caps
                heap_caps.free(self._fb)
            except Exception:
                pass
            self._fb = None
        if self._read_buf is not None:
            try:
                import heap_caps
                heap_caps.free(self._read_buf)
            except Exception:
                pass
            self._read_buf = None
        if self._pack is not None:
            try:
                self._pack.close()
            except Exception:
                pass
            self._pack = None
