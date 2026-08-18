# pixel 子系統 — README

> pixel 子系統把「效果 / 群組排列 / 模式配對 / 播放清單」拆成四層，各自定義，
> 由 `PixelTask`（`slave/tasks/pixel_task.py`）在開機時依序初始化並執行大隊列自動播放。

## 1. 四層資料

| 層 | 內容 | 檔案 | bus key |
|---|---|---|---|
| 效果 | 波形生成器（怎麼動） | `pixel/effects/`（effects.json + effects.py） | `pixel_gens` |
| mapping | 群組排列（怎麼排） | `pixel/map/*.json`（每套一個檔，自帶 id/name） | `pixel_layout` |
| modes | 效果 × 群組配對 + 播放參數 | `pixel/modes/*.json` | `pixel_maps` |
| 播放清單 | 播什麼、開不開自動播放 | `pixel/registry.json` | `pixel_show` |

## 2. 資料模型

### 2.1 effects/ — 效果

`pixel/effects/effects.json`（JSON 形式，id + params）+ `pixel/effects/effects.py`
（PY 形式，效果類別）。兩者共用登記表：**名稱撞車時程式（py）優先**，json 只補
id / params。

- 效果 = `Effect` 類別（有 id/name、可 `restart()`、可 `seek(t)`），每次播放重建實例。
- 數學核心在 `slave/lib/PixelMathMethod.py`：**`@micropython.viper` 整數多項式逼近**
  （拋物線基底 + `922*(y²-y)>>12` 修正），**無查表、無浮點、值域固定 12-bit 0-4095**。
- 空間分布：`frame(t)` 把時間波攤到 pixel_n 顆 → `pattern_value_at(program, 相位)`，
  相位 = `(t // speed) * step + i * spacing + offset`（對齊舊 `wave_list_assign_next`）。
- 吐 `array('H')`（0-4095），供 scatter 的 viper 用 ptr16 直接讀。

波形段 `type`：`keep` / `math_now` / `square_wave_now` / `pulse_wave` / `pulse` / `starter`。

| JSON 欄位 | 說明 |
|---|---|
| `pixel_n` | 輸出位數 |
| `program` | 波形段序列（type / F / l_max / l_lim / phi / end_Time / pulse） |
| `step` | 時間步進（舊 step） |
| `spacing` | pixel 間距（空間分布） |
| `offset` | 空間偏移 |
| `speed` | 倍速 |
| `reverse` | 反向 |

#### 寫效果（最高優化）

- **路 A 波形類（首選）**：`class xxx(Effect)` + 定義 `DEFAULT_PROGRAM`。自動拿到
  波表預算（開機 `warm_up()` 先算好）+ viper `_fill_fwd` 播放，熱路徑只做 index 讀取。
  範例：`wave` / `eyes` / `breathing`。
- **路 B 自訂/狀態機類**：`class xxx(Effect)` + override `frame(t)`。保持整數、無浮點，
  能 bulk 就 bulk、能 viper 就 viper；輸出 `array('H')`、長度 `pixel_n`、值域 0-4095。

#### 色彩接口（bulk，暫時包裝）

`slave/lib/PixelMathMethod.py` 提供 HSV↔RGB（全整數、無浮點、viper bulk 批次，一次處理整條 buffer）：
- 8-bit（0-255）：`hsv_to_rgb8_buf` / `rgb_to_hsv8_buf`（RGB 為 bytearray 3B/px）
- 12-bit（0-4095）：`hsv_to_rgb12_buf` / `rgb_to_hsv12_buf`（RGB 為 array('H') 3 值/px）
- 單值便利函式：`hsv_to_rgb8` / `rgb_to_hsv8` / `hsv_to_rgb12` / `rgb_to_hsv12`

已修掉舊專案的 bug（RGB 順序、飽和度、色相 offset）。**本輪只提供接口，未接
scatter/effect/controller**——未來彩色 effect 再接；controller 整合遲啲處理。

### 2.2 map/ — mapping（群組排列）

每套 mapping 一個檔，自帶 id/name；**不寫硬體 order/counts**（硬體真值一律從
播放器 `PixelStreamer.controllers` 推導，統一 key 見下）。

```json
{
  "id": 1,
  "name": "gundam",
  "groups": [
    { "id": 1, "name": "gundam_body", "sel": [
        {"type": "pwm",    "sel": "10:15"},
        {"type": "ws2812", "sel": "40:200"},
        {"type": "ws2812", "sel": ":10"},
        {"type": "pwm",    "sel": "15:10:-1"}
    ]},
    { "id": 2, "name": "motors", "sel": [{"type": "uartMotor1", "sel": ":"}] }
  ]
}
```

- `sel` 是「有序的段列表」，段依書寫次序拼接 = 像素次序，可交叉型別、反序、重疊。
- 選擇器：`7`（單顆）、`"0:14"`（範圍，end 不含）、`":"`（全選）、`"15:10:-1"`（反序）。
- **群組 id/name 在同 mapping 內必須唯一**，重複 → 該 mapping 載入失敗（warn + 跳過）。
- 引用硬體不存在的型別（如 pwm / uartMotor1 未接播放器）→ 該段為空（載入時 warn），不報錯。

**統一 key（硬體型別 → registry 型別名）**，在 `pixel_task.py` 的 `TYPE_MAP`：

| 播放器 `pixel_type` | registry key |
|---|---|
| `WS2812` | `ws2812` |
| `APA102` | `apa102` |
| `i2c_pixel` | `pca9685` |

### 2.3 modes/ — 模式（效果 × 群組配對 + 播放參數）

```json
{
  "id": 1,
  "name": "demo1",
  "index": 1,            // 大隊列排序備援：先比 index 再比 id，越少越前（list 順序為主）
  "play_count": 1,       // 0=永遠跳過; 1..N=只在前 N 輪出現; -1=常駐每輪
  "play_interval": 1,    // 每隔 N 輪出現一次（1=每輪）
  "mapping": "gundam",   // 選用：預設 mapping（id 或 name）；可省略
  "map": [
    { "group": "1.1", "effect": 1, "write": "rgb" },
    { "group": "motors", "effect": "breathing", "write": "w" }
  ]
}
```

- **group 複合引用**：`mapping.group`，兩邊各可用 id 或 name（`gundam.motors` /
  `1.motors` / `gundam.1` / `1.1`）；無點號時以頂層 `mapping` 為預設。
- effect 同用 id 或 name 引用。
- **同 mode 內 group 引用不得重複**，重複 → warn + 只保留第一項。
- 播放參數單位全用 **frame**（不用 ms，節奏由播放端控制）。

`write` 白名單：`r` / `g` / `b` / `w` / `ww` / `rgb` / `rgbw` / `wwww`。

### 2.4 registry.json — 播放清單 + 自動播放

```json
{
  "version": 1,
  "auto_play": true,
  "list": ["demo1", "demo2"]
}
```

- `list`：mode 名稱（或 id）依序播放 = 大隊列；順序即播放順序，播完一輪 → 再從頭循環。
- `auto_play=false`（或檔案不存在）→ 不自動播放，等指令層下 `pixel_play`。

## 3. 播放模型（大隊列 show）

- show = registry.list 的 mode 序列，循環播放；每播完一輪 `pass+1`。
- mode 每次播放 = 用 effects.json params **重建 generator**（fresh gen），播到耗盡（StopIteration）。
  想播久一點 → 在效果內延長（如 `end_Time`）。
- 每輪依播放參數決定該 mode 是否出現：
  - `play_count==0` → 永遠跳過
  - `play_count>0` 且 `pass > play_count` → 這輪起消失（開頭段）
  - `(pass-1) % play_interval != 0` → 這輪跳過（週期性）
  - 其餘（含 `play_count=-1` 常駐）→ 播放
- 例：`[intro(count=1), A(-1), B(-1)]` → 第 1 輪 intro+A+B，第 2 輪起 A+B 循環。
- 例：`ticker(count=1, interval=5)` → 第 1、6、11…輪才出現。

## 4. 整合流程（一幀怎麼跑）

```
gen（效果生成器，fresh）──▶ array('H') 緩衝（0-4095）
        │ 依 mode 配對（mapping.group + write）
PixelLayout.scatter（亂序選擇 → 整齊表落點，viper）
        │
        ▼
big_buffer（RGBW 幀，bytearray）──▶ st_pixel.show_all()（一次推硬體）
```

- 幀格式：每顆控制單元 4 bytes（R,G,B,W），拼接順序 = 播放器 controllers 順序。
- `r/g/b/w`：每顆 1 值，只寫對應通道，其餘「不修改」（可累加組合）。
- `ww`：12-bit 完整（byte2 低 8 + byte3 高 4）；`wwww`：1 值代表整顆 pixel。
- `rgb`：3 值/顆；`rgbw`：4 值/顆；全部 >>4。
- 保底：值流不足 → 取模循環；過長 → 多餘丟棄；空 → 全寫 0。

## 5. PixelTask 初始化順序

```
on_start
├─ 1. 硬體：確保 st_pixel（無 → driver.pixel_drv.init_pixel()；config 全 disable → 空播放器）
├─ 2. effects：py register + 載 effects.json → bus.shared["pixel_gens"]
├─ 3. mapping：從播放器推導 order/counts + 載 map/*.json → bus.shared["pixel_layout"]
├─ 4. modes：載 modes/*.json（解析複合 group 引用）→ bus.shared["pixel_maps"]
└─ 5. registry：載 registry.json → bus.shared["pixel_show"]；auto_play → 啟動 show
```

指令介面（bus.shared，指令層寫入）：
- `pixel_play` → 開始/重啟 show
- `pixel_stop` → 停止（熄燈）
- `pixel_pause` → 暫停 / 恢復

## 6. 自檢

```bash
# 於 slave/ 目錄執行
python3 lib/pixel_layout.py      # 多 mapping + 複合引用 + 重複檢查 + scatter 保底
python3 pixel/effects/effects.py # 效果登記 + 生成器輸出（array('H')）
```

viper 速度只能在裝置上測（PC 沒有 micropython）。
