# test/lvgl_tick_closure.py — tick 函式:bound method vs 閉包
#
# 崩在 s7(app.step),s1-s6 全通過。
# app.step 呼叫 platform["tick"]() = LvglDisp.tick(bound method),
# 內含 self._disp(lv.refr_now(self._disp))。
# L4 _loop 用局部 disp 變數(lv.refr_now(disp))— 通過。
#
# 測試:在 thread 裡跑 app.step,但 tick 改用閉包(捕獲局部 disp)。
#   版本 A: tick 用 plat.tick(bound method)— 預期崩
#   版本 B: tick 用閉包(局部 disp)— 測試
#
# 用法:
#   import lvgl_tick_closure as t
#   t.run()

import _thread, time, gc
import lvgl as lv
from lib.sys_bus import bus


def _cpu0_sleep():
    while bus.shared.get("engine_run", True):
        time.sleep_ms(5)


def _setup_and_step(tick_fn_name, result):
    """CPU1:完整 setup + step,用指定的 tick 策略。"""
    try:
        from ui.lvgl import lvgl_init, ui_common, app, board
        import ui.lvgl.page  # noqa

        plat = lvgl_init.get_platform()
        ui_common.init(plat)
        ui_common.init_fonts()
        app.build_all()
        inputs = board._make_inputs()

        if tick_fn_name == "bound":
            # bound method(原始)— self._disp
            tick_fn = plat.tick
        else:
            # 閉包 — 捕獲局部 disp
            disp = plat._disp
            bus_obj = plat._bus
            dirty = plat._dirty
            def tick_fn():
                lv.tick_inc(5)
                lv.task_handler()
                lv.refr_now(disp)

        app.init({
            "tick": tick_fn,
            "take": plat.take,
            "show": plat.show,
            "enc_delta": inputs[0],
            "confirm": inputs[1],
            "exit": inputs[2],
        })
        app.go("launcher")
        print("[{}] setup done".format(tick_fn_name))

        for i in range(50):
            app.step()
            if i % 10 == 0:
                print("[{}]   frame {}".format(tick_fn_name, i))

        result["ok"] = True
        print("[{}] ✅ 50 幀完成".format(tick_fn_name))
    except Exception as e:
        result["ok"] = False
        result["err"] = str(e)


def _test(tick_name):
    print("\n" + "=" * 55)
    print("[test] tick={} (thread 裡)".format(tick_name))
    print("=" * 55)
    gc.collect()
    bus.shared["engine_run"] = True
    result = {"ok": None}

    _thread.start_new_thread(_cpu0_sleep, ())
    time.sleep_ms(100)
    _thread.start_new_thread(_setup_and_step, (tick_name, result))

    waited = 0
    while result["ok"] is None and waited < 20000:
        time.sleep_ms(50)
        waited += 50

    bus.shared["engine_run"] = False
    time.sleep_ms(200)
    ok = result.get("ok", False)
    print("[test] tick={} → {}".format(tick_name, "✅ 通過" if ok else "❌ 崩潰"))
    return ok


def run():
    print("\n" + "█" * 55)
    print("█ tick: bound method(self._disp) vs 閉包(局部 disp)")
    print("█" * 55)

    r_closure = _test("closure")
    time.sleep_ms(2000)
    gc.collect()
    r_bound = _test("bound")

    print("\n" + "█" * 55)
    print("  bound method (self._disp): {}".format("✅" if r_bound else "❌ 崩潰"))
    print("  閉包 (局部 disp):          {}".format("✅" if r_closure else "❌ 崩潰"))


if __name__ == "__main__":
    run()
