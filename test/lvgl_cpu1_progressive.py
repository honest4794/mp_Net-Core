# test/lvgl_cpu1_progressive.py — 漸進式找出 board.run 崩潰點
#
# 策略 A/B/C 全通過(簡單 UI),但 board.run(完整 UI)崩潰。
# 本測試從簡單 UI 開始,逐步加入 board._setup 的元素,找出崩潰步驟。
#
# 測試階梯:
#   L0: 策略 A 簡單 UI(已知通過)— 基準
#   L1: + ui_common.init_fonts()(載 73KB 字型)
#   L2: + import ui.lvgl.page(@register 全部頁面)
#   L3: + app.build_all()(build 4 個 screen)
#   L4: + board._make_inputs()(hw_manager 快照輸入)
#   L5: = 完整 board._setup()(全部元素)
#
# 用法(soft reboot 後,boot.py 已跑完):
#   import lvgl_cpu1_progressive as t
#   t.run_all()

import _thread, time, gc
import lvgl as lv
from lib.sys_bus import bus

_W = 320
_H = 240
_BPP = 2
_MADCTL = 0x60
_LINES = 40
_FRAMES = 200

_LEVEL_NAMES = ["簡單UI", "+字型", "+頁面import", "+build_all", "+hw輸入", "完整_setup"]


def _get_hw():
    lcd = bus.get_service("lcd")
    bus_obj = getattr(lcd, "_bus")
    enc_list = bus.get_service("enc_list") or []
    pin_by_label = bus.get_service("pin_by_label") or {}
    return bus_obj, enc_list[0] if enc_list else None, pin_by_label


def _cpu0_sampler():
    from lib.hw_manager import sample_inputs
    sample_inputs()
    while bus.shared.get("engine_run", True):
        sample_inputs()
        time.sleep_ms(5)


def _make_flush_cb(bus_obj, dirty):
    """PARTIAL flush_cb(bytes 拷貝,跟策略 A 一樣)。"""
    def flush_cb(disp_drv, area, color_p):
        w = area.x2 - area.x1 + 1
        h = area.y2 - area.y1 + 1
        data = color_p.__dereference__(w * h * _BPP)
        lv.draw_sw_rgb565_swap(data, w * h)
        dirty.append((area.x1, area.y1, area.x2, area.y2, bytes(data)))
        disp_drv.flush_ready()
    return flush_cb


def _loop(bus_obj, disp, dirty, frames):
    """主迴圈。"""
    for _ in range(frames):
        lv.tick_inc(5)
        lv.task_handler()
        lv.refr_now(disp)
        while dirty:
            x1, y1, x2, y2, data = dirty.pop(0)
            bus_obj.set_window(x1, y1, x2, y2)
            bus_obj.write_data_async(data)
            bus_obj.flush()
        time.sleep_ms(5)


# ══════════════════════════════════════════════════════
# 測試階梯
# ══════════════════════════════════════════════════════

def _test_level(level, setup_fn):
    """測單一階梯。"""
    print("\n" + "=" * 55)
    print("[L{}] {} (CPU0 採樣緒 + CPU1, {} 幀)".format(level, _LEVEL_NAMES[level], _FRAMES))
    print("=" * 55)

    gc.collect()
    print("[L{}] free mem start: {} KB".format(level, gc.mem_free() // 1024))

    bus.shared["engine_run"] = True
    result = {"ok": None}

    def _cpu1_run():
        try:
            bus_obj, enc, pin_by_label = _get_hw()
            dirty = []

            # MADCTL + LVGL init(跟策略 A 一樣)
            bus_obj.write_cmd_data(0x36, bytes([_MADCTL]))
            lv.init()
            disp = lv.display_create(_W, _H)
            disp.set_color_format(18)
            buf = bytearray(_W * _LINES * _BPP)
            disp.set_buffers(buf, None, len(buf), 0)
            disp.set_flush_cb(_make_flush_cb(bus_obj, dirty))

            # 階梯特定的 setup
            setup_fn(disp, dirty)

            time.sleep_ms(200)
            print("[L{}] setup done, free: {} KB".format(level, gc.mem_free() // 1024))

            _loop(bus_obj, disp, dirty, _FRAMES)
            result["ok"] = True
        except Exception as e:
            result["ok"] = False
            result["err"] = str(e)
            print("[L{}] ❌ setup/loop error: {}".format(level, e))

    # CPU0 採樣緒
    _thread.start_new_thread(_cpu0_sampler, ())
    time.sleep_ms(100)
    # CPU1
    _thread.start_new_thread(_cpu1_run, ())

    waited = 0
    timeout = _FRAMES * 60 + 10000
    while result["ok"] is None and waited < timeout:
        time.sleep_ms(50)
        waited += 50

    bus.shared["engine_run"] = False
    time.sleep_ms(200)

    status = "✅ 通過" if result["ok"] else "❌ 崩潰({})".format(result.get("err", "timeout")[:40])
    print("[L{}] {}".format(level, status))
    return result.get("ok", False)


def setup_l0(disp, dirty):
    """L0: 簡單 UI(2 label, 基準)"""
    scr = lv.obj(None)
    scr.set_style_bg_color(lv.color_hex(0x1A2B3C), 0)
    lbl = lv.label(scr)
    lbl.set_text("L0 baseline")
    lbl.set_style_text_color(lv.color_hex(0x4FC3F7), 0)
    lv.screen_load(scr)


def setup_l1(disp, dirty):
    """L1: + 載入字型(73KB)"""
    from ui.lvgl import ui_common
    # 建 fake platform(只為 init_fonts 需要 W/H)
    ui_common.W = _W
    ui_common.H = _H
    ui_common.init_fonts()
    print("[L1] font loaded: ZH={}".format(ui_common.ZH is not None))
    scr = lv.obj(None)
    scr.set_style_bg_color(lv.color_hex(0x1A2B3C), 0)
    lbl = lv.label(scr)
    lbl.set_text("L1 font")
    if ui_common.ZH:
        lbl.set_style_text_font(ui_common.ZH, 0)
    lv.screen_load(scr)


def setup_l2(disp, dirty):
    """L2: + import 頁面(@register)"""
    from ui.lvgl import ui_common
    ui_common.W = _W
    ui_common.H = _H
    ui_common.init_fonts()
    try:
        import ui.lvgl.page  # noqa: F401
        from ui.lvgl import registry
        print("[L2] pages registered: {}".format(list(registry.PAGES.keys())))
    except Exception as e:
        print("[L2] page import: {}".format(e))
    scr = lv.obj(None)
    scr.set_style_bg_color(lv.color_hex(0x1A2B3C), 0)
    lbl = lv.label(scr)
    lbl.set_text("L2 pages")
    lv.screen_load(scr)


def setup_l3(disp, dirty):
    """L3: + app.build_all()(build 全部 screen)"""
    from ui.lvgl import ui_common, app
    ui_common.W = _W
    ui_common.H = _H
    ui_common.init_fonts()
    try:
        import ui.lvgl.page  # noqa: F401
    except Exception as e:
        print("[L3] page import: {}".format(e))
    app.build_all()
    print("[L3] screens built: {}".format(len(app._screens)))
    app.go("launcher")


def setup_l4(disp, dirty):
    """L4: + hw_manager 輸入(完整 board._make_inputs 等價)"""
    from ui.lvgl import ui_common, app
    from lib.hw_manager import get_input
    ui_common.W = _W
    ui_common.H = _H
    ui_common.init_fonts()
    try:
        import ui.lvgl.page  # noqa: F401
    except Exception as e:
        print("[L4] page import: {}".format(e))
    app.build_all()

    # hw_manager 輸入(跟 board._make_inputs 一樣)
    def enc_delta():
        return get_input("enc", idx=0) or 0
    def confirm():
        return get_input("pin", key="encC") == 0
    def exit_pressed():
        return get_input("pin", key="btn") == 0

    app.init({
        "tick": disp_drv_tick_factory(disp),
        "take": lambda: [],
        "show": lambda *a: None,
        "enc_delta": enc_delta,
        "confirm": confirm,
        "exit": exit_pressed,
    })
    app.go("launcher")
    print("[L4] inputs wired via hw_manager")


def disp_drv_tick_factory(disp):
    """tick 函式(只跑 task_handler,渲染由外部 loop 處理)。"""
    def tick():
        pass
    return tick


def setup_l5(disp, dirty):
    """L5: 完整 board._setup()"""
    from ui.lvgl import board
    board._started = False  # 重設 once-only guard
    board._setup()


def run_all():
    """依序測 L0→L5,找出崩潰點。"""
    print("\n" + "█" * 55)
    print("█ 漸進式找出 board.run @ CPU1 崩潰點")
    print("█ 每階加入一個元素,CPU0 同時跑採樣緒")
    print("█" * 55)

    levels = [
        (0, setup_l0),
        (1, setup_l1),
        (2, setup_l2),
        (3, setup_l3),
        (4, setup_l4),
        (5, setup_l5),
    ]
    results = {}
    for level, fn in levels:
        results[level] = _test_level(level, fn)
        if not results[level]:
            print("\n[!] L{} 崩潰 — 這就是觸發點".format(level))
            break
        time.sleep_ms(1000)
        gc.collect()

    print("\n" + "█" * 55)
    print("█ 匯總")
    print("█" * 55)
    for level in sorted(results):
        print("  L{} {:<35s} {}".format(
            level, _LEVEL_NAMES[level],
            "✅" if results[level] else "❌ 崩潰"))
    print()


if __name__ == "__main__":
    run_all()
