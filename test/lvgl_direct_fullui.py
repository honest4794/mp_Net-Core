# test/lvgl_direct_fullui.py — DIRECT mode + 完整 UI @ CPU1
#
# ring buffer(PARTIAL)也崩 → 不是 buffer 問題。
# benchmark DIRECT@CPU1 通過(簡單 UI)→ DIRECT 可能解決。
# 但 DIRECT + 完整 UI + thread 沒測過。
#
# 本測試:DIRECT mode + 完整 UI(4 screen + update)+ thread。
#
# 用法:
#   import lvgl_direct_fullui as t
#   t.run()

import _thread, time, gc
import lvgl as lv
from lib.sys_bus import bus

_W = 320
_H = 240
_BPP = 2
_MADCTL = 0x60
_RM_DIRECT = 1


def _cpu0_sleep():
    while bus.shared.get("engine_run", True):
        time.sleep_ms(5)


def _cpu1_run(result):
    """CPU1:DIRECT mode + 完整 UI + app.step。"""
    try:
        lcd = bus.get_service("lcd")
        bus_obj = getattr(lcd, "_bus")
        dirty = []

        # PSRAM framebuffer
        try:
            import heap_caps
            fb = heap_caps.malloc(_W * _H * _BPP, heap_caps.CAP_SPIRAM)
            if fb is None:
                fb = bytearray(_W * _H * _BPP)
        except Exception:
            fb = bytearray(_W * _H * _BPP)

        bus_obj.write_cmd_data(0x36, bytes([_MADCTL]))
        lv.init()
        disp = lv.display_create(_W, _H)
        disp.set_color_format(18)
        disp.set_buffers(fb, None, len(fb), _RM_DIRECT)

        def flush_cb(disp_drv, area, color_p):
            dirty.append((area.x1, area.y1, area.x2, area.y2))
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

        def show(x1, y1, x2, y2):
            w = x2 - x1 + 1
            h = y2 - y1 + 1
            off = (y1 * _W + x1) * _BPP
            stride = _W * _BPP
            bus_obj.set_window(x1, y1, x2, y2)
            if w == _W:
                bus_obj.write_data_async(memoryview(fb)[off:off + w * h * _BPP])
            else:
                row_len = w * _BPP
                for row in range(h):
                    ro = off + row * stride
                    bus_obj.write_data_async(memoryview(fb)[ro:ro + row_len])
            bus_obj.flush()

        # 完整 UI
        from ui.lvgl import ui_common, app
        ui_common.W = _W
        ui_common.H = _H
        ui_common.init_fonts()
        import ui.lvgl.page  # noqa
        app.build_all()

        from lib.hw_manager import get_input
        app.init({
            "tick": tick, "take": take, "show": show,
            "enc_delta": lambda: get_input("enc", idx=0) or 0,
            "confirm": lambda: get_input("pin", key="encC") == 0,
            "exit": lambda: get_input("pin", key="btn") == 0,
        })
        app.go("launcher")
        print("[direct] setup done, free: {} KB".format(gc.mem_free() // 1024))

        for i in range(100):
            app.step()
            if i % 20 == 0:
                print("[direct]   frame {} free: {}KB".format(i, gc.mem_free() // 1024))

        result["ok"] = True
        print("[direct] ✅ 100 幀完成")
    except Exception as e:
        result["ok"] = False
        result["err"] = str(e)
        print("[direct] ❌ error: {}".format(e))


def run():
    print("=" * 55)
    print("[test] DIRECT mode + 完整 UI @ CPU1(thread)")
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
    print("\n[result] {}".format(
        "✅ 通過 — DIRECT + 完整 UI 可跑 CPU1" if ok else "❌ 崩潰 — DIRECT 也救不了"))


if __name__ == "__main__":
    run()
