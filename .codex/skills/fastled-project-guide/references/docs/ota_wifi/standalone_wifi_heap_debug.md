# Standalone WiFi 無法加入 AP — Heap 耗盡事故報告（2026-07-12）

> **給未來 agent 的提醒**：改 storymode / patterns / shared 程式碼前，先讀本文件。
> 任何人報告「standalone WiFi 搜到但加入唔到」，第一步唔係查天線、密碼或 TX power，
> 而係**查 heap**。

## 症狀

- 手機搜到 `GARDUA_TEST` AP，但點擊加入後 tick 彈回，無法連線。
- 嚴重時 SSID 都唔穩定（beacon 斷斷續續）。
- Serial log 一切「正常」：AP 起動成功、無 error。
- 同一塊板燒回舊 commit（`093e70c8`）就可以正常加入。

## 根因

**Static RAM (.bss) 增長食光 WiFi 運作所需嘅 heap。**

- ESP32-S3 內部 DRAM 預算約 320KB；`pio run` 會顯示 `RAM: xx%`。
- WiFi softAP 起動後，剩餘 internal heap 必須夠處理 client association / DHCP。
- 實測門檻：**free heap ~22KB 可以正常 join；~2.3KB 時 AP 起到但 join 必定失敗**。
- 本次事故：`093e70c8` 之後 69 個 commit 新增嘅 storymode globals（slave8 booster
  fade states、`selected_RGB*`、各種 config struct）合共 +19.4KB static，
  令 RAM 由 77.5% 升到 83.4%，runtime free heap 跌到 2364 bytes。
- storymode + patterns 嘅 .bss 總量約 **159KB**，係最大 RAM 消耗者，
  每加一個新效果都會直接扣減 standalone WiFi mode 嘅 heap。

## 錯誤路徑（浪費時間的假設）

依次序被推翻，供未來參考：

1. ❌ MON touch LCD usb_test build（問題根本唔喺 MON）
2. ❌ Lolin S3 Mini 天線 TX power 過高（舊 firmware 同一塊板正常，證僞）
3. ❌ AP 設定順序 / softAPConfig DHCP 問題（master 用同一套 code 正常）
4. ✅ Heap 耗盡（serial log `heap=2364` 一錘定音）

**教訓：有 working commit 就先 diff + 比較兩版 `pio run` 嘅 RAM%，唔好靠估。**

## 修復

1. `firmware/shared/src/patterns/patterns_rgb/signal.cpp`：
   specificColor 8 組 `[5][25]` per-LED state array（~31KB .bss）改成
   `SpecificColorStatePool<T>` 首次使用先 `calloc`。WiFi mode 唔觸發呢啲
   pattern → RAM 全數釋放；story mode 時無 WiFi，heap 充裕。alloc 失敗
   fallback 返 `baseState`，唔會 crash。
2. 結果：RAM 83.4% → **73.5%**，WiFi mode free heap ~35KB，join 正常。
3. 同場移除 standalone digest auth（`STANDALONE_ADMIN_*`）：401 challenge
   會令 iOS captive portal probe 失敗，portal 唔會自動彈出。

## 未來規則

- **改 shared/storymode/patterns 前**：build `slave_standalone`，檢查 RAM%。
  **超過 ~76% 即係踩線**——standalone WiFi mode 會開始唔穩定。
- 新增大型 state array（>1KB）時，優先用 lazy heap pool 模式
  （參考 `signal.cpp` 嘅 `SpecificColorStatePool`），唔好直接開 file-scope static。
- 診斷工具：`standaloneController.cpp` 嘅 WiFi mode 有每 5 秒
  `heap= maxAlloc= psram= stations=` log，同 `STA connected/disconnected/got IP`
  事件 log。懷疑 WiFi 問題，一律先開 serial monitor 睇呢啲數。
- 塊板（lolin_s3_mini）**有 2MB PSRAM 且正常**（`psram=2097152`）。
  大型 buffer 可考慮 `ps_malloc`，但 WiFi driver 內部 alloc 必須用 internal RAM，
  所以 internal .bss 仍然要慳。
- Standalone 唔設 HTTP 驗證：本機 AP、無外網，加 auth 會殺死 captive portal。

## 相關檔案

- `firmware/slave/src/standaloneController.cpp` — AP 起動、診斷 log
- `firmware/shared/src/patterns/patterns_rgb/signal.cpp` — lazy state pool
- `docs/ota_wifi/wifi_update.md` — WiFi 啟動機制總覽
- `docs/colorpicker/color_picker.md` — standalone AP / ColorPicker 使用方式
