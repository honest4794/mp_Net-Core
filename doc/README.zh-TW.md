## mp_heap_caps

這是一個 MicroPython 的 User C Module，用來把 ESP-IDF 的 `heap_caps_*` 記憶體配置/查詢能力包成 Python 介面。

- MicroPython 模組名稱：`heap_caps`
- 典型用途：SPI 螢幕 DMA buffer、PSRAM（SPIRAM）大緩衝區、依照能力（caps）查詢目前剩餘記憶體。

## 功能

- 依照 `caps`（能力 bitmask）配置/釋放/重配記憶體
-（ESP32）支援 aligned allocation
-（ESP32）查詢指定 caps 的 free/total/largest
- 將常用 `MALLOC_CAP_*` 常數輸出到 Python（例如 `CAP_DMA`、`CAP_SPIRAM`）

## API

### 配置與釋放

所有配置函式成功會回傳可寫的 `memoryview`，失敗回傳 `None`。

- `heap_caps.malloc(size, caps) -> memoryview | None`
  - 依 `caps` 配置 `size` bytes
  - 目前實作使用 `heap_caps_calloc(1, size, caps)`（回來的 buffer 會先清 0）
- `heap_caps.free(buf) -> None`
  - 釋放由本模組配置出來的 buffer
  - `buf` 可以是單一 `memoryview`，也可以是 `memoryview` 的 list（list 中每個元素必須是「獨立配置」出來的 buffer）
- `heap_caps.realloc(buf, size, caps) -> memoryview | None`
  - 重新配置已存在的 buffer，並指定新的 `caps`
- `heap_caps.calloc(count, size, caps) -> memoryview | None`
  - 配置 `count * size` bytes，並清 0
- `heap_caps.aligned_alloc(alignment, size, caps) -> memoryview | None`（僅 ESP32）
- `heap_caps.aligned_calloc(alignment, count, size, caps) -> memoryview | None`（僅 ESP32）

### Heap 查詢（僅 ESP32）

- `heap_caps.get_free_size(caps) -> int`：目前可用 bytes
- `heap_caps.get_total_size(caps) -> int`：總量 bytes
- `heap_caps.get_largest_free_block(caps) -> int`：最大連續可用區塊 bytes

### 常用 caps 常數

模組會提供常用常數，例如：

- `heap_caps.CAP_DMA`（可用於 DMA 的記憶體，通常是 internal SRAM）
- `heap_caps.CAP_INTERNAL`（internal RAM）
- `heap_caps.CAP_SPIRAM`（PSRAM / SPIRAM）
- 以及其他目標平台提供的 `CAP_*`

## 範例

### 印出 DMA / PSRAM / INTERNAL 的容量

```python
import heap_caps

def show(title, caps):
    print(title)
    print("  free   :", heap_caps.get_free_size(caps))
    print("  total  :", heap_caps.get_total_size(caps))
    print("  largest:", heap_caps.get_largest_free_block(caps))
    print()

show("DMA (CAP_DMA)", heap_caps.CAP_DMA)
show("SPIRAM (CAP_SPIRAM)", heap_caps.CAP_SPIRAM)
show("INTERNAL (CAP_INTERNAL)", heap_caps.CAP_INTERNAL)
```

也可以把多個條件 OR 起來：

```python
show("INTERNAL|DMA", heap_caps.CAP_INTERNAL | heap_caps.CAP_DMA)
```

### 配置 DMA buffer

```python
import heap_caps

buf = heap_caps.malloc(32 * 1024, heap_caps.CAP_DMA)
if buf is None:
    raise MemoryError("no DMA heap")

# 把 buf 丟給你的驅動使用...

heap_caps.free(buf)
```

### SPI 螢幕常見做法（PSRAM 當 framebuffer + DMA 中轉）

在 ESP32 上，PSRAM 很大，適合放 framebuffer；但 SPI DMA 傳輸通常要求 buffer 在 `CAP_DMA`（internal）記憶體，因此需要中轉（bounce buffer）。

```python
import heap_caps

frame = heap_caps.malloc(240 * 320 * 2, heap_caps.CAP_SPIRAM)  # RGB565 framebuffer in PSRAM
tx = heap_caps.malloc(32 * 1024, heap_caps.CAP_DMA)           # DMA 中轉 buffer（internal）

if frame is None or tx is None:
    raise MemoryError

# 典型流程（示意）：
# for each chunk:
#     tx[:n] = frame[offset:offset+n]
#     spi.write(tx[:n])

heap_caps.free(tx)
heap_caps.free(frame)
```

## 重要注意事項（務必看）

- 本模組配置的記憶體不受 MicroPython GC 管理，必須手動 `heap_caps.free()`，否則會漏記憶體。
- 只能 free「由本模組配置回來的原始 memoryview」：
  - 不要把 slice（例如 `buf[16:]`）拿去 free，slice 指向的是偏移位址，free 會是非法行為。
  - 不要拿一般 `bytearray`/其他來源的 `memoryview` 丟進來 free。
- 做 DMA 時通常要看 `get_largest_free_block(caps)`：總可用量很大，不代表你能一次拿到一整塊連續的大 buffer。

## 建置 / 對接

### CMake ports（例如 ESP32 / ESP-IDF）

把本 repo 當成 user C module，並 include [micropython.cmake](file:///c:/Users/bl91920/Documents/code/git/mp_heap_caps/micropython.cmake)。

此模組會依據平台選檔：

- `ESP_PLATFORM` 為真：使用 `esp32_src/heap_caps.c`
- 其他：使用 `common_src/heap_caps.c`

### Make ports

使用 [micropython.mk](file:///c:/Users/bl91920/Documents/code/git/mp_heap_caps/micropython.mk) 以 user C module 方式加入。

