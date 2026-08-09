# test/lvgl_direct_cpu1_test.py — LVGL rendering mode + CPU core 隔離/對比測試
#
# 目的:
#   1. 驗證 LVGL 能否在 CPU1 穩定渲染(消除 C→Python callback 內操作 SPI 的跨核問題)
#   2. 對比 PARTIAL vs DIRECT mode 的效能(frame time / flush time / 記憶體)
#
# 原理:
#   PARTIAL(CPU0 現狀): flush_cb 內做 __dereference__ + swap + 攢 bytes(C→Py callback 碰 SPI)
#   DIRECT(CPU1 測試):  flush_cb 只記 dirty area;show() 從自己 framebuffer 切(純 Py→C,跟 JPEG player 同構)
#
# 用法(soft reboot 後,boot.py 已跑完,確保 LVGL task 沒跑):
#   import lvgl_direct_cpu1_test
#   lvgl_direct_cpu1_test.benchmark(mode="partial", core=0)   # PARTIAL @ CPU0(基準)
#   lvgl_direct_cpu1_test.benchmark(mode="direct",  core=1)   # DIRECT @ CPU1(測試)
#   # 或跑全部對比:
#   lvgl_direct_cpu1_test.run_all()
#
# 判讀:
#   - 螢幕顯示 + 印出穩定 fps 數據 = 通過
#   - 崩潰/watchdog reset = 該模式/core 組合不穩定

import _thread, time, gc
import lvgl as lv
from lib.sys_bus import bus

_W = 320
_H = 240
_BPP = 2
_MADCTL = 0x60   # 橫屏(對齊 lvgl_init)

# LVGL render mode 常數(PARTIAL=0, DIRECT=1, FULL=2)
_RM_PARTIAL = 0
_RM_DIRECT = 1
_PARTIAL_LINES = 40   # PARTIAL draw buffer 行數(對齊 lvgl_init)

_BENCH_FRAMES = 60    # benchmark 採集幀數
_WARMUP_FRAMES = 10   # 熱身幀(不計)


class BenchDisp:
    """可切換 PARTIAL/DIRECT 的 LVGL display,帶效能採集。"""

    def __init__(self, mode=_RM_DIRECT):
        self.lcd = bus.get_service("lcd")
        if self.lcd is None:
            raise RuntimeError("lcd not on bus — 先跑 boot.py")
        self._bus = getattr(self.lcd, "_bus", None)
        if self._bus is None:
            raise RuntimeError("lcd service missing _bus (adapter)")

        self.W = _W
        self.H = _H
        self._dirty = []
        self.mode = mode

        # 效能採集
        self.stats_tick = []      # tick() 耗時(task_handler + render)
        self.stats_flush = []     # show() 送 SPI 耗時
        self.stats_dirty_per_frame = []  # 每幀 dirty region 數

        # 送 MADCTL(橫屏)
        self._bus.write_cmd_data(0x36, bytes([_MADCTL]))

        # LVGL 初始化(soft-reboot 殘留防護)
        if lv.is_initialized():
            try:
                lv.deinit()
            except Exception:
                pass
        lv.init()
        self._disp = lv.display_create(self.W, self.H)
        self._disp.set_color_format(18)  # RGB565

        if mode == _RM_DIRECT:
            # DIRECT:整個螢幕 framebuffer(PSRAM 優先)
            self._fb = self._alloc_fb(_W * _H * _BPP)
            self._disp.set_buffers(self._fb, None, len(self._fb), _RM_DIRECT)
            self._mode_name = "DIRECT"
        else:
            # PARTIAL:小 buffer(對齊 lvgl_init 的 40 行)
            self._fb = bytearray(_W * _PARTIAL_LINES * _BPP)
            self._disp.set_buffers(self._fb, None, len(self._fb), _RM_PARTIAL)
            self._mode_name = "PARTIAL"

        self._disp.set_flush_cb(self._flush_cb)
        print("[bench] {}x{} {} mode fb={}KB".format(
            self.W, self.H, self._mode_name, len(self._fb) // 1024))

    def _alloc_fb(self, size):
        try:
            import heap_caps
            buf = heap_caps.malloc(size, heap_caps.CAP_SPIRAM)
            if buf is not None:
                print("[bench] fb from PSRAM")
                return buf
        except Exception:
            pass
        print("[bench] fb from heap")
        return bytearray(size)

    def _flush_cb(self, disp_drv, area, color_p):
        """DIRECT:只記 dirty area。PARTIAL:記 dirty + 攢像素(對齊現狀)。"""
        if self.mode == _RM_DIRECT:
            self._dirty.append((area.x1, area.y1, area.x2, area.y2))
        else:
            # PARTIAL:必須 dereference + swap(跟現有 lvgl_init 一樣)
            w = area.x2 - area.x1 + 1
            h = area.y2 - area.y1 + 1
            data = color_p.__dereference__(w * h * _BPP)
            lv.draw_sw_rgb565_swap(data, w * h)
            self._dirty.append((area.x1, area.y1, area.x2, area.y2, bytes(data)))
        disp_drv.flush_ready()

    def tick(self):
        t0 = time.ticks_us()
        lv.tick_inc(5)
        lv.task_handler()
        lv.refr_now(self._disp)
        self.stats_tick.append(time.ticks_diff(time.ticks_us(), t0))

    def take(self):
        rects = self._dirty
        self._dirty = []
        return rects

    def show(self, *rect):
        """送 dirty region 到 LCD。DIRECT 從 fb 切,PARTIAL 用 callback 攢的 data。"""
        t0 = time.ticks_us()
        if self.mode == _RM_DIRECT:
            x1, y1, x2, y2 = rect
            w = x2 - x1 + 1
            h = y2 - y1 + 1
            off = (y1 * self.W + x1) * _BPP
            stride = self.W * _BPP
            self._bus.set_window(x1, y1, x2, y2)
            if w == self.W:
                chunk = memoryview(self._fb)[off:off + w * h * _BPP]
                self._bus.write_data_async(chunk)
            else:
                row_len = w * _BPP
                for row in range(h):
                    row_off = off + row * stride
                    self._bus.write_data_async(
                        memoryview(self._fb)[row_off:row_off + row_len])
            self._bus.flush()
        else:
            x1, y1, x2, y2, data = rect
            self._bus.set_window(x1, y1, x2, y2)
            self._bus.write_data_async(data)
            self._bus.flush()
        self.stats_flush.append(time.ticks_diff(time.ticks_us(), t0))


# ══════════════════════════════════════════════════════
# 測試 UI + benchmark 邏輯
# ══════════════════════════════════════════════════════

_label = None
_frame_count = 0


def _build_ui(plat):
    """簡單畫面:色塊背景 + 計數文字(每幀更新觸發重繪)。"""
    global _label
    scr = lv.obj(None)
    scr.set_style_bg_color(lv.color_hex(0x1A73E8), 0)
    title = lv.label(scr)
    title.set_text("{} @ CPU?".format(plat._mode_name))
    title.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
    _label = lv.label(scr)
    _label.set_text("0")
    _label.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
    try:
        title.set_pos(80, 90)
        _label.set_pos(140, 130)
    except Exception:
        pass
    lv.screen_load(scr)


def _loop(plat, frames):
    """跑 N 幀,回傳是否成功(沒崩)。"""
    global _frame_count
    _frame_count = 0
    try:
        for _ in range(frames):
            # 更新文字(觸發重繪)
            _frame_count += 1
            if _label:
                _label.set_text(str(_frame_count))

            plat.tick()
            dirty = plat.take()
            plat.stats_dirty_per_frame.append(len(dirty))
            for rect in dirty:
                plat.show(*rect)
            time.sleep_ms(5)
        return True
    except Exception as e:
        print("[bench] ❌ loop crashed: {}".format(e))
        return False


def _print_stats(plat, mode_name, core, ok):
    """列印 benchmark 統計。"""
    print("\n" + "=" * 55)
    print(" {} @ CPU{}  {}".format(mode_name, core, "✅ OK" if ok else "❌ CRASHED"))
    print("=" * 55)

    if not ok:
        print("  (崩潰,無數據)\n")
        return

    st = plat.stats_tick
    sf = plat.stats_flush
    sd = plat.stats_dirty_per_frame
    n = len(st)

    if n == 0:
        print("  (無採集數據)\n")
        return

    # 跳過熱身(前 _WARMUP_FRAMES 幀)
    warmup = min(_WARMUP_FRAMES, n)
    st2 = st[warmup:]
    sf2 = sf[warmup:]
    sd2 = sd[warmup:]
    n2 = len(st2)
    if n2 == 0:
        st2, sf2, sd2, n2 = st, sf, sd, n

    avg_tick = sum(st2) // n2
    max_tick = max(st2)
    avg_flush = sum(sf2) // len(sf2) if sf2 else 0
    max_flush = max(sf2) if sf2 else 0
    avg_dirty = sum(sd2) // len(sd2) if sd2 else 0
    frame_us = avg_tick + avg_flush
    fps = 1000000 // frame_us if frame_us > 0 else 0

    print("  frames sampled : {} (warmup {} excluded)".format(n2, warmup))
    print("  tick avg/max   : {} / {} us  (task_handler + render + refr_now)".format(avg_tick, max_tick))
    print("  flush avg/max  : {} / {} us  (show: set_window + DMA + flush)".format(avg_flush, max_flush))
    print("  dirty/frame    : {} regions".format(avg_dirty))
    print("  frame time     : {} us  (tick + flush)".format(frame_us))
    print("  est. fps       : {}".format(fps))
    print("  free mem       : {} KB\n".format(gc.mem_free() // 1024))


def benchmark(mode="direct", core=1, frames=_BENCH_FRAMES):
    """單次 benchmark。
    mode = "partial" | "direct"
    core = 0 | 1
    """
    rm = _RM_PARTIAL if mode == "partial" else _RM_DIRECT
    mode_name = "PARTIAL" if rm == _RM_PARTIAL else "DIRECT"

    print("\n[bench] starting: {} @ CPU{}, {} frames...".format(mode_name, core, frames))
    gc.collect()
    print("[bench] free mem start: {} KB".format(gc.mem_free() // 1024))

    result = {"ok": False}

    def _run():
        try:
            plat = BenchDisp(rm)
            _build_ui(plat)
            time.sleep_ms(200)  # 讓畫面穩定
            ok = _loop(plat, frames)
            result["plat"] = plat
            result["ok"] = ok
        except Exception as e:
            print("[bench] ❌ init/run failed: {}".format(e))
            result["ok"] = False
            result["err"] = str(e)

    if core == 1:
        # CPU1:跑在獨立 thread
        _thread.start_new_thread(_run, ())
        # 等 thread 跑完(最多 frames * 50ms + buffer)
        timeout_ms = frames * 50 + 5000
        waited = 0
        while not result.get("plat") and not result.get("err") and waited < timeout_ms:
            time.sleep_ms(50)
            waited += 50
        time.sleep_ms(500)  # 讓 thread 結束統計
    else:
        # CPU0:直接跑
        _run()

    plat = result.get("plat")
    ok = result.get("ok", False)
    if plat:
        _print_stats(plat, mode_name, core, ok)
    else:
        print("\n[bench] ❌ {} @ CPU{} failed before stats\n".format(mode_name, core))
    return ok


def run_all():
    """跑全部對比:PARTIAL@CPU0 vs DIRECT@CPU0 vs DIRECT@CPU1。
    PARTIAL@CPU1 不測(已知 callback 跨核崩潰)。"""
    print("\n" + "█" * 55)
    print("█ LVGL rendering mode + CPU core 全對比")
    print("█" * 55)

    results = {}

    # 1. PARTIAL @ CPU0(現狀基準)
    results["PARTIAL@CPU0"] = benchmark("partial", 0)
    time.sleep_ms(1000)

    # 2. DIRECT @ CPU0(確認 DIRECT mode 本身可行)
    results["DIRECT@CPU0"] = benchmark("direct", 0)
    time.sleep_ms(1000)

    # 3. DIRECT @ CPU1(核心測試:能否跨核)
    results["DIRECT@CPU1"] = benchmark("direct", 1)

    # ── 匯總 ──
    print("\n" + "█" * 55)
    print("█ 匯總")
    print("█" * 55)
    for name, ok in results.items():
        print("  {:16s} {}".format(name, "✅ 通過" if ok else "❌ 崩潰"))
    print()


if __name__ == "__main__":
    run_all()
