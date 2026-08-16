# pixel 模式層（第三層：map）

> 介紹區：模式是什麼、id/name 雙引用、執行語意。

## 1. 介紹區 — 模式（mode）

「模式」是真正生效的載體，把一個效果（effect）綁到群組（group）或單顆 pixel，
並在配對時指定寫入方法（`write`：`rgb` / `w` / `ww`）。

每個模式有**模式 ID（`id`）+ 模式名稱（`name`）**，兩個都是全域唯一，供指令層
用 id 或 name 引用。

## 2. 介紹區 — 檔案

`pixel/map/<name>.mode.json`

```json
{
  "id": 1,
  "name": "demo1",
  "map": [
    { "group": 1,        "effect": 1,          "write": "rgb" },
    { "group": "motors", "effect": "breathing", "write": "w"   }
  ],
  "gap_time_ms": 20,
  "run_time": 300
}
```

## 3. 介紹區 — 群組與效果都用 id / name 雙引用

`map[]` 的 `group` 與 `effect` 欄位**同時支援 id（整數）或 name（字串）**：

- `group`：群組的 id 或 name（對應 `registry.json` 的 groups）。
- `effect`：效果的 id 或 name（對應 `effects/effects.json` / `effects/effects.py`）。

可混用。上例中：

- 第一項：group 用 id（1 = gundam_body）、effect 用 id（1 = breathing）。
- 第二項：group 用 name（motors = 群組 3）、effect 用 name（breathing）。

## 4. 介紹區 — id 慣例

與 effects / groups 一致：**id 從 1 開始**，`0` 保留為「未指定 / 自動配發」哨兵值。

## 5. 介紹區 — 執行（一次 / 循環）

模式本身只描述「怎麼配對」，**不寫執行次數**。執行「一次」或「不斷循環」由
指令層（command）決定，例：

- `run_mode_once(id)` — 跑一次
- `run_mode_loop(id)` — 不斷循環

> 指令層尚未實作，本階段只在方向文件記錄語意。
