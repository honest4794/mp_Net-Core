"""WebMaster 服務入口 (FastAPI + WebSocket)。

端點:
  GET  /                    → 靜態 SPA (static/index.html)
  WS   /ws/{slave_id}       → slave 連入 (binary NC 幀)
  WS   /ws/ui               → 瀏覽器連入 (JSON 控制 + 訂閱設備狀態)
  GET  /api/devices         → 設備清單
  GET  /api/mp3             → MP3 清單
  GET  /media/{name}        → MP3 檔案 (供 <audio> 播放)
  POST /api/upload/{slave_id} → 上傳檔案到指定設備 (multipart)

啟動: uvicorn server:app --host 0.0.0.0 --port 8000
"""
import asyncio
import json
import logging
import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from protocol import protocol
from device_manager import manager, Device
import transfer, stream, audio

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("webmaster")

app = FastAPI(title="NetBus WebMaster")

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ═══════════════════════ 靜態 / 頁面 ═══════════════════════
@app.get("/", response_class=HTMLResponse)
async def index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h1>WebMaster</h1><p>static/index.html 缺失</p>")


# ═══════════════════════ REST API ═══════════════════════
@app.get("/api/devices")
async def api_devices():
    return JSONResponse({"ok": True, "data": manager.list_devices()})


@app.get("/api/mp3")
async def api_mp3():
    return JSONResponse({"ok": True, "data": audio.list_mp3()})


@app.get("/media/{name}")
async def media_mp3(name: str):
    path = audio.resolve_mp3(name)
    if path is None:
        return JSONResponse({"ok": False, "err": "not found"}, status_code=404)
    return FileResponse(path, media_type="audio/mpeg")


@app.post("/api/upload/{slave_id}")
async def api_upload(slave_id: str, request: Request):
    """上傳 raw 檔案 body 到指定設備 (remote_path/chunk_size 用 query 參數)。

    用 raw body 而非 multipart, 避免額外依賴 python-multipart。
    """
    dev = manager.get(slave_id)
    if dev is None:
        return JSONResponse({"ok": False, "err": "slave 離線"}, status_code=404)
    remote_path = request.query_params.get("remote_path", "/sd/upload.bin")
    try:
        chunk_size = int(request.query_params.get("chunk_size", 4096))
    except ValueError:
        chunk_size = 4096
    data = await request.body()
    try:
        sha = await transfer.upload(dev, data, remote_path, chunk_size=chunk_size)
        return JSONResponse({"ok": True, "size": len(data), "sha": sha.hex()})
    except Exception as e:
        return JSONResponse({"ok": False, "err": str(e)}, status_code=500)


# ═══════════════════════ WebSocket: slave ═══════════════════════
@app.websocket("/ws/{slave_id}")
async def ws_slave(websocket: WebSocket, slave_id: str):
    await websocket.accept()
    dev = manager.register(slave_id, websocket, addr=websocket.client.host if websocket.client else None)
    await manager.broadcast_ui({"type": "device_list", "data": manager.list_devices()})
    try:
        while True:
            data = await websocket.receive_bytes()
            await dev.feed_bytes(data)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        log.warning("slave %s 連線異常: %s", slave_id, e)
    finally:
        manager.unregister(slave_id)
        await manager.broadcast_ui({"type": "device_list", "data": manager.list_devices()})


# ═══════════════════════ WebSocket: UI ═══════════════════════
@app.websocket("/ws/ui")
async def ws_ui(websocket: WebSocket):
    await websocket.accept()
    manager.ui_clients.add(websocket)
    try:
        await websocket.send_text(json.dumps({"type": "device_list", "data": manager.list_devices()}, ensure_ascii=False))
        while True:
            raw = await websocket.receive_text()
            await handle_ui_message(websocket, raw)
    except WebSocketDisconnect:
        pass
    finally:
        manager.ui_clients.discard(websocket)


async def handle_ui_message(ws: WebSocket, raw: str):
    """處理瀏覽器送來的 JSON 控制指令。"""
    try:
        msg = json.loads(raw)
    except Exception:
        await ws.send_text(json.dumps({"type": "error", "err": "invalid json"}))
        return

    action = msg.get("action")
    slave_id = msg.get("slave_id")
    dev = manager.get(slave_id) if slave_id else None

    if action == "ping":
        await ws.send_text(json.dumps({"type": "pong"}))

    elif action == "device_list":
        await ws.send_text(json.dumps({"type": "device_list", "data": manager.list_devices()}, ensure_ascii=False))

    elif action == "stream_prepare" and dev:
        await stream.prepare(dev, msg.get("file_name", "data.bin"),
                             int(msg.get("block_id", 0)), int(msg.get("play_mode", 0)))
        await ws.send_text(json.dumps({"type": "ok", "action": action}))

    elif action == "stream_play" and dev:
        await stream.play(dev, int(msg.get("start_frame", 0)))
        await ws.send_text(json.dumps({"type": "ok", "action": action}))

    elif action == "stream_pause" and dev:
        await stream.pause(dev, bool(msg.get("paused", True)))
        await ws.send_text(json.dumps({"type": "ok", "action": action}))

    elif action == "stream_stop" and dev:
        await stream.stop(dev)
        await ws.send_text(json.dumps({"type": "ok", "action": action}))

    elif action == "stream_seek" and dev:
        await stream.seek(dev, int(msg.get("frame", 0)))
        await ws.send_text(json.dumps({"type": "ok", "action": action}))

    elif action == "stream_fps" and dev:
        await stream.set_fps(dev, int(msg.get("fps", 40)))
        await ws.send_text(json.dumps({"type": "ok", "action": action}))

    elif action == "ram_upload" and dev:
        # 上傳資料到 RAM 緩衝區 (實時播放)
        import base64
        b64 = msg.get("data_b64", "")
        remote = msg.get("remote_path", "/ram/live.bin")
        try:
            data = base64.b64decode(b64)
            sha = await transfer.upload(dev, data, remote, chunk_size=int(msg.get("chunk_size", 4096)))
            await ws.send_text(json.dumps({"type": "ok", "action": action, "sha": sha.hex(), "size": len(data)}))
        except Exception as e:
            await ws.send_text(json.dumps({"type": "error", "err": str(e)}))

    else:
        await ws.send_text(json.dumps({"type": "error", "err": f"unknown action: {action}"}))


# ═══════════════════════ 啟動 (背景心跳) ═══════════════════════
@app.on_event("startup")
async def startup():
    asyncio.create_task(manager.heartbeat_loop())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
