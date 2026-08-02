# ui/lvgl/ui_common.py — lvgl-console-ui 共用 UI 層 + 控制平面 helper
#
# 把 lvgl-console-ui 設計稿（colors_and_type.css / components.css）
# 轉成 LVGL9 橫屏 320×240 可用的 palette / 字體 / 元件 builder。
#
# 注意（對應 DEV_NOTES 踩坑）：
#   - 字體用 getattr fallback（binding 沒編到的尺寸自動降級）
#   - 枚举常數能用整數就用整數（soft reboot 後常數可能不穩）
#   - 所有容器 pad_all(0) + 移除 SCROLLABLE（預設樣式會干擾佈局）
#
# ★新增（slave new 控制平面）:
#   begin_page(page_id) / declare(id, type, label, dir, ...) — 在 build() 宣告 widget,
#   由 ui_space.py 的 sync() 每幀呼叫 read() 寫 state、讀 ctrl 呼叫 apply()。

import lvgl as lv

# ====== 版面（橫屏 ST7789，MADCTL=0x60） ======
W = 320
H = 240

# ====== Palette（來自 colors_and_type.css） ======
BG       = 0xF5F5F5   # --bg-base-secondary
SURFACE  = 0xFFFFFF   # --bg-base-default
BORDER   = 0xE0E0E0   # --border-neutral-l1
TEXT     = 0x1F1F1F   # --text-default
TEXT2    = 0x5F5F5F   # --text-secondary
TEXT3    = 0x8F8F8F   # --text-tertiary
PRIMARY  = 0x1A73E8   # --bg-brand
SUCCESS  = 0x188038   # --status-success-default
WARNING  = 0xF9AB00   # --status-warning-default
DANGER   = 0xD93025   # --status-danger-default
TRACK    = 0xDADCE0   # --bg-overlay-l3
FOCUS_BG = 0xE8F0FE   # 焦點卡片底色（brand 淡色）
DANGER_BG = 0xFCE8E6  # danger-subtle 按鈕底色

# ====== 字體 ======
# 繁體中文 .bin 字體須在 lv.init() 之後才能載入，
# 因此用 init_fonts() 延遲載入（由 board 在 lv.init() 後呼叫）。
ZH = None

def init_fonts():
    """在 lv.init() 完成後呼叫，載入繁體中文 .bin 字體。
    用 Python open() 讀檔 → binfont_create_from_buffer()，
    繞過 LVGL FS 驅動（lv_conf 未啟用 POSIX/STDIO/FATFS）。
    slave new 佈局:/ui/lvgl/src/zh_hant_16.bin
    """
    global ZH
    if ZH:
        return
    # 方法：Python 讀檔 → buffer 載入
    try:
        with open("/ui/lvgl/src/zh_hant_16.bin", "rb") as fp:
            buf = fp.read()
        print("[font] read {} bytes".format(len(buf)))
        f = None
        if hasattr(lv, "binfont_create_from_buffer"):
            try:
                f = lv.binfont_create_from_buffer(bytearray(buf), len(buf))
            except TypeError:
                # binding 可能只需一個參數（自動推斷 size）
                try:
                    f = lv.binfont_create_from_buffer(bytearray(buf))
                except Exception as e2:
                    print("[font] from_buffer(1arg) fail:", e2)
            except Exception as e1:
                print("[font] from_buffer(2arg) fail:", e1)
        else:
            print("[font] binfont_create_from_buffer NOT in binding")
        if f:
            ZH = f
            print("[font] loaded from buffer OK")
            return
        print("[font] from_buffer returned None")
    except Exception as _e:
        print("[font] buffer load fail:", _e)
    # 最後 fallback：內建 CJK（通常未編入）
    ZH = getattr(lv, "font_simsun_16_cjk", None)
    print("[font] fallback:", ZH)

# 此 binding 沒有 lv.font_default()，用 montserrat_14（LVGL 主題預設字體）兜底
_BASE_FONT = None
for _n in ("font_montserrat_14", "font_montserrat_16", "font_montserrat_12",
           "font_montserrat_18", "font_montserrat_20"):
    _BASE_FONT = getattr(lv, _n, None)
    if _BASE_FONT:
        break

# ====== 圖示字體（lv_icons.py，由 tools/ 工具產生） ======
# 板上沒有 icons_16.bin 時全部降級為 None，不影響其他功能。
_icon_font = None

def _icon_font_ready():
    """回傳 icon 字體（首次使用才載入）。"""
    global _icon_font
    if _icon_font is None:
        try:
            from lv_icons import load_icon_font
            _icon_font = load_icon_font()
        except Exception as e:
            print("[icons] skip:", e)
            _icon_font = False
    return _icon_font or None

def mk_icon(parent, name, x, y, color=TEXT2):
    """建立圖示 label（lucide 名）。icon 字體不可用時回傳 None。"""
    f = _icon_font_ready()
    if f is None:
        return None
    from lv_icons import ICONS
    if name not in ICONS:
        return None
    lb = lv.label(parent)
    lb.set_text(ICONS[name])
    lb.set_pos(x, y)
    lb.set_style_text_color(C(color), 0)
    lb.set_style_text_font(f, 0)
    return lb

# ====== 動效 helper（lv_ui_fx.py，由 tools/ 工具產生） ======
# 板上沒有 lv_ui_fx.py 時降級為 no-op。
try:
    from lv_ui_fx import pulse as _fx_pulse, fade_in as _fx_fade_in
except Exception:
    _fx_pulse = _fx_fade_in = None

def pulse(wid, period_ms=1500, min_opa=110, max_opa=255):
    if _fx_pulse:
        return _fx_pulse(wid, period_ms, min_opa, max_opa)
    return None

def fade_in(wid, dy=6, time_ms=300, delay_ms=0):
    if _fx_fade_in:
        return _fx_fade_in(wid, dy, time_ms, delay_ms)
    return None

def font(*names):
    """依序嘗試字體名，全部沒有就回 montserrat 基本字體。"""
    for n in names:
        f = getattr(lv, n, None)
        if f:
            return f
    return _BASE_FONT

# 數字/拉丁用 Montserrat（binding 有編到哪個尺寸就用哪個）
F_NUM_L = font("font_montserrat_22", "font_montserrat_20", "font_montserrat_18")
F_NUM_M = font("font_montserrat_16", "font_montserrat_14")
F_NUM_S = font("font_montserrat_12", "font_montserrat_10")

# ====== 基礎 builder ======

def C(hexval):
    return lv.color_hex(hexval)

def mk_label(parent, text, x, y, color=TEXT, f=None):
    lb = lv.label(parent)
    lb.set_text(text)
    lb.set_pos(x, y)
    lb.set_style_text_color(C(color), 0)
    if f:
        lb.set_style_text_font(f, 0)
    elif ZH:
        lb.set_style_text_font(ZH, 0)
    return lb

def mk_card(parent, x, y, w, h):
    c = lv.obj(parent)
    c.set_size(w, h)
    c.set_pos(x, y)
    c.set_style_bg_color(C(SURFACE), 0)
    c.set_style_radius(10, 0)
    c.set_style_border_color(C(BORDER), 0)
    c.set_style_border_width(1, 0)
    c.set_style_pad_all(0, 0)
    c.remove_flag(lv.obj.FLAG.SCROLLABLE)
    return c

def mk_appbar(scr, title, right=""):
    """頂欄 36px：返回符號 + 標題 + 右側狀態。"""
    bar = lv.obj(scr)
    bar.set_size(W, 36)
    bar.set_pos(0, 0)
    bar.set_style_bg_color(C(SURFACE), 0)
    bar.set_style_radius(0, 0)
    bar.set_style_border_color(C(BORDER), 0)
    bar.set_style_border_width(1, 0)
    bar.set_style_pad_all(0, 0)
    bar.remove_flag(lv.obj.FLAG.SCROLLABLE)

    # 返回指示（BTN42）：優先 icon 字體,沒有就文字符號
    back = mk_icon(bar, "chevron-left", 8, 9, TEXT2)
    if back is None:
        mk_label(bar, "<", 10, 9, TEXT2, F_NUM_M)
    mk_label(bar, title, 28, 9, TEXT, ZH)
    r = None
    if right:
        r = mk_label(bar, right, 0, 0, TEXT3, F_NUM_S)
        r.align(lv.ALIGN.RIGHT_MID, -10, 0)
    return bar, r

def mk_btn(parent, text, x, y, w, h, kind="primary"):
    """kind: primary / secondary / danger-subtle"""
    b = lv.button(parent)
    b.set_size(w, h)
    b.set_pos(x, y)
    if kind == "primary":
        b.set_style_bg_color(C(PRIMARY), 0)
        b.set_style_border_width(0, 0)
        fg = 0xFFFFFF
    elif kind == "danger":
        b.set_style_bg_color(C(DANGER_BG), 0)
        b.set_style_border_width(0, 0)
        fg = DANGER
    else:  # secondary
        b.set_style_bg_color(C(SURFACE), 0)
        b.set_style_border_color(C(BORDER), 0)
        b.set_style_border_width(1, 0)
        fg = TEXT2
    b.set_style_radius(8, 0)
    lb = lv.label(b)
    lb.set_text(text)
    lb.align(lv.ALIGN.CENTER, 0, 0)
    lb.set_style_text_color(C(fg), 0)
    if ZH:
        lb.set_style_text_font(ZH, 0)
    return b

def mk_slider(parent, x, y, w, lo, hi, val, color=PRIMARY):
    s = lv.slider(parent)
    s.set_size(w, 8)
    s.set_pos(x, y)
    s.set_range(lo, hi)
    s.set_value(val, 0)   # 0 = ANIM_OFF
    s.set_style_bg_color(C(TRACK), lv.PART.MAIN)
    s.set_style_radius(4, lv.PART.MAIN)
    s.set_style_bg_color(C(color), lv.PART.INDICATOR)
    s.set_style_radius(4, lv.PART.INDICATOR)
    s.set_style_bg_color(C(color), lv.PART.KNOB)
    s.set_style_radius(8, lv.PART.KNOB)
    s.set_style_pad_all(4, lv.PART.KNOB)
    return s

def mk_switch(parent, x, y, on=False, color=PRIMARY):
    s = lv.switch(parent)
    s.set_size(44, 24)
    s.set_pos(x, y)
    s.set_style_bg_color(C(TRACK), lv.PART.MAIN)
    s.set_style_radius(12, lv.PART.MAIN)
    s.set_style_bg_color(C(color), lv.PART.INDICATOR)
    s.set_style_radius(12, lv.PART.INDICATOR)
    s.set_style_bg_color(C(SURFACE), lv.PART.KNOB)
    s.set_style_radius(10, lv.PART.KNOB)
    s.set_style_shadow_width(0, lv.PART.KNOB)
    if on:
        sw_set(s, True)
    return s


# ====== switch state 防護 wrapper（binding 版本差異） ======
# 不同 LVGL binding 的 switch/obj 狀態 API 名稱不一致:
#   有 add_state/clear_state/has_state(LVGL 9.x),也有 add_flag/clear_flag(舊版)
#   這裡全部 try,任一可用即可;都不行就 no-op(不崩潰)。

def _state_const():
    """取得 CHECKED 狀態常數(binding 差異防護)。"""
    try:
        return lv.STATE.CHECKED
    except Exception:
        return 1


def sw_set(sw, on):
    """設定 switch 開/關。跨 binding 防護。"""
    chk = _state_const()
    if on:
        for m in ("add_state", "add_flag"):
            fn = getattr(sw, m, None)
            if fn is not None:
                try:
                    fn(chk if m == "add_state" else getattr(lv.obj.STATE, "CHECKED", 0x1000))
                    return
                except TypeError:
                    try:
                        fn()
                        return
                    except Exception:
                        continue
                except Exception:
                    continue
    else:
        for m in ("clear_state", "clear_flag"):
            fn = getattr(sw, m, None)
            if fn is not None:
                try:
                    fn(chk if m == "clear_state" else getattr(lv.obj.STATE, "CHECKED", 0x1000))
                    return
                except TypeError:
                    try:
                        fn()
                        return
                    except Exception:
                        continue
                except Exception:
                    continue


def sw_get(sw):
    """讀 switch 是否開。跨 binding 防護。"""
    for m in ("has_state", "get_state"):
        fn = getattr(sw, m, None)
        if fn is not None:
            try:
                return bool(fn(_state_const()))
            except TypeError:
                try:
                    return bool(fn())
                except Exception:
                    continue
            except Exception:
                continue
    return False

def mk_arc(parent, x, y, size, color):
    """環形量表（不可調整，knob 隱藏）。"""
    a = lv.arc(parent)
    a.set_size(size, size)
    a.set_pos(x, y)
    a.set_range(0, 100)
    a.set_style_arc_width(8, lv.PART.MAIN)
    a.set_style_arc_color(C(TRACK), lv.PART.MAIN)
    a.set_style_arc_width(8, lv.PART.INDICATOR)
    a.set_style_arc_color(C(color), lv.PART.INDICATOR)
    # 隱藏 knob（不設透明會畫出一個圓點）
    a.set_style_arc_opa(0, lv.PART.KNOB)
    a.set_style_bg_opa(0, lv.PART.KNOB)
    a.set_style_outline_width(0, lv.PART.KNOB)
    return a

def mk_bar(parent, x, y, w, h, val, color=PRIMARY):
    b = lv.bar(parent)
    b.set_size(w, h)
    b.set_pos(x, y)
    b.set_range(0, 100)
    b.set_value(val, 0)
    b.set_style_bg_color(C(TRACK), lv.PART.MAIN)
    b.set_style_radius(4, lv.PART.MAIN)
    b.set_style_bg_color(C(color), lv.PART.INDICATOR)
    b.set_style_radius(4, lv.PART.INDICATOR)
    return b

# chart 常量（binding 差異防護）
_CHART_TYPE_LINE = getattr(getattr(lv, "CHART_TYPE", None), "LINE", 1)
_CHART_AXIS_Y = getattr(getattr(lv, "CHART_AXIS", None), "PRIMARY_Y", 0)

def mk_chart(parent, x, y, w, h, color, points=24, ymax=100):
    """迷你趨勢圖（LINE，無座標軸文字）。"""
    ch = lv.chart(parent)
    ch.set_size(w, h)
    ch.set_pos(x, y)
    ch.set_type(_CHART_TYPE_LINE)
    ch.set_point_count(points)
    # LVGL 9.3：set_range 改名為 set_axis_range(axis, min, max)
    # 某些 port(JS/wasm)較舊,用 set_range 或無 → 都 try
    try:
        ch.set_axis_range(_CHART_AXIS_Y, 0, ymax)
    except Exception:
        try:
            ch.set_range(0, ymax)
        except Exception:
            pass
    try:
        ch.set_div_line_count(3, 0)
    except Exception:
        pass
    # 樣式設定:某些 port(JS/wasm)的 chart 缺部分 set_style_* → 整段保護,
    # 趨勢圖核心(軸/線/資料)不受影響。
    try:
        ch.set_style_bg_opa(0, 0)
        ch.set_style_border_width(0, 0)
        ch.set_style_pad_all(2, 0)
        ch.set_style_line_width(2, lv.PART.ITEMS)
        ch.set_style_line_color(C(color), lv.PART.ITEMS)
    except Exception:
        pass
    # LVGL 9.3：set_style_size 改為 (width, height, selector)；設 0 不畫資料點
    try:
        ch.set_style_size(0, 0, lv.PART.INDICATOR)
    except Exception:
        pass
    ser = ch.add_series(C(color), _CHART_AXIS_Y)
    return ch, ser

# ====== 焦點視覺 ======

def set_focus(wid, on, editing=False):
    """外框焦點環：藍=導覽中、琥珀=編輯中。"""
    if on:
        wid.set_style_outline_color(C(WARNING if editing else PRIMARY), 0)
        wid.set_style_outline_width(2, 0)
        wid.set_style_outline_pad(3, 0)
    else:
        wid.set_style_outline_width(0, 0)


# ══════════════════════════════════════════════════════
# ★控制平面 helper（slave new bus 空間宣告）
#
# page 在 build() 裡:
#   begin_page("overview")          # 標記此頁開始(清該頁 widget 暫存)
#   declare(id, type, label, dir, ...)  # 宣告一個 widget 綁定 bus 空間
#
# declare 會向 ui_space 註冊 widget 的 (arr, idx) 與 read/apply lambda。
# sync() 時 ui_space 透過這些 lambda 讀寫 widget ↔ 打包陣列。
# lambda 是 LVGL sync 時自己呼叫的橋,外部(action)只透過 bus 陣列存取,
# 不直接呼叫 widget 方法 → LVGL 仍是唯一摸 widget 的人(thread-safe)。
# ══════════════════════════════════════════════════════

_cur_page = None


def begin_page(page_id):
    """標記目前 build() 的頁面 id;清該頁舊 widget 暫存。"""
    global _cur_page
    _cur_page = page_id
    try:
        from ui.lvgl import ui_space
        ui_space.begin_page(page_id)
    except Exception as e:
        print("[ui] begin_page fail:", e)


def declare(id, type, label, dir="r", read=None, apply=None,
            options=None, source=None, event=None, scale=1, **extra):
    """宣告一個 widget 綁 bus 空間。

    type:  switch / display / slider / enum / list / str / action
    dir:   'r'(唯讀顯示) / 'rw'(可設)
    read:  callable() → 目前 widget 值(LVGL sync 時呼叫,寫 state)
    apply: callable(v) → 把 ctrl 值套到 widget(rw 才有,LVGL sync 時呼叫)
    options:  enum 用,選項清單(list)
    source:   list 用,指向 _ui_var 動態鍵
    event:    action 用,指向 _ui_var 事件佇列鍵(如 "pca.actions")
    scale:    display 數值定點放大(如溫度 ×100)
    extra:    額外 meta 原樣存進宣告(查詢可見)
    """
    if _cur_page is None:
        return
    try:
        from ui.lvgl import ui_space
        ui_space.declare(_cur_page, id, type, label, dir,
                         read=read, apply=apply, options=options,
                         source=source, event=event, scale=scale, **extra)
    except Exception as e:
        print("[ui] declare fail:", id, e)


def post_action(event_key, payload):
    """UI→外部:把一個事件 append 進 _ui_var[event_key] 佇列。
    例:按鈕按下、頁面 on_enter/on_leave 觸發的動作。
    外部 task 用 list.pop(0) 消費(本輪消費端可選做空殼)。"""
    try:
        from lib.sys_bus import bus
        var = bus.shared.get("_ui_var")
        if not isinstance(var, dict):
            return
        q = var.get(event_key)
        if not isinstance(q, list):
            q = []
            var[event_key] = q
        q.append(payload)
    except Exception as e:
        print("[ui] post_action fail:", event_key, e)
