# 更新紀錄：遠端更新鏈路 / 臨時提速 / lib 三級分類 / 解碼性能 / 重複 import 清理

> **用途**：整合說明本次一系列更新的完整設計、指令集、檔案結構與行為語意。
> **分類**：筆記（03_notes）
> **最後更新**：2026-08-21
> **範圍**：`slave/` 韌體；`cores/`（PC 模板，已同步 import）；`test/` 與 `tools/` 尚未同步（見 §6）。

---

## 1) 總覽：本次更新包含四大塊

| 區塊 | 摘要 | 關鍵檔案 |
|------|------|---------|
| 遠端更新鏈路（第一階段） | 發現(IDENTIFY)、保險(REBOOT/WREPL/WEBUI)、網絡(NET_START)、IP(GET_IP)、master 定址(SET_MASTER) | `action/net_actions.py`、`schema/sys.json` |
| 臨時提速 | 協商式 UART 提速 + 超時回滾 | `action/hw_actions.py`、`schema/hw.json`、`lib/sys/bus_speed.py` |
| lib 三級分類 | `lib/` 拆為 `hw/ sys/ sw/` | `lib/hw/`、`lib/sys/`、`lib/sw/` |
| 解碼性能優化 | `pop_frame` 零拷貝 + 非 generator、ADDR 過濾、native handle_stream | `lib/sys/proto.py`、`app.py` |
| 重複 import 清理 | 熱路徑內（`loop`/handler）的函式內 import 提到模組頂部 | `lib/sys/task.py`、`action/hw_actions.py`、`action/net_actions.py` |

---

## 2) 定址模型（cID / master_cid）

- **`bus.cid`(uint16)**：裝置自身的協議短身份，由 `ConfigManager.ensure_cID()` 於 **T0（boot.py import 時）** 建立——`System.cID` 為空時以 `machine.unique_id()` 末 4 碼填入並持久化；取不到則 `"FFFF"`。cID 是**單一擁有**、由 ConfigManager 推動，消費者（解碼層）只讀不重算。
- **`bus.master_cid`(uint16, 內存)**：回應定址目標，預設 `0xFFFF`（廣播=未設定）。Master 透過 `SET_MASTER` 或 `IDENTIFY_REQ` 的 `reply_addr` 告知 slave；slave 記住後，所有回應的 `addr` 欄位都填 `bus.master_cid`。**只存內存，重開機丟失**（下次開機 master 再告訴）。
- **ADDR 過濾(`app.py` `handle_stream`)**：只收 `addr == ADDR_BROADCAST(0xFFFF)` 或 `addr == bus.cid` 的幀，其餘 `continue` 丟棄。這讓「逐 address 掃描」的 RX 端現成可用。

### IDENTIFY 流程（逐 address 掃描，模仿 I2C）

```
master 對 addr=X 發 IDENTIFY_REQ(0x100D, payload 帶 reply_addr)
  → 只有 cid==X 的 slave 收到
  → 記 bus.master_cid = reply_addr(非 0xFFFF 才記)
  → 回 IDENTIFY_RSP(0x100E): cid + slave_id + 多介面 IP JSON, addr 回 master_cid
```

---

## 3) 新增指令集

### 3.1 sys 群（0x10xx，空編號 0x100D 起）

| CMD | 名稱 | 方向(發起→接收) | Payload | 行為 |
|---|---|---|---|---|
| 0x100D | IDENTIFY_REQ | Master→Slave | `reply_addr(u16)` | 逐 address 素描；帶 reply_addr 告知 master_cid |
| 0x100E | IDENTIFY_RSP | Slave→Master | `cid(u16)` `slave_id(str)` `ip(str)` | 回應；`ip`=多介面 JSON |
| 0x100F | REBOOT | Master→Slave | `delay_ms(u32)` | 延遲後 `machine.reset()` |
| 0x1010 | WREPL_CTRL | Master→Slave | `action(u8)` 0=查 1=開 2=關 | 回 0x1011 |
| 0x1011 | WREPL_RSP | Slave→Master | `enabled(u8)` `info(str)` | WebREPL 狀態 |
| 0x1012 | NET_START | Master→Slave | `iface_type(u8)` 0=lan 1=wifi 2=ap 3=espnow | 依 config 啟動，回 0x1013 |
| 0x1013 | NET_START_RSP | Slave→Master | `ok(u8)` `iface(str)` `ip(str)` | 啟動結果 |
| 0x1014 | GET_IP | Master→Slave | (空) | 回 0x1015 |
| 0x1015 | IP_RSP | Slave→Master | `ip(str)` | `ip`=多介面 JSON |
| 0x1016 | SET_MASTER | Master→Slave | `master_cid(u16)` | 顯式設 master_cid |
| 0x1017 | WEBUI_CTRL | Master→Slave | `action(u8)` 0=查 1=開 2=關 | 回 0x1018 |
| 0x1018 | WEBUI_RSP | Slave→Master | `enabled(u8)` `info(str)` | WebUI 狀態 |

> Slave 端註冊 handler 的請求：0x100D / 0x100F / 0x1010 / 0x1012 / 0x1014 / 0x1016 / 0x1017。
> Slave 端只送出（不註冊 handler）的回應：0x100E / 0x1011 / 0x1013 / 0x1015 / 0x1018。
> 既有 0x1009 WEB_CTRL 保留不動（舊式、無回應，不動合同）。

### 3.2 hw 群（0x14xx，空編號 0x1403 起）— 臨時提速

| CMD | 名稱 | 方向 | Payload | 行為 |
|---|---|---|---|---|
| 0x1403 | SPEED_SET | M→S | `bus_type(u8)` `bus_id(u8)` `speed(u32)` `timeout_ms(u32)` | 記 old/target/timeout_at，回 0x1404 後立即切速 |
| 0x1404 | SPEED_ACK | S→M | `ok(u8)` `bus_type(u8)` `bus_id(u8)` `cur_speed(u32)` `target_speed(u32)` | 同步點（送出即切） |
| 0x1405 | SPEED_COMMIT | M→S | `bus_type(u8)` `bus_id(u8)` | 鎖定新速、取消回滾 |
| 0x1406 | SPEED_REVERT | M→S | `bus_type(u8)` `bus_id(u8)` | 還原 old_baud（config 舊速） |
| 0x1407 | SPEED_QUERY | M→S | `bus_type(u8)` `bus_id(u8)` | 查狀態，回 0x1408 |
| 0x1408 | SPEED_STATUS | S→M | `state(u8)` `bus_type(u8)` `bus_id(u8)` `cur_speed(u32)` `target_speed(u32)` `remain_ms(u32)` | 狀態回報 |

- `bus_type` 沿用 `hw_manager.HW` 常數：UART=7, SPI=2, I2C=3。**第一階段只實作 UART**；SPI/I2C 回 `ok=0`（not supported）。
- `speed` 用 u32（baudrate 如 921600 超 u16）。
- `state`：0=IDLE, 1=SYNCING（已切、待 COMMIT）, 2=COMMITTED（鎖定）。

### 提速協商流程（同步點 = SPEED_ACK）

```
1. [舊速] master 發 SPEED_SET(0x1403: bus_type, bus_id, speed, timeout_ms)
2. slave 記 old_baud / target / timeout_at → 回 SPEED_ACK(0x1404, 舊速)
3. slave 送出 0x1404 後「同一 handler 內立即」uart.init(baudrate=target) 切速
   master 收到 0x1404 後立即切速
4. [新速] master 用既有 STATUS_GET(0x1101) / IDENTIFY_REQ(0x100D) 敲門驗證
5. 驗證 OK → SPEED_COMMIT(0x1405) 鎖定(取消回滾)
   ; 否則 timeout_at 到 → 自動回滾 config 舊速 → IDLE
6. 傳輸完成 → SPEED_REVERT(0x1406) 還原 old_baud
```

- **唯一的「等待」是 `timeout_ms`**（沒 COMMIT 就回滾的保險），不是 apply delay。
- **「亂碼不回覆」是切速瞬間外部 bus 的自然現象，Net-Core 不偵測亂碼、不 auto-baud**。
- 回滾 = 純時間檢查，由 `CircuitTask.loop` 每輪呼叫 `bus_speed_poll()`；即使新速下收不到有效幀，loop 照跑、照樣回滾（解掉「收不到指令→惰性檢查不觸發」死結）。

---

## 4) lib 三級分類重構

### 分類規則（已定案）

- **`lib/hw/`（硬體）**：直接碰 `machine`/GPIO/I2C/SPI/UART 的週邊驅動。
- **`lib/sys/`（系統）**：Net-Core 框架本身，彼此互相依賴的那群。
- **`lib/sw/`（軟體）**：獨立可用、能搬去別處照用的通用工具（不依賴框架）。

### 最終目錄結構

```
lib/
├── __init__.py
├── hw/  (8 模組 + __init__.py = 9 檔)  apa102, gt1151q, husb238, mp3_tf_16p, pca9685, TFT, uart_motor, xl9555
├── sys/ (21 模組 + __init__.py = 22 檔) buffer_hub, bus_adapter, bus_sources, bus_speed, circuit_bus,
│             ConfigManager, dispatch, fast_io, fs_manager, hw_manager,
│             log_service, net_bus, network_manager, now_bus, proto,
│             schema_codec, schema_loader, sys_bus, task, task_manager, webrepl_ctl
└── sw/  (3 模組 + __init__.py = 4 檔)  PixelController, PixelMathMethod, pixel_layout
```

### import 規則

- 一律**絕對 import**：`from lib.<cat>.X import ...`。
- 動態字串：`__import__("lib.TFT", ...)` → `__import__("lib.hw.TFT", ...)`（`driver/tft_drv.py:30`）。
- 跨包依賴：TFT(hw) → bus_adapter(sys) 用 `from lib.sys.bus_adapter import ...`。
- sw 包零內部依賴（只 import stdlib/machine）。

---

## 5) 解碼性能優化

### 5.1 pop_frame（零拷貝 + 非 generator）

- `StreamParser.pop_frame()`：解出單幀回 `(ver, addr, cmd, payload_mv)`，payload 是 `_buf` 的 memoryview（零拷貝），非 generator。
- `pop()`：相容介面，包 `pop_frame()` + `bytes(payload_mv)`（payload 可跨 feed 安全持有），保留給正確性測試/需跨幀持有者。
- 熱路徑（`app.handle_stream`）改用 `pop_frame`，避免每幀 `bytes()` 配置 + generator 物件引發的 GC churn。

**實測（ESP32, MicroPython/viper 真實）：**

| 測試 | 改前(pop) | 改後(pop_frame) |
|---|---|---|
| 純解碼 8K | 1.11 MB/s | **4.00 MB/s** |
| 純解碼 4K | 0.91 | **3.62** |
| 純解碼 2K | 0.85 | **2.99** |
| 雙緒管道 4K | 0.97 | **2.33** |

### 5.2 ADDR 過濾 + native handle_stream

- `handle_stream` 加 `@micropython.native`，hot loop 用 `pop_frame` + `bus.cid` 過濾。
- `my_cid`/`disp` hoist 到 loop 外（local），每幀只做 int 比較，零 hex 轉換。

### 5.3 緩衝重用（已探討、未採用）

- 「從 hub slot 零拷貝 pop」原型量到 6.85 MB/s，但因 MicroPython `memoryview` 無 `.find`、`bytes()` 拷貝 + GIL 串行下打崩，**不採用**；實際瓶頸在 feed 拷貝，已由 pop_frame 吸收大部分。

### 5.4 重複 import 清理（熱路徑 hoist 到頂部）

掃描全部函式體內的 import，分「該提」與「該留」兩類，只提前者：

**提到模組頂部（熱路徑 / 重複觸發，無循環依賴）：**
- `lib/sys/task.py`：`fcache_get()`（每 loop 都呼叫的快取讀取）內的 `from lib.sys.sys_bus import bus` 提到頂部。
- `action/hw_actions.py`：4 個 SPEED handler 內的 `from lib.sys import bus_speed` 提到頂部。
- `action/net_actions.py`：`on_wrepl_ctrl` 內的 `from lib.sys import webrepl_ctl` 提到頂部。

**刻意保留（lazy import，動了會壞）：**
- `from lib.sys.now_bus import NowBus`（now_bus import `espnow`，硬性依賴，不能 eager）。
- `fs_manager` / `log_service` / `network_manager` 內部的 `sys_bus` / `cfg_manager` import（避免循環依賴 + 延遲載入）。
- `tft_drv` / `gt1151q_drv` / `husb238_drv` / `xl9555_drv` / `PixelController` 等可選硬體驅動（沒啟用就不吃記憶體）。

> 原因：MicroPython 的 `import` 靠 `sys.modules` 快取，模組只載入一次、不會重複佔記憶體；但**函式體內的 `from lib import X` 每次執行都做 dict 查表**。在 `loop()` 這種巨大循環內，每輪查表會累積；在 handler（收到指令才觸發）內則可接受。規則：熱路徑一律模組級 import，handler 可保留函式內 import。

---

## 6) 已知待辦與注意

- **`test/` 與 `tools/` 尚未同步新 import 路徑**（重構只改了 `slave/` + `cores/`）。這些目錄的 `from lib.X import` 目前會 import 失敗，需後續補。
- **`temp/1/` 是 legacy 樹**，有自己的 lib，不屬本次範圍，勿動。
- **OTA（0x22xx）完全不動**——屬合作方合同，不增減、不實作、不用。
- 一次性重構腳本（`refactor_lib.py`、`deploy_lib.py`）與診斷檔（`test/_diag_*.py`、`test/_verify_*.py` 等）保留供參考，可視需要清理。

---

## 7) 相關文件索引

- `01_protocol/09_bus_speed_protocol.md` — 臨時提速協商流程詳解（本文件 §3.2 的獨立版）。
- `01_protocol/01_nc4_protocol.md` — NC4 封包格式（SOF/ADDR/CMD/CRC）。
- `01_protocol/05_integration_overview.md` — 既有協議整合說明。
- `slave/schema/sys.json` / `hw.json` — 指令 schema 唯一真相。
- `slave/action/net_actions.py` / `hw_actions.py` — 新指令 handler 實作。
- `slave/lib/sys/bus_speed.py` — 提速狀態機。
- `slave/lib/sys/proto.py` — 封包 + pop_frame。

---

## 8) 檔案更新流程重設計（2026-08-21）

FILE_* 0x20xx 檔案傳輸鏈路的重新設計：接收端完全被動、傳輸無關；新增兩段式 commit、斷點續傳、manifest 分離與 delta journal。

| 項目 | 內容 |
|------|------|
| 新增指令 | `0x2008 FILE_CONFIRM`、`0x200A FILE_UNDO`、`0x200D FILE_MOVE`、`0x200E FILE_PARTIAL_QUERY`、`0x200F FILE_PARTIAL_RSP`、`0x2010 FILE_ERROR_RSP` |
| 加欄位 | `FILE_QUERY_RSP`(0x2006) 加 `free` `pending`；`FILE_SCAN`(0x200B) 加 `target` |
| 兩段式 commit | 同名覆蓋不再直接刪舊檔：寫 pending → 舊檔 `.bak` → 新檔上位 → 更新 manifest；CONFIRM/UNDO 收尾 |
| 斷點續傳 | `.tmp` + delta `partial` 紀錄；正確性由 FILE_END 整檔 sha256 保證 |
| manifest 分離 | 本地 `/manifest.json` + SD `/sd/.manifest.json`，不融合，write-through 維護 |
| delta journal | `/sd/.delta.json`，`partial` + `pending` 兩段 |
| 自測 | `tools/selftest_file.py` loopback，真機 17 通過 0 失敗 |

關鍵檔案：`slave/lib/sys/fs_manager.py`、`slave/action/file_actions.py`、`slave/schema/file.json`（`echo/lib/fs_manager.py` 已同步）。完整用法見 `02_guides/10_file_update.md`。

> 已知限制：Slave 端回應幀仍走廣播（`Proto.pack` 不帶 addr）。單一 master 沒問題，但真正 MCU↔MCU 對等（多節點共享介質）需補「來源位址 + 回給來源」，建議單獨一輪做，避免與檔案流程耦合。
