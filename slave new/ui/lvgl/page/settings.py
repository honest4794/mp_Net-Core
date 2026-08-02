# ui/lvgl/page/settings.py — 系統設定頁
#
# 1 個 rw 開關(wifi_enable) + 5 個唯讀字串顯示。
# 字串只顯示不可編輯(編輯交 web UI);值由 board._fill_var_strings() 填入 _ui_var。

import lvgl as lv
try:
    from ui.lvgl.registry import register
    from ui.lvgl import ui_common as u
    from ui.lvgl import ui_common
except ImportError:
    from registry import register
    import ui_common as u
    import ui_common

# 唯讀字串欄位:(_ui_var 子鍵, 顯示標籤, icon)
_STR_FIELDS = [
    ("hostname",   "主機名",   "settings"),
    ("master_IP",  "Master",  "wifi"),
    ("wifi_ssid",  "Wi-Fi",   "wifi"),
    ("slave_id",   "裝置 ID",  "shield"),
    ("mac",        "MAC",     "shield"),
]

scr = None
_wifi_sw = None
_str_lbs = {}
_focusables = []
_fi = 0


@register(id="settings", title="系統設定", icon="settings",
          desc="網路·裝置資訊", order=4, accent=0x7F8C8D)
def build():
    global scr, _wifi_sw, _str_lbs, _focusables, _fi
    _str_lbs = {}
    _focusables = []
    _fi = 0

    scr = lv.obj(None)
    scr.set_style_bg_color(u.C(u.BG), 0)
    u.mk_appbar(scr, "系統設定", "RO")

    ui_common.begin_page("settings")

    # ── Wi-Fi 開關(頂部) ──
    c1 = u.mk_card(scr, 12, 48, 296, 52)
    u.mk_icon(c1, "wifi", 10, 14, u.TEXT2)
    u.mk_label(c1, "Wi-Fi 啟用", 32, 16, u.TEXT, u.ZH)
    _wifi_sw = u.mk_switch(c1, 240, 14, on=False)
    _focusables.append(("sw", _wifi_sw))
    ui_common.declare("wifi_enable", "switch", "Wi-Fi 啟用", dir="rw",
                      read=lambda: u.sw_get(_wifi_sw),
                      apply=lambda v: _apply_wifi(v))

    # ── 裝置資訊(唯讀字串列表) ──
    y = 108
    for key, label, ico in _STR_FIELDS:
        c = u.mk_card(scr, 12, y, 296, 24)
        u.mk_icon(c, ico, 6, 4, u.TEXT3)
        u.mk_label(c, label, 24, 4, u.TEXT2, u.ZH)
        lb = lv.label(c)
        lb.set_pos(100, 4)
        lb.set_style_text_color(u.C(u.TEXT), 0)
        if u.ZH:
            lb.set_style_text_font(u.ZH, 0)
        lb.set_text("—")
        _str_lbs[key] = lb
        y += 26

    _paint_focus()
    return scr


def _paint_focus():
    for i, (kind, wid) in enumerate(_focusables):
        u.set_focus(wid, i == _fi, editing=False)


def _apply_wifi(v):
    u.sw_set(_wifi_sw, bool(v))


def _get_str(key):
    try:
        from lib.sys_bus import bus
        var = bus.shared.get("_ui_var", {})
        return var.get("sys", {}).get(key, "—") or "—"
    except Exception:
        return "—"


# ====== 頁面接口 ======

def on_enter():
    pass

def on_leave():
    pass

def on_enc(d):
    global _fi
    if not _focusables:
        return
    _fi = (_fi + (1 if d > 0 else -1)) % len(_focusables)
    _paint_focus()

def on_confirm():
    kind, _wid = _focusables[_fi]
    if kind == "sw":
        new = not u.sw_get(_wifi_sw)
        _apply_wifi(new)
        try:
            from ui.lvgl import ui_space
            ui_space.set_value("settings", "wifi_enable", 1 if new else 0)
        except Exception:
            pass
        print("[settings] wifi_enable -> {}".format("ON" if new else "OFF"))
    return None

def on_exit():
    return False

def update(run):
    if run % 20 != 0:
        return
    # 刷新唯讀字串(從 _ui_var)
    for key, _label, _ico in _STR_FIELDS:
        lb = _str_lbs.get(key)
        if lb:
            lb.set_text(str(_get_str(key)))
