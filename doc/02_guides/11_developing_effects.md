# 開發燈效完整教學 — 從零寫一個效果並播放

> **用途**：pixel 子系統效果開發的完整參考手冊。涵蓋心智模型、三種寫法、`Effect` 介面、波形段、色彩、write 模式、框架 API、四層資料、播放模型、效能與驗證。
> **分類**：使用教學（02_guides）
> **最後更新**：2026-08-21
> **前置閱讀**：`08_pixel_subsystem.md`（四層資料 + 播放模型）
> **相關**：`slave/lib/sw/effect_core.py`（框架）、`slave/lib/sw/PixelMathMethod.py`（數學/色彩）、`slave/lib/sw/pixel_layout.py`（mapping/scatter）、`slave/pixel/effects/`（效果目錄）、`slave/tasks/pixel_task.py`（計算核）、`slave/tasks/render.py`（播放核）

---

## 0. 心智模型（先看這一段）

pixel 子系統把「效果」拆成**兩半**，各司其職：

```
effects.json（唯一真源）          effects.py（py 補充）
┌────────────────────────┐      ┌────────────────────────┐
│ id / name / params     │      │ 畫波寫不出來的演算法    │
│ program（畫波波形）     │ ─配對─│ class xxx + register() │
└────────────────────────┘      └────────────────────────┘
        │ 靠 name 對上                      │
        └──────────┬───────────────────────┘
                   ▼
        lib/sw/effect_core.py（框架：Effect 基類 + 登記表 + 波表 + 衝突檢查）
                   ▼
        make("name") → effect 實例（迭代器）
                   ▼
        PixelTask（core1 計算）→ hub → RenderTask（core0 播放）→ 硬體
```

**三條鐵律：**
1. **json 是唯一真源**：id / name / params（含 program 畫波）都在 effects.json 手寫。
2. **畫波效果不需要 py 類別**：program 寫 json，由內建 `Effect` 播放。
3. **只有畫波寫不出來的效果才寫 py**：`register(類別)`，靠 name 與 json 配對，參數仍在 json。

> 寫效果的人不用碰雙核、不用碰硬體、不用碰 hub —— 只要寫出「輸出 array('H') 幀」的東西。

---

## 1. 檔案地圖

| 檔案 | 角色 |
|---|---|
| `slave/pixel/effects/effects.json` | **唯一真源**：每個效果的 id/name/params/program |
| `slave/pixel/effects/effects.py` | 效果目錄 + py 補充類別 + `register()` + 自檢 |
| `slave/lib/sw/effect_core.py` | 框架：`Effect` 基類、登記表、波表快取、`check_conflicts()` |
| `slave/lib/sw/PixelMathMethod.py` | 數學核心：波形逼近（viper 多項式）、HSV↔RGB |
| `slave/lib/sw/pixel_layout.py` | `PixelLayout`：mapping（群組排列）→ big_buffer 落點 + scatter |
| `slave/pixel/map/*.json` | mapping（群組排列，怎麼排） |
| `slave/pixel/modes/*.json` | mode（效果 × 群組配對 + 播放參數） |
| `slave/pixel/registry.json` | 可內嵌少量 `modes` + 播放清單 + `auto_play` |
| `slave/tasks/pixel_task.py` | 計算核：初始化四層 + 大隊列播放 |
| `slave/tasks/render.py` | 播放核：固定 fps 從 hub 取幀 → 推硬體 |

---

## 2. 三種寫法（由簡到繁）

### 路 A：畫波類（首選，純 json，不用寫 py）

在 `effects.json` 加一段即可：

```json
{ "id": 5, "name": "comet", "pixel_n": 64,
  "program": [
    {"type": "math_now", "F": 1, "l_max": 3200, "l_lim": 100, "phi": 0, "end_Time": 120}
  ],
  "step": 1, "spacing": 2, "offset": 0, "speed": 1, "reverse": false }
```

框架會用內建 `Effect` 畫波播放：開機 `warm_up()` 先算好波表、viper 播放、無浮點。

### 路 B：畫波 + 自訂 frame（畫波寫不出來時，override frame）

畫波寫不出來、但想沿用空間分布時，寫 py 類別 override `frame(t)`：

```python
class my_effect(Effect):
    def frame(self, t):
        # 自訂邏輯，手動寫進 self._buf
        return self._buf
register(my_effect)
```

#### 路 B 實例：珍珠鏈（畫完波後「批量派發 + 控制間距」）

`spacing` 只能給「一片連續斜坡」（珍珠數量與間距綁死）。要「畫好一顆珍珠波形，
再獨立指定派發幾顆、間距幾格」，就 override `frame(t)` 自己寫 buffer：

```python
class pearl_chain(Effect):
    """一顆珍珠波形，派發成 N 顆、間距 D 格，順序流動。"""
    DEFAULT_PROGRAM = [   # 單顆珍珠：升起 → 保持 → 下降
        {"type": "math_now", "F": 5, "l_max": 4095, "l_lim": 0, "phi": 3071, "end_Time": 8},
        {"type": "keep",     "F": 1, "l_max": 4095, "l_lim": 0, "phi": 0,    "end_Time": 16},
        {"type": "math_now", "F": 5, "l_max": 4095, "l_lim": 0, "phi": 1023, "end_Time": 24},
    ]

    def __init__(self, name, params=None):
        super().__init__(name, params)
        params = params or {}
        self.pearl_n = int(params.get("pearl_n", 4))      # 派發幾顆
        self.pearl_gap = int(params.get("pearl_gap", 12)) # 間距（格）

    def frame(self, t):
        total = self._total
        N, D = self.pearl_n, self.pearl_gap
        phase_step = total / D   # 間距 D 格 = 一顆珍珠寬
        for i in range(self.pixel_n):
            if i < N * D:
                self._buf[i] = self._wave[int((t * self.step + i * phase_step) + self.offset) % total]
            else:
                self._buf[i] = 0
        return self._buf

register(pearl_chain)
```

**派發參數**（畫完波後才做的「派發」步驟）：

| 參數 | 意義 |
|---|---|
| `pearl_n` | 派發幾顆珍珠 |
| `pearl_gap` | 珍珠間距（格），一顆珍珠寬度 = D 格 |
| `program` | 單顆珍珠波形（時間維度） |
| `step` / `offset` | 整體流動速度 / 相位平移 |

> 完整可跑版本見 `slave/pixel/effects/effects.py` 的 `pearl_chain`。

### 路 C：完全自訂類別（不繼承 Effect）

畫波、空間分布都用不上時，寫完全不繼承 `Effect` 的類別，實作完整介面：

```python
class xxx:
    def __init__(self, name, params=None): ...
    def __next__(self): ...
    def restart(self): ...
    def seek(self, t): ...
    def release(self): ...
register(xxx)
```

---

## 3. Effect 介面完整 API

### 3.1 實例屬性（`__init__` 後可用）

| 屬性 | 型別 | 說明 |
|---|---|---|
| `name` | str | 效果名（= 類別名 / json name） |
| `id` | int | 效果 id（來自 json） |
| `program` | list | 波形段序列（json 的 program 或 DEFAULT_PROGRAM） |
| `pixel_n` | int | 輸出顆數（json `pixel_n`） |
| `step` | int | 時間步進（json `step`） |
| `spacing` | int | pixel 間距（json `spacing`，>0 產生流動） |
| `offset` | int | 空間偏移（json `offset`） |
| `speed` | int | 倍速（json `speed`，>1 重複輸出） |
| `reverse` | bool | 反向（json `reverse`） |
| `_t` | int | 內部幀計數器（迭代器推進用） |
| `_buf` | `array('H')` | 幀緩衝，長度 pixel_n，值域 0-4095 |
| `_wave` | `array('H')` | 波表（預算好的整條波） |
| `_total` | int | 波長（= program 最後一段 end_Time） |

### 3.2 方法

| 方法 | 說明 |
|---|---|
| `__init__(name, params=None)` | 建實例：讀 params、建 `_buf`、預算波表 |
| `frame(t)` | 回傳第 t 幀 `array('H')`（決定性、無狀態） |
| `__next__()` | 迭代器：`frame(_t)` 後 `_t += 1` |
| `restart()` | 重置內部時間（`_t = 0`） |
| `seek(t)` | 跳到第 t 幀（`_t = t`） |
| `release()` | off 時丟棄波表引用（波表本身在 module 快取） |

### 3.3 兩種取幀方式（迭代器 vs buffer）

```python
eff = make("eyes")

# 方式 1：迭代器 —— 逐幀推進
b0 = next(eff)   # 第 0 幀
b1 = next(eff)   # 第 1 幀（內部 _t 已 +1）

# 方式 2：buffer —— 指定幀，不推進
b5 = eff.frame(5)   # 第 5 幀（_t 不變）

# restart / seek 決定性（無狀態 frame 的基石）
eff.seek(0)
assert next(eff) == eff.frame(0)
```

---

## 4. 波形段完整說明

### 4.1 欄位

| 欄位 | 意義 |
|---|---|
| `type` | 波形段型別（見下） |
| `F` | 頻率（波形段內幾個週期） |
| `l_max` | 峰值（0-4095） |
| `l_lim` | 基底（0-4095） |
| `phi` | 相位（0-4095 ≈ 0-360°） |
| `end_Time` | 該段結束幀（**累加**） |
| `pulse` | pulse_wave / pulse 型專用門檻 |

### 4.2 六種 type

| type | 行為 | 備註 |
|---|---|---|
| `keep` | 恆定 `l_lim + (l_max - l_lim)`（即 l_max） | 平段 |
| `math_now` | 正弦：`A·sin + A + l_lim`，A=(l_max-l_lim)/2 | 主波形 |
| `square_wave_now` | 方波：正弦 ≥ 2048 時 l_max，否則 l_lim | 硬切換 |
| `pulse_wave` | 脈波：正弦 ≥ `pulse` 時 l_max，否則 l_lim | pulse=門檻 |
| `pulse` | 不經正弦，直接 `(rel+phi)%gap ≤ width` 時 l_max | 精確脈衝 |
| `starter` | 恆 0 | 開頭熄燈段 |

**段序列規則**：`end_Time` 是累加值（第 n 段 end_Time 必須 > 第 n-1 段），最後一段的 end_Time 就是波長 `_total`。

---

## 5. 空間分布參數

`frame(t)` 的相位公式（對齊舊 `wave_list_assign_next`）：

```
相位 g = (t // speed) * step + offset
第 i 顆的值 = wave[(g + i * spacing) % total]
```

| 參數 | 效果 |
|---|---|
| `step` | 時間步進：每幀相位前進多少 |
| `spacing` | pixel 間距：>0 產生流動/波浪，=0 全像素同值 |
| `offset` | 空間偏移：整條一起平移 |
| `speed` | 倍速：>1 每幀輸出重複（減速） |
| `reverse` | 反向：輸出順序反轉 |

> 手動寫 buffer（路 B）時，你可以在 `frame(t)` 裡用 `self._wave` / `self._total` /
> `self.step` / `self.spacing` / `self.offset` / `self.speed` / `self.reverse`，
> 對照舊 `main.py` 的 `_tempbuf` / `_wave_history` / `_step_counter`。

---

## 6. 色彩 HSV↔RGB（`lib/sw/PixelMathMethod.py`）

全整數、無浮點、viper bulk 批次（一次處理整條 buffer）。

### 6.1 單值函式

| 函式 | 位深 | 回傳 |
|---|---|---|
| `hsv_to_rgb8(h, s, v)` | h 0-360, s/v 0-255 | (R, G, B) 0-255 |
| `rgb_to_hsv8(r, g, b)` | r/g/b 0-255 | (h, s, v) |
| `hsv_to_rgb12(h, s, v)` | h 0-360, s/v 0-4095 | (R, G, B) 0-4095 |
| `rgb_to_hsv12(r, g, b)` | r/g/b 0-4095 | (h, s, v) |

### 6.2 bulk 函式（viper，效能優先）

| 函式 | 輸入 | 輸出 |
|---|---|---|
| `hsv_to_rgb8_buf(h,s,v,out,n)` | h/s/v 各 `array('H')` | out `bytearray`（3B/px） |
| `rgb_to_hsv8_buf(rgb,h,s,v,n)` | rgb `bytearray`（3B/px） | h/s/v 各 `array('H')` |
| `hsv_to_rgb12_buf(h,s,v,out,n)` | h/s/v 各 `array('H')` | out `array('H')`（3 值/px） |
| `rgb_to_hsv12_buf(rgb,h,s,v,n)` | rgb `array('H')`（3 值/px） | h/s/v 各 `array('H')` |

> ⚠️ **暫時包裝**：色彩接口本輪只提供函式，尚未接進 scatter/effect/controller。
> 畫波效果直接輸出亮度值（灰階 R=G=B）；彩色效果未來再接。

---

## 7. write 模式（scatter 的消費形狀）

決定效果輸出值流的長度與每顆的通道語義：

| write | 每顆值數 | 輸出長度（pixel_n=64） | 寫入 |
|---|---|---|---|
| `r` / `g` / `b` / `w` | 1 | 64 | 只寫對應通道，其餘不修改（可累加組合） |
| `ww` | 1 | 64 | 12-bit 完整（byte2 低8 + byte3 高4） |
| `rgb` | 3 | 192 | R,G,B 依序，全部 >>4 |
| `rgbw` | 4 | 256 | R,G,B,W 依序，全部 >>4 |
| `wwww` | 1 | 64 | 1 值代表整顆（4 byte 同值） |

> **別搞錯長度**：scatter 的 `rgb` 是「3 值/顆 依序」——`[R0,G0,B0, R1,G1,B1, ...]`。
> 輸出長度 = pixel_n × 每顆值數。值流不足 → 取模循環；過長 → 多餘丟棄。

### 用 `write:"w"` 驅動馬達（UART-412）

馬達 controller（`UartMotor`，mapping type `uartMotor1`）從 big_buffer 的 **W 通道**讀速度 byte（8-bit，0-255）：

| W 值 | 馬達行為（UART-412 `updateMotor`） |
|---|---|
| `0x80` (128) | **死區停**（兩腳 PWM 都 0）——也是停止/歸零的中性值 |
| `0x01..0x7F` | 正轉，越接近 0 越快 |
| `0x81..0xFF` | 反轉，越接近 0xFF 越快 |

效果輸出（0-4095）→ `>>4` → W 通道。**要讓馬達停，效果輸出 2048（中點）**；輸出 0 會被歸零保護映射成死區（不會全速暴走）。

```json
{ "group": "matrix.motors", "effect": "wave", "write": "w" }
```

> 廣播模式受 UART-412 `MAX_DEVICE=32` 限制，address > 32 時 `UartMotor.show_all()` 自動改用單台 frame 串接（`ff addr value fe` × N）一次過發射。

---

## 8. 框架 API 完整清單（`lib/sw/effect_core.py`）

### 8.1 登記 / 查詢

| 函式 | 說明 |
|---|---|
| `register(cls)` | 登記 py 補充類別（name = cls.__name__），不自動配 id/name |
| `load_json(effects_list)` | 載入 effects.json，按 name 把 py 類別與 json 配對 |
| `resolve(ref)` | id(int) 或 name(str) → 效果類別（畫波效果回內建 `Effect`） |
| `get_params(ref)` | id 或 name → 效果參數 dict（json） |
| `make(ref)` | id 或 name → 建效果實例（每次播放重建一份） |
| `dump()` | 回傳 name → id 對照（除錯用） |

### 8.2 波表

| 函式 | 說明 |
|---|---|
| `warm_up()` | 開機預算所有畫波效果的波表（掩蓋首次播放成本），回傳數量 |
| `clear_wave_cache()` | 清空波表快取（effects.json 重載後重新預算） |

### 8.3 衝突檢查

| 函式 | 說明 |
|---|---|
| `check_conflicts()` | 回傳 id/name/配對衝突警告行（無衝突 → []） |

啟動時 `PixelTask._init_effects` 呼叫它，把警告列印出來（對齊 boot GPIO 檢查）：

| 警告 | 情境 |
|---|---|
| `EFFECT ID CONFLICT` | 兩個 name 用同一 id |
| `EFFECT NAME CONFLICT` | json 內 / py 內 name 重複 |
| `EFFECT 無 json` | py 有類別但 json 沒 entry |
| `EFFECT 缺 program` | 畫波效果（無 py 類別）但 json 沒 program |
| `EFFECT 缺參數` | 缺 pixel_n/step/spacing/offset/speed/reverse 任一 |

---

## 9. 四層資料設定

寫好效果後，要讓它播放，需設定 mapping / modes / registry：

### 9.1 effects.json — 效果定義（唯一真源）

```json
{ "id": 3, "name": "wave", "pixel_n": 64,
  "program": [ {"type": "math_now", "F": 1, "l_max": 3200, "l_lim": 100, "phi": 0, "end_Time": 120} ],
  "step": 1, "spacing": 2, "offset": 0, "speed": 1, "reverse": false }
```

- id 全 json 唯一、name 手寫；畫波寫 program，補充類別讓 name 對應 py 類別名。

### 9.2 map/*.json — mapping（群組排列）

```json
{ "id": 3, "name": "matrix",
  "groups": [ { "id": 1, "name": "full", "sel": [ {"type": "ws2812", "sel": ":"} ] } ] }
```

- `sel` 選擇器：`7`（單顆）、`"0:14"`（範圍，end 不含）、`":"`（全選）、`"15:10:-1"`（反序）。
- mapping id / group id 全域唯一。

### 9.3 modes/*.json — 模式（效果 × 群組配對）

```json
{ "id": 1, "name": "demo_eyes", "index": 1, "play_count": -1, "play_interval": 1,
  "mapping": "matrix",
  "map": [ { "group": "matrix.full", "effect": "eyes", "write": "rgb" } ] }
```

- `group`：`mapping.group` 複合引用。`play_count`：-1 常駐、1..N 前 N 輪、0 跳過。
- `play_interval`：每隔 N 輪一次。

### 9.4 registry.json — 可內嵌 mode + 播放清單

```json
{ "version": 1, "auto_play": true, "list": ["demo_eyes"] }
```

---

## 10. 播放模型（雙核分工）

```
core1（計算核）PixelTask                  core0（播放核）RenderTask
┌─────────────────────────────┐          ┌─────────────────────────────┐
│ 效果計算 → scatter 進 hub    │  ──幀──▶  │ 固定 fps 節奏取幀 → show     │
│ (pixel_stream hub)          │          │ 推硬體（WS2812/APA102/…）    │
└─────────────────────────────┘          └─────────────────────────────┘
```

- 計算核全力算幀，hub 滿就 drop（不阻塞）；播放核固定 `System.frame_interval_ms`（預設 20ms）取幀。
- 指令介面（bus.shared）：`pixel_play` / `pixel_stop` / `pixel_pause`。

---

## 11. 效能要點

| 問題 | 解法 |
|---|---|
| 一卡一卡 | 雙核分工（已做） |
| 播放積壓 | hub 滿 drop（已做） |
| 效果初始化卡頓 | 波表 module 快取，開機 warm_up() 預算 |
| scatter 慢 | 用 `write: "rgb"` 走 viper（loop 在 viper 內） |
| 值域錯 | 全程整數、clamp 0-4095 |

---

## 12. 驗證流程

### PC（slave/ 目錄）

```bash
python lib/sw/pixel_layout.py        # mapping/scatter 自檢
python pixel/effects/effects.py      # 效果登記 + 輸出自檢
python -B test/pixel/test_pixel_math.py    # 波形 + Effect 單元測試
python -B test/pixel/test_pixel_color.py   # 色彩單元測試
```

### 裝置

1. 上傳效果檔 + 四層設定（mpremote cp）。
2. 硬體重置（RESET 鍵）。
3. 看 boot log：`[Pixel] effects: N 個`、`[Pixel] ▶ show 開始`。

---

## 13. 常見踩坑

1. **mapping id 衝突** → 該 mapping 被跳過（`MAPPING ID CONFLICT`）。
2. **effect id/name/配對衝突** → 不 raise，啟動列印 `EFFECT ID CONFLICT` / `EFFECT 無 json` / `EFFECT 缺 program` / `EFFECT 缺參數` 警告。
3. **效果輸出長度錯** → scatter 取模循環，畫面錯亂。長度 = pixel_n × 每顆值數。
4. **thread 內重計算崩潰** → 波表 module 級快取，import 時預算（主線程）。
5. **值域超過 4095** → 畫面爆亮/閃爍。全程整數 + clamp。

---

## 相關文件

- `08_pixel_subsystem.md` — pixel 四層資料 + 播放模型
- `slave/lib/sw/effect_core.py` — 框架：Effect 基類 / 登記表 / 波表快取 / `check_conflicts()`
- `slave/lib/sw/PixelMathMethod.py` — 數學核心（波形 + 色彩）
- `slave/lib/sw/pixel_layout.py` — mapping / scatter
- `slave/pixel/effects/effects.py` — 範例框架（畫波效果目錄 + py 補充範例）
- `slave/tasks/render.py` — 播放核（fps 節奏）
- `slave/tasks/pixel_task.py` — 計算核（hub 寫入）
- `03_notes/07_pixel_test_results.md` — 測試結果與未來方向
