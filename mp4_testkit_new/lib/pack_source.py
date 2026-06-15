import time


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


class _MemFile:
    def __init__(self, data):
        self._data = data
        self._pos = 0

    def read(self, n=-1):
        if n < 0:
            n = len(self._data) - self._pos
        end = min(self._pos + n, len(self._data))
        result = self._data[self._pos:end]
        self._pos = end
        return result

    def readinto(self, buf):
        n = min(len(buf), len(self._data) - self._pos)
        buf[:n] = self._data[self._pos:self._pos + n]
        self._pos += n
        return n

    def seek(self, pos, whence=0):
        if whence == 0:
            self._pos = pos
        elif whence == 1:
            self._pos += pos
        elif whence == 2:
            self._pos = len(self._data) + pos
        return self._pos

    def tell(self):
        return self._pos

    def close(self):
        pass


def _open_fs(path):
    try:
        from lib.sys_bus import bus
        fs = bus.get_service("data")
        if fs is not None:
            try:
                f = fs.open_read(path)
                if f is not None:
                    return f
            except Exception:
                pass
            try:
                data = fs.read(path)
                if data is not None:
                    return _MemFile(data)
            except Exception:
                pass
    except Exception:
        pass
    return open(path, "rb")


class PackSource:
    def __init__(self, path, loop=True):
        self.path = path
        self.loop = bool(loop)
        self._f = _open_fs(path)
        hdr = self._f.read(16)
        if len(hdr) != 16 or hdr[0:4] != b"JPK1":
            raise ValueError("bad pack header")
        self.count = _u32_le(hdr, 4)
        self.max_size = _u32_le(hdr, 8)
        self._start = 16
        self._idx = 0
        self._len_buf = bytearray(4)
        self._len_mv = memoryview(self._len_buf)

    def reset(self):
        self._f.seek(self._start)
        self._idx = 0
    
    def tell(self):
        try:
            return int(self._f.tell()), int(self._idx)
        except Exception:
            return 0, int(self._idx)
    
    def seek_to(self, pos, idx=0):
        self._f.seek(int(pos))
        self._idx = int(idx or 0)

    def skip_next(self, count):
        count = int(count or 0)
        if count <= 0:
            return True, 0

        t0 = _ticks_us()
        while count > 0:
            ln_n = self._f.readinto(self._len_mv)
            if ln_n != 4:
                if not self.loop:
                    return False, _ticks_diff(_ticks_us(), t0)
                self.reset()
                ln_n = self._f.readinto(self._len_mv)
                if ln_n != 4:
                    return False, _ticks_diff(_ticks_us(), t0)

            n = _u32_le(self._len_buf, 0)
            self._f.seek(n, 1)

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
        ln_n = self._f.readinto(self._len_mv)
        if ln_n != 4:
            if not self.loop:
                return None, 0, _ticks_diff(_ticks_us(), t0)
            self.reset()
            ln_n = self._f.readinto(self._len_mv)
            if ln_n != 4:
                return None, 0, _ticks_diff(_ticks_us(), t0)

        n = _u32_le(self._len_buf, 0)
        if n > max_len:
            raise ValueError("frame too big: " + str(n))

        mv = dst[:n]
        got = self._f.readinto(mv)
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
