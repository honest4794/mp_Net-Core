# test/lvgl_ring_fullui.py — ring buffer + 完整 UI @ CPU1
#
# 你的方案:callback 把 data 寫進預分配 ring buffer(不分配 bytes),
#           callback 外面送 TFT。犧牲一幀延遲(DMA pipeline)。
# 之前策略 C 通過(簡單 UI),但完整 UI 沒測過。
# 本測試:完整 UI(4 screen + update)+ ring buffer + thread。
#
# 用法:
#   import lvgl_ring_fullui as t
#   t.run()

import _thread, time, gc
import lvgl as lv
from lib.sys_bus import bus

_W = 320
_H = 240
_BPP = 2
_MADCTL = 0x60
_LINES = 40
_RING_N = 8   # ring buffer 數量


def _cpu0_sleep():
    while bus.shared.get("engine_run", True):
        time.sleep_ms(5)


def _cpu1_run(result):
    """CPU1:完整 UI + ring buffer flush_cb + app.step。"""
    try:
        lcd = bus.get_service("lcd")
        bus_obj = getattr(lcd, "_bus")

        # 預分配 ring buffer(避免 callback 裡 bytes() 分配)
        ring = [bytearray(_W * _LINES * _BPP) for _ in range(_RING_N)]
        ring_idx = [0]
        dirty = []  # (x1,y1,x2,y2,n,ring_idx)

        bus_obj.write_cmd_data(0x36, bytes([_MADCTL]))
        lv.init()
        disp = lv.display_create(_W, _H)
        disp.set_color_format(18)
        buf = bytearray(_W * _LINES * _BPP)
        disp.set_buffers(buf, None, len(buf), 0)  # PARTIAL

        def flush_cb(disp_drv, area, color_p):
            w = area.x2 - area.x1 + 1
            h = area.y2 - area.y1 + 1
            n = w * h * _BPP
            data = color_p.__dereference__(n)
            lv.draw_sw_rgb565_swap(data, w * h)
            # 拷貝到 ring buffer(不分配新物件)
            buf_dst = ring[ring_idx[0]]
            buf_dst[:n] = data
            dirty.append((area.x1, area.y1, area.x2, area.y2, n, ring_idx[0]))
            ring_idx[0] = (ring_idx[0] + 1) % _RING_N
            disp_drv.flush_ready()

        disp.set_flush_cb(flush_cb)

        # tick:只 task_handler(refr_now 會觸發 flush_cb)
        def tick():
            lv.tick_inc(5)
            lv.task_handler()
            lv.refr_now(disp)

        def take():
            r = dirty[:]
            dirty.clear()
            return r

        def show(x1, y1, x2, y2, n, idx):
            bus_obj.set_window(x1, y1, x2, y2)
            bus_obj.write_data_async(memoryview(ring[idx])[:n])
            bus_obj.flush()

        # 完整 UI
        from ui.lvgl import ui_common, app
        ui_common.W = _W
        ui_common.H = _H
        ui_common.init_fonts()
        import ui.lvgl.page  # noqa
        app.build_all()

        # 輸入
        from lib.hw_manager import get_input
        def enc_delta():
            return get_input("enc", idx=0) or 0
        def confirm():
            return get_input("pin", key="encC") == 0
        def exit_pressed():
            return get_input("pin", key="btn") == 0

        app.init({
            "tick": tick, "take": take, "show": show,
            "enc_delta": enc_delta, "confirm": confirm, "exit": exit_pressed,
        })
        app.go("launcher")
        print("[ring] setup done, free: {} KB".format(gc.mem_free() // 1024))

        for i in range(100):
            app.step()
            if i % 20 == 0:
                print("[ring]   frame {} free: {}KB".format(i, gc.mem_free() // 1024))

        result["ok"] = True
        print("[ring] ✅ 100 幀完成")
    except Exception as e:
        result["ok"] = False
        result["err"] = str(e)
        print("[ring] ❌ error: {}".format(e))


def run():
    print("=" * 55)
    print("[test] ring buffer + 完整 UI @ CPU1(thread)")
    print("[test] callback 寫 ring(不分配),外面送 TFT")
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
        "✅ 通過 — ring buffer 解決,保留 PARTIAL 省記憶體" if ok else "❌ 崩潰"))


if __name__ == "__main__":
    run()
