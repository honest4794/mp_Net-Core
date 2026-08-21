# fast_io — SD 卡中央儲存管理器

> **用途**：MicroPython 上 DMA 加速的 SD 卡管理套件。繞過 FAT/VFS，直接操作 raw sector，提供檔案級別的讀寫 API。
> **分類**：使用教學（02_guides）
> **最後更新**：2026-08-16
> **位置**：`slave/lib/sys/fast_io.py`
> **相依**：`/sd/alloc.json`、`lib.sys_bus`（提供 `sd_raw`）；與 `storage_tool.py`（PC 端導入工具）共用相同 managed area 格式
> **相關**：底層記憶體與串流慣例見 `03_notes/02_buffer_architecture.md`（L0/L5）

---

## 元件

| 元件 | 用途 | 記憶體 |
|------|------|--------|
| `Allocator` | sector 分配表 (alloc.json) 讀寫 | 內部使用 |
| `Storage` | 檔案級別讀寫 | 單一 DMA buffer |
| `StreamReader` | 雙緩衝零複製串流 | 雙 DMA buffer |

匯入：

```python
from lib.sys.fast_io import Storage, StreamReader
```

---

## Storage API

### 初始化

```python
s = Storage(buf_size=16384)
```

- `buf_size`：DMA buffer 大小，也是每次 SD 交易的 chunk 大小。預設 16384（16KB）

### 寫入

**一次寫入：**

```python
data = bytearray(512 * 1024)
s.write_file("scene.jpk", data)
# 自動佔位 → 寫入 → CRC → 完成
```

**分段寫入：**

```python
s.write_begin("anim.bin", total_bytes)
while True:
    chunk = next_chunk()
    if not chunk: break
    s.write(chunk)     # 累計 CRC，寫滿自動結束
```

**手動結束：**

```python
s.write_end()
```

寫入流程：
```
write_begin → alloc.json 佔位 (CRC=FFFFFFFF)
write(chunk) → SD 寫入 + CRC 累計
write_end   → alloc.json 更新為最終 CRC
```

### 讀取

**一次性讀取：**

```python
data = s.read_all("scene.jpk")
```

**分段讀取：**

```python
s.read_begin("scene.jpk")
buf = bytearray(16384)
while True:
    n = s.read_into(buf)
    if n == 0: break
    process(buf[:n])
s.read_end()
```

`read_begin` 會檢查 CRC。如果檔案是未完成的寫入（CRC=FFFFFFFF），會拋出錯誤。

### 管理

```python
s.list_files()
s.remove("scene.jpk")
s.close()
```

---

## StreamReader API

雙 DMA 緩衝，零複製串流。適合需要最高吞吐的 pipeline。

```python
r = StreamReader(buf_size=16384, n_bufs=2)
r.start(alloc, "scene.jpk")

# 填充 → 消耗 循環
rem = r._r_cnt
spc = r.chunk_sectors
sec = r._r_sector

while rem > 0:
    if not r.feed(sec):
        v = r.next()
        if v is not None:
            process(v)   # 零複製，直接操作 memoryview
            r.release()
        continue
    sec += spc; rem -= spc

while True:
    v = r.next()
    if v is None: break
    process(v)
    r.release()

r.close()
```

| 方法 | 說明 |
|------|------|
| `feed(sector)` | 從 SD 讀一個 chunk 到空閒 DMA buffer |
| `next()` | 取得 ready chunk 的 `memoryview`（零複製） |
| `release()` | 歸還 buffer |
| `read_into(buf)` | 複製模式（相容 Storage 風格） |

**重要**：`next()` 傳回的 memoryview 指向 DMA buffer，處理後必須 `release()`，否則 buffer 無法回收。

---

## alloc.json 格式

```json
{
  "_version": 1,
  "_offset": 65536,
  "scene.jpk": [65536, 2048, "C0DE1234"],
  "anim.bin": [67584, 512, "FFFFFFFF"]
}
```

- `_offset`：managed area 起始 sector（FAT 之後）
- `[sector, count, crc]`：起始 sector、sector 數、CRC32
- CRC = `FFFFFFFF`：寫入未完成，不可讀取

---

## 效能參考（ESP32-S3, 16KB DMA, 512KB 檔案）

| 操作 | 速度 | vs VFS |
|------|------|--------|
| `Storage.write_file` | 3.5 MB/s | 14x |
| `Storage.read_into` | 7.3 MB/s | 7x |
| `StreamReader` 零複製 | **12.8 MB/s** | **12x** |
| VFS 讀取 | 1.1 MB/s | 1x |

## 相關文件

- `03_notes/02_buffer_architecture.md` — 多級緩衝架構（L0 分配層 / L5 輸出層）
- `03_notes/06_raw_sd_plan.md` — Raw SD 繞過 FAT 的兩階段計劃（本模組的進化方向）
