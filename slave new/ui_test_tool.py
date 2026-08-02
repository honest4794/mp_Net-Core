# ui_test_tool.py — LVGL UI 獨立測試工具
#
# 跟 tft_test_tool.py 同一層,慣例一致:
#   假設 boot.py 已跑完(LCD 已在 bus 上、字型檔已就位)。
# 不受 config 的 lcd_mode 閘門限制(測試時強制 LCD 給 UI)。
#
# 用法(REPL,soft reboot 後):
#   import ui_test_tool
#   ui_test_tool.start()          # 初始化 LVGL + 控制平面 + 註冊頁面(不進主迴圈)
#   ui_test_tool.pages()          # 列出所有已註冊頁面
#   ui_test_tool.go("settings")   # 跳到某頁(單幀渲染+顯示)
#   ui_test_tool.describe()       # dump 所有頁的 widget 宣告(JSON)
#   ui_test_tool.describe("pca9685")
#   ui_test_tool.set("settings", "wifi_enable", 1)   # 模擬外部 UI_SET
#   ui_test_tool.get("settings", "wifi_enable")      # 讀實際值
#   ui_test_tool.frame(60)        # 跑 N 幀(看動畫/refresh)
#   ui_test_tool.run()            # 進主迴圈(Ctrl-C 停)
#   ui_test_tool.stop()           # 釋放 LVGL display

import sys
import json
from lib.sys_bus import bus

# LVGL 資源路徑(ui_common 的 from lv_icons/lv_ui_fx 由此找到)
_SRC = "/ui/lvgl/src"
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

_started = False
_plat = None


def _log(msg):
    print("[ui_test] " + msg)


def start():
    """初始化 LVGL + 控制平面 + 註冊頁面。不進主迴圈。
    重複呼叫安全(已啟動則跳過)。"""
    global _started, _plat
    if _started:
        _log("already started")
        return

    # LVGL display:一次初始化 + bus reuse(對齊 i80_drv/tft_drv)。
    # soft-reboot 後 LVGL C 層狀態殘留,重複 init 會要配置數百 MB garbage → 只能一次。
    from ui.lvgl import lvgl_init
    _plat = lvgl_init.get_platform()

    from ui.lvgl import app
    import ui.lvgl.ui_common as ui_common
    from ui.lvgl import ui_space

    ui_common.init_fonts()

    # 註冊所有頁面(集中 import 觸發 @register)
    try:
        import ui.lvgl.page  # noqa: F401
    except ImportError as e:
        _log("page import fail: {}".format(e))
    # 預建所有 screen(此時 build() 內的 declare 全部到位)
    app.build_all()
    # 配置 bus 空間(依 declare 總數配額,順序關鍵:必須在 build_all 之後)
    ui_space.alloc_from_decl()
    bus.register_service("ui", ui_space)
    # 填字串欄位(slave_id/mac/hostname 等)
    _fill_var_strings()

    app.init({
        "tick": _plat.tick,
        "take": _plat.take,
        "show": _plat.show,
        "enc_delta": _plat.enc_delta,
        "confirm": _plat.confirm,
        "exit": _plat.exit,
    }, reuse=True)
    # 進 launcher 首頁(渲染一幀)
    app.go("launcher")
    _plat.tick()
    for rect in _plat.take():
        _plat.show(*rect)
    _started = True
    _log("started — {} page(s) registered".format(_page_count()))
    pages()


def _fill_var_strings():
    """填系統設定頁的字串欄位(同 board._fill_var_strings)。"""
    var = bus.shared.setdefault("_ui_var", {})
    var.setdefault("sys", {})
    s = var["sys"]
    sid = bus.slave_id or "UNKNOWN"
    s["slave_id"] = sid
    if len(sid) >= 12:
        s["mac"] = ":".join(sid[i:i + 2] for i in range(0, 12, 2))
    else:
        s["mac"] = sid
    sys_cfg = bus.shared.get("System", {})
    s["hostname"] = str(sys_cfg.get("hostname", "") or "")
    s["master_IP"] = "{}:{}".format(
        sys_cfg.get("master_IP", ""), sys_cfg.get("master_port", 0))
    wifi = bus.shared.get("Network", {}).get("wifi", {})
    s["wifi_ssid"] = str(wifi.get("ssid", "") or "")


def _page_count():
    from ui.lvgl import registry
    return len(registry.PAGES)


# ══════════════════════════════════════════════════════════════
#  公開測試 API
# ══════════════════════════════════════════════════════════════

def pages():
    """列出所有已註冊頁面(id / title / order)。"""
    from ui.lvgl import registry
    _log("registered pages ({}):".format(len(registry.PAGES)))
    for m in registry.ordered():
        print("  {:02d}  {:14s}  {}".format(
            m["order"], m["id"], m.get("title", "")))


def go(name):
    """跳到指定頁面,渲染一幀。"""
    _ensure()
    from ui.lvgl import app
    from ui.lvgl import ui_space
    if name != "launcher" and name not in __pages_dict():
        _log("unknown page: {}".format(name))
        return
    app.go(name)
    ui_space.sync()
    _plat.tick()
    for rect in _plat.take():
        _plat.show(*rect)
    _log("-> {}".format(name))


def __pages_dict():
    from ui.lvgl import registry
    return registry.PAGES


def describe(page_id=None):
    """dump UI 空間映射(JSON)。page_id 空=全部頁。
    MicroPython json.dumps 不支援 ensure_ascii/indent,用自製縮排印。"""
    _ensure()
    from ui.lvgl import ui_space
    obj = ui_space.describe(page_id)
    print(json.dumps(obj))
    _print_tree(obj)
    return obj


def _print_tree(obj, indent=0):
    """簡易縮排印 dict/list,避開 MP json 的 kwarg 限制。"""
    pad = "  " * indent
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                print("{}{}:".format(pad, k))
                _print_tree(v, indent + 1)
            else:
                print("{}{}: {}".format(pad, k, v))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            if isinstance(v, (dict, list)):
                print("{}[{}]".format(pad, i))
                _print_tree(v, indent + 1)
            else:
                print("{}[{}]: {}".format(pad, i, v))
    else:
        print("{}{}".format(pad, obj))


def set(page_id, widget_id, value):
    """模擬外部 UI_SET:寫期望值進 ctrl 陣列。下一幀 sync 時 LVGL 套用。"""
    _ensure()
    from ui.lvgl import ui_space
    ok = ui_space.set_value(page_id, widget_id, value)
    _log("set {}/{} = {} -> {}".format(page_id, widget_id, value, "ok" if ok else "FAIL"))
    return ok


def get(page_id, widget_id):
    """讀單一 widget 的實際值(讀 state 陣列)。"""
    _ensure()
    from ui.lvgl import ui_space
    v = ui_space.get_value(page_id, widget_id)
    _log("get {}/{} = {}".format(page_id, widget_id, v))
    return v


def frame(n=1):
    """跑 N 幀(每幀 step+sync,看動畫/refresh)。"""
    _ensure()
    from ui.lvgl import app
    from ui.lvgl import ui_space
    import time
    for i in range(n):
        app.step()
        ui_space.sync()
        time.sleep_ms(5)
    _log("ran {} frame(s)".format(n))


def run():
    """進主迴圈(Ctrl-C 停)。"""
    _ensure()
    from ui.lvgl import app
    from ui.lvgl import ui_space
    import time
    _log("running main loop... (Ctrl-C to stop)")
    try:
        while True:
            try:
                app.step()
                ui_space.sync()
            except Exception as e:
                _log("loop err: {}".format(e))
            time.sleep_ms(5)
    except KeyboardInterrupt:
        _log("stopped")


def stop():
    """結束測試 session(回到 launcher、清工具狀態)。
    不 deinit LVGL — display 留在 bus 供下次 reuse(避免 soft-reboot garbage)。
    要完全清掉 LVGL 只能 hard reset。"""
    global _started, _plat
    if not _started:
        return
    try:
        from ui.lvgl import app
        app.go("launcher")
        _plat.tick()
        for rect in _plat.take():
            _plat.show(*rect)
    except Exception:
        pass
    _plat = None
    _started = False
    _log("stopped (LVGL display kept on bus for reuse)")


# ── 輸入注入(測試 encoder/confirm,因為測試時不接實體) ──

def inject_enc(delta):
    """模擬 encoder 轉動:直接呼叫當前頁的 on_enc。"""
    _ensure()
    from ui.lvgl import app
    m = app._page()
    if hasattr(m, "on_enc"):
        m.on_enc(delta)
        _plat.tick()
        for rect in _plat.take():
            _plat.show(*rect)
        _log("enc delta={} injected".format(delta))


def inject_confirm():
    """模擬 confirm 按下:呼叫當前頁 on_confirm(可能觸發導航)。"""
    _ensure()
    from ui.lvgl import app
    m = app._page()
    if hasattr(m, "on_confirm"):
        target = m.on_confirm()
        if target:
            go(target)
            return
    # 沒導航就刷新一幀
    _plat.tick()
    for rect in _plat.take():
        _plat.show(*rect)
    _log("confirm injected")


# ══════════════════════════════════════════════════════════════
#  內部 helper
# ══════════════════════════════════════════════════════════════

def _ensure():
    if not _started:
        raise RuntimeError("not started — call start() first")


def all():
    """一鍵全測:依序跳到每頁 + describe + 各跑幾幀。"""
    start()
    from ui.lvgl import registry
    _log("=== walking all pages ===")
    go("launcher")
    for m in registry.ordered():
        go(m["id"])
        frame(20)
    _log("=== describe (all) ===")
    describe()
    _log("=== all UI tests done ===")


if __name__ == "__main__":
    all()
