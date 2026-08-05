# waiting_to_trash_actions.py
# 過渡期顯示控制協議（mode/brightness）— 對齊 jpeg_actions 模式。
#
# 跨板指令走 schema dispatch（ESP-NOW/UART/WebSocket），
# 翻譯成 bus.shared["_display_cmd"]，action_task_1 消費執行。
#
# 命名為 waiting_to_trash：這組 cmd 碼/欄位待日後重整協議時清理。
# 混搭環境：
#   - 遠端板 LVGL/按鈕 → ESP-NOW → 本板 dispatch → on_ctl → bus.shared["_display_cmd"]
#   - 本板 LVGL 頁面 → 直寫 bus.shared["_display_cmd"]（不過 dispatch，同板）
# 兩條路殊途同歸，action_task_1._consume_display_cmd() 統一消費。

from lib.sys_bus import bus

_NO_CHANGE = 0xFF   # u8 約定：255 = 不改該欄位


def on_ctl(ctx, args):
    """0x1501 — 設定 mode/brightness（跨板指令）。
    mode/brightness = 255 表示不改該欄位。"""
    mode = int(args.get("mode", _NO_CHANGE) or _NO_CHANGE)
    brightness = int(args.get("brightness", _NO_CHANGE) or _NO_CHANGE)
    cmd = {}
    if mode != _NO_CHANGE:
        cmd["mode"] = mode & 0xFF
    if brightness != _NO_CHANGE:
        cmd["brightness"] = max(0, min(brightness, 36))
    if cmd:
        bus.shared["_display_cmd"] = cmd
    print("[WTT] ctl mode={} bri={}".format(
        "skip" if mode == _NO_CHANGE else mode,
        "skip" if brightness == _NO_CHANGE else brightness))


def register(app):
    app.disp.on(0x1501, on_ctl)
    print("[Action] waiting_to_trash actions registered")
