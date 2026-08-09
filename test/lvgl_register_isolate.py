# test/lvgl_register_isolate.py — register_service 是否導致 _thread 崩潰
#
# 無 thread 全通過 → 程式碼本身沒問題。
# 有 thread 崩 → _thread + board._setup 組合有問題。
# L0-L4(閉包 flush_cb, 不 register)通過。
# L5/V1(LvglDisp bound method + register_service)崩。
#
# 本測試:在 _thread 裡跑完整 board._setup,但關閉 register_service。
# 如果通過 → register_service 是元兇(LvglDisp 進 bus dict → GC 跨核掃描)。
#
# 用法:
#   import lvgl_register_isolate as t
#   t.test_no_register()   # 不 register
#   t.test_with_register() # 有 register(對照)

import _thread, time, gc
import lvgl as lv
from lib.sys_bus import bus

_FRAMES = 100


def _cpu0_sleep():
    """CPU0 只 sleep(已證實即使只 sleep 也會干擾)。"""
    while bus.shared.get("engine_run", True):
        time.sleep_ms(5)


def _cpu1_board_no_register(result):
    """CPU1:跑 board._setup 但不 register_service。
    Monkey-patch get_platform 暫時不註冊。"""
    try:
        from ui.lvgl import lvgl_init, board, app

        # Monkey-patch: get_platform 不做 register_service
        original_get = lvgl_init.get_platform
        def _get_no_register():
            existing = bus.get_service(lvgl_init._SERVICE)
            if existing is not None:
                return existing
            plat = lvgl_init.LvglDisp()
            # 不呼叫 register_service — plat 只在本地引用
            return plat
        lvgl_init.get_platform = _get_no_register

        board._started = False
        board._setup()
        print("[no-reg] _setup done, free: {} KB".format(gc.mem_free() // 1024))

        for i in range(_FRAMES):
            app.step()
            time.sleep_ms(5)

        result["ok"] = True
        print("[no-reg] ✅ {} 幀完成".format(_FRAMES))
    except Exception as e:
        result["ok"] = False
        result["err"] = str(e)
        print("[no-reg] ❌ error: {}".format(e))


def _cpu1_board_with_register(result):
    """CPU1:正常 board._setup(有 register_service)— 對照。"""
    try:
        from ui.lvgl import board, app
        board._started = False
        board._setup()
        print("[reg] _setup done, free: {} KB".format(gc.mem_free() // 1024))

        for i in range(_FRAMES):
            app.step()
            time.sleep_ms(5)

        result["ok"] = True
        print("[reg] ✅ {} 幀完成".format(_FRAMES))
    except Exception as e:
        result["ok"] = False
        result["err"] = str(e)
        print("[reg] ❌ error: {}".format(e))


def _test(cpu1_fn, label):
    print("\n" + "=" * 55)
    print("[test] {} (CPU0 sleep + CPU1 board)".format(label))
    print("=" * 55)
    gc.collect()
    bus.shared["engine_run"] = True
    result = {"ok": None}

    _thread.start_new_thread(_cpu0_sleep, ())
    time.sleep_ms(100)
    _thread.start_new_thread(cpu1_fn, (result,))

    waited = 0
    timeout = _FRAMES * 60 + 15000
    while result["ok"] is None and waited < timeout:
        time.sleep_ms(50)
        waited += 50

    bus.shared["engine_run"] = False
    time.sleep_ms(200)
    ok = result.get("ok", False)
    print("[test] {} → {}".format(label, "✅ 通過" if ok else "❌ 崩潰"))
    return ok


def test_no_register():
    """不 register_service(預期通過)。"""
    return _test(_cpu1_board_no_register, "不register")


def test_with_register():
    """有 register_service(對照,預期崩)。"""
    return _test(_cpu1_board_with_register, "有register")


def run_all():
    print("\n" + "█" * 55)
    print("█ register_service 是否導致 _thread 崩潰")
    print("█" * 55)

    r_no = test_no_register()
    time.sleep_ms(2000)
    gc.collect()
    r_yes = test_with_register()

    print("\n" + "█" * 55)
    print("  不 register: {}".format("✅ 通過" if r_no else "❌ 崩潰"))
    print("  有 register:  {}".format("✅ 通過" if r_yes else "❌ 崩潰"))
    if r_no and not r_yes:
        print("\n→ register_service 是元兇:LvglDisp 進 bus dict → GC 跨核掃描 → 崩")
        print("→ 解法:get_platform 不做 register_service(CPU1 本地持有)")
    print()


if __name__ == "__main__":
    run_all()
