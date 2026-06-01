"""16KB vs 32KB DMA buffer 對比"""

import time, gc
from tools.fast_io import Storage

TEST = "cmp.bin"
SIZE = 1 * 1024 * 1024
SECT = 600000


def _sz(b):
    for u in ("B","KB","MB"):
        if b < 1024: return "{}{}".format(b, u)
        b //= 1024
    return "{}{}".format(b, "MB")


def _row(label, ms, total):
    spd = total / 1048576 / (ms / 1000) if ms else 0
    print("  {:>6s}  {:>7.1f} ms  {:>8.2f} MB/s".format(label, ms, spd))
    return spd


def _pattern(sz):
    p = bytearray(sz)
    for i in range(sz): p[i] = i & 0xFF
    return p


def bench(label, bsz):
    print("\n  {} DMA buffer:".format(_sz(bsz)))
    s = Storage(buf_size=bsz)
    pat = _pattern(bsz)
    n = max(SIZE // bsz, 2)
    s.write_begin(TEST, n * bsz)
    t0 = time.ticks_ms()
    for _ in range(n): s.write(pat)
    ms_w = time.ticks_diff(time.ticks_ms(), t0)
    s.write_end()
    _row("write", ms_w, n * bsz)
    buf = bytearray(bsz)
    tsz = s.read_begin(TEST)
    rn = max(tsz // bsz, 4)
    gc.collect()
    t0 = time.ticks_ms()
    total = 0
    for _ in range(rn):
        nb = s.read_into(buf)
        if nb == 0: break
        total += nb
    ms_r = time.ticks_diff(time.ticks_ms(), t0)
    s.read_end()
    _row("read", ms_r, total)
    s.remove(TEST)
    s.close()
    return ms_w, ms_r


print("\n" + "=" * 40)
print("  16KB vs 32KB DMA buffer 對比")
print("  寫入 1MB  讀取 4MB")
print("=" * 40)
m16_w, m16_r = bench("16KB", 16384)
m32_w, m32_r = bench("32KB", 32768)
print()
print("=" * 40)
print("  buffer  gain")
print("  {:>4s}  write={:+.0f}%  read={:+.0f}%".format("16K", 0, 0))
print("  {:>4s}  write={:+.0f}%  read={:+.0f}%".format("32K",
    (m16_w - m32_w) / m16_w * 100,
    (m16_r - m32_r) / m16_r * 100))
print()
