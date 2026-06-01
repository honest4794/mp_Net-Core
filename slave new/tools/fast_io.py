# -*- coding: utf-8 -*-
"""SD 卡中央儲存管理器 — 檔案級別 API

內部管理 sector 與 alloc.json，外部只需檔名。
同時最多一個讀取 + 一個寫入 (兩個指標)。

用法:
  from tools.fast_io import Storage

  s = Storage()

  # ── 寫入 ──
  s.write_begin("frame.jpk", total_bytes=102400)
  s.write(header_bytes)
  s.write(body_bytes)
  s.write_end()

  # ── 讀取 ──
  s.read_begin("frame.jpk")
  buf = bytearray(16384)
  while True:
      n = s.read_into(buf)
      if n == 0: break
      process(buf[:n])
  s.read_end()

  # ── 便捷 ──
  data = s.read_all("frame.jpk")
  s.list_files()
  s.remove("frame.jpk")
"""

import gc, _thread
from tools.alloc import Allocator

BUF_SIZE = 32768
_sd_lock = _thread.allocate_lock()


def _sd():
    from lib.sys_bus import bus
    s = bus.get_service("sd_raw")
    if s is None:
        raise RuntimeError("sd_raw not on bus")
    return s


class Storage:
    def __init__(self, sd=None, buf_size=BUF_SIZE):
        self._sd = sd or _sd()
        self._ss = self._sd.info()[1]
        self._alloc = Allocator()
        self._chunk = buf_size  # API 層 chunk size

        # 分配 DMA buffer，大小跟 API chunk 一致
        self._buf_bytes = buf_size
        try:
            import heap_caps
            self._io_buf = heap_caps.malloc(buf_size, heap_caps.CAP_DMA)
        except:
            self._io_buf = None
        if self._io_buf is None:
            self._io_buf = bytearray(buf_size)

        # 用實際 buffer 大小計算 sector per chunk
        self._spc = self._buf_bytes // self._ss
        self._buf_size = self._buf_bytes

        self._c = False

        self._w_open = False
        self._r_open = False

        self._w_file = None
        self._w_sector = 0
        self._w_cnt = 0
        self._w_byte = 0
        self._w_total = 0

        self._r_file = None
        self._r_sector = 0
        self._r_cnt = 0
        self._r_byte = 0

    # ── 寫入 ──

    def write_begin(self, name, total_bytes):
        if self._w_open:
            raise RuntimeError("already writing")
        if self._r_open and self._r_file == name:
            raise RuntimeError("cannot write while reading same file")

        self._w_open = True
        self._w_file = name
        self._w_total = total_bytes
        self._w_cnt = (total_bytes + self._ss - 1) // self._ss
        self._w_sector = self._alloc.append(name, self._w_cnt)
        self._w_byte = 0

    def write(self, data):
        if not self._w_open:
            raise RuntimeError("no active write")

        src = memoryview(data)
        total = len(src)
        p = 0
        buf = self._io_buf

        while p < total:
            n = min(total - p, self._buf_size)
            buf[:n] = src[p:p + n]

            sector = self._w_sector + self._w_byte // self._ss
            with _sd_lock:
                self._sd.writeblocks(sector, buf)

            self._w_byte += n
            p += n

        return p

    def write_end(self):
        if not self._w_open:
            return
        if self._w_byte > self._w_total:
            actual_cnt = (self._w_byte + self._ss - 1) // self._ss
            if actual_cnt > self._w_cnt:
                self._w_cnt = actual_cnt
                self._alloc._e[self._w_file] = (self._w_sector, self._w_cnt)
        self._alloc.save()
        self._w_open = False
        self._w_file = None

    # ── 讀取 ──

    def read_begin(self, name):
        if self._r_open:
            raise RuntimeError("already reading")
        entry = self._alloc.find(name)
        if entry is None:
            raise RuntimeError("file not found: {}".format(name))
        self._r_open = True
        self._r_file = name
        self._r_sector, self._r_cnt = entry
        self._r_byte = 0
        return self._r_cnt * self._ss

    def read_into(self, buf, off=0):
        if not self._r_open:
            return 0

        max_bytes = len(buf) - off
        if max_bytes <= 0:
            return 0

        remaining = self._r_cnt * self._ss - self._r_byte
        if remaining <= 0:
            return 0

        sector = self._r_sector + self._r_byte // self._ss
        n_sectors = min(self._spc, (remaining + self._ss - 1) // self._ss)
        with _sd_lock:
            self._sd.readblocks(sector, self._io_buf)

        n_bytes = min(remaining, n_sectors * self._ss)
        n_bytes = min(n_bytes, max_bytes)
        buf[off:off + n_bytes] = self._io_buf[:n_bytes]

        self._r_byte += n_bytes
        return n_bytes

    def read_end(self):
        self._r_open = False
        self._r_file = None

    # ── 便捷 API ──

    def read_all(self, name):
        size = self.read_begin(name)
        data = bytearray(size)
        off = 0
        while True:
            n = self.read_into(data, off)
            if n == 0:
                break
            off += n
        self.read_end()
        return data[:off] if off < size else data

    def list_files(self):
        return self._alloc.list_files()

    def remove(self, name):
        self._alloc.trim_from(name)
        self._alloc.save()

    def close(self):
        if self._c:
            return
        if self._w_open:
            self.write_end()
        if self._r_open:
            self.read_end()
        if self._io_buf is not None:
            try:
                import heap_caps
                heap_caps.free(self._io_buf)
            except Exception:
                pass
            self._io_buf = None
        self._c = True

    def __del__(self):
        self.close()


class StreamReader:
    def __init__(self, sd=None, buf_size=16384, n_bufs=2):
        from lib.sys_bus import bus
        from lib.buffer_hub import AtomicStreamHub
        self._sd = sd or bus.get_service("sd_raw")
        self._ss = self._sd.info()[1]
        self._hub = AtomicStreamHub(buf_size, num_buffers=n_bufs, try_dma=True)
        self._buf_size = buf_size
        self._spc = buf_size // self._ss
        self._r_sector = 0
        self._r_cnt = 0
        self._r_byte = 0
        self._eof = False
        self._started = False

    @property
    def chunk_sectors(self):
        return self._spc
    @property
    def chunk_bytes(self):
        return self._buf_size

    def start(self, alloc, name):
        e = alloc.find(name)
        if e is None:
            raise RuntimeError("file not found")
        self._r_sector, self._r_cnt = e
        self._r_byte = 0
        self._eof = False
        self._started = True

    def start_sector(self, sector, cnt):
        self._r_sector = sector
        self._r_cnt = cnt
        self._r_byte = 0
        self._eof = False
        self._started = True

    def feed(self, sector):
        if self._eof:
            return False
        v = self._hub.get_write_view()
        if v is None:
            return False
        self._sd.readblocks(sector, v)
        self._hub.commit()
        return True

    def feed_all(self):
        sec = self._r_sector
        rem = self._r_cnt
        while rem > 0:
            n = min(self._spc, rem)
            while not self.feed(sec):
                time.sleep_ms(1)
            sec += n
            rem -= n
        self._eof = True

    def feed_done(self):
        self._eof = True

    def next(self):
        if not self._started:
            return None
        v = self._hub.get_read_view()
        if v is None:
            return None if self._eof else None
        self._r_byte += len(v)
        return v

    def release(self):
        self._hub.release_read()

    def read_into(self, buf, off=0):
        v = self.next()
        if v is None:
            return 0
        n = min(len(v), len(buf) - off)
        buf[off:off + n] = v[:n]
        self._hub.release_read()
        return n

    def close(self):
        self._hub.close()
        self._started = False

    def __del__(self):
        self.close()
