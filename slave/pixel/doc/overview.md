# pixel 子系統 — 總覽

> 介紹區：這個子系統是什麼、三層怎麼分、pixel_stream 怎麼讀。
> 測試區：§6 的自檢指令。

## 1. 介紹區 — 這個子系統是什麼

pixel 子系統把「控制單元（pixel / 電機）」的**排列順序與分組**、**動畫效果**、**兩者配對**
拆成三個獨立層，各自定義、最後才配對。

| 層 | 內容 | 檔案 | 最終 key（暫名） |
|---|---|---|---|
| 1. 分組 | 控制單元怎麼排、怎麼分組 | `pixel/registry.json` | `wave_groups` |
| 2. 效果 | 怎麼動（波形，全是生成器） | `pixel/effects/`（`effects.json` + `effects.py`） | `wave_effects` |
| 3. 模式 | 效果 × 群組/單顆 pixel + 寫入方法 | `pixel/map/*.mode.json` | `wave_map` |

> 「暫名」表示 key 尚未定案。

## 2. 介紹區 — pixel_stream 讀取契約

所有 pixel 引擎的輸出最終都要走 `pixel_stream` 這條通路。

### 2.1 它是什麼

`pixel_stream` 是一個 `AtomicStreamHub`（單寫者 / 單讀者 SPSC 無鎖環形緩衝），
在 `Core_Manager.launcher()` 建立：

```python
st_pixel = bus.get_service("st_pixel")                # PixelStreamer（slave/lib/PixelController.py）
hub = AtomicStreamHub(st_pixel.total_bytes * bus_sys["buffer_frames"])
bus.register_service("pixel_stream", hub)
```

- `total_bytes` = 所有 device 的 `num_pixels × 4` 加總 = **一幀 RGBW 的 byte 數**
- `buffer_frames`（config，目前 = 1）→ 單 slot 大小 = 一幀
- 槽數預設 3（三重緩衝）

### 2.2 幀格式（RGBW cell）

`pixel_stream` 流動的是一整幀 RGBW，每顆控制單元佔 4 bytes：

```
byte 0 = R,  byte 1 = G,  byte 2 = B,  byte 3 = W
```

幀內 device 的拼接順序由 `registry.json` 的 `order` 定義；這個順序**必須**與
`PixelStreamer.big_buffer` 的 controller 拼接順序一致。

### 2.3 讀取 API（`AtomicStreamHub` 兩種模式）

**copy 模式（現行 `RenderTask` 用）**：

```python
if hub.read_into(self.st_pixel.big_buffer):   # 把當前 slot 整塊複製進 big_buffer
    self.st_pixel.show_all()                   # 一幀渲染
# read_into 空了回 False → 跳過此 tick，不 show
```

**view 模式（零拷貝，將來熱路徑可用）**：

```python
view = hub.get_read_view()    # 取出當前 READY slot 的 memoryview，空了回 None
if view is not None:
    # ... 讀 view ...
    hub.release_read()        # 歸還 slot
```

### 2.4 讀者要做的固定動作（無分支）

讀者（`RenderTask`，跑在 Core 1）每次取到一幀後，永遠做同樣兩件事：

```python
st_pixel.big_buffer[:] = frame   # 1. 寫進 big_buffer（與 pixel_stream 同構）
st_pixel.show_all()              # 2. 逐 device 轉換 + 硬體輸出
```

`show_all()` 內部（見 `slave/lib/PixelController.py`）：
1. 對每個 controller 呼叫 `st_load_and_convert(buf, offset)` → `_convert`（依 `_tid` 分派 WS2812 / APA102 / i2c_pixel）
2. 再 `st_show()` 輸出

### 2.5 讀取契約總結

| 項 | 值 |
|---|---|
| hub 型別 | `AtomicStreamHub` |
| 單 slot 大小 | `st_pixel.total_bytes`（一幀 RGBW） |
| 槽數 | 3 |
| 讀取方法 | `read_into(target)`（copy）/ `get_read_view()`+`release_read()`（view） |
| 空語義 | 讀空回 `False` / `None` → 讀者跳過，不 show |
| 幀格式 | RGBW，每單元 4B，順序 = `order` |
| 讀者位置 | Core 1（`RenderTask`，`slave/tasks/render.py`） |

## 3. 介紹區 — 三層骨架

### 3.1 registry.json — 只管「排列次序」

- `order`：型別列表 = 各型別在全域 index 空間的拼接順序，也是「型別當作列表」的
  順序（對應舊的 LED_list / RGB_list）。
- `groups[].sel`：**有序的段列表**，每一段 `{"type": 型別名/int, "sel": 選擇器}`。
  段依書寫次序拼接成該 group 的像素序列——可交叉型別、跳躍、反序、重疊，
  對應舊的 `[LED_list[10:15], RGB_list[40:200], RGB_list[:10], LED_list[17:14]]`。
  選擇器：`7`（單顆）、`"0:14"`（範圍，end 不含）、`":"`（全選）、`"15:10:-1"`（反序）。
- **不再放 `state`（寫入方法）**——寫入方法移到配對層（§4）。

### 3.2 effects/ — 效果（生成器）

集中兩個檔：`pixel/effects/effects.json`（效果列表）+ `pixel/effects/effects.py`（生成器）。
**每個效果都有自己的 id + name**；id 從 1 開始，`0` 保留為「未指定 / 自動配發」哨兵值。

- **py 的效果名稱 = 函數名稱**（`fn.__name__`）。
- json 與 py 共用登記表、防撞車；**名稱撞車時程式（py）優先**，json 只補 id / params。
- 載入順序無關。

**已取消 `engine` 參數，也沒有「逐顆 / 整批」等模式之分**：只有一個生成器，輸出
位數由 `pixel_n` 決定（[1] ~ [n]）。效果參數 `pixel_n` / `program` / `speed` /
`reverse` 與程式函數的同名參數一一對應。生成器吐 **`array('H')` 緩衝**（0-4095），
供 scatter 的 viper 用 ptr16 直接讀，零分配。

### 3.3 map/*.mode.json — 模式（效果 × 群組 / 單顆 pixel）

「模式」是真正生效的載體，每個模式有**模式 ID（id）+ 模式名稱（name）**，放在
`map/` 資料夾下。`map[]` 把 effect 綁到 group（或單顆 pixel），**寫入方法在此配對時
輸入**。

- `group` 與 `effect` 都**同時支援 id（整數）或 name（字串）**，可混用。
- 執行「一次」或「不斷循環」由指令層決定，不寫進模式檔。

## 4. 介紹區 — 寫入方法（輸入方法）在哪裡

`rgb` / `w` / `ww` 這類「寫入方法」是**配對層**的屬性，不是效果、也不是型別的屬性。
同一個波（effect）可以配對不同群組、各給不同寫入方法，更模組化、更好操控。

| write | 每顆 LED 消費 | 寫入方式 | 語義 |
|---|---|---|---|
| `r` / `g` / `b` / `w` | 1 值 | >>4 → 只寫對應通道 | 單通道：**只寫自己，其餘通道不修改**（保留原值，可累加組合） |
| `ww` | 1 值 | 12-bit → byte2 低 8 + byte3 高 4 | 單通道（12-bit） |
| `rgb` | **3 值**（R,G,B） | 各 >>4 → R,G,B 位，W=0 | 多通道 |
| `rgbw` | **4 值**（R,G,B,W） | 各 >>4 → R,G,B,W 位 | 多通道（分開代表 4 位） |
| `wwww` | 1 值 | >>4 → 4 個 byte 全寫同值 | **一整個 LED**：一個數值代表整顆，scatter 不做通道語義，設備自行限制範圍（`_convert` 依 `_tid` 取它要的 byte） |

> **分工原則**：操作模式 = 值流的「消費形狀」，不猜設備。設備行為只在
> `PixelController._convert`（層 2，依 `_tid` 分派）。scatter 寫的是 RGBW cell
> （層 1 ↔ 層 2 的中間契約），不需要知道對方是誰。
> 保底：值流不足 → 取模循環重用；過長 → 多餘丟棄；空 → 全寫 0（對齊舊專案）。

**注意**：一個 group 若橫跨多種 device 型別（如現有 `full`），單一 `write` 無法同時
正確——建議群組按 device 型別保持同質，或由 map 作者確認 `write` 對目標型別正確。

## 5. 介紹區 — lib/pixel_layout.py（slave/lib）兩張表的橋樑

「混亂表（group 選擇）」與「整齊表（big_buffer）」之間的快速對照表，效果類似
PixelStreamer 預算 offsets：

- **混亂表**＝ registry 的 `order` + `groups[].sel`（選擇順序可任意）。
- **整齊表**＝ `big_buffer`（依 `order` 累加 count，每顆 pixel 一個 RGBW cell 4B）。

`PixelLayout` 預先把每個 group 的選擇展開成「全域 pixel index」存進 `array('H')`
（uint16，上限 65535 顆），`scatter(big_buffer, group, values, write)` 每幀用
`@micropython.viper` 的 `ptr16 + ptr8` 做零分配散射（實測 24× 快於純 Python）。
另提供 `set_value`/`get_value`（單顆操作）與 `controller_offsets`（整齊表單一真源，
供 PixelStreamer 取 offsets）。整合流程詳見 `integration.md`。

**實例數：所有 group 共用一个 `PixelLayout` 實例**（不是每個 group 一個）：

- `type_offsets` / `counts` 是「整齊表」的骨架，全域唯一——每個 group 的 index
  都基於同一張表，才能保證與 `big_buffer` 的 controller 順序一致（單一真源）。
- `register_group` 就是把各 group 的展開「加進」同一個實例的 `_groups` 表。
- 每個 group 各建一個實例會重複算骨架，且可能漂移出不同的整齊表。

## 6. 測試區 — 自檢

```bash
# 於 slave/ 目錄執行
python3 lib/pixel_layout.py      # 兩張表對照 + scatter + set/get + controller 對照
python3 pixel/effects/effects.py # 效果登記 + 生成器輸出（array('H')）
```

viper 速度只能在裝置上測（PC 沒有 micropython），測試骨架見
`lib/pixel_layout.py` 檔尾的 docstring。
