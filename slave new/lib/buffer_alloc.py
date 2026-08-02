"""
lib/buffer_alloc.py — 統一的 framebuffer 分配器

依 fb_mode 選擇 buffer 來源，並記住來源供正確 free（修復
「對 fallback bytearray 誤呼叫 heap_caps.free」的 bug）。

用法:
  from lib.buffer_alloc import alloc_fb, get_fb_mode

  fb = alloc_fb(size, fb_mode="auto")   # 回傳 Fb 物件 (用 fb.buf 存取)
  ... fill fb.buf ...
  fb.free()                              # 依來源正確釋放

fb_mode:
  "auto"  — SPIRAM → CAP_DMA → bytearray 三級 fallback
  "psram" — 只試 CAP_SPIRAM，失敗 fallback bytearray
  "dma"   — 只試 CAP_DMA（內部 SRAM，DMA 可直讀）
  "ram"   — 純 bytearray
"""
from lib.sys_bus import bus


def get_fb_mode(override=None):
    """回傳 fb_mode：override 優先，否則從 bus.shared['Buffer']['fb_mode'] 讀"""
    if override:
        return override
    buf_cfg = bus.shared.get("Buffer", {}) or {}
    return buf_cfg.get("fb_mode", "auto")


class Fb:
    """帶來源標記的 buffer。__slots__ 省記憶體。"""

    __slots__ = ("buf", "_from_heap_caps")

    def __init__(self, buf, from_heap_caps):
        self.buf = buf
        self._from_heap_caps = from_heap_caps

    def free(self):
        """依來源正確釋放：heap_caps buffer 用 heap_caps.free，bytearray 留給 GC"""
        if self.buf is None:
            return
        if self._from_heap_caps:
            try:
                import heap_caps
                heap_caps.free(self.buf)
            except Exception:
                pass
        self.buf = None
        self._from_heap_caps = False

    @property
    def kind(self):
        return "heap_caps" if self._from_heap_caps else "bytearray"

    def __len__(self):
        return len(self.buf) if self.buf is not None else 0


def _try_heap_caps(size, caps):
    try:
        import heap_caps
        b = heap_caps.malloc(size, caps)
        return b if b is not None else None
    except Exception:
        return None


def alloc_fb(size, fb_mode="auto"):
    """
    分配 framebuffer，回傳 Fb 物件。
    fb_mode="auto" 時也接受 bus.shared 的 Buffer.fb_mode。
    """
    if fb_mode == "auto":
        fb_mode = get_fb_mode()

    if fb_mode in ("auto", "psram"):
        b = _try_heap_caps(size, getattr(__import__("heap_caps"), "CAP_SPIRAM", 0))
        if b is not None:
            return Fb(b, True)

    if fb_mode in ("auto", "dma"):
        b = _try_heap_caps(size, getattr(__import__("heap_caps"), "CAP_DMA", 0))
        if b is not None:
            return Fb(b, True)

    return Fb(bytearray(size), False)


def free_fb(fb):
    """相容簡便函式：接受 Fb 或原始 buffer（原始 buffer 一律不 free，安全）"""
    if isinstance(fb, Fb):
        fb.free()
