# test/lvgl_thread_steps.py — _thread 裡逐步執行 board._setup
#
# 無 thread 全通過(minimal),有 thread 崩在 _setup 過程中。
# 本測試:在 _thread 裡逐步跑 _setup 的 7 步驟,每步印 log,找精確崩潰行。
# CPU0 只 sleep(最小干擾)。
#
# 用法:
#   import lvgl_thread_steps as t
#   t.run()

import _thread, time, gc
import lvgl as lv
from lib.sys_bus import bus


def _cpu0_sleep():
    while bus.shared.get("engine_run", True):
        time.sleep_ms(5)


def _cpu1_steps():
    """CPU1:逐步執行 _setup 7 步驟。"""
    try:
        print("[s1] get_platform...")
        from ui.lvgl import lvgl_init
        plat = lvgl_init.get_platform()
        print("[s1] ✅ get_platform")

        time.sleep_ms(50)
        print("[s2] init_fonts...")
        from ui.lvgl import ui_common
        ui_common.init(plat)
        ui_common.init_fonts()
        print("[s2] ✅ fonts")

        time.sleep_ms(50)
        print("[s3] import pages...")
        import ui.lvgl.page  # noqa
        print("[s3] ✅ pages")

        time.sleep_ms(50)
        print("[s4] build_all...")
        from ui.lvgl import app
        app.build_all()
        print("[s4] ✅ build_all ({} screens)".format(len(app._screens)))

        time.sleep_ms(50)
        print("[s5] _make_inputs...")
        from ui.lvgl import board
        inputs = board._make_inputs()
        print("[s5] ✅ inputs")

        time.sleep_ms(50)
        print("[s6] app.init + go...")
        app.init({
            "tick": plat.tick,
            "take": plat.take,
            "show": plat.show,
            "enc_delta": inputs[0],
            "confirm": inputs[1],
            "exit": inputs[2],
        })
        app.go("launcher")
        print("[s6] ✅ app.init + go")

        time.sleep_ms(50)
        print("[s7] 50 frames app.step...")
        for i in range(50):
            app.step()
            if i % 10 == 0:
                print("[s7]   frame {}".format(i))
        print("[s7] ✅ 50 frames — 全部通過!")
        bus.shared["_test_ok"] = True
    except Exception as e:
        print("[!!] ❌ 崩潰: {}".format(e))
        bus.shared["_test_ok"] = False
        bus.shared["_test_err"] = str(e)


def run():
    print("=" * 55)
    print("[test] _thread 裡逐步執行 board._setup")
    print("[test] CPU0 只 sleep, CPU1 逐步跑")
    print("=" * 55)

    gc.collect()
    bus.shared["engine_run"] = True
    bus.shared["_test_ok"] = None

    _thread.start_new_thread(_cpu0_sleep, ())
    time.sleep_ms(100)
    _thread.start_new_thread(_cpu1_steps, ())

    # 等 CPU1 跑完或崩
    waited = 0
    while bus.shared.get("_test_ok") is None and waited < 30000:
        time.sleep_ms(50)
        waited += 50

    bus.shared["engine_run"] = False
    time.sleep_ms(200)

    ok = bus.shared.get("_test_ok")
    if ok is True:
        print("\n[result] ✅ 全部通過")
    elif ok is False:
        print("\n[result] ❌ 崩潰: {}".format(bus.shared.get("_test_err", "?")))
    else:
        print("\n[result] ⏰ timeout(可能崩潰沒設旗標)")


if __name__ == "__main__":
    run()
