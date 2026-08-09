# test/lvgl_cpu0_load_test.py — CPU0 負載類型對 CPU1 LVGL 的影響
#
# B(純 tick+show,不讀 shared)也崩 → 不是 bus.shared 讀取問題。
# L4 通過、B 崩 → 差異在 LvglDisp(register_service)vs L4 本地物件。
#
# 本測試:固定 CPU1 跑完整 board._setup + app.step,
#        變化 CPU0 採樣緒做什麼,找出 CPU0 的什麼操作導致 CPU1 崩。
#
# CPU0 變體:
#   V1: 只 sleep(不碰 bus,不碰任何 dict)— 基準
#   V2: 寫 bus.shared(模擬採樣,但不讀硬體)
#   V3: 完整 sample_inputs(讀硬體 + 寫 bus.shared)
#
# 用法:
#   import lvgl_cpu0_load_test as t
#   t.run_all()

import _thread, time, gc
import lvgl as lv
from lib.sys_bus import bus

_FRAMES = 200


def _cpu0_sleep_only():
    """V1: 只 sleep,不碰 bus。"""
    while bus.shared.get("engine_run", True):
        time.sleep_ms(5)


def _cpu0_write_shared():
    """V2: 寫 bus.shared(不讀硬體,純 dict 寫)。"""
    counter = 0
    while bus.shared.get("engine_run", True):
        bus.shared["_hw_inputs"] = {"enc": [counter % 4], "pin": {"encC": 1, "btn": 1}, "_enc_last": [counter]}
        counter += 1
        time.sleep_ms(5)


def _cpu0_full_sample():
    """V3: 完整 sample_inputs(讀硬體 + 寫 bus.shared)。"""
    from lib.hw_manager import sample_inputs
    sample_inputs()
    while bus.shared.get("engine_run", True):
        sample_inputs()
        time.sleep_ms(5)


def _cpu1_board(result):
    """CPU1:完整 board._setup + app.step。"""
    try:
        from ui.lvgl import board, app
        board._started = False
        board._setup()
        print("[CPU1] _setup done, free: {} KB".format(gc.mem_free() // 1024))

        for i in range(_FRAMES):
            app.step()
            time.sleep_ms(5)

        result["ok"] = True
        print("[CPU1] ✅ {} 幀完成".format(_FRAMES))
    except Exception as e:
        result["ok"] = False
        result["err"] = str(e)


def _test(cpu0_fn, label):
    print("\n" + "=" * 55)
    print("[test] CPU0: {} + CPU1: 完整 board".format(label))
    print("=" * 55)
    gc.collect()
    bus.shared["engine_run"] = True
    result = {"ok": None}

    _thread.start_new_thread(cpu0_fn, ())
    time.sleep_ms(100)
    _thread.start_new_thread(_cpu1_board, (result,))

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


def run_all():
    print("\n" + "█" * 55)
    print("█ CPU0 負載類型對 CPU1 LVGL 的影響")
    print("█ CPU1 固定跑完整 board,變化 CPU0 做什麼")
    print("█" * 55)

    tests = [
        (_cpu0_sleep_only, "V1: 只sleep(不碰bus)"),
        (_cpu0_write_shared, "V2: 寫bus.shared(不讀硬體)"),
        (_cpu0_full_sample, "V3: 完整採樣(讀硬體+寫shared)"),
    ]

    results = {}
    for fn, label in tests:
        key = label[:2]
        results[key] = _test(fn, label)
        time.sleep_ms(2000)
        gc.collect()

    print("\n" + "█" * 55)
    for key in results:
        print("  {} {}".format(key, "✅" if results[key] else "❌ 崩潰"))
    print()

    # 判讀
    if results.get("V1") and not results.get("V2"):
        print("→ CPU0 碰 bus.shared(dict 寫)導致 CPU1 崩 → dict 競態")
    elif not results.get("V1"):
        print("→ CPU0 只 sleep 也崩 → CPU1 board 本身有問題(LvglDisp?)")
    elif results.get("V2") and not results.get("V3"):
        print("→ CPU0 讀硬體(encoder.value)導致崩 → GPIO 跨核?")


if __name__ == "__main__":
    run_all()
