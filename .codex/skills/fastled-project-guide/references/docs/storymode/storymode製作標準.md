# Story Mode 製作標準

本文件整理燈效技術會議的主要規則，給燈效實習生與 agent 製作、修改 story mode 前使用。它補充 `docs/storymode/storymode目錄.md` 與 `docs/project/standards/uniform_coding_style.md`：前者查現有模式，後者管程式碼風格，本文件管製作流程與內容標準。

## 會議主軸

1. **分工**：先確認 project、負責人、deadline、目前進度與實機狀態。
2. **基本技巧**：先熟悉 RGB strip、單色燈/PWM、PCA9685、slave ID、story mode 時序與 `platformio_local.ini` 設定。
3. **製作流程**：按照「試燈效 → 設參數 → 寫 story mode → 除錯/重構 → WiFi update」執行。
4. **Deadline of Projects**：白板上的項目要按 deadline 由早到晚重排；未定日期放最後。

## Workflow 五步

### 1. 寫 / 試燈效

- 先在最小範圍試單一 effect，不要一開始就塞入完整 story mode。
- 先確認 general name 與 effect name：
  - general name：給人看的效果描述，例如「流光」、「漩渦」、「散氣口」、「警示燈」。
  - effect name：實際函式或 pattern，例如 `whiteSwipe`、`turbine_v3`、`SpecificColorPattern`。
- 如果 effect 會重用，放入 `firmware/shared/src/lib/` 或 `firmware/shared/src/patterns/`，並同步更新 header。

### 2. 設定參數

新增或調整 story mode 前，先檢查三類檔案：

1. `platformio_local.ini`：story mode 總秒數、slave 數量、LED 數量、本機 upload/monitor port。
2. `firmware/shared/include/storymode/storyMode_parameter.h`：參數宣告、struct、instance、array。
3. `firmware/shared/src/storymode/storyMode_parameter.cpp`：參數定義與預設值。

常見參數要先定清楚：

1. 速度：`InitSpeed` / `FinalSpeed` / interval / cycle duration。
2. 亮度：最光、最暗、fade in、fade out。
3. 色盤：palette、固定色、override color。
4. 方向：正反、中心擴散、中心收縮。
5. Cycle 時長：每段效果的持續時間與重複週期。
6. 參數封裝：需要時用 Pointer `*` 與 Reference `&` 將類別參數打包至 `StoryMode_struct`。

### 3. 寫 Story Mode

- 每個 story mode 要有自己的清楚段落或頁面說明。
- 中間流程應寫 **timeslot + general description**，例如 `0:02-0:04 散氣口漸入`，不要把箭頭流程寫成 effect name 清單。
- 左右欄才放：
  - description：人能理解的部位與視覺效果。
  - effect name：實際函式與 RGB/PWM channel。
- 在程式碼中，story mode 應直接展開到 `case slaveId`，清楚看到 slave、RGB strip、PWM channel 與 motor pin。
- 不要把主要硬體呼叫藏在新 wrapper 或 macro 後面。
- 每個 RGB / PWM / motor / GPIO 呼叫前都要加硬體註解，優先從 Excel / 接線表複製，例如 `// RGB4 (12) 大腿-膝-小腿-腳掌 訊號 — SpecificColorPattern per-LED dispatch`。

### 4. 除錯、重構程式風格、調整時序

本階段本次簡報只列標題，不展開內容。實作時仍要遵守：

- 修改 shared code 後至少建置 master、一個 slave 與 standalone。
- Story mode 時長要和 timer screen 一致。
- 時序敏感位置避免 blocking call、過多 logging、動態配置與無必要 delay。

### 5. WiFi Update

本階段本次簡報只列標題，不展開內容。實作時參考 `docs/ota_wifi/wifi_update.md`。

## Story Mode 文件標準

每個 story mode 文件或簡報頁應包含：

1. Story mode 名稱：例如 `storyMode_awakening_3`。
2. 中文功能名：例如「蘇醒模式 3」。
3. Timeslot 流程：中間用時間段與 general description。
4. Description 欄：說明部位、視覺效果、演出目的。
5. Effect name 欄：列實際函式、RGB/PWM channel、重要參數。
6. 實作注意：哪些 slave 特別不同、哪些 strip 不參與、是否需要 colorpicker 驗證。
7. GPIO 註解來源：每個實作呼叫前的部位名稱與數量應能回查 Excel / 接線表。

## Story Mode Description 唯一來源

所有正式 mode 的名稱、Controller 狀態、設定時長與演出 description，統一維護在 `docs/storymode/storymode目錄.md`。本製作標準不再重複保存效果摘要，避免 Storing Energy、Plasma 或其他 mode 重構後留下舊 states 與舊時序。

更新 story mode 時，同一次變更必須：

1. 先以 `storyModeController.cpp` 確認正式 LED／servo 清單。
2. 以目前 `storyMode_*.cpp` 與 `storyMode_parameter.{h,cpp}` 更新 `docs/storymode/storymode目錄.md`。
3. 未註冊的 `storyMode_vu`、demo/dev 入口與工具函式要放在「非正式 Controller 入口」，不可混進正式清單。

## 完成前 Checklist

- [ ] 已確認 project deadline 與負責人。
- [ ] 已確認 `platformio_local.ini` 的 story mode 秒數與 LED 數量。
- [ ] 已確認 timer screen 的 story mode 秒數同步。
- [ ] 已把 general name 與 effect name 分開記錄。
- [ ] 已直接按 slave / RGB / PWM / motor 展開實作。
- [ ] 每個 RGB / PWM / motor / GPIO 呼叫前都有 Excel / 接線表來源的硬體註解。
- [ ] 已更新 `docs/storymode/storymode目錄.md`。
- [ ] shared code 有變更時，已建置 master、一個 slave 與 standalone。
