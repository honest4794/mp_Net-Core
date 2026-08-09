# test/lvgl_step_breakdown.py — app.step() 哪個部分導致 thread 崩潰
#
# 全局部 platform 也崩 → 不是 LvglDisp 問題。
# L4(不操作 widget)通過,local_platform(操作 widget via update)崩。
#
# app.step() 的組成:
#   1. enc_delta/confirm/exit (讀 bus.shared hw_manager)
#   2. on_enc/on_confirm/on_exit (操作 LVGL widget: nav, go)
#   3. update() (讀 bus.shared + 操作 LVGL widget: set_text 等)
#   4. tick() (task_handler + refr_now → flush_cb)
#   5. take() + show() (送 SPI)
#
# 測試:逐步加入 1→5,找出哪步導致崩潰。
#
# 用法:
#   import lvgl_step_breakdown as t
#   t.run()

import _thread, time, gc
import lvgl as lv
from lib.sys_bus import bus


def _cpu0_sleep():
    while bus.shared.get("engine_run", True):
        time.sleep_ms(5)


def _build_local_platform():
    """建全局部 platform(像 local_platform 測試)。"""
    lcd = bus.get_service("lcd")
    bus_obj = getattr(lcd, "_bus")
    dirty = []

    bus_obj.write_cmd_data(0x36, bytes([0x60]))
    lv.init()
    disp = lv.display_create(320, 240)
    disp.set_color_format(18)
    buf = bytearray(320 * 40 * 2)
    disp.set_buffers(buf, None, len(buf), 0)

    def flush_cb(disp_drv, area, color_p):
        w = area.x2 - area.x1 + 1
        h = area.y2 - area.y1 + 1
        data = color_p.__dereference__(w * h * 2)
        lv.draw_sw_rgb565_swap(data, w * h)
        dirty.append((area.x1, area.y1, area.x2, area.y2, bytes(data)))
        disp_drv.flush_ready()
    disp.set_flush_cb(flush_cb)

    def tick():
        lv.tick_inc(5)
        lv.task_handler()
        lv.refr_now(disp)

    def take():
        r = dirty[:]
        dirty.clear()
        return r

    def show(x1, y1, x2, y2, data):
        bus_obj.set_window(x1, y1, x2, y2)
        bus_obj.write_data_async(data)
        bus_obj.flush()

    from lib.hw_manager import get_input
    def enc_delta():
        return get_input("enc", idx=0) or 0
    def confirm():
        return get_input("pin", key="encC") == 0
    def exit_pressed():
        return get_input("pin", key="btn") == 0

    return {
        "tick": tick, "take": take, "show": show,
        "enc_delta": enc_delta, "confirm": confirm, "exit": exit_pressed,
    }


def _setup_ui(plat):
    """完整 UI build + app.init。"""
    from ui.lvgl import ui_common, app
    ui_common.W = 320
    ui_common.H = 240
    ui_common.init_fonts()
    import ui.lvgl.page  # noqa
    app.build_all()
    app.init(plat)
    app.go("launcher")


def _make_step_variant(plat, variant):
    """產生不同版本的 step 函式。"""
    from ui.lvgl import app

    if variant == "tick_only":
        # 只 tick + take + show(不讀輸入,不碰 widget)
        def step():
            plat["tick"]()
            for r in plat["take"]():
                plat["show"](*r)
        return step

    elif variant == "input_tick":
        # 輸入 + tick + show(讀 hw_manager,但不碰 widget)
        def step():
            plat["enc_delta"]()
            plat["confirm"]()
            plat["exit"]()
            plat["tick"]()
            for r in plat["take"]():
                plat["show"](*r)
        return step

    elif variant == "update_tick":
        # update + tick + show(碰 widget: set_text 等)
        def step():
            m = app._page()
            if hasattr(m, "update"):
                m.update(0)
            plat["tick"]()
            for r in plat["take"]():
                plat["show"](*r)
        return step

    elif variant == "full_step":
        # 完整 app.step(輸入 + update + tick + show)
        return app.step


def _cpu1_run(variant, result):
    """CPU1:完整 UI + 指定 step 變體。"""
    try:
        plat = _build_local_platform()
        _setup_ui(plat)
        step_fn = _make_step_variant(plat, variant)
        print("[{}] setup done, free: {} KB".format(variant, gc.mem_free() // 1024))

        for i in range(50):
            step_fn()
            if i % 10 == 0:
                print("[{}]   frame {}".format(variant, i))

        result["ok"] = True
        print("[{}] ✅ 50 幀完成".format(variant))
    except Exception as e:
        result["ok"] = False
        result["err"] = str(e)
        print("[{}] ❌ error: {}".format(variant, e))


def _test(variant):
    print("\n" + "=" * 55)
    print("[test] step={} (thread)".format(variant))
    print("=" * 55)
    gc.collect()
    bus.shared["engine_run"] = True
    result = {"ok": None}

    _thread.start_new_thread(_cpu0_sleep, ())
    time.sleep_ms(100)
    _thread.start_new_thread(_cpu1_run, (variant, result))

    waited = 0
    while result["ok"] is None and waited < 15000:
        time.sleep_ms(50)
        waited += 50

    bus.shared["engine_run"] = False
    time.sleep_ms(200)
    ok = result.get("ok", False)
    print("[test] {} → {}".format(variant, "✅ 通過" if ok else "❌ 崩潰"))
    return ok


def run():
    print("\n" + "█" * 55)
    print("█ app.step() 拆解:哪部分導致 thread 崩潰")
    print("█" * 55)

    tests = [
        ("tick_only", "只 tick+show(不碰widget)"),
        ("input_tick", "輸入+tick+show(讀hw不碰widget)"),
        ("update_tick", "update+tick+show(碰widget)"),
        ("full_step", "完整step(對照)"),
    ]

    results = {}
    for variant, desc in tests:
        results[variant] = _test(variant)
        if not results[variant]:
            print("\n[!] {} 崩潰 — 觸發點: {}".format(variant, desc))
            # 不 break,繼續測下一個(每個獨立)
        time.sleep_ms(2000)
        gc.collect()

    print("\n" + "█" * 55)
    for variant, desc in tests:
        print("  {:<12s} {:<28s} {}".format(
            variant, desc, "✅" if results[variant] else "❌ 崩潰"))
    print()


if __name__ == "__main__":
    run()
