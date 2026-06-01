"""Storage 效能測試 — 預設 32KB DMA buffer

測試寫入/讀取吞吐量，與 raw 和 VFS 對比。
寫入走 managed area，結束自動清理。
"""

import time, gc, os, ubinascii
from tools.fast_io import Storage, BUF_SIZE

TEST_FILE = "fst_test.bin"
READ_SIZE = 4 * 1024 * 1024
WRITE_TOTAL = 1 * 1024 * 1024


def _sz(b):
    for u in ("B","KB","MB"):
        if b < 1024: return "{}{}".format(b, u)
        b //= 1024
    return "{}{}".format(b, "MB")


def _row(label, op, ms, total):
    spd = total / 1048576 / (ms / 1000) if ms else 0
    print("  {:>4s} {:>3s}  {:>7.1f} ms  {:>8.2f} MB/s".format(label, op, ms, spd))
    return spd


def _pattern(size):
    p = bytearray(size)
    for i in range(size): p[i] = i & 0xFF
    return p


def bench_raw(sd):
    ss = sd.info()[1]
    try:
        import heap_caps
        b = heap_caps.malloc(16384, heap_caps.CAP_DMA)
        if not b: b = bytearray(16384)
    except: b = bytearray(16384)
    spc = 16384 // ss
    n = max(READ_SIZE // 16384, 4)
    gc.collect()
    t0 = time.ticks_ms()
    sec = 400000
    for _ in range(n):
        sd.readblocks(sec, b)
        sec += spc
    ms = time.ticks_diff(time.ticks_ms(), t0)
    spd = _row("raw","rd", ms, n * 16384)
    try: import heap_caps; heap_caps.free(b)
    except: pass
    return spd


def bench_write():
    print("\n  Storage 寫入 (buf {}):".format(_sz(BUF_SIZE)))
    s = Storage()
    chunk = BUF_SIZE
    pat = _pattern(chunk)
    n = max(WRITE_TOTAL // chunk, 2)
    s.write_begin(TEST_FILE, n * chunk)
    t0 = time.ticks_ms()
    for _ in range(n): s.write(pat)
    ms = time.ticks_diff(time.ticks_ms(), t0)
    s.write_end()
    spd = _row("str","wr", ms, n * chunk)
    s.remove(TEST_FILE)
    s.close()
    return spd


def bench_read():
    print("\n  Storage 讀取 (buf {}):".format(_sz(BUF_SIZE)))
    s = Storage()
    chunk = BUF_SIZE
    pat = _pattern(chunk)
    n = max(READ_SIZE // chunk, 4)
    s.write_begin(TEST_FILE, n * chunk)
    for _ in range(n): s.write(pat)
    s.write_end()
    buf = bytearray(chunk)
    tsz = s.read_begin(TEST_FILE)
    rn = max(tsz // chunk, 4)
    gc.collect()
    t0 = time.ticks_ms()
    total = 0
    for _ in range(rn):
        nbytes = s.read_into(buf)
        if nbytes == 0: break
        total += nbytes
    ms = time.ticks_diff(time.ticks_ms(), t0)
    s.read_end()
    spd = _row("str","rd", ms, total)
    s.remove(TEST_FILE)
    s.close()
    return spd


def bench_read_all():
    print("\n  read_all (256KB):")
    s = Storage()
    sz = 256 * 1024
    chunk = BUF_SIZE
    pat = _pattern(chunk)
    n = sz // chunk
    s.write_begin(TEST_FILE, sz)
    for _ in range(n): s.write(pat)
    s.write_end()
    gc.collect()
    t0 = time.ticks_ms()
    data = s.read_all(TEST_FILE)
    ms = time.ticks_diff(time.ticks_ms(), t0)
    ok = data is not None and len(data) == sz
    _row("str","all", ms, sz)
    print("  {:>4s} {:>3s}  {:>10s}".format("","","OK" if ok else "FAIL"))
    s.remove(TEST_FILE)
    s.close()
    return _row("str","all", ms, sz), ok


def bench_vfs():
    tf = "/sd/.fstt"
    sz = 256 * 1024
    chunk = 16384
    b = bytearray(chunk)
    n = sz // chunk
    v = {}
    for op_name, mode in (("wr","wb"),("rd","rb")):
        gc.collect()
        try:
            t0 = time.ticks_ms()
            with open(tf, mode) as f:
                if mode=="wb":
                    for _ in range(n): f.write(b)
                    f.flush()
                else:
                    for _ in range(n): f.read(chunk)
            ms = time.ticks_diff(time.ticks_ms(), t0)
            spd = sz / 1048576 / (ms / 1000) if ms else 0
            _row("vfs",op_name, ms, sz)
            v[op_name] = spd
        except Exception as e:
            print("  (vfs {} skip: {})".format(op_name, e))
    try: os.remove(tf)
    except: pass
    return v


def run(readonly=False):
    s0 = Storage()
    buf_actual = _sz(s0._buf_bytes)
    s0.close()
    print("\n" + "=" * 48)
    print("  Storage 測試  (buf={} actual={})".format(_sz(BUF_SIZE), buf_actual))
    if not readonly:
        print("  寫入:{}  讀取:{}".format(_sz(WRITE_TOTAL), _sz(READ_SIZE)))
    print("=" * 48)
    from tools.fast_io import _sd
    sd = _sd()
    r_raw = bench_raw(sd)
    w_st = bench_write() if not readonly else 0
    r_st = bench_read()
    ra, ra_ok = bench_read_all()
    v = bench_vfs()
    print()
    print("=" * 48)
    print("  結論")
    print("=" * 48)
    if not readonly:
        print("  write:  {:.2f} MB/s".format(w_st))
    print("  read:   {:.2f} MB/s".format(r_st))
    print("  raw:    {:.2f} MB/s".format(r_raw))
    if r_st and r_raw:
        print("  vs raw: {:.0f}%".format(r_st / r_raw * 100))
    if r_st and v.get("rd", 0):
        print("  vs VFS: {:.1f}x".format(r_st / v.get("rd")))
    print("  r_all:  {}".format("OK" if ra_ok else "NO"))
    print()
    return {"write": w_st, "read": r_st, "raw": r_raw, "vfs": v}
