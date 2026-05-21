import time
import micropython

_READ_BUF_SIZE = micropython.const(32768)


def _ticks_us():
    if hasattr(time, "ticks_us"):
        return time.ticks_us()
    return int(time.time() * 1000000)


def _ticks_diff(a, b):
    if hasattr(time, "ticks_diff"):
        return time.ticks_diff(a, b)
    return a - b


def _u32_le(b, off):
    return b[off + 0] | (b[off + 1] << 8) | (b[off + 2] << 16) | (b[off + 3] << 24)


class PackSource:
    def __init__(self, path, loop=True):
        self.path = path
        self.loop = bool(loop)
        self._f = open(path, "rb")
        hdr = self._f.read(16)
        if len(hdr) != 16 or hdr[0:4] != b"JPK1":
            raise ValueError("bad pack header")
        self.count = _u32_le(hdr, 4)
        self.max_size = _u32_le(hdr, 8)
        self._start = 16
        self._pos = 16
        self._idx = 0
        self._buf = bytearray(_READ_BUF_SIZE)
        self._buf_mv = memoryview(self._buf)
        self._buf_off = 0
        self._buf_len = 0

    def _fill(self):
        try:
            self._f.seek(self._pos)
        except Exception:
            pass
        n = self._f.readinto(self._buf_mv)
        if n is None:
            n = 0
        self._buf_off = 0
        self._buf_len = int(n)
        self._pos += self._buf_len

    def _read4(self):
        if self._buf_off + 4 > self._buf_len:
            self._fill()
            if self._buf_off + 4 > self._buf_len:
                return None
        off = self._buf_off
        self._buf_off += 4
        return _u32_le(self._buf, off)

    def _read_into(self, dst, n):
        got = 0
        while got < n:
            if self._buf_off >= self._buf_len:
                self._fill()
                if self._buf_len == 0:
                    break
            avail = self._buf_len - self._buf_off
            take = min(n - got, avail)
            dst[got:got + take] = self._buf_mv[self._buf_off:self._buf_off + take]
            self._buf_off += take
            got += take
        return got

    def reset(self):
        self._pos = self._start
        self._buf_off = 0
        self._buf_len = 0
        self._idx = 0

    def tell(self):
        return self._pos, self._idx

    def seek_to(self, pos, idx=0):
        self._pos = int(pos)
        self._buf_off = 0
        self._buf_len = 0
        self._idx = int(idx or 0)

    def skip_next(self, count):
        count = int(count or 0)
        if count <= 0:
            return True, 0

        t0 = _ticks_us()
        while count > 0:
            n = self._read4()
            if n is None:
                if not self.loop:
                    return False, _ticks_diff(_ticks_us(), t0)
                self.reset()
                n = self._read4()
                if n is None:
                    return False, _ticks_diff(_ticks_us(), t0)

            self._pos = self._pos - (self._buf_len - self._buf_off) + n
            self._buf_off = 0
            self._buf_len = 0

            self._idx += 1
            if self.count and self._idx >= self.count:
                if self.loop:
                    self.reset()
                else:
                    self._idx = self.count
                    return False, _ticks_diff(_ticks_us(), t0)

            count -= 1

        return True, _ticks_diff(_ticks_us(), t0)

    def read_next_into(self, dst, max_len):
        t0 = _ticks_us()

        n = self._read4()
        if n is None:
            if not self.loop:
                return None, 0, _ticks_diff(_ticks_us(), t0)
            self.reset()
            n = self._read4()
            if n is None:
                return None, 0, _ticks_diff(_ticks_us(), t0)

        if n > max_len:
            raise ValueError("frame too big: " + str(n))

        mv = dst[:n]
        got = self._read_into(mv, n)
        if got is None:
            got = 0
        dt = _ticks_diff(_ticks_us(), t0)

        idx = self._idx
        self._idx += 1
        if self.count and self._idx >= self.count:
            if self.loop:
                self.reset()
            else:
                self._idx = self.count

        return idx, got, dt

    def close(self):
        try:
            self._f.close()
        except Exception:
            pass
