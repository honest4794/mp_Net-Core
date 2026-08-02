# ui/lvgl/page/control_panel.py — 控制面板硬體監視（唯讀）
#
# 導覽用共用 nav helper:enc 選區域(三張卡片)聚焦查看,confirm 無副作用。
# info 項:可聚焦,confirm 不做事;exit 回 launcher。
# update() 自己讀 bus:btn/encC ← HW.get(VBTN,id);enc_pos ← bus.shared["_enc_pos"]
import lvgl as lv
from ui.lvgl.registry import register
from ui.lvgl import ui_common as u
from ui.lvgl.nav import Nav, ITEM_INFO

nav = Nav()
scr = None
_enc_lb = _btn_lb = _encC_lb = None

@register(id="control_panel", title="控制面板", icon="sliders-horizontal",
          desc="硬體狀態監視", order=1, accent=0x4A90D9)
def build():
    global scr, _enc_lb, _btn_lb, _encC_lb
    nav.reset()
    scr = lv.obj(None)
    scr.set_style_bg_color(u.C(u.BG), 0)

    # 編碼器位置(上,全寬)
    c1 = u.mk_card(scr, 12, 6, u.W - 24, 56)
    u.mk_icon(c1, "refresh-cw", 10, 16, u.TEXT2)
    u.mk_label(c1, "編碼器位置", 30, 12, u.TEXT2, u.ZH)
    _enc_lb = lv.label(c1)
    _enc_lb.align(lv.ALIGN.RIGHT_MID, -10, 2)
    _enc_lb.set_style_text_font(u.F_NUM_L, 0)
    _enc_lb.set_style_text_color(u.C(u.PRIMARY), 0)
    _enc_lb.set_text("0")
    nav.add(c1, ITEM_INFO)   # 唯讀聚焦

    # 按鍵狀態(下,左右兩欄)
    c2 = u.mk_card(scr, 12, 70, 148, 84)
    u.mk_label(c2, "btn", 10, 8, u.TEXT2, u.ZH)
    u.mk_icon(c2, "square", 10, 40, u.TEXT2)
    _btn_lb = lv.label(c2)
    _btn_lb.set_pos(38, 40)
    _btn_lb.set_style_text_font(u.F_NUM_M, 0)
    _btn_lb.set_style_text_color(u.C(u.TEXT3), 0)
    _btn_lb.set_text("OFF")
    nav.add(c2, ITEM_INFO)

    c3 = u.mk_card(scr, 166, 70, u.W - 24 - 154, 84)
    u.mk_label(c3, "encC", 10, 8, u.TEXT2, u.ZH)
    u.mk_icon(c3, "square", 10, 40, u.TEXT2)
    _encC_lb = lv.label(c3)
    _encC_lb.set_pos(38, 40)
    _encC_lb.set_style_text_font(u.F_NUM_M, 0)
    _encC_lb.set_style_text_color(u.C(u.TEXT3), 0)
    _encC_lb.set_text("OFF")
    nav.add(c3, ITEM_INFO)

    u.fade_in(c1, dy=5, time_ms=280, delay_ms=40)
    u.fade_in(c2, dy=5, time_ms=280, delay_ms=120)
    u.fade_in(c3, dy=5, time_ms=280, delay_ms=200)
    nav.paint()
    return scr


def _read_vbtn(vbtn_id):
    try:
        from lib.hw_manager import HW
        return HW.get(HW.VBTN, vbtn_id) or 0
    except Exception:
        return 0


def on_enter(): pass
def on_leave(): pass

def on_enc(d):
    nav.enc(d)

def on_confirm():
    nav.confirm()   # info 項 confirm 無副作用
    return None

def on_exit():
    return nav.exit()   # 非編輯態 → False → 回 launcher

def update(run):
    if run % 10 != 0:
        return
    try:
        from lib.sys_bus import bus
        _enc_lb.set_text(str(bus.shared.get("_enc_pos", 0)))
        btn = _read_vbtn(0)
        encC = _read_vbtn(1)
        _btn_lb.set_text("ON" if btn else "OFF")
        _btn_lb.set_style_text_color(u.C(u.SUCCESS if btn else u.TEXT3), 0)
        _encC_lb.set_text("ON" if encC else "OFF")
        _encC_lb.set_style_text_color(u.C(u.SUCCESS if encC else u.TEXT3), 0)
    except Exception:
        pass
