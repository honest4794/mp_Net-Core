import gc
import micropython

_IDLE = micropython.const(0)
_READY = micropython.const(1)
_READING = micropython.const(2)

_HEAP_CAPS_AVAILABLE = False
_DMA_ALLOC = None
_DMA_FREE = None
_DMA_BOUNCE_SIZE = 32 * 1024


def _import_heap_caps():
    global _HEAP_CAPS_AVAILABLE, _DMA_ALLOC, _DMA_FREE
    if _HEAP_CAPS_AVAILABLE:
        return True
    try:
        import heap_caps
        _HEAP_CAPS_AVAILABLE = True
        _DMA_ALLOC = lambda sz: heap_caps.malloc(sz, heap_caps.CAP_DMA)
        _DMA_FREE = heap_caps.free
        return True
    except ImportError:
        _HEAP_CAPS_AVAILABLE = False
        _DMA_ALLOC = None
        _DMA_FREE = None
        return False


def _alloc_dma(size):
    if _import_heap_caps():
        try:
            buf = _DMA_ALLOC(size)
            if buf is not None:
                return buf
        except Exception:
            pass
    return None


def _free_dma(buf):
    if _DMA_FREE and buf is not None:
        try:
            _DMA_FREE(buf)
        except Exception:
            pass


class DmaBounceBuf:
    def __init__(self, size=_DMA_BOUNCE_SIZE):
        self._buf = _alloc_dma(size)
        self.size = size

    @property
    def available(self):
        return self._buf is not None

    def get(self):
        return self._buf

    def copy_into(self, target_mv, source_mv, n):
        if self._buf and n <= self.size:
            self._buf[:n] = source_mv[:n]
            target_mv[:n] = self._buf[:n]
        else:
            target_mv[:n] = source_mv[:n]

    def prep_for_spi(self, source_mv, n):
        if self._buf and n <= self.size:
            self._buf[:n] = source_mv[:n]
            return self._buf[:n]
        return source_mv[:n]

    def close(self):
        _free_dma(self._buf)
        self._buf = None


class AtomicStreamHub:
    IDLE = _IDLE
    READY = _READY
    READING = _READING

    def __init__(self, size, num_buffers=3, try_dma=False, try_bounce=False):
        self._dma_bufs = None
        self._bufs = []
        self._views = []

        dma_used = 0
        for i in range(num_buffers):
            if try_dma:
                dma_buf = _alloc_dma(size)
                if dma_buf is not None:
                    if self._dma_bufs is None:
                        self._dma_bufs = []
                    self._dma_bufs.append(dma_buf)
                    self._bufs.append(None)
                    self._views.append(memoryview(dma_buf))
                    dma_used += 1
                    continue
            b = bytearray(size)
            self._bufs.append(b)
            self._views.append(memoryview(b))

        self._status = [_IDLE] * num_buffers
        self._w_ptr = 0
        self._r_ptr = 0

        self.size = size
        self.num_buffers = num_buffers
        self._last_read_idx = -1
        self._dma_count = dma_used

        self._bounce = _alloc_dma(_DMA_BOUNCE_SIZE) if try_bounce else None

        tag = ""
        parts = []
        if dma_used > 0:
            parts.append("DMA:{}".format(dma_used))
        if self._bounce is not None:
            parts.append("bounce")
        if parts:
            tag = " [{}]".format(",".join(parts))
        print("🚀 [BufferHub] Ready: {} KB total{}".format((size * num_buffers) // 1024, tag))

    @property
    def dirty(self):
        return self._status[self._r_ptr] == _READY

    @micropython.native
    def write_from(self, source):
        ptr = self._w_ptr
        if self._status[ptr] != _IDLE:
            return False
        self._views[ptr][:] = source
        self._status[ptr] = _READY
        self._w_ptr = (ptr + 1) % self.num_buffers
        return True

    @micropython.native
    def read_into(self, target):
        if self._last_read_idx != -1:
            self._status[self._last_read_idx] = _IDLE
            self._last_read_idx = -1
        ptr = self._r_ptr
        if self._status[ptr] != _READY:
            return False
        target[:] = self._views[ptr]
        self._status[ptr] = _IDLE
        self._r_ptr = (ptr + 1) % self.num_buffers
        return True

    @micropython.native
    def flush(self):
        for i in range(self.num_buffers):
            self._status[i] = _IDLE
        self._w_ptr = 0
        self._r_ptr = 0
        self._last_read_idx = -1

    def get_fill_level(self):
        count = 0
        for s in self._status:
            if s == _READY:
                count += 1
        return count

    @micropython.native
    def get_write_view(self):
        ptr = self._w_ptr
        if self._status[ptr] != _IDLE:
            return None
        return self._views[ptr]

    @micropython.native
    def commit(self):
        ptr = self._w_ptr
        if self._status[ptr] == _IDLE:
            self._status[ptr] = _READY
            self._w_ptr = (ptr + 1) % self.num_buffers

    @micropython.native
    def get_read_view(self):
        if self._last_read_idx != -1:
            self._status[self._last_read_idx] = _IDLE
            self._last_read_idx = -1
        ptr = self._r_ptr
        if self._status[ptr] == _READY:
            self._status[ptr] = _READING
            self._last_read_idx = ptr
            self._r_ptr = (ptr + 1) % self.num_buffers
            return self._views[ptr]
        return None

    @micropython.native
    def release_read(self):
        if self._last_read_idx != -1:
            self._status[self._last_read_idx] = _IDLE
            self._last_read_idx = -1

    def force_get_view(self):
        return self._views[self._r_ptr]

    def bounce_into(self, dst_mv, src_mv, n):
        if self._bounce and n <= _DMA_BOUNCE_SIZE:
            self._bounce[:n] = src_mv[:n]
            dst_mv[:n] = self._bounce[:n]
        else:
            dst_mv[:n] = src_mv[:n]

    @property
    def dma_count(self):
        return self._dma_count

    @property
    def has_bounce(self):
        return self._bounce is not None

    def close(self):
        if self._dma_bufs:
            for b in self._dma_bufs:
                _free_dma(b)
            self._dma_bufs = None
        _free_dma(self._bounce)
        self._bounce = None
        self._bufs = []
        self._views = []
        self._status = []
        self._w_ptr = 0
        self._r_ptr = 0
        self._last_read_idx = -1
