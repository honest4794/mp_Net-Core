# action/status_actions.py
import json
import gc
import os
import time
import machine, ubinascii
from lib.sys.sys_bus import bus
from lib.sys.proto import Proto
from lib.sys.schema_codec import SchemaCodec

# 引用其他模組的狀態
from action import stream_actions

def get_runtime_info():
    """抓取整合性的實時運行數據"""
    # 獲取文件系統空間
    fs_stat = os.statvfs('/')
    fs_free = (fs_stat[0] * fs_stat[3]) // 1024
    uid = bus.slave_id
    
    return {
        "id": uid,
        "mem_free": gc.mem_free(),
        "uptime_ms": time.ticks_ms(),
        "fs_free_kb": fs_free,
        # 🚀 整合 Stream 模組的實時數據
        "fps": stream_actions._STREAM_STATE["fps"],
        "frame_count": stream_actions.get_frame_count(),
        "stream_mode": stream_actions.get_mode(),
        "is_streaming": stream_actions.is_streaming()
    }

def on_status_get(ctx, args):
    """處理 0x1101：動態抓取 hub 註冊的所有 Provider 數據"""
    app = ctx["app"]
    
    # 從總線獲取所有 Action 自動註冊的數值 (fps, mem, count等)
    metrics = bus.get_metrics()
    
    # 額外補充即時內存訊息
    metrics["mem_free"] = gc.mem_free()
    
    try:
        status_json = json.dumps(metrics)
        cmd_def = app.store.get(0x1102)
        payload = SchemaCodec.encode(cmd_def, {"status_json": status_json})
        if "send" in ctx:
            ctx["send"](Proto.pack(0x1102, payload))
    except Exception as e:
        print(f"❌ [Status] Error: {e}")

def register(app):
    """註冊狀態與健康查詢指令"""
    app.disp.on(0x1101, on_status_get)

    # 多介面 IP 清單 provider (STATUS_GET 0x1101 的 metrics 帶 ips)
    def _ips_provider():
        nm = bus.get_service("network_manager")
        if nm is None:
            return {}
        try:
            return nm.get_ips()
        except Exception:
            return {}

    bus.register_provider("ips", _ips_provider)

    # 🔧 目前渲染幀率 provider (主動同步/Profile 用; PC 端 0x1101 可取回)
    def _local_fps_provider():
        try:
            return bus.shared.get("System", {}).get("local_fps", 0)
        except Exception:
            return 0

    bus.register_provider("local_fps", _local_fps_provider)
    print("✅ [Action] Status & Health actions integrated")