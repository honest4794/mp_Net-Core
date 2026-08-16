# pixel 整合流程 — 一幀怎麼跑

> 介紹區：gen → map → layout → show_all 五步整合。全程用**緩衝**表示，
> 不用 Python list 語法，避免誤解成列表。

## 1. 介紹區 — 整條鏈

```
gen（效果生成器）──▶ 緩衝（array('H')，0-4095）
        │
        ▼  依 map 配對（group + write）
PixelLayout.scatter（亂序選擇 → 整齊表落點，viper）
        │
        ▼
big_buffer（RGBW 幀，bytearray）──▶ st_pixel.show_all()（一次推硬體）
```

## 2. 介紹區 — 逐步說明

### 第 1 步：gen 產出一個緩衝

`PixelGenTask` 開機時把 effect 變成 generator 存進 `bus.shared["pixel_gens"]`。
執行時 `next(gen)` 一次，拿到一個 `array('H')` 緩衝：**長度 = pixel_n、每項 0-4095**。

例：gen 吐 5 個位，內容是 123、255、50、200、100（假設 pixel_n = 5）。

```python
vals = next(gen)     # array('H')，長度 5
```

### 第 2 步：map 告訴你「放哪、怎麼放」

`pixel/map/demo1.mode.json` 的第一個配對（map 的第 0 項，對應「群組 0」）：

```json
{ "group": 1, "effect": 1, "write": "rgb" }
```

- `effect: 1` → 用 breathing 的 gen（上面那組值）
- `group: 1` → 目標是 `gundam_body` 這個群組
- `write: "rgb"` → 單色值要放進 RGBW cell 的 R=G=B（混白光）

### 第 3 步：群組展開成「目標像素」（建表時只做一次）

`PixelLayout.register_group` 把 `registry.json` 裡 `gundam_body` 的 `sel`（四段）
展開成**全域 pixel index 緩衝**，存進 `array('H')`。以第一段 `pwm 10:15` 為例，
前 5 顆落在全域 index：326、327、328、329、330。

byte 落點 = index × 4（viper 裡 `<< 2` 免費算）：1304、1308、1312、1316、1320。

### 第 4 步：scatter 逐顆整合進 big_buffer（通道流視圖）

```python
lay.scatter(big_buffer, "gundam_body", vals, "rgb")
```

**操作模式 = 值流的消費形狀**（不猜設備）：

- 單通道（1 值/顆，獨立操作單一通道）：`r` / `g` / `b` / `w`——**只寫對應通道，
  **其餘通道不修改**（保留原值，可累加組合）；`ww` 12-bit 寫 byte2/3
- 多通道（每顆多值）：`rgb` 3 值、`rgbw` 4 值（分開代表 R,G,B,W 四個位）
- `wwww`：**1 值/顆，一個數值代表整顆 LED**——4 個 byte 全寫同值（>>4），
  scatter 不做通道語義，設備自行限制範圍

例：gen 吐 5 個值 123、255、50、200、100（pixel_n = 5），`rgb` 寫給 5 顆 → 每顆 3 值：

| 通道序 | 值(H) | 值>>4 | LED | 通道 |
|---|---|---|---|---|
| 0 | 123 | 7 | 0 | R |
| 1 | 255 | 15 | 0 | G |
| 2 | 50 | 3 | 0 | B |
| 3 | 200 | 12 | 1 | R |
| 4 | 100 | 6 | 1 | G |

第 1 顆的 B 通道拿不到第 6 個值 → **保底：取模循環**回第 0 個值（123→7）。

big_buffer 的連續 byte 流：

```
7, 15, 3, 0,  12, 6, 7, 0,  15, 3, 12, 0,  ...
│───第 0 顆──│  │───第 1 顆──│  │───第 2 顆──│
   (R,G,B,0)     (R,G,B,0)     (R,G,B,0)
```

- **`r` / `g` / `b` / `w`**：每顆 1 值 → **只寫對應通道，其餘通道不修改**
  （同一顆 LED 可連續用 r→g→b 累加組合出完整顏色）
- **`ww`**：每顆 1 值 → cell `(0, 0, low8, high4)`（12-bit 完整，不 >>4）
- **`rgb`**：每顆 3 值 → cell `(R>>4, G>>4, B>>4, 0)`
- **`rgbw`**：每顆 4 值 → cell `(R>>4, G>>4, B>>4, W>>4)`
- **`wwww`**：每顆 1 值 → 4 個 byte 全寫 `v>>4`（一個數值代表整顆 LED）

**這就是「整合」的關鍵：索引對齊。** gen 吐的通道順序 = 群組 `sel` 展開的順序 =
big_buffer 落點順序，三者完全同步。通道消費量 = 每顆值數 × 像素數。

### 第 4.5 步：保底機制（不足 / 過長 / 空）

對齊舊專案的 `value[idx % len(value)]`（取模循環，不報錯）：

| 情況 | 行為 |
|---|---|
| 值流不足 | 通道索引取模循環重用（舊 `_handle_basic_led` 同款） |
| 值流過長 | 只取前 N 個通道值，多餘丟棄（舊 `_handle_rgb_led` 的截斷） |
| 值流空 | 全寫 0（避免 `% 0`） |

### 第 5 步：show_all 一次推硬體

```python
st_pixel.show_all()
```

`PixelStreamer` 依 `order`（apa102 → ws2812 → pca9685 → pwm → uartMotor1）逐個
controller，把 big_buffer 對應區段 `_convert` 成硬體原生格式（GRB / BGRW / W…），
一次發送。整齊表在這一刻變成真正的像素輸出。

## 3. 測試區 — 一個注意

`demo1.mode.json` 現在配 breathing（pixel_n = 10）綁 `gundam_body`（展開 180 顆）。
兩者目前不一致：**pixel_n（值數）必須覆蓋群組的通道消費量**——rgb 每顆 3 值、
rgbw 每顆 4 值、r/g/b/w/ww/wwww 每顆 1 值。這是「效果參數」與「群組大小」之間的
約束（待定案：pixel_n 由效果定死，還是由群組決定），真接線前要決定。不足時
保底會取模循環，不會報錯。
