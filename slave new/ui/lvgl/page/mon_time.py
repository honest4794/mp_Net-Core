# ui/lvgl/page/mon_time.py — 模式/亮度/倒數計時頁(橫屏 320×240)
#
# 佈局:
#   左欄(x=6,w=104):lv_list 顯示模式清單。enc 選 list → confirm 進編輯 →
#                    enc 上下選模式 → confirm/exit 退出(選中即寫 bus)。
#   右欄(x=116,w=198):
#     上 亮度(slider)
#     中 倒數時間(arc 進度 + 中央時間文字)
#     下 Bit7/Bit6 旗標狀態 + 兩個切換按鈕
#
# 協議對接(與 action_task_1.py 共享同一 byte):
#   bus.shared["_display_mode"] = mode byte(Bit7=特殊, Bit6=保留, Bit5-0=模式值)
#   bus.shared["_display_brightness"] = 亮度
#   bus.shared["_display_time"] = 剩餘秒數(0-255)
#   bus.shared["_display_running"] = 計時中(本頁自用,協議無此欄)
#   mon_time dict 為本頁快取(is_running 等)
import lvgl as lv
from ui.lvgl.registry import register
from ui.lvgl import ui_common as u
from ui.lvgl.nav import Nav, ITEM_LIST, ITEM_SLIDER, ITEM_BUTTON

MODE_LABELS = ["模式 1", "模式 2", "模式 3", "模式 4", "模式 5"]
_TIME_MAX = 255   # time 欄位上限(1 byte),arc 滿圓 = 255
_BIT7 = 0x80      # 特殊模式旗標
_BIT6 = 0x40      # 保留旗標(目標頂部/底部)
_MODE_MASK = 0x3F

nav = Nav()
scr = None
_mode_list = None
_mode_btns = []
_bright_sl = _bright_lb = _time_lb = _time_arc = _run_lb = None
_bit7_lb = _bit6_lb = None
_last_txt = {}


@register(id="mon_time", title="倒數計時", icon="clock",
          desc="模式·亮度·計時", order=2, accent=0xF9AB00)
def build():
    global scr, _mode_list, _mode_btns
    global _bright_sl, _bright_lb, _time_lb, _time_arc, _run_lb
    global _bit7_lb, _bit6_lb, _last_txt
    _last_txt = {}
    nav.reset()

    scr = lv.obj(None)
    scr.set_style_bg_color(u.C(u.BG), 0)

    # 左欄:模式清單(lv_list)
    lx, lw = 6, 104
    rx = lx + lw + 6
    rw = u.W - 6 - rx
    _mode_list, _mode_btns = u.mk_list(scr, lx, 6, lw, u.H - 12, MODE_LABELS)
    nav.add(_mode_list, ITEM_LIST, on_change=_sel_mode_delta)

    # 右欄上:亮度
    c2 = u.mk_card(scr, rx, 6, rw, 54)
    u.mk_label(c2, "亮度", 8, 6, u.TEXT2, u.ZH)
    _bright_lb = lv.label(c2)
    _bright_lb.align(lv.ALIGN.TOP_RIGHT, -8, 6)
    _bright_lb.set_style_text_font(u.F_NUM_M, 0)
    _bright_lb.set_style_text_color(u.C(u.PRIMARY), 0)
    _bright_lb.set_text("0")
    _bright_sl = u.mk_slider(c2, 8, 34, rw - 16, 0, 36, 0)
    nav.add(_bright_sl, ITEM_SLIDER, on_change=_adj_bright)

    # 右欄中:倒數時間(arc 進度 + 中央時間文字)
    c3 = u.mk_card(scr, rx, 66, rw, 86)
    u.mk_label(c3, "剩餘時間", 8, 6, u.TEXT2, u.ZH)
    arc_sz = 56
    arc_x, arc_y = 10, 22
    _time_arc = u.mk_arc(c3, arc_x, arc_y, arc_sz, u.PRIMARY, lo=0, hi=_TIME_MAX)
    _time_arc.set_value(_TIME_MAX)
    _time_lb = lv.label(c3)
    # 置中於 arc(絕對定位,避免 align_to binding 差異)
    _time_lb.set_pos(arc_x + arc_sz // 2 - 16, arc_y + arc_sz // 2 - 7)
    _time_lb.set_style_text_font(u.F_NUM_M, 0)
    _time_lb.set_style_text_color(u.C(u.TEXT), 0)
    _time_lb.set_text("00:00")
    # 狀態(右上)
    _run_lb = lv.label(c3)
    _run_lb.align(lv.ALIGN.TOP_RIGHT, -8, 6)
    _run_lb.set_style_text_font(u.F_NUM_S, 0)
    _run_lb.set_style_text_color(u.C(u.TEXT3), 0)
    _run_lb.set_text("待機")

    # 右欄下:Bit7 / Bit6 旗標(顯示 + 切換按鈕)
    c4 = u.mk_card(scr, rx, 158, rw, u.H - 12 - 158)
    u.mk_label(c4, "旗標", 8, 6, u.TEXT2, u.ZH)
    # Bit7
    _bit7_lb = lv.label(c4)
    _bit7_lb.set_pos(8, 26)
    _bit7_lb.set_style_text_font(u.F_NUM_S, 0)
    _bit7_lb.set_text("Bit7 特殊:OFF")
    btn7 = u.mk_btn(c4, "Bit7", rw - 56, 22, 44, 22, "secondary")
    nav.add(btn7, ITEM_BUTTON, on_change=_toggle_bit7)
    # Bit6
    _bit6_lb = lv.label(c4)
    _bit6_lb.set_pos(8, 44)
    _bit6_lb.set_style_text_font(u.F_NUM_S, 0)
    _bit6_lb.set_text("Bit6 保留:OFF")
    btn6 = u.mk_btn(c4, "Bit6", rw - 56, 44, 44, 22, "secondary")
    nav.add(btn6, ITEM_BUTTON, on_change=_toggle_bit6)

    u.fade_in(_mode_list, dy=5, time_ms=280, delay_ms=40)
    u.fade_in(c2, dy=5, time_ms=280, delay_ms=120)
    u.fade_in(c3, dy=5, time_ms=280, delay_ms=200)
    u.fade_in(c4, dy=5, time_ms=280, delay_ms=280)
    _sync_list()
    nav.paint()
    return scr


# ═══ bus 讀寫(與 action_task_1 共享 _display_* 欄位) ═══

def _mode_byte():
    """讀完整 mode byte(含旗標)。"""
    from lib.sys_bus import bus
    return int(bus.shared.get("_display_mode", 0)) & 0xFF


def _set_mode_byte(v):
    from lib.sys_bus import bus
    bus.shared["_display_mode"] = int(v) & 0xFF


def _state():
    """本頁自用快取 dict(非協議欄位,如 is_running)。"""
    from lib.sys_bus import bus
    s = bus.shared.get("mon_time")
    if not isinstance(s, dict):
        s = {}
        bus.shared["mon_time"] = s
    return s


def _sync_list():
    """依 mode byte 低 6 bit 同步 list 選中高亮。"""
    cur = _mode_byte() & _MODE_MASK
    cur = cur % len(MODE_LABELS)
    u.list_select(_mode_btns, cur, editing=nav.is_editing())


def _sel_mode_delta(dd):
    """編輯態 enc:上下移模式選擇(只改低 6 bit,保留旗標)。"""
    mb = _mode_byte()
    flags = mb & ~_MODE_MASK
    val = (mb & _MODE_MASK) + dd
    val = val % len(MODE_LABELS)
    _set_mode_byte(flags | val)
    _sync_list()


def _toggle_bit7():
    mb = _mode_byte()
    _set_mode_byte(mb ^ _BIT7)
    _refresh_bits()


def _toggle_bit6():
    mb = _mode_byte()
    _set_mode_byte(mb ^ _BIT6)
    _refresh_bits()


def _refresh_bits():
    mb = _mode_byte()
    b7 = bool(mb & _BIT7)
    b6 = bool(mb & _BIT6)
    _bit7_lb.set_text("Bit7 特殊:" + ("ON" if b7 else "OFF"))
    _bit7_lb.set_style_text_color(u.C(u.SUCCESS if b7 else u.TEXT3), 0)
    _bit6_lb.set_text("Bit6 保留:" + ("ON" if b6 else "OFF"))
    _bit6_lb.set_style_text_color(u.C(u.SUCCESS if b6 else u.TEXT3), 0)


def _adj_bright(dd):
    """編輯態 enc:調亮度。"""
    from lib.sys_bus import bus
    v = max(0, min(36, _bright_sl.get_value() + dd))
    _bright_sl.set_value(v, 0)
    _bright_lb.set_text(str(v))
    bus.shared["_display_brightness"] = v


# ====== 頁面接口(轉發給 nav) ======

def on_enter(): pass

def on_leave():
    if nav.is_editing():
        nav.exit()
        _sync_list()

def on_enc(d):
    nav.enc(d)
    if nav.current_kind() == ITEM_LIST:
        _sync_list()

def on_confirm():
    nav.confirm()
    _sync_list()
    return None

def on_exit():
    consumed = nav.exit()
    _sync_list()
    return consumed

def update(run):
    if run % 10 != 0:
        return
    try:
        from lib.sys_bus import bus
        # 模式 list(若不在 list 編輯態,跟 bus 同步)
        if not (nav.is_editing() and nav.current_kind() == ITEM_LIST):
            _sync_list()
        # 旗標
        _refresh_bits()
        # 亮度
        b = int(bus.shared.get("_display_brightness", _bright_sl.get_value()))
        if 0 <= b <= 36 and _bright_sl.get_value() != b:
            _bright_sl.set_value(b, 0)
            _bright_lb.set_text(str(b))
        # 倒數時間(arc + 文字)
        t = int(bus.shared.get("_display_time", 0))
        t = max(0, min(_TIME_MAX, t))
        mtxt = "{:02d}:{:02d}".format(*divmod(t, 60))
        if _last_txt.get("time") != mtxt:
            _last_txt["time"] = mtxt
            _time_lb.set_text(mtxt)
        try:
            _time_arc.set_value(t, 0)
        except Exception:
            pass
        # 計時狀態
        r = bool(_state().get("is_running", 0))
        rtxt = "計時中" if r else "待機"
        if _last_txt.get("run") != rtxt:
            _last_txt["run"] = rtxt
            _run_lb.set_text(rtxt)
            _run_lb.set_style_text_color(u.C(u.SUCCESS if r else u.TEXT3), 0)
    except Exception:
        pass
