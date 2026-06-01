"""64KB 直寫 DMA — 獨立測試，無前置配置消耗 DMA"""

import gc, time, _thread
_sd_lock = _thread.allocate_lock()
BENCH = 1024 * 1024


def run(buf_size=65536):
    from lib.sys_bus import bus
    sd = bus.get_service("sd_raw")
    ss = sd.info()[1]
    spc = buf_size // ss
    n_ops = BENCH // buf_size

    import heap_caps
    buf = heap_caps.malloc(buf_size, heap_caps.CAP_DMA)
    if buf is None:
        print("64KB DMA fail -> fallback 32KB")
        buf_size = 32768
        buf = heap_caps.malloc(buf_size, heap_caps.CAP_DMA)
        spc = buf_size // ss
        n_ops = BENCH // buf_size

    ok = buf is not None
    if not ok:
        print("DMA unavailable")
        return

    for i in range(buf_size):
        buf[i] = i & 0xFF

    t0 = time.ticks_ms()
    sec = 600000
    for _ in range(n_ops):
        with _sd_lock:
            sd.writeblocks(sec, buf)
        sec += spc
    ms = time.ticks_diff(time.ticks_ms(), t0)
    spd = BENCH / 1048576 / (ms / 1000)
    print("{} B  {} ops  {} ms  {:.2f} MB/s".format(buf_size, n_ops, ms, spd))
    heap_caps.free(buf)


run()
