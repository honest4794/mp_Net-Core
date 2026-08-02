# ui/lvgl/page/mon_time.py — 模式/亮度/倒數計時頁
#
# 移植自 micropython_some_drive/example/mon_time_testkit 的控制邏輯,
# 改走 slave new bus(取代原 UART)。
#   mode        模式 enum(0-4),rw
#   brightness  亮度 slider(0-36),rw
#   time_remaining  剩餘時間(秒),唯讀 display(由未來 timer task 寫 state)
#   is_running  計時中,唯讀 switch(由未來 timer task 寫 state)
#
# 計時邏輯本輪不做(由獨立 Timer task,之後接);頁面先把介面 + mode/brightness 的 rw 做出來。

import lvgl as lv
try:
    from ui.lvgl.registry import register
    from ui.lvgl import ui_common as u
    from ui.lvgl import ui_common
except ImportError:
    from registry import register
    import ui_common as u
    import ui_common

# 每個模式的倒數時長(秒),對應原 dp_config.json counter_time
COUNTER_TIME = [5, 4, 8, 3, 120]
MODE_LABELS = ["模式 1", "模式 2", "模式 3", "模式 4", "模式 5"]

scr = None
_mode_lb = None
_bright_sl = None
_bright_lb = None
_time_lb = None
_run_lb = None
_focusables = []
_fi = 0
_editing = False


@register(id="mon_time", title="倒數計時", icon="clock",
          desc="模式·亮度·計時", order=2, accent=0xF9AB00)
def build():
    global scr, _mode_lb, _bright_sl, _bright_lb, _time_lb, _run_lb
    global _focusables, _fi, _editing
    _focusables = []
    _fi = 0
    _editing = False

    scr = lv.obj(None)
    scr.set_style_bg_color(u.C(u.BG), 0)
    u.mk_appbar(scr, "倒數計時", "")

    ui_common.begin_page("mon_time")

    # ── 模式選擇(左) ──
    c1 = u.mk_card(scr, 12, 48, 148, 80)
    u.mk_label(c1, "模式", 10, 8, u.TEXT2, u.ZH)
    _mode_lb = lv.label(c1)
    _mode_lb.set_pos(10, 36)
    _mode_lb.set_style_text_font(u.F_NUM_L, 0)
    _mode_lb.set_style_text_color(u.C(u.PRIMARY), 0)
    _mode_lb.set_text(MODE_LABELS[0])
    u.mk_label(c1, "旋鈕切換", 10, 62, u.TEXT3, u.ZH)
    _focusables.append(("mode", _mode_lb))
    ui_common.declare("mode", "enum", "模式", dir="rw",
                      options=list(range(len(MODE_LABELS))),
                      read=lambda: _read_enum("mode", 0),
                      apply=lambda v: _apply_mode(v))

    # ── 亮度滑桿(右) ──
    c2 = u.mk_card(scr, 164, 48, 144, 80)
    u.mk_label(c2, "亮度", 10, 8, u.TEXT2, u.ZH)
    _bright_lb = lv.label(c2)
    _bright_lb.align(lv.ALIGN.TOP_RIGHT, -8, 8)
    _bright_lb.set_style_text_font(u.F_NUM_M, 0)
    _bright_lb.set_style_text_color(u.C(u.PRIMARY), 0)
    _bright_lb.set_text("0")
    _bright_sl = u.mk_slider(c2, 10, 50, 124, 0, 36, 0)
    _focusables.append(("slider", _bright_sl))
    ui_common.declare("brightness", "slider", "亮度", dir="rw",
                      read=lambda: _bright_sl.get_value(),
                      apply=lambda v: _apply_slider(v))

    # ── 倒數時間(下) ──
    c3 = u.mk_card(scr, 12, 136, 200, 88)
    u.mk_label(c3, "剩餘時間", 10, 8, u.TEXT2, u.ZH)
    _time_lb = lv.label(c3)
    _time_lb.align(lv.ALIGN.BOTTOM_RIGHT, -10, -8)
    _time_lb.set_style_text_font(u.F_NUM_L, 0)
    _time_lb.set_style_text_color(u.C(u.TEXT), 0)
    _time_lb.set_text("00:00")
    ui_common.declare("time_remaining", "display", "剩餘時間", dir="r",
                      read=lambda: 0)  # 由未來 timer task 寫 state

    # ── 計時狀態(右下) ──
    c4 = u.mk_card(scr, 220, 136, 88, 88)
    u.mk_label(c4, "狀態", 10, 8, u.TEXT2, u.ZH)
    _run_lb = lv.label(c4)
    _run_lb.align(lv.ALIGN.CENTER, 0, 8)
    _run_lb.set_style_text_font(u.F_NUM_M, 0)
    _run_lb.set_style_text_color(u.C(u.TEXT3), 0)
    _run_lb.set_text("待機")
    ui_common.declare("is_running", "switch", "計時中", dir="r",
                      read=lambda: 0)  # 由未來 timer task 寫 state

    _paint_focus()
    u.fade_in(c1, dy=5, time_ms=280, delay_ms=40)
    u.fade_in(c2, dy=5, time_ms=280, delay_ms=120)
    u.fade_in(c3, dy=5, time_ms=280, delay_ms=200)
    u.fade_in(c4, dy=5, time_ms=280, delay_ms=280)
    return scr


def _paint_focus():
    for i, (kind, wid) in enumerate(_focusables):
        u.set_focus(wid, i == _fi, editing=(_editing and i == _fi))


def _read_enum(_id, default):
    """讀 enum 的目前值(從打包陣列)。"""
    try:
        from ui.lvgl import ui_space
        v = ui_space.get_value("mon_time", _id)
        return v if v is not None else default
    except Exception:
        return default


def _apply_mode(v):
    global _mode_lb
    idx = int(v) % len(MODE_LABELS)
    if _mode_lb:
        _mode_lb.set_text(MODE_LABELS[idx])


def _apply_slider(v):
    global _bright_lb
    v = max(0, min(36, int(v)))
    _bright_sl.set_value(v, 0)
    if _bright_lb:
        _bright_lb.set_text(str(v))


# ====== 頁面接口 ======

def on_enter():
    pass

def on_leave():
    global _editing
    _editing = False

def on_enc(d):
    global _fi, _editing
    if _editing and _fi == 1:
        # 編輯亮度
        v = max(0, min(36, _bright_sl.get_value() + (1 if d > 0 else -1)))
        _apply_slider(v)
        return
    if _fi == 0:
        # 模式切換:旋一下就換下一個
        cur = _read_enum("mode", 0) or 0
        nxt = (int(cur) + (1 if d > 0 else -1)) % len(MODE_LABELS)
        _apply_mode(nxt)
        try:
            from ui.lvgl import ui_space
            ui_space.set_value("mon_time", "mode", nxt)
        except Exception:
            pass
        return
    _fi = (_fi + (1 if d > 0 else -1)) % len(_focusables)
    _paint_focus()

def on_confirm():
    global _editing
    kind, _wid = _focusables[_fi]
    if kind == "slider":
        _editing = not _editing
        _paint_focus()
    return None

def on_exit():
    global _editing
    if _editing:
        _editing = False
        _paint_focus()
        return True
    return False

def update(run):
    if run % 10 != 0:
        return
    try:
        from ui.lvgl import ui_space
        # 顯示模式(從打包陣列同步)
        m = ui_space.get_value("mon_time", "mode")
        if m is not None and _mode_lb:
            _mode_lb.set_text(MODE_LABELS[int(m) % len(MODE_LABELS)])
        # 剩餘時間(MM:SS)
        t = ui_space.get_value("mon_time", "time_remaining") or 0
        if _time_lb:
            mm, ss = divmod(int(t), 60)
            _time_lb.set_text("{:02d}:{:02d}".format(mm, ss))
        # 計時狀態
        r = ui_space.get_value("mon_time", "is_running")
        if _run_lb:
            if r:
                _run_lb.set_text("計時中")
                _run_lb.set_style_text_color(u.C(u.SUCCESS), 0)
            else:
                _run_lb.set_text("待機")
                _run_lb.set_style_text_color(u.C(u.TEXT3), 0)
    except Exception:
        pass
