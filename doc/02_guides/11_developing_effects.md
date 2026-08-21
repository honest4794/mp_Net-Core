# 開發燈效指南 — 從零寫一個效果並播放

> **用途**：在 pixel 子系統寫新燈效的完整教學。涵蓋效果介面、三種寫法、mapping / modes / registry 設定、雙核播放架構、效能與驗證。
> **分類**：使用教學（02_guides）
> **最後更新**：2026-08-21
> **前置閱讀**：`08_pixel_subsystem.md`（四層資料 + 播放模型）
> **相關**：`slave/pixel/effects/`（效果目錄）、`slave/tasks/pixel_task.py`（計算核）、`slave/tasks/render.py`（播放核）

---

## 1. 先懂架構：雙核播放

pixel 子系統用**雙核心分工**解決「一卡一卡」（效果計算與硬體輸出互相阻塞）：

```
core1（計算核）PixelTask                  core0（播放核）RenderTask
┌─────────────────────────────┐          ┌─────────────────────────────┐
│ 效果計算 → scatter 進 hub    │  ──幀──▶  │ 固定 fps 節奏取幀 → show     │
│ (pixel_stream hub)          │          │ 推硬體（WS2812/APA102/…）    │
└─────────────────────────────┘          └─────────────────────────────┘
        ▲ 計算多快就多快                        ▲ 節奏固定，不受計算影響
        │ hub 滿就 drop 幀（不阻塞）            │ 沒幀就跳過（不重播）
```

- **計算核（core1）**：`PixelTask.loop()` 全力算幀，`_tick_player` 把一幀 scatter 進 `pixel_stream` hub 的 slot 後 `commit()`。hub 滿（播放核來不及消化）→ 這幀直接 drop，**不阻塞計算**。
- **播放核（core0）**：`RenderTask.loop()`（`slave/tasks/render.py`，專案既有）用固定節奏（`System.local_fps`，預設 50 = 20ms）從 hub `read_into(big_buffer)` → `show_all()`。hub 空 → 這輪跳過。
- **幀率設定**：`config.json` → `System.local_fps`（預設 50）。播放核間隔 = `1000 // fps` 毫秒。
- **與外部串流的關係**：`pixel_stream` hub 同時供外部串流（PC 0x3003 / 檔案播放）與本地效果使用；`is_streaming` 旗標控制播放核要不要取幀。PixelTask `_start()`/`_stop()` 會設定它。

> **寫效果的人不用碰雙核**——只要寫 Effect 類別（輸出 array('H') 幀），PixelTask 自動計算、RenderTask 自動播放。

---

## 2. 效果介面：Effect 類別

所有效果都是一個**類別**，實作同一套介面，供播放端 `next(effect)` 逐幀取：

```python
class 我的效果:
    def __init__(self, name, params=None):
        self.pixel_n = 64          # 輸出顆數
        self._buf = array('H', [0] * (self.pixel_n * 3))  # 幀緩衝

    def __next__(self):
        # 回傳下一幀：array('H')，值域 0-4095
        # 長度 = 依 write 模式決定（見 §5）
        b = self.frame(self._t)
        self._t += 1
        return b

    def restart(self): ...        # 重播：重置狀態
    def seek(self, t): ...        # 跳幀
    def release(self): ...        # 停止時釋放資源
```

**三條硬規則**：
1. **全程整數、無浮點**（熱路徑）。`math.sin` 只能在「建構時預算波表」用一次，播放期零重算。
2. **值域固定 12-bit（0-4095）**。
3. **輸出必須是 `array('H')`**（viper scatter 用 `ptr16` 直接讀，list 不行）。

---

## 3. 三種寫法（由簡到繁）

### 路 A：波形類（首選，自動最高優化）

只要定義 `DEFAULT_PROGRAM`（波形段序列），自動拿到波表預算 + viper 播放：

```python
class wave(Effect):
    """波浪：單條 math_now 波 + spacing 逐顆相位偏移（流動感）。"""
    DEFAULT_PROGRAM = [
        {"type": "math_now", "F": 1, "l_max": 3200, "l_lim": 100, "phi": 0, "end_Time": 120},
    ]

register(wave)   # 效果 name = 類別名 "wave"
```

波形段欄位：

| 欄位 | 意義 |
|---|---|
| `type` | `keep`（恆定 l_lim+l_range）/ `math_now`（正弦）/ `square_wave_now`（方波）/ `pulse_wave` / `pulse` / `starter`（全 0） |
| `F` | 頻率（波形段內幾個週期） |
| `l_max` | 峰值（0-4095） |
| `l_lim` | 基底（0-4095） |
| `phi` | 相位（0-4095 ≈ 0-360°） |
| `end_Time` | 該段結束幀（累加） |

**空間分布**由 json params 控制：`step`（時間步進）、`spacing`（每顆相位間距，>0 產生流動）、`offset`、`speed`（值重複）、`reverse`。

### 路 B：自訂 / 狀態機類（override frame）

需要自訂邏輯（狀態機、隨機、疊加）時 override `frame(t)`：

```python
class 我的效果(Effect):
    def frame(self, t):
        # 自訂邏輯，寫進 self._buf
        # 保持整數、能 bulk 就 bulk、能 viper 就 viper
        return self._buf
register(我的效果)
```

### 路 C：獨立模組類（完全自訂，不繼承 Effect）

效果邏輯複雜、想獨立成檔時，放 `slave/pixel/effects/xxx_effect.py`，實作完整介面（`__next__` / `restart` / `seek` / `release`），再在 `effects.py` 檔尾 import + register：

```python
# slave/pixel/effects/xxx_effect.py
class xxx:
    def __init__(self, name, params=None): ...
    def __next__(self): ...
    def restart(self): ...
    def seek(self, t): ...
    def release(self): ...

# slave/pixel/effects/effects.py 檔尾
try:
    from pixel.effects.xxx_effect import xxx as _xxx_cls
    register(_xxx_cls)
except Exception as _e:
    print("[effects] xxx 載入失敗: {}".format(_e))
```

> **注意（踩坑）**：PixelTask 在 **core1（_thread）** 實例化效果。若效果 `__init__` 做重計算（如 `math.sin` 建波表），**在 thread 內執行有崩潰風險**。解法：波表用 **module 級快取**，在 import 時（主線程）算好，`__init__` 只讀快取。範例見 `diffusion_effect.py` 的 `_get_wave()`。

---

## 4. 色彩：灰階與 RGB

- **灰階**（舊專案 diffusion 那類）：R=G=B=亮度值。效果輸出 `array('H')` 192 個值（64 顆 × 3），`write: "rgb"`。
- **單通道**：`write: "w"` 時輸出 64 個值（每顆 1 值），只寫 W 通道。
- **HSV→RGB**：`slave/lib/sw/PixelMathMethod.py` 提供 `hsv_to_rgb8_buf` / `hsv_to_rgb12_buf`（bulk 批次，全整數）。效果內可先算 HSV 再轉 RGB。

---

## 5. write 模式決定輸出長度

| write | 每顆值數 | 效果輸出長度（pixel_n=64） | 寫入 |
|---|---|---|---|
| `r` / `g` / `b` / `w` | 1 | 64 | 只寫對應通道，其餘不修改 |
| `ww` | 1 | 64 | 12-bit 完整（byte2 低8 + byte3 高4） |
| `rgb` | 3 | 192 | R,G,B 依序，全部 >>4 |
| `rgbw` | 4 | 256 | R,G,B,W 依序，全部 >>4 |
| `wwww` | 1 | 64 | 1 值代表整顆（4 byte 同值） |

> **別搞錯長度**：scatter 的 `rgb` 是「3 值/顆 依序」——效果輸出 `[R0,G0,B0, R1,G1,B1, ...]`。輸出長度 = pixel_n × 每顆值數。

---

## 6. 四層資料設定

寫好效果類別後，要讓它被播放，需設定三層資料（mapping / modes / registry）：

### 6.1 effects.json — 效果參數

`slave/pixel/effects/effects.json` 的 `effects[]` 加一段（id 唯一、name 對應類別名）：

```json
{
  "id": 4,
  "name": "diffusion",
  "pixel_n": 64,
  "program": [],
  "step": 1, "spacing": 0, "offset": 0, "speed": 1, "reverse": false
}
```

路 A/C 的效果：`params` 由 json 提供（含 `program`）。路 B 純 py 效果可省略 json（自動配 id）。

### 6.2 map/ — mapping（群組排列）

`slave/pixel/map/*.json`，每套一個檔，**id 必須全域唯一**（與其他 mapping 不衝突！）：

```json
{
  "version": 1,
  "id": 3,
  "name": "matrix",
  "groups": [
    { "id": 1, "name": "full", "sel": [ {"type": "ws2812", "sel": ":"} ] }
  ]
}
```

- `sel` 選擇器：`7`（單顆）、`"0:14"`（範圍，end 不含）、`":"`（全選）、`"15:10:-1"`（反序）。
- **mapping id 衝突會導致該 mapping 被跳過**（`MAPPING ID CONFLICT`）→ mode 引用它的 group 會失敗。新 mapping 記得用沒用過的 id。

### 6.3 modes/ — 模式（效果 × 群組配對）

`slave/pixel/modes/*.json`：

```json
{
  "version": 1,
  "id": 2,
  "name": "diffusion",
  "index": 2,
  "play_count": -1,
  "play_interval": 1,
  "mapping": "matrix",
  "map": [
    { "group": "matrix.full", "effect": "diffusion", "write": "rgb" }
  ]
}
```

- `group`：`mapping.group` 複合引用（`matrix.full`）。效果與群組各可用 id 或 name。
- `play_count`：`-1` = 常駐每輪；`1..N` = 只在前 N 輪出現；`0` = 永遠跳過。
- `play_interval`：每隔 N 輪出現一次（1 = 每輪）。
- 同 mode 內 group 引用不得重複。

### 6.4 registry.json — 播放清單

```json
{
  "version": 1,
  "auto_play": true,
  "list": ["diffusion"]
}
```

`list` 依序播放 = 大隊列，播完一輪循環。

---

## 7. 效能要點（為什麼會卡）

| 問題 | 原因 | 解法 |
|---|---|---|
| 一卡一卡 | 計算 + 輸出同核互相阻塞 | 雙核分工（本架構已做） |
| 播放追趕積壓 | 計算核產出遠快於播放 | hub 滿就 drop（已做）；播放核沒幀就跳過，不積壓 |
| 效果初始化卡頓 | `__init__` 重計算（math.sin 波表） | module 級快取，import 時預算 |
| scatter 慢 | Python 迴圈逐顆 | 用 `write: "rgb"` 走 viper `_scatter_rgb`（loop 在 viper 內） |
| 值域錯 | 浮點/超範圍 | 全程整數、clamp 0-4095 |

**測幀率**：播放核 `on_start` 會印 `[RenderTask] Engine Online | {fps} FPS`。若實際卡頓，檢查 log 有沒有 `[Pixel]` 錯誤或 hub drop 頻率。

---

## 8. 實例：移植舊專案 diffusion 效果

舊 `temp/1/main.py` 直接進入的 `run_Pattern(diffusion_init)`（灰階擴散）移植步驟：

1. **分析舊 generator**：`stepping_wave_next(2, eyes_start1, step=40)` + `stepping_engine_list_next(8, p, pulse_list)` + `overlay(16, p, pulse_list, overlay=5, gap=10)`，合成 64 顆。
2. **寫 diffusion_effect.py**（路 C）：`_build_wave()` 預算波表（module 快取），`_StepEngine` 精確模擬舊 stepping_engine 的 pulse 狀態機，`frame(t)` 合成三引擎到 64 顆 RGB。
3. **設定**：effects.json id=4、map/matrix.json（id=3, ws2812 全選）、modes/diffusion.json（`matrix.full` + `rgb`）、registry.json（auto_play: ["diffusion"]）。
4. **驗證**：PC 跑 `pixel/effects/effects.py` 自檢 + 手動 `effects.make('diffusion')` 看 frame 輸出；裝置上看 boot log `[Pixel] ▶ show 開始`。

完整程式碼見 `slave/pixel/effects/diffusion_effect.py`。

---

## 9. 驗證流程

### PC（slave/ 目錄）

```bash
python lib/sw/pixel_layout.py        # mapping/scatter 自檢
python pixel/effects/effects.py      # 效果登記 + 輸出自檢
```

### 裝置

1. 上傳效果檔 + 四層設定（mpremote cp）。
2. 硬體重置（RESET 鍵）。
3. 看 boot log：`[Pixel] effects: N 個`、`[Pixel] ▶ show 開始`。
4. 打斷後手動驗證：

```python
from pixel.effects import effects
eff = effects.make("你的效果")
b = next(eff)
lit = sum(1 for i in range(eff.pixel_n) if b[i*3] or b[i*3+1] or b[i*3+2])
print("lit", lit, "/", eff.pixel_n)
```

---

## 10. 常見踩坑

1. **mapping id 衝突** → mapping 被跳過 → mode 引用 group 失敗（warn `MAPPING ID CONFLICT`）。檢查所有 map/*.json 的 id 唯一。
2. **效果輸出長度錯** → scatter 取模循環，畫面看起來錯亂。確認長度 = pixel_n × 每顆值數。
3. **thread 內重計算崩潰** → 波表 module 級快取，import 時預算。
4. **值域超過 4095** → 畫面爆亮/閃爍。全程整數 + clamp。
5. **板子 USB-CDC 掉線** → 軟重置（mpremote exec）會 soft reset + 可能崩潰在 App()。硬體重置後系統正常；驗證用「打斷後查」而非反覆 exec。

---

## 相關文件

- `08_pixel_subsystem.md` — pixel 四層資料 + 播放模型
- `slave/tasks/render.py` — 播放核實作（fps 節奏）
- `slave/tasks/pixel_task.py` — 計算核實作（hub 寫入）
- `slave/pixel/effects/diffusion_effect.py` — 路 C 完整範例
- `03_notes/07_pixel_test_results.md` — 測試結果與未來方向
