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
| 0x1403 | SPEED_SET | M→S | `bus_type(u8)` `bus_id(u8)` `speed(u32)` `timeout_ms(u32)` | 記 old/target/timeout_at（**不切速**），先回 0x1404(舊速) 再 apply 切速 |
| 0x1404 | SPEED_ACK | S→M | `ok(u8)` `bus_type(u8)` `bus_id(u8)` `cur_speed(u32)` `target_speed(u32)` | 同步點（收到後兩邊一起切速） |
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
2. slave 記 old_baud / target / timeout_at（進 SYNCING，**尚未切速**）
3. slave 回 SPEED_ACK(0x1404, 舊速)
4. slave 送出 0x1404 後呼叫 bus_speed_apply()：等 txdone() 排空 + margin，再 uart.init(target) 切速
   master 收到 0x1404 後立即切速（兩邊同步切）
5. [新速] master 在 timeout_ms 內「不斷敲門」驗證（SPEED_QUERY/STATUS_GET/IDENTIFY）
6. 驗證 OK → SPEED_COMMIT(0x1405) 鎖定（取消回滾，進入 COMMITTED + 啟動 idle 超時）
   ; 否則 timeout_at 到 → 自動回滾 config 舊速 → IDLE
7. 傳輸完成 → SPEED_REVERT(0x1406) 還原 old_baud
```

- **兩層 timeout**：①SYNCING 層 `timeout_at`（SET 的 `timeout_ms`，敲門失敗回滾）；②COMMITTED 層 `idle_timeout_at`（進入通訊後 N 秒無有效通訊回滾，`app.handle_stream` 每收到有效幀呼叫 `bus_speed_touch()` 刷新）。目前兩層暫共用同一 `timeout_ms`。
- **同步點 = SPEED_ACK**：slave「先回 ACK(舊速) 再切速」，master 收到 ACK 後一起切速。避免舊版「先切速再回 ACK」造成 ACK 以新速發出、master 收不到的時序 bug。
- 回滾 = 純時間檢查，由 `CircuitTask.loop` 每輪呼叫 `bus_speed_poll()`；即使新速下收不到有效幀，loop 照跑、照樣回滾（解掉「收不到指令→惰性檢查不觸發」死結）。
- **`_cur_baud` 修正**：MicroPython UART 無 `baudrate` 屬性，`_cur_baud` 回 0 會導致 `old_baud=0`、REVERT 不切速。已加 `_config_baud(bus_id)` 從 config 讀舊速，`_reinit_uart()` 切速時保留 rxbuf/txbuf（避免 `uart.init(baudrate=...)` 把 buffer 縮回預設 256）。

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

---

## 9) 2026-08-23 新增：FILE_PROMOTE + buffer 調校 + 測試工具（晚間）

> 更新日期 2026-08-23。這輪圍繞「雙板 UART 檔案傳輸 + 固件交換上線」做了三塊：①新增 FILE_PROMOTE 指令；②UART 接收 buffer 對齊 + 多插槽；③master 端互動/安全更新工具。

### 9.1 FILE_PROMOTE（0x2011）— SD → 根目錄固件正式上線

新增獨立指令，把「先上傳到 SD 驗證、確認無損再交換到根目錄正式上線」的需求落地。設計要點：

| 面向 | 內容 |
|------|------|
| 指令 | `FILE_PROMOTE 0x2011`，payload `src(str)` + `dst(str)` |
| 語意 | 把 `src`（/sd 暫存）內容「正式上線」到 `dst`（根目錄系統檔），舊 `dst` 自動留 `.bak` |
| 跨卷安全 | 用「讀+寫+刪」三步法，**不靠 `os.rename`**（未來接真 SD 卡、獨立掛載點也能用） |
| 流程 | ①src 串流複製到 dst.tmp → ②舊 dst→dst.bak（失敗自動還原）→ ③dst.tmp→dst → ④刪 src |
| 成功回覆 | `FILE_QUERY_RSP`（path=dst、exists=1、size） |
| 失敗回覆 | `FILE_ERROR_RSP`（err_write_fail=1） |

實作檔案：`slave/schema/file.json`、`slave/lib/sys/fs_manager.py::promote_file()`、`slave/action/file_actions.py::on_file_promote`。

### 9.2 UART 接收 buffer 對齊 + 多插槽

- `slave/driver/uart_drv.py`：UART `rxbuf/txbuf` 都改 16384（原先 txbuf 只有 4096，裝不下最大幀 8205B）。
- `slave/lib/sys/proto.py`：`RX_BUF_SIZE` 4096 → **4115**（一幀剛好一槽，避免拆幀）。
- `slave/lib/sys/circuit_bus.py`：`u8_rx_slots` 預設 2→8、上限 4→16（多插槽扛消費延遲，而非單槽變大）。
- `slave/lib/sys/bus_speed.py`：`_reinit_uart()` 切速時保留 rxbuf/txbuf（`uart.init(baudrate=...)` 會把 buffer 縮回預設 256）。

> 判斷：這批 buffer 調校方向正確，115200 下 4KB chunk 傳輸已穩定（8/10，重試可到近 100%）。高速 460800 可正常收發（3/5），剩餘掉包是 CircuitTask 排程 / bus_decode 消費速度問題，尚未根治（見 `08_night_test_results.md` §18）。

### 9.3 master 端工具（`test/protocol/night_run/`）

| 檔案 | 用途 |
|------|------|
| `master_agent.py` | master 測試 agent：NC4 組/拆幀 + SPEED/FILE 指令 + 手動 decoder + `send_wait` 重試 |
| `safe_update.py` | 安全檔案更新流程：`stage`/`verify_stage`/`apply`/`promote`/`confirm`/`undo`/`cleanup` |
| `interactive_master.py` | 互動式選單（仿 NetBusMaster 風格）：敲門/檔案傳輸/固件更新/查詢/刪除/提速 |
| `repl_upload.py` | 透過 normal REPL(ctrl-B) base64 寫檔的工具（繞過 TaskManager 佔用 raw REPL） |
| `espnow_transfer.py` | ESP-NOW 板間傳檔框架（未端到端實測） |

### 9.4 尚未完成

- **端到端 FILE_PROMOTE 實測**：卡在多 chunk 連續傳輸掉包（單 4KB chunk 可過，8KB 兩 chunk 連發偶發失敗）。
- **掉包根因**：slave 端 `bus_decode` 每輪只讀 1 slot（`decode_budget_slots` 預設 1）+ CircuitTask 排程，是架構級瓶頸，需進一步調整。
- **RS485 半雙工**：master 端時序要照 `_Rs485Uart`（listen-before-talk + DE 切換 + txdone）重寫；目前是點對點全雙工。
- **無線 ESP-NOW 傳檔**：鏈路驗證過、腳本備好，端到端未測。

---

## 10) 2026-08-24 新增：pixel 效果子系統重構 + RenderTask 節拍 wrap 修復

> 這輪圍繞 pixel 燈效做了兩塊：①效果框架與目錄解耦、json 成為唯一真源；②修掉 RenderTask 計時器 wrap 導致「跑一段時間燈自己停」的 bug。

### 10.1 效果子系統重構（框架 / 目錄 / json 三權分立）

| 檔案 | 角色 |
|------|------|
| `slave/lib/sw/effect_core.py` | 框架：`Effect` 基類 + 登記表 + 波表快取 + `check_conflicts()` |
| `slave/pixel/effects/effects.py` | 效果目錄：畫波效果 + py 補充類別 + `register()` + 自檢 |
| `slave/pixel/effects/effects.json` | **唯一真源**：id/name/params（含 program 畫波）都在這手寫 |

設計要點：

- **json 是唯一真源**：id / name / params（含 program 畫波）全在 `effects.json` 手寫。
- **畫波效果不需要 py 類別**：program 寫 json，由內建 `Effect` 播放（波表預算 + viper + 無浮點）。
- **只有畫波寫不出來的效果才寫 py**：`register(類別)`，靠 name 與 json 配對（如 `pearl_chain` 珍珠鏈：畫完波後「批量派發 + 控制間距」）。
- **id/name/配對衝突不 raise**：啟動時 `check_conflicts()` 列印警告（對齊 boot GPIO 檢查），人肉判斷修正。
- 波形段 `F` 語義：**`F/10 = 段內週期數`**（`F=5` 半週期=純升或純降、`F=10` 完整週期=升+降）。
- 相位 `phi`（0-4095 ≈ 0-360°）：`1023`=峰、`2047`=中點、`3071`=谷。

### 10.2 RenderTask 節拍 wrap bug（燈跑一陣子自己停、無 log）

**症狀**：本地燈效無限循環播放一段時間後，燈靜止/熄滅，且**不印任何 log**（不是 buffer 爆、不是重啟）。

**根因**：`slave/tasks/render.py` 的 RenderTask 節拍推進用錯 API：

```python
# ❌ 錯：普通整數加法，next_tick_us 不會 wrap
self.next_tick_us += self.interval_us
```

而 `time.ticks_us()` 在 ESP32 MicroPython 是**會週期性 wrap 的 32-bit 值**。`+=` 讓 `next_tick_us` 一路往上加，與 wrap 回小值的 `now` 相位錯開後，`ticks_diff(now, next_tick_us)` 永遠為負 → `>= 0` 永不成立 → RenderTask 每輪都 `return`，靜默停止取幀。

**修復**：

```python
# ✅ 對：ticks_add 會正確 wrap
self.next_tick_us = time.ticks_add(self.next_tick_us, self.interval_us)
```

> 已 grep 全 `slave/` 確認只有 `render.py` 這一處誤用；其餘 tick 推進都用 `ticks_add` / `ticks_diff`。

### 10.3 相關文件

- `02_guides/11_developing_effects.md` — 開發燈效完整教學（三種寫法 / Effect API / 波形段 / 色彩 / write 模式 / 框架 API / 四層資料）。
- `02_guides/08_pixel_subsystem.md` — pixel 四層資料 + 播放模型。
- `slave/lib/sw/effect_core.py` — 效果框架。
- `slave/pixel/effects/effects.py` — 效果目錄（含 `pearl_chain` / `example_eyes` 範例）。

---

## 11) 2026-08-24 新增：UART-412 馬達接入 pixel + 停止填中性值（dStay）

> 這輪把 UART-412 馬達（ATTiny412 電機控制器）接入 pixel 系統，並把「停止/熄燈」改成填中性值（對齊舊專案 mp_LEDController 的 dArc 概念）。

### 11.1 馬達走 pixel 系統（讀 W 通道）

- `UartMotor`（`slave/lib/hw/uart_motor.py`）實作 controller 介面：`pixel_type="uartMotor1"`、`frame_size`（×4）、`st_load_and_convert()`（從 big_buffer 提取 W 通道 8-bit）、`st_show()`。
- 效果用 `write:"w"`（或 rgbw）→ W 通道 = 速度 byte（0x80 停、<0x80 正轉、>0x80 反轉）。
- 初始化鏈：`driver/motor_drv.py`（讀 config `uartMotor`）→ `boot.py` 註冊 → `pixel_drv.py` 聚合進 pixel_list → `pixel_task.TYPE_MAP` 加 `uartMotor1`。

### 11.2 UART-412 協議關鍵（單台串接，不用廣播）

- 廣播模式受 `MAX_DEVICE=32` 限制（原碼 `while i < MAX_DEVICE+2`），address > 32 收不到。
- `show_all()` 改為**單台 frame 串接**：`ff addr value fe` × N 一次過 uart.write（address 不連續也不填空洞）。
- **歸零保護**：UART-412 的 `value=0` = 全速正轉（updateMotor: IN1 PWM 254）！`st_load_and_convert` 讀到 0 → 映射中性值（死區 0x80），避免 reset/熄燈暴走。

### 11.3 停止 = 填中性值（dStay，對齊舊項目 dArc）

- 舊專案 `LEDController.reset()` 回到 config 的 `dArc`（不是 0）；本專案命名 **`dStay`**（default Stay，12-bit 0-4095）。
- `PixelStreamer.clear_all()`：每個 controller 填自己的 `neutral_value`（燈=0 熄滅、motor=0x80 死區停）。
- 三處停止流程統一改用：`render.py`（is_streaming 熄燈）、`pixel_task._stop()`、`Core_Manager` 退出。
- config 每台設備可設 `dStay`：WS2812/APA102/PCA9685 預設 0；uartMotor 預設 2048（= 0x80）。

### 11.4 相關文件

- `02_guides/08_pixel_subsystem.md` — §4.1 Pixel Render 架構簡介（雙核 + hub + controller + 停止填中性值 + motor 接入）。
- `02_guides/11_developing_effects.md` — §7 新增「用 write:w 驅動馬達」。
- `slave/lib/hw/uart_motor.py`、`slave/driver/motor_drv.py`、`slave/lib/sw/PixelController.py`（clear_all / neutral_value）。
