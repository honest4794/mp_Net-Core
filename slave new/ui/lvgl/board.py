# ui/lvgl/board.py — 板上對接層（slave new bus 系統）
#
# ui/lvgl/ 是 slave new 專案裡的一個 UI 區塊(像 tasks/lib)。
# 硬體全部透過 slave new 的 bus 系統取得,本檔不自建任何硬體:
#   顯示   bus.get_service("lcd")   （ST7789 + SpiBusAdapter,set_window/write_data_async）
#   確認鍵 bus.shared.pop("_vbtn1_event") （control_panel 累加寫入,latching 用 pop 消費）
#   encoder 本輪不接(等 control_panel 邏輯併入 LVGL 時一起處理)
#
# LCD 模式閘門:bus.shared["System"]["lcd_mode"] == "ui" 才啟動,否則讓 LCD 給 player。
#   這是 slave new 的 config 切換機制,讀取點就一個地方。
#
# 用法(soft reboot 後,boot.py 已跑完):
#   import ui.lvgl.board
#   ui.lvgl.board.run()
import sys
import lvgl as lv
from lib.sys_bus import bus
from ui.lvgl import app
from ui.lvgl import ui_space
from ui.lvgl import lvgl_init

# 資源在 ui/lvgl/src,加進 import 路徑（ui_common 的 from lv_icons/lv_ui_fx 由此找到）
_SRC = "/ui/lvgl/src"
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)


def _fill_var_strings():
    """把系統設定頁的字串欄位填進 _ui_var(唯讀顯示)。
    slave_id/MAC 來自 machine.unique_id;hostname/master_IP/ssid 來自 bus.shared。"""
    var = bus.shared.setdefault("_ui_var", {})
    var.setdefault("sys", {})
    s = var["sys"]

    # slave_id / MAC:unique_id 的 hex(+ 加冒號格式)
    sid = bus.slave_id or "UNKNOWN"
    s["slave_id"] = sid
    if len(sid) >= 12:
        s["mac"] = ":".join(sid[i:i + 2] for i in range(0, 12, 2))
    else:
        s["mac"] = sid

    # hostname / master_IP / wifi_ssid:從 bus.shared["System"]/["Network"] 讀
    sys_cfg = bus.shared.get("System", {})
    s["hostname"] = str(sys_cfg.get("hostname", "") or "")
    s["master_IP"] = "{}:{}".format(
        sys_cfg.get("master_IP", ""), sys_cfg.get("master_port", 0))

    wifi = bus.shared.get("Network", {}).get("wifi", {})
    s["wifi_ssid"] = str(wifi.get("ssid", "") or "")


def _init_control_plane():
    """註冊所有頁面 → 預建所有 screen → 配置 bus 空間 → 註冊 ui service。
    順序關鍵:page import(觸發 @register) → build_all(觸發 declare) →
    alloc_from_decl(依 declare 總數配 buffer)。"""
    # 1. 載入所有頁面(集中 import 觸發 @register)
    try:
        import ui.lvgl.page  # noqa: F401
    except ImportError:
        pass
    # 2. 預建所有 screen(此時 build() 內的 declare 全部到位)
    app.build_all()
    # 3. 配置打包陣列(依 _ui_decl 總數一次性配固定大小)
    ui_space.alloc_from_decl()
    # 4. 註冊 service:action handler 用 bus.get_service("ui") 存取
    bus.register_service("ui", ui_space)
    # 5. 填字串欄位
    _fill_var_strings()
    get_log = None
    try:
        from lib.log_service import get_log
    except Exception:
        pass
    if get_log:
        get_log().info("[board] ui service registered, lcd_mode ready")


def run():
    """建立 slave new 平台 + 啟動 UI 主迴圈。"""

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

    # LVGL display:一次初始化 + bus reuse(對齊 i80_drv/tft_drv)
    plat = lvgl_init.get_platform()

    # 載入字體資源 + 控制平面 + 頁面註冊(ui/lvgl/src 已加進 sys.path)
    import ui.lvgl.ui_common as ui_common
    ui_common.init_fonts()
    _init_control_plane()

    # reuse 模式:沿用預建 screen(扁平設計,widget 永駐)
    # confirm 覆寫:用 _vbtn1_event(latching,只認 1=按下)
    def _confirm():
        v = bus.shared.pop("_vbtn1_event", None)
        return v is not None and v == 1

    app.init({
        "tick": plat.tick,
        "take": plat.take,
        "show": plat.show,
        "enc_delta": plat.enc_delta,
        "confirm": _confirm,
        "exit": plat.exit,
    }, reuse=True)
    app.go("launcher")

    # ── 主迴圈(board 自跑,不呼叫 app.run():要在每幀插入 ui_space.sync) ──
    while True:
        try:
            app.step()
            ui_space.sync()
        except Exception as e:
            if get_log:
                get_log().error("[board] loop err: {}".format(e))
            else:
                print("[board] loop err:", e)
        _sleep(5)


def _sleep(ms):
    try:
        import time
        time.sleep_ms(ms)
    except Exception:
        pass
