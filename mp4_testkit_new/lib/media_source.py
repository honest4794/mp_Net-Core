import os

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


def list_jpegs(folder_path):
    files = [
        f
        for f in os.listdir(folder_path)
        if f.lower().endswith(".jpeg") or f.lower().endswith(".jpg")
    ]
    files.sort()
    return [folder_path + "/" + f for f in files]


def compute_max_file_size(paths, default_bytes=64 * 1024):
    max_bytes = 0
    for p in paths:
        sz = os.stat(p)[6]
        if sz > max_bytes:
            max_bytes = sz
    return max_bytes if max_bytes > 0 else default_bytes


def compute_max_frame_size(paths, default_bytes=240 * 240, bytes_per_pixel=2):
    max_w = 0
    max_h = 0
    for p in paths:
        try:
            with _open_fs(p) as f:
                if f.read(2) == b'\xff\xd8':
                    while True:
                        marker_data = f.read(2)
                        if len(marker_data) < 2:
                            break
                        if marker_data[0] != 0xff:
                            continue
                        marker = marker_data[1]
                        if marker in (0xc0, 0xc1, 0xc2, 0xc3, 0xc5, 0xc6, 0xc7, 0xc9, 0xca, 0xcb, 0xcd, 0xce, 0xcf):
                            f.read(3)  # Skip length and precision
                            h = int.from_bytes(f.read(2), 'big')
                            w = int.from_bytes(f.read(2), 'big')
                            if w > max_w: max_w = w
                            if h > max_h: max_h = h
                            break
                        else:
                            length = int.from_bytes(f.read(2), 'big')
                            f.read(length - 2)
        except Exception:
            pass
            
    if max_w > 0 and max_h > 0:
        return max_w * max_h * int(bytes_per_pixel)
    return int(default_bytes) * int(bytes_per_pixel)
