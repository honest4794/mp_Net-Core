# ColorPicker 使用筆記

ColorPicker 是本專案的燈光測試 app；`slave_standalone` 現在可以不用 router，直接開本機 AP 進入控制頁。

---

## Profile 快取

Master 的 `/api/state` 會快取每台 slave 的 RGB/PCA profile 45 秒，避免每次頁面刷新都同步等待 7 個 `INFO:` I2C 查詢。需要立即重讀硬體設定時使用：

```text
GET /api/state?refresh=1
```

`/api/pwm_scan` 是使用者主動掃描，仍會即時送出 `INFO:PSC`，不使用掃描結果快取。

## Sequence 編輯與裝置播放

Sequence 頁會把 timeline 編譯成 `SEQV1` 後上傳到 `/api/seq/upload`；裝置以非阻塞 tick 轉送既有 `LC:` 指令。完整格式與 API 見 [`docs/colorpicker/sequencer.md`](sequencer.md)。

Story mode boundary 匯出只產生 `-D STORYMODE_*_TOTAL_SECONDS=` 片段，不會在 runtime 覆寫 Master/Timer 的時長合約。

可用端點：`/api/seq/upload`、`/api/seq/play`、`/api/seq/stop`、`/api/seq/list`、`/api/seq/get`。

## UART Motor 頁

核心概念：ColorPicker 只發「想點郁」嘅命令；真正安全停止由 Slave 本地 1 秒 lease 保證。

- 頂層 `UART Motor` 分頁已有 DC Motor 控制；Servo Motor、Stepping Motor 暫時只保留分頁入口。
- 可選 Slave 1–20、設定 1–16 個不重複十進制地址（`1..253`）及 `0..100%` 速度。
- `Direction A = Close`、`Direction B = Open`；手動按鈕必須按住，放手即 STOP。
- Pattern 有 `Sine`、`Smooth Mechanical`、`Hydraulic Cinematic`，曲線實作集中在 `firmware/shared/src/patterns/patterns_uart_dc_motor.cpp`。
- 瀏覽器每 300 ms 發 keepalive；離開分頁、頁面失焦／隱藏、關閉頁面或 WiFi 中斷時會要求 STOP。即使最後一個 HTTP STOP 遺失，Slave 收不到 keepalive 超過 1 秒亦會自行停止。
- 大型紅色 `STOP ALL UART MOTORS` 只停止指定 Slave 目前由 live UI 控制的 UART motors，不會中止 RGB story timeline。

Master HTTP endpoint：

```text
POST /api/uart_motor
```

Master 會把 HTTP payload 轉成既有 `LC:` side-channel，再按 `target` route 到指定 Slave：

```text
LC:um,drive,A|B,SPEED,COUNT,ADDR...
LC:um,pattern,sine|smooth|hydraulic,SPEED,COUNT,ADDR...
LC:um,keep
LC:um,stop
```

修改 UI 後的最低驗證：

```bash
node --check web/script.js
node scripts/test_colorpicker_uart_motor.js
python3 scripts/build_web.py
```

---

## 入口

### Master WiFi 更新模式

- 控制頁：`http://<master-ip>/colorpicker`
- 主要檔案：`firmware/master/src/colorpicker.cpp`
- 靜態頁來源：`web/`，由 `scripts/build_web.py` 預壓成 `data/html/colorpicker.html.gz`。
- Master 使用 `config/partitions/partitions_master_usb.csv` 的約 2.19 MB LittleFS，優先開啟 gzip 頁面；若缺少 `.gz`，才 fallback 到 `colorpicker.html`／`picker.html`。
- 傳送方式與 standalone 相同：設定 `Content-Length`、只送一次 `Content-Encoding: gzip`，並以 512-byte 非阻塞區塊傳送；60 秒無進度才中止，期間持續餵 watchdog，避免大型頁面變成亂碼或連線卡死。
- 安全：連上 Master AP 後即可直接使用所有 Web route，不需要額外 HTTP 登入；Wi-Fi AP 密碼仍然保留。
- Master 韌體只用 USB 更新；Wi-Fi 頁只保留 ColorPicker 與 Slave 1–10 OTA。

#### WiFi ColorPicker compile flag

核心概念：WiFi ColorPicker 只是「網頁遙控器」；mon / Touch LCD 以後會變成「UART 遙控器」。兩者最後都靠 slave 的 live ColorPicker receiver 執行 `LC:` 指令。

開關在 `firmware/shared/include/globals.h`：

```cpp
#define ENABLE_WIFI_COLORPICKER 1
```

- `1`：master 註冊 `/colorpicker` 與 `/api/...`，適合現在沒有 mon、要用 WiFi 測燈。
- `0`：master 不註冊 WiFi ColorPicker route，可節省 master flash；`LCUSB`、Touch UART、master-to-slave I2C、slave live receiver 仍保留。

之後 mon / Touch LCD 接好後，可在 `platformio_local.ini` 的 `[env:master]` build flags 加：

```ini
-D ENABLE_WIFI_COLORPICKER=0
```

不要用這個 flag 關掉 `firmware/slave/src/slave_live_colorpicker.cpp`；mon 仍需要 slave 端接收 `LC:` 指令。

### Slave Standalone 本機 AP

- AP 名稱：以 `platformio_local.ini` 的 `STANDALONE_WIFI_NAME` 為準（目前 `GARDUA_TEST`）
- AP 密碼：以 `STANDALONE_WIFI_PASSWORD` 為準（目前 `12345678`）
- Web 管理登入：無（standalone 不設 HTTP 驗證，連上 AP 即可使用，captive portal 自動彈出）
- IP：`192.168.4.1`
- 完整控制頁：`http://192.168.4.1/colorpicker.html`
- `/`、`/app`、`/colorpicker`、`/colorpicker.html` 會送出完整 ColorPicker app。
- app 頁以 **gzip 預壓**方式提供：uploadfs 只打包 `/html/colorpicker.html.gz`（約 892 KB → 約 160 KB），`standaloneHandleApp` 送出時加 `Content-Encoding: gzip`。
- iPhone / Android / Windows 的 captive portal 偵測網址會依 `9999de1f` 時期的方式 redirect 到 `/app`，而 `/app` 會直接送完整 ColorPicker；目前仍保留 gzip 傳輸降低 AP 傳輸量。

`slave_standalone` 只保留本機 AP。它不連 router、不掃描 WiFi、不存 router 密碼，也沒有 WiFi manager。

### Shopping Mall Playlist

- Playlists 頁的八個位置有明確用途：Playlist 1 是 69-step Shopping Mall Demo，Playlist 2 是可編輯 Teddy Bear StoryMode，Playlist 3–8 由使用者自由編輯。
- 主要控制是「上一個效果／停留目前效果／下一個效果」；「停留目前效果」再次按下會繼續自動播放，紅色 STOP 仍獨立保留。
- 對應 API 是 `POST /api/v2/playlists/{slot}/previous`、`/pause`、`/resume`、`/next`；Previous 在第一個 step 會回到最後一個 step。
- Demo 使用裝置目前回報的 strip 與編譯期 `NUM_LEDS_RGB*`，不把其他 project 的燈數硬編碼進 Playlist。

### WLED 效果分類與名稱

- 一般燈帶頁獨立顯示 61 個 WLED 1D，Matrix 頁獨立顯示 11 個 WLED 2D。
- 畫面名稱統一為 `WLED 1D | English（繁體中文）` 及 `WLED 2D Matrix | English（繁體中文）`，例如 `WLED 1D | Colorwaves（彩色波浪）`。

### Playlist Preview 參數檢查

- 本機 Preview 可直接開啟 `simulator/preview.html#playlists`，不依賴 ESP32 或裝置 API。
- Playlist 1 直接讀取 `web/data/shopping_mall_playlist.json` 的 69 個 steps；Playlist 2 直接讀取 `web/data/teddy_bear_storymode_demo.json` 的 11 個 modes／320 個 events。
- 點擊 Playlist 會立即預覽第一項；再點 Step／Mode／Event 可同時查看原始 JSON 參數、實際送入預覽引擎的值，以及 Pattern／Matrix／PWM／Solid 畫面。

---

## 進入 Standalone WiFi Mode

目前 standalone 用「短時間重開機」進入 WiFi mode：

1. 10 秒內第 1 次開機：log 顯示 `Standalone: reboot counter 1/3`
2. 10 秒內第 2 次開機：log 顯示 `Standalone: reboot counter 2/3`
3. 10 秒內第 3 次開機：啟動 AP，log 顯示：

```text
Standalone: reboot counter 3/3
Standalone: WiFi AP 'Penelope-Standalone' IP=192.168.4.1 channel=6 stations=0
Standalone: WiFi mode active; story effects stopped
```

達到 `3/3` 後，計數器會歸零；下一輪會重新從 `1/3` 開始。若尚未達到 `3/3` 且超過 10 秒，目前程式會保留計數。

---

## 燒錄與上傳 Web UI

只測 standalone 時用：

```bash
arch -arm64 pio run -e slave_standalone
arch -arm64 pio run --target upload -e slave_standalone
arch -arm64 pio run --target uploadfs -e slave_standalone
```

修改 `web/` 後先打包，再 `uploadfs`：

```bash
python3 scripts/build_web.py
arch -arm64 pio run --target uploadfs -e slave_standalone
```

如果改過 `config/partitions/partitions_standalone.csv`，需要整顆 erase、重新燒 firmware，再重新 `uploadfs`。

```bash
arch -arm64 pio run --target erase -e slave_standalone
arch -arm64 pio run --target upload -e slave_standalone
arch -arm64 pio run --target uploadfs -e slave_standalone
```

---

## Standalone ColorPicker 行為

- 進入 WiFi mode 後，standalone story loop 會停止，避免 story effect 跟 ColorPicker 搶 LED。
- ColorPicker 可控制 RGB、PCA/WLED、亮度、pattern 與每條 RGB 的 live `NUM_RGBX`。
- 如果 live `NUM_RGBX` 從 200 改成 20，韌體會清掉第 21 到 200 顆的尾端殘影，避免保留上一個 pattern 的靜止畫面。
- WiFi ColorPicker 的輸出幀率維持 20 FPS；VU meter 測試頁目前也是 20 FPS，並用平滑與 peak comet 讓下降不要像閃爍。

相關檔案：

- `firmware/slave/src/standaloneController.cpp`
- `firmware/slave/src/slave_live_colorpicker.cpp`
- `web/script.js`
- `web/tabs/vu_test.html`

### 本次 session 更新紀錄

- 已將 `lib_rgb` 中 5 個 RGB pattern 的呼叫簽名改為「參數 struct + context」：
  `randomBreath`、`gradientDynamicPalette_V2`、`twoSideComet`、`randomFillAllMultiStage`、`discreteBreathWave`。
- 已同步更新 `firmware/slave/src/slave_live_colorpicker.cpp` 的對應 case 呼叫，並將 `PAT_RGB_GRAD_VENT_PALETTE` 也改為新版 `gradientDynamicPalette_V2` 參數化呼叫。
- 已更新 `firmware/shared/src/patterns/patterns_rgb.cpp` 中 GN Wire Normal/TransAM 舊版 `gradientDynamicPalette_V2` 呼叫，改用新的 struct 簽名。
- 2026-07-06 續轉 Batch A：已將 `fadeInOut`、`fadeInOutPalette` 與 `drawTwinkles` 改為 `RgbUniversalParams + Params + Context` 呼叫；同步更新 `slave_live_colorpicker.cpp`、`patterns_rgb.cpp` 與 `storyMode_struct.h` callsite。
- Batch A 驗證：`python scripts/validate_rgb_full_param_inventory.py` 顯示 `converted=28`、`remaining_effects=77`；`python scripts/validate_rgb_colorpicker_params.py`、`python scripts/validate_wled_universal_params.py` 通過；`arch -arm64 pio run -e slave_standalone` 成功。
- 2026-07-06 續轉 Batch A.1：已將 `fadeInOutPartial` 改為 `RgbUniversalParams + RgbFadeInOutPartialParams + RgbFadeInOutContext`；同步更新 `platform()` 內唯一 callsite。驗證後 `converted=29`、`remaining_effects=76`，`arch -arm64 pio run -e slave_standalone` 成功。
- 2026-07-06 續轉 Batch B：已將 `gradualFill`、`gradualFillInOut`、`gradualFillInOutPalette` 改為 universal params / params / context；同步更新 `platform()` 內 gradual flow callsite。驗證後 `converted=32`、`remaining_effects=73`，`arch -arm64 pio run -e slave_standalone` 成功。
- 2026-07-06 續轉 Batch B.1：已將 `paletteFlow` 與 `signalPalette` 改為 universal params / params / context。驗證後 `converted=34`、`remaining_effects=71`，`arch -arm64 pio run -e slave_standalone` 成功。
- 2026-07-06 續轉 major storyMode batch：已將 `whiteSwipe`、`shoppingMallLight_V2`、`randomFillAll_V2` 改為「universal 欄位展開 + effect params + context」；`storyMode` 呼叫點的 universal 預設、常用 twinkle params、random fill 顏色/速度集中到 `storyMode_parameter.cpp` 的 `sm_rgb`，避免在 storyMode 內硬寫 `255, 0, 255, 0, 0` 這類數字。驗證後 `converted=37`、`remaining_effects=68`，`arch -arm64 pio run -e slave_standalone` 成功。
- 2026-07-06 續轉 high-use storyMode flash batch：已將 `randomFlashWithGap_multiple`、`randomLightUp` 改為「universal 欄位展開 + params + context」；同步更新 `storyMode_0_v1.cpp`、`storyMode_0_v2.cpp` 與 ColorPicker live case。`/4`、`fadeAmount=150`、random-light density 等常用值集中到 `sm_rgb`。驗證後 `converted=39`、`remaining_effects=66`，`arch -arm64 pio run -e slave_standalone` 成功。
- 2026-07-06 續轉 GN Wire batch：已將 `GN_Wire_Normal`、`GN_Wire_TransAM` 改為「universal 欄位展開 + params + context」；storyMode 呼叫點改用 `storyMode_awakening_3_params` namespace 的參數（如 `speed`、`gnWireNormalBrightnessMin`、`gnWireNormalBrightnessMax`、`gnWireNormalCycleDurationMs`、`gnWireNormalTotalDurationMs`、`gnWireNormalBrightnessRampUpMs`），不再把 `255, 0, 255, 0, 0` 類型硬值塞在呼叫端。ColorPicker 的 GN Wire UI 也補上 speed、brightness、direction、palette 與 GN Wire 子參數 slider，並同步 output JSON。驗證後 `converted=41`、`remaining_effects=64`，`python scripts/validate_rgb_colorpicker_params.py`、`python scripts/validate_wled_universal_params.py`、`arch -arm64 pio run -e slave_standalone` 成功。
- 2026-07-06 續轉 Turbine V3 batch：已將 `turbine_v3` 改為「universal 欄位展開 + `RgbTurbineV3Params` + `RgbTurbineV3Context`」；storyMode 呼叫點改用 `sm_rgb::turbineV3Config`，原本函式內的 frame interval、flash/booster/rotate/decelerate 時間、顏色與亮度都集中到 `storyMode_parameter.cpp` 的命名常數。ColorPicker 原本沒有 `PAT_RGB_TURBINE_V3` live case，這次已補上，並新增 Turbine V3 的 speed、brightness、direction 與主要 stage slider。驗證後 `converted=42`、`remaining_effects=63`，`python scripts/validate_rgb_colorpicker_params.py`、`arch -arm64 pio run -e slave_standalone` 成功。
- 2026-07-06 續轉 Footplate V2 / universal 實作檢查：已修正 `turbine_v3` live case 不再用預設 `cycleDurationMs=3000` / `totalDurationMs=60000` 強行改變原始時序，改成使用者有送參數才覆蓋。`footplatev2` 已改為「universal 欄位展開 + `RgbFootplateV2Params` + `RgbFootplateV2Context`」，storyMode 呼叫點改用 `sm_rgb::footplateV2Config`，Footplate V2 的 fade、booster、stage duration、white swipe、ignition、explosion 參數集中到 `storyMode_parameter.cpp`；ColorPicker 補上 `PAT_RGB_FOOTPLATE_V2` live case、output JSON 與 sliders。驗證後 `converted=43`、`remaining_effects=62`，`python3 scripts/validate_rgb_full_param_inventory.py`、`python3 scripts/validate_rgb_colorpicker_params.py`、`python3 scripts/validate_wled_universal_params.py`、`git diff --check` 與 `arch -arm64 pio run -e slave_standalone` 成功。
- 2026-07-06 universal 參數實作稽核：新增 `scripts/validate_rgb_universal_param_usage.py`，專門防止已轉換的 high-use RGB effects 把 universal 參數用 `(void)` 空接。已修正 `whiteSwipe`、`randomFlashWithGap_multiple`、`randomLightUp`、`shoppingMallLight_V2`、`randomFillAll_V2`，讓 speed、duration、palette/color 進入實際邏輯。驗證後 `python3 scripts/validate_rgb_universal_param_usage.py`、`python3 scripts/validate_rgb_full_param_inventory.py`、`python3 scripts/validate_rgb_colorpicker_params.py`、`python3 scripts/validate_wled_universal_params.py`、`git diff --check` 與 `arch -arm64 pio run -e slave_standalone` 成功。
- 2026-07-06 universal signature 展開：已移除已轉換 RGB effects 的 `const RgbUniversalParams& universal` 函式簽名，改為直接展開 `speed`、`brightnessMin`、`brightnessMax`、`cycleDurationMs`、`totalDurationMs`、`directionMode`、`color`、`palette` 八個欄位；effect-specific `params` 與 `context` struct 保留。同步更新 live colorpicker、story mode 與 validator，`arch -arm64 pio run -e slave_standalone` 成功。
- 2026-07-06 GN/Kampfer batch：已將 `GN_Capacitor_Normal`、`GN_Capacitor_TransAM`、`GN_Shield_Normal`、`GN_Shield_TransAM` 與 `KampferGrenade` 改為「universal 欄位展開 + effect params + context」。新增的 wrapper config 使用 `Rgb...Config` 命名，不再使用容易誤解成 story 專屬的 story-prefixed config 名字。GN Capacitor / Shield 的預設值集中到 `storyMode_parameter.cpp`，ColorPicker 補上 GN Capacitor / Shield sliders、中文/英文 info 說明與 output JSON，同步 slave live case 實際讀取的 key。驗證後 `converted=48`、`remaining_effects=57`，`python3 scripts/validate_rgb_full_param_inventory.py`、`python3 scripts/validate_rgb_colorpicker_params.py`、`python3 scripts/validate_rgb_bottom_params.py`、`python3 scripts/validate_pattern_info_icons.py`、`python3 scripts/validate_colorpicker_uart_workflow.py`、`git diff --check` 與 `arch -arm64 pio run -e slave_standalone` 成功。
- 2026-07-07 GN Drive batch：已將 `GN_Drive_Normal`、`GN_Drive_Running`、`GN_Drive_TransAM` 改為「universal 欄位展開 + params + direct instance context」。storyMode callsite 改用 `sm_rgb::gnDrive*Config` 與 `gnDriveInstances[]` / `gnDriveRunningInstances[]` / `gnTransAMInstances[]`；WiFi ColorPicker live case 接上 `speed`、`brightness`、`directionMode`、`color`。驗證後 `converted=51`、`remaining_effects=54`，`python3 scripts/validate_rgb_full_param_inventory.py`、`git diff --check` 與 `arch -arm64 pio run -e slave_standalone` 成功。

---

## Audio Active / VU 測試

ColorPicker 內有 Audio Active / VU 測試頁，可用兩種來源：

- iPhone / browser 內建 microphone：只用來測 web UI 與視覺反應。
- ESP32 I2S mic：實機 standalone 音訊來源。

Standalone I2S mic 預設腳位：

| 訊號 | GPIO |
|---|---:|
| SCK / BCLK | 12 |
| WS / LRCLK | 11 |
| SD / DATA | 13 |

常見 I2S MEMS mic 的 `L/R` 腳是選左右聲道，不是 `WS`。如果要選 left channel，通常把 `L/R` 接 GND；不要把 GND 接到 `WS`。

VU patterns 已從 `rhythm_detector.cpp` 移到：

- `firmware/shared/include/patterns/patterns_audio_active/patterns_vu.h`
- `firmware/shared/src/patterns/patterns_audio_active/patterns_vu.cpp`

目前有 20 個獨立 VU pattern。`storyMode_vu.cpp` 會每個 pattern 跑 20 秒，總共 400 秒。

---

## 分割區

`slave_standalone` 使用 `config/partitions/partitions_standalone.csv`：

- app0：`0x270000`，保留給 ColorPicker/audio firmware。
- LittleFS：`0x170000`，只放 standalone ColorPicker web UI。使用者不透過 ColorPicker 放 soundtrack；MP3 一律放 SD card。
- master 的 `data/html` 保留 Slave OTA 頁面；`slave_standalone` build/uploadfs 會透過 `tools/use_standalone_data_dir.py` 把 `data/html/colorpicker.html` 或 fallback 的 `web/colorpicker.html` **gzip 成 `/html/colorpicker.html.gz`** 才打包，避免把 `picker.html`、`jquery.min.js`、`slave.html` 等 Master 專用頁塞進 standalone LittleFS。
- standalone `/` / `/app` 送出預壓的 `colorpicker.html.gz` 並帶 `Content-Encoding: gzip`；若 FS 內無 `.gz` 才 fallback 到 raw `colorpicker.html` / `picker.html`。captive portal 偵測網址會 redirect 到 `/app`。

### Captive portal 修正重點

核心概念：captive portal 像手機問「這個 WiFi 登入頁在哪？」；standalone 現在一律把它帶到完整 ColorPicker。

- 常見偵測路徑 `/generate_204`、`/hotspot-detect.html`、`/fwlink`、`/ncsi.txt`、`/connecttest.txt` 會 redirect 到 `/app`。
- `/`、`/app`、`/colorpicker`、`/colorpicker.html` 都由 `standaloneHandleApp()` 回完整 ColorPicker。
- `standaloneHandleApp()` 優先送 `/html/colorpicker.html.gz`，並加上 `Content-Encoding: gzip`。
- `tools/use_standalone_data_dir.py` 會在 build/uploadfs 前把 ColorPicker 來源 gzip 成 `/html/colorpicker.html.gz`；若 `data/html/colorpicker.html` 不存在，會 fallback 使用 `web/colorpicker.html`。
- 不再依賴 master 舊頁或缺失的 plain HTML，所以連上 `Penelope-Standalone` 後 captive portal 可以打開完整 ColorPicker。

相關驗證：

```bash
python3 scripts/validate_standalone_captive_portal.py
python3 scripts/validate_standalone_web_assets.py
python3 scripts/validate_standalone_streaming.py
arch -arm64 pio run -e slave_standalone
```

---

## 快速排查

- 看不到 AP：確認 serial log 是否到 `reboot counter 3/3`，並掃描 channel 6。
- Captive portal 會 redirect 到完整 ColorPicker。Serial 應先看到 `Standalone HTTP redirect /hotspot-detect.html -> /app`，接著看到 `Standalone HTTP app ... gzip=1`。
- 打開 `192.168.4.1` 不是 app：直接試 `http://192.168.4.1/colorpicker.html` 或 `http://192.168.4.1/app`，並確認 uploadfs 有打包 `/html/colorpicker.html.gz`。
- 更新 web UI 後沒有變：先跑 `python3 scripts/build_web.py`，再 `uploadfs`。
- VU 一直 0%：先確認 mic 接線，尤其 `WS` 不要接 GND；`L/R` 才是聲道選擇腳。
- RGB 改短後尾端還亮：確認 firmware 已包含 `clearLiveStripTail()` 修正。

---

## 聯動頁與故事模式即時參數

- 聯動頁用逐段 UI 收集 `Slave ID`、`NUM_RGBX` 與 `bool direction`，不再要求手寫 `id:count`。
- Cross effect 的 Universal 與效果 Sub-menu 參數都會經 `/api/cross` 轉成既有 `LC:xu`／`LC:xp`。
- 故事模式頁會從實際 `storyMode_*.cpp` 呼叫產生「階段／效果」清單；效果名稱為唯讀，使用者不用也不能另選不屬於該故事的效果。
- 選定呼叫後，頁面會載入該呼叫的 Universal 與效果 Sub-menu 預設值，並可在播放中用 `/api/storylive` 調整指定 Slave／RGB strip；slave 在 story frame 最後套用 `LC:sfx`／`LC:sfxp`，不會停止故事時序。
- 參數 UI 沿用 Pattern schema；slider 取 schema 與 C++ 型別範圍的交集，`uint8_t` 最大不超過 255，也不會把用途較窄的 `uint16_t` slider 放大到 65535。
- `master` 與 `slave_standalone` 環境已註冊 `pre:scripts/build_web.py`。執行一般 build、`upload` 或 `uploadfs` 前，都會重新解析 StoryMode 呼叫並產生 ColorPicker；不需要另外手動執行 `python3 scripts/build_web.py`。

---

## 2026-07-07 RGB GN Sword ColorPicker 同步

- `GN_Sword_Normal`、`GN_Sword_Pulse`、`GN_Sword_Pulse_Color`、`GN_Sword_TransAM` 已改成 expanded universal params 加 `RgbGnSword*Params` / `RgbGnSword*Context`。
- `speed` 會影響填滿或彗星移動速度，`brightness` 會限制最終輸出，`directionMode` 會套用正向、反向、中心擴散、中心收縮。
- Web ColorPicker 已補上 GN Sword 四個效果的 slider schema、output JSON 與 info icon 說明；子參數使用 `effectBrightness` 避免和通用 `brightness` 混淆。
- 預設效果參數集中在 `storyMode_parameter.cpp` 的 `sm_rgb::gnSword*Config`，story mode 和 standalone ColorPicker 共用同一組預設值。

## 2026-07-07 RGB VentEffect ColorPicker 同步

- `VentEffect` 已改成 expanded universal params 加 `RgbVentEffectParams` / `RgbVentEffectContext`。
- 舊的散氣口硬編碼值已集中到 `sm_rgb::ventEffectConfig`；story mode 與 standalone ColorPicker 共用同一組預設值。
- `speed` 會影響散氣閃動與隨機填滿速度，`brightness` 會限制最終輸出，`directionMode` 會套用輸出方向，`color/palette` 會決定散氣底色。
- Web ColorPicker 已補上 VentEffect 的 slider schema、output JSON 與中英文 info icon，包含 palette index、閃動亮度範圍、閃動間隔、基礎亮度與隨機填滿時間。

## 2026-07-07 RGB Axe ColorPicker 同步

- `axe` 已改成 expanded universal params 加 `RgbAxeParams` / `RgbAxeContext`。
- `speed` 會影響白色掃光速度，`brightness` 會限制最終輸出，`directionMode` 會套用輸出方向，`color/palette` 會控制白色掃光與彩虹背景。
- `whiteLightSpeed`、`holdDurationMs`、`stageDurationMs` 等原本寫死的數值已集中到 `sm_rgb::axeConfig`。
- Web ColorPicker 已補上 Axe 的 slider schema、output JSON 與中英文 info icon。

## 2026-07-07 RGB Gundam Eye Wake ColorPicker 同步

- `gundamEyeWake` 已改成 expanded universal params 加 `RgbGundamEyeWakeParams` / `RgbGundamEyeWakeContext`。
- standalone live render 現在有 `PAT_RGB_GUNDAM_EYE_WAKE` case，ColorPicker 選這個效果會真正輸出。
- `speed` 會縮放爆亮與轉穩時間，`brightness` 限制最終輸出，`directionMode` 套用輸出方向，`color/palette` 可覆寫眼睛顏色。
- Web ColorPicker 已補上 burst/stationary 顏色、亮度與時間 slider，以及中英文 info icon。

## 2026-07-07 RGB Gradient Rainbow Swipe ColorPicker 同步

- `gradientRainbowSwipe` 已改成 expanded universal params 加 `RgbGradientRainbowSwipeParams` / `RgbGradientRainbowSwipeContext`。
- story mode 預設值集中到 `sm_rgb::gradientRainbowSwipeConfig`，active call 不再使用舊的 instance-only 簽名。
- `speed` 會影響彩虹流動與掃入節奏，`brightness` 限制最終輸出，`directionMode` 套用正向、反向與中心方向。
- Web ColorPicker 已補上 `hueStep`、`swipeDelayMs`、`totalDurationMs` slider、output JSON 與中英文 info icon。

## 2026-07-07 RGB Gun Fire Pattern ColorPicker 同步

- `GunFirePattern` 已改成 expanded universal params 加 `RgbGunFirePatternParams` / `RgbGunFirePatternContext`。
- 原本函式內共用的 static 狀態已移到每條 strip 的 context，standalone 多條 RGB 同時測試時不會互相污染。
- `speed` 會縮放槍火節奏，`brightness` 限制最終輸出，`directionMode` 套用輸出方向，`color/palette/flashColor` 會改變爆閃顏色。
- Web ColorPicker 已補上 duration、acceleration、flash、fade、toggle 與 flash color 的 sliders / output JSON / info icon。

## 2026-07-07 RGB Gradient Rainbow Thunder ColorPicker 同步

- `gradientRainbowThunder` 已改成 expanded universal params 加 `RgbGradientRainbowThunderParams` / `RgbGradientRainbowThunderContext`。
- live ColorPicker 不再共用全域 `thunderstate`，每條 RGB strip 有自己的雷光狀態。
- `speed` 會影響彩虹流動與掃入節奏，`brightness` 限制最終輸出，`directionMode` 套用輸出方向，`color/palette/thunderColor` 會改變底色與雷光爆閃色。
- Web ColorPicker 已補上 duration、swipe delay、thunder chance、thunder cooldown、thunder color 的 sliders / output JSON / info icon。

## 2026-07-07 RGB Color Spinner ColorPicker 同步

- `ColorSpinner` 已改成 expanded universal params 加 `RgbColorSpinnerParams` / `RgbColorSpinnerContext`。
- standalone live render 已補上 `PAT_RGB_COLOR_SPINNER` case，ColorPicker 選這個效果會真正輸出。
- `speed` 會縮放旋轉速度，`brightness` 限制最終輸出，`directionMode` 套用輸出方向，`palette/startColor/endColor` 控制變色。
- Web ColorPicker 已補上 start palette index、start color、end color、spinner speed、arc length、fade duration 的 sliders / output JSON / info icon。

## 2026-07-07 RGB Destiny Wing ColorPicker 同步

- `DestinyWing` 已改成 expanded universal params 加 `RgbDestinyWingParams` / `RgbDestinyWingContext`。
- standalone live render 已補上 `PAT_RGB_DESTINY_WING` case，ColorPicker 選這個效果會真正輸出。
- `speed` 會縮放填充與彗星速度，`brightness` 限制最終輸出，`directionMode` 套用輸出方向，`palette/gradient*/cometColor` 控制光翼漸層與彗星色。
- Web ColorPicker 已補上 gradient palette indexes、gradient color overrides、comet speed、head/tail length、fill speed 的 sliders / output JSON / info icon。

## 2026-07-07 RGB Machine Gun ColorPicker 同步

- `Machine_Gun` 與 `Machine_Gun_RedAstrayLimited` 已改成 expanded universal params 加 params/context。
- standalone live render 已補上兩個 machine gun case，ColorPicker 選這兩個效果會真正輸出。
- `speed` 會縮放子彈步進延遲，`brightness` 限制最終輸出，`directionMode` 套用輸出方向，`color/palette/bulletColor/bulletTailColor` 控制子彈與尾巴顏色。
- Web ColorPicker 已補上 step delay、bullet/tail colors、barrel/muzzle brightness、run/pause duration 的 sliders / output JSON / info icon。

## 2026-07-07 RGB Missile Launcher ColorPicker 同步

- `Missile_Launcher`、`Missile_Launcher_breath`、`Missile_Launcher_F16` 已改成 expanded universal params 加 params/context，不保留舊 positional 簽名。
- standalone live render 已補上 `PAT_RGB_MISSILE_LAUNCHER` case，ColorPicker 選 `RGB Missile Launcher` 會真正輸出。
- `speed` 會縮放點亮、閃爍、掃光與爆發時間，`brightness` 限制最終輸出，`directionMode` 套用輸出方向，`color/palette/rapidSwipeColor/burstColor` 控制主色、掃光色與爆發色。
- Web ColorPicker 已補上 light-up interval、blink duration/interval、swipe duration、burst move/shake/fade、wait time、shake strength 的 sliders / output JSON / info icon。

## 2026-07-07 RGB Signal / WarmWhite / Fadeout 同步

- `RandomFlashFadeout` 已改成 expanded universal params 加 params/context，並更新 `turbine_v3` 內部 fadeout 呼叫。
- `SignalLightEffect` 已改成 expanded universal params 加 params/context，storyMode callsite 改用 `sm_rgb::signalLightConfig`，standalone live render 已補上 `PAT_RGB_SIGNAL_LIGHT` case。
- `WarmWhitePalette` 已改成 expanded universal params 加 params/context，standalone `PAT_RGB_WARM_WHITE_PALETTE` 不再用 `gradientDynamicPalette` 代跑，改呼叫真正效果。
- Web ColorPicker 已補上 Signal Light 與 Warm White Palette 的 sliders / output JSON / info icon。

## 2026-07-07 RGB Ripple / Comet Reverse 同步

- `SingleRippleEffect_V2` 已改成 expanded universal params 加 params/context，standalone live render 已補上 `PAT_RGB_SINGLE_RIPPLE_V2` case。
- `cometReverse`、`cometReverse2`、`cometReverse4a` 已改成 expanded universal params 加 params/context，`cometIronMan` 內部 callsite 已更新。
- Web ColorPicker 已補上 `RGB Single Ripple V2` 的 sliders / output JSON / info icon。

## 2026-07-07 RGB Comet IronMan ColorPicker 同步

- `cometIronMan` 已改成 expanded universal params 加 `RgbCometIronManParams` / `RgbCometIronManContext`。
- standalone live render 已補上 `PAT_RGB_COMET_IRONMAN` case，ColorPicker 選 `RGB Comet IronMan` 會真正輸出。
- Web ColorPicker 已補上三段時間、stage1 head/tail、comet/breath color、呼吸亮度/速度、fade amount 的 sliders / output JSON / info icon。

## 2026-07-07 RGB Zoids Tail 參數同步

- `zoidsTail` 已改成 expanded universal params 加 `RgbZoidsTailParams` / `RgbZoidsTailContext`。
- demo story mode 的 zoidsTail callsite 已改用 `sm_rgb::zoidsTailDemoConfig`，背景色、彗星色、點亮間隔、彗星速度、頭尾長度與等待時間集中在 `storyMode_parameter.cpp`。

## 2026-07-07 RGB White Swipe / Dual Swipe ColorPicker submenu 同步

- `RGB White Swipe Bg V3` 已接到 standalone live render；ColorPicker 的 `speed`、`brightness`、`directionMode`、`color`、`paletteName`、`totalDurationMs`、`trailLength`、`hasHeadTrail` 會同步送到 slave。
- `RGB Dual Swipe Time Mod` 已接到 standalone live render；ColorPicker 的 `secondaryColor`、`backgroundColor`、`trailLength`、`secondarySpeedPercent`、`phaseOffsetPercent`、`timeModDivisorMs`、`timeModModulo` 會同步送到 slave。
- Pattern 參數 UI 現在用可展開 submenu：`Universal` 預設展開，`Sub-menu` 預設收合，避免進階 slider 一次全部擠在畫面上。
- Info icon 文案改成先看「effect + parameter」專屬說明，再 fallback 到共用參數說明；例如 `RGB White Swipe Bg V3` 的 `speed` 會說明白光掃過背景的速度，不再只顯示泛用速度說明。

## 2026-07-07 RGB Breath Swipe / Palette Wave ColorPicker 同步

- `rgbBreath_swipe`、`rgbBreath_swipe_palette`、`rgbBreath_swipe_palette_v2` 已改成 expanded universal params 加 `RgbBreathSwipeParams` / `RgbBreathSwipeContext`，story mode callsite 直接使用新簽名，沒有保留 legacy adapter。
- `paletteWave`、`paletteWave_V2`、`paletteWave_StoringEnergy`、`paletteWave_80Percent_SpecialWave` 已改成 expanded universal params 加 params/context structs，蓄能填色起點改由 `fillStartPercent` 控制。
- standalone live render 已補上 Breath Swipe 與 Palette Wave 系列 case，ColorPicker submenu 可調 breath cycle/run time、swipe color、wave width、initial/final speed、charge fill color、fill delay/batch、special wave chance/cooldown 等參數。

## Cross-FX Phase 1（slave live 執行核心）

`slave_live_colorpicker.cpp` 可把選中的本機 RGB strip 當成一條 virtual strip，跑 6 個 cross 效果（plasma / seqv2 / seqv3 meteor / breathv1 / breathv3 / seqoff）。LC 協議：

- `LC:xfx,<plasma|seqv2|seqv3|breathv1|breathv3|seqoff>`：選效果並進入 cross 模式。
- `LC:xgrp,RGB1,RGB2,...`：設有序 virtual strip（預設 RGB1）。
- `LC:xu,<speed|bmin|bmax|cyclems|totalms|dir|pal|color>,<value>`：universal（color=`r-g-b`，dir=0..3 對應 `WLED_DirectionMode`）。
- `LC:xp,<thick|branch|flash|tail|base|mintensity|mspeed|msize|mdurationms|fadeinms|intervalms|holdms|bcometsize|bswipe>,<value>`：effect params（base=`r-g-b`）。
- `LC:xstart[,<syncedMs>]` / `LC:xstop`：重啟（可帶同步時鐘域 startMs）/ 退出。
- `LC:xgrpc,<slaveId>:<count>,...`：**真 cross-chip** group（master 廣播用）。每段用真 slave id + 硬定段長，本地 buffer 一律 RGB1；只有 id == 本機 `SLAVE_ID` 嗰段會被寫 → 每塊真 slave render 自己一段。

單晶片（standalone）：用 `LC:xgrp` 本機 demo，所有段用本機 `SLAVE_ID`，一塊板 render 整條 virtual strip。時間基準 `storyModeAnimationMillis() - startMs`。

真 cross-chip：master 送 `LC:xgrpc,6:20,7:120` + `LC:xfx,...` + `LC:xstart,<syncedMs>`，各真 slave 用同一 synced 時鐘算相同 bolt、render 自己段 → 接縫連續。前提：slave 有 logClock offset（`logClockHasOffset()` true）。

**Web UI（聯動 tab）＋ `/api/cross` endpoint：**
- 頁：`web/tabs/cross_fx.html`（tab `data-t="crossFx"`）。真 slave 拓撲改用逐段 UI，每段明確選 `Slave ID` 與 `NUM_RGBX`；網頁才在送出時產生 `grpc`，不再讓使用者手寫 `id:count`。
- Universal 區完整提供 speed、brightness min/max、cycle、total duration、`bool direction`、palette、color；Sub-menu 依效果只顯示 plasma／meteor／sequence／breath 的適用參數。
- `POST /api/cross`：standalone（`standaloneHandleCross`）→ `sendLiveCommand` LC:x*；master（`handleApiCross` @ colorpicker.cpp，`#if ENABLE_WIFI_COLORPICKER`）→ 解析 `grpc` 目標 slave，`broadcastLiveCommand` 廣播 LC:x*，`LC:xstart,<syncedMs>` 用 `logClockMasterMillis()+lead`（預設 500ms）。
- 有填 `grpc` → cross-chip（`LC:xgrpc`）；否則本機 `LC:xgrp`。USB 模式由 `usbPost` client-side 轉 LC。

設計見 `docs/superpowers/specs/2026-07-13-cross-fx-colorpicker-phase1-design.md`。

## 故事模式播放中即時 RGB 參數

- 故事模式頁可選 Slave、RGB strip 與 RGB effect；參數直接沿用 Pattern schema，因此 Universal 與 Sub-menu 不會各自維護而漏欄位。
- `POST /api/storylive` 會轉成 `LC:sfx`／`LC:sfxp`；slave 不會關閉 `enableRunStory`，而是在每個 story frame 完成後套用指定 strip 的即時覆寫。
- `LC:sfxclear[,RGBX]` 清除覆寫。切換故事模式前網頁會先清除舊覆寫，避免上一個測試效果留到下一個故事。
- Slider 範圍採「schema 用途範圍與 C++ 型別範圍的交集」：例如 `uint8_t` 絕不超過 255，但 `uint16_t` 也不會無條件放大成 65535。
