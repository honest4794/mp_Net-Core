# test/lvgl_direct_fullui_nothread.py — DIRECT + 完整 UI,無 thread(對照)
#
# 所有 thread + 完整 UI 都崩。本測試:同樣 DIRECT + 完整 UI,但主執行緒跑。
# 如果通過 → 鐵證:問題是 thread + 完整 UI,不是 mode/buffer。
#
# 用法:
#   import lvgl_direct_fullui_nothread as t
#   t.run()

import time, gc
import lvgl as lv
from lib.sys_bus import bus

_W = 320
_H = 240
_BPP = 2
_MADCTL = 0x60
_RM_DIRECT = 1


def run():
    print("=" * 55)
    print("[test] DIRECT + 完整 UI,無 thread(主執行緒)")
    print("=" * 55)

    gc.collect()
    bus.shared["engine_run"] = True

    try:
        lcd = bus.get_service("lcd")
        bus_obj = getattr(lcd, "_bus")
        dirty = []

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

        from ui.lvgl import ui_common, app
        ui_common.W = _W
        ui_common.H = _H
        ui_common.init_fonts()
        import ui.lvgl.page  # noqa
        app.build_all()

        from lib.hw_manager import get_input
        app.init({
            "tick": lambda: (lv.tick_inc(5), lv.task_handler(), lv.refr_now(disp)),
            "take": lambda: (dirty[:] , dirty.clear())[0],
            "show": lambda x1, y1, x2, y2: _show(bus_obj, fb, x1, y1, x2, y2),
            "enc_delta": lambda: get_input("enc", idx=0) or 0,
            "confirm": lambda: get_input("pin", key="encC") == 0,
            "exit": lambda: get_input("pin", key="btn") == 0,
        })
        app.go("launcher")
        print("[direct-nothread] setup done, free: {} KB".format(gc.mem_free() // 1024))

        for i in range(50):
            app.step()
            if i % 10 == 0:
                print("[direct-nothread]   frame {}".format(i))

        print("[direct-nothread] ✅ 50 幀完成 — 無 thread 通過!")
        bus.shared["engine_run"] = False
    except Exception as e:
        print("[direct-nothread] ❌ error: {}".format(e))
        bus.shared["engine_run"] = False


def _show(bus_obj, fb, x1, y1, x2, y2):
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


if __name__ == "__main__":
    run()
