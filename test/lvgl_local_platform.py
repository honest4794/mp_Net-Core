# test/lvgl_local_platform.py — 全本地 platform(take/show/flush 都用局部變數)
#
# closure tick 也崩 → 不是 tick 的問題。
# L0-L4 用局部 dirty list + 局部 bus_obj → 通過。
# app.step() 用 LvglDisp._dirty(物件成員) + LvglDisp.show(bound method) → 崩。
#
# 本測試:thread 裡跑完整 app.step(UI + 輸入 + update),
# 但 platform 的 take/show 改用局部 dirty list + 局部 bus_obj(像 L4)。
# flush_cb 也寫進局部 dirty(不碰 self._dirty)。
#
# 用法:
#   import lvgl_local_platform as t
#   t.run()

import _thread, time, gc
import lvgl as lv
from lib.sys_bus import bus


def _cpu0_sleep():
    while bus.shared.get("engine_run", True):
        time.sleep_ms(5)


def _cpu1_run(result):
    """CPU1:完整 LVGL UI,但 platform 全用局部變數。"""
    try:
        lcd = bus.get_service("lcd")
        bus_obj = getattr(lcd, "_bus")
        dirty = []  # 局部 dirty(不碰 LvglDisp._dirty)

        # LVGL init(像 L4,不經 LvglDisp)
        bus_obj.write_cmd_data(0x36, bytes([0x60]))
        lv.init()
        disp = lv.display_create(320, 240)
        disp.set_color_format(18)
        buf = bytearray(320 * 40 * 2)
        disp.set_buffers(buf, None, len(buf), 0)  # PARTIAL

        # flush_cb → 局部 dirty(像 L4)
        def flush_cb(disp_drv, area, color_p):
            w = area.x2 - area.x1 + 1
            h = area.y2 - area.y1 + 1
            data = color_p.__dereference__(w * h * 2)
            lv.draw_sw_rgb565_swap(data, w * h)
            dirty.append((area.x1, area.y1, area.x2, area.y2, bytes(data)))
            disp_drv.flush_ready()
        disp.set_flush_cb(flush_cb)

        # tick → 局部 disp(像 L4)
        def tick():
            lv.tick_inc(5)
            lv.task_handler()
            lv.refr_now(disp)

        # take → 局部 dirty
        def take():
            rects = dirty[:]
            dirty.clear()
            return rects

        # show → 局部 bus_obj
        def show(x1, y1, x2, y2, data):
            bus_obj.set_window(x1, y1, x2, y2)
            bus_obj.write_data_async(data)
            bus_obj.flush()

        # 字型 + 頁面 + UI(完整 board 體驗)
        from ui.lvgl import ui_common, app
        ui_common.W = 320
        ui_common.H = 240
        ui_common.init_fonts()
        import ui.lvgl.page  # noqa
        app.build_all()

        # 輸入(像 board._make_inputs,讀 hw_manager 快照)
        from lib.hw_manager import get_input
        def enc_delta():
            return get_input("enc", idx=0) or 0
        def confirm():
            return get_input("pin", key="encC") == 0
        def exit_pressed():
            return get_input("pin", key="btn") == 0

        # app.init 用全局部 platform
        app.init({
            "tick": tick,
            "take": take,
            "show": show,
            "enc_delta": enc_delta,
            "confirm": confirm,
            "exit": exit_pressed,
        })
        app.go("launcher")
        print("[local] setup done, free: {} KB".format(gc.mem_free() // 1024))

        # 跑 app.step(完整 UI + 輸入 + update)
        for i in range(100):
            app.step()
            if i % 20 == 0:
                print("[local]   frame {}".format(i))

        result["ok"] = True
        print("[local] ✅ 100 幀完成")
    except Exception as e:
        result["ok"] = False
        result["err"] = str(e)
        print("[local] ❌ error: {}".format(e))


def run():
    print("=" * 55)
    print("[test] 全局部 platform + 完整 UI + app.step")
    print("[test] flush_cb/take/show/tick 全用局部變數(像 L4)")
    print("[test] 但 app.step 含完整 UI + 輸入 + update")
    print("=" * 55)

    gc.collect()
    bus.shared["engine_run"] = True
    result = {"ok": None}

    _thread.start_new_thread(_cpu0_sleep, ())
    time.sleep_ms(100)
    _thread.start_new_thread(_cpu1_run, (result,))

    waited = 0
    while result["ok"] is None and waited < 20000:
        time.sleep_ms(50)
        waited += 50

    bus.shared["engine_run"] = False
    time.sleep_ms(200)

    ok = result.get("ok", False)
    print("\n[result] {}".format("✅ 通過 — app.step 可在 thread 跑" if ok else "❌ 崩潰"))


if __name__ == "__main__":
    run()
