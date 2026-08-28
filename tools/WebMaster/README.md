# WebMaster — 網頁操作介面

操控 mp_Net-Core 設備（NC4 協議）的輕量 Web 控制台。MP3 用瀏覽器原生 `<audio>` 播放，後端零音訊依賴。

## 啟動

```bash
cd tools/WebMaster
python3 -B run.py          # 預設 0.0.0.0:8000
python3 -B run.py 9000     # 自訂 port
```

瀏覽器開 `http://<本機IP>:8000/`。

## 設備連線

slave 韌體會連到 master 的 `ws://<ip>:<port>/ws/<slave_id>`。所以 WebMaster 的 WS port（預設 8000）要與 slave config 的 `master_port` 一致，slave 開機或敲門時會自動連入。

## 端點

| 方法 | 路徑 | 說明 |
|---|---|---|
| GET | `/` | 操作台 SPA |
| WS | `/ws/{slave_id}` | slave 連入（binary NC 幀） |
| WS | `/ws/ui` | 瀏覽器控制台（JSON） |
| GET | `/api/devices` | 在線設備清單 |
| GET | `/api/mp3` | MP3 清單 |
| GET | `/media/{name}` | MP3 檔案 |
| POST | `/api/upload/{slave_id}?remote_path=...&chunk_size=...` | raw body 上傳檔案 |

## UI → WS 指令（JSON）

```json
{"action": "stream_prepare", "slave_id": "S1", "file_name": "/ram/live.bin", "play_mode": 0}
{"action": "stream_play",   "slave_id": "S1", "start_frame": 0}
{"action": "stream_pause",  "slave_id": "S1", "paused": true}
{"action": "stream_stop",   "slave_id": "S1"}
{"action": "stream_seek",   "slave_id": "S1", "frame": 0}
{"action": "stream_fps",    "slave_id": "S1", "fps": 40}
{"action": "ram_upload",    "slave_id": "S1", "remote_path": "/ram/live.bin", "data_b64": "..."}
```

## 測試

```bash
# in-memory 整合測試 (不需硬體 / 不需網路)
python3 -B test_webmaster.py

# 端到端 mock slave (需 pip install websockets)
python3 -B run.py 8000 &
python3 -B mock_slave.py ws://127.0.0.1:8000/ws/MOCK MOCK
```

## 模組

- `protocol.py` — NC4 打包/解包（復用 slave/lib/sys）
- `device_manager.py` — slave 連線 + 回應匹配 + 狀態快取 + 心跳
- `transfer.py` — 上傳/下載/promote/confirm/delta（ACK 停等）
- `stream.py` — 串流控制（含 RAM 緩衝區實時播放）
- `audio.py` — MP3 清單（播放由瀏覽器 `<audio>` 負責）
- `server.py` — FastAPI 入口
- `static/` — SPA 前端
