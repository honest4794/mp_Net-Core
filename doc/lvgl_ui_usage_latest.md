# LVGL UI 最新使用指南（2026-08 驗證版）

> 本文件對應 **slave new/** 的 LVGL 本地 UI 層（`ui/lvgl/` + `ui_test_tool.py`）。
> 描述：架構、啟動方式、螢幕方向、config 設定、字型生成、導覽框架、踩坑記錄。
> 舊參考：`mp_LVGL/ui/`（設計稿來源，只參考 UI 層面，內部數據機制不照抄）。

---

## 1. 檔案對應

```
slave new/
├── ui/lvgl/
│   ├── lvgl_init.py     # LVGL display 一次初始化 + bus reuse（對齊 i80_drv/tft_drv）
│   ├── ui_common.py     # palette / 字型 / widget builder + mk_list/mk_led/mk_arc 等 helper
│   ├── registry.py      # @register 動態註冊表
│   ├── app.py           # 平台解耦路由器（build_all 預建 screen + go 沿用）
│   ├── launcher.py      # 動態首頁（讀 registry 產生卡片）
│   ├── nav.py           # ★共用三層導覽狀態機（class Nav）
│   ├── board.py         # 板上對接層（lcd_mode 閘門 + 輸入 + 主迴圈）
│   └── page/
│       ├── __init__.py  # 集中 import（容錯：單頁失敗不拖垮其他）
│       ├── control_panel.py  # 控制面板（模式/亮度/倒數/拍攝·可動旗標）
│       ├── pca9685.py        # PCA9685 I2C 檢查器
│       └── settings.py       # 系統設定
├── driver/enc_drv.py    # ★硬體編碼器 driver（config ENC 區塊）
├── ui_test_tool.py      # ★獨立測試入口（import 即用，旋鈕+按鈕操作）
└── config.json          # System.lcd_mode / ENC / PIN(encC,btn)
```

## 2. 啟動方式

### 正式啟動（board.run）
- 受 `System.lcd_mode` 閘門控制：`"ui"` 才啟動 LVGL，否則 LCD 留給 player。
- 用法：
  ```python
  import ui.lvgl.board
  ui.lvgl.board.run()
  ```

### 獨立測試入口（ui_test_tool）
- **不受 lcd_mode 閘門限制**，import 即用（對齊 tft_test_tool 慣例）：
  ```python
  import ui_test_tool
  # 直接進主迴圈，實體旋鈕 + encC(確認) + btn(離開) 操作
  # Ctrl-C 回 REPL，LVGL 留 bus reuse
  ```
- REPL 除錯 API：`pages()`、`goto("settings")`、`cur()`、`peek("control_panel")`、`set("control_panel", {...})`、`frame(n)`、`run()`。

## 3. 架構原則

### 分層（對齊 slave new driver → bus → 應用）
- **硬體一律由 driver 初始化**，UI 只從 bus 取用，不自己 `machine.Encoder()`/`Pin()`。
  - encoder → `driver/enc_drv.py`（`bus.get_service("enc_list")`）
  - 確認鍵/離開鍵 → `driver/pin_drv.py`（`bus.get_service("pin_by_label")["encC"/"btn"]`）
  - LCD → `driver/tft_drv.py`（`bus.get_service("lcd")`）
- **LVGL display 一次初始化 + bus reuse**：`lvgl_init.get_platform()` 先查 `bus.service("lvgl_disp")`，已存在就重用。soft-reboot 後 LVGL C 層狀態殘留，重複 `lv.init()`/`display_create()` 會要配置數百 MB garbage（見踩坑 §8.1）。
- **頁面數據從 bus 讀**：`update()` 自己 `bus.shared.get(...)`（對齊 `jpeg_player` 慣例）。

### 導覽框架（nav.py）
三層狀態機 class，頁面只宣告「項清單 + 每項 kind + 回呼」，框架自動處理 enc/confirm/exit：
```python
from ui.lvgl.nav import Nav, ITEM_LIST, ITEM_SLIDER, ITEM_BUTTON
nav = Nav()
def build():
    nav.reset()
    nav.add(_mode_list, ITEM_LIST, on_change=_sel_mode_delta)   # confirm 進編輯，enc 上下選
    nav.add(_bright_sl, ITEM_SLIDER, on_change=_adj_bright)     # confirm 進編輯，enc 調值
    nav.add(btn, ITEM_BUTTON, on_change=_toggle)                # confirm 觸發
def on_enc(d):    nav.enc(d)
def on_confirm(): nav.confirm()
def on_exit():    return nav.exit()   # True=消耗(編輯中先退編輯)；False=回 launcher
```
項型別：`ITEM_INFO`（唯讀聚焦）/ `ITEM_SWITCH` / `ITEM_ENUM` / `ITEM_SLIDER` / `ITEM_BUTTON` / `ITEM_LIST`（新增，可編輯態）。

## 4. 螢幕方向（重要）

- **LCD 橫屏 320×240，但 config 是直向 240×320**。
- 關鍵：LVGL 自己送 MADCTL 0x60（`lvgl_init._MADCTL`），讓 ST7789 framebuffer 旋轉；`show()` 用 **bus adapter 的 `set_window`**（繞過 `ST7789.set_window` 在 rotation 90/270 的 x/y swap）。
- `config.json` 的 `TFT.rotation` 必須維持 `0`（driver 不送 MADCTL、不 swap），否則跟 LVGL 送的 MADCTL **double-rotate**。
- 要改直屏：`lvgl_init._MADCTL` 改 `0x00`，但頁面佈局也要改回直向。

## 5. config 設定

```json
"System": { "lcd_mode": "player" },        // "ui" = 啟動 LVGL；"player" = 留給 JPEG
"ENC": {
    "enable": 1,
    "list": [ { "id": 0, "GPIO": { "a": 18, "b": 8 } } ]   // 硬體編碼器 A/B
},
"PIN": {
    "list": [
        { "GPIO": 17, "label": "encC", "mode": "IN", "pull": "UP" },  // 確認鍵
        { "GPIO": 42, "label": "btn",  "mode": "IN", "pull": "UP" }   // 離開鍵
    ]
}
```
- **encoder A/B 不能放 PIN 段**：`machine.Encoder` 是硬體周邊，PIN 段會把它建成普通 GPIO Pin 衝突。放獨立 `ENC` 區塊（enc_drv 處理）。
- encoder 用 GPIO 18/8 需 `UART.enable = 0`（UART1 原本佔用 18/8）。

## 6. 字型生成（補缺字）

中文字體 `ui/lvgl/src/zh_hant_16.bin` 是 `lv_font_conv` 產生的 binfont（--no-compress）。頁面新中文字顯示成方塊 = 字集不足。

```bash
# 掃整個 ui/lvgl/ 目錄所有 .py 的非 ASCII 字 + 符號 → 重新生成
npx lv_font_conv --font "/Library/Fonts/Arial Unicode.ttf" --size 16 \
  --format bin --bpp 4 -r "0x20-0x7F,<所有碼點>" --no-compress \
  -o ui/lvgl/src/zh_hant_16.bin
```
- **掃整個目錄**（不手列 SRC），否則漏檔 → 缺字。
- 多收無害（註釋字也收），漏收才變方塊。
- 符號要補：`▲▼◀▶▽△↕↑↓→←°℃·±×÷—…（）` 等。
- 用 `lvgl/ui_common.py` 的 `init_fonts()` 讀 `/ui/lvgl/src/zh_hant_16.bin`。

## 7. 頁面數據對接（control_panel 與協議）

control_panel 頁與 `tasks/action_task_1.py` 共享 mode byte：
- `bus.shared["_display_mode"]` = mode byte：Bit7=拍攝模式(0x80)、Bit6=可動模式(0x40)、Bit5-0=模式值
- `bus.shared["_display_brightness"]`、`bus.shared["_display_time"]`（0-255）
- 切換旗標用 XOR（`_display_mode ^ 0x80`），只改旗標不動 mode 低 6 bit。

## 8. 踩坑記錄（開發技巧）

1. **LVGL 只能初始化一次**：soft-reboot 後 C 層殘留，重複 `lv.init()`+`display_create()` 會 `MemoryError` 要求數百 MB。解法：`get_platform()` 一次初始化 + bus reuse。
2. **MADCTL 只能一邊送**：driver rotation 與 LVGL 自送 MADCTL 只能擇一，否則 double-rotate 花屏。
3. **declare/build 時機**：頁面 `@register` 在 import 時跑、`build()` 在 `build_all()` 跑；依賴「build 後才有的 widget 資料」的邏輯要放對時機。
4. **switch binding API 差異**：`add_state`/`clear_state`/`has_state` 各 binding 名稱不一，用 `ui_common.sw_set/sw_get` wrapper 防護。
5. **MicroPython `json.dumps` 不吃 kwargs**：`ensure_ascii`/`indent` 在板上會 `TypeError`，用無 kwargs 版本 + 自製縮排。
6. **page import 容錯**：`page/__init__.py` 每個 import 包 try/except + `if pid in PAGES` 守護，單頁刪除/壞檔不拖垮其他頁。
7. **字型缺字**：新中文字 → 重跑字型生成（§6），方塊字消失。
8. **encoder 是硬體周邊**：不能放 PIN 段，獨立 `enc_drv`。

## 9. 常見操作

- 啟動測試：`import ui_test_tool`（旋鈕選/調，encC 確認，btn 返回，Ctrl-C 回 REPL）。
- 跳頁：`ui_test_tool.goto("pca9685")`。
- 看/設 bus 值：`ui_test_tool.peek("_display_mode")`、`ui_test_tool.set("_display_time", 120)`。
- 加新頁：建 `page/xxx.py`（`@register` + `nav`）+ `__init__.py` 加兩行（import + `_PAGES_MOD`）。
- 換螢幕方向：改 `lvgl_init._MADCTL`（0x60 橫 / 0x00 直）。
