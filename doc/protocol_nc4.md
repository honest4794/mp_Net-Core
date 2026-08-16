# NC4 二進位封包協議(mp_Net-Core slave)

> **用途**：`slave/` 與 Server / PC 工具之間的二進位封包協議完整說明,包含封包格式、CRC、schema 驅動 payload、傳輸層與完整指令集。
> **對象**：任何要新增指令、解析封包、寫 PC/Server 端對接工具的人。
> **最後更新**：2026-08-16
> **實作來源**：`slave/lib/proto.py`(唯一真相,以此文件描述為準)

---

## 1) 協議版本:NC4

```
協議代號    : NC4
SOF 標記    : b"NC" (0x4E43)
CUR_VER     : 4
Header 長度 : HDR_LEN = 9 bytes
CRC 演算法  : CRC32 (binascii.crc32)
CRC 長度    : CRC_LEN = 4 bytes
```

> ⚠️ **與舊文件差異**:`mp_Net-Light/doc/AI_CONTEXT.md` 描述的 VER=3 + CRC16-CCITT-FALSE(2B)是**舊版**。目前 `slave/lib/proto.py` 已升級為 **VER=4 + CRC32(4B)**,header 也由 10B(含 CRC16 位置)改為 **9B(HDR_LEN)+ payload + 4B CRC32**。任何新對接一律以本文件為準。

---

## 2) 封包格式

```
┌───────┬───────┬────────┬────────┬────────┬────────────┬──────────┐
│  SOF  │  VER  │  ADDR  │  CMD   │  LEN   │    DATA    │   CRC32  │
│ (2B)  │ (1B)  │  (2B)  │  (2B)  │  (2B)  │  (LEN B)   │   (4B)   │
└───────┴───────┴────────┴────────┴────────┴────────────┴──────────┘
  0-1    2       3-4      5-6      7-8      9..9+LEN-1   9+LEN..9+LEN+3
```

### 欄位說明

| 欄位 | 長度 | offset | 說明 |
|------|------|--------|------|
| SOF | 2B | 0 | 固定 `b"NC"` |
| VER | 1B | 2 | 協議版本,固定 `4`(`CUR_VER`) |
| ADDR | 2B | 3 | 目的地址(uint16 LE;`ADDR_BROADCAST = 0xFFFF` 為廣播) |
| CMD | 2B | 5 | 指令碼(uint16 LE),由 `/schema/*.json` 定義 |
| LEN | 2B | 7 | DATA 長度(uint16 LE) |
| DATA | 變長 | 9 | Payload,格式由 schema 定義 |
| CRC32 | 4B | 9+LEN | CRC32 檢查碼(uint32 LE) |

### CRC32 計算範圍

```
crc = binascii.crc32(data, 0)
data = VER + ADDR + CMD + LEN + DATA     ← 即 buffer[2 : 9+LEN]
(不含 SOF,不含 CRC32 自身)
```

實作(`proto.py`):

```python
crc_val = Proto.crc32_update(b[2:HDR_LEN + ln], 0) & 0xFFFFFFFF
struct.pack_into("<I", b, HDR_LEN + ln, crc_val)
```

### 組包範例

```python
from lib.proto import Proto

pkt = Proto.pack(0x1002, payload_bytes, addr=0xFFFF)
# ⚠️ 回傳值是「指向共享 buffer 的 memoryview」,必須立即消費(送出/寫入),
#    下一次 pack() 會覆蓋它。
```

---

## 3) 流式解析(黏包/拆包)

`StreamParser` 處理 TCP/WS 的黏包與拆包:

```python
parser = StreamParser(max_len=base_size * 2)   # app.py 預設 max_len = Buffer.size * 2

parser.feed(data)                    # 收進內部緩衝(viper 加速 append/compact)
for ver, addr, cmd, payload in parser.pop():   # 生成器,撈出所有完整封包
    app.disp.dispatch(cmd, payload, ctx)
```

解析策略:

1. **找 SOF**:`buf.find(b"NC", start, end)`,錯位時自動掃描下一個標記(SOF 重同步)。
2. **驗證**:`ver != CUR_VER` 或 `ln > max_len` → 前移 1 byte 繼續找 SOF。
3. **湊齊整幀**:`(end - start) < 9 + ln + 4` → 等更多資料。
4. **驗 CRC32**:通過才 `yield`,失敗 → 前移 1 byte(視為錯位資料)。
5. **max_len 保護**:避免誤同步讀到超大 LEN 造成記憶體溢出。

`max_len` 由 `app.create_parser()` 設定,基礎為 `config.json` 的 `Buffer.size`(預設 16384)的 2 倍。

---

## 4) Schema 驅動 Payload

### 4.1 支援的 payload 類型

`schema_loader._TYPE_CODE` 定義的 6 種類型(全部 little-endian):

| type | type code | 大小 | 說明 |
|------|-----------|------|------|
| `u8` | 0 | 1B | 無號整數 |
| `u16` | 1 | 2B | 無號整數 LE |
| `u32` | 2 | 4B | 無號整數 LE |
| `str_u16len` | 3 | 2B 長度 + 內容 | 前綴 2B LE 長度,內容為 UTF-8 字串 |
| `bytes_fixed` | 4 | 固定 `"len": N` | 長度取自 schema JSON 的 `len` 欄位(如 sha256 = 32) |
| `bytes_rest` | 5 | 剩餘全部 | 吃掉 payload 剩餘所有 bytes,**必須放最後** |

> `SchemaCodec.encode` 也支援 `i16` / `i32` 有號整數,但 `schema_loader` 沒有對應 type code(會落成 255),decode 無法還原,目前所有 schema JSON 都只用上面 6 種。

### 4.2 Schema JSON 格式

```json
{
  "group": "sys",
  "cmds": [
    {
      "cmd": "0x1002",
      "name": "SLAVE_ANNOUNCE",
      "payload": [
        {"name": "slave_id",   "type": "str_u16len"},
        {"name": "pixel_count","type": "u16"},
        {"name": "hw_version", "type": "str_u16len"}
      ]
    }
  ]
}
```

- `cmd` 支援 `"0x1001"`(hex 字串)或十進位字串。
- `SchemaStore.load_dir("/schema")` 依檔名排序載入所有 JSON;`finalize()` 依 cmd id 排序建 `dispatch_buf`(每筆 8B)+ `field_buf`(每欄 2B)+ `field_names`,供 viper 加速解碼。
- 重複 cmd id 時,後載入者覆寫。

### 4.3 編解碼 API

```python
from lib.schema_loader import SchemaStore
from lib.schema_codec import SchemaCodec

store = SchemaStore(); store.load_dir("/schema"); store.finalize()

cmd_def = store.get(0x1002)                    # 依 cmd int 取得定義(沒有 get_cmd!)
payload = SchemaCodec.encode(cmd_def, {"slave_id": "ESP32_A1B2", ...})
args    = SchemaCodec.decode(cmd_def, payload, store)   # 回傳 dict,恆含 _name / _cmd
```

decode 邊界行為(對接工具需注意):

- 欄位不足(如 u32 需要 4B 但只剩 2B)→ 該欄位不寫入 dict,不 raise。
- `bytes_rest` 即使長度 0 也會寫入(回傳空 memoryview)。
- 未定義的 type code 在 decode 無分支 → 該欄位不寫入、offset 不推進,可能造成後續錯位。

---

## 5) 傳輸層

同一套 NC4 封包可跑在 5 種傳輸上,接收端統一寫進各 bus 的 `AtomicStreamHub`(見 `doc/multi_level_buffer.md` L2):

| bus | 檔案 | 傳輸 | 用途 |
|-----|------|------|------|
| `CTRL-WS` | `lib/net_bus.py` (TYPE_WS) | WebSocket | 主控制通道(指令 + 回覆 + 串流) |
| `UDP-DISCV` | `lib/net_bus.py` (TYPE_UDP) | UDP | 發現/廣播(`discovery_port` = 9000) |
| TCP | `lib/net_bus.py` (TYPE_TCP) | TCP | 備用/直連 |
| `CIRCUIT` | `lib/circuit_bus.py` | UART 實體線 | 有線控制(`CircuitDecode` 設定) |
| `NOW-Bus` | `lib/now_bus.py` | ESP-NOW | 無 WiFi 的短距離控制 |

每個 bus 的 rx_hub slot 佈局(收進 ring 後,`BusDecodeTask` 讀取時剝離):

```
[0:2] = u16 LE 資料長度 n | [2:2+n] = NC4 封包資料
```

---

## 6) 完整指令集

指令碼分配(依 `slave/schema/` 實際內容):

```
0x10xx — sys         系統發現/控制/任務管理
0x11xx — status      狀態查詢/配置更新
0x12xx — heartbeat   心跳
0x13xx — now         ESP-NOW
0x14xx — hw          硬體控制
0x15xx — waiting_to_trash  待清理功能
0x18xx — ram_bench   記憶體效能測試
0x20xx — file        檔案傳輸/查詢
0x30xx — stream      pixel 串流
0x31xx — jpeg        JPEG 播放器
0x32xx — mp4         MP4 播放器
```

### 6.1 sys.json(0x10xx)

| CMD | 名稱 | 方向 | Payload | 說明 |
|-----|------|------|---------|------|
| 0x1001 | DISCOVER | Server → MCU | `server_ip(str)` `ws_url(str)` | UDP 廣播發現從機 |
| 0x1002 | SLAVE_ANNOUNCE | MCU → Server | `slave_id(str)` `pixel_count(u16)` `hw_version(str)` | 從機回報身份 |
| 0x1004 | SYS_CTRL | Server → MCU | `wifi_enable(u8)` `core_control(u8)` | 系統控制 |
| 0x1008 | WIFI_CTRL | Server → MCU | `wifi_enable(u8)` | WiFi 開關 |
| 0x1009 | WEB_CTRL | Server → MCU | `web_enable(u8)` | Web UI 開關 |
| 0x1005 | SYS_TASK_QUERY | Server → MCU | (空) | 查詢任務清單 |
| 0x1006 | SYS_TASK_RSP | MCU → Server | `tasks_json(str)` | 回報任務清單 |
| 0x1007 | SYS_TASK_SET | Server → MCU | `task_name(str)` `affinity_c0(u8)` `affinity_c1(u8)` | 設定任務核心親和性 |

### 6.2 status.json(0x11xx)

| CMD | 名稱 | 方向 | Payload | 說明 |
|-----|------|------|---------|------|
| 0x1101 | STATUS_GET | Server → MCU | `query_type(u8)` | 請求狀態(0=全部, 1=精簡) |
| 0x1102 | STATUS_RSP | MCU → Server | `status_json(str)` | 回傳 JSON 狀態 |
| 0x1103 | STATUS_UPDATE | Server → MCU | `config_json(str)` | 更新配置 |
| 0x1104 | STATUS_UPDATE_ACK | MCU → Server | `success(u8)` `message(str)` | 更新結果 |

### 6.3 heartbeat.json(0x12xx)

| CMD | 名稱 | 方向 | Payload | 說明 |
|-----|------|------|---------|------|
| 0x1201 | HEARTBEAT | MCU → Server | `slave_id(str)` `uptime_ms(u32)` `mem_free(u32)` `ws_connected(u8)` | 從機主動心跳 |
| 0x1202 | HEARTBEAT_ACK | Server → MCU | `server_time(u32)` `success(u8)` | Server 確認存活 |

### 6.4 now.json(0x13xx,ESP-NOW)

| CMD | 名稱 | 方向 | Payload | 說明 |
|-----|------|------|---------|------|
| 0x1301 | NOW_INIT | Server → MCU | (空) | 初始化 ESP-NOW |
| 0x1302 | NOW_SEND_HB | Server → MCU | `target_mac(str)` `count(u8)` | 送心跳測試 |
| 0x1303 | NOW_STATS | Server → MCU | (空) | 查詢 ESP-NOW 統計 |

### 6.5 hw.json(0x14xx)

| CMD | 名稱 | 方向 | Payload | 說明 |
|-----|------|------|---------|------|
| 0x1401 | HW_CTL | Server → MCU | `type(u8)` `id(u8)` `label(str)` `value(u16)` | 硬體控制 |
| 0x1402 | HW_QUERY | Server → MCU | `type(u8)` `id(u8)` | 硬體查詢 |

### 6.6 waiting_to_trash.json(0x15xx)

| CMD | 名稱 | 方向 | Payload | 說明 |
|-----|------|------|---------|------|
| 0x1501 | WTT_CTL | Server → MCU | `mode(u8)` `brightness(u8)` | 待清理功能控制 |
| 0x1502 | WTT_STATUS | MCU → Server | `mode(u8)` `brightness(u8)` `time(u8)` | 狀態回報 |

### 6.7 ram_bench.json(0x18xx)

| CMD | 名稱 | 方向 | Payload | 說明 |
|-----|------|------|---------|------|
| 0x1811 | RAM_BENCH_START | Server → MCU | `run_id(u16)` `total_size(u32)` `chunk_size(u16)` `mode(u8)` `ring_kb(u16)` | 開始測試 |
| 0x1812 | RAM_BENCH_CHUNK | Server → MCU | `run_id(u16)` `seq(u32)` `data(bytes_rest)` | 測試資料塊 |
| 0x1813 | RAM_BENCH_STOP | Server → MCU | `run_id(u16)` | 停止測試 |
| 0x1814 | RAM_BENCH_REPORT | MCU → Server | `run_id(u16)` `bytes(u32)` `chunks(u32)` `elapsed_ms(u32)` `mb_s_x1000(u32)` | 測試結果 |

### 6.8 file.json(0x20xx)

| CMD | 名稱 | 方向 | Payload | 說明 |
|-----|------|------|---------|------|
| 0x2001 | FILE_BEGIN | 雙向 | `file_id(u16)` `total_size(u32)` `chunk_size(u16)` `sha256(bytes_fixed 32)` `path(str)` | 開始傳輸 |
| 0x2002 | FILE_CHUNK | 雙向 | `file_id(u16)` `offset(u32)` `data(bytes_rest)` | 傳輸塊 |
| 0x2003 | FILE_END | 雙向 | `file_id(u16)` | 傳輸完成 |
| 0x2004 | FILE_ACK | 雙向 | `file_id(u16)` `offset(u32)` | 確認(斷點續傳) |
| 0x2005 | FILE_QUERY | Server → MCU | `path(str)` | 查詢檔案 |
| 0x2006 | FILE_QUERY_RSP | MCU → Server | `exists(u8)` `sha256(bytes_fixed 32)` `size(u32)` `path(str)` | 檔案資訊 |
| 0x2007 | FILE_READ | Server → MCU | `path(str)` `offset(u32)` `length(u16)` | 讀取檔案片段 |
| 0x2009 | FILE_DELETE | Server → MCU | `path(str)` | 刪除檔案 |
| 0x200B | FILE_SCAN | Server → MCU | (空) | 掃描檔案系統 |

### 6.9 stream.json(0x30xx)

| CMD | 名稱 | 方向 | Payload | 說明 |
|-----|------|------|---------|------|
| 0x3001 | STREAM_INFO | MCU → Server | `total_blocks(u32)` `frames_per_block(u32)` `fps(u8)` | 串流資訊 |
| 0x3002 | STREAM_STOP | Server → MCU | (空) | 停止串流 |
| 0x3003 | STREAM_FRAME | Server → MCU | `pixel_data(bytes_rest)` | Direct Mode 直接推幀(注意:schema JSON 未定義,由 action 直接註冊) |
| 0x3004 | STREAM_SEEK | Server → MCU | `target_block(u32)` `target_frame(u32)` | 跳轉 |
| 0x3005 | STREAM_PAUSE | Server → MCU | `pause(u8)` | 暫停/恢復 |
| 0x3008 | STREAM_READY_ACK | MCU → Server | `block_id(u32)` | 準備完成 |
| 0x3009 | STREAM_STATE_SET | Server → MCU | `file_name(str)` `block_id(u32)` `play_mode(u8)` | 設定播放檔案與區塊 |
| 0x300A | STREAM_PLAY | Server → MCU | `start_frame(u32)` | 開始播放 |

### 6.10 jpeg.json(0x31xx)

| CMD | 名稱 | 方向 | Payload | 說明 |
|-----|------|------|---------|------|
| 0x3101 | JPEG_PLAYER_CTL | Server → MCU | `action(u8)` `seek_frame(u32)` | 播放器控制 |
| 0x3103 | JPEG_PLAYER_PARAMS | Server → MCU | `pace_ms(u16)` `loop(u8)` | 播放參數 |
| 0x3105 | JPEG_STATUS_GET | Server → MCU | (空) | 查詢狀態 |
| 0x3106 | JPEG_STATUS_RSP | MCU → Server | `playing(u8)` `frame(u32)` `total(u32)` `fps(u16)` `err(str)` | 狀態回報 |
| 0x3107 | JPEG_SOURCE_SET | Server → MCU | `source(str)` | 設定來源(資料夾/jpk/bin) |

### 6.11 mp4.json(0x32xx)

| CMD | 名稱 | 方向 | Payload | 說明 |
|-----|------|------|---------|------|
| 0x3201 | MP4_PLAYER_CTL | Server → MCU | `action(u8)` `value(u32)` | 播放器控制 |
| 0x3202 | MP4_SOURCE_SET | Server → MCU | `source(str)` `mode(u8)` `start(u32)` `range(u32)` | 設定來源 |
| 0x3203 | MP4_STATUS_GET | Server → MCU | (空) | 查詢狀態 |
| 0x3204 | MP4_STATUS_RSP | MCU → Server | `playing(u8)` `paused(u8)` `mode(u8)` `frame(u32)` `total(u32)` `source(str)` `err(str)` | 狀態回報 |

---

## 7) 新增指令流程

新增一個指令需要修改 **4 個位置**(詳細見 `Skills/mp-netcore`):

1. **`/schema/<group>.json`**:在 `cmds` 陣列新增 cmd 定義(或建新 JSON)。
2. **`/action/<group>_actions.py`**:寫 `on_xxx(ctx, args)` handler + 在 `register(app)` 註冊 `app.disp.on(0xXXXX, on_xxx)`。
3. **`/action/registry.py`**:import 新模組並呼叫 `register(app)`。
4. **(可選)** `/tasks/` + `main.py` 或 `Core0.py`:若有背景任務。

驗證:

```python
# 離線 loopback
pkt = Proto.pack(0xXXXX, SchemaCodec.encode(cmd_def, {...}))
app.handle_stream(parser, pkt, transport_name="Test", send_func=print)
```

---

## 8) 與 mp_Net-Light 協議對照

| 項目 | mp_Net-Light(AI_CONTEXT.md 舊版) | mp_Net-Core(NC4,目前) |
|------|----------------------------------|----------------------|
| VER | 3 | **4** |
| Header | 2+1+2+2+2 = 9B(不含 CRC) | 2+1+2+2+2 = **9B** |
| CRC | CRC16-CCITT-FALSE,2B | **CRC32(binascii.crc32),4B** |
| CRC 範圍 | VER..DATA | **VER..DATA(buffer[2:9+LEN])** |
| 指令域 | 0x10xx sys / 0x11xx status / 0x12xx heartbeat+fs / 0x20xx file / 0x30xx stream | 0x10xx sys / 0x11xx status / 0x12xx heartbeat / 0x13xx now / 0x14xx hw / 0x15xx wtt / 0x18xx ram_bench / 0x20xx file / 0x30xx stream / 0x31xx jpeg / 0x32xx mp4 |
| Payload 類型 | 同 | 同(u8/u16/u32/i16/i32/str_u16len/bytes_fixed/bytes_rest) |

> `mp_Net-Light` 的 `ADD_NEW_CMD_FLOW.md` / `RUN_NETWORK_SERVER.md` 描述的組包/解析流程與本專案相同,只差 VER/CRC 常數。對接工具請以 `slave/lib/proto.py` 為準。

---

## 9) 相關檔案

- `slave/lib/proto.py` — 封包打包/解析(唯一真相)
- `slave/lib/schema_loader.py` — Schema 載入/排序/type code
- `slave/lib/schema_codec.py` — payload 編解碼
- `slave/lib/dispatch.py` — cmd → decode → handler
- `slave/lib/net_bus.py` / `circuit_bus.py` / `now_bus.py` — 傳輸層
- `slave/schema/*.json` — 指令定義
- `slave/action/*.py` — handler 實作
- `slave/app.py` — 裝配(create_parser / handle_stream)
