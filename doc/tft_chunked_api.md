# TFT Chunked Write Session API

> 修改時間: 2026-06-08
> 修改範圍: `slave new/lib/TFT.py` — 基類 `TFT` 新增方法與屬性
> 未動: `bus_adapter.py`, `tft_drv.py`, 所有子類別 (ST7789/ST7735/ST7796/GC9A01/GC9D01/ILI9341/NV3030B/RM67162/SH8601)

---

## 原理

`BusAdapter.write_data_async()` 已有兩種行為語義：

- **DMA 模式**: 回傳 handle (truthy) = 排隊成功；回傳 None = 隊列滿
- **非 DMA 模式**: 永遠回傳 True (同步寫完)

TFT 層直接映射這組語義，不需額外判斷。

## 新增 API

### 初始化

```python
TFT(..., chunk_size=8192)   # chunk_size=0 表示不分塊（預設行為）
```

### 方法

| 方法 | 用途 | 對應經典 |
|---|---|---|
| `begin_write(x, y, w, h)` | 開始寫入會話 — set_window + 重置計數 | Adafruit `beginWrite()` / TFT_eSPI `startWrite()` |
| `write_pixels(data)` | 中斷寫入 — 等傳輸完成才返回 | TFT_eSPI `pushPixels()` / Adafruit `writePixels(block=True)` |
| `write_pixels_nonblock(data) → bool` | 非中斷 DMA 嘗試 — True=排隊成功, False=重試 | 傳統 `_nonblock` 後綴 |
| `end_write()` | 結束寫入會話 — flush DMA | Adafruit / TFT_eSPI `endWrite()` |

### 唯讀屬性

| 屬性 | 說明 |
|---|---|
| `.chunk_total` | 當前幀總塊數 (begin_write 後有效) |
| `.chunk_done` | 已成功傳輸的塊數 |
| `.remaining` | 剩餘塊數 |
| `.busy` | DMA 是否仍在傳輸中 |

### 螢幕差異抹平

所有螢幕差異由 `adapter.set_window()` 層處理：需要 CASET/PASET/RAMWR 的螢幕會發送，不需要的 (RGB bus) 為 no-op。TFT 層不區分螢幕類型。

## 用法範例

### 中斷模式 (blocking)

```python
lcd.begin_write(0, 0)               # set_window + RAMWR
for i in range(lcd.chunk_total):
    chunk = fetch_frame_chunk(i)    # 取得第 i 塊像素資料
    lcd.write_pixels(chunk)         # 阻塞直到傳完
lcd.end_write()                     # flush
```

### 非中斷 DMA 模式 (non-blocking)

```python
lcd.begin_write(0, 0)
while lcd.remaining > 0:
    chunk = fetch_current_chunk()
    while not lcd.write_pixels_nonblock(chunk):
        pass                        # DMA 隊列滿，原地重試
    advance_to_next_chunk()
lcd.end_write()
```

---

## 變更摘要

```
slave new/lib/TFT.py
  └── class TFT
       ├── __init__: +chunk_size=0 parameter
       ├── +begin_write(x, y, w, h)
       ├── +write_pixels(data)
       ├── +write_pixels_nonblock(data) → bool
       ├── +end_write()
       ├── +chunk_total (property)
       ├── +chunk_done (property)
       ├── +remaining (property)
       └── +busy (property)
```
