# ui/lvgl/board.py — 板上對接層（slave new bus 系統）
#
# 硬體全部透過 slave new 的 bus 系統取得,本檔不自建任何硬體:
#   顯示   bus.get_service("lcd")   → lvgl_init.get_platform()(一次初始化 + reuse)
#   輸入   Encoder + 確認鍵(encC) + 離開鍵(btn),腳位從 config PIN 標籤解析
#
# LCD 模式閘門:bus.shared["System"]["lcd_mode"] == "ui" 才啟動,否則讓 LCD 給 player。
#
# 用法(soft reboot 後,boot.py 已跑完):
#   import ui.lvgl.board
#   ui.lvgl.board.run()
import sys
from lib.sys_bus import bus
from ui.lvgl import app
from ui.lvgl import ui_common
from ui.lvgl import lvgl_init

# 資源在 ui/lvgl/src,加進 import 路徑(ui_common 的 from lv_icons/lv_ui_fx 由此找到)
_SRC = "/ui/lvgl/src"
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)


def _make_inputs():
    """從 bus 拿 driver 已 init 好的輸入裝置,組成 app 介面。
    硬體全部由 driver init,UI 只取用:
      encoder  bus.get_service("enc_list")[0]   (enc_drv 建立)
      確認鍵   bus.get_service("pin_by_label")["encC"]  (pin_drv 建立)
      離開鍵   bus.get_service("pin_by_label")["btn"]
    仿 mp_LVGL/ui/lvgl_shared.py Inputs 的邊緣偵測。
    按鈕 label 預設 encC / btn,可在 config PIN 段改名。"""
    enc_list = bus.get_service("enc_list") or []
    enc = enc_list[0] if enc_list else None
    enc_last = enc.value() if enc is not None else 0

    pin_by_label = bus.get_service("pin_by_label") or {}
    confirm_pin = pin_by_label.get("encC")
    exit_pin = pin_by_label.get("btn")
    c_last = confirm_pin.value() if confirm_pin is not None else 1
    e_last = exit_pin.value() if exit_pin is not None else 1
    print("[board] inputs: enc={} encC={} btn={}".format(
        "ok" if enc else "none",
        "ok" if confirm_pin else "none",
        "ok" if exit_pin else "none"))

    def enc_delta():
        nonlocal enc_last
        if enc is None:
            return 0
        v = enc.value()
        d = v - enc_last
        enc_last = v
        return d

    def confirm():
        nonlocal c_last
        if confirm_pin is None:
            return False
        v = confirm_pin.value()
        edge = (c_last == 1 and v == 0)   # 高→低 = 按下
        c_last = v
        return edge

    def exit_pressed():
        nonlocal e_last
        if exit_pin is None:
            return False
        v = exit_pin.value()
        edge = (e_last == 1 and v == 0)
        e_last = v
        return edge

    return enc_delta, confirm, exit_pressed


def run():
    """啟動 LVGL UI 主迴圈。"""

    # ── LCD 模式閘門:不是 "ui" 就讓 LCD 給 player,直接返回 ──
    sys_cfg = bus.shared.get("System", {})
    if sys_cfg.get("lcd_mode") != "ui":
        print("[board] lcd_mode != 'ui', UI not started (LCD kept for player)")
        return

    try:
        from lib.log_service import get_log
    except Exception:
        get_log = None
    if get_log:
        get_log().info("[board] lcd_mode='ui', starting LVGL UI")

    _boot()


def _boot():
    """實際啟動(閘門通過後)。test tool 也可呼叫此函式跳過閘門。"""
    try:
        from lib.log_service import get_log
    except Exception:
        get_log = None

    # LVGL display:一次初始化 + bus reuse(對齊 i80_drv/tft_drv)
    plat = lvgl_init.get_platform()
    ui_common.init(plat)        # 注入 W/H
    ui_common.init_fonts()

    # 註冊所有頁面 → 預建所有 screen
    try:
        import ui.lvgl.page  # noqa: F401
    except ImportError as e:
        print("[board] page import fail:", e)
    app.build_all()

    # 輸入:encoder + 確認 + 離開
    enc_delta, confirm, exit_pressed = _make_inputs()

    app.init({
        "tick": plat.tick,
        "take": plat.take,
        "show": plat.show,
        "enc_delta": enc_delta,
        "confirm": confirm,
        "exit": exit_pressed,
    })
    app.go("launcher")

    # ── 主迴圈(board 自跑) ──
    try:
        while True:
            try:
                app.step()
            except Exception as e:
                if get_log:
                    get_log().error("[board] loop err: {}".format(e))
                else:
                    print("[board] loop err:", e)
            _sleep(5)
    except KeyboardInterrupt:
        print("[board] stopped")


def _sleep(ms):
    try:
        import time
        time.sleep_ms(ms)
    except Exception:
        pass
