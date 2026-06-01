"""SD 卡寫入微基準 — Buffer 組合掃描

測試各種 buffer size / DMA / hub 狀態機 / GC 控制的實際吞吐。
找出最快寫入模式，再套回 Storage。
"""

import gc, time, _thread
_sd_lock = _thread.allocate_lock()

BENCH_TOTAL = 1024 * 1024
SAFE_SEC    = 600000


def _sd():
    from lib.sys_bus import bus
    s = bus.get_service("sd_raw")
    if s is None:
        raise RuntimeError("sd_raw not on bus")
    return s


def _alloc_dma(size):
    try:
        import heap_caps
        b = heap_caps.malloc(size, heap_caps.CAP_DMA)
        if b: return b
    except:
        pass
    return None


def _free_dma(buf):
    if buf is None: return
    try:
        import heap_caps
        heap_caps.free(buf)
    except:
        pass


def _fill(buf):
    for i in range(len(buf)):
        buf[i] = i & 0xFF


def mode_dma(buf_size):
    buf = _alloc_dma(buf_size)
    if buf is None:
        buf = bytearray(buf_size)
    _fill(buf)
    return buf


def mode_hub(buf_size, n_bufs):
    from lib.buffer_hub import AtomicStreamHub
    hub = AtomicStreamHub(buf_size, num_buffers=n_bufs, try_dma=True)
    fill = bytearray(buf_size)
    _fill(fill)
    return hub, fill


def run_write(buf_size, n_bufs=0, gc_ctrl=False):
    sd = _sd()
    ss = sd.info()[1]
    spc = buf_size // ss
    n_ops = BENCH_TOTAL // buf_size
    direct = n_bufs == 0

    if direct:
        buf = mode_dma(buf_size)
        pattern = buf
    else:
        hub, pattern = mode_hub(buf_size, n_bufs)

    if gc_ctrl:
        gc.disable()

    t0 = time.ticks_ms()
    sec = SAFE_SEC

    if direct:
        for _ in range(n_ops):
            with _sd_lock:
                sd.writeblocks(sec, buf)
            sec += spc
    else:
        for _ in range(n_ops):
            view = hub.get_write_view()
            if view is None:
                view = bytearray(buf_size)
            view[:] = pattern
            with _sd_lock:
                sd.writeblocks(sec, view)
            hub.commit()
            hub.get_read_view()
            hub.release_read()
            sec += spc

    ms = time.ticks_diff(time.ticks_ms(), t0)

    if gc_ctrl:
        gc.enable()
        gc.collect()

    spd = BENCH_TOTAL / 1048576 / (ms / 1000) if ms else 0

    if direct:
        _free_dma(buf)
    else:
        hub.close()

    return ms, spd


def scan():
    print()
    print("=" * 60)
    print("  SD 卡寫入微基準掃描")
    print("  總量: {}  sector: {}".format(BENCH_TOTAL, SAFE_SEC))
    print("=" * 60)

    sizes = [4096, 8192, 16384, 32768, 65536]
    modes = [
        ("直寫DMA",   0, False),
        ("直寫DMA-G", 0, True),
        ("hub-2buf",  2, False),
        ("hub-2buf-G", 2, True),
        ("hub-4buf",  4, False),
        ("hub-4buf-G", 4, True),
    ]

    header = "{:>8s}".format("size")
    for label, _, _ in modes:
        header += "  {:>12s}".format(label)
    print(header)
    print("  " + "-" * (8 + 15 * len(modes)))

    raw_16k = _alloc_dma(16384)
    if raw_16k:
        _fill(raw_16k)
        t0 = time.ticks_ms()
        sd = _sd()
        for _ in range(BENCH_TOTAL // 16384):
            sd.writeblocks(SAFE_SEC, raw_16k)
        ms_raw = time.ticks_diff(time.ticks_ms(), t0)
        spd_raw = BENCH_TOTAL / 1048576 / (ms_raw / 1000)
        _free_dma(raw_16k)
    else:
        spd_raw = 0

    best = {"label": "", "size": 0, "spd": 0}

    for size in sizes:
        if size > BENCH_TOTAL:
            continue
        line = "{:>8s}".format(_sz(size))
        for label, n_bufs, gc_ctrl in modes:
            gc.collect()
            _, spd = run_write(size, n_bufs, gc_ctrl)
            line += "  {:>7.2f}MB/s".format(spd)
            if spd > best["spd"]:
                best = {"label": label, "size": size, "spd": spd}
        print(line)

    print()
    print("  " + "-" * 60)
    print("  raw 16KB 參考: {:.2f} MB/s".format(spd_raw))
    print("  最佳: {} @ {} = {:.2f} MB/s ({:.0f}% of raw)".format(
        best["label"], _sz(best["size"]), best["spd"],
        best["spd"] / spd_raw * 100 if spd_raw else 0))
    print()


def _sz(b):
    for u in ("B", "KB", "MB"):
        if b < 1024: return "{}{}".format(b, u)
        b //= 1024
    return "{}{}".format(b, "KB")


scan()
