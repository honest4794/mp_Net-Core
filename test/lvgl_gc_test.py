# test/lvgl_gc_test.py — gc.disable() 是否解決 thread 崩潰
#
# 假設:mp_thread_gc_others 在 GC 時掃描 CPU1 stack,CPU1 正在操作 LVGL widget
#      → stack 中途不一致 → heap 損壞。
#
# 測試:thread 裡 gc.disable() 禁止自動 GC,看是否不崩。
#
# 用法:
#   import lvgl_gc_test as t
#   t.test_disable_gc()   # gc.disable + 完整 app.step
#   t.test_enable_gc()    # 對照(不自動 gc)
#   t.run()

import _thread, time, gc
import lvgl as lv
from lib.sys_bus import bus


def _cpu0_sleep():
    while bus.shared.get("engine_run", True):
        time.sleep_ms(5)


def _cpu1_full_app_step(use_disable_gc, result):
    """CPU1:完整 board._setup + app.step,可選 gc.disable。"""
    try:
        if use_disable_gc:
            gc.disable()
            print("[gc] auto GC disabled")

        from ui.lvgl import board, app
        board._started = False
        board._setup()
        print("[gc] _setup done, free: {} KB".format(gc.mem_free() // 1024))

        for i in range(100):
            app.step()
            if i % 20 == 0:
                print("[gc]   frame {} free: {}KB".format(i, gc.mem_free() // 1024))

        result["ok"] = True
        print("[gc] ✅ 100 幀完成")
    except Exception as e:
        result["ok"] = False
        result["err"] = str(e)
        print("[gc] ❌ error: {}".format(e))
    finally:
        if use_disable_gc:
            try:
                gc.enable()
            except Exception:
                pass


def _test(use_disable_gc, label):
    print("\n" + "=" * 55)
    print("[test] {} (thread + 完整 board)".format(label))
    print("=" * 55)
    gc.collect()  # 測試前先 clean
    bus.shared["engine_run"] = True
    result = {"ok": None}

    _thread.start_new_thread(_cpu0_sleep, ())
    time.sleep_ms(100)
    _thread.start_new_thread(_cpu1_full_app_step, (use_disable_gc, result))

    waited = 0
    while result["ok"] is None and waited < 20000:
        time.sleep_ms(50)
        waited += 50

    bus.shared["engine_run"] = False
    time.sleep_ms(200)
    ok = result.get("ok", False)
    print("[test] {} → {}".format(label, "✅ 通過" if ok else "❌ 崩潰"))
    return ok


def test_disable_gc():
    """gc.disable + 完整 app.step。"""
    return _test(True, "gc.disable")


def test_enable_gc():
    """對照(自動 gc)。"""
    return _test(False, "gc.enable(對照)")


def run():
    print("\n" + "█" * 55)
    print("█ gc.disable() 是否解決 thread + 完整 UI 崩潰")
    print("█" * 55)

    r_disable = test_disable_gc()
    if r_disable:
        print("\n→ gc.disable 通過!根因 = GC 跨 thread stack 掃描競態")
        print("→ 但 disable GC 會慢慢漏記憶體,需配搭定期 gc.collect()")
    else:
        print("\n→ gc.disable 也崩 → 不是 GC 問題")

    print()


if __name__ == "__main__":
    run()
