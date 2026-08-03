# ui/lvgl/page/control_panel.py — 模式/亮度/倒數計時頁(橫屏 320×240)
#
# 佈局:
#   左欄(x=6,w=104):lv_list 顯示模式清單。enc 選 list → confirm 進編輯 →
#                    enc 上下選模式 → confirm/exit 退出(選中即寫 bus)。
#   右欄(x=116,w=198):
#     上 亮度(slider)
#     中 倒數時間(arc 進度 + 中央時間文字)
#     下 Bit7/Bit6 旗標狀態 + 兩個切換按鈕
#
# 協議對接(混搭環境:本頁是控制端也是被控制端):
#   指令(控制端): _send_cmd() → bus.shared["_display_cmd"] = {"mode":..,"brightness":..}
#                 → action_task_1._consume_display_cmd() → set_display_state() → UART 執行
#                 跨板時走 schema 0x1501(waiting_to_trash_actions.on_ctl 翻譯進同一欄位)
#   狀態(被控制端,顯示用): bus.shared["_display_mode/_brightness/_time"]
#                 action_task_1 執行後寫回,本頁 update() 讀同一位置顯示
#   control_panel dict 為本頁快取(is_running 等)
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
_bit7_led = _bit6_led = None
_last_txt = {}


@register(id="control_panel", title="控制面板", icon="sliders-horizontal",
          desc="模式·亮度·計時", order=1, accent=0xF9AB00)
def build():
    global scr, _mode_list, _mode_btns
    global _bright_sl, _bright_lb, _time_lb, _time_arc, _run_lb
    global _bit7_led, _bit6_led, _last_txt
    _last_txt = {}
    nav.reset()

    scr = lv.obj(None)
    scr.set_style_bg_color(u.C(u.BG), 0)

    # 左欄:模式清單(lv_list,字體放大用 F_NUM_M)
    lx, lw = 4, 96
    rx = lx + lw + 4
    rw = u.W - 4 - rx
    _mode_list, _mode_btns = u.mk_list(scr, lx, 4, lw, u.H - 8, MODE_LABELS,
                                       font=u.F_NUM_M)
    nav.add(_mode_list, ITEM_LIST, on_change=_sel_mode_delta)

    # 右欄上:亮度(無邊框卡片,省空間)
    c2 = _panel(scr, rx, 4, rw, 50)
    u.mk_label(c2, "亮度", 6, 4, u.TEXT2, u.ZH)
    _bright_lb = lv.label(c2)
    _bright_lb.align(lv.ALIGN.TOP_RIGHT, -6, 4)
    _bright_lb.set_style_text_font(u.F_NUM_M, 0)
    _bright_lb.set_style_text_color(u.C(u.PRIMARY), 0)
    _bright_lb.set_text("0")
    _bright_sl = u.mk_slider(c2, 6, 30, rw - 12, 0, 36, 0)
    nav.add(_bright_sl, ITEM_SLIDER, on_change=_adj_bright)

    # 右欄下:倒數時間 + 模式旗標 + 快捷(合併一區)
    #   上半:大 arc 置中 + 中央時間(F_NUM_XL)
    #   下排:狀態 / LED+切換 / 上一個下一個模式
    c3 = _panel(scr, rx, 58, rw, u.H - 4 - 58)
    # arc 置中上方
    arc_sz = 110
    arc_x = rw // 2 - arc_sz // 2
    arc_y = 6
    _time_arc = u.mk_arc(c3, arc_x, arc_y, arc_sz, u.PRIMARY, lo=0, hi=_TIME_MAX)
    _time_arc.set_value(_TIME_MAX)
    _time_lb = lv.label(c3)
    _time_lb.set_pos(arc_x + arc_sz // 2 - 34, arc_y + arc_sz // 2 - 14)
    _time_lb.set_style_text_font(u.F_NUM_XL, 0)
    _time_lb.set_style_text_color(u.C(u.TEXT), 0)
    _time_lb.set_text("00:00")
    # 狀態(arc 右上角)
    _run_lb = lv.label(c3)
    _run_lb.align(lv.ALIGN.TOP_RIGHT, -6, 8)
    _run_lb.set_style_text_font(u.F_NUM_M, 0)
    _run_lb.set_style_text_color(u.C(u.TEXT3), 0)
    _run_lb.set_text("待機")

    # 下排:左 LED+標籤按鈕(拍攝/可動,點擊切換)、右 模式快捷(▲▼)
    row_y = arc_y + arc_sz + 8
    # 拍攝(Bit7):LED + 按鈕(按鈕帶文字,點擊切換)
    _bit7_led = u.mk_led(c3, 8, row_y + 4, 12, on=False)
    btn7 = u.mk_btn(c3, "拍攝", 26, row_y, 56, 22, "secondary")
    nav.add(btn7, ITEM_BUTTON, on_change=_toggle_bit7)
    # 可動(Bit6)
    _bit6_led = u.mk_led(c3, 8, row_y + 30, 12, on=False)
    btn6 = u.mk_btn(c3, "可動", 26, row_y + 26, 56, 22, "secondary")
    nav.add(btn6, ITEM_BUTTON, on_change=_toggle_bit6)
    # 模式快捷(右側:上下排列,對齊 list 上下選的語意)
    btn_up = u.mk_btn(c3, "▲", rw - 40, row_y, 34, 22, "primary")
    nav.add(btn_up, ITEM_BUTTON, on_change=lambda: _sel_mode_delta(-1))
    btn_dn = u.mk_btn(c3, "▼", rw - 40, row_y + 26, 34, 22, "primary")
    nav.add(btn_dn, ITEM_BUTTON, on_change=lambda: _sel_mode_delta(1))

    u.fade_in(_mode_list, dy=5, time_ms=280, delay_ms=40)
    u.fade_in(c2, dy=5, time_ms=280, delay_ms=120)
    u.fade_in(c3, dy=5, time_ms=280, delay_ms=200)
    _sync_list()
    nav.paint()
    return scr


def _panel(parent, x, y, w, h):
    """輕量分區:無邊框、淡底色、pad 0(比 mk_card 省邊框空間)。"""
    c = lv.obj(parent)
    c.set_size(w, h)
    c.set_pos(x, y)
    c.set_style_bg_color(u.C(u.SURFACE), 0)
    c.set_style_radius(8, 0)
    c.set_style_border_width(0, 0)
    c.set_style_pad_all(0, 0)
    c.remove_flag(lv.obj.FLAG.SCROLLABLE)
    return c


# ═══ bus 讀寫(與 action_task_1 共享 _display_* 欄位) ═══

def _send_cmd(mode=None, brightness=None):
    """發指令給 action_task_1 via bus.shared['_display_cmd']。
    同板直寫；跨板時由 waiting_to_trash_actions.on_ctl 翻譯進同一欄位。
    action_task_1._consume_display_cmd() 統一消費 → set_display_state() → UART 執行。"""
    from lib.sys_bus import bus
    cmd = {}
    if mode is not None:
        cmd["mode"] = int(mode) & 0xFF
    if brightness is not None:
        cmd["brightness"] = int(brightness)
    if cmd:
        bus.shared["_display_cmd"] = cmd


def _mode_byte():
    """讀完整 mode byte(含旗標)。"""
    from lib.sys_bus import bus
    return int(bus.shared.get("_display_mode", 0)) & 0xFF


def _set_mode_byte(v):
    """發完整 mode 指令給 action_task_1（不再直寫 _display_mode 狀態欄位）。
    action_task_1 執行後會把最終狀態寫回 _display_mode，update() 讀回顯示。"""
    _send_cmd(mode=int(v) & 0xFF)


def _state():
    """本頁自用快取 dict(非協議欄位,如 is_running)。"""
    from lib.sys_bus import bus
    s = bus.shared.get("control_panel")
    if not isinstance(s, dict):
        s = {}
        bus.shared["control_panel"] = s
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
    u.led_set(_bit7_led, b7)
    u.led_set(_bit6_led, b6)


def _adj_bright(dd):
    """編輯態 enc:調亮度。發指令給 action_task_1(不直寫狀態欄位)。"""
    v = max(0, min(36, _bright_sl.get_value() + dd))
    _bright_sl.set_value(v, 0)
    _bright_lb.set_text(str(v))
    _send_cmd(brightness=v)


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
