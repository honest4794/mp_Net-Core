# action/ui_actions.py — UI 控制平面 handler
#
# 對應 schema/ui.json(0x40xx):
#   0x4001 UI_DESCRIBE  查詢 UI 空間映射(_ui_decl,回傳各 page 的 widget 清單 + bus 位置)
#   0x4002 UI_RSP       回應(str_u16len 包 JSON,沿用 STATUS_GET→STATUS_RSP 慣例)
#   0x4003 UI_SET       外部寫期望值進 ctrl 陣列(直寫 buffer,跨核安全、零延遲)
#   0x4004 UI_GET       讀單一 widget 的實際值(讀 state 陣列)
#
# handler 一律透過 bus.get_service("ui")(= ui_space 模組)存取,不碰 LVGL widget。
# LVGL 是唯一摸 widget 的人,本 handler 只讀寫打包 bytearray / _ui_var → thread-safe。

import json
from lib.sys_bus import bus
from lib.proto import Proto
from lib.schema_codec import SchemaCodec

CMD_UI_DESCRIBE = 0x4001
CMD_UI_RSP = 0x4002
CMD_UI_SET = 0x4003
CMD_UI_GET = 0x4004


def _ui():
    """取得 ui_space service(由 board.run() 註冊)。"""
    return bus.get_service("ui")


def on_ui_describe(ctx, args):
    """0x4001:回傳 UI 空間映射(JSON via UI_RSP)。page_id 空=全部頁。"""
    app = ctx["app"]
    page_id = args.get("page_id", "") or ""
    ui = _ui()
    if ui is None:
        _send_json(ctx, app, {"status": "error", "error": "ui service not registered"})
        return
    try:
        result = ui.describe(page_id if page_id else None)
        _send_json(ctx, app, result)
    except Exception as e:
        _send_json(ctx, app, {"status": "error", "error": str(e)})


def on_ui_get(ctx, args):
    """0x4004:讀單一 widget 實際值。"""
    app = ctx["app"]
    page_id = args.get("page_id", "") or ""
    widget_id = args.get("widget_id", "") or ""
    ui = _ui()
    if ui is None:
        _send_json(ctx, app, {"status": "error", "error": "ui service not registered"})
        return
    try:
        val = ui.get_value(page_id, widget_id)
        _send_json(ctx, app, {"page": page_id, "widget": widget_id, "value": val})
    except Exception as e:
        _send_json(ctx, app, {"status": "error", "error": str(e)})


def on_ui_set(ctx, args):
    """0x4003:外部寫期望值進 ctrl 陣列。value_json 包實際值(JSON 編碼)。
    直寫 buffer,繞過 LVGL;LVGL 下幀 sync 時套用。"""
    app = ctx["app"]
    page_id = args.get("page_id", "") or ""
    widget_id = args.get("widget_id", "") or ""
    value_json = args.get("value_json", "") or ""
    ui = _ui()
    if ui is None:
        _send_json(ctx, app, {"status": "error", "error": "ui service not registered"})
        return
    try:
        value = json.loads(value_json) if value_json else None
    except Exception:
        value = value_json
    try:
        ok = ui.set_value(page_id, widget_id, value)
        _send_json(ctx, app, {"status": "ok" if ok else "error",
                              "page": page_id, "widget": widget_id})
    except Exception as e:
        _send_json(ctx, app, {"status": "error", "error": str(e)})


def _send_json(ctx, app, obj):
    """把 dict 編成 UI_RSP(0x4002)封包送回。沿用 status_actions.on_status_get 模板。"""
    try:
        ui_json = json.dumps(obj)
        cmd_def = app.store.get(CMD_UI_RSP)
        payload = SchemaCodec.encode(cmd_def, {"ui_json": ui_json})
        if "send" in ctx:
            ctx["send"](Proto.pack(CMD_UI_RSP, payload))
    except Exception as e:
        print("[ui_actions] send fail:", e)


def register(app):
    """註冊 UI 控制命令。"""
    app.disp.on(CMD_UI_DESCRIBE, on_ui_describe)
    app.disp.on(CMD_UI_SET, on_ui_set)
    app.disp.on(CMD_UI_GET, on_ui_get)
    print("[Action] UI control actions integrated (0x4001-0x4004)")
