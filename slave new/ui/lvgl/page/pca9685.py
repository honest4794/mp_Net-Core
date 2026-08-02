# ui/lvgl/page/pca9685.py — PCA9685 I2C 總線檢查/示範播放頁
#
# 操作邏輯(使用者定義):
#   1. 連接 I2C 總線 → 按「掃描」→ 顯示掃描到的裝置 address 清單(device_list)
#   2. 選播放模式(mode):逐腳呼吸 / 全腳呼吸
#   3. 選目標 IC(target):廣播(-1,All-Call)+ 掃描到的裝置
#   4. 進頁即開始播放(on_enter post start),退頁即全熄停止(on_leave post stop+alloff)
#   5. 16 通道用左右八個小圓圈顯示當前亮度 + 腳 ID [0-15](唯讀)
#
# 無播放/暫停按鈕:生命週期驅動(on_enter start / on_leave stop)。
# 掃描/呼吸動畫實際執行是之後接的業務,本輪頁面把介面 + bus 空間 + 事件佇列做出來。

import lvgl as lv
try:
    from ui.lvgl.registry import register
    from ui.lvgl import ui_common as u
    from ui.lvgl import ui_common
except ImportError:
    from registry import register
    import ui_common as u
    import ui_common

MODE_OPTIONS = [0, 1]  # 0=逐腳呼吸, 1=全腳呼吸
MODE_LABELS = ["逐腳呼吸", "全腳呼吸"]
EVENT_KEY = "pca.actions"
DEV_KEY = "pca.devices"

scr = None
_scan_btn = None
_mode_lb = None
_target_lb = None
_dots = []            # 16 個圓圈物件
_dot_ids = []         # 16 個 ID label
_focusables = []
_fi = 0


@register(id="pca9685", title="PCA9685", icon="sun",
          desc="I2C PWM 檢查器", order=3, accent=0x1A73E8)
def build():
    global scr, _scan_btn, _mode_lb, _target_lb, _dots, _dot_ids, _focusables, _fi
    _focusables = []
    _fi = 0
    _dots = []
    _dot_ids = []

    scr = lv.obj(None)
    scr.set_style_bg_color(u.C(u.BG), 0)
    u.mk_appbar(scr, "PCA9685 檢查器", "")

    ui_common.begin_page("pca9685")

    # ── 掃描按鈕 + 模式/目標(頂部) ──
    _scan_btn = u.mk_btn(scr, "掃描", 12, 44, 64, 28, "primary")
    _focusables.append(("btn", _scan_btn))
    ui_common.declare("scan", "action", "掃描 I2C", dir="ui→ext",
                      event=EVENT_KEY)

    u.mk_label(scr, "模式", 84, 48, u.TEXT2, u.ZH)
    _mode_box = lv.obj(scr)
    _mode_box.set_size(70, 24)
    _mode_box.set_pos(116, 44)
    _mode_box.set_style_bg_color(u.C(u.SURFACE), 0)
    _mode_box.set_style_radius(6, 0)
    _mode_box.set_style_border_color(u.C(u.BORDER), 0)
    _mode_box.set_style_border_width(1, 0)
    _mode_box.set_style_pad_all(0, 0)
    _mode_box.remove_flag(lv.obj.FLAG.SCROLLABLE)
    _mode_lb = u.mk_label(_mode_box, MODE_LABELS[0], 8, 4, u.TEXT, u.ZH)
    _focusables.append(("mode", _mode_box))
    ui_common.declare("mode", "enum", "播放模式", dir="rw",
                      options=MODE_OPTIONS,
                      read=lambda: _read_enum("mode", 0),
                      apply=lambda v: _apply_mode(v))

    u.mk_label(scr, "目標", 196, 48, u.TEXT2, u.ZH)
    _target_box = lv.obj(scr)
    _target_box.set_size(76, 24)
    _target_box.set_pos(232, 44)
    _target_box.set_style_bg_color(u.C(u.SURFACE), 0)
    _target_box.set_style_radius(6, 0)
    _target_box.set_style_border_color(u.C(u.BORDER), 0)
    _target_box.set_style_border_width(1, 0)
    _target_box.set_style_pad_all(0, 0)
    _target_box.remove_flag(lv.obj.FLAG.SCROLLABLE)
    _target_lb = u.mk_label(_target_box, "廣播", 6, 4, u.TEXT, u.ZH)
    _focusables.append(("target", _target_box))
    ui_common.declare("target", "enum", "目標 IC", dir="rw",
                      options=[-1],  # 廣播;實際 options 動態綁 device_list
                      source=DEV_KEY,
                      read=lambda: _read_enum("target", -1),
                      apply=lambda v: _apply_target(v))

    # device_list(掃描結果,外部 task 寫 _ui_var)
    ui_common.declare("device_list", "list", "掃描裝置", dir="r",
                      source=DEV_KEY, read=None)

    # ── 16 通道圓圈指示(左 8 右 8) ──
    u.mk_label(scr, "通道亮度", 12, 80, u.TEXT2, u.ZH)
    _build_dots(scr)

    # ch0..ch15 唯讀 display(0-4095,由未來播放邏輯寫 state)
    for i in range(16):
        ui_common.declare("ch{}".format(i), "display",
                          "通道 {}".format(i), dir="r", idx_hint=i,
                          read=lambda _i=i: _read_enum("ch{}".format(_i), 0))

    _paint_focus()
    return scr


def _build_dots(parent):
    """左右各 8 個圓圈(2 欄 × 8 列),標 ID[0-15],顯示亮度(填色深淺)。
    左欄 x=30(ch0-7),右欄 x=186(ch8-15),每列高 15px。"""
    dot_r = 6
    cols = [30, 186]
    for col in range(2):
        x = cols[col]
        for row in range(8):
            idx = col * 8 + row
            y = 100 + row * 16
            # 圓圈(用 obj + radius)
            d = lv.obj(parent)
            d.set_size(dot_r * 2, dot_r * 2)
            d.set_pos(x, y)
            d.set_style_radius(dot_r, 0)
            d.set_style_bg_color(u.C(u.TRACK), 0)
            d.set_style_border_color(u.C(u.BORDER), 0)
            d.set_style_border_width(1, 0)
            d.set_style_pad_all(0, 0)
            d.remove_flag(lv.obj.FLAG.SCROLLABLE)
            _dots.append(d)
            # ID label(圓圈右側)
            lb = lv.label(parent)
            lb.set_text(str(idx))
            lb.set_pos(x + dot_r * 2 + 3, y - 2)
            lb.set_style_text_font(u.F_NUM_S, 0)
            lb.set_style_text_color(u.C(u.TEXT3), 0)
            _dot_ids.append(lb)


def _paint_focus():
    for i, (kind, wid) in enumerate(_focusables):
        u.set_focus(wid, i == _fi, editing=False)


def _read_enum(id_, default):
    try:
        from ui.lvgl import ui_space
        v = ui_space.get_value("pca9685", id_)
        return v if v is not None else default
    except Exception:
        return default


def _apply_mode(v):
    global _mode_lb
    idx = int(v) % len(MODE_LABELS)
    if _mode_lb:
        _mode_lb.set_text(MODE_LABELS[idx])


def _apply_target(v):
    global _target_lb
    try:
        from lib.sys_bus import bus
        var = bus.shared.get("_ui_var", {})
        devs = var.get(DEV_KEY, [])
        if int(v) == -1 or not devs:
            label = "廣播"
        else:
            label = "0x{:02X}".format(int(v))
        if _target_lb:
            _target_lb.set_text(label)
    except Exception:
        pass


def _options_target():
    """target 的動態 options:[-1=廣播] + device_list。"""
    try:
        from lib.sys_bus import bus
        var = bus.shared.get("_ui_var", {})
        devs = var.get(DEV_KEY, [])
        return [-1] + list(devs)
    except Exception:
        return [-1]


# ====== 頁面接口 ======

def on_enter():
    """進頁即開始播放:post start 事件。"""
    ui_common.post_action(EVENT_KEY, {"action": "start"})


def on_leave():
    """退頁即全熄停止:post stop+alloff 事件。"""
    ui_common.post_action(EVENT_KEY, {"action": "stop", "alloff": True})


def on_enc(d):
    global _fi
    kind, _wid = _focusables[_fi]
    if kind == "mode":
        cur = _read_enum("mode", 0) or 0
        nxt = (int(cur) + (1 if d > 0 else -1)) % len(MODE_OPTIONS)
        _apply_mode(nxt)
        try:
            from ui.lvgl import ui_space
            ui_space.set_value("pca9685", "mode", nxt)
        except Exception:
            pass
        return
    if kind == "target":
        opts = _options_target()
        cur = _read_enum("target", -1)
        try:
            ci = opts.index(int(cur)) if int(cur) in opts else 0
        except Exception:
            ci = 0
        ni = (ci + (1 if d > 0 else -1)) % len(opts)
        _apply_target(opts[ni])
        try:
            from ui.lvgl import ui_space
            ui_space.set_value("pca9685", "target", opts[ni])
        except Exception:
            pass
        return
    _fi = (_fi + (1 if d > 0 else -1)) % len(_focusables)
    _paint_focus()


def on_confirm():
    kind, _wid = _focusables[_fi]
    if kind == "btn":
        # 掃描按鈕:post scan 事件(外部 task 消費,執行 I2C scan 寫 device_list)
        ui_common.post_action(EVENT_KEY, {"action": "scan"})
        print("[pca9685] scan requested")
    return None


def on_exit():
    return False


def update(run):
    if run % 8 != 0:
        return
    try:
        from ui.lvgl import ui_space
        # 16 通道圓圈亮度(0-4095 → 填色深淺)
        for i in range(16):
            v = ui_space.get_value("pca9685", "ch{}".format(i)) or 0
            v = max(0, min(4095, int(v)))
            # 亮度越高 → 顏色越亮(從 TRACK 到 PRIMARY)
            ratio = v / 4095.0
            if ratio > 0.05:
                _dots[i].set_style_bg_color(u.C(u.PRIMARY), 0)
                _dots[i].set_style_opa(int(80 + 175 * ratio), 0)
            else:
                _dots[i].set_style_bg_color(u.C(u.TRACK), 0)
                _dots[i].set_style_opa(255, 0)
    except Exception:
        pass
