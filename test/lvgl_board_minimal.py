# test/lvgl_board_minimal.py — 最小化重現 board._setup 崩潰
#
# V1(CPU0 只 sleep)也崩 → 不是 CPU0 問題。
# 崩在 _setup 期間(沒印 _setup done)。
#
# 本測試:逐步執行 board._setup 內部步驟,找出精確崩潰行。
# 不開任何 thread(純主執行緒),排除 thread 因素。
#
# 用法:
#   import lvgl_board_minimal as t
#   t.run()

import time, gc
import lvgl as lv
from lib.sys_bus import bus


def run():
    """逐步執行 board._setup 內部,每步印 log。"""
    print("=" * 55)
    print("[min] 最小化重現 board._setup(無 thread)")
    print("=" * 55)

    gc.collect()
    print("[min] free: {} KB".format(gc.mem_free() // 1024))

    # ── 步驟 1: get_platform (LvglDisp.__init__) ──
    print("[min] step 1: get_platform...")
    try:
        from ui.lvgl import lvgl_init
        plat = lvgl_init.get_platform()
        print("[min] ✅ get_platform OK, plat={}".format(type(plat).__name__))
    except Exception as e:
        print("[min] ❌ get_platform: {}".format(e))
        return

    time.sleep_ms(100)

    # ── 步驟 2: ui_common.init + init_fonts ──
    print("[min] step 2: init_fonts...")
    try:
        from ui.lvgl import ui_common
        ui_common.init(plat)
        ui_common.init_fonts()
        print("[min] ✅ fonts OK")
    except Exception as e:
        print("[min] ❌ fonts: {}".format(e))
        return

    time.sleep_ms(100)

    # ── 步驟 3: import pages ──
    print("[min] step 3: import pages...")
    try:
        import ui.lvgl.page  # noqa
        print("[min] ✅ pages imported")
    except Exception as e:
        print("[min] ❌ pages: {}".format(e))
        return

    time.sleep_ms(100)

    # ── 步驟 4: build_all ──
    print("[min] step 4: build_all...")
    try:
        from ui.lvgl import app
        app.build_all()
        print("[min] ✅ build_all OK ({} screens)".format(len(app._screens)))
    except Exception as e:
        print("[min] ❌ build_all: {}".format(e))
        return

    time.sleep_ms(100)

    # ── 步驟 5: _make_inputs ──
    print("[min] step 5: _make_inputs...")
    try:
        from ui.lvgl import board
        inputs = board._make_inputs()
        print("[min] ✅ inputs OK: {}".format(len(inputs)))
    except Exception as e:
        print("[min] ❌ inputs: {}".format(e))
        return

    time.sleep_ms(100)

    # ── 步驟 6: app.init + go ──
    print("[min] step 6: app.init + go...")
    try:
        app.init({
            "tick": plat.tick,
            "take": plat.take,
            "show": plat.show,
            "enc_delta": inputs[0],
            "confirm": inputs[1],
            "exit": inputs[2],
        })
        app.go("launcher")
        print("[min] ✅ app.init + go OK")
    except Exception as e:
        print("[min] ❌ app.init: {}".format(e))
        return

    time.sleep_ms(100)

    # ── 步驟 7: 跑 10 幀 app.step ──
    print("[min] step 7: 10 frames app.step...")
    try:
        for i in range(10):
            app.step()
            print("[min]   frame {} OK".format(i))
        print("[min] ✅ 10 frames OK — 全部通過!")
    except Exception as e:
        print("[min] ❌ step frame {}: {}".format(i, e))
        return


if __name__ == "__main__":
    run()
