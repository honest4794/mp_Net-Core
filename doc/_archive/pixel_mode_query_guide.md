# Pixel 模式查詢指南（MODE_LIST + MODE_DETAIL）

> 本文件說明模式播放嘅「查詢」方向：Master 點樣攞到模式列表、點樣逐個攞模式細節。
> 對應 schema：`slave/schema/pixel.json` 嘅 `0x3101/0x3102` 同 `0x3107/0x3108`。
> 播放控制（`0x3103~0x3106`）見 `doc/pixel_0x31xx_integration.md`。

---

## 0. 一分鐘結論

查詢分**兩層**：

1. **`0x3101/0x3102` 攞列表**：指定組別（`mode_type`：0=全部、1=LED、2=SERVO）攞該組模式嘅 `(mode_type, mode_id)` + `total_ms`（保底時間）。回覆會**回音 `mode_type`**（表示呢個 list 係邊一組）。每筆固定 6 bytes，最多 255 筆，永遠唔會爆 8K payload。
2. **`0x3107/0x3108` 攞細節**：逐個模式問 `total_ms` 回音 + `name`（UTF-8）。

Master 只需要攞自己用到嘅模式細節，唔使硬食晒成個列表嘅名。

---

## 1. 方向總覽

| 指令 | 方向 | 誰發 | 誰收 | 單播/廣播 | 回覆 |
|---|---|---|---|---|---|
| `0x3101 MODE_LIST_QUERY` | Master → Slave | Master | Slave | 指定單播（必回覆） | `0x3102` |
| `0x3102 MODE_LIST_RSP` | Slave → Master | Slave | Master | — | — |
| `0x3107 MODE_DETAIL_QUERY` | Master → Slave | Master | Slave | 指定單播（必回覆） | `0x3108` |
| `0x3108 MODE_DETAIL_RSP` | Slave → Master | Slave | Master | — | — |

- 兩條 QUERY 都係**單播**（ADDR 指定單顆 Slave），Slave 必回覆；唔支援廣播。
- `MODE_LIST_QUERY` 要帶 `mode_type` 指定查邊一組（0=全部、1=LED、2=SERVO）；`MODE_LIST_RSP` 會**回音**呢個值。
  ⚠️ 注意：query 參數嘅 `mode_type=0` 係「查全部」，同模式識別碼入面嘅 `mode_type=0`（系統模式 UNKNOWN/DEV）**語義唔同**，唔好混淆（見 §2）。
- Slave 被動原則：唔會自己推送，一定要 Master 問先答。

---

## 2. 指令總表

| CMD | 名稱 | Payload 摘要 |
|---:|---|---|
| `0x3101` | `MODE_LIST_QUERY` | `mode_type:u8`（0=全部、1=LED、2=SERVO） |
| `0x3102` | `MODE_LIST_RSP` | `mode_type:u8`（回音） + `count:u8` + `entries:bytes_rest`（每筆 6B：mode_type + mode_id + total_ms） |
| `0x3107` | `MODE_DETAIL_QUERY` | `mode_type:u8` + `mode_id:u8` |
| `0x3108` | `MODE_DETAIL_RSP` | `mode_type:u8` + `mode_id:u8` + `total_ms:u32` + `name:str_u16len` |

> **語義區別**：`0x3101/0x3102` 入面嘅 `mode_type` 係「組別選擇／回音」（0=全部、1=LED、2=SERVO）；
> 而 `0x3107/0x3108` 同 entries 入面嘅 `mode_type` 係「模式識別碼高位」（1=LED、2=SERVO，0=系統模式）。
> 兩個用法唔同，睇清楚係邊條指令。

---

## 3. 逐指令 byte 佔位

### 3.1 `0x3101 MODE_LIST_QUERY`

**Payload = 1 byte（`mode_type`）。** 指定查邊一組：

| byte offset | size | 欄位 | 說明 |
|---|---|---|---|
| 0 | 1 | `mode_type` | `0`=全部（LED+SERVO 一次過）、`1`=LED、`2`=SERVO，其餘保留 |

範例：查 LED 組 → payload = `01`。全個 NC4 幀：

```text
SOF "NC" | VER 04 | ADDR(2B) | CMD 01 31 | LEN 01 00 | 01 | CRC32(4B)
```

### 3.2 `0x3102 MODE_LIST_RSP`

Payload 佈局：

```text
byte 0                    mode_type (u8)  回音 query：0=全部、1=LED、2=SERVO
byte 1                    count     (u8)  模式總數, 上限 255
byte 2 .. 2+6×count       entries         每筆連續排列, 無 padding / 無分隔
```

每筆 entry（**固定 6 bytes**，全部 little-endian）：

| byte offset | size | 欄位 | 值域 / 說明 |
|---|---|---|---|
| 0 | 1 | `mode_type` | key 高位：`1`=LED、`2`=SERVO，其餘保留 |
| 1 | 1 | `mode_id` | key 低位：該組內索引，0 起 |
| 2 | 4 | `total_ms` | 模式總時間（毫秒）；`0`=不設限（DEV／常駐） |

**範例：** 查 LED 組（`MODE_LIST_QUERY mode_type=1`），回 2 個 LED 模式 `(1,0)` 30000ms、`(1,1)` 5000ms：

```text
01                         mode_type 回音 = 1 (LED)
02                         count = 2
01 00  30 75 00 00         entry[0]: mode_type=1, mode_id=0, total_ms=30000
01 01  88 13 00 00         entry[1]: mode_type=1, mode_id=1, total_ms=5000
```

（`30000 = 0x7530` → LE `30 75 00 00`；`5000 = 0x1388` → LE `88 13 00 00`。）

### 3.3 `0x3107 MODE_DETAIL_QUERY`

Payload **固定 2 bytes**：

| byte offset | size | 欄位 | 說明 |
|---|---|---|---|
| 0 | 1 | `mode_type` | 要查嘅模式 key 高位（1=LED、2=SERVO） |
| 1 | 1 | `mode_id` | 要查嘅模式 key 低位 |

`(mode_type, mode_id)` 必須係 `MODE_LIST_RSP` 清單內嘅組合，直接由列表原樣搬過嚟。

**範例：** 查 `(1, 0)` → payload = `01 00`。

### 3.4 `0x3108 MODE_DETAIL_RSP`

Payload 佈局（`name` 用協議原生 `str_u16len`：前置 2B LE 長度 + UTF-8 內容）：

| byte offset | size | 欄位 | 說明 |
|---|---|---|---|
| 0 | 1 | `mode_type` | 回音, 同 query |
| 1 | 1 | `mode_id` | 回音, 同 query |
| 2 | 4 | `total_ms` | 模式總時間（與 list 一致） |
| 6 | 2 | `name_len` | **name 的 byte 數**（不是字元數）；`0`=空名 |
| 8 | `name_len` | `name` | UTF-8, 可含中文, 無 null terminator |

**範例：** `(1,0)` 30000ms、名「預設模式」（UTF-8 12 bytes）：

```text
01  00  30 75 00 00  0C 00  E9 A0 90 E8 A8 AD E6 A8 A1 E5 BC 8F
│   │   └─total_ms─┘  └─len─┘  └──── name "預設模式" (12B) ────┘
└─┬─┴─ type/id
```

---

## 4. 建議使用流程

```text
Master                            Slave
  │  1. MODE_LIST_QUERY (0x3101)   │
  │     mode_type (0=全部/1=LED/2=SERVO)
  ├───────────────────────────────>│
  │  2. MODE_LIST_RSP   (0x3102)   │  ← 回音 mode_type + 攞晒 ID + total_ms
  │     mode_type + count + N 筆 6B entry │
  │<───────────────────────────────┤
  │  3. MODE_DETAIL_QUERY (0x3107)  │  對「自己要用」嘅模式逐個問
  │     mode_type, mode_id         │
  ├───────────────────────────────>│
  │  4. MODE_DETAIL_RSP   (0x3108) │  ← total_ms 回音 + name
  │<───────────────────────────────┤
  │  5. (重複 3~4 直到攞完)          │
```

**要點：**
- 第 1~2 步係一個 round trip：一次指定 `mode_type` 查一組（或 0=全部），攞晒嗰組。
- 第 3~4 步**唔使每個模式都做**——Master 只需要攞自己有需要顯示／使用嘅模式，例如 UI 只顯示前 5 個，就只問嗰 5 個。
- 順序：建議 Master 按列表順序逐個查，Slave 唔保證回覆順序，Master 靠 `(mode_type, mode_id)` 回音對返。

---

## 5. 容量與限制

| 限制 | 數值 | 計法 |
|---|---|---|
| `count` 上限 | **255 筆** | u8 極限 |
| list payload | 1532 bytes（mode_type 1B + count 1B + 255 筆 × 6B） | 遠低於 8K |
| 8K payload 可容 | 1365 筆（6B/筆） | 實際用唔到，count 先爆 |
| name 上限 | 65535 bytes（u16 len） | 實際受 8K payload 約束 |

**結論：** 列表唔需要分頁；樽頸係 `count:u8`（255）。若模式總數超過 255，可按組別（`mode_type`）分開查詢（每組仍受 255 上限）；只有當**單一組**都會超過 255 時，先需要升級 `count` 型別（目前無此需求）。

---

## 6. 邊界與錯誤處理

| 情況 | 行為 |
|---|---|
| `MODE_LIST_QUERY.mode_type` 唔合法（3–255） | Slave 回 `MODE_LIST_RSP`：`mode_type` 回音=0、`count=0`（空列表） |
| `MODE_DETAIL_QUERY` 嘅 `(mode_type, mode_id)` 唔喺清單內 | Slave 回 `mode_type=0, mode_id=0, name 空`（或忽略, 待決） |
| Slave 收唔到 / Master 等唔到回覆 | Master 視為 UNKNOWN（`mode_type=0, mode_id=0`），保留上次有效狀態 |
| `name_len=0` | 空名, 合法（例如機械模式無名） |
| `total_ms=0` | 不設限（DEV／常駐模式）, 唔係錯誤 |
| 收到 payload 長度同 count 唔夾（多咗／少咗） | 以 `count` 為準解析, 忽略尾隨／唔足就當截斷, 唔好靠長度猜筆數 |
