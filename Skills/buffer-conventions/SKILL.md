---
name: buffer-conventions
description: 本專案的緩衝層（buffer / ring / DMA 記憶體）使用規範。當要新增緩衝、傳輸資料、存取 heap_caps、建立 ring buffer、處理雙核心資料交換、寫 SD/顯示器的 I/O buffer，或看到 AtomicStreamHub / alloc_dma / heap_caps 想動手時，先讀這份。防止重新發明已有的緩衝機制。
---

# 緩衝層使用規範

本專案的資料緩衝已經有固定架構，**不要重新發明**。動手寫任何 buffer / ring / DMA 記憶體之前，先讀懂這份，用既有的東西。

## 架構全貌

```
┌──────────────────────────────────────────────────────┐
│  alloc_dma(size) → (buf, is_dma)                      │  唯一碰 heap_caps 的入口
│  free_dma(buf, is_dma)                                │  (lib/buffer_hub.py)
├──────────────────────────────────────────────────────┤
│  AtomicStreamHub                                      │  SPSC 無鎖環形緩衝
│   • try_dma=True → slot 配在內部 SRAM（CAP_DMA）      │  (lib/buffer_hub.py)
│   • copy 模式 + view 模式                              │
├──────────────────────────────────────────────────────┤
│  BusSources                                           │  bus 物件註冊表
│   • list() 供 BusDecodeTask 一次 drain 所有 rx_hub    │  (lib/bus_sources.py)
└──────────────────────────────────────────────────────┘
```

三層職責分明：分配器（記憶體從哪來）、環形緩衝（資料怎麼流）、註冊表（有哪些 bus）。**不要把這三件事混進同一個類別**——之前 `buffer_hub.py` 就是因為混了 bounce buffer 進來才變成四不像，已經清掉了。

## 規則一：heap_caps 只有一個入口

**需要「DMA 記憶體」（內部 SRAM）時，一律用 `lib.buffer_hub` 的 `alloc_dma` / `free_dma`，不要自己 `import heap_caps`。**

```python
from lib.buffer_hub import alloc_dma, free_dma

buf, is_dma = alloc_dma(size)   # is_dma=True 表示 buf 在內部 SRAM，需用 free_dma 釋放
# ... 用 buf ...
free_dma(buf, is_dma)           # is_dma=False 時 no-op，bytearray 交給 GC
```

- `alloc_dma` 優先用 `heap_caps.malloc(size, CAP_DMA)`，拿不到會自動 fallback 成 `bytearray`，**回傳的 buf 永遠可用**（不會是 None）。
- `is_dma` 旗標要記住，釋放時要帶進 `free_dma`。
- **絕對不要**在別的檔案寫 `import heap_caps; heap_caps.malloc(...)`。這份規則的存在，就是因為以前四個檔案各寫一份同樣的 try/except 樣板，互不共用。

**唯一例外**：`tasks/jpeg_player_task.py` 的 framebuffer 用 `CAP_SPIRAM`（PSRAM，大但慢），那是「PSRAM-first、搶不到才 DMA、再 fallback bytearray」的不同策略，跟 ring 的「內部 SRAM」需求無關，維持獨立。除非你真的要做 framebuffer，否則別碰那條路。

## 規則二：環形緩衝只有 `AtomicStreamHub`

跨核心、跨任務的資料交換用 `AtomicStreamHub`（`lib/buffer_hub.py`）。它是 **SPSC 無鎖 ring**——單一寫入者、單一讀取者。

### 雙核心交換 = 一對 ring

```
CPU A                          CPU B
┌──────┐   TX ring (A寫 B讀)   ┌──────┐
│      │ ────────────────────→│      │
│      │   RX ring (B寫 A讀)   │      │
│      │ ←────────────────────│      │
└──────┘                      └──────┘
```

- 兩個 core 交換資料 = **兩個 ring**，一個只讀一個只寫，方向相反。
- 每個 ring 內部 `_w_ptr` 只有寫端碰、`_r_ptr` 只有讀端碰，不需要鎖。
- **不要為了「雙核心」另寫一套 ring**，`AtomicStreamHub` 就是幹這個的。

### 建構

```python
from lib.buffer_hub import AtomicStreamHub

hub = AtomicStreamHub(size=1024, num_buffers=3, try_dma=False)
#                  ↑ 每槽位元組數  ↑ 槽數   ↑ True = slot 配在內部 SRAM
```

`try_dma=True` 的語意是「這個 ring 跨 core 傳資料，backing buffer 放內部 SRAM，讀寫更快且無 cache 一致性問題」。螢幕、SD 讀寫這類週邊 DMA 路徑才需要開。一般 bus RX 不用開。

### 兩種資料搬法——涵蓋所有場景

**copy 模式**（小封包、省事）：
```python
# 寫端
hub.write_from(source_bytes)     # 整塊 copy 進 slot；滿了回 False

# 讀端
hub.read_into(target_bytes)      # 整塊 copy 出來；空了回 False
```

**view 模式**（大 frame、零拷貝）：
```python
# 寫端
v = hub.get_write_view()         # 取出 slot 的 memoryview 直接寫；滿了回 None
if v is not None:
    v[:n] = my_data
    hub.commit()                 # 標記 READY 並推進寫指標

# 讀端
v = hub.get_read_view()          # 取出 READY slot 直接讀；空了回 None
if v is not None:
    process(v)
    hub.release_read()           # 歸還 slot
```

**選擇原則**：有完整一塊資料、圖省事 → copy 模式。資料很大、想省一次 memcpy（例如像素流）→ view 模式。兩者**不混用**在同一個 hub 的同一筆資料上。其他 API（`flush` / `dirty` / `get_fill_level` / `force_get_view`）視需要用。

## 規則三：不要加 bounce buffer

**本專案沒有、也不該有 Python 層的 bounce buffer。** 這是歷史教訓：

- 以前 `buffer_hub.py` 和 `bus_adapter.py` 各有一份 bounce buffer 寫法，**全部是死碼、從未被呼叫**，已經在整合時清掉。
- 真正的熱路徑（SPI 顯示器輸出）走的是 **C 層 `write_frame_dma` 自動分 chunk**，不需要 Python 中間過一手。`bus_adapter.py` 的 `write_data_async` 註解寫得很清楚：「不再過 Python bounce 序列化」。
- 如果哪天量測到某條路徑真的需要 Python 層 bounce，**它應該是 `alloc_dma` 之上的一個 helper，不是塞進 ring 的方法**。先討論再動手，不要默默又寫一份。

## 規則四：BusSources 不用動

`lib/busSources`（`bus_sources.py`）是一個 bus 物件清單，用 `id()` 去重，供 `BusDecodeTask` 一次撈出所有 bus 的 `rx_hub` 去 drain。它和 ring 是不同層（一個管「有哪些 bus」，一個管「bus 內的 ring」），職責清楚，**不要把它跟 ring 混在一起**。

## 快速判斷：我該用什麼？

| 我想做的事 | 用這個 |
|-----------|--------|
| 分配一塊 DMA 記憶體（給週邊、給跨 core） | `alloc_dma(size)` |
| 兩個任務/核心之間傳資料 | `AtomicStreamHub`，一對 TX/RX ring |
| 小資料塞進 ring | copy 模式：`write_from` / `read_into` |
| 大 frame 進 ring、省 copy | view 模式：`get_write_view`+`commit` / `get_read_view`+`release_read` |
| 註冊一個新 bus 讓 BusDecodeTask 收 | `BusSources.add(bus)` |
| 寫一個新的 ring buffer 類別 | **停下來。** 先讀這份，用 `AtomicStreamHub` |
| 寫 `import heap_caps` | **停下來。** 用 `alloc_dma` |
| 加一個 bounce buffer | **停下來。** 讀「規則三」 |

## 常見錯誤（前人踩過的）

1. **就地 `import heap_caps` 重寫一份** — 四個檔案各寫一次，維護不過來。全收斂到 `alloc_dma` 了，別再開分支。
2. **把 DMA 分配塞進 ring 類別當方法** — 讓 ring 變成「緩衝 + DMA + bounce」四不像。分配是分配、ring 是 ring，分開。
3. **為了「效能」自建 ring** — `AtomicStreamHub` 有 `@micropython.native`，已經夠快。先量測再說。
4. **mix copy 模式跟 view 模式在同一筆資料** — 會打亂 slot 狀態機。一筆資料從頭到尾用同一種模式。

## 相關檔案

- `lib/buffer_hub.py` — `alloc_dma` / `free_dma` / `AtomicStreamHub`
- `lib/bus_sources.py` — `BusSources` 註冊表
- `lib/bus_adapter.py` — 週邊 adapter（SPI/I2C/I80/RGB），不再碰 heap_caps
- `lib/fast_io.py` — SD 讀寫，`Storage` / `StreamReader` 都走 `alloc_dma`
- `tasks/bus_decode.py` — `BusDecodeTask`，消費 `BusSources`
