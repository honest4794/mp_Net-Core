# test/lvgl_l5_isolate.py — L5 崩潰點隔離測試
#
# L0-L4 通過,L5(完整 board._setup)崩潰。
# 差異:L5 走 LvglDisp.tick()含 sleep_us(5000),L4 不含。
#
# 本測試直接跑完整 board._setup + app.step 迴圈,但用兩種 tick:
#   版本 A: board 原始 tick(含 sleep_us)— 預期崩(對照)
#   版本 B: 無 sleep_us 的 tick — 測試是否 sleep 導致崩潰
#
# 用法:
#   import lvgl_l5_isolate as t
#   t.test_no_sleep()   # 測無 sleep 版
#   t.test_original()   # 測原始版(對照)

import _thread, time, gc
import lvgl as lv
from lib.sys_bus import bus

_FRAMES = 200


def _cpu0_sampler():
    from lib.hw_manager import sample_inputs
    sample_inputs()
    while bus.shared.get("engine_run", True):
        sample_inputs()
        time.sleep_ms(5)


def _run_on_cpu1(tick_fn, label, result):
    """CPU1:完整 board._setup + app.step,但用指定的 tick 函式。"""
    try:
        from ui.lvgl import board, app
        board._started = False  # 重設 once-only guard
        board._setup()

        # 覆寫 platform 的 tick
        app.platform["tick"] = tick_fn
        print("[{}] _setup done, tick={}".format(label, tick_fn.__name__))

        for i in range(_FRAMES):
            app.step()
            time.sleep_ms(5)

        result["ok"] = True
        print("[{}] ✅ {} 幀完成".format(label, _FRAMES))
    except Exception as e:
        result["ok"] = False
        result["err"] = str(e)
        print("[{}] ❌ error: {}".format(label, e))


def _tick_no_sleep():
    """無 sleep 的 tick。"""
    lv.tick_inc(5)
    lv.task_handler()
    lv.refr_now(lv.disp_get_default())


def _tick_original():
    """原始 tick(含 sleep_us 5000)。"""
    time.sleep_us(5000)
    lv.tick_inc(5)
    lv.task_handler()
    lv.refr_now(lv.disp_get_default())


def _test(tick_fn, label):
    print("\n" + "=" * 55)
    print("[test] {} — CPU0 採樣緒 + CPU1 完整 board".format(label))
    print("=" * 55)

    gc.collect()
    bus.shared["engine_run"] = True
    result = {"ok": None}

    _thread.start_new_thread(_cpu0_sampler, ())
    time.sleep_ms(100)
    _thread.start_new_thread(_run_on_cpu1, (tick_fn, label, result))

    waited = 0
    timeout = _FRAMES * 60 + 15000
    while result["ok"] is None and waited < timeout:
        time.sleep_ms(50)
        waited += 50

    bus.shared["engine_run"] = False
    time.sleep_ms(200)
    return result.get("ok", False)


def test_no_sleep():
    """測無 sleep 版(預期通過)。"""
    return _test(_tick_no_sleep, "無sleep")


def test_original():
    """測原始版含 sleep(預期崩,對照)。"""
    return _test(_tick_original, "原始sleep")


def run_all():
    print("\n" + "█" * 55)
    print("█ L5 隔離:sleep_us 是否導致崩潰")
    print("█" * 55)

    r_nosleep = test_no_sleep()
    time.sleep_ms(2000)
    gc.collect()
    r_orig = test_original()

    print("\n" + "█" * 55)
    print("  無 sleep:  {}".format("✅ 通過" if r_nosleep else "❌ 崩潰"))
    print("  原始 sleep: {}".format("✅ 通過" if r_orig else "❌ 崩潰"))
    print()


if __name__ == "__main__":
    run_all()
