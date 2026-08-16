# pixel 效果層（第二層）

> 介紹區：效果有哪兩種形式、id/name 怎麼定、防撞車規則。
> 測試區：§6 的自檢。

## 1. 介紹區 — 效果的形式

效果集中存放在 `pixel/effects/` 兩個檔，**每個效果都有自己的 id + name**：

- **`effects.json`**（JSON 形式）：效果列表 `effects[]`，每個效果登記 id / name / 參數。
- **`effects.py`**（PY 形式）：效果生成器集中在此，**名稱 = 函數名稱**（`fn.__name__`）。

兩者共用同一張登記表，map（模式）配對時用 id 或 name 引用。

## 2. 介紹區 — 名稱與 id 怎麼決定

- **py 的效果名稱直接用函數名稱**：函數叫 `breathing`，效果名就是 `breathing`。
- **id 從 1 開始**，`0` 保留為「未指定 / 自動配發」哨兵值：
  - json 有給 id → 用 json 的 id。
  - 純 py（json 沒這個效果）→ 自動配發下一個可用 id。

## 3. 介紹區 — 兩邊防撞車（程式優先）

json 與 py 同名時，**程式（py）優先**：

- 生成器函數永遠由 py 提供。
- json 只提供 id / params。
- 載入順序無關：json 先載或 py 先登記，結果一致。

撞車規則：

| 情況 | 行為 |
|---|---|
| json 內同 name 重複 | raise（NAME CONFLICT） |
| json 與 py 同 name | 程式優先，保留 json 的 id / params |
| 同 id 被不同 name 使用 | raise（ID CONFLICT） |

## 4. 介紹區 — 檔案

### 4.1 effects.json

```json
{
  "version": 1,
  "effects": [
    { "id": 1, "name": "breathing", "pixel_n": 10, "program": [ ... ], "speed": 3, "reverse": false }
  ]
}
```

### 4.2 effects.py

```python
def breathing(pixel_n, program=None, speed=1, reverse=False, **params):
    ...

register(breathing)   # name = "breathing"
```

## 5. 介紹區 — 參數（JSON 與程式一一對應）

| JSON 欄位 | 程式參數 | 說明 |
|---|---|---|
| `pixel_n` | `pixel_n` | 輸出位數 [1]~[n] |
| `program` | `program` | 波形序列 |
| `speed` | `speed` | 倍速 |
| `reverse` | `reverse` | 反向 |

無 `engine` 欄位、無「逐顆 / 整批」等模式之分：只有一個生成器，輸出位數由
`pixel_n` 決定。生成器吐 **`array('H')` 緩衝**（0-4095），供 scatter 的 viper
用 ptr16 直接讀，零分配。

## 6. 測試區 — 自檢

```bash
# 於 slave/ 目錄執行
python3 pixel/effects/effects.py
```

`_shape()` 只示範 `math_now`（正弦），其餘 func 待接 `LEDMathMethod.is_math_pattern_next`。
