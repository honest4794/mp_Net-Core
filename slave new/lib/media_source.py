# media_source.py
# 統一媒體來源抽象 — 一個 read_into(fb) 介面，吐出「可立即 DMA 的像素資料」
#
# 三種模式（依輸入路徑自動判斷）：
#   folder : 資料夾內多個 JPEG 檔，逐檔整幀解碼（decode_into blocks=0）
#   jpk    : 單一 JPK1 打包檔（變長 JPEG frame），整幀解碼
#   bin    : 單一定長 raw 像素檔（RGB565/RGB888，無需解碼，直接拷貝）
#
# 設計重點（依使用者決策）：
#   1. 解碼器放進來：folder/jpk 內部 decode_into，最終都得到同一種可立即使用的輸出
#   2. blocks=0（整幀解碼），避免 Python 層逐 block for 迴圈吃資源
#   3. 模式自動判斷：資料夾→folder；檔案看副檔名（.jpk/.pack→jpk，.bin/.raw→bin）
#   4. bin 每幀大小由外部直接傳入（frame_size 或 width*height*bpp），相容 RGB565/RGB888
#
# 統一介面：
#   src.read_into(fb)  -> (frame_idx, nbytes) 或 (None, 0) 代表結束
#   src.reset()        -> 回到第一幀
#   src.count          -> 總幀數（0 表示未知）
#   src.close()

import os


# ── 工具函數（沿用，folder 掃描 / buffer 估算）─────────────────


def list_jpegs(folder_path):
    """列出資料夾內所有 jpeg/jpg，排序後回傳完整路徑列表"""
    files = [
        f
        for f in os.listdir(folder_path)
        if f.lower().endswith(".jpeg") or f.lower().endswith(".jpg")
    ]
    files.sort()
    return [folder_path + "/" + f for f in files]


def compute_max_file_size(paths, default_bytes=64 * 1024):
    """掃描檔案列表，回傳最大檔案位元組數"""
    max_bytes = 0
    for p in paths:
        try:
            sz = os.stat(p)[6]
        except Exception:
            continue
        if sz > max_bytes:
            max_bytes = sz
    return max_bytes if max_bytes > 0 else default_bytes


def compute_max_frame_size(paths, default_bytes=240 * 240, bytes_per_pixel=2):
    """解析 jpeg header 取得最大解析度，回傳所需 frame buffer 位元組數"""
    max_w = 0
    max_h = 0
    for p in paths:
        try:
            with _open_read(p) as f:
                if f.read(2) == b"\xff\xd8":
                    while True:
                        marker_data = f.read(2)
                        if len(marker_data) < 2:
                            break
                        if marker_data[0] != 0xFF:
                            continue
                        marker = marker_data[1]
                        if marker in (
                            0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                            0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF,
                        ):
                            f.read(3)  # 跳過長度與精度
                            h = int.from_bytes(f.read(2), "big")
                            w = int.from_bytes(f.read(2), "big")
                            if w > max_w:
                                max_w = w
                            if h > max_h:
                                max_h = h
                            break
                        else:
                            length = int.from_bytes(f.read(2), "big")
                            f.read(length - 2)
        except Exception:
            pass

    if max_w > 0 and max_h > 0:
        return max_w * max_h * int(bytes_per_pixel)
    return int(default_bytes) * int(bytes_per_pixel)


def _clamp_range(total, start=0, end=None):
    total = int(total or 0)
    if total <= 0:
        return 0, -1, 0
    start = int(start or 0)
    if start < 0:
        start = 0
    if start >= total:
        start = total - 1
    if end is None or int(end) == 0xFFFFFFFF:
        end = total - 1
    else:
        end = int(end)
    if end < start:
        end = start
    if end >= total:
        end = total - 1
    return start, end, (end - start + 1)


# ── 統一資料層存取（fs）───────────────────────────────────────


def _data_fs():
    """取得統一資料層服務（fs_manager），取不到回 None 退回原生 open()"""
    try:
        from lib.sys_bus import bus

        return bus.get_service("data")
    except Exception:
        return None


def _open_read(path):
    """經統一資料層開檔；失敗退回原生 open()。

    三層降級鏈：fs.open_read(RAM/FAT) → fs.read(raw-SD→BytesIO) → open()
    """
    fs = _data_fs()
    if fs is not None:
        # 1) fs.open_read — 支援 RAM (BytesIO) 與 FAT (原生 file)
        try:
            f = fs.open_read(path)
            if f is not None:
                return f
        except Exception:
            pass
        # 2) fs.read — 支援 raw-SD (fast_io.Storage) 讀全檔轉 BytesIO
        try:
            data = fs.read(path)
            if data is not None:
                import io
                return io.BytesIO(data)
        except Exception:
            pass
    # 3) 最終 fallback
    return open(path, "rb")


# ── 統一媒體來源基類 ──────────────────────────────────────────


class MediaSource:
    """統一媒體來源介面。

    子類需提供 read_into(fb) -> (frame_idx, nbytes)，把「可立即 DMA 的像素」
    寫入 fb（bytearray / memoryview / framebuffer）。
    """

    is_raw = False   # True: fb 內已是 raw 像素，player 跳過解碼直接 DMA
    count = 0        # 總幀數，0 表示未知
    width = 0
    height = 0
    frame_size = 0   # 每幀像素位元組數（bin 模式必填；jpeg 解碼後 = w*h*bpp）

    def read_into(self, _fb):
        raise NotImplementedError

    def reset(self):
        pass

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# ── JPEG 共用：整幀解碼進 fb ──────────────────────────────────


class _JpegDecodeMixin:
    """共用 JPEG 整幀解碼邏輯（folder / jpk）。

    需要 self._decoder（jpeg.Decoder, return_bytes=False）。
    blocks=0 → 整幀解碼，避免 Python 層逐 block 迴圈。
    """

    def _decode_into(self, jpeg_data, fb):
        info = self._decoder.get_img_info(jpeg_data)
        self.width = int(info[0])
        self.height = int(info[1])
        self.frame_size = self.width * self.height * self._bpp
        # blocks 預設 0 = 整幀解碼
        self._decoder.decode_into(jpeg_data, fb)
        return self.frame_size


# ── folder 模式 ──────────────────────────────────────────────


class FolderSource(MediaSource, _JpegDecodeMixin):
    """資料夾內多個 JPEG 檔，逐檔整幀解碼進 fb。"""

    is_raw = False

    def __init__(self, folder, decoder, bpp=2, loop=True, start=0, end=None):
        self._decoder = decoder
        self._bpp = int(bpp)
        self.loop = bool(loop)
        fs = _data_fs()
        if fs is not None:
            try:
                self._paths = fs.list_jpegs(folder)
            except Exception:
                self._paths = list_jpegs(folder)
        else:
            self._paths = list_jpegs(folder)
        self._range_start, self._range_end, self.count = _clamp_range(
            len(self._paths), start, end)
        self._idx = self._range_start

    def read_into(self, fb):
        if not self._paths or self.count <= 0:
            return None, 0
        if self._idx > self._range_end:
            if not self.loop:
                return None, 0
            self._idx = self._range_start
        path = self._paths[self._idx]
        idx = self._idx
        self._idx += 1
        try:
            f = _open_read(path)
            try:
                data = f.read()
            finally:
                f.close()
            n = self._decode_into(data, fb)
            return idx, n
        except Exception:
            return idx, 0

    def reset(self):
        self._idx = self._range_start


# ── jpk 模式 ─────────────────────────────────────────────────


class PackJpegSource(MediaSource, _JpegDecodeMixin):
    """JPK1 打包檔（變長 JPEG frame），讀出後整幀解碼進 fb。

    包裝 lib.pack_source.PackSource：先讀 JPEG raw 進內部 buffer，再 decode 進 fb。
    """

    is_raw = False

    def __init__(self, path, decoder, bpp=2, loop=True, max_jpeg=None,
                 start=0, end=None):
        from lib.pack_source import PackSource

        self._decoder = decoder
        self._bpp = int(bpp)
        self.loop = bool(loop)
        self._pack = PackSource(path, loop=loop)
        self._range_start, self._range_end, self.count = _clamp_range(
            int(self._pack.count), start, end)
        # JPEG raw 暫存區：用 pack header 內的 max_size，不足則回退預設
        self._max_jpeg = int(max_jpeg or self._pack.max_size or (64 * 1024))
        self._read_buf = bytearray(self._max_jpeg)
        self._read_mv = memoryview(self._read_buf)
        self.reset()

    def read_into(self, fb):
        if self.count <= 0:
            return None, 0
        if self._pack._idx > self._range_end:
            if not self.loop:
                return None, 0
            self.reset()
        idx, got, _dt = self._pack.read_next_into(self._read_mv, self._max_jpeg)
        if idx is None:
            return None, 0
        try:
            n = self._decode_into(self._read_mv[:got], fb)
            return int(idx), n
        except Exception:
            return int(idx), 0

    def reset(self):
        self._pack.reset()
        if self._range_start > 0:
            self._pack.skip_next(self._range_start)

    def close(self):
        try:
            self._pack.close()
        except Exception:
            pass


# ── bin 模式（移植 VideoStreamReader）─────────────────────────


class BinSource(MediaSource):
    """定長 raw 像素檔（RGB565/RGB888），無需解碼，直接拷貝整幀進 fb。

    移植自舊代碼 TFT.VideoStreamReader：保持檔案開啟、定長 frame_size、
    seek/sequential 讀取。frame_size 由外部傳入（相容不同像素格式）。
    """

    is_raw = True

    def __init__(self, path, frame_size=None, width=0, height=0, bpp=2, loop=True,
                 start=0, end=None):
        if frame_size is None:
            if width and height:
                frame_size = int(width) * int(height) * int(bpp)
            else:
                raise ValueError("BinSource needs frame_size or width/height")
        self.path = path
        self.frame_size = int(frame_size)
        self.width = int(width)
        self.height = int(height)
        self.loop = bool(loop)
        self.file_size = os.stat(path)[6]
        self._full_count = self.file_size // self.frame_size
        self._range_start, self._range_end, self.count = _clamp_range(
            self._full_count, start, end)
        self._f = _open_read(path)  # 經 fs_manager 開檔，保持開啟
        self._idx = self._range_start
        if self._range_start > 0:
            self._f.seek(self._range_start * self.frame_size)

    def read_into(self, fb):
        """順序讀下一幀進 fb（最高效）；EOF 時依 loop 重置。"""
        mv = fb if isinstance(fb, memoryview) else memoryview(fb)
        if len(mv) < self.frame_size:
            raise ValueError("fb too small for bin frame")
        if self.count <= 0:
            return None, 0
        if self._idx > self._range_end:
            if not self.loop:
                return None, 0
            self.reset()
        target = mv[: self.frame_size]
        n = self._f.readinto(target)
        if not n:
            if not self.loop:
                return None, 0
            self.reset()
            n = self._f.readinto(target)
            if not n:
                return None, 0
        idx = self._idx
        self._idx += 1
        if self._idx > self._range_end and self.loop:
            self.reset()
        return idx, n

    def read_frame_into(self, fb, frame_index):
        """讀取指定索引的單幀進 fb（隨機存取）。"""
        if frame_index < self._range_start or frame_index > self._range_end:
            return None, 0
        mv = fb if isinstance(fb, memoryview) else memoryview(fb)
        offset = frame_index * self.frame_size
        self._f.seek(offset)
        n = self._f.readinto(mv[: self.frame_size])
        self._idx = frame_index + 1
        return frame_index, n

    def reset(self):
        self._f.seek(self._range_start * self.frame_size)
        self._idx = self._range_start

    def close(self):
        try:
            self._f.close()
        except Exception:
            pass


# ── 工廠：依路徑自動判斷模式 ──────────────────────────────────


def _is_dir(path):
    try:
        return (os.stat(path)[0] & 0x4000) != 0  # S_IFDIR
    except Exception:
        return False


def open_source(path, decoder=None, bpp=2, loop=True,
                frame_size=None, width=0, height=0, max_jpeg=None,
                range_start=0, range_end=None):
    """依輸入路徑自動判斷模式並回傳統一 MediaSource。

    判斷規則：
      - 路徑是資料夾            → FolderSource（需 decoder）
      - 副檔名 .jpk / .pack     → PackJpegSource（需 decoder）
      - 副檔名 .bin / .raw      → BinSource（需 frame_size 或 width/height）
      - 其他                    → 無法判斷，丟 ValueError

    參數：
      decoder    : jpeg.Decoder 實例（folder/jpk 必填；return_bytes=False）
      bpp        : 每像素位元組（RGB565=2, RGB888=3）
      frame_size : bin 模式每幀位元組數（優先）
      width/height: bin 模式可用 w*h*bpp 推算 frame_size
      max_jpeg   : jpk 模式 JPEG raw 暫存區上限（預設取 pack header max_size）
    """
    p = str(path)
    low = p.lower()

    if _is_dir(p):
        if decoder is None:
            raise ValueError("FolderSource needs a decoder")
        return FolderSource(
            p, decoder, bpp=bpp, loop=loop,
            start=range_start, end=range_end)

    if low.endswith(".jpk") or low.endswith(".pack"):
        if decoder is None:
            raise ValueError("PackJpegSource needs a decoder")
        return PackJpegSource(
            p, decoder, bpp=bpp, loop=loop, max_jpeg=max_jpeg,
            start=range_start, end=range_end)

    if low.endswith(".bin") or low.endswith(".raw"):
        return BinSource(
            p, frame_size=frame_size, width=width, height=height,
            bpp=bpp, loop=loop, start=range_start, end=range_end)

    raise ValueError("unknown media source: " + p)
