# test/lvgl_l5_isolate2.py — L5 崩潰點二次隔離
#
# 無 sleep 也崩 → 不是 sleep 問題。
# L4 vs L5 差異:app.step() 含 enc_delta/confirm/exit/update(讀 bus.shared),
#                L4 的 _loop() 不讀。
#
# 測試:
#   版本 A: app.step() 完整(含輸入 + update)— 預期崩
#   版本 B: 只 tick + take + show(跳過輸入 + update)— 測是否 bus.shared 讀取導致
#   版本 C: tick + take + show + update(含頁面讀 bus.shared,但跳過輸入)
#
# 用法:
#   import lvgl_l5_isolate2 as t
#   t.run_all()

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


def _cpu1_run(step_fn, label, result):
    """CPU1:完整 board._setup + 指定的 step 函式。"""
    try:
        from ui.lvgl import board, app
        board._started = False
        board._setup()
        print("[{}] _setup done, free: {} KB".format(label, gc.mem_free() // 1024))

        for i in range(_FRAMES):
            step_fn(app)
            time.sleep_ms(5)

        result["ok"] = True
        print("[{}] ✅ {} 幀完成".format(label, _FRAMES))
    except Exception as e:
        result["ok"] = False
        result["err"] = str(e)
        print("[{}] ❌ error: {}".format(label, e))


def _step_full(app):
    """完整 app.step()(含輸入 + update + tick + show)。"""
    app.step()


def _step_tick_show_only(app):
    """只 tick + take + show(跳過輸入 enc/confirm/exit + update)。
    測試:是否讀 bus.shared(輸入/update)導致崩潰。"""
    plat = app.platform
    plat["tick"]()
    for rect in plat["take"]():
        plat["show"](*rect)


def _step_update_tick_show(app):
    """update + tick + show(含頁面讀 bus.shared,但跳過輸入)。
    測試:是頁面 update 讀 bus.shared 還是輸入讀。"""
    plat = app.platform
    m = app._page()
    if hasattr(m, "update"):
        m.update(0)
    plat["tick"]()
    for rect in plat["take"]():
        plat["show"](*rect)


def _step_input_tick_show(app):
    """輸入 + tick + show(讀 hw_manager,但跳過 update)。"""
    plat = app.platform
    d = plat["enc_delta"]()
    c = plat["confirm"]()
    ex = plat["exit"]()
    plat["tick"]()
    for rect in plat["take"]():
        plat["show"](*rect)


def _test(step_fn, label):
    print("\n" + "=" * 55)
    print("[test] {} (CPU0 採樣緒 + CPU1)".format(label))
    print("=" * 55)
    gc.collect()
    bus.shared["engine_run"] = True
    result = {"ok": None}

    _thread.start_new_thread(_cpu0_sampler, ())
    time.sleep_ms(100)
    _thread.start_new_thread(_cpu1_run, (step_fn, label, result))

    waited = 0
    timeout = _FRAMES * 60 + 15000
    while result["ok"] is None and waited < timeout:
        time.sleep_ms(50)
        waited += 50

    bus.shared["engine_run"] = False
    time.sleep_ms(200)
    return result.get("ok", False)


def run_all():
    print("\n" + "█" * 55)
    print("█ L5 二次隔離:bus.shared 讀取 vs 純渲染")
    print("█" * 55)

    tests = [
        (_step_tick_show_only, "B: 純tick+show(不讀shared)"),
        (_step_input_tick_show, "C: 輸入+tick+show(讀hw)"),
        (_step_update_tick_show, "D: update+tick+show(讀shared)"),
        (_step_full, "A: 完整step(對照)"),
    ]

    results = {}
    for fn, label in tests:
        key = label[0]
        results[key] = _test(fn, label)
        if not results[key] and key != "A":
            print("\n[!] {} 崩潰 — 觸發點".format(label))
        time.sleep_ms(2000)
        gc.collect()

    print("\n" + "█" * 55)
    for key in ["B", "C", "D", "A"]:
        labels = {"B": "純tick+show", "C": "輸入+tick+show", "D": "update+tick+show", "A": "完整step"}
        print("  {} {:<20s} {}".format(key, labels[key], "✅" if results.get(key) else "❌ 崩潰"))
    print()


if __name__ == "__main__":
    run_all()
