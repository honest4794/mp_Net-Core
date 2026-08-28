# action/pixel_actions.py
# 本地燈效 (Local Mode) 遠端控制 + 配對支援
#
# 指令 (pixel 群 0x31xx, 對應 slave/schema/pixel.json):
#   請求 (Master→Slave, 本模組註冊 handler):
#     0x3101 MODE_LIST_QUERY    — 查詢本地燈效模式 id 清單
#     0x3103 MODE_GET           — 查詢目前本地模式狀態
#     0x3105 MODE_SET           — 播放指定本地模式 (一個一個播, 供配對識別)
#     0x3106 MODE_STOP          — 停止本地模式 (熄燈)
#     0x3107 MODE_DETAIL_QUERY  — 查詢單一模式名稱等細節
#   回應 (Slave→Master, 只送出):
#     0x3102 MODE_LIST_RSP / 0x3104 MODE_GET_RSP / 0x3108 MODE_DETAIL_RSP
#
# 播放端 = PixelTask (Core1, pixel_task.py): 本模組只把指令寫進 bus.shared
# ("pixel_remote_set"/"pixel_remote_stop"), PixelTask._consume_cmds 消費後
# 以本地 registry/show 機制播放該單一模式, 不需 PC 串流 data.bin。

import time
from lib.sys.proto import Proto
from lib.sys.schema_codec import SchemaCodec
from lib.sys.sys_bus import bus


def _send(ctx, rsp_cmd, fields):
    app = ctx["app"]
    try:
        cmd_def = app.store.get(rsp_cmd)
        payload = SchemaCodec.encode(cmd_def, fields)
        if "send" in ctx:
            ctx["send"](Proto.pack(rsp_cmd, payload, addr=bus.cid))
    except Exception as e:
        print("[Pixel] reply {} failed: {}".format(hex(rsp_cmd), e))


def on_mode_list_query(ctx, args):
    """0x3101: 回報本地燈效 id 清單 (entries = 依 id 排序的 u8 串)。"""
    mode_type = args.get("mode_type", 0)
    modes = bus.shared.get("pixel_maps", {})
    ids = sorted(modes.keys())
    entries = bytes(ids) if ids else b""
    _send(ctx, 0x3102, {
        "mode_type": mode_type,
        "count": len(ids),
        "entries": entries,
    })
    print("[Pixel] MODE_LIST type={} count={}".format(mode_type, len(ids)))


def _ticks_ms():
    try:
        return time.ticks_ms()
    except AttributeError:
        return int(time.monotonic() * 1000)


def _ticks_diff(now, then):
    try:
        return time.ticks_diff(now, then)
    except AttributeError:
        return now - then


def on_mode_get(ctx, args):
    """0x3103: 回報目前模式，供 Hi-Nu Master 探測及收斂確認。"""
    status = bus.shared.get("pixel_nc4_status") or {}
    running = 1 if status.get("running") else 0
    elapsed_ms = int(status.get("elapsed_ms", 0) or 0)
    if running:
        elapsed_ms = max(0, _ticks_diff(_ticks_ms(), status.get("started_at", _ticks_ms())))
    _send(ctx, 0x3104, {
        "mode_type": int(status.get("mode_type", 0) or 0),
        "mode_id": int(status.get("mode_id", 0) or 0),
        "elapsed_ms": elapsed_ms,
        "total_ms": 0,
        "running": running,
    })


def on_mode_set(ctx, args):
    """0x3105: 播放指定本地模式 (配對用, 一個一個播)。

    先強制退出串流 (stream_active=False / is_streaming=False), 避免 data.bin
    供給鏈 (NetworkTask.handle_supply_chain) 與本地燈效搶 pixel_stream hub。
    """
    mode_type = args.get("mode_type", 0)
    mode_id = args.get("mode_id", 0)
    start_delay_ms = args.get("start_delay_ms", 0) or 0
    brightness = args.get("brightness", 255)
    if start_delay_ms > 0:
        time.sleep_ms(min(start_delay_ms, 10000))
    # 停用串流供給鏈 (stream_active) 與渲染旗標, 避免與本地 show 衝突
    bus.shared.update({
        "stream_active": False,
        "is_streaming": False,
        "is_paused": False,
        "is_ready": False,
    })
    bus.shared["pixel_remote_set"] = mode_id
    bus.shared["pixel_nc4_status"] = {
        "mode_type": int(mode_type),
        "mode_id": int(mode_id),
        "started_at": _ticks_ms(),
        "elapsed_ms": 0,
        "running": 1,
    }
    print("[Pixel] MODE_SET type={} id={} bri={}".format(mode_type, mode_id, brightness))


def on_mode_stop(ctx, args):
    """0x3106: 停止本地模式 (熄燈)。"""
    bus.shared.update({
        "stream_active": False,
        "is_streaming": False,
        "is_paused": False,
        "is_ready": False,
    })
    bus.shared["pixel_remote_stop"] = 1
    status = bus.shared.get("pixel_nc4_status") or {}
    if status.get("running"):
        status["elapsed_ms"] = max(
            0, _ticks_diff(_ticks_ms(), status.get("started_at", _ticks_ms()))
        )
    status["running"] = 0
    bus.shared["pixel_nc4_status"] = status
    print("[Pixel] MODE_STOP")


def on_mode_detail_query(ctx, args):
    """0x3107: 回報單一模式細節 (名稱; total_ms 目前無資料=0)。"""
    mode_type = args.get("mode_type", 0)
    mode_id = args.get("mode_id", 0)
    modes = bus.shared.get("pixel_maps", {})
    m = modes.get(mode_id)
    name = m.get("name", "") if m else ""
    _send(ctx, 0x3108, {
        "mode_type": mode_type,
        "mode_id": mode_id,
        "total_ms": 0,
        "name": name,
    })


def register(app):
    app.disp.on(0x3101, on_mode_list_query)
    app.disp.on(0x3103, on_mode_get)
    app.disp.on(0x3105, on_mode_set)
    app.disp.on(0x3106, on_mode_stop)
    app.disp.on(0x3107, on_mode_detail_query)
    print("[Pixel] Local-mode actions registered")
