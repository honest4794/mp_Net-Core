# test/lvgl_partial_cpu1_strategies.py — PARTIAL mode @ CPU1 策略對比測試
#
# 目的:找出讓 PARTIAL mode 在 CPU1 穩定跑的方法(CPU0 同時有採樣緒)。
#
# 已知:
#   - PARTIAL @ CPU1, CPU0 無 thread → ✅ 穩定(isolated 測試)
#   - PARTIAL @ CPU1, CPU0 有 thread → ❌ 崩潰(board.run 測試)
#   - DIRECT @ CPU1, CPU0 有 thread → ✅ 穩定(benchmark)
#
# 假設:崩潰跟 _flush_cb 裡的操作有關。測試不同 callback 策略:
#   A. 現狀(bytes 拷貝 + 外部 show)— 已知崩
#   B. callback 直接送 SPI + wait DMA(不分配記憶體)
#   C. callback 用預分配 ring buffer(避免 bytes 分配)
#
# 用法(soft reboot 後,boot.py 已跑完):
#   import lvgl_partial_cpu1_strategies as t
#   t.test_strategy("B")   # 測策略 B
#   t.test_strategy("C")   # 測策略 C
#   t.run_all()            # 依序測全部

import _thread, time, gc
import lvgl as lv
from lib.sys_bus import bus

_W = 320
_H = 240
_BPP = 2
_MADCTL = 0x60
_LINES = 40


def _get_hw():
    """取硬體物件指標(只讀一次 service dict)。"""
    lcd = bus.get_service("lcd")
    if lcd is None:
        raise RuntimeError("lcd not on bus")
    bus_obj = getattr(lcd, "_bus", None)
    if bus_obj is None:
        raise RuntimeError("lcd missing _bus")
    enc_list = bus.get_service("enc_list") or []
    enc = enc_list[0] if enc_list else None
    pin_by_label = bus.get_service("pin_by_label") or {}
    return bus_obj, enc, pin_by_label.get("encC"), pin_by_label.get("btn")


def _cpu0_sampler():
    """CPU0 採樣緒 — 模擬實際環境(CPU0 有 thread 在跑)。"""
    from lib.hw_manager import sample_inputs
    sample_inputs()
    while bus.shared.get("engine_run", True):
        sample_inputs()
        time.sleep_ms(5)


# ══════════════════════════════════════════════════════
# 策略 A:現狀(bytes 拷貝)— 已知崩,作對照
# ══════════════════════════════════════════════════════

class StrategyA:
    """bytes() 拷貝 + 外部 show(現狀)。"""
    name = "A: bytes() copy + external show"

    def __init__(self, bus_obj):
        self._bus = bus_obj
        self._dirty = []
        self._frame = 0

    def flush_cb(self, disp_drv, area, color_p):
        w = area.x2 - area.x1 + 1
        h = area.y2 - area.y1 + 1
        data = color_p.__dereference__(w * h * _BPP)
        lv.draw_sw_rgb565_swap(data, w * h)
        self._dirty.append((area.x1, area.y1, area.x2, area.y2, bytes(data)))
        disp_drv.flush_ready()

    def after_tick(self):
        while self._dirty:
            x1, y1, x2, y2, data = self._dirty.pop(0)
            self._bus.set_window(x1, y1, x2, y2)
            self._bus.write_data_async(data)
            self._bus.flush()


# ══════════════════════════════════════════════════════
# 策略 B:callback 裡直接送 SPI + wait DMA(不分配記憶體)
# ══════════════════════════════════════════════════════

class StrategyB:
    """callback 裡直接送 SPI,wait DMA 完成後才 flush_ready。
    不做 bytes() 拷貝 — __dereference__ 的 memoryview 直接丟給 SPI。
    flush_ready 延後到 DMA 完成,確保 LVGL 不提前覆蓋 buffer。"""
    name = "B: direct SPI in callback (no alloc)"

    def __init__(self, bus_obj):
        self._bus = bus_obj
        self._frame = 0

    def flush_cb(self, disp_drv, area, color_p):
        w = area.x2 - area.x1 + 1
        h = area.y2 - area.y1 + 1
        data = color_p.__dereference__(w * h * _BPP)
        lv.draw_sw_rgb565_swap(data, w * h)
        # 直接送 SPI(不拷貝,不分配)
        self._bus.set_window(area.x1, area.y1, area.x2, area.y2)
        tid = self._bus.write_data_async(data)
        if tid is not None:
            self._bus.wait(tid)
        self._bus.flush()
        # DMA 完成後才 flush_ready(LVGL 才會重用 buffer)
        disp_drv.flush_ready()

    def after_tick(self):
        pass  # 已在 callback 裡送完


# ══════════════════════════════════════════════════════
# 策略 C:預分配 ring buffer(避免 bytes 分配)
# ══════════════════════════════════════════════════════

class StrategyC:
    """用預分配 ring buffer 取代 bytes() — 避免 callback 裡分配記憶體。
    ring buffer 預先建好,copy 到裡面,不觸發 GC。"""
    name = "C: prealloc ring buffer"

    def __init__(self, bus_obj):
        self._bus = bus_obj
        self._dirty = []
        self._frame = 0
        self._ring_n = 8
        self._ring = [bytearray(_W * _LINES * _BPP) for _ in range(self._ring_n)]
        self._ring_idx = 0

    def flush_cb(self, disp_drv, area, color_p):
        w = area.x2 - area.x1 + 1
        h = area.y2 - area.y1 + 1
        n = w * h * _BPP
        data = color_p.__dereference__(n)
        lv.draw_sw_rgb565_swap(data, w * h)
        # 拷貝到預分配 buffer(不分配新物件)
        buf = self._ring[self._ring_idx]
        buf[:n] = data
        self._dirty.append((area.x1, area.y1, area.x2, area.y2, n, self._ring_idx))
        self._ring_idx = (self._ring_idx + 1) % self._ring_n
        disp_drv.flush_ready()

    def after_tick(self):
        while self._dirty:
            x1, y1, x2, y2, n, idx = self._dirty.pop(0)
            buf = self._ring[idx]
            self._bus.set_window(x1, y1, x2, y2)
            self._bus.write_data_async(memoryview(buf)[:n])
            self._bus.flush()


# ══════════════════════════════════════════════════════
# 測試框架
# ══════════════════════════════════════════════════════

STRATEGIES = {"A": StrategyA, "B": StrategyB, "C": StrategyC}


def _run_on_cpu1(strategy_cls, bus_obj, frames, result):
    """CPU1 主迴圈。"""
    try:
        strategy = strategy_cls(bus_obj)

        # MADCTL + LVGL init
        bus_obj.write_cmd_data(0x36, bytes([_MADCTL]))
        lv.init()
        disp = lv.display_create(_W, _H)
        disp.set_color_format(18)
        buf = bytearray(_W * _LINES * _BPP)
        disp.set_buffers(buf, None, len(buf), 0)  # PARTIAL
        disp.set_flush_cb(strategy.flush_cb)

        # 簡單 UI
        scr = lv.obj(None)
        scr.set_style_bg_color(lv.color_hex(0x1A2B3C), 0)
        label = lv.label(scr)
        label.set_text(strategy.name[:20])
        label.set_style_text_color(lv.color_hex(0x4FC3F7), 0)
        counter = lv.label(scr)
        counter.set_text("0")
        counter.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
        lv.screen_load(scr)
        time.sleep_ms(200)

        t0 = time.ticks_ms()
        for i in range(frames):
            counter.set_text(str(i))
            lv.tick_inc(5)
            lv.task_handler()
            lv.refr_now(disp)
            strategy.after_tick()
            strategy._frame += 1
            time.sleep_ms(5)

        dt = time.ticks_diff(time.ticks_ms(), t0)
        result["ok"] = True
        result["fps"] = frames * 1000 // dt if dt > 0 else 0
        result["frame"] = strategy._frame
    except Exception as e:
        result["ok"] = False
        result["err"] = str(e)


def test_strategy(strategy_key, frames=300):
    """測單一策略:CPU0 採樣緒 + CPU1 跑 LVGL。"""
    cls = STRATEGIES[strategy_key]
    print("\n" + "=" * 55)
    print("[test] 策略 {} — CPU0 採樣緒 + CPU1 PARTIAL".format(strategy_key))
    print("[test] {} ({} 幀)".format(cls.name, frames))
    print("=" * 55)

    bus_obj, enc, encC, btn = _get_hw()
    gc.collect()
    print("[test] free mem: {} KB".format(gc.mem_free() // 1024))

    bus.shared["engine_run"] = True
    result = {"ok": None}

    # CPU0 採樣緒
    _thread.start_new_thread(_cpu0_sampler, ())
    time.sleep_ms(100)  # 讓採樣緒先跑

    # CPU1 跑策略
    _thread.start_new_thread(_run_on_cpu1, (cls, bus_obj, frames, result))

    # 等 CPU1 跑完(或崩)
    waited = 0
    timeout = frames * 60 + 5000
    while result["ok"] is None and waited < timeout:
        time.sleep_ms(50)
        waited += 50

    bus.shared["engine_run"] = False
    time.sleep_ms(200)

    if result["ok"]:
        print("[test] ✅ {} — {} 幀, {} fps".format(
            strategy_key, result.get("frame", 0), result.get("fps", 0)))
    else:
        print("[test] ❌ {} — 崩潰: {}".format(strategy_key, result.get("err", "timeout")))

    return result.get("ok", False)


def run_all():
    """依序測 B 和 C（A 已知崩,只測新的）。"""
    print("\n" + "█" * 55)
    print("█ PARTIAL mode @ CPU1 策略對比(CPU0 有採樣緒)")
    print("█" * 55)

    results = {}
    for key in ("B", "C"):
        results[key] = test_strategy(key)
        time.sleep_ms(1000)
        gc.collect()

    # 也測 A 作對照(確認它確實崩)
    print("\n[test] (對照) 策略 A — 預期崩潰")
    results["A"] = test_strategy("A", frames=100)

    print("\n" + "█" * 55)
    print("█ 匯總")
    print("█" * 55)
    for key in ("A", "B", "C"):
        cls = STRATEGIES[key]
        ok = results[key]
        print("  策略 {} {:<40s} {}".format(
            key, cls.name[:40], "✅ 通過" if ok else "❌ 崩潰"))
    print()


if __name__ == "__main__":
    run_all()
