# ui/lvgl/page/control_panel.py — 控制面板硬體監視（唯讀）
#
# 反映 tasks/control_panel.py 的硬體狀態:
#   enc_pos  編碼器位置(LogService enc_pos,這裡從 _vbtn/HW 讀或暫以 0 顯示)
#   btn      按鍵 btn 狀態
#   encC     確認鍵 encC 狀態
#
# 本頁全唯讀,純診斷用。encoder 轉動/confirm 是 LVGL 導覽輸入,不進控制陣列。
# 注意:control_panel.py 的 enc_pos 寫在 ControlPanelTask 私有 viper buffer,
#   外部讀不到乾淨值,故 enc_pos 暫顯示 HW VBTN 累計或 0(待 control_panel 併入 LVGL 後補)。

import lvgl as lv
try:
    from ui.lvgl.registry import register
    from ui.lvgl import ui_common as u
    from ui.lvgl import ui_common
except ImportError:
    from registry import register
    import ui_common as u
    import ui_common

scr = None
_enc_lb = None
_btn_lb = None
_encC_lb = None


@register(id="control_panel", title="控制面板", icon="sliders-horizontal",
          desc="硬體狀態監視", order=1, accent=0x4A90D9)
def build():
    global scr, _enc_lb, _btn_lb, _encC_lb
    scr = lv.obj(None)
    scr.set_style_bg_color(u.C(u.BG), 0)
    u.mk_appbar(scr, "控制面板", "RO")

    ui_common.begin_page("control_panel")

    # 編碼器位置
    c1 = u.mk_card(scr, 12, 48, 296, 56)
    u.mk_icon(c1, "refresh-cw", 10, 16, u.TEXT2)
    u.mk_label(c1, "編碼器位置", 30, 12, u.TEXT2, u.ZH)
    _enc_lb = lv.label(c1)
    _enc_lb.align(lv.ALIGN.RIGHT_MID, -12, 0)
    _enc_lb.set_style_text_font(u.F_NUM_L, 0)
    _enc_lb.set_style_text_color(u.C(u.PRIMARY), 0)
    _enc_lb.set_text("0")
    # declare(唯讀 display):read 從 HW VBTN 或 bus 讀,本輪暫回 0
    ui_common.declare("enc_pos", "display", "編碼器位置", dir="r",
                      read=lambda: _read_enc_pos())

    # 按鍵狀態(2 個 switch 顯示)
    c2 = u.mk_card(scr, 12, 112, 144, 110)
    u.mk_label(c2, "按鍵狀態", 10, 8, u.TEXT2, u.ZH)
    u.mk_icon(c2, "square", 10, 42, u.TEXT2)
    u.mk_label(c2, "btn", 30, 38, u.TEXT, u.ZH)
    _btn_lb = lv.label(c2)
    _btn_lb.set_pos(100, 40)
    _btn_lb.set_style_text_font(u.F_NUM_M, 0)
    _btn_lb.set_style_text_color(u.C(u.TEXT3), 0)
    _btn_lb.set_text("0")
    ui_common.declare("btn", "switch", "按鍵 btn", dir="r",
                      read=lambda: _read_vbtn(0))

    c3 = u.mk_card(scr, 164, 112, 144, 110)
    u.mk_label(c3, "確認鍵", 10, 8, u.TEXT2, u.ZH)
    u.mk_icon(c3, "square", 10, 42, u.TEXT2)
    u.mk_label(c3, "encC", 30, 38, u.TEXT, u.ZH)
    _encC_lb = lv.label(c3)
    _encC_lb.set_pos(100, 40)
    _encC_lb.set_style_text_font(u.F_NUM_M, 0)
    _encC_lb.set_style_text_color(u.C(u.TEXT3), 0)
    _encC_lb.set_text("0")
    ui_common.declare("encC", "switch", "確認鍵 encC", dir="r",
                      read=lambda: _read_vbtn(1))

    u.fade_in(c1, dy=5, time_ms=280, delay_ms=40)
    u.fade_in(c2, dy=5, time_ms=280, delay_ms=120)
    u.fade_in(c3, dy=5, time_ms=280, delay_ms=200)
    return scr


def _read_enc_pos():
    # control_panel 的 enc_pos 在私有 viper buffer,外部讀不到乾淨值。
    # 本輪暫回 0(待 control_panel 邏輯併入 LVGL 後補真實值)。
    return 0


def _read_vbtn(vbtn_id):
    """讀 HW VBTN bitmap(vbtn_id 0=btn, 1=encC)。"""
    try:
        from lib.hw_manager import HW
        return HW.get(HW.VBTN, vbtn_id) or 0
    except Exception:
        return 0


# ====== 頁面接口 ======

def on_enter():
    pass

def on_leave():
    pass

def on_enc(d):
    pass

def on_confirm():
    return None

def on_exit():
    return False

def update(run):
    # 每 10 幀刷新顯示(狀態從打包陣列讀,已由 sync 寫入)
    if run % 10 != 0:
        return
    try:
        from ui.lvgl import ui_space
        enc = ui_space.get_value("control_panel", "enc_pos")
        btn = ui_space.get_value("control_panel", "btn")
        encC = ui_space.get_value("control_panel", "encC")
        _enc_lb.set_text(str(enc or 0))
        _btn_lb.set_text("ON" if btn else "OFF")
        _btn_lb.set_style_text_color(u.C(u.SUCCESS if btn else u.TEXT3), 0)
        _encC_lb.set_text("ON" if encC else "OFF")
        _encC_lb.set_style_text_color(u.C(u.SUCCESS if encC else u.TEXT3), 0)
    except Exception:
        pass
